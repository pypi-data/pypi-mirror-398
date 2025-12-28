#!/usr/bin/env python3
"""MCP服务器启动脚本 - 作为包入口点"""
import sys
import os

# 确保可以导入包内模块
from douyin_summary_mcp.mcp_protocol_server import main

if __name__ == "__main__":
    main()
