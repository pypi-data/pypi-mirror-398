"""
P2P Store Server 模块.

该模块提供了 P2P Store 系统的元数据服务器入口 `P2PServer`。
它封装了底层的 MetadataServer 实现，提供统一的启动/停止/状态查询接口。
"""

from __future__ import annotations

import re
import signal
import time

from .metadata import create_metadata_server
from .utils import LoggerManager, P2PConfig


class P2PServer:
    """
    P2P Store 元数据服务器.

    封装了 MetadataServer 的创建和生命周期管理。
    直接从 P2PConfig.metadata_server 解析绑定地址。

    Usage:
        ```python
        config = P2PConfig(metadata_server="zmq://10.0.0.1:5765,10.0.0.1:5766")
        server = P2PServer(config)
        server.start()  # 阻塞运行
        ```
    """

    def __init__(self, config: P2PConfig):
        """
        初始化 P2P Server.

        Args:
            config: 服务器配置，如果为 None 则使用默认配置
        """
        self.config = config
        self.logger = LoggerManager.get_logger(self.config.log_name or "p2p-server")
        self._server = None
        self._running = False

        self._bind_sync_addr = self.config.sync_addr
        self._bind_coord_addr = self.config.coord_addr

    @staticmethod
    def _extract_port(addr: str | None) -> str:
        """从地址中提取端口."""
        if not addr:
            return "5765"
        match = re.search(r":(\d+)$", addr)
        return match.group(1) if match else "5765"

    @property
    def metadata_server(self) -> str:
        """返回配置中的 metadata_server."""
        return self.config.metadata_server

    def start(self, block: bool = True) -> None:
        """
        启动服务器.

        Args:
            block: 是否阻塞运行。如果为 True，会阻塞直到收到 SIGINT/SIGTERM
        """
        self.logger.info("=" * 50)
        self.logger.info("P2P Store Server")
        self.logger.info("=" * 50)
        self.logger.info("Metadata Type: %s", self.config.metadata_type)
        self.logger.info(
            "Bind Addr:     %s, %s", self._bind_sync_addr, self._bind_coord_addr
        )
        self.logger.info("Metaserver:    %s", self.metadata_server)
        self.logger.info("=" * 50)

        # 创建 MetadataServer
        self._server = create_metadata_server(
            metadata_type=self.config.metadata_type,
            sync_addr=self._bind_sync_addr,
            coord_addr=self._bind_coord_addr,
        )
        self._running = True

        self.logger.info("服务已启动")

        if block:
            self._run_blocking()

    def _run_blocking(self) -> None:
        """阻塞运行，处理信号."""

        def signal_handler(signum, frame):
            self.logger.info("收到信号 %s，正在停止...", signum)
            self.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        self.logger.info("按 Ctrl+C 停止服务")

        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """停止服务器."""
        if not self._running:
            return

        self._running = False

        if self._server:
            stats = self.get_stats()
            self.logger.info(
                "最终统计: %d 个 Provider, %d 个文件",
                stats["providers"],
                stats["files"],
            )
            self._server.close()
            self._server = None

        self.logger.info("服务已停止")

    def get_stats(self) -> dict:
        """
        获取服务器状态.

        Returns:
            dict: 包含 providers, files, provider_list, file_list
        """
        if self._server:
            return self._server.get_stats()
        return {"providers": 0, "files": 0, "provider_list": [], "file_list": []}

    def __enter__(self):
        """支持 context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出时自动停止."""
        self.stop()
