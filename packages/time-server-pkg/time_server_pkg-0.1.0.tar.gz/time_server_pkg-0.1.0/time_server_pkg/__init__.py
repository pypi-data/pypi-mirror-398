"""
时间服务器包

提供JSON-RPC接口的时间服务器，支持获取不同时区的当前时间。
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# 从主要模块导入关键组件
from .main import app, mcp, server, get_current_time

__all__ = [
    "app",
    "mcp",
    "server",
    "get_current_time",
    "__version__",
    "__author__",
    "__email__"
]
