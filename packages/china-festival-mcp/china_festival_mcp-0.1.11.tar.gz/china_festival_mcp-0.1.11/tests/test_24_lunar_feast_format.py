#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试二十四节气功能返回格式
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from tools.lunar import LunarTools
import json

def test_24_lunar_feast_format():
    """测试二十四节气功能返回格式"""
    print("=== 测试二十四节气功能返回格式 ===")
    
    # 测试用例
    test_cases = [
        (2024, 1),   # 小寒、大寒
        (2024, 3),   # 惊蛰、春分
        (2024, 6),   # 芒种、夏至
        (2024, 9),   # 白露、秋分
        (2024, 12),  # 大雪、冬至
    ]
    
    for year, month in test_cases:
        print(f"\n测试日期: {year}年{month}月")
        
        try:
            result = LunarTools.get_24_lunar_feast(year, month)
            print(f"返回结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 验证返回格式
            if isinstance(result, dict) and "error" not in result:
                # 检查必需字段
                required_fields = ["year", "month", "solar_terms"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    print(f"✗ 缺少必需字段: {missing_fields}")
                    continue
                
                # 检查不应存在的字段
                forbidden_fields = ["term_count", "next_solar_term", "primary_term", "description"]
                existing_forbidden = [field for field in forbidden_fields if field in result]
                
                if existing_forbidden:
                    print(f"✗ 包含不应存在的字段: {existing_forbidden}")
                    continue
                
                print("✓ 基本格式正确: 包含必需字段，不包含禁止字段")
                
                # 验证solar_terms格式
                solar_terms = result.get("solar_terms", [])
                if isinstance(solar_terms, list):
                    print(f"✓ solar_terms是列表，包含{len(solar_terms)}个节气")
                    
                    for i, term in enumerate(solar_terms):
                        if isinstance(term, dict):
                            # 检查必需字段
                            term_required = ["name", "date", "days_until", "season"]
                            term_missing = [field for field in term_required if field not in term]
                            
                            # 检查不应存在的字段
                            if "day" in term:
                                print(f"  ✗ 节气{i+1}包含不应存在的'day'字段")
                                continue
                            
                            if term_missing:
                                print(f"  ✗ 节气{i+1}缺少字段: {term_missing}")
                            else:
                                print(f"  ✓ 节气{i+1}: {term['name']} - {term['date']} (倒计时{term['days_until']}天)")
                        else:
                            print(f"  ✗ 节气{i+1}不是字典格式")
                else:
                    print("✗ solar_terms不是列表格式")
                    
            else:
                print(f"✗ 测试失败或返回错误: {result}")
                
        except Exception as e:
            print(f"✗ 测试失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_24_lunar_feast_format()