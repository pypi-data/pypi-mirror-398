#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试八字功能返回格式
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from tools.lunar import LunarTools
import json

def test_8zi_format():
    """测试八字功能返回格式"""
    print("=== 测试八字功能返回格式 ===")
    
    # 测试用例
    test_cases = [
        (2024, 1, 1, 12),  # 2024年1月1日12点
        (2023, 6, 15, 8),  # 2023年6月15日8点
        (2025, 3, 20, 18), # 2025年3月20日18点
    ]
    
    for year, month, day, hour in test_cases:
        print(f"\n测试日期: {year}年{month}月{day}日 {hour}时")
        
        try:
            result = LunarTools.get_8zi(year, month, day, hour)
            print(f"返回结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 验证返回格式
            if isinstance(result, dict) and "eight_characters" in result and len(result) == 1:
                print("✓ 格式正确: 只包含 eight_characters 字段")
                
                # 验证八字格式
                eight_chars = result["eight_characters"]
                if isinstance(eight_chars, str) and len(eight_chars.split()) == 4:
                    print(f"✓ 八字格式正确: {eight_chars}")
                else:
                    print(f"✗ 八字格式错误: {eight_chars}")
            else:
                print("✗ 格式错误: 应该只包含 eight_characters 字段")
                
        except Exception as e:
            print(f"✗ 测试失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_8zi_format()