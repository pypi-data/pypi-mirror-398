"""
Transport 接口定义模块.

该模块定义了 `Transport` 抽象基类，规范了底层数据传输层的行为。
所有的传输协议实现 (如 RDMA, TCP 等) 都必须继承此类并实现其抽象方法。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from .transfer_request import TransferRequest


class Transport(ABC):
    """传输层抽象基类, 定义数据传输接口."""

    @abstractmethod
    def initialize(self, local_addr: str, device: str = "") -> bool:
        """初始化传输层."""
        pass

    @abstractmethod
    def send(self, remote_addr: str, request: TransferRequest, data: Any) -> bool:
        """发送/注册数据."""
        pass

    @abstractmethod
    def recv(self, request: TransferRequest, remote_addr: Optional[str] = None) -> Any:
        """接收/获取数据."""
        pass

    @abstractmethod
    def get_local_addr(self) -> str:
        """获取本地传输地址."""
        pass

    @abstractmethod
    def release(self, key: str) -> None:
        """释放与指定 key 关联的本地资源."""
        pass
