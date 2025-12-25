"""
Transfer Engine Mock 模块.

该模块提供了一个纯 Python 实现的 `TransferEngine` 类，用于模拟底层 C++ 传输引擎的行为。
主要用于在没有编译 C++ 扩展的环境中进行开发、测试和接口验证。
它实现了与真实引擎一致的接口 (initialize, register_memory, transfer_sync_read 等)。
"""

from __future__ import annotations

import itertools
from typing import Dict

from ..utils.logger import LoggerManager


class TransferEngine:
    """纯 Python 版 TransferEngine, 作为 RDMA 引擎的占位实现.

    该实现主要用于解耦 pythonSDK, 提供 initialize/register/unregister/transfer_read
    等方法, 以便上层 EngineAdapter/Transport 能够保持稳定接口。
    """

    _DEFAULT_PORT = 5755
    _PTR_COUNTER = itertools.count(1 << 32)

    def __init__(self) -> None:
        self.logger = LoggerManager.get_logger("transfer-engine")
        self.local_ip = ""
        self.device = ""
        self._port = self._DEFAULT_PORT
        self._registered: Dict[int, int] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def initialize(
        self, local_host: str, meta_server: str, protocol: str, device: str
    ) -> int:
        """初始化引擎 (Mock)."""
        self.device = device
        self.local_ip, self._port = self._parse_host(local_host)
        self.logger.info(
            "TransferEngine 初始化完成 (模拟). ip=%s port=%d protocol=%s meta=%s device=%s",
            self.local_ip,
            self._port,
            protocol,
            meta_server,
            device,
        )
        return 0

    def get_rpc_port(self) -> int:
        """获取 RPC 端口."""
        return self._port

    # ------------------------------------------------------------------
    # Memory registration (mock)
    # ------------------------------------------------------------------
    def register_memory(self, buffer_ptr: int, size: int) -> int:
        """注册内存 (Mock)."""
        self._registered[buffer_ptr] = size
        self.logger.debug("登记内存: ptr=%d size=%d", buffer_ptr, size)
        return 0

    def unregister_memory(self, buffer_ptr: int) -> None:
        """注销内存 (Mock)."""
        if buffer_ptr in self._registered:
            self.logger.debug("释放内存: ptr=%d", buffer_ptr)
            del self._registered[buffer_ptr]

    # ------------------------------------------------------------------
    # RDMA operations (mock)
    # ------------------------------------------------------------------
    def transfer_sync_read(
        self, remote_host: str, local_ptr: int, remote_ptr: int, size: int
    ) -> int:
        """执行同步读取 (Mock)."""
        self.logger.debug(
            "模拟 RDMA 读取: remote=%s remote_ptr=%d -> local_ptr=%d size=%d",
            remote_host,
            remote_ptr,
            local_ptr,
            size,
        )
        # 纯 Python 实现无法真正执行 RDMA, 但返回 0 代表接口调用成功
        return 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _parse_host(self, host: str):
        ip = host
        port = self._DEFAULT_PORT
        if ":" in host:
            ip_part, port_part = host.split(":", 1)
            ip = ip_part or "0.0.0.0"
            if port_part.isdigit():
                port = int(port_part)
        return ip, port
