"""FlaxKV2 MCP 服务

提供 FlaxKV2 用法查询的 MCP (Model Context Protocol) 服务。
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .docs import DOCS, TOPICS, get_doc

# 创建 MCP 服务实例
mcp = Server("flaxkv2")


@mcp.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用的工具"""
    return [
        Tool(
            name="flaxkv2_usage",
            description="查询 FlaxKV2 的用法文档。可查询的主题包括: overview(概述), basic_usage(基本用法), cache(缓存系统), ttl(TTL过期), nested(嵌套结构), remote(远程后端), cli(命令行), vector(向量存储)",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": f"要查询的主题。可选值: {', '.join(TOPICS)}",
                        "enum": TOPICS,
                    }
                },
                "required": ["topic"],
            },
        ),
        Tool(
            name="flaxkv2_list_topics",
            description="列出所有可用的 FlaxKV2 文档主题",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="flaxkv2_quick_start",
            description="获取 FlaxKV2 快速入门指南，包含最常用的用法示例",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@mcp.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理工具调用"""
    if name == "flaxkv2_usage":
        topic = arguments.get("topic", "overview")
        content = get_doc(topic)
        return [TextContent(type="text", text=content)]

    elif name == "flaxkv2_list_topics":
        topics_info = """# FlaxKV2 文档主题

可用主题列表:

| 主题 | 描述 |
|------|------|
| overview | 项目概述和快速开始 |
| basic_usage | 基本操作（读写、遍历、批量操作） |
| cache | 缓存系统（读缓存、写缓冲、性能配置） |
| ttl | TTL 自动过期功能 |
| nested | 嵌套字典和列表 |
| remote | 远程后端（ZeroMQ 服务器和客户端） |
| cli | 命令行工具 |
| vector | 向量存储扩展 |

使用 `flaxkv2_usage` 工具并传入主题名称即可查看详细文档。
"""
        return [TextContent(type="text", text=topics_info)]

    elif name == "flaxkv2_quick_start":
        quick_start = """# FlaxKV2 快速入门

## 安装
```bash
pip install flaxkv2
```

## 最常用的用法

### 1. 本地数据库
```python
from flaxkv2 import FlaxKV

with FlaxKV("mydb", "./data") as db:
    # 写入
    db["name"] = "Alice"
    db["data"] = {"key": "value", "list": [1, 2, 3]}

    # 读取
    print(db["name"])  # "Alice"
    print(db.get("missing", "default"))  # "default"

    # 遍历
    for key, value in db.items():
        print(f"{key}: {value}")
```

### 2. 启用缓存（高性能）
```python
db = FlaxKV("mydb", "./data",
            read_cache_size=10000,      # 读缓存
            write_buffer_size=500,      # 写缓冲
            async_flush=True)           # 异步刷新
```

### 3. TTL 过期
```python
db = FlaxKV("cache", "./data", default_ttl=3600)  # 1小时过期
db["session"] = {"user": "alice"}
```

### 4. 远程连接
```bash
# 启动服务器
flaxkv2 run --port 5555 --data-dir ./data --enable-encryption --password mypass
```

```python
# 客户端连接
db = FlaxKV("mydb", "tcp://127.0.0.1:5555",
            enable_encryption=True, password="mypass")
```

更多详情请使用 `flaxkv2_usage` 查询具体主题。
"""
        return [TextContent(type="text", text=quick_start)]

    else:
        return [TextContent(type="text", text=f"未知工具: {name}")]


async def run_server():
    """运行 MCP 服务"""
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(read_stream, write_stream, mcp.create_initialization_options())


def main():
    """入口函数"""
    import asyncio

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
