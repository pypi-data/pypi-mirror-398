# P2P Store - 分布式 P2P 数据存储系统

## 项目概述

P2P Store 是一个基于 RDMA 的高性能分布式数据传输系统，支持 Tensor、文件、字节数据的点对点传输。

### 核心概念

- **P2PClient**: 客户端，用于 put/get/list/delete 数据
- **P2PServer**: 服务端，元数据服务器 (MetadataServer)
- **P2PConfig**: 统一配置类，Server 和 Client 共用
- **Transport**: 传输层，负责实际的数据传输，支持 RDMA 和 TCP 协议

## 安装指南

### 安装步骤

1. 依赖 RDMA 库

```bash
apt install -y rdma-core libibverbs1 libmlx5-1 libibverbs-dev
```

2. 安装 mooncake-transfer-engine

```bash
pip install mooncake-transfer-engine==0.3.7

# 其他环境已有的依赖
# numpy>=1.20.0
# pyzmq>=22.0.0
# safetensors
# paddlepaddle-gpu
```

## 快速开始

### 1. 启动 Metaserver

```bash
# 直接运行 (使用默认配置: zmq://127.0.0.1:5765,127.0.0.1:5766)
python examples/start_metaserver.py
```

### 2. 启动 Put 节点

```bash
# 直接运行 (默认: 5 个 1MB 的 test_data_{i} key)
python examples/test_put.py
```

### 3. 启动 Get 节点

在其他节点启动示例脚本获取数据:

```bash
python examples/benchmark_get.py
```

## 示例脚本

`examples/` 目录提供了多个示例脚本，**所有脚本都支持直接运行（使用默认参数）**:

| 脚本                   | 作用                 | 默认配置                                |
| ---------------------- | -------------------- | --------------------------------------- |
| `start_metaserver.py`  | 启动 Metadata Server | `zmq://{POD_0_IP}:5765,{POD_0_IP}:5766` |
| `test_put.py`          | 写入测试数据         | 5 个 1MB 数据, key 前缀 `test_data`     |
| `test_delete.py`       | 删除数据             | 删除 `test_data` 前缀的 key             |
| `test_delete_batch.py` | 批量删除数据         | 删除 `test_data` 前缀的 key             |
| `test_list_files.py`   | 列出所有已注册数据   | -                                       |
| `test_clear.py`        | 清空所有数据         | -                                       |
| `benchmark_put.py`     | PUT 性能测试         | 10MB × 10 个 key (`bench_test_key_{i}`) |
| `benchmark_get.py`     | GET 性能测试         | 拉取 10 个 `bench_test_key_{i}`, 1 轮   |

### 使用示例

#### 直接运行（使用默认参数）

```bash
# 1. 启动 Metaserver (默认监听 127.0.0.1:5765,5766)
python examples/start_metaserver.py

# 2. 写入测试数据 (默认: 5 个 1MB, key 前缀 test_data)
python examples/test_put.py

# 3. 查看已注册数据
python examples/test_list_files.py

# 4. 删除数据 (默认删除 test_data 前缀的 key)
python examples/test_delete.py

# 5. 批量删除 (默认删除 test_data 前缀的 key)
python examples/test_delete_batch.py

# 6. 清空所有数据
python examples/test_clear.py
```

#### 自定义参数

```bash
# 写入 10 个 50MB 数据，key 前缀为 my_data
python examples/test_put.py --size_mb 50 --count 10 --key-prefix my_data

# 删除指定前缀的 key
python examples/test_delete_batch.py --key-prefix my_data

# 删除指定的多个 key
python examples/test_delete_batch.py --keys key1,key2,key3

# 指定 Metaserver 地址
python examples/test_put.py --metadata-server zmq://10.0.0.1:5765,10.0.0.1:5766
```

## 配置说明

P2P Store 使用 `P2PConfig` 类进行配置管理，Server 和 Client 共用同一配置类:

| 配置项          | 描述                                                      | 默认值               |
| --------------- | --------------------------------------------------------- | -------------------- |
| metadata_server | Metaserver 地址，格式: `zmq://ip:sync_port,ip:coord_port` | 必填                 |
| local_host      | 本地地址 (ip)                                             | 从 `POD_IP` 环境变量 |
| protocol        | 传输协议 (rdma/tcp)                                       | `"rdma"`             |
| device          | RDMA 设备列表                                             | 自动探测             |
| max_retries     | 最大重试次数                                              | `10`                 |
| retry_interval  | 重试间隔 (秒)                                             | `3`                  |

### 配置示例

```python
from p2pstore import P2PConfig

# ZMQ 模式
config = P2PConfig(
    metadata_server="zmq://10.0.0.1:5765,10.0.0.1:5766",
    protocol="rdma",
    device="mlx5_2,mlx5_3,mlx5_4,mlx5_5"
)
```

## Client API

### 初始化 Client

```python
from p2pstore import P2PClient, P2PConfig

# 创建配置
config = P2PConfig(
    metadata_server="zmq://10.0.0.1:5765,10.0.0.1:5766",
    protocol="rdma",
    device="mlx5_2,mlx5_3,mlx5_4,mlx5_5"
)

# 初始化客户端
client = P2PClient(config)
```

### 注册数据 (put)

```python
import paddle
import numpy as np

# 创建示例数据
tensor = paddle.to_tensor(np.random.randn(128, 128), dtype="float32")

# 注册数据，指定 key (如果 key 已存在，会先删除旧数据再写入)
await client.put("my_tensor", tensor)
```

### 获取数据 (get)

```python
# 获取数据
tensor = await client.get("my_tensor")

# 保存到文件
await client.get("my_tensor", output_path="/path/to/save.bin")
```

### 删除数据 (delete)

```python
# 删除指定 key 的数据 (可删除任意节点注册的数据)
await client.delete("my_tensor")

# 批量删除
results = await client.delete_batch(["key1", "key2", "key3"])
```

### 清除所有数据 (clear)

```python
# 清除所有已注册的数据
result = await client.clear()
# result: {"success": bool, "cleared": int, "failed": list[str]}
```

### 列出数据 (list)

```python
# 列出所有已注册的数据
files = client.list()
print(f"已注册的数据: {list(files.keys())}")
```

### 检查数据是否存在 (exists)

```python
# 检查指定 key 是否存在
exists = await client.exists("my_tensor")
```

## 环境变量

| 变量名     | 作用                         | 默认值      |
| ---------- | ---------------------------- | ----------- |
| `POD_0_IP` | Metaserver 所在节点 IP       | `127.0.0.1` |
| `POD_IP`   | 本地节点 IP (用于 RDMA 绑定) | `127.0.0.1` |

所有脚本默认从 `POD_0_IP` 环境变量拼装 Metaserver 地址（格式：`zmq://{POD_0_IP}:5765,{POD_0_IP}:5766`）。

## Benchmark 脚本

`benchmark/` 目录提供了多种性能基准测试，方便验证 RDMA 传输链路。**所有脚本的参数都有默认值，可直接运行**。

### 脚本列表

| 脚本                          | 作用                                                      | 关键指标                             |
| ----------------------------- | --------------------------------------------------------- | ------------------------------------ |
| `benchmark_put.py`            | 单客户端顺序 PUT，生成指定数量的 `bench_test_key_{i}`     | 吞吐量、Avg/P50/P95/P99 Latency      |
| `benchmark_get.py`            | 单客户端顺序 GET，拉取 PUT 端生成的 `bench_test_key_{i}`  | 吞吐量、Avg/P50/P99 Latency          |
| `benchmark_put_size_sweep.py` | 按不同数据大小生成 Key，格式 `{prefix}_{size}mb_{index}`  | 各尺寸吞吐、Avg/P95/P99、失败次数    |
| `benchmark_get_size_sweep.py` | 适配 PUT sweep，按目标尺寸列表逐一测试 GET                | 各尺寸吞吐、Avg/P95/P99、失败次数    |
| `benchmark_get_concurrent.py` | 启动 N 个独立 Client 并发拉取同一批 Key，评估链路饱和吞吐 | 总吞吐、QPS、Avg/P50/P95/P99 Latency |

### 使用示例

#### 基础 PUT/GET 测试

```bash
# PUT 端：写入 16 个 10MB 的 Key (默认 key 为 bench_test_key_{i})
python benchmark/benchmark_put.py --size_mb 10 --count 16

# GET 端：拉取 PUT 端写入的数据，循环拉取 3 轮 (count 需与 PUT 端一致)
python benchmark/benchmark_get.py --count 16 --rounds 3
```

#### 多尺寸 Size Sweep 测试

```bash
# PUT 端：使用默认值 (10MB × 8 个 key)
python benchmark/benchmark_put_size_sweep.py

# PUT 端：按 1MB/10MB/50MB 三个尺寸生成数据
python benchmark/benchmark_put_size_sweep.py \
    --size_mb 1,10,50 --keys-per-size 8 --key-prefix bench_size_sweep

# GET 端：拉取对应尺寸的数据，循环 3 轮
python benchmark/benchmark_get_size_sweep.py \
    --size_mb 1,10,50 --keys-per-size 8 --rounds 3 --key-prefix bench_size_sweep
```

#### 并发 GET 测试

```bash
# 先启动 PUT 端生成数据 (默认值: 10MB × 8 key, prefix=bench_size_sweep)
python benchmark/benchmark_put_size_sweep.py
# 或自定义 PUT 参数
python benchmark/benchmark_put_size_sweep.py --size_mb 10 --keys-per-size 8 --key-prefix bench_size_sweep

# 启动并发 GET (默认值: 4 并发, 10MB × 8 key, 5 轮, prefix=bench_size_sweep)
python benchmark/benchmark_get_concurrent.py

# 自定义参数: 8 个客户端并发 GET，循环 5 轮
python benchmark/benchmark_get_concurrent.py \
    --size_mb 10 --keys-per-size 8 --concurrency 8 --rounds 5
```
