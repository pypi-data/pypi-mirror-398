"""
NexFramework - AI 对话框架
支持多模型切换、工具调用、流式输出、多会话管理、MCP服务器
"""
from .framework import NexFramework
from .database import Database
from .webserver import app as webserver_app
from .mcp_client import MCPClient, MCPManager
from ._version import __version__

__author__ = "3w4e"
__all__ = ['NexFramework', 'Database', 'webserver_app', 'MCPClient', 'MCPManager', '__version__']
