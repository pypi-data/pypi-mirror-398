"""
Common Utils 模块.

该模块提供了一些通用的辅助函数，如文件 Key 生成、数据类型验证等。
"""

import os
import re
import uuid
from typing import Any


def generate_file_key(file_path: str) -> str:
    """生成唯一的文件 key."""
    return f"file_{os.path.basename(file_path)}_{uuid.uuid4().hex[:8]}"


def validate_data_type(data: Any) -> str:
    """
    验证并返回数据类型.

    Returns:
        str: 'numpy', 'tensor', 'safetensors', 'file', 'object' 之一.
    """
    # 检查 Numpy 数组
    try:
        import numpy as np

        if isinstance(data, np.ndarray):
            return "numpy"
    except ImportError:
        pass

    # 检查 Paddle Tensor
    try:
        import paddle

        if isinstance(data, paddle.Tensor):
            return "tensor"
    except ImportError:
        pass

    if isinstance(data, str) and os.path.isfile(data):
        if data.endswith(".safetensors"):
            return "safetensors"

    return "object"


def collect_device_info():
    """收集所有 RDMA 设备并按自然顺序排序 (mlx5_0, mlx5_1, ...)."""
    devices = []
    infiniBand_path = "/sys/class/infiniband"

    try:
        files = os.listdir(infiniBand_path)
        # 【核心修复】增加自然排序
        # 它可以让 ['mlx5_0', 'mlx5_10', 'mlx5_2'] 排序为 ['mlx5_0', 'mlx5_2', 'mlx5_10']
        files.sort(
            key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r"(\d+)", x)]
        )
    except FileNotFoundError:
        return []

    for file in files:
        if not file.startswith("mlx5_"):
            continue
        devices.append(file)

    return devices
