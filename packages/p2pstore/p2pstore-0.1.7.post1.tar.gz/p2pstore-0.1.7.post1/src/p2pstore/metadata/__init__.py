"""
Metadata 模块 (精简版).
"""

from ..core import MetadataClient, MetadataServer
from ..utils.config import P2PConfig

# ZMQ Imports
from .zmq_client import ZMQMetadataClient
from .zmq_server import ZMQMetadataServer

# Etcd Imports (只导入 Client)
try:
    from .etcd_client import EtcdMetadataClient
except ImportError:
    EtcdMetadataClient = None


def create_metadata_server(
    metadata_type: str = "zmq",
    sync_addr: str = None,
    coord_addr: str = None,
    etcd_endpoints: list[str] = None,
) -> MetadataServer:
    """
    创建元数据服务端.
    """
    metadata_type = metadata_type.lower()

    if metadata_type == "zmq":
        return ZMQMetadataServer(sync_addr=sync_addr, coord_addr=coord_addr)

    elif metadata_type == "etcd":
        # Etcd 模式下不需要 Python Server
        raise RuntimeError(
            "Etcd 模式不需要启动 Python Metaserver。\n"
            "请直接启动 Etcd 进程 (例如使用 Docker)，然后运行 Client 即可。"
        )

    raise ValueError(f"不支持的元数据服务类型: {metadata_type}")


def create_metadata_client(config: P2PConfig, local_ip: str) -> MetadataClient:
    """创建元数据客户端."""
    metadata_type = (config.metadata_type or "zmq").lower()

    if metadata_type == "zmq":
        if not config.sync_addr or not config.coord_addr:
            raise ValueError("使用 ZMQ metadata 需要配置 sync_addr 和 coord_addr")
        return ZMQMetadataClient(
            sync_addr=config.sync_addr,
            coord_addr=config.coord_addr,
            local_ip=local_ip,
        )

    elif metadata_type == "etcd":
        if EtcdMetadataClient is None:
            raise ImportError("请先安装 etcd3 库: pip install etcd3")
        if not config.etcd_endpoints:
            raise ValueError("使用 Etcd 模式必须配置 metadata_server=etcd://...")
        return EtcdMetadataClient(
            etcd_endpoints=config.etcd_endpoints,
            local_ip=local_ip,
            enable_watch=config.enable_watch,  # 传递 enable_watch 参数
        )

    raise ValueError(f"不支持的元数据类型: {config.metadata_type}")


__all__ = [
    "MetadataServer",
    "MetadataClient",
    "ZMQMetadataServer",
    "ZMQMetadataClient",
    "EtcdMetadataClient",
    "create_metadata_server",
    "create_metadata_client",
]
