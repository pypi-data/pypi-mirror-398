#!/usr/bin/env python3
"""测试MCP服务器功能"""

import asyncio
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tools.holiday import HolidayTools
from tools.lunar import LunarTools

async def test_holiday_tools():
    """测试节假日工具"""
    print("\n=== 测试节假日工具 ===")
    
    # 测试获取节假日信息
    print("\n1. 测试获取节假日信息:")
    result = await HolidayTools.get_holiday_info("2024-01-01")
    print(f"2024-01-01: {result}")
    
    # 测试判断是否为节假日
    print("\n2. 测试判断是否为节假日:")
    result = await HolidayTools.is_holiday("2024-01-01")
    print(f"2024-01-01 是否为节假日: {result}")
    
    # 测试获取下一个节假日
    print("\n3. 测试获取下一个节假日:")
    result = await HolidayTools.get_next_holiday()
    print(f"下一个节假日: {result}")

def test_lunar_tools():
    """测试农历工具"""
    print("\n=== 测试农历工具 ===")
    
    # 测试公历转农历
    print("\n1. 测试公历转农历:")
    result = LunarTools.gregorian_to_lunar(2024, 1, 1)
    print(f"2024-01-01 转农历: {result}")
    
    # 测试农历转公历
    print("\n2. 测试农历转公历:")
    result = LunarTools.lunar_to_gregorian(2023, 11, 20, False)  # 2023年农历十一月二十
    print(f"农历2023年十一月二十 转公历: {result}")
    
    # 测试获取农历字符串
    print("\n3. 测试获取农历字符串:")
    result = LunarTools.get_lunar_string(2024, 1, 1)
    print(f"2024-01-01 农历字符串: {result}")
    
    # 测试获取24节气
    print("\n4. 测试获取24节气:")
    result = LunarTools.get_24_lunar_feast(2024, 1)
    print(f"2024年1月节气: {result}")
    
    # 测试获取八字
    print("\n5. 测试获取八字:")
    result = LunarTools.get_8zi(2024, 1, 1, 12, 0)  # 2024年1月1日中午12点
    print(f"2024-01-01 12:00 八字: {result}")

async def test_mcp_tools():
    """测试MCP工具列表"""
    print("\n=== 测试MCP工具列表 ===")
    
    # 测试节假日工具列表
    holiday_tools = HolidayTools.get_tools()
    print(f"\n节假日工具数量: {len(holiday_tools)}")
    for tool in holiday_tools:
        print(f"- {tool.name}: {tool.description}")
    
    # 测试农历工具列表
    lunar_tools = LunarTools.get_tools()
    print(f"\n农历工具数量: {len(lunar_tools)}")
    for tool in lunar_tools:
        print(f"- {tool.name}: {tool.description}")

async def main():
    """主测试函数"""
    print("开始测试中国节假日MCP服务器...")
    
    try:
        # 测试MCP工具列表
        await test_mcp_tools()
        
        # 测试节假日工具
        await test_holiday_tools()
        
        # 测试农历工具
        test_lunar_tools()
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())