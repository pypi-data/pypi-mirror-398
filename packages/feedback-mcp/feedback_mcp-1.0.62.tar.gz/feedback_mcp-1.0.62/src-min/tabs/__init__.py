"""
标签页模块 - 导出所有标签页组件
"""

# 基础标签页
try:
    from .base_tab import BaseTab
except ImportError:
    BaseTab = None

# 简单标签页
try:
    from .workflow_tab import WorkflowTab
except ImportError:
    WorkflowTab = None

try:
    from .taskflow_tab import TaskflowTab
except ImportError:
    TaskflowTab = None

try:
    from .new_work_tab import NewWorkTab
except ImportError:
    NewWorkTab = None

# 复杂标签页 - 分别导入，避免一个失败影响其他
try:
    from .chat_tab import ChatTab
except ImportError:
    ChatTab = None

try:
    from .stats_tab import StatsTab
except ImportError:
    StatsTab = None

try:
    from .memory_tab import MemoryTab
except ImportError:
    MemoryTab = None

try:
    from .rules_tab import RulesTab
except ImportError:
    RulesTab = None

try:
    from .todos_tab import TodosTab
except ImportError:
    TodosTab = None

try:
    from .checkpoints_tab import CheckpointsTab
except ImportError:
    CheckpointsTab = None

try:
    from .new_project_tab import NewProjectTab
except ImportError:
    NewProjectTab = None

try:
    from .workspace_tab import WorkspaceTab
except ImportError:
    WorkspaceTab = None

try:
    from .chat_history_tab import ChatHistoryTab
except ImportError:
    ChatHistoryTab = None

__all__ = [
    'BaseTab',
    'WorkflowTab',
    'TaskflowTab',
    'NewWorkTab',
    'ChatTab',
    'ChatHistoryTab',
    'StatsTab',
    'MemoryTab',
    'RulesTab',
    'TodosTab',
    'CheckpointsTab',
    'NewProjectTab',
    'WorkspaceTab'
] 