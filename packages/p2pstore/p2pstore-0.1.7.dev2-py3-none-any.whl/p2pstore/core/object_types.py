"""
Object Types 定义模块.

该模块定义了 Mooncake 系统中支持的传输对象类型枚举 `ObjectType`。
包括文件 (FILE)、Tensor (TENSOR)、SafeTensors (SAFETENSORS) 等。
"""

from enum import Enum


class ObjectType(str, Enum):
    """支持的传输对象类型枚举."""

    FILE = "file"
    TENSOR = "tensor"
    SAFETENSORS = "safetensors"
    OBJECT = "object"
