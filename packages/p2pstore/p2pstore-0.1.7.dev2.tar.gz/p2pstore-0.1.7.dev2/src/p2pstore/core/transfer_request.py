"""
Transfer Request 模型模块.

该模块定义了 `TransferRequest` 数据类，用于封装一次数据传输请求所需的所有信息。
包括对象类型、数据大小、Tensor 形状/类型、文件路径、内存地址等。
它是 MetadataStore 和 Transport 层之间交互的标准数据结构。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass
class TransferRequest:
    """统一的数据传输请求模型, 与 new_client 结构保持一致."""

    object_type: str
    data_size: int
    tensor_shape: Tuple[int, ...] = ()
    tensor_dtype: Optional[str] = None
    file_path: str = ""
    buffer_ptr: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_metadata(self, file_key: str, host: str) -> Dict[str, Any]:
        """转换为用于注册的元数据字典."""
        payload = {
            "type": "file_register",
            "host": host,
            "file_key": file_key,
            "object_type": self.object_type,
            "data_size": self.data_size,
        }
        if self.tensor_shape:
            payload["tensor_shape"] = self.tensor_shape
        if self.tensor_dtype:
            payload["tensor_dtype"] = self.tensor_dtype
        if self.file_path:
            payload["source_path"] = self.file_path
        if self.buffer_ptr is not None:
            payload["buffer_ptr"] = self.buffer_ptr
        payload.update(self.metadata)
        return payload
