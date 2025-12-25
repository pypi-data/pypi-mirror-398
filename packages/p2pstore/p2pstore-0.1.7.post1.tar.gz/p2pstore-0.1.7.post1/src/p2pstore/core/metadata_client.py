"""
Metadata Client 接口定义模块.

该模块定义了 `MetadataClient` 抽象基类，规范了元数据客户端的行为。
所有的元数据客户端实现 (如 ZMQ, Etcd 等) 都必须继承此类并实现其抽象方法。
"""

from abc import ABC, abstractmethod


class MetadataClient(ABC):
    """元数据客户端抽象基类, 支持多实现插拔"""

    @abstractmethod
    def register_provider(self, host: str) -> None:
        """注册 Provider 节点."""
        pass

    @abstractmethod
    def unregister_provider(self, host: str) -> None:
        """注销 Provider 节点."""
        pass

    @abstractmethod
    def update_heartbeat(self, host: str) -> None:
        """更新 Provider 心跳."""
        pass

    @abstractmethod
    def register_file(self, file_key: str, host: str, metadata: dict) -> bool:
        """
        注册文件元数据.

        Returns:
            bool: 注册是否成功
        """
        pass

    @abstractmethod
    def unregister_file(self, file_key: str) -> None:
        """注销文件元数据 (仅本地, 用于 put 后清理)."""
        pass

    @abstractmethod
    def delete_file(self, file_key: str) -> bool:
        """
        删除文件 (发送到 Metaserver, 广播给所有节点).

        Returns:
            bool: 删除是否成功
        """
        pass

    @abstractmethod
    def delete_prefix(self, prefix: str) -> bool:
        """
        根据前缀删除文件 (发送到 Metaserver, 广播给所有节点).

        Args:
            prefix: 文件 key 的前缀

        Returns:
            bool: 删除是否成功
        """
        pass

    @abstractmethod
    def delete_prefix_batch(self, prefixes: list[str]) -> dict[str, bool]:
        """
        批量根据前缀删除文件.

        Args:
            prefixes: 前缀列表

        Returns:
            dict[str, bool]: 每个前缀的删除结果
        """
        pass

    def set_release_callback(self, callback) -> None:
        """
        设置 buffer 释放回调函数.
        当收到 file_unregister 广播时, 调用此回调释放本地 buffer.

        Args:
            callback: 回调函数, 签名为 callback(file_key: str) -> None
        """
        pass

    def close(self) -> None:  # pragma: no cover - 默认 no-op，具体实现可覆盖
        """关闭元数据客户端并释放资源.

        说明：
        - 部分实现（如 Etcd）会启动后台线程（watch/keep-alive），需要显式 close。
        - 其他实现可以保持默认 no-op。
        """
        return None

    @abstractmethod
    def check_connection(self, timeout_ms: int = 3000) -> bool:
        """
        检查与 Metaserver 的连通性.

        Args:
            timeout_ms: 超时时间（毫秒）

        Returns:
            bool: 连通返回 True，否则 False
        """
        pass

    @abstractmethod
    def query_file(self, file_key: str) -> dict | None:
        """查询文件元数据."""
        pass

    @abstractmethod
    def update_load(self, host: str, delta: int) -> None:
        """更新节点负载."""
        pass

    @abstractmethod
    def list_files(self) -> dict[str, dict]:
        """列出所有文件."""
        pass

    @abstractmethod
    def get_prefix(self, prefix: str) -> dict[str, dict]:
        """
        根据前缀获取文件元数据.

        Args:
            prefix: 文件 key 的前缀

        Returns:
            Dict[str, Dict]: 文件元数据字典
        """
        pass

    @abstractmethod
    def clear_files(self) -> dict:
        """
        清空所有文件元数据.

        Returns:
            Dict: {"success": bool, "cleared": int, "failed": List[str]}
        """
        pass
