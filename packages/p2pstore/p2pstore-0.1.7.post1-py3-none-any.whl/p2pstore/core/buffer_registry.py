"""
Buffer Registry 模块.

该模块提供了 `BufferRegistry` 类，用于管理本地注册的内存缓冲区 (BufferEntry)。
主要用于防止 Python 对象 (如 numpy array) 在传输完成前被垃圾回收 (GC)，
同时维护了 key 到 buffer 的映射关系。
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .transfer_request import TransferRequest


@dataclass
class BufferEntry:
    """缓存条目, 包含原始数据对象和传输请求信息."""

    backing: Any
    request: TransferRequest


class BufferRegistry:
    """管理本地注册的内存缓冲区, 防止被 GC 回收."""

    def __init__(self) -> None:
        self._entries: Dict[str, BufferEntry] = {}

    def add(self, key: str, backing: Any, request: TransferRequest) -> None:
        """添加缓冲区记录."""
        self._entries[key] = BufferEntry(backing=backing, request=request)

    def pop(self, key: str) -> Optional[BufferEntry]:
        """移除并返回缓冲区记录."""
        return self._entries.pop(key, None)

    def get(self, key: str) -> Optional[BufferEntry]:
        """获取缓冲区记录."""
        return self._entries.get(key)

    def items(self):
        """返回所有缓冲区记录."""
        return self._entries.items()
