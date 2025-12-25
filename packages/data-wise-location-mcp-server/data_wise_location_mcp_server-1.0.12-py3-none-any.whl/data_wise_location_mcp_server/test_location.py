"""
Location MCP Server 测试文件
测试各种归属地查询功能
"""

import json
import asyncio
import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from query import LocationQueryEngine


def test_query_engine():
    """测试查询引擎的基本功能"""
    print("🔍 测试 Location 查询引擎...")
    
    engine = LocationQueryEngine()
    
    # 测试数据
    test_cards = ["6222021000011111111", "6217001000022222222"]
    test_ids = ["110101199001011234", "310101198002022345"]
    test_ips = ["192.168.1.1", "8.8.8.8", "153.3.164.212"]
    test_phones = ["13800138000", "15900159001"]
    
    try:
        # 测试银行卡归属地查询
        print("\n📱 测试银行卡归属地查询...")
        bank_result = engine.query_bank_attribution(test_cards)
        print(f"银行卡查询结果: {json.dumps(bank_result, ensure_ascii=False, indent=2)}")
        
        # 测试身份证归属地查询
        print("\n🆔 测试身份证归属地查询...")
        id_result = engine.query_id_attribution(test_ids)
        print(f"身份证查询结果: {json.dumps(id_result, ensure_ascii=False, indent=2)}")
        
        # 测试IP归属地查询
        print("\n🌐 测试IP归属地查询...")
        ip_result = engine.query_ip_attribution(test_ips)
        print(f"IP查询结果: {json.dumps(ip_result, ensure_ascii=False, indent=2)}")
        
        # 测试手机号归属地查询
        print("\n📞 测试手机号归属地查询...")
        mobile_result = engine.query_mobile_attribution(test_phones)
        print(f"手机号查询结果: {json.dumps(mobile_result, ensure_ascii=False, indent=2)}")
        
        print("\n✅ 查询引擎测试完成")
        
    except FileNotFoundError as e:
        print(f"❌ 数据库文件未找到: {e}")
        print("💡 请确保数据文件存在于 src/datasets/location/data/ 目录中")
    except Exception as e:
        print(f"❌ 查询引擎测试失败: {e}")


def test_mcp_tools():
    """测试 MCP 工具功能"""
    print("\n🛠️ 测试 MCP 工具...")
    
    try:
        # FastMCP 工具通过装饰器注册，我们直接测试底层逻辑
        print("📋 可用工具: bank_attribution_batch, id_attribution_batch, ip_attribution_batch, mobile_attribution_batch")
        
        # 测试银行卡工具的底层逻辑
        print("\n📱 测试银行卡归属地工具逻辑...")
        query_engine = LocationQueryEngine()
        
        # 模拟工具请求
        bank_request = ["6222021000011111111"]
        result = query_engine.query_bank_attribution(bank_request)
        
        # 格式化为工具返回格式
        response = {
            "success": True,
            "data": result,
            "count": len(result)
        }
        
        print(f"工具调用结果: {json.dumps(response, ensure_ascii=False, indent=2)}")
        
        print("\n✅ MCP 工具测试完成")
        
    except Exception as e:
        print(f"❌ MCP 工具测试失败: {e}")


def test_error_handling():
    """测试错误处理"""
    print("\n⚠️ 测试错误处理...")
    
    engine = LocationQueryEngine()
    
    try:
        # 测试空参数
        engine.query_bank_attribution([])
        print("❌ 空参数测试失败：应该抛出异常")
    except ValueError as e:
        print(f"✅ 空参数错误处理正确: {e}")
    
    try:
        # 测试超长列表
        long_list = ["1"] * 1001
        engine.query_bank_attribution(long_list)
        print("❌ 超长列表测试失败：应该抛出异常")
    except ValueError as e:
        print(f"✅ 超长列表错误处理正确: {e}")
    
    print("\n✅ 错误处理测试完成")


def main():
    """主测试函数"""
    print("🚀 开始 Location MCP Server 测试")
    print("=" * 50)
    
    # 运行各项测试
    test_query_engine()
    test_mcp_tools()
    test_error_handling()
    
    print("\n" + "=" * 50)
    print("🎉 所有测试完成")


if __name__ == "__main__":
    main()
