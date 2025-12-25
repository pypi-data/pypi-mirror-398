"""transport 模块负责不同传输协议的实现与选择"""

from ..core import Transport
from ..utils.config import P2PConfig
from .rdma_transport import RDMATransport
from .tcp_transport import TCPTransport


def create_transport(config: P2PConfig) -> Transport:
    """根据配置创建对应的 Transport 实例."""

    protocol = (config.protocol or "rdma").lower()
    if protocol == "rdma":
        return RDMATransport(meta_server=config.meta_server)
    if protocol == "tcp":
        return TCPTransport()
    raise ValueError(f"不支持的传输协议: {config.protocol}")


__all__ = ["create_transport", "RDMATransport", "TCPTransport"]
