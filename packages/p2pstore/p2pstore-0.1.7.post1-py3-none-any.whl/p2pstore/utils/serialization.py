"""
Serialization Utils 模块.

该模块提供了数据序列化和反序列化的辅助函数。
主要处理 Paddle Tensor 与 Numpy Array/Bytes 之间的转换，以及文件读取等操作。
支持延迟加载 Paddle 模块以减少硬依赖。
"""

from __future__ import annotations

import io
import pickle
from typing import Any

import numpy as np

try:  # pragma: no cover
    import paddle as _paddle_mod  # type: ignore
except ImportError as _paddle_exc:
    _paddle_mod = None
else:
    _paddle_exc = None


def get_paddle():
    """延迟获取 paddle 模块, 避免硬依赖."""
    if _paddle_mod is None:
        raise RuntimeError("paddle 未安装，无法执行序列化逻辑") from _paddle_exc
    return _paddle_mod


def ensure_cpu_tensor(tensor: Any) -> Any:
    """确保 Tensor 在 CPU 上."""
    paddle = get_paddle()
    if hasattr(tensor, "place") and tensor.place.is_gpu_place():
        return tensor.cpu()
    return tensor


def numpy_from_file(file_path: str) -> np.ndarray:
    """从文件读取数据并转换为 numpy 数组 (uint8)."""
    with open(file_path, "rb") as f:
        data = f.read()
    return np.frombuffer(data, dtype=np.uint8)


def serialize_tensor(tensor: Any) -> np.ndarray:
    """序列化 Tensor 为 numpy 数组 (uint8)."""
    paddle = get_paddle()
    tensor = ensure_cpu_tensor(tensor)
    buffer = io.BytesIO()
    paddle.save(tensor, buffer)
    return np.frombuffer(buffer.getvalue(), dtype=np.uint8)


def try_paddle_load(bytes_data: bytes, logger, context: str):
    """尝试反序列化 Paddle Tensor."""
    paddle = get_paddle()
    buffer = io.BytesIO(bytes_data)
    try:
        obj = paddle.load(buffer)
        if isinstance(obj, paddle.Tensor):
            logger.info(
                "Paddle Load(%s) 成功: shape=%s dtype=%s",
                context,
                tuple(obj.shape),
                obj.dtype,
            )
        else:
            logger.info("Paddle Load(%s) 成功: %s", context, type(obj))
        return obj
    except Exception as exc:
        logger.info("Paddle Load(%s) 失败: %s", context, exc)
        return None


def decode_safetensors(bytes_data: bytes, logger):
    """
    decode_safetensors 的 Docstring
    """
    try:
        from safetensors.paddle import load

        tensors = load(bytes_data)
        logger.info("Safetensors 解析成功, 共 %d 个 tensor", len(tensors))
        if len(tensors) == 1:
            return next(iter(tensors.values()))
        return tensors
    except Exception as exc:
        logger.info("Safetensors 解析失败: %s", exc)
        return None


def serialize_object(obj: Any) -> np.ndarray:
    """序列化 Python 对象为 numpy 数组 (uint8)."""
    buffer = io.BytesIO()
    pickle.dump(obj, buffer)
    return np.frombuffer(buffer.getvalue(), dtype=np.uint8)


def deserialize_object(bytes_data: bytes) -> Any:
    """反序列化 Python 对象."""
    return pickle.loads(bytes_data)
