"""
路径配置模块 - 统一管理应用程序各种文件路径
"""
import os
from typing import Optional

# 导入调试日志模块
try:
    from debug_logger import get_debug_logger
    DEBUG_LOG_AVAILABLE = True
except ImportError:
    DEBUG_LOG_AVAILABLE = False


class PathConfig:
    """路径配置管理类"""
    
    def __init__(self, project_path: Optional[str] = None):
        # 获取脚本文件所在目录
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        # 设置项目路径
        self.project_path = project_path
        
        # 记录路径配置初始化
        if DEBUG_LOG_AVAILABLE:
            logger = get_debug_logger()
            logger.log_path_config(self.script_dir, "INIT")
    
    # 已移除个人指令目录，只保留项目指令

    def get_plugins_config_path(self) -> str:
        """获取插件配置文件路径（支持 Windows/macOS/Linux）"""
        claude_dir = os.path.expanduser("~/.claude")
        return os.path.join(claude_dir, "plugins", "installed_plugins.json")

    def get_settings_path(self) -> str:
        """获取 Claude 设置文件路径（支持 Windows/macOS/Linux）"""
        claude_dir = os.path.expanduser("~/.claude")
        return os.path.join(claude_dir, "settings.json")

    def get_project_commands_dir(self, project_path: Optional[str] = None) -> Optional[str]:
        """获取项目指令目录路径"""
        target_project_path = project_path or self.project_path
        if not target_project_path:
            return None
        path = os.path.join(target_project_path, ".claude", "commands")
        return os.path.abspath(path)
    
    def get_project_commands_display_path(self) -> str:
        """获取项目指令目录的显示名称"""
        return ".claude/commands/"
    
    def get_env_file_path(self, project_path: Optional[str] = None) -> Optional[str]:
        """获取项目的.agent/.env文件路径"""
        target_project_path = project_path or self.project_path
        if not target_project_path:
            return None
        
        env_path = os.path.join(target_project_path, '.agent', '.env')
        return os.path.abspath(env_path)
    
    # 已移除ensure_personal_commands_dir方法
    
    def ensure_project_commands_dir(self, project_path: str) -> str:
        """确保项目指令目录存在，返回路径"""
        path = self.get_project_commands_dir(project_path)
        if path:
            try:
                os.makedirs(path, exist_ok=True)
                if DEBUG_LOG_AVAILABLE:
                    logger = get_debug_logger()
                    logger.log_save_operation("项目指令目录创建", path, True)
            except Exception as e:
                if DEBUG_LOG_AVAILABLE:
                    logger = get_debug_logger()
                    logger.log_save_operation("项目指令目录创建", path, False, str(e))
                raise
        return path


# 全局路径配置实例
_path_config = None

def get_path_config(project_path: Optional[str] = None) -> PathConfig:
    """获取全局路径配置实例"""
    global _path_config
    if _path_config is None or project_path:
        _path_config = PathConfig(project_path)
    return _path_config 