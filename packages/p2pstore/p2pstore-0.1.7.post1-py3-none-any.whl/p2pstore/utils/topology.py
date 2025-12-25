#!/usr/bin/env python3
"""
NIC Priority Matrix Generator for RDMA High-Performance Transfer

根据 NUMA 亲和性和网卡带宽自动选择最佳网卡
支持 CPU 和 CUDA 设备的拓扑生成
"""

import os
import re
import json
import subprocess
from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

from p2pstore.utils.logger import LoggerManager

logger = LoggerManager.get_logger(__name__)

# 默认输出路径
DEFAULT_OUTPUT_PATH = "/tmp/pdc/p2p_nic_priority_matrix.json"

# 环境变量名
TOPOLOGY_ENV_KEY = "MC_CUSTOM_TOPO_JSON"


@dataclass
class DeviceInfo:
    """RDMA 设备信息"""

    name: str
    rate: int  # Gbps
    numa_node: int


@dataclass
class GPUInfo:
    """GPU 设备信息"""

    index: int
    name: str
    numa_node: int
    pci_bus_id: str


class NICPriorityMatrix:
    """NIC 优先级矩阵生成器"""

    INFINIBAND_PATH = "/sys/class/infiniband"
    HIGH_PERF_RATE = 400  # 400Gbps
    NORMAL_RATE = 100  # 100Gbps

    def __init__(self, output_path: Optional[str] = None):
        self.output_path = output_path
        self.devices: List[DeviceInfo] = []
        self.matrix: Dict[str, List[List[str]]] = {}

    def collect_device_info(self) -> List[DeviceInfo]:
        """收集所有 mlx5 设备信息"""
        devices = []

        if not os.path.exists(self.INFINIBAND_PATH):
            raise FileNotFoundError(f"InfiniBand 路径不存在: {self.INFINIBAND_PATH}")

        for name in os.listdir(self.INFINIBAND_PATH):
            if not name.startswith("mlx5_"):
                continue

            # 获取 NUMA 节点
            numa_node = self._get_numa_node(name)

            # 获取设备速率
            rate = self._get_device_rate(name)
            if rate is None:
                logger.warning(f"无法获取设备 {name} 的速率，跳过")
                continue

            devices.append(DeviceInfo(name=name, rate=rate, numa_node=numa_node))
            logger.info(f"发现设备: {name}, 速率: {rate}Gbps, NUMA节点: {numa_node}")

        self.devices = devices
        return devices

    def _get_numa_node(self, device_name: str) -> int:
        """获取设备的 NUMA 节点"""
        numa_path = os.path.join(
            self.INFINIBAND_PATH, device_name, "device", "numa_node"
        )
        try:
            with open(numa_path, "r") as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return -1

    def _get_device_rate(self, device_name: str) -> Optional[int]:
        """通过 ibstat 获取设备速率"""
        try:
            result = subprocess.run(
                ["ibstat", device_name], capture_output=True, text=True, timeout=10
            )

            # 解析速率: "Rate: 400" 或 "Rate: 100"
            match = re.search(r"Rate:\s*(\d+)", result.stdout)
            if match:
                return int(match.group(1))
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"执行 ibstat 失败: {e}")

        return None

    def generate_matrix(self) -> Dict[str, List[List[str]]]:
        """
        生成优先级矩阵

        格式: {
            "cpu:0": [["mlx5_0", "mlx5_1"], ["mlx5_4"]],  # [高性能网卡, 普通网卡]
            "cpu:1": [["mlx5_2", "mlx5_3"], ["mlx5_5"]]
        }
        """
        if not self.devices:
            self.collect_device_info()

        # 按 NUMA 节点分组
        numa_groups: Dict[int, List[DeviceInfo]] = defaultdict(list)
        default_group: List[DeviceInfo] = []

        for device in self.devices:
            if device.numa_node == -1:
                default_group.append(device)
            else:
                numa_groups[device.numa_node].append(device)

        # 为每个 NUMA 节点生成优先级列表
        matrix = {}

        for numa_node in sorted(numa_groups.keys()):
            high_perf, normal_perf = self._classify_devices(numa_groups[numa_node])
            matrix[f"cpu:{numa_node}"] = [high_perf, normal_perf]

        # 处理无 NUMA 信息的设备
        if default_group:
            high_perf, normal_perf = self._classify_devices(default_group)
            matrix["cpu:default"] = [high_perf, normal_perf]

        self.matrix = matrix
        return matrix

    def _classify_devices(
        self, devices: List[DeviceInfo]
    ) -> Tuple[List[str], List[str]]:
        """按性能分类设备，只保留高性能网卡"""
        high_perf = []

        for device in devices:
            if device.rate >= self.HIGH_PERF_RATE:
                high_perf.append(device.name)
            # 低于 400Gbps 的设备不纳入

        return high_perf, []

    def save_to_file(self, filepath: Optional[str] = None) -> str:
        """保存矩阵到 JSON 文件"""
        filepath = filepath or self.output_path
        if not filepath:
            raise ValueError("未指定输出文件路径")

        if not self.matrix:
            self.generate_matrix()

        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(self.matrix, f, indent=2)

        logger.info(f"优先级矩阵已保存到: {filepath}")
        return filepath

    def get_best_nic(self, numa_node: int = 0) -> Optional[str]:
        """
        获取指定 NUMA 节点的最佳网卡

        优先级: 同 NUMA 高性能 > 同 NUMA 普通 > 其他 NUMA 高性能 > 其他 NUMA 普通
        """
        if not self.matrix:
            self.generate_matrix()

        cpu_key = f"cpu:{numa_node}"

        # 1. 尝试同 NUMA 节点的高性能网卡
        if cpu_key in self.matrix:
            high_perf, normal_perf = self.matrix[cpu_key]
            if high_perf:
                return high_perf[0]
            if normal_perf:
                return normal_perf[0]

        # 2. 尝试其他 NUMA 节点
        for key, (high_perf, normal_perf) in self.matrix.items():
            if key == cpu_key:
                continue
            if high_perf:
                return high_perf[0]
            if normal_perf:
                return normal_perf[0]

        return None

    def print_matrix(self):
        """打印矩阵内容"""
        if not self.matrix:
            self.generate_matrix()

        logger.info("=== NIC 优先级矩阵 ===")
        for location, devices in sorted(self.matrix.items()):
            logger.info(f"{location}:")
            if devices[0]:
                logger.info(f"  高性能网卡 (≥400Gbps): {devices[0]}")
            if devices[1]:
                logger.info(f"  普通网卡 (≥100Gbps): {devices[1]}")
        logger.info("=" * 25)

    def collect_gpu_info(self) -> List[GPUInfo]:
        """收集 CUDA GPU 信息"""
        gpus = []

        try:
            # 使用 nvidia-smi 获取 GPU 信息
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,name,pci.bus_id",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                logger.warning("nvidia-smi 执行失败，无法获取 GPU 信息")
                return gpus

            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    index = int(parts[0])
                    name = parts[1]
                    pci_bus_id = parts[2]

                    # 获取 GPU 的 NUMA 节点
                    numa_node = self._get_gpu_numa_node(pci_bus_id)

                    gpus.append(
                        GPUInfo(
                            index=index,
                            name=name,
                            numa_node=numa_node,
                            pci_bus_id=pci_bus_id,
                        )
                    )
                    logger.info(
                        f"发现 GPU: cuda:{index} ({name}), NUMA节点: {numa_node}"
                    )

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"执行 nvidia-smi 失败: {e}")

        return gpus

    def _get_gpu_numa_node(self, pci_bus_id: str) -> int:
        """获取 GPU 的 NUMA 节点"""
        # PCI bus ID 格式: 00000000:3B:00.0 -> 转换为 0000:3b:00.0
        # 标准化 PCI ID
        pci_id = pci_bus_id.lower()
        if pci_id.startswith("00000000:"):
            pci_id = "0000:" + pci_id[9:]

        numa_path = f"/sys/bus/pci/devices/{pci_id}/numa_node"
        try:
            with open(numa_path, "r") as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            # 尝试其他格式
            pass

        return -1

    def generate_matrix_with_cuda(self) -> Dict[str, List[List[str]]]:
        """
        生成包含 CPU 和 CUDA 的完整优先级矩阵

        格式: {
            "cpu:0": [["mlx5_0", "mlx5_1"], ["mlx5_4"]],
            "cpu:1": [["mlx5_2", "mlx5_3"], ["mlx5_5"]],
            "cuda:0": [["mlx5_0"], ["mlx5_4"]],
            "cuda:1": [["mlx5_2"], ["mlx5_5"]]
        }
        """
        # 先生成 CPU 矩阵
        self.generate_matrix()

        # 收集 GPU 信息
        # gpus = self.collect_gpu_info()

        # 为每个 GPU 分配网卡（基于 NUMA 亲和性）
        # for gpu in gpus:
        #     cuda_key = f"cuda:{gpu.index}"
        #     numa_key = f"cpu:{gpu.numa_node}"

        #     if gpu.numa_node >= 0 and numa_key in self.matrix:
        #         # 使用同 NUMA 节点的网卡配置
        #         self.matrix[cuda_key] = self.matrix[numa_key].copy()
        #     else:
        #         # 没有 NUMA 信息，使用所有高性能网卡
        #         all_high_perf = []
        #         all_normal = []
        #         for key, (high, normal) in self.matrix.items():
        #             if key.startswith("cpu:"):
        #                 all_high_perf.extend(high)
        #                 all_normal.extend(normal)
        #         self.matrix[cuda_key] = [all_high_perf, all_normal]

            # logger.info(
            #     f"  cuda:{gpu.index} -> NUMA {gpu.numa_node} -> {self.matrix[cuda_key]}"
            # )

        return self.matrix


def get_priority_matrix(
    nic_priority_matrix_path: Optional[str] = None,
    device_name: Optional[str] = None,
    include_cuda: bool = True,
) -> str:
    """
    获取 NIC 优先级矩阵

    Args:
        nic_priority_matrix_path: 矩阵配置文件路径，如果不存在会自动生成
        device_name: 直接指定设备名（当 path 为空时使用）
        include_cuda: 是否包含 CUDA 设备的拓扑

    Returns:
        JSON 格式的优先级矩阵字符串
    """
    # 方式一：直接指定设备名
    if not nic_priority_matrix_path:
        if not device_name:
            raise ValueError("必须指定 nic_priority_matrix_path 或 device_name")
        return json.dumps({"cpu:0": [[device_name], []]})

    # 方式二：通过配置文件
    if os.path.exists(nic_priority_matrix_path):
        with open(nic_priority_matrix_path, "r") as f:
            return f.read()

    # 自动生成
    generator = NICPriorityMatrix(nic_priority_matrix_path)
    if include_cuda:
        generator.generate_matrix_with_cuda()
    else:
        generator.generate_matrix()
    generator.save_to_file()

    return json.dumps(generator.matrix)


def setup_topology_env(
    output_path: str = DEFAULT_OUTPUT_PATH,
    include_cuda: bool = True,
    force_regenerate: bool = False,
) -> str | None:
    """
    生成拓扑文件并设置环境变量 MC_CUSTOM_TOPO_JSON

    Args:
        output_path: 输出文件路径
        include_cuda: 是否包含 CUDA 设备
        force_regenerate: 是否强制重新生成（即使文件已存在）

    Returns:
        拓扑文件路径，失败返回 None
    """
    # 如果文件已存在且不强制重新生成，直接使用
    if os.path.exists(output_path) and not force_regenerate:
        os.environ[TOPOLOGY_ENV_KEY] = output_path
        logger.info(f"使用已有拓扑文件: {output_path}")
        logger.info(f"已设置环境变量 {TOPOLOGY_ENV_KEY}={output_path}")
        return output_path

    try:
        generator = NICPriorityMatrix(output_path)
        if include_cuda:
            generator.generate_matrix_with_cuda()
        else:
            generator.generate_matrix()
        generator.save_to_file()

        # 设置环境变量
        os.environ[TOPOLOGY_ENV_KEY] = output_path
        logger.info(f"已设置环境变量 {TOPOLOGY_ENV_KEY}={output_path}")
        return output_path

    except Exception as e:
        logger.error(f"生成拓扑失败: {e}")
        return None


def get_topology_env() -> str | None:
    """获取当前拓扑文件路径（从环境变量）"""
    return os.environ.get(TOPOLOGY_ENV_KEY)
