"""
工作空间管理器 - 处理工作空间和阶段信息
"""
import os
import json
import yaml
from typing import Optional, Dict, Any, Tuple
from pathlib import Path


class WorkspaceManager:
    """工作空间管理器"""

    def __init__(self, project_path: str = None):
        """初始化工作空间管理器

        Args:
            project_path: 项目路径，如果不提供则使用当前工作目录
        """
        if project_path:
            self.project_path = Path(project_path)
        else:
            # 尝试找到项目根目录
            current_path = Path.cwd()
            while current_path != current_path.parent:
                if (current_path / '.workspace').exists():
                    self.project_path = current_path
                    break
                current_path = current_path.parent
            else:
                self.project_path = Path.cwd()

        self.workspace_dir = self.project_path / '.workspace'
        self.workflows_dir = self.project_path / '.claude' / 'workflows'

    def get_workspace_id_by_session(self, session_id: str) -> Optional[str]:
        """根据session_id获取workspace_id

        Args:
            session_id: 会话ID

        Returns:
            workspace_id 或 None
        """
        session_map_path = self.workspace_dir / 'session_map.json'
        if not session_map_path.exists():
            return None

        try:
            with open(session_map_path, 'r', encoding='utf-8') as f:
                session_map = json.load(f)

            # 查找workspace_mappings
            workspace_mappings = session_map.get('workspace_mappings', {})
            return workspace_mappings.get(session_id)
        except Exception as e:
            print(f"Error reading session_map.json: {e}")
            return None

    def load_workspace_config(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """加载工作空间配置

        Args:
            workspace_id: 工作空间ID

        Returns:
            工作空间配置字典 或 None
        """
        workspace_path = self.workspace_dir / workspace_id / 'workspace.yml'
        if not workspace_path.exists():
            return None

        try:
            with open(workspace_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error reading workspace.yml: {e}")
            return None

    def load_stage_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """加载阶段模板

        Args:
            template_id: 模板ID或完整文件路径

        Returns:
            阶段模板配置 或 None
        """
        # 判断是否为完整路径
        if '/' in template_id or template_id.endswith('.yml'):
            # 直接使用路径
            template_path = Path(template_id)
        else:
            # 兼容旧逻辑：拼接路径
            template_path = self.workflows_dir / f'{template_id}.yml'

        if not template_path.exists():
            return None

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error reading stage template: {e}")
            return None

    def get_stage_info(self, session_id: str = None, workspace_id: str = None) -> Optional[Dict[str, Any]]:
        """获取阶段信息

        Args:
            session_id: 会话ID（如果提供了workspace_id则可选）
            workspace_id: 工作空间ID（优先使用，如果不提供则通过session_id查找）

        Returns:
            包含当前阶段、上一阶段、下一阶段信息的字典
        """
        # 1. 获取workspace_id
        if not workspace_id:
            if not session_id:
                return None
            workspace_id = self.get_workspace_id_by_session(session_id)
            if not workspace_id:
                return None

        # 2. 加载workspace配置
        workspace_config = self.load_workspace_config(workspace_id)
        if not workspace_config:
            return None

        # 3. 获取阶段模板和当前阶段
        stage_template_id = workspace_config.get('stage_template_id')
        current_stage_id = workspace_config.get('current_stage_id')

        if not stage_template_id or not current_stage_id:
            return None

        # 4. 加载阶段模板
        template_config = self.load_stage_template(stage_template_id)
        if not template_config:
            return None

        # 5. 解析阶段信息
        workflow = template_config.get('workflow', {})
        steps = workflow.get('steps', [])

        if not steps:
            return None

        # 找到当前阶段索引
        current_index = -1
        for i, step in enumerate(steps):
            if step.get('id') == current_stage_id:
                current_index = i
                break

        if current_index == -1:
            return None

        # 构建阶段信息
        result = {
            'workspace_id': workspace_id,
            'current_stage': {
                'id': steps[current_index].get('id'),
                'title': steps[current_index].get('title'),
                'description': steps[current_index].get('des')
            }
        }

        # 上一阶段
        if current_index > 0:
            result['prev_stage'] = {
                'id': steps[current_index - 1].get('id'),
                'title': steps[current_index - 1].get('title'),
                'description': steps[current_index - 1].get('des')
            }
        else:
            result['prev_stage'] = None

        # 下一阶段
        if current_index < len(steps) - 1:
            result['next_stage'] = {
                'id': steps[current_index + 1].get('id'),
                'title': steps[current_index + 1].get('title'),
                'description': steps[current_index + 1].get('des')
            }
        else:
            result['next_stage'] = None

        return result


def get_stage_info_for_session(session_id: str, project_path: str = None) -> Optional[Dict[str, Any]]:
    """便捷函数：获取指定会话的阶段信息

    Args:
        session_id: 会话ID
        project_path: 项目路径

    Returns:
        阶段信息字典
    """
    manager = WorkspaceManager(project_path)
    return manager.get_stage_info(session_id)


def get_workspace_goal_for_session(session_id: str, project_path: str = None) -> Optional[str]:
    """便捷函数：获取指定会话的工作空间goal

    Args:
        session_id: 会话ID
        project_path: 项目路径

    Returns:
        工作空间goal或None
    """
    manager = WorkspaceManager(project_path)
    workspace_id = manager.get_workspace_id_by_session(session_id)
    if not workspace_id:
        return None

    workspace_config = manager.load_workspace_config(workspace_id)
    if not workspace_config:
        return None

    return workspace_config.get('goal')


def get_session_title_for_session(session_id: str, project_path: str = None) -> Optional[str]:
    """便捷函数：获取指定会话的对话标题

    Args:
        session_id: 会话ID
        project_path: 项目路径

    Returns:
        对话标题或None
    """
    manager = WorkspaceManager(project_path)
    workspace_id = manager.get_workspace_id_by_session(session_id)
    if not workspace_id:
        return None

    workspace_config = manager.load_workspace_config(workspace_id)
    if not workspace_config:
        return None

    # 从sessions列表中查找匹配的session
    sessions = workspace_config.get('sessions', [])
    for session in sessions:
        if session.get('id') == session_id:
            return session.get('title')

    return None