#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试虚拟环境检测功能
"""

import sys
import os

# 添加当前目录到路径，以便导入cbuild模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cbuild.cbuild import detect_virtual_environment, print_info

def main():
    print("开始测试虚拟环境检测功能...")
    
    # 测试虚拟环境检测
    python_exe = detect_virtual_environment()
    
    if python_exe:
        print_info(f"检测到虚拟环境 Python 解释器: {python_exe}")
        
        # 检查是否与当前解释器不同
        if python_exe != sys.executable:
            print_info(f"当前解释器: {sys.executable}")
            print_info("虚拟环境检测成功，解释器路径不同")
        else:
            print_info("当前已经在虚拟环境中运行")
    else:
        print_info("未检测到虚拟环境")
        print_info(f"当前解释器: {sys.executable}")

if __name__ == "__main__":
    main()
