#!/usr/bin/env python3
"""
Interactive Feedback MCP - 跨平台安装脚本
仅支持 uv 包管理器，确保依赖版本一致性
"""

import sys
import os
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    print(f"检测到 Python {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 10):
        print("❌ 错误: 需要 Python 3.10 或更高版本")
        print("   FastMCP 2.5.1 要求 Python 3.10+")
        print("请升级Python版本后重试")
        sys.exit(1)
    
    print("✅ Python版本符合要求")
    
    # 特别欢迎Python 3.13用户
    if version >= (3, 13):
        print("🎉 检测到Python 3.13！享受最新特性：")
        print("   • 改进的交互式解释器")
        print("   • 实验性JIT编译器") 
        print("   • 无GIL模式支持")
    elif version >= (3, 12):
        print("⚡ Python 3.12 - 性能优化版本")
    elif version >= (3, 11):
        print("🚀 Python 3.11 - 高性能版本")

def check_uv_available():
    """检查 uv 是否可用"""
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, check=True, text=True)
        print(f"✅ 检测到 uv: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_uv():
    """安装 uv 包管理器"""
    print("正在安装 uv 包管理器...")
    system = platform.system().lower()
    
    try:
        if system == "windows":
            # Windows: 使用 PowerShell 安装
            print("使用 PowerShell 安装 uv...")
            subprocess.run([
                'powershell', '-Command',
                'irm https://astral.sh/uv/install.ps1 | iex'
            ], check=True)
        else:
            # macOS/Linux: 使用官方安装脚本
            print("使用官方脚本安装 uv...")
            subprocess.run([
                'curl', '-LsSf', 'https://astral.sh/uv/install.sh', '|', 'sh'
            ], check=True)
        
        # 验证安装
        if check_uv_available():
            print("✅ uv 安装成功")
            return True
        else:
            print("❌ uv 安装失败，请手动安装")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ uv 安装失败: {e}")
        print("请手动安装 uv: https://astral.sh/uv/")
        return False

def ensure_uv():
    """确保 uv 可用"""
    if check_uv_available():
        return True
    
    print("未检测到 uv 包管理器")
    print("uv 是现代化的 Python 包管理器，提供:")
    print("  • 极快的依赖解析和安装速度")
    print("  • 严格的版本锁定确保一致性")
    print("  • 更好的错误处理和用户体验")
    print()
    
    response = input("是否自动安装 uv? (y/N): ").lower().strip()
    if response in ['y', 'yes']:
        return install_uv()
    else:
        print("❌ 本项目仅支持 uv 安装以确保依赖版本一致性")
        print("请先安装 uv: https://astral.sh/uv/")
        sys.exit(1)

def create_virtual_environment():
    """使用 uv 创建虚拟环境"""
    venv_path = Path('.venv')
    
    if venv_path.exists():
        print("虚拟环境已存在，跳过创建")
        return venv_path
    
    print("正在使用 uv 创建虚拟环境...")
    
    try:
        subprocess.run(['uv', 'venv'], check=True)
        print("✅ 虚拟环境创建成功")
        return venv_path
    except subprocess.CalledProcessError as e:
        print(f"❌ 虚拟环境创建失败: {e}")
        sys.exit(1)

def install_dependencies():
    """使用 uv 安装依赖"""
    print("正在使用 uv 安装依赖包...")
    
    # 检查必要文件
    pyproject_file = Path('pyproject.toml')
    uv_lock_file = Path('uv.lock')
    
    if not pyproject_file.exists():
        print("❌ 错误: 未找到 pyproject.toml")
        print("请确保在正确的项目目录中运行此脚本")
        sys.exit(1)
    
    if not uv_lock_file.exists():
        print("⚠️  警告: 未找到 uv.lock，将生成新的锁定文件")
        print("这可能导致版本不一致，建议使用项目提供的 uv.lock")
    
    try:
        # 使用 uv sync 安装精确锁定的依赖
        print("使用 uv.lock 安装精确版本依赖...")
        subprocess.run(['uv', 'sync'], check=True)
        print("✅ 依赖安装成功")
        print("所有依赖版本已按 uv.lock 精确锁定")
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        print("可能的解决方案:")
        print("  • 检查网络连接")
        print("  • 尝试使用不同的镜像源")
        print("  • 删除 .venv 目录后重试")
        sys.exit(1)

def test_installation():
    """测试安装是否成功"""
    print("正在测试安装...")
    
    # 测试关键模块导入
    test_imports = [
        ('fastmcp', 'FastMCP MCP服务器框架'),
        ('PySide6', 'Qt GUI框架'),
        ('pydantic', '数据验证库'),
        ('mcp.server.fastmcp.utilities.types', 'MCP类型定义'),
    ]
    
    failed_imports = []
    success_count = 0
    
    for module, description in test_imports:
        try:
            if module == 'mcp.server.fastmcp.utilities.types':
                # 特别测试 MCPImage 兼容性
                from mcp.server.fastmcp.utilities.types import Image as MCPImage
                from pydantic import Field
                from typing import List, Union
                from mcp.types import TextContent
                
                # 测试类型注解是否有问题
                def test_func() -> List[Union[TextContent, MCPImage]]:
                    return []
                
                print(f"✅ MCPImage 兼容性测试通过")
            else:
                __import__(module)
                print(f"✅ {module} ({description}) 导入成功")
            success_count += 1
        except ImportError as e:
            failed_imports.append((module, description, str(e)))
            print(f"❌ {module} ({description}) 导入失败: {e}")
        except Exception as e:
            failed_imports.append((module, description, f"兼容性错误: {e}"))
            print(f"❌ {module} ({description}) 兼容性错误: {e}")
    
    if failed_imports:
        print(f"\n❌ {len(failed_imports)} 个模块测试失败:")
        for module, desc, error in failed_imports:
            print(f"   • {module}: {error}")
        return False
    
    print(f"\n✅ 所有 {success_count} 个模块测试通过")
    print("✅ FastMCP + Pydantic 兼容性验证成功")
    return True

def get_activation_command():
    """获取虚拟环境激活命令"""
    system = platform.system().lower()
    
    if system == "windows":
        return ".venv\\Scripts\\activate"
    else:
        return "source .venv/bin/activate"

def show_usage_info():
    """显示使用说明"""
    print("\n" + "=" * 60)
    print("🎉 安装完成！Interactive Feedback MCP 已就绪")
    print("=" * 60)
    
    # 显示版本信息
    try:
        result = subprocess.run(['uv', 'run', 'python', '-c', 
                               'import pydantic, fastmcp; print(f"Pydantic: {pydantic.__version__}, FastMCP: {fastmcp.__version__}")'], 
                              capture_output=True, text=True, check=True)
        print(f"📦 已安装版本: {result.stdout.strip()}")
    except:
        pass
    
    print(f"\n🔧 环境激活: {get_activation_command()}")
    print("\n🚀 启动服务:")
    print("   • MCP服务器: uv run server.py")
    print("   • 反馈界面: uv run feedback_ui.py")
    
    print("\n💡 推荐使用 uv run 命令确保环境一致性")
    print("💡 所有依赖版本已通过 uv.lock 精确锁定")

def main():
    """主函数"""
    print("=" * 60)
    print("Interactive Feedback MCP - 现代化安装脚本")
    print("仅支持 uv 包管理器，确保版本一致性")
    print("=" * 60)
    
    # 检查Python版本
    check_python_version()
    
    # 确保 uv 可用
    ensure_uv()
    
    # 创建虚拟环境
    venv_path = create_virtual_environment()
    
    # 安装依赖
    install_dependencies()
    
    # 测试安装
    if test_installation():
        show_usage_info()
    else:
        print("\n❌ 安装验证失败，请检查错误信息")
        print("如需帮助，请查看项目文档或提交Issue")
        sys.exit(1)

if __name__ == "__main__":
    main() 