"""FlaxKV2 用法文档

包含 FlaxKV2 各功能模块的使用说明和示例代码。
"""

# 核心用法文档
DOCS = {
    "overview": """# FlaxKV2 概述

FlaxKV2 是一个高性能的 Python 键值存储库，基于 LevelDB，提供类字典接口。

## 核心特性
- 🚀 本地和远程（ZeroMQ）两种后端
- 🎯 智能缓存系统（读缓存 + 写缓冲）
- 📦 支持丰富的数据类型（NumPy、Pandas、嵌套字典/列表）
- ⏰ TTL 自动过期功能
- 🔒 线程安全

## 安装
```bash
pip install flaxkv2

# 完整安装（包含 Pandas、Web UI、向量存储）
pip install flaxkv2[full]
```

## 快速开始
```python
from flaxkv2 import FlaxKV

# 创建本地数据库
with FlaxKV("mydb", "./data") as db:
    # 类字典操作
    db["key"] = "value"
    print(db["key"])  # "value"

    # 支持复杂数据类型
    db["array"] = [1, 2, 3]
    db["dict"] = {"nested": {"key": "value"}}
```
""",
    "basic_usage": """# 基本用法

## 创建数据库实例

```python
from flaxkv2 import FlaxKV

# 方式1：使用上下文管理器（推荐）
with FlaxKV("mydb", "./data") as db:
    db["key"] = "value"
# 自动关闭，确保数据持久化

# 方式2：手动管理
db = FlaxKV("mydb", "./data")
db["key"] = "value"
db.close()  # 不必手动关闭，程序退出会自动关闭
```

## 基本操作

```python
from flaxkv2 import FlaxKV

with FlaxKV("mydb", "./data") as db:
    # 写入
    db["name"] = "Alice"
    db["age"] = 30
    db["scores"] = [95, 87, 92]

    # 读取
    name = db["name"]  # "Alice"
    age = db.get("age")  # 30

    # 检查键存在
    if "name" in db:
        print("exists")

    # 删除
    del db["name"]

    # 遍历
    for key in db.keys():
        print(key)

    for key, value in db.items():
        print(f"{key}: {value}")

    # 批量更新
    db.update({"a": 1, "b": 2, "c": 3})

    # 获取长度
    print(len(db))
```

## 支持的数据类型

```python
# 基本类型
db["string"] = "hello"
db["int"] = 42
db["float"] = 3.14
db["bool"] = True
db["none"] = None

# 容器类型
db["list"] = [1, 2, 3]
db["dict"] = {"a": 1, "b": 2}
db["tuple"] = (1, 2, 3)  # 存储后变为 list
db["set"] = {1, 2, 3}    # 存储后变为 list

# NumPy 数组（保留 dtype 和 shape）
import numpy as np
db["array"] = np.array([1, 2, 3])
db["matrix"] = np.random.randn(100, 100)

# Pandas DataFrame（需要安装 pandas）
import pandas as pd
db["df"] = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
```
""",
    "cache": """# 缓存系统

FlaxKV2 提供两种本地后端：
- **RawLevelDBDict**: 无缓存，简单可靠
- **CachedLevelDBDict**: 智能缓存，极致性能

## 启用缓存

```python
from flaxkv2 import FlaxKV

# 默认无缓存（RawLevelDBDict）
db = FlaxKV("mydb", "./data")

# 启用读缓存
db = FlaxKV("mydb", "./data", read_cache_size=10000)

# 启用写缓冲
db = FlaxKV("mydb", "./data", write_buffer_size=500)

# 同时启用读缓存和写缓冲
db = FlaxKV("mydb", "./data",
            read_cache_size=10000,
            write_buffer_size=500)

# 异步写缓冲（极致性能）
db = FlaxKV("mydb", "./data",
            write_buffer_size=500,
            async_flush=True)
```

## 性能配置文件

```python
# 使用预设配置
db = FlaxKV("mydb", "./data", performance_profile='read_optimized')

# 可用配置:
# - 'balanced'           通用平衡（默认）
# - 'read_optimized'     读密集型（512MB 缓存）
# - 'write_optimized'    写密集型（256MB 写缓冲）
# - 'memory_constrained' 内存受限（64MB 缓存）
# - 'large_database'     大数据库 >100GB（1GB 缓存）
# - 'ml_workload'        机器学习（512MB 缓存，64KB 块）
```

## 性能对比

| 模式 | 读取速度 | 写入速度 |
|------|---------|---------|
| 无缓存 | 107K ops/s | 1.6K ops/s |
| 读缓存 | 1064K ops/s (10x) | 1.6K ops/s |
| 写缓冲 | 1064K ops/s | 926K ops/s (580x) |
| 异步写 | 1434K ops/s | 1434K ops/s (895x) |
""",
    "ttl": """# TTL 自动过期

FlaxKV2 支持设置键的过期时间（Time To Live）。

## 基本用法

```python
from flaxkv2 import FlaxKV

with FlaxKV("cache", "./data") as db:
    # 写入数据
    db["session:123"] = {"user": "alice"}

    # 设置 TTL（秒）
    db.set_ttl("session:123", 3600)  # 1小时后过期

    # 查询剩余时间
    remaining = db.get_ttl("session:123")  # 返回秒数，-1 表示永不过期

    # 移除 TTL
    db.remove_ttl("session:123")  # 变为永不过期
```

## 默认 TTL

```python
# 所有新写入的键都会自动设置 TTL
db = FlaxKV("cache", "./data", default_ttl=3600)

db["key1"] = "value1"  # 自动设置 1小时 TTL
db["key2"] = "value2"  # 自动设置 1小时 TTL

# 覆盖默认 TTL
db["key3"] = "value3"
db.set_ttl("key3", 7200)  # 改为 2小时
```

## TTL 自动清理

过期的键会被后台线程自动清理（默认 60 秒间隔）。

```python
# 自定义清理间隔
db = FlaxKV("cache", "./data",
            default_ttl=3600,
            cleanup_interval=30)  # 30秒清理一次
```
""",
    "nested": """# 嵌套字典和列表

FlaxKV2 支持嵌套数据结构，每个字段独立存储，避免整个对象序列化。

## 嵌套字典

```python
from flaxkv2 import FlaxKV

with FlaxKV("mydb", "./data") as db:
    # 创建嵌套字典
    user = db.nested("user:123")

    # 操作嵌套字段
    user["name"] = "Alice"
    user["email"] = "alice@example.com"
    user["profile"] = {"age": 30, "city": "Beijing"}

    # 读取
    print(user["name"])  # "Alice"
    print(user["profile"]["age"])  # 30

    # 遍历
    for key, value in user.items():
        print(f"{key}: {value}")
```

## 嵌套列表

```python
with FlaxKV("mydb", "./data") as db:
    # 创建嵌套列表
    logs = db.nested_list("logs")

    # 追加元素
    logs.append({"time": "2024-01-01", "msg": "start"})
    logs.append({"time": "2024-01-02", "msg": "running"})

    # 索引访问
    print(logs[0])  # {"time": "2024-01-01", "msg": "start"}

    # 长度
    print(len(logs))  # 2

    # 遍历
    for item in logs:
        print(item)
```

## 自动嵌套模式

```python
# 启用自动嵌套后，赋值字典/列表自动变为嵌套结构
db = FlaxKV("mydb", "./data", auto_nested=True)

# 自动创建嵌套字典
db["user"] = {"name": "Alice", "age": 30}
db["user"]["email"] = "alice@example.com"  # 直接修改字段

# 自动创建嵌套列表
db["items"] = [1, 2, 3]
db["items"].append(4)  # 直接追加
```
""",
    "remote": """# 远程后端

FlaxKV2 支持通过 ZeroMQ 连接远程服务器，实现分布式存储。

## 启动服务器

```bash
# 基本启动
flaxkv2 run --host 127.0.0.1 --port 5555 --data-dir ./data

# 启用加密（推荐生产环境）
flaxkv2 run --host 0.0.0.0 --port 5555 --data-dir ./data \\
    --enable-encryption --password your_password

# 启用压缩
flaxkv2 run --host 0.0.0.0 --port 5555 --data-dir ./data \\
    --enable-encryption --password your_password \\
    --enable-compression
```

## 同步客户端

```python
from flaxkv2 import FlaxKV

# 连接远程服务器
db = FlaxKV("mydb", "tcp://127.0.0.1:5555")

# 加密连接
db = FlaxKV("mydb", "tcp://127.0.0.1:5555",
            enable_encryption=True,
            password="your_password")

# 使用方式与本地完全相同
db["key"] = "value"
print(db["key"])
db.close()
```

## 异步客户端（推荐高并发场景）

```python
import asyncio
from flaxkv2.client.async_zmq_client import AsyncRemoteDBDict

async def main():
    async with AsyncRemoteDBDict(
        'mydb',
        'tcp://127.0.0.1:5555',
        enable_encryption=True,
        password='your_password'
    ) as db:
        # 并发写入
        await asyncio.gather(
            db.set('key1', 'value1'),
            db.set('key2', 'value2'),
            db.set('key3', 'value3')
        )

        # 并发读取
        results = await asyncio.gather(
            db.get('key1'),
            db.get('key2'),
            db.get('key3')
        )
        print(results)

asyncio.run(main())
```

## 安全建议

- 生产环境务必启用加密：`enable_encryption=True, password='your_password'`
- 使用强密码（建议 16+ 字符）
- 限制访问 IP（使用防火墙）
""",
    "cli": """# CLI 命令

FlaxKV2 提供命令行工具管理数据库。

## 启动服务器

```bash
# 基本启动
flaxkv2 run --host 127.0.0.1 --port 5555 --data-dir ./data

# 查看帮助
flaxkv2 run --help
```

## Inspector 数据查看

```bash
# 查看所有键
flaxkv2 inspect keys mydb --path ./data

# 查看键详情
flaxkv2 inspect get mydb user123 --path ./data

# 统计分析
flaxkv2 inspect stats mydb --path ./data

# 启动 Web UI
flaxkv2 web mydb --path ./data --port 8080
```

## 实用工具

```bash
# 根据端口号 kill 进程
flaxkv2 kill 5555

# 查看版本
flaxkv2 version

# 生成示例配置
flaxkv2 config init
```

## 命令别名

```bash
# 以下命令等价
flaxkv2 run --port 5555
kv2 run --port 5555
```
""",
    "vector": """# 向量存储

FlaxKV2 提供向量存储扩展，支持高效的相似度搜索。

## 安装

```bash
pip install flaxkv2[vector]
```

## 基本用法

```python
from flaxkv2.vector import VectorStore

# 创建向量存储
store = VectorStore(
    db_path="./vector_db",
    dim=384,  # 向量维度
    max_elements=100000
)

# 添加向量
store.add(
    ids=["doc1", "doc2"],
    vectors=[[0.1, 0.2, ...], [0.3, 0.4, ...]],
    metadata=[{"title": "Doc 1"}, {"title": "Doc 2"}]
)

# 相似度搜索
results = store.search(
    query_vector=[0.15, 0.25, ...],
    k=10  # 返回前10个最相似的结果
)

for result in results:
    print(f"ID: {result['id']}, Score: {result['score']}")
    print(f"Metadata: {result['metadata']}")
```
""",
}

# 可用的文档主题
TOPICS = list(DOCS.keys())


def get_doc(topic: str) -> str:
    """获取指定主题的文档"""
    if topic in DOCS:
        return DOCS[topic]
    return f"未找到主题 '{topic}'。可用主题: {', '.join(TOPICS)}"


def get_all_topics() -> list[str]:
    """获取所有可用主题"""
    return TOPICS
