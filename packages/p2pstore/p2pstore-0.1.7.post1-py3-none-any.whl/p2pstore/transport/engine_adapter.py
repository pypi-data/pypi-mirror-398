"""
Engine Adapter 模块.

该模块提供了 `EngineAdapter` 类，用于适配底层的传输引擎 (TransferEngine)。
它将 Python 层的调用转换为底层引擎 (通常是 C++ 实现或其 Mock) 的接口调用，
负责处理初始化、内存注册/注销、RDMA 读取等底层操作。
"""

from __future__ import annotations

from typing import Any, Optional

from mooncake.engine import TransferEngine

from ..utils.logger import LoggerManager


class EngineAdapter:
    """适配底层 TransferEngine (C++ / Mock) 的接口封装."""

    def __init__(self) -> None:
        self._engine = TransferEngine()
        self._logger = LoggerManager.get_logger("engine-adapter")
        self.local_host: Optional[str] = None

    def initialize(
        self, local_host: str, meta_server: str, protocol: str, device: str
    ) -> str:
        """初始化引擎并返回实际绑定的地址."""
        ret = self._engine.initialize(local_host, meta_server, protocol, device)
        if ret != 0:
            raise RuntimeError(f"TransferEngine 初始化失败, 错误码: {ret}")
        port = self._engine.get_rpc_port()
        self.local_host = f"{local_host.split(':')[0]}:{port}"
        self._logger.info("TransferEngine 初始化成功, 地址: %s", self.local_host)
        return self.local_host

    def register(self, buffer_ptr: int, size: int) -> None:
        """注册内存到 RDMA 引擎."""
        ret = self._engine.register_memory(buffer_ptr, size)
        if ret != 0:
            raise RuntimeError(f"RDMA 内存注册失败, 错误码: {ret}")

    def unregister(self, buffer_ptr: int) -> None:
        """从 RDMA 引擎注销内存."""
        try:
            self._engine.unregister_memory(buffer_ptr)
        except Exception as exc:
            self._logger.warning("RDMA 内存注销失败: %s", exc)

    def transfer_read(
        self, remote_host: str, local_ptr: int, remote_ptr: int, size: int
    ) -> None:
        """执行 RDMA Read 操作."""
        ret = self._engine.transfer_sync_read(remote_host, local_ptr, remote_ptr, size)
        if ret != 0:
            raise RuntimeError(f"RDMA 传输失败, 错误码: {ret}")

    def raw_engine(self) -> Any:
        """获取底层引擎实例."""
        return self._engine
