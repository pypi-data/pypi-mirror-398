#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试虚拟环境返回值功能
"""

import sys
import os

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入函数
from cbuild.cbuild import detect_virtual_environment

def test_venv_return_value():
    """测试虚拟环境返回值功能"""
    print("=== 测试虚拟环境返回值 ===")
    
    # 测试虚拟环境检测函数返回值
    result = detect_virtual_environment()
    print(f"detect_virtual_environment() 返回值: {result}")
    
    # 检查路径是否包含错误拼写
    if result:
        if "pyymod" in result:
            print("[ERROR] 路径包含错误拼写: pyymod")
        else:
            print("[OK] 路径拼写正确")
        
        # 验证解释器路径是否存在
        if os.path.exists(result):
            print("[OK] 虚拟环境解释器路径验证通过")
        else:
            print("[ERROR] 虚拟环境解释器路径不存在")
    else:
        print("[WARN] 未检测到虚拟环境")
    
    # 打印当前Python解释器路径
    print(f"当前sys.executable: {sys.executable}")

def main():
    """主测试函数"""
    print("CBuild 虚拟环境返回值测试")
    print("=" * 50)
    
    test_venv_return_value()
    
    print("\n" + "=" * 50)
    print("测试完成")

if __name__ == "__main__":
    main()
