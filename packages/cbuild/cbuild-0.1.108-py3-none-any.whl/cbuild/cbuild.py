#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一 PyInstaller / Nuitka 打包脚本
保持你原有配置接口，修复路径/命令生成/平台判断/异常处理，并增加若干有用参数。
兼容 Python 3.7 及以上版本。
"""

import argparse
import subprocess
import sys
import os
import time
import shutil
import shlex
import fnmatch
import hashlib
import tempfile
import re


# 自定义异常类
class CBuildError(Exception):
    """CBuild基础异常类"""


class ConfigurationError(CBuildError):
    """配置相关错误"""


class ToolNotFoundError(CBuildError):
    """构建工具未找到错误"""


class BuildProcessError(CBuildError):
    """构建过程错误"""


class CBuildFileNotFoundError(CBuildError, FileNotFoundError):
    """文件未找到错误"""


class CBuildPermissionError(CBuildError, PermissionError):
    """权限错误"""


# 确保 Python 版本兼容性
if sys.version_info < (3, 7):
    print("❌ 错误：需要 Python 3.7 或更高版本！")
    sys.exit(1)

try:
    import toml
except ImportError:
    print("❌ 错误：缺少依赖包 'toml'，请使用 'pip install toml' 安装")
    sys.exit(1)

# ========================== 配置文件相关 ==========================
CONFIG_FILE_NAME = "cbuild.toml"
CONFIG_FILE_EXAMPLE = "cbuild.toml.example"

# 配置模板（用于生成默认配置文件和DEFAULT_CONFIG）
CONFIG_TEMPLATE = """# CBuild Configuration File

# 通用配置
[general]
# 主脚本文件路径
main_script = "main.py"

# 输出目录
output_dir = "dist"

# 输出文件名配置
# 如果未配置、为空或无效名称，则使用原脚本定义的命名方式
build_filename = ""

# Python优化级别 (0-2)
optimize_level = 2

# 日志级别: DEBUG, INFO, WARNING, ERROR
log_level = "INFO"

# 打包配置
[packaging]
# 生成单文件可执行文件
use_single_file = true

# 移除调试符号以减小文件大小
remove_debug_symbols = true

# 自动跟随导入的模块
follow_imports = true

# 使用链接时优化
use_lto = true

# 使用UPX压缩可执行文件
use_upx = false

# 排除模块配置
# 打包时排除的模块列表
exclude_modules = [
    "pyinstaller",    # 排除PyInstaller
    "pyqt6-tools",    # 排除PyQt6工具
    "tkinter",        # 排除Tkinter
    "pip-tools",      # 排除pip工具
    "nuitka",         # 排除Nuitka
    "test",           # 排除测试模块
    "tests",          # 排除测试模块
    "__pycache__",    # 排除缓存文件
    "setuptools",     # 排除setuptools
    "pkg_resources",  # 排除pkg_resources
    "distutils",      # 排除distutils
    "build",          # 排除build模块
    "compile",        # 排除compile模块
    "cbuild"       # 排除cbuild
]

# 资源配置
[resources]
# 应用图标路径（仅Windows支持.ico）
app_icon = ""

# 要添加的数据文件列表 [["src", "dst"], ...]
add_data = []

# UPX工具目录
upx_dir = "D:/upx"

# UPX压缩排除的文件
upx_exclude = ["vcruntime140.dll"]

# 显式包含的额外模块
include_modules = []

# Windows系统特定配置
[windows]
# 控制台模式: true - 显示控制台, false - 隐藏控制台
# 如果未配置、为空或无效值，则默认显示控制台
console_mode = true

# 需要管理员权限
uac_admin = false

# 是否从pyproject.toml读取版本号并设置到编译后的程序
use_pyproject_version = false

# 编译器配置
[compiler]

# Nuitka 特定配置
[nuitka]
# 使用Clang编译器（仅Nuitka支持）
use_clang = true

# 使用最新的MSVC编译器（仅Windows和Nuitka支持）
use_latest_msvc = true
# 启用的Nuitka插件列表
# 所有可用插件列表及描述:
# - anti-bloat: 从广泛使用的库模块源代码中移除不必要的导入(默认启用)
# - data-files: 包含由包配置文件指定的数据文件
# - delvewheel: 在独立模式下支持使用'delvewheel'的包
# - dill-compat: 支持'dill'包和'cloudpickle'兼容性
# - dll-files: 包含包配置文件指定的DLL文件
# - enum-compat: Python2和'enum'包所需
# - eventlet: 支持包含'eventlet'依赖及其对'dns'包猴子补丁的需求
# - gevent: 'gevent'包所需
# - gi: 支持GI包类型库依赖
# - glfw: 在独立模式下支持'OpenGL' (PyOpenGL)和'glfw'包
# - implicit-imports: 按照包配置文件提供包的隐式导入
# - kivy: 'kivy'包所需
# - matplotlib: 'matplotlib'模块所需
# - multiprocessing: Python的'multiprocessing'模块所需
# - no-qt: 禁用所有Qt绑定的包含
# - options-nanny: 根据包配置文件告知用户潜在问题
# - pbr-compat: 在独立模式下'pbr'包所需
# - pkg-resources: 'pkg_resources'的解决方法
# - playwright: 'playwright'包所需
# - pmw-freezer: 'Pmw'包所需
# - pyqt5: PyQt5包所需
# - pyqt6: PyQt6包在独立模式下所需
# - pyside2: PySide2包所需
# - pyside6: PySide6包在独立模式下所需
# - pywebview: 'webview'包(pywebview on PyPI)所需
# - spacy: 'spacy'包所需
# - tk-inter: Python的Tk模块所需
# - transformers: 为transformers包提供隐式导入
# - upx: 自动使用UPX压缩创建的二进制文件(单文件模式下无效)
# 示例: plugins = ["multiprocessing", "tk-inter", "pyqt5", "matplotlib", "data-files"]
plugins = []

# Nuitka自定义参数列表
# 可以添加本工具未支持的Nuitka参数
# 示例: custom_args = ["--enable-plugin=qml", "--include-plugin-directory=path/to/plugin"]
custom_args = []

# PyInstaller 特定配置
[pyinstaller]
# PyInstaller自定义参数列表
# 可以添加本工具未支持的PyInstaller参数
# 示例: custom_args = ["--console", "--noupx", "--add-binary=path/to/binary:."]
custom_args = []
"""

# 默认配置（从配置模板自动生成，避免重复维护）
DEFAULT_CONFIG = toml.loads(CONFIG_TEMPLATE)

# 全局配置变量（将从配置文件加载）
CONFIG = None
# 配置文件是否是新生成的标志
CONFIG_NEWLY_GENERATED = False
# ===================================================================

IS_WINDOWS = os.name == "nt"


# ---------- 打印辅助 ----------
def print_section(title):
    print(f"\n{'='*60}\n{title:^60}\n{'='*60}")


def print_success(msg):
    try:
        print(f"✅ {msg}")
    except UnicodeEncodeError:
        print(f"[SUCCESS] {msg}")


def print_error(msg):
    try:
        print(f"❌ {msg}")
    except UnicodeEncodeError:
        print(f"[ERROR] {msg}")


def print_info(msg):
    try:
        print(f"[INFO] {msg}")
    except UnicodeEncodeError:
        print(f"[INFO] {msg}")


def print_warning(msg):
    try:
        print(f"⚠️  {msg}")
    except UnicodeEncodeError:
        print(f"[WARNING] {msg}")


# ---------- 配置文件处理 ----------
def load_config_file(config_file_path: str) -> dict:
    """
    从指定路径加载配置文件。

    Args:
        config_file_path: 配置文件路径

    Returns:
        加载的配置字典

    Raises:
        Exception: 加载配置文件失败时抛出
    """
    with open(config_file_path, "r", encoding="utf-8") as f:
        return toml.load(f)


def migrate_config(config: dict) -> dict:
    """
    迁移配置文件，处理版本兼容性问题。

    Args:
        config: 原始配置字典

    Returns:
        迁移后的配置字典
    """
    # 标准化 exclude_modules 配置
    config = normalize_exclude_modules(config)

    # 兼容性处理：将旧版本配置文件中的use_clang和use_latest_msvc从compiler移动到nuitka部分
    if "compiler" in config and (
        "use_clang" in config["compiler"] or "use_latest_msvc" in config["compiler"]
    ):
        if "nuitka" not in config:
            config["nuitka"] = {}
        # 如果nuitka部分没有这两个选项，则从compiler部分复制
        if "use_clang" not in config["nuitka"] and "use_clang" in config["compiler"]:
            config["nuitka"]["use_clang"] = config["compiler"]["use_clang"]
        if (
            "use_latest_msvc" not in config["nuitka"]
            and "use_latest_msvc" in config["compiler"]
        ):
            config["nuitka"]["use_latest_msvc"] = config["compiler"]["use_latest_msvc"]

    return config


def validate_config(config: dict) -> dict:
    """
    验证配置有效性，确保所有必要的键都存在。

    Args:
        config: 配置字典

    Returns:
        验证后的配置字典
    """
    # 确保所有必要的配置部分都存在
    required_sections = ["general", "packaging", "resources", "windows"]
    for section in required_sections:
        if section not in config:
            config[section] = DEFAULT_CONFIG[section].copy()
        else:
            # 确保子键存在
            for key, default_value in DEFAULT_CONFIG[section].items():
                if key not in config[section]:
                    config[section][key] = default_value

    # 确保nuitka和pyinstaller部分存在
    if "nuitka" not in config:
        config["nuitka"] = DEFAULT_CONFIG["nuitka"].copy()
    if "pyinstaller" not in config:
        config["pyinstaller"] = DEFAULT_CONFIG["pyinstaller"].copy()

    return config


def load_config() -> None:
    """
    加载配置文件，如果配置文件不存在则生成默认配置文件。
    """
    global CONFIG, CONFIG_NEWLY_GENERATED

    if os.path.exists(CONFIG_FILE_NAME):
        try:
            config = load_config_file(CONFIG_FILE_NAME)
            config = migrate_config(config)
            config = validate_config(config)
            CONFIG = config
            print_info(f"已加载配置文件: {CONFIG_FILE_NAME}")
            CONFIG_NEWLY_GENERATED = False
        except Exception as e:
            print_error(f"加载配置文件失败: {e}")
            print_info("将使用默认配置")
            CONFIG = DEFAULT_CONFIG.copy()
            CONFIG_NEWLY_GENERATED = False
    else:
        generate_default_config()
        # 重新加载生成的配置文件
        try:
            config = load_config_file(CONFIG_FILE_NAME)
            config = migrate_config(config)
            config = validate_config(config)
            CONFIG = config
            print_info(f"已加载新生成的配置文件: {CONFIG_FILE_NAME}")
            CONFIG_NEWLY_GENERATED = True
        except Exception as e:
            print_error(f"加载新生成的配置文件失败: {e}")
            print_info("将使用默认配置")
            CONFIG = DEFAULT_CONFIG.copy()
            CONFIG_NEWLY_GENERATED = False


def normalize_exclude_modules(config: dict) -> dict:
    """
    标准化 exclude_modules 配置，处理兼容性问题。
    将旧版本的 exclude_modules 从 resources 部分移动到根级别，
    确保 exclude_modules 是列表类型。

    Args:
        config: 配置字典

    Returns:
        标准化后的配置字典
    """
    # 兼容性处理：确保exclude_modules在根级别
    if "exclude_modules" not in config:
        if "resources" in config and "exclude_modules" in config["resources"]:
            # 从resources section移动到根级别
            config["exclude_modules"] = config["resources"]["exclude_modules"]
            del config["resources"]["exclude_modules"]
        elif (
            "packaging" in DEFAULT_CONFIG
            and "exclude_modules" in DEFAULT_CONFIG["packaging"]
        ):
            # 从DEFAULT_CONFIG的packaging部分获取默认值
            config["exclude_modules"] = DEFAULT_CONFIG["packaging"][
                "exclude_modules"
            ].copy()
        else:
            # 作为最后的回退，使用空列表
            config["exclude_modules"] = []
    elif not isinstance(config["exclude_modules"], list):
        # 确保exclude_modules是列表类型
        if (
            "packaging" in DEFAULT_CONFIG
            and "exclude_modules" in DEFAULT_CONFIG["packaging"]
        ):
            config["exclude_modules"] = DEFAULT_CONFIG["packaging"][
                "exclude_modules"
            ].copy()
        else:
            config["exclude_modules"] = []
    return config


def generate_default_config() -> None:
    """
    生成默认配置文件。
    """
    # 配置文件生成优先级：
    # 1. 当前目录下的示例配置文件
    # 2. 使用DEFAULT_CONFIG生成（无注释）

    # 尝试从当前目录读取示例配置文件
    if os.path.exists(CONFIG_FILE_EXAMPLE):
        try:
            # 复制示例配置文件
            shutil.copy(CONFIG_FILE_EXAMPLE, CONFIG_FILE_NAME)
            print_info(f"已从示例配置文件生成: {CONFIG_FILE_NAME}")
            return
        except Exception as e:
            print_error(f"从当前目录示例配置文件生成失败: {e}")

    # 最后回退到使用带注释的模板字符串生成
    try:
        # 使用全局定义的CONFIG_TEMPLATE生成默认配置文件
        with open(CONFIG_FILE_NAME, "w", encoding="utf-8") as f:
            f.write(CONFIG_TEMPLATE)
        print_info(f"已生成默认配置文件: {CONFIG_FILE_NAME}")
    except Exception as e:
        print_error(f"生成配置文件失败: {e}")


# ---------- 工具检测 ----------
def ensure_executable_exists(name: str, module: bool = False) -> bool:
    """
    检查工具是否可用。
    - 若 module=True，优先使用 python -m name --version 探测，import 作为 fallback
    - 否则检查 PATH 中命令

    Args:
        name: 工具名称
        module: 是否作为 Python 模块检查

    Returns:
        工具是否可用
    """
    if module:
        # 1. 首先检查当前 Python 环境（可能是虚拟环境）中的工具
        # 1.1 尝试 python -m name --version
        try:
            cmd = [sys.executable, "-m", name, "--version"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return True
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError):
            pass
        
        # 1.2 尝试直接导入模块
        try:
            __import__(name)
            return True
        except Exception:
            pass
        
        # 2. 只有当当前环境中没有工具时，才尝试使用全局 Python 环境
        if hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix:
            # 当前在虚拟环境中，且虚拟环境中没有工具
            # 尝试使用全局 Python 解释器检查工具
            try:
                # 构建全局 Python 解释器路径
                global_python = sys.executable.replace(sys.prefix, sys.base_prefix)
                cmd = [global_python, "-m", name, "--version"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return True
            except (subprocess.SubprocessError, FileNotFoundError, TimeoutError):
                pass
            
            # 尝试全局 Python 环境的直接导入
            try:
                # 使用全局 Python 执行导入命令
                global_python = sys.executable.replace(sys.prefix, sys.base_prefix)
                cmd = [global_python, "-c", f"import {name}"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return True
            except (subprocess.SubprocessError, FileNotFoundError, TimeoutError):
                pass
        
        # 3. 所有检查都失败，返回 False
        return False
    else:
        return shutil.which(name) is not None


# ---------- 参数映射辅助函数 ----------
def add_common_options(opts: list, project_name: str, tool: str) -> None:
    """
    添加公共参数选项。

    Args:
        opts: 参数列表
        project_name: 项目名称
        tool: 工具名称（'nuitka' 或 'pyinstaller'）
    """
    # 输出文件名/目录
    if tool == "nuitka":
        opts.append(f"--output-filename={project_name}")
        opts.append(f"--output-dir={CONFIG['general']['output_dir']}")
    elif tool == "pyinstaller":
        opts.append(f"--name={project_name}")
        opts.append(f"--distpath={CONFIG['general']['output_dir']}")
        opts.append(f"--log-level={CONFIG['general']['log_level']}")
        opts.append(f"--optimize={int(CONFIG['general']['optimize_level'])}")

    # 打包模式相关参数
    if CONFIG["packaging"]["use_single_file"]:
        if tool == "nuitka":
            opts.append("--onefile")
            # Nuitka 的 onefile 模式会单文件打包，不必也可指定 standalone
            if CONFIG["packaging"]["follow_imports"]:
                # 当需要跟随导入并且使用 onefile 模式时，不需要额外添加 standalone 参数
                pass
        elif tool == "pyinstaller":
            opts.append("-F")
    else:
        if tool == "nuitka":
            opts.append("--standalone")

    if CONFIG["packaging"]["follow_imports"] and tool == "nuitka":
        opts.append("--follow-imports")

    if not CONFIG["packaging"]["remove_debug_symbols"] and tool == "nuitka":
        opts.append("--unstripped")

    if CONFIG["packaging"]["use_lto"] and tool == "nuitka":
        opts.append("--lto=yes")


def add_windows_options(opts: list, tool: str) -> None:
    """
    添加Windows专属选项。

    Args:
        opts: 参数列表
        tool: 工具名称（'nuitka' 或 'pyinstaller'）
    """
    if not IS_WINDOWS:
        return

    app_icon = CONFIG["resources"]["app_icon"]
    if app_icon and os.path.exists(app_icon):
        if tool == "nuitka":
            opts.append(f"--windows-icon-from-ico={app_icon}")
        elif tool == "pyinstaller":
            opts.append(f"--icon={app_icon}")

    # 处理控制台模式
    console_mode = CONFIG["windows"].get("console_mode")
    try:
        if console_mode is None:
            show_console = True
        elif isinstance(console_mode, str):
            console_mode = console_mode.lower()
            show_console = console_mode in ["true", "1", "yes", "force"]
        else:
            show_console = bool(console_mode)

        if tool == "nuitka":
            console_mode_value = "force" if show_console else "disable"
            opts.append(f"--windows-console-mode={console_mode_value}")
        elif tool == "pyinstaller":
            if show_console:
                opts.append("--console")
            else:
                opts.append("--noconsole")
    except Exception:
        # 处理无效值，默认显示控制台
        if tool == "nuitka":
            opts.append("--windows-console-mode=force")
        elif tool == "pyinstaller":
            opts.append("--console")

    if CONFIG["windows"]["uac_admin"] and tool == "nuitka":
        opts.append("--windows-uac-admin")


def add_data_options(opts: list, tool: str) -> None:
    """
    添加数据文件和模块相关选项。

    Args:
        opts: 参数列表
        tool: 工具名称（'nuitka' 或 'pyinstaller'）
    """
    # 数据文件
    for src, dst in CONFIG["resources"]["add_data"]:
        if os.path.exists(src):
            if tool == "nuitka":
                opts.append(f"--include-data-dir={src}={dst}")
            elif tool == "pyinstaller":
                sep = ";" if IS_WINDOWS else ":"
                opts.append(f"--add-data={src}{sep}{dst}")
        else:
            print_warning(f"[{tool.capitalize()}] 数据文件不存在，跳过: {src}")

    # 包含/排除模块
    for m in CONFIG["resources"]["include_modules"]:
        if tool == "nuitka":
            opts.append(f"--include-module={m}")
        elif tool == "pyinstaller":
            opts.append(f"--hidden-import={m}")

    # 处理 exclude_modules 配置
    exclude_modules = []
    
    # 从 packaging 部分获取 exclude_modules（优先）
    if "packaging" in CONFIG and "exclude_modules" in CONFIG["packaging"]:
        exclude_modules = CONFIG["packaging"]["exclude_modules"]
    # 从根级别获取 exclude_modules（兼容旧配置）
    elif "exclude_modules" in CONFIG:
        exclude_modules = CONFIG["exclude_modules"]
    # 从 resources 部分获取 exclude_modules（兼容更旧配置）
    elif "resources" in CONFIG and "exclude_modules" in CONFIG["resources"]:
        exclude_modules = CONFIG["resources"]["exclude_modules"]
    
    # 确保 exclude_modules 是列表类型
    if not isinstance(exclude_modules, list):
        exclude_modules = []
    
    for m in exclude_modules:
        if tool == "nuitka":
            opts.append(f"--nofollow-import-to={m}")
        elif tool == "pyinstaller":
            opts.append(f"--exclude-module={m}")


def add_upx_options(opts: list, tool: str) -> None:
    """
    添加UPX相关选项。

    Args:
        opts: 参数列表
        tool: 工具名称（'nuitka' 或 'pyinstaller'）
    """
    upx_dir = CONFIG["resources"]["upx_dir"]
    if not os.path.exists(upx_dir):
        print_warning(f"[{tool.capitalize()}] 未找到 UPX 目录: {upx_dir}")
        return

    if tool == "nuitka":
        # Nuitka通过插件使用UPX
        plugins = CONFIG["nuitka"].get("plugins", [])
        if "upx" in plugins:
            upx_binary = os.path.join(upx_dir, "upx.exe" if IS_WINDOWS else "upx")
            if os.path.exists(upx_binary):
                opts.append(f"--upx-binary={upx_binary}")
            else:
                print_warning(
                    f"[{tool.capitalize()}] 未找到 UPX 二进制文件: {upx_binary}"
                )
    elif tool == "pyinstaller":
        if CONFIG["packaging"]["use_upx"]:
            opts.extend(["--upx-dir", upx_dir])
            for ex in CONFIG["resources"]["upx_exclude"]:
                opts.append(f"--upx-exclude={ex}")


# ---------- 参数映射 ----------
def generate_nuitka_options(project_name: str) -> list:
    opts: list = []

    # 添加公共选项
    add_common_options(opts, project_name, "nuitka")

    # 添加Windows专属选项
    add_windows_options(opts, "nuitka")

    # 添加数据和模块选项
    add_data_options(opts, "nuitka")

    # 添加UPX选项
    add_upx_options(opts, "nuitka")

    # Nuitka 特定选项
    if "nuitka" in CONFIG and CONFIG["nuitka"].get("use_clang"):
        opts.append("--clang")
    if "nuitka" in CONFIG and CONFIG["nuitka"].get("use_latest_msvc") and IS_WINDOWS:
        opts.append("--msvc=latest")

    # 启用Nuitka插件
    if "nuitka" in CONFIG and "plugins" in CONFIG["nuitka"]:
        for plugin in CONFIG["nuitka"]["plugins"]:
            if plugin.startswith("qt-plugins="):
                # 特殊处理qt-plugins插件，分离插件名和参数
                opts.append("--enable-plugin=qt-plugins")
                opts.append(f"--{plugin}")
            else:
                opts.append(f"--enable-plugin={plugin}")

    # 添加版本号信息（如果配置了从pyproject.toml读取版本号）
    if IS_WINDOWS and CONFIG["windows"].get("use_pyproject_version"):
        version = get_project_version()
        if version:
            formatted_version = format_windows_version(version)
            print_info(f"从 pyproject.toml 读取到版本号: {version}，格式化后: {formatted_version}")
            # 设置Windows文件版本和产品版本
            opts.append(f"--windows-file-version={formatted_version}")
            opts.append(f"--windows-product-version={formatted_version}")

    # 添加自定义参数
    if "nuitka" in CONFIG and "custom_args" in CONFIG["nuitka"]:
        opts.extend(CONFIG["nuitka"]["custom_args"])

    return opts


def generate_pyinstaller_options(project_name: str) -> list:
    opts: list = []

    # 添加公共选项
    add_common_options(opts, project_name, "pyinstaller")

    # 添加Windows专属选项
    add_windows_options(opts, "pyinstaller")

    # 添加调试符号相关参数
    if CONFIG["packaging"]["remove_debug_symbols"]:
        opts.append("-s")

    # 添加数据和模块选项
    add_data_options(opts, "pyinstaller")

    # 添加UPX选项
    add_upx_options(opts, "pyinstaller")

    # 添加版本号信息（如果配置了从pyproject.toml读取版本号）
    if IS_WINDOWS and CONFIG["windows"].get("use_pyproject_version"):
        version = get_project_version()
        if version:
            formatted_version = format_windows_version(version)
            version_tuple = get_windows_version_tuple(version)
            print_info(f"从 pyproject.toml 读取到版本号: {version}，格式化后: {formatted_version}")
            # PyInstaller 使用 --version-file 参数来设置版本信息
            # 首先创建一个临时的版本信息文件
        
            version_file_content = f'''
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(\n  ffi=FixedFileInfo(\n    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.\n    filevers=({version_tuple}),\n    prodvers=({version_tuple}),\n    mask=0x3f,  # 0x3f means all flags
    flags=0x0,  # 0x0 means no flags
    OS=0x40004,  # 0x40004 means NT and Windows 2000
    fileType=0x1,  # 0x1 means APPLICATION
    subtype=0x0,  # 0x0 means subtype is not defined
    date=(0, 0)  # date and time stamps are not defined here
    ),\n  kids=[\n    StringFileInfo(\n      [\n      StringTable(\n        u'040904b0',\n        [StringStruct(u'CompanyName', u''),\n        StringStruct(u'FileDescription', u''),\n        StringStruct(u'FileVersion', u'{formatted_version}'),\n        StringStruct(u'InternalName', u'{project_name}'),\n        StringStruct(u'LegalCopyright', u''),\n        StringStruct(u'OriginalFilename', u'{project_name}.exe'),\n        StringStruct(u'ProductName', u'{project_name}'),\n        StringStruct(u'ProductVersion', u'{formatted_version}')])\n      ]),\n    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])\n  ]\n)'''
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(version_file_content)
                version_file_path = f.name
            
            # 添加版本文件参数
            opts.append(f"--version-file={version_file_path}")

    # 添加自定义参数
    if "pyinstaller" in CONFIG and "custom_args" in CONFIG["pyinstaller"]:
        opts.extend(CONFIG["pyinstaller"]["custom_args"])

    return opts


# ---------- 虚拟环境检测 ----------
def _check_python_executable(venv_path: str) -> str | None:
    """检查虚拟环境中的Python解释器是否存在

    Args:
        venv_path: 虚拟环境路径

    Returns:
        Python解释器路径，如果不存在则返回None
    """
    if IS_WINDOWS:
        python_exe = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        python_exe = os.path.join(venv_path, "bin", "python")
    
    if os.path.exists(python_exe):
        return python_exe
    return None


def find_project_root(start_dir: str) -> str | None:
    """
    查找项目根目录，通过识别常见的项目根目录标志文件/目录
    
    Args:
        start_dir: 开始查找的目录
        
    Returns:
        项目根目录路径，如果未找到则返回None
    """
    # 常见的项目根目录标志文件/目录（按优先级排序）
    # 版本控制系统目录具有最高优先级
    project_root_markers = [
        # 版本控制系统（最高优先级）
        ".git", ".hg", ".svn",
        
        # 核心Python项目标志
        "pyproject.toml", "setup.py", "setup.cfg", "MANIFEST.in",
        
        # 依赖管理
        "requirements.txt", "requirements-dev.txt", 
        "tox.ini", "uv.lock", "poetry.lock", "Pipfile",
        
        # 构建工具
        "Makefile", "CMakeLists.txt", "build.py",
        
        # 配置文件
        ".env.example", ".env.local", 
        # 将cbuild.toml放在较低优先级，避免将子目录识别为项目根目录
        "cbuild.toml"
    ]
    
    current_dir = start_dir
    
    while True:
        # 检查当前目录是否包含项目根目录标志
        for marker in project_root_markers:
            marker_path = os.path.join(current_dir, marker)
            if os.path.exists(marker_path):
                return current_dir
        
        # 检查是否到达文件系统根目录
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break
        
        current_dir = parent_dir
    
    return None


def detect_virtual_environment() -> str | None:
    """
    检测当前项目目录下的Python虚拟环境
    
    Returns:
        虚拟环境中Python解释器的路径，如果未找到则返回None
    """
    # 1. 获取当前工作目录（项目目录）
    current_dir = os.getcwd()
    
    # 2. 检查环境变量（需要过滤工具自身的虚拟环境）
    # Python虚拟环境标准环境变量
    venv_env_vars = [
        'VIRTUAL_ENV',          # 标准虚拟环境变量
        'CONDA_PREFIX',         # Conda环境根目录
        'POETRY_VIRTUALENV',    # Poetry虚拟环境
        'PIPENV_VENV_IN_PROJECT', # Pipenv项目内虚拟环境
    ]
    
    for env_var in venv_env_vars:
        if env_var in os.environ:
            venv_path = os.environ[env_var]
            if os.path.exists(venv_path):
                if env_var == 'PIPENV_VENV_IN_PROJECT' and venv_path.lower() == 'true':
                    # 特殊处理：PIPENV_VENV_IN_PROJECT=true 表示虚拟环境在项目内的.env目录
                    project_dir = current_dir
                    venv_path = os.path.join(project_dir, ".venv")
                    if not os.path.exists(venv_path):
                        venv_path = os.path.join(project_dir, "venv")
                
                # 检查虚拟环境中的Python解释器
                python_exe = _check_python_executable(venv_path)
                if python_exe:
                    # 仅当虚拟环境路径包含当前项目路径，或者当前不在任何虚拟环境中时才使用
                    # 这是为了过滤掉工具自身的虚拟环境（如uv tool install创建的虚拟环境）
                    if current_dir in venv_path or not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
                        return python_exe
    
    # 检查CONDA_DEFAULT_ENV（需要转换为路径）
    if 'CONDA_DEFAULT_ENV' in os.environ:
        conda_prefix = os.environ.get('CONDA_PREFIX')
        if conda_prefix and os.path.exists(conda_prefix):
            python_exe = _check_python_executable(conda_prefix)
            if python_exe:
                # 同样过滤掉工具自身的虚拟环境
                if current_dir in conda_prefix or not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
                    return python_exe
    
    # 3. 检查当前Python解释器是否已经在虚拟环境中
    # 过滤掉工具自身的虚拟环境
    if hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix:
        # 检查当前虚拟环境是否与项目相关
        # 如果Python解释器路径包含当前项目路径，或者当前目录是虚拟环境的父目录，则认为是项目相关的虚拟环境
        if current_dir in sys.executable or os.path.dirname(current_dir) in sys.executable:
            return sys.executable
    
    # 3. 常见的虚拟环境目录名称（按优先级排序，最常用的放在前面）
    venv_patterns = [
        ".venv", "venv", "env", 
        "virtualenv", "venv-win", "env-win",
        ".env", "ENV", "env-*", "venv-*",
        "virtualenv-*"
    ]
    
    # 5. 从当前目录开始向上遍历
    traverse_dir = os.getcwd()
    project_root_dir = find_project_root(traverse_dir)
    
    while True:
        try:
            # 检查当前目录下是否有虚拟环境目录
            if os.path.exists(traverse_dir):
                # 获取当前目录下的所有子目录
                subdirs = [d for d in os.listdir(traverse_dir) if os.path.isdir(os.path.join(traverse_dir, d))]
                
                for venv_pattern in venv_patterns:
                    # 使用fnmatch匹配带通配符的虚拟环境目录名称
                    matched_dirs = fnmatch.filter(subdirs, venv_pattern)
                    
                    for venv_name in matched_dirs:
                        venv_path = os.path.join(traverse_dir, venv_name)
                        
                        # 验证是否是有效的虚拟环境
                        pyvenv_cfg = os.path.join(venv_path, "pyvenv.cfg")
                        
                        # 检查是否为有效的虚拟环境：存在pyvenv.cfg或python解释器
                        python_exe = _check_python_executable(venv_path)
                        if os.path.exists(pyvenv_cfg) or python_exe:
                            if python_exe:
                                return python_exe
        except PermissionError:
            # 如果没有权限访问当前目录，继续遍历父目录
            pass
        
        # 6. 检查是否为Poetry虚拟环境
        poetry_config = os.path.join(traverse_dir, "pyproject.toml")
        if os.path.exists(poetry_config):
            try:
                # 尝试解析pyproject.toml获取项目名称
                with open(poetry_config, 'r', encoding='utf-8') as f:
                    pyproject_data = toml.load(f)
                
                project_name = pyproject_data.get('tool', {}).get('poetry', {}).get('name', '')
                if project_name:
                    # Poetry虚拟环境命名格式：{project_name}-{hash}-py{python_version}
                    # 计算项目目录的哈希值（简化版，实际Poetry使用更复杂的算法）
                    project_hash = hashlib.sha256(traverse_dir.encode()).hexdigest()[:8]
                    
                    if IS_WINDOWS:
                        poetry_venv_base = os.path.join(os.environ.get("USERPROFILE", ""), ".cache", "pypoetry", "virtualenvs")
                    else:
                        poetry_venv_base = os.path.join(os.environ.get("HOME", ""), ".cache", "pypoetry", "virtualenvs")
                    
                    if os.path.exists(poetry_venv_base):
                        # 搜索匹配的虚拟环境目录
                        for venv_dir in os.listdir(poetry_venv_base):
                            if project_name in venv_dir and project_hash in venv_dir:
                                venv_path = os.path.join(poetry_venv_base, venv_dir)
                                python_exe = _check_python_executable(venv_path)
                                if python_exe:
                                    return python_exe
            except (toml.TomlDecodeError, KeyError, PermissionError, FileNotFoundError):
                # 如果解析失败，尝试使用原始方式
                if IS_WINDOWS:
                    poetry_venv_base = os.path.join(os.environ.get("USERPROFILE", ""), ".cache", "pypoetry", "virtualenvs")
                else:
                    poetry_venv_base = os.path.join(os.environ.get("HOME", ""), ".cache", "pypoetry", "virtualenvs")
                
                if os.path.exists(poetry_venv_base):
                    try:
                        # 查找最近修改的Poetry虚拟环境（备选方案）
                        latest_venv = None
                        latest_mtime = 0
                        
                        for venv_dir in os.listdir(poetry_venv_base):
                            venv_path = os.path.join(poetry_venv_base, venv_dir)
                            if os.path.isdir(venv_path):
                                mtime = os.path.getmtime(venv_path)
                                if mtime > latest_mtime:
                                    latest_mtime = mtime
                                    latest_venv = venv_path
                        
                        if latest_venv:
                            python_exe = _check_python_executable(latest_venv)
                            if python_exe:
                                return python_exe
                    except PermissionError:
                        pass
        
        # 7. 检查是否为Pipenv虚拟环境
        pipfile_path = os.path.join(traverse_dir, "Pipfile")
        if os.path.exists(pipfile_path):
            try:
                # 计算Pipenv虚拟环境的哈希值（基于Pipfile的内容）
                with open(pipfile_path, 'r', encoding='utf-8') as f:
                    pipfile_content = f.read()
                
                pipfile_hash = hashlib.sha256(pipfile_content.encode()).hexdigest()[:8]
                
                if IS_WINDOWS:
                    pipenv_venv_base = os.path.join(os.environ.get("USERPROFILE", ""), ".virtualenvs")
                else:
                    pipenv_venv_base = os.path.join(os.environ.get("HOME", ""), ".virtualenvs")
                
                if os.path.exists(pipenv_venv_base):
                    # 搜索匹配的虚拟环境目录
                    for venv_dir in os.listdir(pipenv_venv_base):
                        if pipfile_hash in venv_dir:
                            venv_path = os.path.join(pipenv_venv_base, venv_dir)
                            python_exe = _check_python_executable(venv_path)
                            if python_exe:
                                return python_exe
            except (PermissionError, FileNotFoundError):
                # 如果解析失败，尝试使用原始方式
                if IS_WINDOWS:
                    pipenv_venv_base = os.path.join(os.environ.get("USERPROFILE", ""), ".virtualenvs")
                else:
                    pipenv_venv_base = os.path.join(os.environ.get("HOME", ""), ".virtualenvs")
                
                if os.path.exists(pipenv_venv_base):
                    try:
                        # 查找最近修改的Pipenv虚拟环境（备选方案）
                        latest_venv = None
                        latest_mtime = 0
                        
                        for venv_dir in os.listdir(pipenv_venv_base):
                            venv_path = os.path.join(pipenv_venv_base, venv_dir)
                            if os.path.isdir(venv_path):
                                mtime = os.path.getmtime(venv_path)
                                if mtime > latest_mtime:
                                    latest_mtime = mtime
                                    latest_venv = venv_path
                        
                        if latest_venv:
                            python_exe = _check_python_executable(latest_venv)
                            if python_exe:
                                return python_exe
                    except PermissionError:
                        pass
        
        # 检查是否到达项目根目录
        if project_root_dir and traverse_dir == project_root_dir:
            # 已经检查了项目根目录，停止遍历
            break
        
        # 检查是否到达文件系统根目录
        parent_dir = os.path.dirname(traverse_dir)
        if parent_dir == traverse_dir:
            break
        
        # 继续遍历父目录
        traverse_dir = parent_dir
    
    # 未找到虚拟环境
    return None


# ---------- 辅助 ----------
def ensure_output_dir() -> None:
    os.makedirs(CONFIG["general"]["output_dir"], exist_ok=True)


def detect_output_artifact(project_name: str) -> str | None:
    """尝试检测最终产物（.exe 或 dist 目录），并返回描述字符串

    Args:
        project_name: 项目名称

    Returns:
        产物路径和大小的描述字符串，若未找到则返回None
    """
    output_dir = CONFIG["general"]["output_dir"]
    # 1) onefile => dist/{project_name}.exe
    exe_path = (
        os.path.join(output_dir, f"{project_name}.exe")
        if IS_WINDOWS
        else os.path.join(output_dir, project_name)
    )
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        return f"{exe_path} ({size_mb:.2f} MB)"
    # 2) standalone folder
    folder = os.path.join(output_dir, project_name)
    if os.path.exists(folder):
        total_size = 0
        for root, _, files in os.walk(folder):
            for f in files:
                try:
                    total_size += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
        return f"{folder} (folder, ~{total_size / (1024*1024):.2f} MB)"
    return None


def process_output_file(project_name: str, start_time: float, build_type: str) -> None:
    """处理并显示打包输出文件信息

    Args:
        project_name: 项目名称
        start_time: 打包开始时间
        build_type: 打包工具类型（PyInstaller 或 Nuitka）
    """
    elapsed_time = time.time() - start_time
    output_dir = CONFIG["general"]["output_dir"]
    print_success(f"{build_type} 打包完成，耗时: {elapsed_time:.2f} 秒")
    print_success(f"输出目录: {os.path.abspath(output_dir)}")
    artifact = detect_output_artifact(project_name)
    if artifact:
        print_success(f"产物: {artifact}")
    else:
        print_warning("未检测到预期的产物，请检查打包输出日志。")


# ---------- 构建函数 ----------
def build_with_pyinstaller(
    project_name: str = "vpn", dry_run: bool = False, verbose: bool = False
) -> None:
    print_section("PyInstaller 打包")
    print_info("使用 Python 模块方式调用 PyInstaller（确保在虚拟环境中）")

    # 检查PyInstaller是否可用
    if not ensure_executable_exists("PyInstaller", module=True):
        print_error("PyInstaller 未安装或不可用。请在当前 Python 环境中安装 pyinstaller。")
        sys.exit(2)

    start_time = time.time()

    # 构建命令
    main_script = CONFIG["general"]["main_script"]
    opts = generate_pyinstaller_options(project_name)
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        *opts,
        main_script,
    ]

    print_info("构建命令预览:")
    if verbose:
        print_info(" ".join(cmd))
    else:
        print_info(shlex.join(cmd))

    ensure_output_dir()

    if dry_run:
        print_info("[dry-run] 未真正执行打包命令。")
        # 清理临时文件
        for opt in opts:
            if opt.startswith("--version-file="):
                version_file_path = opt.split("=")[1]
                if os.path.exists(version_file_path):
                    os.unlink(version_file_path)
        return

    try:
        subprocess.check_call(cmd)
        process_output_file(project_name, start_time, "PyInstaller")
    except subprocess.CalledProcessError as e:
        print_error(f"PyInstaller 打包失败，返回码: {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError as e:
        print_error(f"文件未找到: {e}")
        sys.exit(3)
    finally:
        # 清理临时文件
        for opt in opts:
            if opt.startswith("--version-file="):
                version_file_path = opt.split("=")[1]
                if os.path.exists(version_file_path):
                    os.unlink(version_file_path)


def build_with_nuitka(
    project_name: str = "vpn", dry_run: bool = False, verbose: bool = False
) -> None:
    print_section("Nuitka 打包")
    print_info("使用 Python 模块方式调用 nuitka（确保在虚拟环境中）")

    # 检查Nuitka是否可用
    if not ensure_executable_exists("nuitka", module=True):
        print_error("Nuitka 未安装或不可用。请在当前 Python 环境中安装 nuitka。")
        sys.exit(2)

    start = time.time()
    opts = generate_nuitka_options(project_name)

    main_script = CONFIG["general"]["main_script"]
    cmd = [sys.executable, "-m", "nuitka", *opts, main_script]

    print_info("执行命令预览:")
    if verbose:
        print_info(" ".join(cmd))
    else:
        print_info(shlex.join(cmd))

    ensure_output_dir()

    if dry_run:
        print_info("[dry-run] 未真正执行 nuitka 编译。")
        return

    try:
        subprocess.check_call(cmd)
        process_output_file(project_name, start, "Nuitka")
    except subprocess.CalledProcessError as e:
        print_error(f"Nuitka 编译失败，返回码: {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError as e:
        print_error(f"文件未找到: {e}")
        sys.exit(3)


# ---------- 读取项目名 ----------
def get_project_name() -> str:
    try:
        if os.path.exists("pyproject.toml"):
            with open("pyproject.toml", "r", encoding="utf-8") as f:
                p = toml.load(f)
            return (
                p.get("project", {}).get("name")
                or p.get("tool", {}).get("poetry", {}).get("name")
                or "vpn"
            )
    except Exception as e:
        print_warning(f"读取 pyproject.toml 失败: {e}")
    return "vpn"


# ---------- 读取项目版本号 ----------
def get_project_version() -> str | None:
    try:
        if os.path.exists("pyproject.toml"):
            with open("pyproject.toml", "r", encoding="utf-8") as f:
                p = toml.load(f)
            return (
                p.get("project", {}).get("version")
                or p.get("tool", {}).get("poetry", {}).get("version")
                or None
            )
    except Exception as e:
        print_warning(f"读取 pyproject.toml 版本号失败: {e}")
    return None


# ---------- 格式化版本号为Windows文件版本格式 ----------
def format_windows_version(version: str) -> str:
    """
    将版本号格式化为Windows文件版本格式 (x.y.z.w)
    
    Args:
        version: 原始版本号字符串
        
    Returns:
        格式化后的Windows文件版本字符串
    """
    # 移除预发布版本标识（如 -alpha, -beta1, +build123）

    version = re.sub(r"[-+].*$", "", version)
    
    # 拆分版本号部分
    parts = version.split(".")
    
    # 确保至少有1个部分，最多4个部分
    parts = parts[:4]
    parts += ["0"] * (4 - len(parts))
    
    # 返回格式化的版本号
    return "{}".format(".".join(parts))


# ---------- 获取格式化的Windows版本号元组 ----------
def get_windows_version_tuple(version: str) -> str:
    """
    获取格式化的Windows版本号元组字符串 (x, y, z, w)
    
    Args:
        version: 原始版本号字符串
        
    Returns:
        格式化后的Windows版本号元组字符串
    """
    formatted = format_windows_version(version)
    return formatted.replace(".", ", ")


# ---------- 入口 ----------
def main() -> None:
    print_section("CBuild 编译工具")

    # 检测并使用虚拟环境
    venv_python = detect_virtual_environment()
    if venv_python:
        venv_path = os.path.dirname(os.path.dirname(venv_python))
        print_info(f"检测到虚拟环境: {venv_path}")
        old_python = sys.executable
        sys.executable = venv_python
        print_info(f"Python 解释器已切换: {old_python} -> {venv_python}")
    
    # 加载配置文件
    load_config()
    
    # 如果配置文件是新生成的，提示用户需要修改配置文件，然后退出
    if CONFIG_NEWLY_GENERATED:
        print_warning(f"已生成默认配置文件: {CONFIG_FILE_NAME}")
        print_warning("请根据您的项目需求修改配置文件后再运行编译命令")
        print_warning("例如：修改 main_script 指向您的主脚本文件")
        sys.exit(0)

    # 优先使用配置文件中的build_filename
    build_filename = CONFIG["general"].get("build_filename", "")
    if build_filename and build_filename.strip():
        project_name = build_filename.strip()
        print_info(f"使用配置文件中的输出文件名: {project_name}")
    else:
        project_name = get_project_name()
        print_info(f"使用默认项目名称: {project_name}")

    main_script = CONFIG["general"]["main_script"]
    if not os.path.exists(main_script):
        print_error(f"未找到主脚本: {main_script}")
        sys.exit(4)

    python_ver = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    print_info(f"当前 Python: {python_ver} ({sys.executable})")

    parser = argparse.ArgumentParser(description="选择打包方式")
    parser.add_argument(
        "--pyinstaller", "-p", action="store_true", help="使用 PyInstaller 打包"
    )
    parser.add_argument("--nuitka", "-n", action="store_true", help="使用 Nuitka 打包")
    parser.add_argument(
        "--clean", action="store_true", help="先清理输出目录"
    )  # 取消短参数
    parser.add_argument(
        "--dry-run", "-d", action="store_true", help="仅打印将运行的命令，不实际执行"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="显示完整命令（便于调试）"
    )
    parser.add_argument(
        "--main-script", "-m", type=str, help="指定主脚本文件路径"
    )
    # 输出目录和文件名命令行参数（已优化短参数）
    parser.add_argument(
        "--output-dir", "-D", type=str, help="指定输出目录"
    )
    parser.add_argument(
        "--build-filename", "-f", type=str, help="指定输出文件名"
    )
    # Windows 特定命令行参数（已优化短参数）
    parser.add_argument(
        "--console", "-c", action="store_true", help="显示控制台窗口（Windows）"
    )
    parser.add_argument(
        "--noconsole", "-w", action="store_true", help="隐藏控制台窗口（Windows）"
    )
    parser.add_argument(
        "--uac", "-a", action="store_true", help="请求管理员权限（Windows）"
    )

    args = parser.parse_args()
    if not args.pyinstaller and not args.nuitka:
        print_error("请至少提供一种打包方式：--pyinstaller 或 --nuitka")
        parser.print_help()
        sys.exit(1)

    # 如果命令行指定了主脚本文件，更新CONFIG中的值（优先级高于配置文件）
    if args.main_script:
        CONFIG["general"]["main_script"] = args.main_script
        print_info(f"使用命令行指定的主脚本文件: {args.main_script}")

    # 处理输出目录和文件名命令行参数（优先级高于配置文件）
    if args.output_dir:
        CONFIG["general"]["output_dir"] = args.output_dir
        print_info(f"使用命令行指定的输出目录: {args.output_dir}")
    if args.build_filename:
        # 需要重新计算project_name，因为它可能已经基于配置文件中的build_filename设置了
        project_name = args.build_filename.strip()
        CONFIG["general"]["build_filename"] = args.build_filename
        print_info(f"使用命令行指定的输出文件名: {project_name}")

    # 处理Windows特定命令行参数（优先级高于配置文件）
    if args.console:
        CONFIG["windows"]["console_mode"] = True
        print_info("使用命令行指定：显示控制台窗口")
    if args.noconsole:
        CONFIG["windows"]["console_mode"] = False
        print_info("使用命令行指定：隐藏控制台窗口")
    if args.uac:
        CONFIG["windows"]["uac_admin"] = True
        print_info("使用命令行指定：请求管理员权限")

    output_dir = CONFIG["general"]["output_dir"]
    if args.clean:
        if os.path.exists(output_dir):
            print_info(f"清理输出目录: {output_dir}")
            try:
                shutil.rmtree(output_dir)
            except Exception as e:
                print_warning(f"清理失败: {e}")

    try:
        ensure_output_dir()
        if args.pyinstaller:
            build_with_pyinstaller(
                project_name, dry_run=args.dry_run, verbose=args.verbose
            )
        if args.nuitka:
            build_with_nuitka(project_name, dry_run=args.dry_run, verbose=args.verbose)

        print_section("编译完成")
        print_success("所有打包任务已结束。")
    except KeyboardInterrupt:
        print_error("用户中断")
        sys.exit(130)


if __name__ == "__main__":
    main()