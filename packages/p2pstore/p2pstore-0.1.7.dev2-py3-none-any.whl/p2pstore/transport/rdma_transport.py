"""
RDMA Transport 实现模块.

该模块实现了基于 RDMA 协议的传输层 `RDMATransport`。
它利用 `EngineAdapter` 与底层 RDMA 引擎交互，实现了高效的零拷贝数据传输。
支持 Tensor 和 Buffer 的注册、发送和接收。
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np

from ..core import BufferRegistry, TransferRequest, Transport
from ..utils.logger import LoggerManager
from .engine_adapter import EngineAdapter


class RDMATransport(Transport):
    """基于 pythonSDK EngineAdapter 的 RDMA 传输实现."""

    def __init__(self, meta_server: str):
        self._engine = EngineAdapter()
        self._buffers = BufferRegistry()
        self._meta_server = meta_server
        self._logger = LoggerManager.get_logger("rdma-transport")
        self._local_addr: Optional[str] = None

    def initialize(self, local_addr: str, device: str = "") -> bool:
        """初始化 RDMA 引擎."""
        try:
            self._local_addr = self._engine.initialize(
                local_addr, self._meta_server, "rdma", device
            )
            return True
        except Exception as exc:
            self._logger.error("RDMA 传输初始化失败: %s", exc, exc_info=True)
            return False

    def send(self, remote_addr: str, request: TransferRequest, data: Any) -> bool:
        try:
            file_key = request.metadata.get("file_key")
            if not file_key:
                raise ValueError("TransferRequest.metadata 必须包含 file_key")

            self._logger.debug(
                "[RDMA-SEND] 开始: key=%s, data_type=%s", file_key, type(data).__name__
            )
            buffer = self._get_zero_copy_buffer(data)
            request.buffer_ptr = buffer.ctypes.data
            request.data_size = buffer.nbytes
            self._logger.debug(
                "[RDMA-SEND] 零拷贝 buffer: key=%s, ptr=0x%x, size=%d, contiguous=%s",
                file_key,
                request.buffer_ptr,
                buffer.nbytes,
                buffer.flags["C_CONTIGUOUS"],
            )

            # 检查是否有同 key 的旧注册（覆盖场景）
            old_entry = self._buffers.get(file_key)
            if old_entry:
                old_ptr = old_entry.request.buffer_ptr
                if old_ptr == request.buffer_ptr:
                    # 相同 key + 相同地址 = 重复调用，直接返回成功
                    self._logger.info(
                        "[RDMA-SEND] key=%s 的地址 0x%x 已注册 (重复调用)，跳过",
                        file_key,
                        request.buffer_ptr,
                    )
                    return True
                else:
                    # 相同 key + 不同地址 = PUT 覆盖，先释放旧地址
                    self._logger.info(
                        "[RDMA-SEND] key=%s 覆盖注册: 0x%x -> 0x%x (size: %d -> %d)",
                        file_key,
                        old_ptr,
                        request.buffer_ptr,
                        old_entry.request.data_size,
                        request.data_size,
                    )
                    try:
                        self._engine.unregister(old_ptr)
                        self._logger.info(
                            "[RDMA-SEND] 旧地址已 unregister: key=%s, ptr=0x%x",
                            file_key,
                            old_ptr,
                        )
                    except Exception as e:
                        self._logger.warning(
                            "[RDMA-SEND] 旧地址 unregister 失败: key=%s, ptr=0x%x, error=%s",
                            file_key,
                            old_ptr,
                            e,
                        )
                    self._buffers.pop(file_key)

            # 尝试注册新内存
            try:
                self._engine.register(request.buffer_ptr, request.data_size)
                self._logger.debug(
                    "[RDMA-SEND] register 成功: key=%s, ptr=0x%x, size=%d",
                    file_key,
                    request.buffer_ptr,
                    request.data_size,
                )
            except RuntimeError as e:
                if "错误码: -7" in str(e):
                    # 地址被其他 key 占用（不应该发生，说明有 bug）
                    self._logger.error(
                        "[RDMA-SEND] ERR_ADDRESS_OVERLAPPED (-7): "
                        "地址 0x%x 已被其他 key 占用，拒绝注册 key=%s。"
                        "可能原因: 1) 其他 key 未正确释放 2) Watch 延迟导致竞态 3) 内存地址冲突",
                        request.buffer_ptr,
                        file_key,
                    )
                    # 打印当前 BufferRegistry 状态用于调试
                    self._logger.debug(
                        "[RDMA-SEND] 当前 BufferRegistry keys: %s",
                        list(self._buffers._entries.keys()),
                    )
                    return False
                self._logger.error(
                    "[RDMA-SEND] register 失败: key=%s, error=%s", file_key, e
                )
                raise

            self._buffers.add(file_key, buffer, request)
            self._logger.info(
                "[RDMA-SEND] 完成: key=%s, ptr=0x%x, size=%d, total_buffers=%d",
                file_key,
                request.buffer_ptr,
                buffer.nbytes,
                len(self._buffers._entries),
            )
            return True

        except Exception as exc:
            self._logger.error(
                "[RDMA-SEND] 异常: key=%s, error=%s", file_key, exc, exc_info=True
            )
            return False

    def _get_zero_copy_buffer(self, data: Any) -> np.ndarray:
        """获取数据的 Numpy 视图，尽可能避免拷贝。"""
        # 如果是 Numpy 数组
        if isinstance(data, np.ndarray):
            # RDMA 通常要求内存物理连续。
            # 如果不是连续的 (比如切片 data[:, ::2])，则必须拷贝。
            if not data.flags["C_CONTIGUOUS"]:
                self._logger.warning("检测到非连续内存，执行拷贝以适配 RDMA")
                return np.ascontiguousarray(data)
            return data

        # 如果是 Paddle Tensor，转换为 Numpy (通常在 CPU 上是零拷贝的)
        if hasattr(data, "numpy"):
            data = data.numpy()

        # 如果是 bytes/bytearray (序列化后的对象)
        if isinstance(data, (bytes, bytearray, memoryview)):
            # frombuffer 创建只读视图，不发生拷贝
            # 注意: RDMA register 如果是只读注册，这里是安全的。
            # 如果底层 engine 需要写入权限，可能需要 copy，但作为 Sender (Provider) 通常是只读。
            return np.frombuffer(data, dtype=np.uint8)

        raise TypeError(f"RDMA 不支持的数据类型: {type(data)}")

    def recv(self, request: TransferRequest, remote_addr: Optional[str] = None) -> Any:
        """从远程 RDMA 节点拉取数据 (Consumer)."""
        if remote_addr is None:
            raise ValueError("RDMA recv 需要 remote_addr")

        file_key = request.metadata.get("file_key", "unknown")
        client_id = request.metadata.get("client_id", "unknown")
        self._logger.debug(
            "[RDMA-RECV] 开始: key=%s, remote=%s(client_id=%s), remote_ptr=0x%x, size=%d",
            file_key,
            remote_addr,
            client_id,
            request.buffer_ptr or 0,
            request.data_size,
        )

        if request.buffer_ptr is None:
            raise ValueError("缺少远端 buffer_ptr, 无法执行 RDMA 读取")

        # 远程 RDMA 传输
        local_buffer = np.empty(request.data_size, dtype=np.uint8)
        local_ptr = local_buffer.ctypes.data

        self._logger.debug(
            "[RDMA-RECV] 注册本地 buffer: key=%s, local_ptr=0x%x, size=%d",
            file_key,
            local_ptr,
            request.data_size,
        )
        self._engine.register(local_ptr, request.data_size)

        try:
            self._engine.transfer_read(
                remote_host=remote_addr,
                local_ptr=local_ptr,
                remote_ptr=request.buffer_ptr,
                size=request.data_size,
            )
            self._logger.info(
                "[RDMA-RECV]  : 执行 transfer_read 完成: key=%s, remote=%s(client_id=%s)",
                file_key,
                remote_addr,
                client_id,
            )
            return local_buffer
        except Exception as e:
            self._logger.error(
                "[RDMA-RECV] transfer_read 失败: key=%s, remote=%s(client_id=%s), error=%s",
                file_key,
                remote_addr,
                client_id,
                e,
                exc_info=True,
            )
            raise
        finally:
            self._logger.debug(
                "[RDMA-RECV] 注销本地 buffer: key=%s, local_ptr=0x%x",
                file_key,
                local_ptr,
            )
            self._engine.unregister(local_ptr)

    def get_local_addr(self) -> str:
        """获取本地 RDMA 地址."""
        if not self._local_addr:
            raise RuntimeError("RDMATransport 尚未初始化")
        return self._local_addr

    def release(self, key: str) -> None:
        """释放已注册的 RDMA 内存."""
        self._logger.debug(
            "[RDMA-RELEASE] 尝试释放: key=%s, buffers_count=%d",
            key,
            len(self._buffers._entries),
        )

        entry = self._buffers.pop(key)
        if entry and entry.request.buffer_ptr is not None:
            ptr = entry.request.buffer_ptr
            size = entry.request.data_size
            self._logger.debug(
                "[RDMA-RELEASE] 找到 buffer: key=%s, ptr=0x%x, size=%d", key, ptr, size
            )
            try:
                self._engine.unregister(ptr)
                self._logger.info(
                    "[RDMA-RELEASE] 已释放: key=%s, ptr=0x%x, remaining_buffers=%d",
                    key,
                    ptr,
                    len(self._buffers._entries),
                )
            except Exception as exc:
                # 可能已经被释放过，忽略错误
                self._logger.warning(
                    "[RDMA-RELEASE] unregister 失败 (可能已释放): key=%s, ptr=0x%x, error=%s",
                    key,
                    ptr,
                    exc,
                )
        else:
            self._logger.debug(
                "[RDMA-RELEASE] buffer 不存在或已释放: key=%s (entry=%s)",
                key,
                entry is not None,
            )

    def _ensure_numpy_buffer(self, data: Any) -> np.ndarray:
        """确保数据为连续的 numpy 数组 (uint8)."""
        if isinstance(data, np.ndarray):
            return data if data.dtype == np.uint8 else data.view(np.uint8)
        if isinstance(data, (bytes, bytearray, memoryview)):
            return np.frombuffer(data, dtype=np.uint8).copy()
        raise TypeError(f"RDMA 仅支持 numpy.ndarray/bytes 数据, 当前类型: {type(data)}")
