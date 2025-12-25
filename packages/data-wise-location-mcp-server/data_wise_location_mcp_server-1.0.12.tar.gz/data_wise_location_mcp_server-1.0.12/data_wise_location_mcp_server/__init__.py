"""
Location MCP Server Package
提供银行、身份证、IP、手机号归属地查询的 MCP 服务
"""

from .main import mcp
from .query import LocationQueryEngine

__version__ = "1.0.0"
__all__ = ["mcp", "LocationQueryEngine"]
