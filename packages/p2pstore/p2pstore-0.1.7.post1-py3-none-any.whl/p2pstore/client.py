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

        self._registered_keys = set()

        # 对于 RDMA 协议，根据是否指定设备决定拓扑策略
        if config.protocol == "rdma":
            if config.device:
                # 指定了设备，清除拓扑环境变量，让 Transfer Engine 直接用指定设备
                os.environ.pop("MC_CUSTOM_TOPO_JSON", None)
            else:
                # 未指定设备，自动设置拓扑环境变量
                setup_topology_env(include_cuda=True)

        local_ip = config.local_host.split(":")[0]
        self.metadata_client = create_metadata_client(config, local_ip)
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
            existing_client = existing.get("client_id", "unknown")
            self.logger.info(
                "[PUT] 检测到 key=%s 已存在 (host=%s, client=%s)，准备覆盖",
                key,
                existing_host,
                existing_client,
            )
            # 先同步释放本地内存，避免与 Watch 线程竞态
            if key in self._registered_keys:
                self.logger.debug(
                    "[PUT] key=%s 在本地 _registered_keys，主线程同步释放内存",
                    key,
                )
                try:
                    self.transport.release(key)
                    self._registered_keys.discard(key)
                    self.logger.debug("[PUT] 主线程已同步释放旧内存: %s", key)
                except Exception as e:
                    self.logger.error(
                        "[PUT] 释放旧内存失败: key=%s, error=%s", key, e
                    )
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
        # 在元数据中记录 client_id
        metadata["client_id"] = self.client_id

        self.logger.debug(
            "[PUT] 注册 Etcd 元数据: key=%s, host=%s, metadata=%s",
            key,
            self.transport.get_local_addr(),
            metadata,
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

        self._registered_keys.add(key)
        elapsed = time.perf_counter() - start_time
        self.logger.info(
            "[PUT] 完成注册: key=%s host=%s client_id=%s (total_keys=%d) 耗时: %.4fs",
            key,
            self.transport.get_local_addr(),
            self.client_id,
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

    def _on_file_unregister(self, key: str) -> None:
        """收到 file_unregister 广播时的回调, 释放本地 buffer."""
        self.logger.debug(
            "[WATCH-CALLBACK] 收到 unregister 广播: key=%s, 检查 _registered_keys (size=%d)",
            key,
            len(self._registered_keys),
        )
        if key in self._registered_keys:
            # Watch 线程的异步清理（如果主线程已经同步释放，这里会安全跳过）
            self.transport.release(key)
            self._registered_keys.discard(key)
            self.logger.debug(
                "[WATCH-CALLBACK] key=%s 在 _registered_keys, 已释放本地 buffer (remaining_keys=%d)",
                key,
                len(self._registered_keys),
            )
        else:
            self.logger.debug(
                "[WATCH-CALLBACK] key=%s 不在 _registered_keys，跳过释放 (非本节点数据或已被主线程释放)",
                key,
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

        # 检查本地持久化目录
        local_dir = self.config.persistence_dir
        if local_dir:
            local_path = os.path.join(local_dir, key)
            
            # 检查文件是否存在
            loop = asyncio.get_running_loop()
            file_exists = await loop.run_in_executor(None, os.path.exists, local_path)

            if file_exists:
                self.logger.info(f"[GET] 命中本地持久化缓存: {local_path}")
                try:
                    def _load_as_numpy():
                        # 如果存的是 raw bytes (默认)
                        # 注意：因为没有元数据，这里默认转为 uint8 的一维数组，
                        # 或者你可以根据经验指定 dtype (例如 np.float32)
                        arr = np.fromfile(local_path, dtype=np.int32).reshape(-1, 8)
                        return arr

                    arr = await loop.run_in_executor(None, _load_as_numpy)
                    
                    if arr is not None:
                        return arr
                except Exception as e:
                    self.logger.warning(f"[GET] 读取本地缓存失败: {e}, 转为网络获取")

        if inplace_tensor is not None and hasattr(inplace_tensor, "place"):
            self.logger.debug("[GET] inplace_tensor device: %s", inplace_tensor.place)
        entry = await self._query_with_retry(key)
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

        self.logger.debug(
            "[GET] RDMA 传输准备: key=%s, remote=%s, client_id=%s, ptr=0x%x, size=%d bytes",
            key,
            provider_addr,
            client_id,
            request.buffer_ptr or 0,
            data_size,
        )

        # RDMA 传输带超时和重试逻辑
        max_recv_retries = 3
        recv_timeout = 30.0  # RDMA 传输超时时间（秒）
        payload = None

        for attempt in range(max_recv_retries):
            try:
                self.logger.debug(
                    "[GET] RDMA 传输尝试 %d/%d: key=%s from %s (client_id=%s)",
                    attempt + 1,
                    max_recv_retries,
                    key,
                    provider_addr,
                    client_id,
                )

                loop = asyncio.get_running_loop()
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
                    break
                else:
                    self.logger.warning(
                        "[GET] RDMA 传输返回 None: key=%s, 尝试 %d/%d",
                        key,
                        attempt + 1,
                        max_recv_retries,
                    )

            except asyncio.TimeoutError:
                self.logger.error(
                    "[GET] RDMA 传输超时: key=%s from %s (client_id=%s), 超时 %.1fs, 尝试 %d/%d",
                    key,
                    provider_addr,
                    client_id,
                    recv_timeout,
                    attempt + 1,
                    max_recv_retries,
                )
            except Exception as e:
                self.logger.error(
                    "[GET] RDMA 传输异常: key=%s from %s (client_id=%s), error=%s, 尝试 %d/%d",
                    key,
                    provider_addr,
                    client_id,
                    e,
                    attempt + 1,
                    max_recv_retries,
                )

            # 如果不是最后一次尝试，等待后重试
            if attempt < max_recv_retries - 1 and payload is None:
                retry_wait = 2.0
                self.logger.info(
                    "[GET] 等待 %.1fs 后重试 RDMA 传输: key=%s",
                    retry_wait,
                    key,
                )
                await asyncio.sleep(retry_wait)

        if payload is None:
            self.logger.error(
                "[GET] RDMA 传输最终失败: key=%s from %s (client_id=%s), 已尝试 %d 次",
                key,
                provider_addr,
                client_id,
                max_recv_retries,
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
        entry = await self._query_with_retry(key, retries=1)
        return entry is not None

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------
    async def _query_with_retry(
        self, key: str, retries: int | None = None
    ) -> dict | None:
        max_retries = retries if retries is not None else self.config.max_retries

        # 策略: 首次等待 3s, 之后每次增加 retry_interval (配置值, 默认5s)
        # retry_interval 是配置里的重试间隔，这里用作退避增量
        increment = self.config.retry_interval if self.config.retry_interval > 0 else 5
        wait_time = 3
        self.logger.debug(
            "[QUERY] 查询 key=%s, 最多重试 %d 次, 初始等待 %ds, 增量 %ds",
            key,
            max_retries,
            wait_time,
            increment,
        )
        for i in range(max_retries + 1):
            # 防止 query_file 本身 hang 住 (例如网络分区)
            # 使用 run_in_executor 将同步调用放入专用线程池，避免阻塞主循环
            # 并设置 5s 的硬超时
            try:
                self.logger.info(
                    "[QUERY] 开始调用 etcd query_file: key=%s, 尝试 %d/%d",
                    key,
                    i + 1,
                    max_retries + 1,
                )
                loop = asyncio.get_running_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        self._etcd_executor, self.metadata_client.query_file, key
                    ),
                    timeout=5.0,
                )
                self.logger.info(
                    "[QUERY] etcd query_file 返回: key=%s, found=%s",
                    key,
                    result is not None,
                )

            except asyncio.TimeoutError:
                self.logger.warning(
                    "查询 key=%s 底层调用 etadata_client.query_file 超时 (5s)", key
                )
                result = None
            except Exception as e:
                self.logger.warning("查询 key=%s 异常: %s", key, e)
                result = None

            if result:
                return result

            if i < max_retries:
                self.logger.info(
                    "数据 %s 未就绪, 等待重试 %d/%d (间隔 %ds)...",
                    key,
                    i + 1,
                    max_retries,
                    wait_time,
                )
                await asyncio.sleep(wait_time)
                wait_time += increment

        self.logger.error("数据 %s 不存在 (已重试 %d 次)", key, max_retries)
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
        self, key: str, request: TransferRequest
    ) -> dict[str, Any]:
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
        self, key: str, metadata: dict[str, Any]
    ) -> TransferRequest | None:
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
        inplace_tensor: Any | None,
    ) -> Any:
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
    def list(self) -> dict[str, dict]:
        """
        列出所有已注册的文件.

        Returns:
            dict[str, dict]: 包含文件信息的字典, key 为文件名, value 为元数据.
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
