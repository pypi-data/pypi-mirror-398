"""
调试日志模块 - 用于路径配置和指令加载的调试
"""
import os
import time
from datetime import datetime
from typing import Optional


class DebugLogger:
    """调试日志记录器"""
    
    def __init__(self, log_file: str = "log.txt"):
        # 统一使用脚本所在目录，确保日志位置固定
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_path = os.path.join(script_dir, log_file)
        self._init_log()
    
    def _init_log(self):
        """初始化日志文件"""
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(f"\n=== Statistics Log Session Started at {datetime.now()} ===\n")
                f.write(f"Log file: {self.log_path}\n")
                f.write(f"Script dir: {os.path.dirname(os.path.abspath(__file__))}\n")
                f.write("=" * 50 + "\n")
        except Exception as e:
            pass  # 如果无法创建日志文件，静默失败
    
    def log(self, message: str, category: str = "INFO"):
        """写入日志消息"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"{timestamp} [INFO] statistics: [{category}] {message}\n"
            
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception:
            pass  # 如果写入失败，静默失败
    
    def log_path_config(self, script_dir: str, config_type: str = "INIT"):
        """记录路径配置信息"""
        self.log(f"PathConfig {config_type}: script_dir={script_dir}", "PATH")
    
    def log_personal_commands_load(self, prompts_dir: str, exists: bool, use_config: bool):
        """记录个人指令加载信息"""
        source = "路径配置" if use_config else "降级路径"
        self.log(f"加载个人指令，使用{source}: {prompts_dir}", "LOAD")
        self.log(f"个人指令目录是否存在: {exists}", "LOAD")
    
    def log_dir_scan(self, prompts_dir: str, filenames: list, mdc_files: list):
        """记录目录扫描结果"""
        self.log(f"目录扫描 {prompts_dir}", "SCAN")
        self.log(f"所有文件: {filenames}", "SCAN")
        self.log(f"mdc文件: {mdc_files}", "SCAN")
    
    def log_commands_result(self, command_type: str, count: int):
        """记录指令加载结果"""
        self.log(f"加载到{command_type}指令数量: {count}", "RESULT")
    
    def log_save_operation(self, operation: str, path: str, success: bool, error: Optional[str] = None):
        """记录保存操作"""
        status = "成功" if success else "失败"
        self.log(f"{operation}保存{status}: {path}", "SAVE")
        if error:
            self.log(f"错误详情: {error}", "ERROR")
    
    def log_error(self, message: str, module: str = "SYSTEM"):
        """记录ERROR级别日志"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"{timestamp} [ERROR] {module}: {message}\n"
            
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception:
            pass  # 如果写入失败，静默失败
    
    def log_warning(self, message: str, module: str = "SYSTEM"):
        """记录WARNING级别日志"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"{timestamp} [WARNING] {module}: {message}\n"
            
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception:
            pass  # 如果写入失败，静默失败
    
    def log_legacy_error(self, operation: str, error: str):
        """记录错误信息 - 兼容旧版本"""
        self.log(f"{operation}: {error}", "ERROR")
    
    def get_log_path(self) -> str:
        """获取日志文件路径"""
        return self.log_path


# 全局日志实例
_debug_logger = None

def get_debug_logger() -> DebugLogger:
    """获取全局调试日志实例"""
    global _debug_logger
    if _debug_logger is None:
        _debug_logger = DebugLogger()
    return _debug_logger 