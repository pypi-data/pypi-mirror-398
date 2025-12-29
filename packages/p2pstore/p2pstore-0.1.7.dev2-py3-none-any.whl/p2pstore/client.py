"""
P2P Store Client 模块.

该模块提供了 P2P Store 系统的主客户端入口 `P2PClient`。
它封装了底层的元数据管理 (MetadataClient) 和数据传输 (Transport) 逻辑，
为上层应用提供统一的 put/get/list/delete 等 API。
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import os
import secrets
import time
from typing import Any

import numpy as np

from .core import TransferRequest
from .metadata import create_metadata_client
from .utils import (
    LoggerManager,
    P2PConfig,
    deserialize_object,
    numpy_from_file,
    serialize_object,
    serialize_tensor,
    setup_topology_env,
    validate_data_type,
)


class P2PClient:
    """面向P2P 传输的统一客户端, 支持多 Metadata / Transport 插拔."""

    def __init__(self, config: P2PConfig, check_metaserver: bool = True):
        """
        初始化 P2PClient.

        Args:
            config: P2P 配置.
            check_metaserver: 是否检查 Metaserver 连通性，默认 True.
                              如果为 True 且 Metaserver 不可用，抛出 RuntimeError.
        """
        self.config = config

        # 专用线程池，用于隔离 Etcd 阻塞操作，防止阻塞主线程池
        self._etcd_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1000, thread_name_prefix="etcd_worker"
        )

        # 生成 8 位随机字符串作为 client_id，用于日志子目录和日志格式
        self.client_id = secrets.token_hex(4)
        LoggerManager.set_sub_dir(self.client_id)

        self.logger = LoggerManager.get_logger(config.log_name or "p2p-client")
        self.logger.info("P2PClient 初始化: client_id=%s", self.client_id)
        from .transport import create_transport

        # 存储 {key: put_id}，用于版本控制，防止 Watch 线程误删新数据
        self._registered_keys = {}

        # 对于 RDMA 协议，根据是否指定设备决定拓扑策略
        if config.protocol == "rdma":
            if config.device:
                # 指定了设备，清除拓扑环境变量，让 Transfer Engine 直接用指定设备
                os.environ.pop("MC_CUSTOM_TOPO_JSON", None)
            else:
                # 未指定设备，自动设置拓扑环境变量
                setup_topology_env(include_cuda=True)

        local_ip = config.local_host.split(":")[0]
        self.metadata_client = create_metadata_client(
            config, local_ip, self.client_id, self._registered_keys
        )
        self.transport = create_transport(config)
        if not self.transport.initialize(config.local_host, config.device):
            raise RuntimeError("Transport 初始化失败, 请检查配置")

        # 注册 Provider
        # Etcd 模式需要在此处获取 Lease，否则后续无法注册文件
        self.metadata_client.register_provider(self.transport.get_local_addr())

        # 设置 buffer 释放回调
        self.metadata_client.set_release_callback(self._on_file_unregister)

        # 检查 Metaserver 连通性
        if check_metaserver:
            if not self.metadata_client.check_connection():
                raise RuntimeError(
                    f"Metaserver 不可用: {config.metadata_server}，请确保 Metaserver 已启动"
                )

    # ------------------------------------------------------------------
    # Data APIs
    # ------------------------------------------------------------------
    async def put(self, key: str, data: Any) -> bool:
        """
        注册数据到 P2P Store 系统.

        如果 key 已存在，会先删除旧数据（包括通知原节点释放内存），再注册新数据。

        Args:
            key: 数据的唯一标识符.
            data: 要注册的数据对象 (Tensor, 文件路径, bytes 等).

        Returns:
            bool: 注册是否成功.
        """
        start_time = time.perf_counter()
        self.logger.debug(
            "[PUT] 开始注册 key=%s, data_type=%s", key, type(data).__name__
        )
        if hasattr(data, "place"):
            self.logger.debug("[PUT] Input Tensor device: %s", data.place)

        # 先检查 key 是否已存在，如果存在则删除旧数据
        loop = asyncio.get_running_loop()
        existing = await loop.run_in_executor(
            self._etcd_executor, self.metadata_client.query_file, key
        )
        if existing:
            existing_host = existing.get("host", "unknown")
            existing_client = existing.get("metadata", {}).get("client_id", "unknown")
            self.logger.info(
                "[PUT] 检测到 key=%s 已存在 (host=%s, client=%s)，准备覆盖",
                key,
                existing_host,
                existing_client,
            )
            # 先同步释放本地内存，避免与 Watch 线程竞态
            if key in self._registered_keys:
                old_put_id = self._registered_keys[key]
                self.logger.debug(
                    "[PUT] key=%s 在本地 _registered_keys (put_id=%s)，主线程同步释放内存",
                    key,
                    old_put_id,
                )
                try:
                    self.transport.release(key)
                    self._registered_keys.pop(key, None)
                    self.logger.debug(
                        "[PUT] 主线程已同步释放旧内存: key=%s, put_id=%s",
                        key,
                        old_put_id,
                    )
                except Exception as e:
                    self.logger.error("[PUT] 释放旧内存失败: key=%s, error=%s", key, e)
                    # 继续执行，尝试覆盖写
            else:
                self.logger.debug(
                    "[PUT] key=%s 不在本地 _registered_keys (远程节点数据)，跳过本地释放",
                    key,
                )
            # 再删除元数据（Watch 线程收到事件时，内存已经释放完毕）
            self.logger.debug("[PUT] 删除 Etcd 元数据: key=%s", key)
            await loop.run_in_executor(
                self._etcd_executor, self.metadata_client.delete_file, key
            )
        else:
            self.logger.debug("[PUT] key=%s 不存在，直接注册", key)

        data_type = validate_data_type(data)
        self.logger.debug("[PUT] 构建传输请求: key=%s, data_type=%s", key, data_type)
        payload, request = self._build_transfer_request(key, data, data_type)

        self.logger.debug(
            "[PUT] RDMA 注册: key=%s, size=%d bytes",
            key,
            getattr(request, "data_size", 0),
        )
        success = self.transport.send(
            remote_addr=self.transport.get_local_addr(),
            request=request,
            data=payload,
        )
        if not success:
            self.logger.error(
                "[PUT] RDMA 注册失败: key=%s，client_id=%s", key, self.client_id
            )
            return False

        metadata = self._metadata_from_request(key, request)
        # 生成唯一的 put_id（纳秒时间戳），用于精确标识这次 PUT 操作
        put_id = time.time_ns()
        metadata["client_id"] = self.client_id
        metadata["put_id"] = put_id

        self.logger.debug(
            "[PUT] 注册 Etcd 元数据: key=%s, host=%s, put_id=%d",
            key,
            self.transport.get_local_addr(),
            put_id,
        )
        register_success = await loop.run_in_executor(
            self._etcd_executor,
            lambda: self.metadata_client.register_file(
                file_key=key,
                host=self.transport.get_local_addr(),
                metadata=metadata,
            ),
        )
        if not register_success:
            # 元数据注册失败，释放已分配的 buffer
            self.logger.error(
                "[PUT] Etcd 元数据注册失败，回滚释放 RDMA 内存: key=%s", key
            )
            self.transport.release(key)
            return False

        # 存储 key -> put_id 映射，用于 Watch 线程版本控制
        self._registered_keys[key] = put_id
        elapsed = time.perf_counter() - start_time
        self.logger.info(
            "[PUT] 完成注册: key=%s host=%s client_id=%s put_id=%d (total_keys=%d) 耗时: %.4fs",
            key,
            self.transport.get_local_addr(),
            self.client_id,
            put_id,
            len(self._registered_keys),
            elapsed,
        )
        return True

    async def delete(self, key: str) -> bool:
        """
        删除数据 (可删除任意节点注册的数据).

        Args:
            key: 要删除的数据标识符.

        Returns:
            bool: 删除是否成功
        """
        is_local = key in self._registered_keys
        self.logger.debug(
            "[DELETE] 开始删除: key=%s, is_local=%s",
            key,
            is_local,
        )

        loop = asyncio.get_running_loop()
        success = await loop.run_in_executor(
            self._etcd_executor, self.metadata_client.delete_file, key
        )

        if success:
            self.logger.debug(
                "[DELETE] Etcd 删除成功: key=%s. "
                "注意: 本地/远程内存释放将由 Watch 线程异步触发 (is_local=%s)",
                key,
                is_local,
            )
        else:
            self.logger.error(
                "[DELETE] Etcd 删除失败: key=%s (可能不存在或 Etcd 异常)", key
            )
        return success

    async def delete_batch(self, keys: list[str]) -> dict[str, bool]:
        """
        批量删除数据.

        Args:
            keys: 要删除的数据标识符列表.

        Returns:
            dict[str, bool]: 每个 key 的删除结果.
        """
        results = {}
        for key in keys:
            success = await self.delete(key)
            results[key] = success
        return results

    async def get_prefix(self, prefix: str) -> dict[str, dict]:
        """
        根据前缀查询数据.

        Args:
            prefix: 数据标识符前缀.

        Returns:
            dict[str, dict]: 匹配的文件字典 {file_key: metadata}
        """
        self.logger.debug("[GET_PREFIX] 开始前缀查询: prefix=%s", prefix)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            self._etcd_executor, self.metadata_client.get_prefix, prefix
        )
        self.logger.debug(
            "[GET_PREFIX] 前缀查询完成: prefix=%s, count=%d", prefix, len(result)
        )
        return result

    async def delete_prefix(self, prefix: str) -> bool:
        """
        根据前缀删除数据.

        Args:
            prefix: 数据标识符前缀.

        Returns:
            bool: 删除是否成功
        """
        self.logger.debug("[DELETE] 开始前缀删除: prefix=%s", prefix)
        loop = asyncio.get_running_loop()
        success = await loop.run_in_executor(
            self._etcd_executor, self.metadata_client.delete_prefix, prefix
        )
        if success:
            self.logger.info("[DELETE] 前缀删除成功: prefix=%s", prefix)
        else:
            self.logger.error("[DELETE] 前缀删除失败: prefix=%s", prefix)
        return success

    async def delete_prefix_batch(self, prefixes: list[str]) -> dict[str, bool]:
        """
        批量根据前缀删除数据.

        Args:
            prefixes: 前缀列表.

        Returns:
            dict[str, bool]: 每个前缀的删除结果.
        """
        self.logger.debug("[DELETE] 开始批量前缀删除: count=%d", len(prefixes))
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            self._etcd_executor, self.metadata_client.delete_prefix_batch, prefixes
        )
        return results

    def _on_file_unregister(
        self,
        key: str,
        deleted_put_id: int | None = None,
        deleted_client_id: str | None = None,
    ) -> None:
        """
        收到 file_unregister 广播时的回调, 释放本地 buffer.

        注意：etcd_client 已经完成了所有检查（client_id + key 存在 + put_id 匹配），
        所以这里直接执行释放操作即可。

        Args:
            key: 文件 key
            deleted_put_id: 被删除的数据的 put_id（已在 etcd_client 中验证）
            deleted_client_id: 被删除的数据的 client_id（已在 etcd_client 中验证）
        """
        self.logger.info(
            "[WATCH-CALLBACK] 释放本地 buffer: key=%s, put_id=%s",
            key,
            deleted_put_id,
        )

        # 直接释放（所有检查已在 etcd_client 中完成）
        self.transport.release(key)
        self._registered_keys.pop(key, None)

        self.logger.debug(
            "[WATCH-CALLBACK] key=%s 已释放 (remaining_keys=%d)",
            key,
            len(self._registered_keys),
        )

    async def clear(self) -> dict:
        """
        清空所有文件.

        Returns:
            dict: {"success": bool, "cleared": int, "failed": list[str]}
        """
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            self._etcd_executor, self.metadata_client.clear_files
        )

        if result.get("success"):
            self.logger.info("所有数据已清除, 共 %d 个", result.get("cleared", 0))
        else:
            failed = result.get("failed", [])
            self.logger.warning(
                "清空完成, 成功 %d 个, 失败 %d 个: %s",
                result.get("cleared", 0),
                len(failed),
                failed,
            )

        return result

    async def get(
        self,
        key: str,
        output_path: str | None = None,
        inplace_tensor: Any | None = None,
    ) -> Any | None:
        """
        获取数据.

        Args:
            key: 数据标识符.
            output_path: 可选, 将数据保存到指定文件路径.
            inplace_tensor: 可选, 将数据直接写入该 Tensor (需支持 set_value).

        Returns:
            Optional[Any]: 获取到的数据对象, 失败则返回 None.
        """
        self.logger.debug("[GET] 开始查询: key=%s", key)

        if inplace_tensor is not None and hasattr(inplace_tensor, "place"):
            self.logger.debug("[GET] inplace_tensor device: %s", inplace_tensor.place)

        entry = await self._query_metadata(key)
        if not entry:
            self.logger.error("[GET] 数据不存在: key=%s", key)
            return None

        provider_addr = entry.get("host", "")
        metadata = entry.get("metadata", {})
        client_id = metadata.get("client_id", "unknown")
        data_size = metadata.get("data_size", 0)
        self.logger.debug(
            "[GET] 查询成功: key=%s, provider=%s, size=%d bytes",
            key,
            provider_addr,
            data_size,
        )

        request = self._request_from_metadata(key, metadata)
        if request is None:
            self.logger.error("[GET] 构建传输请求失败: key=%s", key)
            return None

        # RDMA 传输 (带重试机制)
        # 超时策略 (针对高性能 RDMA: 10GB/30s ≈ 333MB/s):
        #   - 小文件 (<10MB): 2-3 秒 (主要场景，高并发下留足余量)
        #   - 中文件 (10-100MB): 3-10 秒 (线性增长)
        #   - 大文件 (>100MB): 10-30 秒 (上限 30s，足够 10GB 传输)
        # 重试策略:
        #   - 最多重试 3 次 (共 4 次尝试)
        #   - 指数退避 + 抖动: 0.5s → 1s → 2s (避免高并发下重试风暴)
        size_mb = data_size / (1024 * 1024)  # 转换为 MB

        # 动态超时计算: 小文件快速失败，大文件留足时间
        if size_mb < 10:
            recv_timeout = max(2.0, size_mb * 0.3)  # 1MB->2s, 10MB->3s
        elif size_mb < 100:
            recv_timeout = 3.0 + (size_mb - 10) * 0.1  # 10MB->3s, 100MB->12s
        else:
            recv_timeout = min(
                12.0 + (size_mb - 100) * 0.018, 30.0
            )  # 100MB->12s, 1GB->30s

        max_retries = 3  # 最多重试 3 次
        base_retry_interval = 0.5  # 基础重试间隔（秒）

        self.logger.debug(
            "[GET] RDMA 传输准备: key=%s, remote=%s, client_id=%s, ptr=0x%x, "
            "size=%d bytes (%.2f MB), timeout=%.1fs",
            key,
            provider_addr,
            client_id,
            request.buffer_ptr or 0,
            data_size,
            size_mb,
            recv_timeout,
        )

        payload = None
        last_error = None
        loop = asyncio.get_running_loop()

        for attempt in range(max_retries + 1):
            try:
                payload = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: self.transport.recv(
                            request=request, remote_addr=provider_addr
                        ),
                    ),
                    timeout=recv_timeout,
                )

                if payload is not None:
                    # 传输成功，跳出重试循环
                    if attempt > 0:
                        self.logger.info(
                            "[GET] RDMA 传输成功 (重试后): key=%s, 尝试 %d/%d",
                            key,
                            attempt + 1,
                            max_retries + 1,
                        )
                    break

                # payload 为 None，记录警告并重试
                self.logger.warning(
                    "[GET] RDMA 传输返回 None: key=%s, 尝试 %d/%d",
                    key,
                    attempt + 1,
                    max_retries + 1,
                )
                last_error = "transport returned None"

            except asyncio.TimeoutError:
                last_error = f"timeout after {recv_timeout:.1f}s"
                self.logger.warning(
                    "[GET] RDMA 传输超时: key=%s, 尝试 %d/%d, timeout=%.1fs",
                    key,
                    attempt + 1,
                    max_retries + 1,
                    recv_timeout,
                )

            except Exception as e:
                last_error = str(e)
                self.logger.warning(
                    "[GET] RDMA 传输异常: key=%s, 尝试 %d/%d, error=%s",
                    key,
                    attempt + 1,
                    max_retries + 1,
                    e,
                )

            # 如果不是最后一次尝试，指数退避后重试
            if attempt < max_retries:
                retry_delay = base_retry_interval * (2**attempt)  # 0.5s, 1s, 2s
                self.logger.debug(
                    "[GET] 等待 %.1fs 后重试 (尝试 %d/%d)",
                    retry_delay,
                    attempt + 1,
                    max_retries,
                )
                await asyncio.sleep(retry_delay)

        # 所有重试都失败
        if payload is None:
            self.logger.error(
                "[GET] RDMA 传输最终失败: key=%s from %s (client_id=%s), "
                "已尝试 %d 次, 最后错误: %s",
                key,
                provider_addr,
                client_id,
                max_retries + 1,
                last_error,
            )
            return None

        self.logger.debug(
            "[GET] RDMA 传输成功: key=%s, from %s (client_id=%s) received=%d bytes",
            key,
            provider_addr,
            client_id,
            len(payload),
        )

        if output_path:
            self.logger.debug("[GET] 保存到文件: %s", output_path)
            self._save_to_file(payload, output_path)

        result = self._decode_payload(request, payload, inplace_tensor)

        return result

    async def exists(self, key: str) -> bool:  # pragma: no cover - 轻量辅助
        """
        检查数据是否存在.

        Args:
            key: 数据标识符.

        Returns:
            bool: 存在返回 True, 否则 False.
        """
        entry = await self._query_metadata(key)
        return entry is not None

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------
    async def _query_metadata(self, key: str) -> dict | None:
        """
        查询 Etcd 中的元数据 (不重试，直接返回结果).

        从 Etcd 查询指定 key 的元数据信息，包括数据所在节点、大小、类型等。
        查询失败时直接返回 None，不进行重试。

        Args:
            key: 数据的唯一标识符
                 示例: "model/layer1/weights"

        Returns:
            dict | None:
                - dict: 包含元数据的字典，结构如下:
                    {
                        "host": "10.0.0.1:5001,5002",  # 数据所在节点
                        "metadata": {
                            "object_type": "numpy",
                            "data_size": 40000,
                            "tensor_shape": [100, 100],
                            "tensor_dtype": "float32"
                        }
                    }
                - None: 数据不存在或查询失败

        超时机制:
            - 查询超时时间: 5 秒
            - 超时后直接返回 None，不重试

        示例:
            entry = await client._query_metadata("my_array")
            if entry:
                provider = entry["host"]  # "10.0.0.1:5001,5002"
                size = entry["metadata"]["data_size"]  # 40000
        """
        self.logger.debug("[QUERY] 查询元数据: key=%s", key)

        try:
            # 使用 run_in_executor 将同步的 Etcd 调用放入专用线程池
            # 避免阻塞主事件循环
            loop = asyncio.get_running_loop()

            # 设置 5 秒超时，防止 Etcd 调用 hang 住 (例如网络分区)
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self._etcd_executor, self.metadata_client.query_file, key
                ),
                timeout=5.0,
            )

            if result:
                self.logger.debug("[QUERY] 查询成功: key=%s", key)
            else:
                self.logger.debug("[QUERY] 数据不存在: key=%s", key)

            return result

        except asyncio.TimeoutError:
            # Etcd 查询超时，可能是网络问题或 Etcd 负载过高
            self.logger.warning("[QUERY] 查询超时 (5s): key=%s", key)
            return None

        except Exception as e:
            # 其他异常 (连接失败、序列化错误等)
            self.logger.warning("[QUERY] 查询异常: key=%s, error=%s", key, e)
            return None

    def _build_transfer_request(self, key: str, data: Any, data_type: str):
        request = TransferRequest(
            object_type=data_type,
            data_size=0,
            tensor_shape=(),
            metadata={"file_key": key},
        )

        if data_type == "numpy":
            # Numpy 数组：直接传递，不序列化
            payload = data
            request.tensor_shape = tuple(payload.shape)
            request.tensor_dtype = str(payload.dtype)
            request.data_size = payload.nbytes

        elif data_type == "tensor":
            if not hasattr(data, "nbytes"):
                # Fallback: 如果无法直接获取大小，才不得不序列化（极少情况）
                payload = serialize_tensor(data)
                request.data_size = len(payload)
            else:
                # Paddle Tensor：直接传递，不序列化
                payload = data
            request.tensor_shape = tuple(payload.shape)
            request.tensor_dtype = str(payload.dtype)
            request.data_size = payload.nbytes

        elif data_type == "safetensors":
            payload = numpy_from_file(data)
            request.file_path = data
            request.data_size = int(payload.nbytes)
        elif data_type == "object":
            payload = serialize_object(data)
            request.data_size = int(payload.nbytes)
        else:
            raise TypeError(f"不支持的数据类型: {data_type}")

        return payload, request

    def _metadata_from_request(
        self, _key: str, request: TransferRequest
    ) -> dict[str, Any]:
        """从传输请求构建元数据字典 (_key 参数保留用于未来扩展)."""
        metadata = {
            "object_type": request.object_type,
            "data_size": request.data_size,
            "tensor_shape": request.tensor_shape,
            "tensor_dtype": request.tensor_dtype,
            "buffer_ptr": request.buffer_ptr,
        }
        metadata.update(request.metadata)
        return metadata

    def _request_from_metadata(
        self, _key: str, metadata: dict[str, Any]
    ) -> TransferRequest | None:
        """从元数据构建传输请求 (_key 参数保留用于未来扩展)."""
        object_type = metadata.get("object_type")
        data_size = int(metadata.get("data_size", 0))
        if not object_type or data_size <= 0:
            self.logger.error("元数据缺失 object_type 或 data_size, 无法传输")
            return None
        request = TransferRequest(
            object_type=object_type,
            data_size=data_size,
            tensor_shape=tuple(metadata.get("tensor_shape") or ()),
            tensor_dtype=metadata.get("tensor_dtype"),
            file_path=metadata.get("file_path", ""),
            buffer_ptr=metadata.get("buffer_ptr"),
            metadata=metadata.copy(),  # 传递完整的原始 metadata
        )
        return request

    def _decode_payload(
        self,
        request: TransferRequest,
        payload: Any,
        _inplace_tensor: Any | None,
    ) -> Any:
        """
        解码传输负载数据.

        Args:
            request: 传输请求对象
            payload: 原始负载数据
            _inplace_tensor: 保留参数，用于未来的原地写入优化

        Returns:
            解码后的数据对象
        """
        raw_bytes = self._to_bytes(payload)
        obj_type = request.object_type

        # Numpy: 直接从 raw bytes 恢复为 ndarray（零拷贝）
        if obj_type == "numpy":
            self.logger.debug(
                "[DECODE] key %s 恢复 Numpy 数组: shape=%s dtype=%s",
                request.metadata.get("file_key", ""),
                request.tensor_shape,
                request.tensor_dtype,
            )
            dtype = np.dtype(request.tensor_dtype)
            arr = np.frombuffer(raw_bytes, dtype=dtype)
            if request.tensor_shape:
                arr = arr.reshape(request.tensor_shape)
            return arr

        # Paddle Tensor / Safetensors: 返回 raw bytes 让用户自己加载
        if obj_type in ("tensor", "safetensors"):
            return raw_bytes

        if obj_type == "object":
            return deserialize_object(raw_bytes)

        return raw_bytes

    def _save_to_file(self, payload: Any, output_path: str) -> None:
        data = self._to_bytes(payload)
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(data)
        self.logger.info("数据已保存到 %s", output_path)

    def _to_bytes(self, payload: Any) -> bytes:
        if isinstance(payload, bytes):
            return payload
        if isinstance(payload, np.ndarray):
            return payload.tobytes()
        if isinstance(payload, bytearray):
            return bytes(payload)
        return bytes(payload)

    # ------------------------------------------------------------------
    # Common APIs
    # ------------------------------------------------------------------
    def list(self) -> list[str]:
        """
        列出所有已注册的文件 key.

        Returns:
            list[str]: 文件 key 的列表.

        Example:
            >>> client.list()
            ['model/layer1', 'model/layer2', 'data/batch1']
        """
        files = self.metadata_client.list_files()
        return list(files.keys())

    def list_files(self) -> dict[str, dict]:
        """
        列出所有已注册的文件及其详细元数据.

        Returns:
            dict[str, dict]: 包含文件信息的字典, key 为文件名, value 为元数据.

        Example:
            >>> client.list_files()
            {
                'model/layer1': {
                    'host': '10.0.0.1:5001',
                    'metadata': {
                        'object_type': 'numpy',
                        'data_size': 40000,
                        'tensor_shape': [100, 100],
                        'tensor_dtype': 'float32'
                    }
                }
            }
        """
        return self.metadata_client.list_files()

    def close(self) -> None:
        """关闭客户端，注销所有已注册的 key 并释放资源."""
        # 先注销 Metaserver 上的元数据
        for key in list(self._registered_keys):
            try:
                self.metadata_client.unregister_file(key)
                self.logger.debug("已注销 key: %s", key)
            except Exception as e:
                self.logger.warning("注销 key '%s' 失败: %s", key, e)
            # 释放本地 buffer
            self.transport.release(key)
        self._registered_keys.clear()

        # 关闭 Metadata Client
        # 停止 Etcd 的心跳续租线程，防止程序挂起
        if hasattr(self.metadata_client, "close"):
            self.metadata_client.close()

        # 关闭 Etcd 专用线程池，避免线程泄漏/进程无法退出
        executor = getattr(self, "_etcd_executor", None)
        if executor is not None:
            try:
                executor.shutdown(wait=True, cancel_futures=True)
                self.logger.debug("Etcd executor 已关闭")
            except Exception as e:
                self.logger.warning("关闭 Etcd executor 失败: %s", e)
            finally:
                self._etcd_executor = None

        self.logger.info("P2PClient 已关闭")
