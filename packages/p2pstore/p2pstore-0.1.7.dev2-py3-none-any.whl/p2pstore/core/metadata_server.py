"""
Metadata Server 接口定义模块.

该模块定义了 `MetadataServer` 抽象基类，规范了元数据服务端的行为。
所有的元数据服务器实现 (如 ZMQ, Etcd 等) 都必须继承此类并实现其抽象方法。
"""

from abc import ABC, abstractmethod


class MetadataServer(ABC):
    """
    元数据服务器抽象基类.

    定义了元数据服务器的标准接口，支持多实现插拔 (ZMQ, Etcd, Redis 等)。
    元数据服务器负责：
    1. 接收和广播元数据消息
    2. 处理客户端的查询请求
    3. 维护 Provider 和文件的注册信息
    """

    @abstractmethod
    def get_stats(self) -> dict:
        """
        获取服务器当前状态统计.

        Returns:
            dict: 包含以下字段:
                - providers: int, 注册的 Provider 数量
                - files: int, 注册的文件数量
                - provider_list: list[str], Provider 地址列表
                - file_list: list[str], 文件 key 列表
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """关闭服务器并释放资源."""
        pass

    def __enter__(self) -> "MetadataServer":
        """支持 context manager 协议."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出时自动关闭."""
        self.close()
