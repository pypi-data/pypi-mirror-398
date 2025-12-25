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
    P2P Store 统一配置类，Server 和 Client 共用.

    核心属性:
        metadata_server: Metaserver 地址，格式根据类型不同:
                         - ZMQ: "zmq://ip:sync_port,ip:coord_port"
                           例如: "zmq://10.54.96.90:5765,10.54.96.90:5766"
                         - Etcd: "etcd://ip:port,ip:port,..."
                           例如: "etcd://10.0.0.1:2379,10.0.0.2:2379"
        local_host: 本地地址，默认从环境变量 POD_IP 获取

    传输属性:
        protocol: 传输协议 (rdma/tcp)
        device: RDMA 设备名

    内部属性 (自动生成):
        metadata_type: 元数据服务类型 (zmq/etcd)
        sync_addr: ZMQ PUB/SUB 地址
        coord_addr: ZMQ ROUTER/DEALER 地址

    Usage:
        # Server 和 Client 使用相同配置
        config = P2PConfig(metadata_server="zmq://10.0.0.1:5765,10.0.0.1:5766")
        server = P2PServer(config)
        client = P2PClient(config)
    """

    # 核心配置 (必填)
    metadata_server: str  # 格式: "zmq://ip:port,ip:port" 或 "etcd://ip:port,..."
    local_host: str = ""

    # 内部使用，自动从 metadata_server 解析
    metadata_type: str = ""
    sync_addr: str | None = None
    coord_addr: str | None = None
    etcd_endpoints: list[str] | None = None
    persistence_dir: str | None = None

    # transport
    protocol: str = "rdma"
    device: str = "mlx5_3"
    meta_server: str = "P2PHANDSHAKE"

    # common
    max_retries: int = 3
    retry_interval: int = 5
    log_name: str | None = None
    enable_watch: bool = True  # 是否启用 Etcd Watch (Consumer get 节点设为 False)

    def __post_init__(self) -> None:
        """初始化后处理."""
        # 自动填充 local_host
        if not self.local_host:
            self.local_host = os.getenv("POD_IP", "").strip() or "127.0.0.1"

        # 解析 metadata_server，格式: "zmq://..." 或 "etcd://..."
        server = self.metadata_server.strip()
        if server.startswith("zmq://"):
            self.metadata_type = "zmq"
            self._parse_zmq_addr(server[6:])  # 去掉 "zmq://"
        elif server.startswith("etcd://"):
            self.metadata_type = "etcd"
            self._parse_etcd_addr(server[7:])  # 去掉 "etcd://"
        else:
            raise ValueError(
                f"配置错误: metadata_server 格式错误 '{server}'，应以 'zmq://' 或 'etcd://' 开头"
            )

    def _parse_zmq_addr(self, addr: str) -> None:
        """解析 ZMQ 模式的地址，格式: "ip:sync_port,ip:coord_port"."""
        if "," not in addr:
            raise ValueError(
                f"配置错误: metadata_server 格式错误 '{self.metadata_server}'，"
                "ZMQ 格式应为 'zmq://ip:sync_port,ip:coord_port'，"
                "例如 'zmq://10.0.0.1:5765,10.0.0.1:5766'"
            )

        parts = [p.strip() for p in addr.split(",")]
        if len(parts) != 2:
            raise ValueError(
                f"配置错误: metadata_server 格式错误 '{self.metadata_server}'，"
                "ZMQ 格式应为 'zmq://ip:sync_port,ip:coord_port'"
            )

        sync_part, coord_part = parts

        # 验证两个地址格式
        for part in (sync_part, coord_part):
            if ":" not in part:
                raise ValueError(
                    f"配置错误: metadata_server 格式错误 '{self.metadata_server}'，'{part}' 缺少端口号"
                )

        self.sync_addr = f"tcp://{sync_part}"
        self.coord_addr = f"tcp://{coord_part}"

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
