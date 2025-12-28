"""K6 MCP Pro Server - FastMCP server setup and tool registration."""

from mcp.server.fastmcp import FastMCP

# 创建 MCP 服务器
mcp = FastMCP("k6-mcp")

# 导入并注册所有工具
from .tools import test, baseline, batch, environment, scenario, system, quick  # noqa: E402, F401
