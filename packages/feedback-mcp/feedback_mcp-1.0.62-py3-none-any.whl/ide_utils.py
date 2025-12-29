"""
IDE 操作工具模块
提供打开各种IDE的通用功能
"""
import os
import subprocess
import platform
import time
import shutil
from typing import Optional, Dict, Any


def open_project_with_ide(project_path: str, ide_name: str = None) -> bool:
    """
    使用指定IDE打开项目

    Args:
        project_path: 项目路径
        ide_name: IDE名称(cursor/kiro/vscode)，如果为None则使用系统默认

    Returns:
        bool: 操作是否成功
    """
    if not project_path or not os.path.exists(project_path):
        return False

    if not ide_name:
        return False  # 不设置默认IDE,必须明确指定

    # 获取IDE命令
    ide_command = get_ide_command(ide_name)
    if not ide_command:
        return False

    # 检查IDE是否可用
    if not is_ide_available(ide_name):
        return False

    try:
        system = platform.system()

        if system == 'Darwin':  # macOS
            return _open_ide_macos(project_path, ide_name, ide_command)
        elif system == 'Windows':  # Windows
            return _open_ide_windows(project_path, ide_name, ide_command)
        else:  # Linux
            return _open_ide_linux(project_path, ide_name, ide_command)

    except Exception as e:
        print(f"打开IDE异常: {e}")
        return False


def get_ide_command(ide_name: str) -> str:
    """
    获取IDE的启动命令

    Args:
        ide_name: IDE名称

    Returns:
        str: IDE启动命令
    """
    # 支持预设的IDE映射
    ide_commands = {
        "cursor": "cursor",
        "kiro": "kiro",
        "vscode": "code"
    }

    # 如果在预设列表中，使用映射的命令
    if ide_name.lower() in ide_commands:
        return ide_commands[ide_name.lower()]

    # 否则直接使用IDE名称作为命令（支持动态IDE）
    return ide_name.lower()


def is_ide_available(ide_name: str) -> bool:
    """
    检查指定IDE是否可用

    Args:
        ide_name: IDE名称

    Returns:
        bool: IDE是否可用
    """
    import platform
    import os

    command = get_ide_command(ide_name)

    # 首先检查命令行工具
    if shutil.which(command) is not None:
        return True

    # 针对不同操作系统的特殊处理
    system = platform.system()

    if system == 'Darwin':  # macOS
        app_map = {
            "cursor": "Cursor",
            "kiro": "Kiro",
            "code": "Visual Studio Code",
            "vscode": "Visual Studio Code"  # 修复VS Code检测
        }

        # 使用command而不是ide_name进行查找（修复bug）
        if command in app_map:
            app_name = app_map[command]
        else:
            # 动态IDE支持：尝试使用IDE名称的首字母大写形式
            app_name = ide_name.capitalize() if ide_name.islower() else ide_name

        # 检查应用程序包是否存在
        app_paths = [
            f"/Applications/{app_name}.app",
            f"/Users/{os.environ.get('USER', 'user')}/Applications/{app_name}.app"
        ]

        for app_path in app_paths:
            if os.path.exists(app_path):
                return True

    elif system == 'Windows':  # Windows
        app_map = {
            "cursor": "Cursor",
            "kiro": "Kiro",
            "code": "Code",
            "vscode": "Code"  # 修复VS Code检测
        }

        # 使用command而不是ide_name进行查找（修复bug）
        if command in app_map:
            app_name = app_map[command]
        else:
            # 动态IDE支持：尝试使用IDE名称的首字母大写形式
            app_name = ide_name.capitalize() if ide_name.islower() else ide_name

        # 检查常见的Windows安装路径
        common_paths = [
            f"C:\\Users\\{os.environ.get('USERNAME', 'user')}\\AppData\\Local\\Programs\\{app_name}\\{app_name}.exe",
            f"C:\\Program Files\\{app_name}\\{app_name}.exe",
            f"C:\\Program Files (x86)\\{app_name}\\{app_name}.exe"
        ]

        for path in common_paths:
            if os.path.exists(path):
                return True

    elif system == 'Linux':  # Linux
        app_map = {
            "cursor": "cursor",
            "kiro": "kiro",
            "code": "code",
            "vscode": "code"  # 修复VS Code检测
        }

        # 使用command而不是ide_name进行查找（修复bug）
        if command in app_map:
            app_name = app_map[command]
        else:
            # 动态IDE支持：直接使用命令名
            app_name = command

        # 检查常见的Linux安装路径
        common_paths = [
            f"/opt/{app_name}/{app_name}",
            f"/usr/local/{app_name}/{app_name}",
            f"/usr/bin/{app_name}",
            f"/snap/bin/{app_name}"
        ]

        for path in common_paths:
            if os.path.exists(path):
                return True
    
    return False


def _open_ide_macos(project_path: str, ide_name: str, ide_command: str) -> bool:
    """macOS平台打开IDE"""
    try:
        app_map = {
            "cursor": "Cursor",
            "kiro": "Kiro",
            "vscode": "Visual Studio Code",
            "code": "Visual Studio Code"  # 支持code命令映射
        }

        # 尝试根据命令名获取应用名
        app_name = app_map.get(ide_command) or app_map.get(ide_name)

        if not app_name:
            # 动态IDE支持：尝试使用IDE名称的首字母大写形式作为应用名
            app_name = ide_name.capitalize() if ide_name.islower() else ide_name

        # 优先使用open命令打开应用
        result = subprocess.run(['open', '-a', app_name, project_path],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # 确保应用在前台
            subprocess.run(['osascript', '-e', f'tell application "{app_name}" to activate'],
                         capture_output=True, text=True, timeout=3)
            return True

        # 如果open命令失败，尝试命令行方式
        if shutil.which(ide_command) is not None:
            result = subprocess.run([ide_command, project_path],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0

        return False

    except Exception as e:
        print(f"macOS下打开{ide_name}失败: {e}")
        return False


def _open_ide_windows(project_path: str, ide_name: str, ide_command: str) -> bool:
    """Windows平台打开IDE"""
    try:
        # Windows下直接调用命令
        result = subprocess.run([ide_command, project_path], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
        
    except Exception as e:
        print(f"Windows下打开{ide_name}失败: {e}")
        return False


def _open_ide_linux(project_path: str, ide_name: str, ide_command: str) -> bool:
    """Linux平台打开IDE"""
    try:
        result = subprocess.run([ide_command, project_path], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
        
    except Exception as e:
        print(f"Linux下打开{ide_name}失败: {e}")
        return False


# 以下是为了向后兼容而保留的函数
def focus_cursor_to_project(project_path: str) -> bool:
    """
    向后兼容：macOS平台下聚焦Cursor到指定项目路径
    
    Args:
        project_path: 项目路径
        
    Returns:
        bool: 操作是否成功
    """
    return open_project_with_ide(project_path, "cursor")


def is_cursor_available() -> bool:
    """
    向后兼容：检查系统是否安装了Cursor
    
    Returns:
        bool: Cursor是否可用
    """
    return is_ide_available("cursor")


def get_ide_info(ide_name: str) -> Dict[str, Any]:
    """
    获取IDE的详细信息
    
    Args:
        ide_name: IDE名称
        
    Returns:
        dict: IDE详细信息
    """
    ide_info_map = {
        "cursor": {
            "name": "Cursor",
            "command": "cursor",
            "description": "AI驱动的代码编辑器",
            "platforms": ["Darwin", "Windows", "Linux"]
        },
        "kiro": {
            "name": "Kiro",
            "command": "kiro", 
            "description": "现代化的代码编辑器",
            "platforms": ["Darwin", "Windows", "Linux"]
        },
        "vscode": {
            "name": "VS Code",
            "command": "code",
            "description": "微软的轻量级代码编辑器",
            "platforms": ["Darwin", "Windows", "Linux"]
        }
    }
    
    info = ide_info_map.get(ide_name, {})
    info["available"] = is_ide_available(ide_name)
    return info


def is_macos() -> bool:
    """
    向后兼容：检查是否为macOS系统
    
    Returns:
        bool: 是否为macOS
    """
    return platform.system() == 'Darwin' 