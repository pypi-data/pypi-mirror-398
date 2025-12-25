#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 normalize_exclude_modules 函数
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

# 导入函数和配置
from cbuild.cbuild import normalize_exclude_modules, DEFAULT_CONFIG

# 测试用例1：空配置
def test_empty_config():
    print("测试1：空配置")
    config = {}
    result = normalize_exclude_modules(config)
    print(f"结果: {result}")
    print(f"has packaging.exclude_modules: {'packaging' in result and 'exclude_modules' in result['packaging']}")
    print(f"exclude_modules 类型: {type(result.get('exclude_modules'))}")
    print(f"packaging.exclude_modules 类型: {type(result.get('packaging', {}).get('exclude_modules'))}")
    print()

# 测试用例2：带有根级别exclude_modules的配置
def test_root_exclude_modules():
    print("测试2：带有根级别exclude_modules的配置")
    config = {
        "exclude_modules": ["module1", "module2"]
    }
    result = normalize_exclude_modules(config)
    print(f"结果: {result}")
    print(f"has root exclude_modules: {'exclude_modules' in result}")
    print(f"has packaging.exclude_modules: {'packaging' in result and 'exclude_modules' in result['packaging']}")
    print(f"packaging.exclude_modules: {result.get('packaging', {}).get('exclude_modules')}")
    print()

# 测试用例3：带有resources.exclude_modules的配置
def test_resources_exclude_modules():
    print("测试3：带有resources.exclude_modules的配置")
    config = {
        "resources": {
            "exclude_modules": ["resource_module1", "resource_module2"]
        }
    }
    result = normalize_exclude_modules(config)
    print(f"结果: {result}")
    print(f"has root exclude_modules: {'exclude_modules' in result}")
    print(f"resources has exclude_modules: {'resources' in result and 'exclude_modules' in result['resources']}")
    print(f"has packaging.exclude_modules: {'packaging' in result and 'exclude_modules' in result['packaging']}")
    print(f"packaging.exclude_modules: {result.get('packaging', {}).get('exclude_modules')}")
    print()

# 测试用例4：带有packaging.exclude_modules的配置
def test_packaging_exclude_modules():
    print("测试4：带有packaging.exclude_modules的配置")
    config = {
        "packaging": {
            "exclude_modules": ["packaging_module1", "packaging_module2"]
        }
    }
    result = normalize_exclude_modules(config)
    print(f"结果: {result}")
    print(f"has root exclude_modules: {'exclude_modules' in result}")
    print(f"packaging.exclude_modules: {result.get('packaging', {}).get('exclude_modules')}")
    print()

# 测试用例5：带有错误类型exclude_modules的配置
def test_invalid_exclude_modules_type():
    print("测试5：带有错误类型exclude_modules的配置")
    config = {
        "exclude_modules": "not_a_list"
    }
    result = normalize_exclude_modules(config)
    print(f"结果: {result}")
    print(f"exclude_modules 类型: {type(result.get('exclude_modules'))}")
    print(f"packaging.exclude_modules 类型: {type(result.get('packaging', {}).get('exclude_modules'))}")
    print()

# 运行所有测试
if __name__ == "__main__":
    print("测试 normalize_exclude_modules 函数")
    print("=" * 50)
    
    test_empty_config()
    test_root_exclude_modules()
    test_resources_exclude_modules()
    test_packaging_exclude_modules()
    test_invalid_exclude_modules_type()
    
    print("测试完成")
    print("=" * 50)
