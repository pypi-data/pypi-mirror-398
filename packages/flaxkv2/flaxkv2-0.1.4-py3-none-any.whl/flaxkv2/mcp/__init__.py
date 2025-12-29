"""FlaxKV2 MCP (Model Context Protocol) 服务

提供 FlaxKV2 的用法查询功能，供 AI 模型调用。
"""

from .server import main, mcp

__all__ = ["main", "mcp"]
