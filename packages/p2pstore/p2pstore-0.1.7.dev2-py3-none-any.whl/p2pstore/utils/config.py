"""
Configuration 模块.

该模块定义了 P2P 系统的统一配置类 `P2PConfig`。
Server 和 Client 共用同一配置类，用于集中管理所有可配置参数。

"""

import os
from dataclasses import dataclass


@dataclass
class P2PConfig:
    """
    P2P Store 统一配置类（仅支持 Etcd）.

    核心属性:
        metadata_server: Etcd 服务器地址，格式:
                         "etcd://ip:port,ip:port,..."
                         例如: "etcd://10.0.0.1:2379,10.0.0.2:2379"
        local_host: 本地地址，默认从环境变量 POD_IP 获取

    传输属性:
        protocol: 传输协议 (rdma/tcp)
        device: RDMA 设备名

    Usage:
        config = P2PConfig(metadata_server="etcd://10.0.0.1:2379")
        client = P2PClient(config)
    """

    # 核心配置 (必填)
    metadata_server: str  # 格式: "etcd://ip:port,..."
    local_host: str = ""

    # 内部使用，自动从 metadata_server 解析
    metadata_type: str = "etcd"
    etcd_endpoints: list[str] | None = None

    # transport
    protocol: str = "rdma"
    device: str = "mlx5_3"
    meta_server: str = "P2PHANDSHAKE"

    # common
    max_retries: int = 3
    retry_interval: int = 5
    log_name: str | None = None
    enable_watch: bool = True  # 是否启用 Etcd Watch (Consumer get 节点设为 False)
    etcd_lease_ttl: int = 3600  # Etcd 租约 TTL (秒)，默认 1小时

    def __post_init__(self) -> None:
        """初始化后处理."""
        # 优先使用环境变量中的 TTL 设置
        if os.getenv("P2P_ETCD_LEASE_TTL"):
            try:
                self.etcd_lease_ttl = int(os.environ["P2P_ETCD_LEASE_TTL"])
            except ValueError:
                pass

        # 自动填充 local_host
        if not self.local_host:
            self.local_host = os.getenv("POD_IP", "").strip() or "127.0.0.1"

        # 解析 metadata_server，仅支持 etcd://
        server = self.metadata_server.strip()
        if server.startswith("etcd://"):
            self.metadata_type = "etcd"
            self._parse_etcd_addr(server[7:])  # 去掉 "etcd://"
        else:
            raise ValueError(
                f"配置错误: metadata_server 格式错误 '{server}'，"
                "当前版本仅支持 Etcd，应以 'etcd://' 开头，"
                "例如: 'etcd://127.0.0.1:2379'"
            )

    def _parse_etcd_addr(self, addr: str) -> None:
        """解析 etcd 模式的地址."""
        endpoints = []

        for endpoint in addr.split(","):
            endpoint = endpoint.strip()
            if not endpoint:
                continue
            if not endpoint.startswith(("http://", "https://")):
                endpoint = f"http://{endpoint}"
            endpoints.append(endpoint)

        if not endpoints:
            raise ValueError(
                f"配置错误: metadata_server 格式错误 '{self.metadata_server}'"
            )

        self.etcd_endpoints = endpoints
