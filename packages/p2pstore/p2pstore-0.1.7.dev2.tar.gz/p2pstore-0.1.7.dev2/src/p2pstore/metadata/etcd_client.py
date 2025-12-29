"""
Etcd Metadata Client 实现模块.

该模块实现了基于 Etcd 的元数据客户端。
- 利用 Etcd 的 Lease 机制管理 Provider 和文件的生命周期
- 利用 Watch 机制监听删除事件，触发 RDMA 内存释放
- 所有查询操作直接访问 Etcd，保证强一致性（不使用本地缓存）
"""

import json
import os
import random
import threading
import time
from urllib.parse import urlparse

import etcd3

from ..core import MetadataClient
from ..utils.logger import LoggerManager


class EtcdMetadataClient(MetadataClient):
    """
    Etcd 元数据客户端.

    前缀设计:
    - /p2p/providers/{host} : Provider 注册信息 (绑定 Lease)
    - /p2p/files/{file_key} : 文件元数据 (绑定 Provider 的 Lease)
    """

    PREFIX_PROVIDER = "/p2p/providers/"
    PREFIX_FILE = "/p2p/files/"

    def __init__(
        self,
        etcd_endpoints: list[str],
        local_ip: str,
        client_id: str,
        registered_keys: dict[str, int] | None = None,
        enable_watch: bool = True,
        ttl: int = 3600,
    ):
        self.logger = LoggerManager.get_logger("etcd-metadata-client")
        self.local_ip = local_ip
        self.client_id = (
            client_id  # 当前 client 的 ID，用于判断删除事件是否是自己的数据
        )
        # 引用 client._registered_keys，用于获取自己的 put_id
        # 注意：不能使用 `or {}`，因为空字典也是 Falsy，会导致创建新字典而不是引用
        self._registered_keys = registered_keys if registered_keys is not None else {}
        self.etcd_endpoints = etcd_endpoints
        self.enable_watch = enable_watch  # 保存配置
        self.ttl = ttl  # 租约 TTL

        # 连接 Etcd (目前简单取第一个地址，生产环境可做高可用轮询)
        self._client = self._connect_etcd()

        # 本地状态
        self.lease = None
        self.lease_id = None
        self._keep_alive_thread = None
        self._watch_thread = None
        self.running = True
        self.local_host = None

        # Lease 恢复控制锁（防止并发重建）
        self._lease_recovery_lock = threading.Lock()
        self._last_recovery_attempt = 0  # 记录上次恢复尝试的时间戳
        self.RECOVERY_COOLDOWN = 5  # 恢复冷却时间（秒），避免频繁重连

        # 释放回调 (用于 Watch 监听到删除事件时触发)
        self._release_callback = None

        # 根据配置决定是否启动 Watch
        if self.enable_watch:
            self._start_watch()
        else:
            self.logger.info(
                "[ETCD] Watch 线程已禁用 (适用于纯 Consumer get 节点，减少 Etcd 压力)"
            )

    def _connect_etcd(self):
        """解析地址并连接 Etcd."""
        try:
            # 假设格式 http://ip:port
            endpoint = self.etcd_endpoints[0]
            parsed = urlparse(endpoint)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or 2379
            self.logger.info("连接 Etcd: %s:%s", host, port)

            # 增加 gRPC 消息大小限制，解决大量文件时 list_files 超限问题
            # grpc_message:"CLIENT: Received message larger than max (42587779 vs. 4194304)
            # 默认 4MB -> 1GB (与服务端 --max-request-bytes 保持一致)
            # 注意：过大会增加内存占用和传输时间，建议根据实际需求调整
            grpc_options = [
                ("grpc.max_send_message_length", 1024 * 1024 * 1024),
                ("grpc.max_receive_message_length", 1024 * 1024 * 1024),
                # 添加 gRPC 超时，防止网络分区时永久阻塞
                ("grpc.keepalive_time_ms", 10000),  # 10秒发送keepalive
                ("grpc.keepalive_timeout_ms", 5000),  # 5秒keepalive超时
            ]
            # 设置Etcd操作的全局超时（10秒），防止gRPC调用永久阻塞
            # 这个timeout会应用到所有Etcd操作（get/put/delete）
            return etcd3.client(
                host=host, port=port, grpc_options=grpc_options, timeout=10
            )
        except Exception as e:
            self.logger.error("Etcd 连接配置错误: %s", e)
            raise

    def _start_watch(self):
        """启动后台线程监听文件变化."""
        self._watch_thread = threading.Thread(target=self._watch_files, daemon=True)
        self._watch_thread.start()

    def _watch_files(self):
        """监听 /p2p/files/ 前缀的变化."""
        self.logger.info("开始监听 Etcd 文件变更...")
        # 启用 prev_kv=True，使 DeleteEvent 能获取被删除 key 的 value
        events_iterator, cancel = self._client.watch_prefix(
            self.PREFIX_FILE, prev_kv=True
        )

        try:
            for event in events_iterator:
                if not self.running:
                    break

                try:
                    key = event.key.decode("utf-8")
                    file_key = key.replace(self.PREFIX_FILE, "")

                    self.logger.debug(
                        "[ETCD-WATCH] 收到事件: type=%s, key=%s",
                        type(event).__name__,
                        file_key,
                    )

                    if isinstance(event, etcd3.events.PutEvent):
                        # 文件注册/更新 (仅记录日志，不维护本地缓存)
                        value = json.loads(event.value.decode("utf-8"))
                        host = value.get("host", "unknown")
                        self.logger.debug(
                            "[ETCD-WATCH] 文件注册/更新: key=%s, host=%s",
                            file_key,
                            host,
                        )

                    elif isinstance(event, etcd3.events.DeleteEvent):
                        # 文件删除事件：只处理本 client 注册的数据
                        self.logger.debug("[ETCD-WATCH] 收到删除事件: key=%s", file_key)

                        # 步骤 1: 从 DeleteEvent 中获取被删除的元数据
                        # python-etcd3 通过 event.prev_value 访问 prev_kv.value
                        deleted_metadata = None
                        deleted_client_id = None
                        deleted_put_id = None

                        try:
                            # 尝试获取 prev_value（需要 watch 启用 prev_kv=True）
                            prev_value = event.prev_value
                            if prev_value:
                                deleted_metadata = json.loads(
                                    prev_value.decode("utf-8")
                                )
                                deleted_client_id = deleted_metadata.get(
                                    "metadata", {}
                                ).get("client_id")
                                deleted_put_id = deleted_metadata.get(
                                    "metadata", {}
                                ).get("put_id")
                                self.logger.debug(
                                    "[ETCD-WATCH] 从 prev_kv 获取删除元数据: key=%s, client_id=%s, put_id=%s",
                                    file_key,
                                    deleted_client_id,
                                    deleted_put_id,
                                )
                            else:
                                self.logger.warning(
                                    "[ETCD-WATCH] prev_value 为空: key=%s (watch 可能未启用 prev_kv=True)",
                                    file_key,
                                )
                        except AttributeError as e:
                            self.logger.warning(
                                "[ETCD-WATCH] 无法访问 prev_value: key=%s, error=%s (watch 可能未启用 prev_kv=True)",
                                file_key,
                                e,
                            )
                        except Exception as e:
                            self.logger.warning(
                                "[ETCD-WATCH] 解析 prev_value 失败: key=%s, error=%s",
                                file_key,
                                e,
                            )

                        # 步骤 2: 优先检查 _registered_keys（核心判断）
                        # 只有在 _registered_keys 中的 key 才是本 client 的数据
                        if file_key not in self._registered_keys:
                            self.logger.debug(
                                "[ETCD-WATCH] key=%s 不在 _registered_keys，跳过释放 (不是本 client 的数据或已被主线程释放)",
                                file_key,
                            )
                            continue

                        # 步骤 3: 如果获取到了 prev_value，进行双重验证（client_id + put_id）
                        current_put_id = self._registered_keys[file_key]

                        if deleted_client_id is not None:
                            # 有 client_id：验证是否匹配
                            if deleted_client_id != self.client_id:
                                self.logger.warning(
                                    "[ETCD-WATCH] client_id 不匹配但 key 在 _registered_keys: key=%s, deleted_client_id=%s, my_client_id=%s (可能是注册残留)",
                                    file_key,
                                    deleted_client_id,
                                    self.client_id,
                                )
                                # 保守策略：跳过释放，避免误删其他 client 的数据
                                continue

                        if deleted_put_id is not None:
                            # 有 put_id：验证版本号防止 ABA 问题
                            if current_put_id != deleted_put_id:
                                self.logger.info(
                                    "[ETCD-WATCH] put_id 不匹配，跳过释放 (旧版本): key=%s, current=%s, deleted=%s",
                                    file_key,
                                    current_put_id,
                                    deleted_put_id,
                                )
                                continue
                        else:
                            # 无法获取 put_id：依赖 _registered_keys 判断（风险较低）
                            self.logger.debug(
                                "[ETCD-WATCH] 无 put_id 信息，仅依赖 _registered_keys 判断: key=%s",
                                file_key,
                            )

                        # 所有检查通过，触发释放回调
                        self.logger.info(
                            "[ETCD-WATCH] 接收到删除 key 事件，触发释放回调: key=%s, put_id=%s, client_id=%s, deleted_metadata=%s",
                            file_key,
                            current_put_id,
                            self.client_id,
                            deleted_metadata,
                        )

                        if self._release_callback:
                            self._release_callback(
                                file_key, current_put_id, self.client_id
                            )
                        else:
                            self.logger.debug(
                                "[ETCD-WATCH] 释放回调未设置，跳过: key=%s",
                                file_key,
                            )
                except Exception as e:
                    self.logger.error("[ETCD-WATCH] 处理事件异常: %s", e, exc_info=True)
        except Exception as e:
            if self.running:
                self.logger.error("Watch 线程异常退出: %s", e)

    # ----------------------------------------------------------------
    # 核心接口实现
    # ----------------------------------------------------------------

    def _try_recover_lease(self) -> bool:
        """
        尝试恢复 Lease（线程安全，带指数退避）.

        Returns:
            bool: 恢复成功返回 True
        """
        # 冷却检查：避免短时间内频繁重连（减少 Etcd 压力）
        current_time = time.time()
        if current_time - self._last_recovery_attempt < self.RECOVERY_COOLDOWN:
            self.logger.debug(
                "[ETCD-RECOVERY] 恢复冷却中，跳过 (%.1fs)",
                self.RECOVERY_COOLDOWN - (current_time - self._last_recovery_attempt),
            )
            return False

        with self._lease_recovery_lock:
            # 双重检查：其他线程可能已经完成恢复
            if self.lease is not None:
                self.logger.debug("[ETCD-RECOVERY] Lease 已恢复，跳过")
                return True

            self._last_recovery_attempt = current_time
            self.logger.warning(
                "[ETCD-RECOVERY] 检测到 Lease 丢失，尝试重新注册 Provider: host=%s",
                self.local_host or "unknown",
            )

            try:
                if not self.local_host:
                    self.logger.error(
                        "[ETCD-RECOVERY] 无法恢复：local_host 未设置（可能是初次注册失败）"
                    )
                    return False

                # 重新创建 Lease
                self.lease = self._client.lease(ttl=self.ttl)
                self.lease_id = getattr(self.lease, "id", None)  # 防御性获取

                if not self.lease_id:
                    self.logger.error(
                        "[ETCD-RECOVERY] Lease 创建成功但 ID 为空，可能是 etcd3 库异常"
                    )
                    self.lease = None
                    return False

                # 重新写入 Provider 注册信息（全局timeout已设置）
                key = f"{self.PREFIX_PROVIDER}{self.local_host}"
                value = json.dumps({"timestamp": time.time(), "state": "recovered"})
                self._client.put(key, value, lease=self.lease)

                self.logger.info(
                    "[ETCD-RECOVERY] Provider 恢复成功: host=%s, new_lease_id=0x%x",
                    self.local_host,
                    self.lease_id,
                )
                return True

            except Exception as e:
                self.logger.error(
                    "[ETCD-RECOVERY] 恢复失败: host=%s, error=%s",
                    self.local_host,
                    e,
                    exc_info=True,
                )
                self.lease = None
                return False

    def register_provider(self, host: str) -> None:
        """注册 Provider，创建 Lease 并启动保活."""
        try:
            # 保存 host 地址，供 close() 使用
            self.local_host = host

            # 创建租约
            self.lease = self._client.lease(ttl=self.ttl)
            # self.lease_id = self.lease.id
            self.lease_id = getattr(self.lease, "id", None)  # 统一使用防御性获取
            if not self.lease_id:
                raise RuntimeError("Lease 创建成功但 ID 为空，可能是 etcd3 库异常")

            key = f"{self.PREFIX_PROVIDER}{host}"
            value = json.dumps({"timestamp": time.time(), "state": "active"})

            # 写入并绑定租约（全局timeout已在client初始化时设置）
            self._client.put(key, value, lease=self.lease)
            self.logger.info(
                "Provider 注册成功: host=%s, Lease ID=0x%x, TTL=%ds",
                host,
                self.lease_id,
                self.ttl,
            )

            # 启动自动续租线程 (etcd3 库并未内置自动后台刷新，需要手动或使用 refresh)
            # 实际上 python-etcd3 的 lease 对象没有自动 refresh thread，这里简单实现一个
            self._keep_alive_thread = threading.Thread(
                target=self._keep_alive_loop, daemon=True
            )
            self._keep_alive_thread.start()

        except Exception as e:
            self.logger.error("注册 Provider 失败: %s", e)
            raise

    def _keep_alive_loop(self):
        """
        Lease 自动续租循环（增强版：失败时自动恢复）.
        """
        consecutive_failures = 0  # 连续失败次数
        max_failures = 3  # 连续失败 N 次后触发恢复

        while self.running:
            if not self.lease:
                # Lease 丢失，尝试恢复
                if self._try_recover_lease():
                    consecutive_failures = 0
                    continue
                else:
                    # 恢复失败，等待下一轮（指数退避已在 _try_recover_lease 中实现）
                    time.sleep(1)
                    continue

            try:
                self.lease.refresh()
                consecutive_failures = 0  # 成功后重置失败计数

                # [新增日志] 打印续租成功状态
                # 如果 TTL 较长(>60s) 或 调试模式，打印 INFO 日志，让用户安心
                # 对于短 TTL，避免日志刷屏，仅在 DEBUG 级别打印
                if self.ttl > 60:
                    self.logger.info(
                        "[ETCD-HEARTBEAT] 续租成功: lease_id=0x%x, ttl=%ds, host=%s, status=Active",
                        self.lease_id or 0,
                        self.ttl,
                        self.local_host,
                    )
                else:
                    self.logger.debug(
                        "[ETCD-HEARTBEAT] 续租成功: lease_id=0x%x", self.lease_id
                    )

                # 动态调整刷新间隔，保证在 TTL 过期前至少刷新 3 次
                base_interval = max(1, self.ttl / 3)
                # 添加 10% 的随机抖动，防止太多 client 同时发起请求 (Thundering Herd)
                jitter = base_interval * 0.1 * (random.random() * 2 - 1)
                time.sleep(base_interval + jitter)

            except Exception as e:
                consecutive_failures += 1
                self.logger.warning(
                    "续租失败 (%d/%d): %s",
                    consecutive_failures,
                    max_failures,
                    e,
                )

                if consecutive_failures >= max_failures:
                    # 连续失败超过阈值，判定 Lease 已失效
                    self.logger.error(
                        "[ETCD] Lease 续租连续失败 %d 次，判定已失效，触发恢复流程",
                        consecutive_failures,
                    )
                    self.lease = None  # 标记为失效
                    consecutive_failures = 0  # 重置计数器
                else:
                    # 快速重试
                    time.sleep(1)

    def unregister_provider(self, host: str) -> None:
        """注销 Provider (撤销租约)."""
        if self.lease:
            try:
                self.logger.info(
                    "[ETCD] 准备撤销 Lease: host=%s, lease_id=0x%x, "
                    "这将触发所有绑定文件的自动删除和 Watch DeleteEvent 广播",
                    host,
                    self.lease_id or 0,
                )
                self.lease.revoke()
                self.logger.info(
                    "[ETCD] Provider 注销成功: host=%s, Lease 已撤销, "
                    "所有绑定的 /p2p/files/* 键已自动删除",
                    host,
                )
            except Exception as e:
                self.logger.error(
                    "[ETCD] 注销 Provider 失败: host=%s, error=%s", host, e
                )
        else:
            self.logger.warning("[ETCD] Lease 未创建，跳过撤销: host=%s", host)
        self.lease = None

    def update_heartbeat(self, host: str) -> None:
        """Etcd 模式下由 Lease 自动处理心跳，无需手动 update."""
        pass

    def register_file(self, file_key: str, host: str, metadata: dict) -> bool:
        """
        注册文件元数据（增强版：自动恢复 Lease）.
        """
        # 关键改进：检测 Lease 丢失时自动恢复
        if not self.lease:
            self.logger.warning(
                "[ETCD] 检测到 Lease 丢失，尝试恢复后再注册文件: key=%s", file_key
            )
            if not self._try_recover_lease():
                self.logger.error(
                    "[ETCD] 注册文件失败: 无法恢复 Lease, key=%s", file_key
                )
                return False

        key = f"{self.PREFIX_FILE}{file_key}"
        # 构造完整元数据
        data = {"host": host, "metadata": metadata, "file_key": file_key}
        value = json.dumps(data)

        self.logger.debug(
            "[ETCD] 注册文件元数据: key=%s, host=%s, lease_id=0x%x, metadata=%s",
            file_key,
            host,
            self.lease_id or 0,
            metadata,
        )

        try:
            # 关键：绑定 Lease！如果 Provider 挂了，文件自动消失（全局timeout已设置）
            self._client.put(key, value, lease=self.lease)
            self.logger.debug(
                "[ETCD] 文件元数据已写入 Etcd: key=%s",
                file_key,
            )
            return True
        except Exception as e:
            self.logger.error("[ETCD] 注册文件失败: key=%s, error=%s", file_key, e)
            # 错误可能是 Lease 已失效，标记以便下次恢复
            error_msg = str(e).lower()
            if any(
                keyword in error_msg
                for keyword in ["lease not found", "lease expired", "not_found"]
            ):
                self.logger.warning(
                    "[ETCD] Lease 已失效（服务端已删除），标记为需要恢复"
                )
                self.lease = None
            return False

    def unregister_file(self, file_key: str) -> None:
        """注销文件 (本地清理)."""
        self.delete_file(file_key)

    def delete_file(self, file_key: str) -> bool:
        """删除文件 (全局删除)."""
        key = f"{self.PREFIX_FILE}{file_key}"

        self.logger.debug(
            "[ETCD] 准备删除文件: client_id=%s, key=%s",
            self.client_id,
            file_key,
        )

        try:
            # 全局timeout已设置
            success = self._client.delete(key)
            if success:
                self.logger.info(
                    "[ETCD] Etcd 删除成功: client_id=%s, key=%s, 等待 Watch 广播 DeleteEvent",
                    self.client_id,
                    file_key,
                )
                return True
            else:
                self.logger.warning(
                    "[ETCD] Etcd 删除返回 False: client_id=%s, key=%s (可能已不存在)",
                    self.client_id,
                    file_key,
                )
            return False
        except Exception as e:
            self.logger.error(
                "[ETCD] 删除文件异常: client_id=%s, key=%s, error=%s",
                self.client_id,
                file_key,
                e,
            )
            return False

    def delete_prefix(self, prefix: str) -> bool:
        """根据前缀删除文件（尽最大努力，带验证与重试）.

        默认策略：
        - **不做 get_prefix 校验**，避免在数据量大/高并发时对 Etcd 造成读放大。
        - 仅发起 Etcd DeleteRange(delete_prefix)，并记录响应中的 deleted 数。
        - 遇到异常会做有限次数重试（best-effort）。

        """

        key_prefix = f"{self.PREFIX_FILE}{prefix}"
        start = time.perf_counter()

        # best-effort 参数
        max_attempts = 3
        verify_checks = 2
        verify_interval_s = (
            0.5  # 如果还没删干净，稍等再查（给 Etcd/Watch 一点传播时间）
        )

        last_deleted = None
        last_remaining = None
        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                # python-etcd3 的 delete_prefix 返回 DeleteResponse
                response = self._client.delete_prefix(key_prefix)
                last_deleted = getattr(response, "deleted", None)
                elapsed = time.perf_counter() - start
                self.logger.info(
                    "[ETCD] delete_prefix 返回: client_id=%s, prefix=%s, attempt=%d/%d, deleted=%s, elapsed=%.3fs",
                    self.client_id,
                    prefix,
                    attempt,
                    max_attempts,
                    last_deleted,
                    elapsed,
                )
            except Exception as e:
                last_error = e
                self.logger.warning(
                    "[ETCD] delete_prefix 异常: client_id=%s, prefix=%s, attempt=%d/%d, error=%s",
                    self.client_id,
                    prefix,
                    attempt,
                    max_attempts,
                    e,
                )
                # 小退避，避免高并发下猛烈重试
                time.sleep(min(1.0, 0.2 * attempt))
                continue

            # 启用校验：做少量轮询确认
            for check_idx in range(1, verify_checks + 1):
                try:
                    remaining_items = self.get_prefix(prefix)
                    last_remaining = len(remaining_items)
                except Exception as e:
                    last_error = e
                    self.logger.warning(
                        "[ETCD] delete_prefix 校验查询异常: prefix=%s, check=%d/%d, error=%s",
                        prefix,
                        check_idx,
                        verify_checks,
                        e,
                    )
                    last_remaining = None

                if last_remaining == 0:
                    elapsed = time.perf_counter() - start
                    self.logger.info(
                        "[ETCD] 前缀删除确认完成: prefix=%s, deleted=%s, attempts=%d, elapsed=%.3fs",
                        prefix,
                        last_deleted,
                        attempt,
                        elapsed,
                    )
                    return True

                # 如果还没删干净，稍等再查（给 Etcd/Watch 一点传播时间）
                time.sleep(verify_interval_s)

            self.logger.warning(
                "[ETCD] 校验仍有残留，将重试 delete_prefix: prefix=%s, remaining=%s, attempt=%d/%d",
                prefix,
                last_remaining,
                attempt,
                max_attempts,
            )

        elapsed = time.perf_counter() - start
        self.logger.error(
            "[ETCD] delete_prefix 最终失败: prefix=%s, deleted=%s, remaining=%s, "
            "attempts=%d, elapsed=%.3fs, last_error=%s",
            prefix,
            last_deleted,
            last_remaining,
            max_attempts,
            elapsed,
            last_error,
        )
        return False

    def delete_prefix_batch(self, prefixes: list[str]) -> dict[str, bool]:
        """批量根据前缀删除文件."""
        results = {}
        for prefix in prefixes:
            results[prefix] = self.delete_prefix(prefix)
        return results

    def check_connection(self, timeout_ms: int = 3000) -> bool:
        """检查 Etcd 连通性."""
        try:
            # 全局timeout已设置（忽略timeout_ms参数）
            self._client.status()
            return True
        except Exception:
            return False

    def query_file(self, file_key: str) -> dict | None:
        """查询文件."""
        key = f"{self.PREFIX_FILE}{file_key}"
        try:
            # 全局timeout已设置
            value, meta = self._client.get(key)
            if value:
                return json.loads(value.decode("utf-8"))
            return None
        except Exception as e:
            self.logger.error("查询文件 %s 异常: %s", file_key, e)
            return None

    def get_prefix(self, prefix: str) -> dict[str, dict]:
        """
        根据前缀查询文件.

        Args:
            prefix: 文件 key 的前缀

        Returns:
            dict[str, dict]: 匹配的文件字典 {file_key: metadata}
        """
        key_prefix = f"{self.PREFIX_FILE}{prefix}"
        try:
            result = {}
            # 查询指定前缀下的所有键值
            for value, meta in self._client.get_prefix(key_prefix):
                if value:
                    data = json.loads(value.decode("utf-8"))
                    file_key = data.get("file_key")
                    if file_key:
                        result[file_key] = data

            self.logger.debug(
                "[ETCD] get_prefix 查询结果: prefix=%s, count=%d", prefix, len(result)
            )
            return result
        except Exception as e:
            self.logger.error(
                "[ETCD] get_prefix 查询异常: prefix=%s, error=%s", prefix, e
            )
            return {}

    def list_files(self) -> dict[str, dict]:
        """列出所有文件 (直接查询 Etcd，保证强一致性)."""
        try:
            result = {}
            # 查询 /p2p/files/ 前缀下的所有键值（全局timeout已设置）
            for value, meta in self._client.get_prefix(self.PREFIX_FILE):
                if value:
                    data = json.loads(value.decode("utf-8"))
                    file_key = data.get("file_key")
                    if file_key:
                        result[file_key] = data

            self.logger.debug("[ETCD] list_files 查询结果: count=%d", len(result))
            return result
        except Exception as e:
            self.logger.error(
                "[ETCD] list_files 查询异常: %s",
                e,
            )
            return {}

    def clear_files(self) -> dict:
        """清空所有文件 (先查询 Etcd，再逐个删除以触发 Watch 释放)."""
        try:
            # 先从 Etcd 实时查询所有文件
            files = self.list_files()
            keys_to_clear = list(files.keys())
            count = len(keys_to_clear)

            self.logger.info(
                "[ETCD] 开始清空文件: client_id=%s, total=%d (查询自 Etcd)",
                self.client_id,
                count,
            )

            # 逐个删除以触发 Watch DeleteEvent
            failed_keys = []
            for i, file_key in enumerate(keys_to_clear):
                try:
                    key = f"{self.PREFIX_FILE}{file_key}"
                    # 全局timeout已设置
                    success = self._client.delete(key)
                    if success:
                        if i % 100 == 0:  # 避免日志刷屏，每100条打印一次进度
                            self.logger.info(
                                "[ETCD] 批量删除进度: %d/%d (当前 key=%s)",
                                i + 1,
                                count,
                                file_key,
                            )
                    else:
                        self.logger.warning(
                            "[ETCD] 删除文件返回 False: key=%s", file_key
                        )
                        failed_keys.append(file_key)
                except Exception as e:
                    self.logger.warning(
                        "[ETCD] 删除文件失败: key=%s, error=%s", file_key, e
                    )
                    failed_keys.append(file_key)

            success_count = count - len(failed_keys)
            self.logger.info(
                "[ETCD] 批量删除请求完成: 成功 %d/%d. "
                "Watch 线程将收到 DeleteEvent 并触发释放回调.",
                success_count,
                count,
            )
            return {
                "success": True,
                "cleared": success_count,
                "failed": failed_keys,
            }
        except Exception as e:
            self.logger.error("[ETCD] clear_files 异常: %s", e)
            return {"success": False, "msg": str(e)}

    def update_load(self, host: str, delta: int) -> None:
        pass

    def set_release_callback(self, callback) -> None:
        self._release_callback = callback

    def close(self) -> None:
        """关闭客户端."""
        self.running = False
        # 使用正确的 host 地址撤销租约
        if self.local_host:
            self.unregister_provider(self.local_host)
        else:
            self.unregister_provider("")
            self.logger.warning("[ETCD] local_host 未设置，执行 unregister_provider()")
        # etcd3 client 不需要显式 close，但可以做一些清理
        self.logger.info("Etcd Metadata Client 已关闭")
