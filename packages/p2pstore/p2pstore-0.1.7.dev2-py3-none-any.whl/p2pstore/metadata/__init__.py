"""
Metadata 模块 (仅支持 Etcd).
"""

from ..core import MetadataClient
from ..utils.config import P2PConfig

# Etcd Imports
try:
    from .etcd_client import EtcdMetadataClient
except ImportError:
    EtcdMetadataClient = None


def create_metadata_client(
    config: P2PConfig,
    local_ip: str,
    client_id: str,
    registered_keys: dict[str, int] | None = None,
) -> MetadataClient:
    """创建元数据客户端（仅支持 Etcd）."""
    metadata_type = (config.metadata_type or "etcd").lower()

    if metadata_type != "etcd":
        raise ValueError(f"不支持的元数据类型: {metadata_type}。当前版本仅支持 Etcd。")

    if EtcdMetadataClient is None:
        raise ImportError("请先安装 etcd3 库: pip install etcd3")

    if not config.etcd_endpoints:
        raise ValueError("使用 Etcd 模式必须配置 metadata_server=etcd://...")

    return EtcdMetadataClient(
        etcd_endpoints=config.etcd_endpoints,
        local_ip=local_ip,
        client_id=client_id,
        registered_keys=registered_keys,
        enable_watch=config.enable_watch,
        ttl=config.etcd_lease_ttl,
    )


__all__ = [
    "MetadataClient",
    "EtcdMetadataClient",
    "create_metadata_client",
]
