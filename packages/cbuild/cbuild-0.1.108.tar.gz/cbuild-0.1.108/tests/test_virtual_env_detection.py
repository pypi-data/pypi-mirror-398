#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试虚拟环境检测功能
"""

import os
import sys
import tempfile
import shutil

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.dirname(__file__))

# 直接导入cbuild模块
import cbuild.cbuild as cbuild_mod
find_project_root = cbuild_mod.find_project_root
detect_virtual_environment = cbuild_mod.detect_virtual_environment

def test_project_root_detection():
    """测试项目根目录检测功能"""
    print("\n=== 测试项目根目录检测 ===")
    
    # 获取当前项目的真实根目录
    current_dir = os.path.abspath(os.path.dirname(__file__))
    real_project_root = find_project_root(current_dir)
    print(f"当前目录: {current_dir}")
    print(f"检测到的项目根目录: {real_project_root}")
    
    # 测试在子目录中的检测
    test_subdir = os.path.join(current_dir, 'test_subdir', 'deep_subdir')
    if os.path.exists(test_subdir):
        subdir_project_root = find_project_root(test_subdir)
        print(f"\n子目录: {test_subdir}")
        print(f"检测到的项目根目录: {subdir_project_root}")
        
        # 验证是否正确识别了项目根目录
        if subdir_project_root == real_project_root:
            print("[OK] 子目录项目根目录检测正确")
        else:
            print("[ERROR] 子目录项目根目录检测错误")
    else:
        print(f"[WARN] 测试子目录 {test_subdir} 不存在，跳过子目录测试")
    
    # 验证是否是有效的项目根目录（包含.git或pyproject.toml等标记）
    if real_project_root:
        has_git = os.path.exists(os.path.join(real_project_root, '.git'))
        has_pyproject = os.path.exists(os.path.join(real_project_root, 'pyproject.toml'))
        if has_git or has_pyproject:
            print("[OK] 项目根目录验证通过")
        else:
            print("[ERROR] 项目根目录验证失败")

def test_virtual_env_detection():
    """测试虚拟环境检测功能"""
    print("\n=== 测试虚拟环境检测 ===")
    
    # 测试当前目录的虚拟环境检测
    venv_python = detect_virtual_environment()
    print(f"当前目录检测到的虚拟环境Python解释器: {venv_python}")
    
    if venv_python:
        print("[OK] 虚拟环境检测成功")
        # 验证解释器路径是否正确
        if os.path.exists(venv_python):
            print("[OK] 虚拟环境解释器路径验证通过")
        else:
            print("[ERROR] 虚拟环境解释器路径验证失败")
        
        # 检查路径中是否有拼写错误
        if "pyymod" in venv_python:
            print("[ERROR] 路径包含错误拼写: pyymod")
        elif "cbuildd" in venv_python:
            print("[ERROR] 路径包含错误拼写: cbuildd")
        else:
            print("[OK] 路径拼写验证通过")
    else:
        print("[WARN] 未检测到虚拟环境")
    
    # 测试在子目录中的虚拟环境检测
    test_subdir = os.path.join(os.path.dirname(__file__), 'test_subdir', 'deep_subdir')
    if os.path.exists(test_subdir):
        print(f"\n子目录: {test_subdir}")
        
        # 切换到子目录并测试
        original_dir = os.getcwd()
        os.chdir(test_subdir)
        
        try:
            subdir_venv_python = detect_virtual_environment()
            print(f"子目录检测到的虚拟环境Python解释器: {subdir_venv_python}")
            
            if subdir_venv_python:
                print("[OK] 子目录虚拟环境检测成功")
                # 验证解释器路径是否正确
                if os.path.exists(subdir_venv_python):
                    print("[OK] 子目录虚拟环境解释器路径验证通过")
                else:
                    print("[ERROR] 子目录虚拟环境解释器路径验证失败")
            else:
                print("[WARN] 子目录未检测到虚拟环境")
        finally:
            os.chdir(original_dir)

def test_environment_variables():
    """测试环境变量对虚拟环境检测的影响"""
    print("\n=== 测试环境变量 ===")
    
    # 检查相关环境变量
    env_vars = ['VIRTUAL_ENV', 'CONDA_PREFIX', 'POETRY_VIRTUALENV', 'PIPENV_VENV_IN_PROJECT']
    for env_var in env_vars:
        if env_var in os.environ:
            print(f"{env_var}: {os.environ[env_var]}")
        else:
            print(f"{env_var}: 未设置")

def main():
    """主测试函数"""
    print("CBuild 虚拟环境检测功能测试")
    print("=" * 50)
    
    test_project_root_detection()
    test_virtual_env_detection()
    test_environment_variables()
    
    print("\n" + "=" * 50)
    print("测试完成")

if __name__ == "__main__":
    main()
