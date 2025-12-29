#!/usr/bin/env python3
import os
import requests
import datetime
import logging
from pathlib import Path
from dotenv import load_dotenv

# 导入统一日志系统
from debug_logger import get_debug_logger

# 导入路径配置模块
try:
    from path_config import get_path_config
    PATH_CONFIG_AVAILABLE = True
except ImportError:
    PATH_CONFIG_AVAILABLE = False

# 全局变量
_project_path = None
_env_loaded = False

def setup_stats_logger():
    """设置统计日志，统一保存到脚本所在目录"""
    logger = logging.getLogger('statistics')
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # 统一使用脚本所在目录，确保日志位置固定
        script_dir = Path(__file__).parent
        log_file = script_dir / "log.txt"
        
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# 创建全局统计日志实例
stats_logger = setup_stats_logger()

def get_absolute_path(path: str, base_dir: str) -> str:
    """将路径转换为绝对路径
    如果是绝对路径直接返回，否则基于base_dir转换为绝对路径
    """
    if not path:
        return path
    return path if os.path.isabs(path) else os.path.join(base_dir, path)

def set_project_path(project_path: str):
    """设置项目路径并加载对应的.env文件"""
    global _project_path, _env_loaded
    _project_path = project_path
    
    if not project_path:
        logger = get_debug_logger()
        logger.log_warning("统计模块：未提供项目路径", "STATS")
        return
    
    if PATH_CONFIG_AVAILABLE:
        # 使用path_config获取.env文件路径
        path_config = get_path_config(project_path)
        env_path = path_config.get_env_file_path()
        
        if env_path and os.path.exists(env_path):
            load_dotenv(env_path)
            _env_loaded = True
        else:
            logger = get_debug_logger()
            logger.log_warning(f"统计模块未找到.env文件: {env_path}", "STATS")
    else:
        # 兜底方案：直接拼接路径
        env_path = os.path.join(project_path, '.agent', '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
            _env_loaded = True
        else:
            logger = get_debug_logger()
            logger.log_warning(f"统计模块兜底也未找到.env文件: {env_path}", "STATS")

def get_user_info():
    """从GitLab认证文件获取用户信息 - 功能已移除

    Returns:
        Tuple[str, str]: (user_id, user_name)
    """
    # GitLab认证功能已移除
    logger = get_debug_logger()
    logger.log_info("GitLab认证功能已移除", "STATS")
    return None, None

def report_action(data):
    """向API上报操作数据

    Args:
        data (dict): 上报数据对象，包含以下字段：
            - user_name (str): 用户名(必填)
            - action (str): 操作类型，如'执行工作流'、'工作流:下一步'等(必填)
            - content (str, optional): 操作内容详情，默认为空字符串
            - workflow_name (str, optional): 工作流名称，默认为空字符串
            - task_name (str, optional): 任务名称，默认为空字符串
            - step_name (str, optional): 步骤名称，默认为空字符串
            - task_id (str, optional): 任务ID，默认为空字符串
            其他字段会作为扩展字段一起上报

    Returns:
        bool: 上报是否成功

    Raises:
        ValueError: 当必填字段缺失时抛出异常
    """
    if not data.get('action'):
        raise ValueError("action 是必填字段")

    # 获取当前时间戳(毫秒)
    current_time = int(datetime.datetime.now().timestamp() * 1000)

    # 定义所有必要字段及其默认值
    user_id, user_name = get_user_info()
    required_fields = {
        'user_name': user_name,  # 必填，但已经在上面检查过了
        'action': '',     # 必填，但已经在上面检查过了
        'content': '',
        'workflow_name': '',
        'task_name': '',
        'step_name': '',
        'task_id': '',
        'time': current_time
    }

    # 使用默认值填充缺失字段
    for field, default_value in required_fields.items():
        data.setdefault(field, default_value)

    try:
        stats_logger.info(f"开始上报统计: action={data['action']}, user={user_name}")
        response = requests.post('https://gitstat.aqwhr.cn/tapd/user-action-data/save', json=data)
        stats_logger.info(f"统计上报成功: status={response.status_code}, action={data['action']}")
        return response.status_code == 200
    except Exception as e:
        stats_logger.error(f"统计上报失败: {e}")
        return False

if __name__ == '__main__':
    # 测试用户信息获取
    user_id, user_name = get_user_info()
    print(f"User ID: {user_id}, User Name: {user_name}")

    # 测试数据上报
    if user_name:
        # 测试基本上报
        success = report_action({
            'user_name': user_name,
            'action': '测试上报',
            'content': '测试内容'
        })
        print(f"Basic report result: {'Success' if success else 'Failed'}")

        # 测试完整参数上报
        success = report_action({
            'user_name': user_name,
            'action': '工作流执行',
            'content': '执行开发工作流',
            'workflow_name': '开发工作流',
            'task_name': '代码开发',
            'step_name': '编写功能',
            'task_id': '1'
        })
        print(f"Full report result: {'Success' if success else 'Failed'}")

        # 测试带扩展字段的上报
        success = report_action({
            'user_name': user_name,
            'action': '自定义事件',
            'content': '测试扩展字段',
            'custom_field': '自定义值',
            'extra_info': {
                'key1': 'value1',
                'key2': 'value2'
            }
        })
        print(f"Extended report result: {'Success' if success else 'Failed'}")
