#!/usr/bin/env python3
"""K6 MCP Pro - Main entry point.

Usage:
    # 直接运行
    python -m src.main
    
    # 或安装后
    k6-mcp-pro
"""

import sys


def main():
    """Run the MCP server."""
    # 延迟导入，避免循环导入
    from .server import mcp
    
    # 启动 MCP 服务器
    mcp.run()


if __name__ == "__main__":
    main()
