"""
Location MCP Server
提供银行、身份证、IP、手机号归属地查询的 MCP 服务
"""

from __future__ import annotations

import json
from typing import Any, Dict, List
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# 导入查询引擎
try:
    # 作为包导入时使用相对导入
    from .query import LocationQueryEngine
except ImportError:
    # 作为脚本直接运行时使用绝对导入
    from query import LocationQueryEngine


# 创建 FastMCP 实例
mcp = FastMCP("Location MCP Server")


class BankAttributionRequest(BaseModel):
    """银行卡归属地查询请求"""
    card_numbers: List[str] = Field(..., description="银行卡号列表（最多1000个）")


class IDAttributionRequest(BaseModel):
    """身份证归属地查询请求"""
    id_numbers: List[str] = Field(..., description="身份证号列表（最多1000个）")


class IPAttributionRequest(BaseModel):
    """IP归属地查询请求"""
    ip_addresses: List[str] = Field(..., description="IP地址列表（最多1000个）")


class MobileAttributionRequest(BaseModel):
    """手机号归属地查询请求"""
    phone_numbers: List[str] = Field(..., description="手机号列表（最多1000个）")


# 初始化查询引擎
query_engine = LocationQueryEngine()


@mcp.tool()
def bank_attribution_batch(request: BankAttributionRequest) -> str:
    """
    批量查询银行卡归属地信息
    
    Args:
        request: 包含银行卡号列表的请求
        
    Returns:
        JSON格式的查询结果
    """
    try:
        result = query_engine.query_bank_attribution(request.card_numbers)
        response = {
            "success": True,
            "data": result,
            "count": len(result)
        }
        return json.dumps(response, ensure_ascii=False, indent=2)
    except Exception as e:
        error_response = {
            "success": False,
            "error": str(e),
            "data": None
        }
        return json.dumps(error_response, ensure_ascii=False, indent=2)


@mcp.tool()
def id_attribution_batch(request: IDAttributionRequest) -> str:
    """
    批量查询身份证归属地信息
    
    Args:
        request: 包含身份证号列表的请求
        
    Returns:
        JSON格式的查询结果
    """
    try:
        result = query_engine.query_id_attribution(request.id_numbers)
        response = {
            "success": True,
            "data": result,
            "count": len(result)
        }
        return json.dumps(response, ensure_ascii=False, indent=2)
    except Exception as e:
        error_response = {
            "success": False,
            "error": str(e),
            "data": None
        }
        return json.dumps(error_response, ensure_ascii=False, indent=2)


@mcp.tool()
def ip_attribution_batch(request: IPAttributionRequest) -> str:
    """
    批量查询IP地址归属地信息
    
    Args:
        request: 包含IP地址列表的请求
        
    Returns:
        JSON格式的查询结果
    """
    try:
        result = query_engine.query_ip_attribution(request.ip_addresses)
        response = {
            "success": True,
            "data": result,
            "count": len(result)
        }
        return json.dumps(response, ensure_ascii=False, indent=2)
    except Exception as e:
        error_response = {
            "success": False,
            "error": str(e),
            "data": None
        }
        return json.dumps(error_response, ensure_ascii=False, indent=2)


@mcp.tool()
def mobile_attribution_batch(request: MobileAttributionRequest) -> str:
    """
    批量查询手机号归属地信息
    
    Args:
        request: 包含手机号列表的请求
        
    Returns:
        JSON格式的查询结果
    """
    try:
        result = query_engine.query_mobile_attribution(request.phone_numbers)
        response = {
            "success": True,
            "data": result,
            "count": len(result)
        }
        return json.dumps(response, ensure_ascii=False, indent=2)
    except Exception as e:
        error_response = {
            "success": False,
            "error": str(e),
            "data": None
        }
        return json.dumps(error_response, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run()


def main():
    """命令行入口点函数"""
    mcp.run()
