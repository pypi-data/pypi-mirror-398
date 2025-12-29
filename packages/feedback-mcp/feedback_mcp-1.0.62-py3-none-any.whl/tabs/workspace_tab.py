"""
工作空间标签页 - 显示工作空间信息
"""
import os
import re
import subprocess
import platform
from typing import Optional
from functools import partial
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QMessageBox, QGridLayout, QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QBrush, QColor

try:
    from .base_tab import BaseTab
except ImportError:
    from base_tab import BaseTab

try:
    from ..components.markdown_display import MarkdownDisplayWidget
except ImportError:
    try:
        from components.markdown_display import MarkdownDisplayWidget
    except ImportError:
        from PySide6.QtWidgets import QTextEdit
        MarkdownDisplayWidget = QTextEdit

try:
    from ..workspace_manager import WorkspaceManager
except ImportError:
    try:
        from workspace_manager import WorkspaceManager
    except ImportError:
        WorkspaceManager = None


class WorkspaceTab(BaseTab):
    """工作空间标签页 - 显示工作空间详细信息"""

    def __init__(self, workspace_id: str, project_path: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.workspace_id = workspace_id
        self.project_path = project_path
        self.workspace_config = None
        self.stage_template = None

        # 加载工作空间配置
        self._load_workspace_config()

        # 创建UI
        self.create_ui()

    def _load_workspace_config(self):
        """加载工作空间配置"""
        if not WorkspaceManager:
            return

        try:
            manager = WorkspaceManager(self.project_path)
            self.workspace_config = manager.load_workspace_config(self.workspace_id)

            # 加载阶段模板
            if self.workspace_config:
                stage_template_id = self.workspace_config.get('stage_template_id')
                if stage_template_id:
                    self.stage_template = manager.load_stage_template(stage_template_id)
        except Exception:
            # 静默处理加载失败
            self.workspace_config = None
            self.stage_template = None

    def create_ui(self):
        """创建工作空间标签页UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 使用 MarkdownDisplayWidget 显示工作空间基本信息
        display_widget = MarkdownDisplayWidget()

        # 格式化工作空间信息为Markdown
        markdown_content = self._format_workspace_info()
        display_widget.setMarkdownText(markdown_content)

        layout.addWidget(display_widget)

        # 添加文件列表区域（如果有文件）
        files = self.workspace_config.get('files', []) if self.workspace_config else []
        if files:
            self._create_files_section(layout, files)

    def _format_workspace_info(self) -> str:
        """格式化工作空间信息为Markdown文本

        Returns:
            str: 格式化的Markdown文本
        """
        if not self.workspace_config:
            return "## ⚠️ 无法加载工作空间配置\n\n请检查工作空间ID是否正确。"

        parts = []

        # 1. 工作空间基本信息
        parts.append("## 📦 工作空间信息")
        parts.append("")
        parts.append(f"**ID:** `{self.workspace_id}`")

        goal = self.workspace_config.get('goal', '未设置')
        parts.append(f"**目标:** {goal}")

        status = self.workspace_config.get('status', '未知')
        parts.append(f"**状态:** {status}")

        created_at = self.workspace_config.get('created_at', '未知')
        parts.append(f"**创建时间:** {created_at}")

        updated_at = self.workspace_config.get('updated_at', '未知')
        parts.append(f"**更新时间:** {updated_at}")

        parts.append("")

        # 2. 阶段信息
        parts.append("## 📍 阶段信息")
        parts.append("")

        stage_template_id = self.workspace_config.get('stage_template_id', '未设置')
        parts.append(f"**模板:** `{stage_template_id}`")

        current_stage_id = self.workspace_config.get('current_stage_id', '未设置')
        parts.append(f"**当前阶段:** `{current_stage_id}`")

        # 显示当前阶段详细信息
        if self.stage_template and current_stage_id:
            workflow = self.stage_template.get('workflow', {})
            steps = workflow.get('steps', [])

            for step in steps:
                if step.get('id') == current_stage_id:
                    parts.append("")
                    parts.append(f"**阶段标题:** {step.get('title', '未知')}")
                    parts.append(f"**阶段描述:** {step.get('des', '无描述')}")
                    break

        parts.append("")

        # 3. 相关文档列表
        documents = self.workspace_config.get('documents', [])
        if documents:
            parts.append("## 📄 相关文档")
            parts.append("")
            for doc in documents:
                if isinstance(doc, dict):
                    title = doc.get('title', '未命名文档')
                    path = doc.get('path', '')
                    parts.append(f"- **{title}** (`{path}`)")
                else:
                    parts.append(f"- `{doc}`")
            parts.append("")

        # 注意：相关文件列表改为独立组件显示，不再在Markdown中显示

        return "\n".join(parts)

    def _create_files_section(self, layout, files: list):
        """创建文件列表显示区域（树形结构）

        Args:
            layout: 父布局
            files: 文件路径列表
        """
        # 导入配置管理
        try:
            from feedback_config import FeedbackConfig
        except ImportError:
            FeedbackConfig = None

        # 获取配置的IDE
        def get_configured_ide():
            """获取配置的IDE名称，优先级：配置文件 > 环境变量 > 默认值"""
            ide_name = None

            # 1. 尝试从配置文件读取
            if FeedbackConfig and self.project_path:
                try:
                    config_manager = FeedbackConfig(self.project_path)
                    ide_name = config_manager.get_ide()
                except Exception:
                    pass

            # 2. 如果配置文件没有，使用环境变量
            if not ide_name:
                ide_name = os.getenv('IDE')

            # 3. 最后使用默认值
            if not ide_name:
                ide_name = 'cursor'

            return ide_name

        # 文件去重并保持顺序
        unique_files = list(dict.fromkeys(files))

        # 路径规范化（移除tag前缀 + 相对路径转绝对路径）
        normalized_files = []
        for file_path in unique_files:
            # 移除路径开头的tag（如 Edit:, Create:, Read: 等）
            cleaned_path = re.sub(r'^[A-Za-z]+:', '', file_path)

            if not os.path.isabs(cleaned_path) and self.project_path:
                # 相对路径转绝对路径
                abs_path = os.path.join(self.project_path, cleaned_path)
                normalized_files.append(abs_path)
            else:
                normalized_files.append(cleaned_path)

        # 创建文件列表标题
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(5, 10, 5, 5)
        title_layout.setSpacing(5)

        title_label = QLabel("📁 相关文件")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #FFA500;
                padding: 5px 0;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        layout.addWidget(title_container)

        # 找到所有文件的公共父目录
        common_prefix = self._find_common_prefix(normalized_files)

        # 创建文件树
        tree_widget = QTreeWidget()
        tree_widget.setHeaderHidden(True)
        tree_widget.setStyleSheet("""
            QTreeWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(76, 175, 80, 8),
                    stop:1 rgba(76, 175, 80, 12));
                border: 2px solid rgba(76, 175, 80, 35);
                border-radius: 8px;
                padding: 4px;
                font-size: 13px;
                outline: none;
                selection-background-color: transparent;
            }
            QTreeWidget::item {
                padding: 3px 6px;
                margin: 0px;
                border-radius: 4px;
                color: #2E7D32;
                min-height: 18px;
                selection-background-color: transparent;
            }
            QTreeWidget::item:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(76, 175, 80, 25),
                    stop:1 rgba(129, 199, 132, 25));
                border-left: 3px solid #4CAF50;
                padding-left: 3px;
            }
            QTreeWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(76, 175, 80, 60),
                    stop:1 rgba(129, 199, 132, 60));
                border-left: 3px solid #66BB6A;
                padding-left: 3px;
                color: #FFFFFF;
                font-weight: 600;
                selection-background-color: transparent;
            }
            QTreeWidget::item:selected:!active {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(76, 175, 80, 60),
                    stop:1 rgba(129, 199, 132, 60));
                color: #FFFFFF;
                border-left: 3px solid #66BB6A;
                padding-left: 3px;
            }
            QTreeWidget::item:selected:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(76, 175, 80, 70),
                    stop:1 rgba(129, 199, 132, 70));
                border-left: 3px solid #81C784;
                color: #FFFFFF;
            }
            QTreeWidget::branch {
                background: transparent;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                border-image: none;
                image: url(none);
                margin: 2px;
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                border-image: none;
                image: url(none);
                margin: 2px;
            }
        """)

        # 构建树形结构
        root_name = os.path.basename(common_prefix) if common_prefix else "Files"
        tree_root = {}  # 存储目录结构的字典树

        for file_path in normalized_files:
            # 获取相对路径
            if common_prefix:
                try:
                    rel_path = os.path.relpath(file_path, common_prefix)
                except ValueError:
                    # 如果无法获取相对路径（例如不同盘符），使用绝对路径
                    rel_path = file_path
            else:
                rel_path = file_path

            # 分割路径
            parts = rel_path.split(os.sep)

            # 构建树形结构
            current = tree_root
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]

        # 递归创建树节点
        def create_tree_items(parent_item, tree_dict, current_path):
            """递归创建树节点

            Args:
                parent_item: 父节点（QTreeWidget或QTreeWidgetItem）
                tree_dict: 当前层级的字典树
                current_path: 当前路径
            """
            for name in sorted(tree_dict.keys()):
                full_path = os.path.join(current_path, name) if current_path else name
                abs_path = os.path.join(common_prefix, full_path) if common_prefix else full_path

                # 创建节点
                item = QTreeWidgetItem(parent_item)
                item.setText(0, name)

                # 判断是文件还是目录
                if tree_dict[name]:  # 有子节点，是目录
                    item.setIcon(0, self._get_folder_icon())
                    # 设置目录样式 - 更加突出
                    font = item.font(0)
                    font.setBold(True)
                    font.setPointSize(13)
                    item.setFont(0, font)
                    # 设置目录颜色为深绿色
                    item.setForeground(0, QBrush(QColor(27, 94, 32)))  # 深绿色
                    # 递归创建子节点
                    create_tree_items(item, tree_dict[name], full_path)
                else:  # 没有子节点，是文件
                    item.setIcon(0, self._get_file_icon())
                    # 设置文件颜色为中等绿色
                    item.setForeground(0, QBrush(QColor(56, 142, 60)))  # 中绿色
                    # 保存文件路径到item数据中
                    item.setData(0, Qt.UserRole, abs_path)
                    # 设置工具提示
                    ide_name = get_configured_ide()
                    ide_display_names = {
                        'cursor': 'Cursor',
                        'kiro': 'Kiro',
                        'vscode': 'VSCode',
                        'code': 'VSCode'
                    }
                    display_ide = ide_display_names.get(ide_name.lower(), ide_name)
                    item.setToolTip(0, f"双击在{display_ide}中打开: {abs_path}")

        # 创建根节点并添加所有文件
        create_tree_items(tree_widget, tree_root, "")

        # 展开所有节点
        tree_widget.expandAll()

        # 连接双击事件
        def on_item_double_clicked(item, column):
            """处理节点双击事件"""
            file_path = item.data(0, Qt.UserRole)
            if not file_path:  # 如果是目录节点，切换展开/折叠
                if item.isExpanded():
                    item.setExpanded(False)
                else:
                    item.setExpanded(True)
                return

            # 打开文件
            try:
                # 导入ide_utils模块
                import sys
                parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                from ide_utils import open_project_with_ide

                # 获取IDE名称（使用配置）
                ide_name = get_configured_ide()

                # 使用通用的IDE打开函数
                success = open_project_with_ide(file_path, ide_name)

                if not success:
                    # 如果失败，使用系统默认编辑器打开
                    if platform.system() == "Darwin":
                        subprocess.run(["open", file_path], check=True)
                    elif platform.system() == "Windows":
                        os.startfile(file_path)
                    else:
                        subprocess.run(["xdg-open", file_path], check=True)

            except Exception as e:
                # 使用系统默认编辑器打开作为最终后备
                try:
                    if platform.system() == "Darwin":
                        subprocess.run(["open", file_path], check=True)
                    elif platform.system() == "Windows":
                        os.startfile(file_path)
                    else:
                        subprocess.run(["xdg-open", file_path], check=True)
                except Exception as e2:
                    file_name = os.path.basename(file_path)
                    QMessageBox.warning(self, "打开失败",
                        f"无法打开文件: {file_name}\n"
                        f"路径: {file_path}\n"
                        f"错误: {str(e2)}")

        tree_widget.itemDoubleClicked.connect(on_item_double_clicked)

        layout.addWidget(tree_widget)

    def _find_common_prefix(self, paths: list) -> str:
        """找到所有路径的公共父目录

        Args:
            paths: 文件路径列表

        Returns:
            str: 公共父目录路径
        """
        if not paths:
            return ""

        if len(paths) == 1:
            return os.path.dirname(paths[0])

        # 分割所有路径
        split_paths = [p.split(os.sep) for p in paths]

        # 找到最短路径的长度
        min_len = min(len(p) for p in split_paths)

        # 找到公共前缀
        common = []
        for i in range(min_len):
            parts = [p[i] for p in split_paths]
            if len(set(parts)) == 1:  # 所有路径在这一层都相同
                common.append(parts[0])
            else:
                break

        # 如果找到公共前缀，返回公共目录
        if common:
            return os.sep.join(common)

        # 如果没有公共前缀，返回空字符串
        return ""

    def _get_folder_icon(self) -> QIcon:
        """获取文件夹图标

        Returns:
            QIcon: 文件夹图标
        """
        # 使用系统提供的文件夹图标或自定义图标
        # 这里使用标准图标，也可以自定义
        from PySide6.QtWidgets import QStyle
        style = self.style()
        icon = style.standardIcon(QStyle.SP_DirIcon)
        return icon

    def _get_file_icon(self) -> QIcon:
        """获取文件图标

        Returns:
            QIcon: 文件图标
        """
        # 使用系统提供的文件图标或自定义图标
        from PySide6.QtWidgets import QStyle
        style = self.style()
        icon = style.standardIcon(QStyle.SP_FileIcon)
        return icon
