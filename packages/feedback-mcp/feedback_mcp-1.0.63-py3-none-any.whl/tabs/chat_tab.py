"""
聊天标签页 - 包含反馈输入、预定义选项、指令管理等功能
"""
import sys
import os
import json
from datetime import datetime
from typing import Optional, List, Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QGridLayout,
    QCheckBox, QPushButton, QProgressBar, QSizePolicy, QFileDialog, QMessageBox, QLabel
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint
from PySide6.QtGui import QFont, QTextCursor, QCursor

try:
    from .base_tab import BaseTab
except ImportError:
    from base_tab import BaseTab

try:
    from ..components.feedback_text_edit import FeedbackTextEdit
    from ..components.markdown_display import MarkdownDisplayWidget
except ImportError:
    try:
        from components.feedback_text_edit import FeedbackTextEdit
        from components.markdown_display import MarkdownDisplayWidget
    except ImportError:
        # 如果导入失败，使用原始组件
        from PySide6.QtWidgets import QTextEdit
        FeedbackTextEdit = QTextEdit
        MarkdownDisplayWidget = QTextEdit

# 导入指令管理组件
try:
    from ..components.command_tab import CommandTabWidget
except ImportError:
    try:
        from components.command_tab import CommandTabWidget
    except ImportError:
        CommandTabWidget = None



class ChatTab(BaseTab):
    """聊天标签页 - 处理用户反馈输入和交互"""
    
    # 信号定义
    feedback_submitted = Signal(list, list)  # 结构化内容数组, 图片列表
    command_executed = Signal(str)  # 指令内容
    option_executed = Signal(int)  # 选项索引
    text_changed = Signal()  # 文本变化
    
    def __init__(self, prompt: str, predefined_options: Optional[List[str]] = None,
                 project_path: Optional[str] = None, work_title: Optional[str] = None,
                 timeout: int = 60, files: Optional[List[str]] = None, bugdetail: Optional[str] = None,
                 session_id: Optional[str] = None, workspace_id: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.predefined_options = predefined_options or []
        self.project_path = project_path
        self.work_title = work_title or ""
        self.timeout = timeout
        self.elapsed_time = 0
        self.files = files or []  # 保存文件列表
        self.bugdetail = bugdetail  # 保存bug详情
        self.session_id = session_id  # 保存会话ID
        self.workspace_id = workspace_id  # 保存工作空间ID

        # 阶段信息
        self.stage_info = None
        self._load_stage_info()

        # 工作空间信息
        self.workspace_goal = None
        self.dialog_title = None
        self._load_workspace_context()

        # 任务信息
        self.current_task = None
        self.next_task = None
        self._load_task_info()

        # 深度思考模式状态 - 从设置中恢复
        self.deep_thinking_mode = self._load_deep_thinking_mode()

        # UI组件
        self.description_display = None
        self.option_checkboxes = []
        self.command_widget = None
        self.feedback_text = None
        self.submit_button = None
        self.progress_bar = None
        self.image_button = None  # 图片选择按钮
        self.deep_thinking_button = None  # 深度思考按钮

        # 指令标签相关属性
        self.selected_command = None  # 当前选中的指令信息
        self.command_label_widget = None  # 指令标签组件

        # Agent 标签相关属性
        self.agent_tags_container = None
        self.agent_tags_layout = None

        # 历史记录管理器
        self.history_manager = None
        self._init_history_manager()

        self.create_ui()

        # 初始化完成后更新深度思考按钮状态
        if hasattr(self, 'deep_thinking_button') and self.deep_thinking_button:
            self.deep_thinking_button.setChecked(self.deep_thinking_mode)

        # 保存AI发送的消息（prompt）到历史记录
        if prompt and prompt.strip():
            self.save_response_to_history(prompt)
    
    def _init_history_manager(self):
        """初始化历史记录管理器"""
        try:
            from components.chat_history import ChatHistoryManager
            self.history_manager = ChatHistoryManager(self.project_path, self.session_id)
        except ImportError:
            try:
                import sys
                parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                from components.chat_history import ChatHistoryManager
                self.history_manager = ChatHistoryManager(self.project_path, self.session_id)
            except Exception:
                self.history_manager = None

    def create_ui(self):
        """创建聊天标签页UI"""
        layout = QVBoxLayout(self)

        # Agent 标签容器（垂直布局，每个标签一行）
        self.agent_tags_container = QWidget()
        self.agent_tags_layout = QVBoxLayout(self.agent_tags_container)
        # 设置左右边距为 0，使标签宽度与下方 MarkdownDisplayWidget 对齐
        # MarkdownDisplayWidget 本身 padding 为 0，HTML body padding 为 5px
        # 标签按钮内部已有 padding: 6px 12px，所以外层左右边距设为 0
        self.agent_tags_layout.setContentsMargins(0, 5, 0, 5)
        self.agent_tags_layout.setSpacing(5)
        # 暂时注释掉 agent 标签加载
        # self._load_agent_tags()
        self.agent_tags_container.hide()  # 默认隐藏
        layout.addWidget(self.agent_tags_container)

        # 构建display_prompt
        display_prompt = self.prompt

        # 1. 如果有bugdetail，添加到前面
        if self.bugdetail:
            display_prompt = f"🐛 **当前正在修复bug:**\n{self.bugdetail}\n\n---\n\n{display_prompt}"

        # 2. 如果有上下文信息，添加到最前面
        context_info = self._format_context_info()
        if context_info:
            display_prompt = f"{context_info}{display_prompt}"

        # 使用支持Markdown的显示组件 - 简化布局，去掉外围框架
        self.description_display = MarkdownDisplayWidget()
        self.description_display.setMarkdownText(display_prompt)
        # 设置合适的高度，降低最小高度以便可选项少时获得更多空间
        self.description_display.setMinimumHeight(150)
        # 移除最大高度限制，让Markdown区域可以自动拉伸
        # self.description_display.setMaximumHeight(400)
        layout.addWidget(self.description_display, 1)  # 设置拉伸因子为1，占用剩余空间
        
        # 创建一个反馈布局容器（只包含其他元素，不包含markdown显示）
        feedback_container = QWidget()
        feedback_layout = QVBoxLayout(feedback_container)
        feedback_layout.setContentsMargins(5, 5, 5, 5)

        # 添加预定义选项
        if self.predefined_options:
            self._create_predefined_options(feedback_layout)

        # 添加阶段切换按钮（如果有）
        if self.stage_info:
            self._create_stage_buttons(feedback_layout)

        # 添加下一任务按钮（独立显示，不依赖stage_info）
        if self.next_task:
            self._create_next_task_button(feedback_layout)

        # 添加文件列表显示
        if self.files:
            self._create_files_list(feedback_layout)

        # 使用新的指令管理组件（隐藏固定显示区域）
        if CommandTabWidget:
            self.command_widget = CommandTabWidget(self.project_path, self)
            self.command_widget.command_executed.connect(self._handle_command_execution)
            # 隐藏固定显示的指令区域，用户通过 / // /// 弹窗使用指令
            self.command_widget.hide()

        # 自由文本反馈输入
        self._create_feedback_input(feedback_layout)
        
        # 提交按钮布局
        self._create_submit_section(feedback_layout)
        
        # 进度条布局
        if self.timeout > 0:
            self._create_progress_section(feedback_layout)

        # 添加反馈容器到主布局（不拉伸）
        layout.addWidget(feedback_container, 0)  # 设置拉伸因子为0，不额外拉伸

        # 恢复草稿内容
        self._restore_draft()

    def _format_context_info(self) -> str:
        """格式化上下文信息为Markdown文本

        Returns:
            str: 格式化的Markdown文本,如果所有信息都为空则返回空字符串

        Example:
            "📦 工作空间: XXX\n📍 阶段: XXX\n💬 对话: XXX\n\n---\n\n"
        """
        parts = []

        if self.workspace_goal:
            parts.append(f"📦 工作空间: {self.workspace_goal}")

        if self.stage_info and self.stage_info.get('current_stage'):
            stage_name = self.stage_info['current_stage'].get('title', '')
            parts.append(f"📍 阶段: {stage_name}")

        if self.dialog_title:
            parts.append(f"💬 对话: {self.dialog_title}")

        if self.current_task:
            task_title = self.current_task.get('title', '')
            parts.append(f"📌 当前任务: {task_title}")

        if not parts:
            return ""

        return "\n".join(parts) + "\n\n---\n\n"

    def _create_files_list(self, layout):
        """创建文件列表显示区域"""
        import subprocess
        import platform
        from functools import partial

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

        # 创建紧凑的文件列表容器（使用水平布局）
        files_container = QWidget()
        files_container.setMaximumHeight(40)  # 限制高度，更紧凑
        files_container_layout = QHBoxLayout(files_container)
        files_container_layout.setContentsMargins(5, 5, 5, 5)
        files_container_layout.setSpacing(10)

        # 添加文件图标标题
        title_label = QLabel("📝")
        title_label.setToolTip("AI创建或修改的文件")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #888;
                background-color: transparent;
            }
        """)
        files_container_layout.addWidget(title_label)

        # 为每个文件创建紧凑的可点击标签
        for file_path in self.files:
            file_name = os.path.basename(file_path)
            # 如果文件名太长，截断显示
            display_name = file_name if len(file_name) <= 20 else file_name[:17] + "..."

            file_btn = QPushButton(display_name)
            # 获取IDE名称（使用配置）
            ide_name = get_configured_ide()
            # IDE显示名称映射
            ide_display_names = {
                'cursor': 'Cursor',
                'kiro': 'Kiro',
                'vscode': 'VSCode',
                'code': 'VSCode'
            }
            display_ide = ide_display_names.get(ide_name.lower(), ide_name)
            file_btn.setToolTip(f"点击在{display_ide}中打开: {file_path}")
            file_btn.setCursor(Qt.PointingHandCursor)  # 设置手形光标
            file_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(76, 175, 80, 20);
                    color: #4CAF50;
                    border: 1px solid rgba(76, 175, 80, 40);
                    padding: 3px 8px;
                    border-radius: 3px;
                    font-size: 11px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: rgba(76, 175, 80, 40);
                    border: 1px solid #4CAF50;
                }
                QPushButton:pressed {
                    background-color: rgba(76, 175, 80, 60);
                }
            """)

            # 使用partial函数绑定参数，避免闭包问题
            def open_with_ide(file_path):
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
                        QMessageBox.warning(self, "打开失败",
                            f"无法打开文件: {file_name}\n"
                            f"路径: {file_path}\n"
                            f"错误: {str(e2)}")

            file_btn.clicked.connect(partial(open_with_ide, file_path))
            files_container_layout.addWidget(file_btn)

        # 添加弹簧使按钮靠左对齐
        files_container_layout.addStretch()

        layout.addWidget(files_container)
    
    def _create_predefined_options(self, layout):
        """创建预定义选项区域 - 与原始版本样式保持一致，高度自适应"""
        options_frame = QFrame()

        # 根据选项数量动态计算高度
        total_options = len(self.predefined_options)
        columns = 2  # 两列布局
        rows = (total_options + columns - 1) // columns  # 向上取整
        item_height = 26  # 每行约26px（包含按钮高度+间距）
        padding = 8  # 上下边距
        calculated_height = max(rows * item_height + padding, 50)  # 最小50px

        options_frame.setMinimumHeight(calculated_height)
        options_frame.setMaximumHeight(calculated_height)  # 设置最大高度=最小高度，实现固定自适应高度

        # 使用网格布局实现两列显示，与原版保持一致
        options_layout = QGridLayout(options_frame)
        options_layout.setContentsMargins(0, 2, 0, 2)
        options_layout.setSpacing(0)  # 设置间距
        
        for i, option in enumerate(self.predefined_options):
            # 计算当前项目在网格中的位置
            row = i // columns
            col = i % columns
            
            # Create horizontal layout for each option (checkbox + button)
            option_item_frame = QFrame()
            option_item_layout = QHBoxLayout(option_item_frame)
            option_item_layout.setContentsMargins(5, 0, 5, 0)
            
            # Checkbox
            checkbox = QCheckBox(option)
            self.option_checkboxes.append(checkbox)
            option_item_layout.addWidget(checkbox)
            
            # Add stretch to push button to the right
            option_item_layout.addStretch()
            
            # Execute button for this option - 使用与原始版本相同的样式
            execute_btn = QPushButton("立即执行")
            execute_btn.setMaximumWidth(80)
            execute_btn.setProperty('option_index', i)
            execute_btn.clicked.connect(lambda checked, idx=i: self._execute_option_immediately(idx))
            execute_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
                QPushButton:pressed {
                    background-color: #E65100;
                }
            """)
            option_item_layout.addWidget(execute_btn)
            
            # Add frame to grid layout
            options_layout.addWidget(option_item_frame, row, col)
        
        layout.addWidget(options_frame)
    
    def _create_feedback_input(self, layout):
        """创建反馈输入区域"""
        # 创建指令标签区域（默认隐藏）
        self._create_command_label_section(layout)
        
        self.feedback_text = FeedbackTextEdit()
        
        # 设置项目路径，启用指令弹窗功能
        if self.project_path:
            self.feedback_text.set_project_path(self.project_path)
        
        # 设置自定义指令选择处理器
        self.feedback_text.set_command_handler(self._on_command_selected_new)
        
        # 设置输入框的大小策略，让它能够随窗口拉伸自适应高度
        self.feedback_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        font_metrics = self.feedback_text.fontMetrics()
        row_height = font_metrics.height()
        # Calculate height for 5 lines + some padding for margins
        padding = self.feedback_text.contentsMargins().top() + self.feedback_text.contentsMargins().bottom() + 5
        self.feedback_text.setMinimumHeight(5 * row_height + padding)

        self.feedback_text.setPlaceholderText("请在此输入您的反馈内容 (Ctrl+Enter 或 Cmd+Enter，输入/打开项目指令; 输入//打开个人指令；输入///打开系统指令；输入指令对应的字母选中指令)")
        
        # 监听文本变化，动态改变发送按钮颜色
        self.feedback_text.textChanged.connect(self._on_text_changed)
        
        layout.addWidget(self.feedback_text)
    
    def _create_command_label_section(self, layout):
        """创建紧凑型Element UI Tag风格的指令标签区域"""
        self.command_label_widget = QFrame()
        # 默认样式，会在显示时根据类型动态设置
        self.command_label_widget.setStyleSheet("""
            QFrame {
                background: #409EFF;
                border: 1px solid #409EFF;
                border-radius: 4px;
                margin: 2px 0px;
                padding: 0px;
            }
        """)
        self.command_label_widget.hide()  # 默认隐藏
        
        label_layout = QHBoxLayout(self.command_label_widget)
        label_layout.setContentsMargins(6, 4, 6, 4)
        label_layout.setSpacing(6)
        
        # 关闭按钮 - 在容器内左侧
        close_button = QPushButton("×")
        close_button.setFixedSize(16, 16)
        close_button.setToolTip("清除选中的指令 (或按ESC键)")
        close_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(255, 255, 255, 0.8);
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                color: white;
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        close_button.clicked.connect(self._clear_selected_command)
        label_layout.addWidget(close_button)
        
        # 指令标题标签
        self.command_title_label = QLabel()
        self.command_title_label.setStyleSheet("""
            QLabel {
                color: white; 
                font-weight: 500;
                font-size: 12px;
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        label_layout.addWidget(self.command_title_label)
        
        # 编辑按钮 - 小图标
        edit_button = QPushButton("✏️")
        edit_button.setFixedSize(16, 16)
        edit_button.setToolTip("在IDE中打开指令文件")
        edit_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(255, 255, 255, 0.8);
                border: none;
                border-radius: 8px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                color: white;
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        edit_button.clicked.connect(self._edit_selected_command)
        label_layout.addWidget(edit_button)
        
        layout.addWidget(self.command_label_widget)
    
    def _on_command_selected_new(self, command_content: str, command_data: dict = None):
        """新的指令选择处理方法 - 显示标签而不是替换文本"""
        # 使用直接传递的指令数据，避免通过弹窗获取可能不准确的数据
        if command_data:
            self.selected_command = {
                'title': command_data.get('title', '未知指令'),
                'content': command_content,
                'type': command_data.get('type', 'unknown'),
                'full_path': command_data.get('full_path', '')  # 保存文件路径
            }
            self._show_command_label()

        # 关闭弹窗但不修改输入框内容
        self.feedback_text._close_command_popup()
    
    def _show_command_label(self):
        """显示紧凑型Element UI Tag风格的指令标签"""
        if not self.selected_command:
            return
            
        # Element UI Tag的类型配色
        type_config = {
            'project': {
                'bg_color': '#409EFF',
                'border_color': '#409EFF'
            },
            'personal': {
                'bg_color': '#67C23A',
                'border_color': '#67C23A'
            },
            'plugin': {
                'bg_color': '#409EFF',  # 与项目指令使用相同的蓝色
                'border_color': '#409EFF'
            },
            'system': {
                'bg_color': '#E6A23C',
                'border_color': '#E6A23C'
            }
        }
        
        config = type_config.get(self.selected_command['type'], {
            'bg_color': '#909399',
            'border_color': '#909399'
        })
        
        # 更新整个容器的Element UI Tag样式
        self.command_label_widget.setStyleSheet(f"""
            QFrame {{
                background: {config['bg_color']};
                border: 1px solid {config['border_color']};
                border-radius: 4px;
                margin: 2px 0px;
                padding: 0px;
            }}
        """)
        
        # 设置标题
        self.command_title_label.setText(self.selected_command['title'])
        
        # 显示标签
        self.command_label_widget.show()
    
    def _clear_selected_command(self):
        """清除选中的指令"""
        self.selected_command = None
        self.command_label_widget.hide()
    
    def _select_image(self):
        """选择图片文件"""
        try:
            file_dialog = QFileDialog(self)
            file_dialog.setFileMode(QFileDialog.ExistingFiles)  # 允许选择多个文件
            file_dialog.setNameFilter("图片文件 (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;所有文件 (*)")
            file_dialog.setWindowTitle("选择图片文件")
            
            if file_dialog.exec():
                selected_files = file_dialog.selectedFiles()
                
                for file_path in selected_files:
                    # 检查文件大小
                    try:
                        import os
                        file_size = os.path.getsize(file_path)
                        file_size_mb = file_size / (1024 * 1024)
                        
                        if file_size_mb > 50:  # 限制原始文件大小不超过50MB
                            QMessageBox.warning(
                                self, 
                                "文件过大", 
                                f"文件 {os.path.basename(file_path)} 大小为 {file_size_mb:.1f}MB，超过50MB限制。\n"
                                "请选择更小的图片文件。"
                            )
                            continue
                        
                        # 添加图片到编辑器
                        self.feedback_text.add_image_file(file_path)
                        
                    except Exception as e:
                        QMessageBox.warning(
                            self, 
                            "添加图片失败", 
                            f"无法添加图片 {file_path}: {str(e)}"
                        )
                        
        except Exception as e:
            QMessageBox.critical(
                self, 
                "选择图片失败", 
                f"选择图片时发生错误: {str(e)}"
            )
    
    def _create_submit_section(self, layout):
        """创建提交按钮区域"""
        submit_layout = QHBoxLayout()

        # 深度思考按钮 - 放在最左边（已隐藏）
        # self.deep_thinking_button = QPushButton("🧠")
        # self.deep_thinking_button.setToolTip("深度思考模式")
        # self.deep_thinking_button.setCheckable(True)  # 可切换状态
        # self.deep_thinking_button.setChecked(self.deep_thinking_mode)
        # self.deep_thinking_button.clicked.connect(self._toggle_deep_thinking)
        # self.deep_thinking_button.setMaximumWidth(30)
        # self.deep_thinking_button.setObjectName("deep_thinking_btn")
        # self.deep_thinking_button.setStyleSheet("""
        #     QPushButton#deep_thinking_btn {
        #         background-color: #404040;
        #         color: white;
        #         border: 1px solid #555;
        #         height: 30px;
        #         width: 30px;
        #         line-height: 30px;
        #         text-align: center;
        #         border-radius: 4px;
        #         font-size: 18px;
        #         font-weight: bold;
        #     }
        #     QPushButton#deep_thinking_btn:checked {
        #         background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        #             stop:0 #667eea, stop:1 #764ba2);
        #         border: 2px solid #667eea;
        #     }
        #     QPushButton#deep_thinking_btn:hover {
        #         background-color: #505050;
        #     }
        #     QPushButton#deep_thinking_btn:checked:hover {
        #         background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        #             stop:0 #7788ff, stop:1 #8755b2);
        #     }
        #     QPushButton#deep_thinking_btn:pressed {
        #         background-color: #303030;
        #     }
        # """)
        # submit_layout.addWidget(self.deep_thinking_button)
        #
        # # 添加一些间距
        # submit_layout.addSpacing(5)
        
        # 指令按钮 - 快速打开指令弹层
        self.command_button = QPushButton("⚡")
        self.command_button.setToolTip("打开指令列表 (相当于输入 / 触发)")
        self.command_button.clicked.connect(self._show_command_popup)
        self.command_button.setMaximumWidth(30)
        self.command_button.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                border: none;
                height:30px;
                width:30px;
                line-height:30px;
                text-align:center;
                border-radius: 4px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #777777;
            }
            QPushButton:pressed {
                background-color: #555555;
            }
        """)
        submit_layout.addWidget(self.command_button)
        
        # 添加一些间距
        submit_layout.addSpacing(5)
        
        # 图片选择按钮 - 只保留图标，与发送按钮并排
        self.image_button = QPushButton("📷")
        self.image_button.setToolTip("选择图片文件 (支持 PNG、JPG、JPEG、GIF、BMP、WebP)")
        self.image_button.clicked.connect(self._select_image)
        # 设置最小宽度，让高度自动匹配发送按钮
        self.image_button.setMaximumWidth(30)
        self.image_button.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                border: none;
                height:30px;
                width:30px;
                line-height:30px;
                text-align:center;
                border-radius: 4px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #777777;
            }
            QPushButton:pressed {
                background-color: #555555;
            }
        """)
        submit_layout.addWidget(self.image_button)
        
        # 添加一些间距
        submit_layout.addSpacing(5)

        # Submit button
        self.submit_button = QPushButton("发送反馈(Ctrl+Enter 或 Cmd+Enter 提交)")
        self.submit_button.clicked.connect(self._submit_feedback)
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                border: none;
                height:30px;
                line-height:30px;
                text-align:center;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #777777;
            }
            QPushButton:pressed {
                background-color: #555555;
            }
        """)
        submit_layout.addWidget(self.submit_button)
        
        layout.addLayout(submit_layout)
    
    def _create_progress_section(self, layout):
        """创建进度条区域"""
        progress_layout = QHBoxLayout()
        
        # Countdown progress bar section
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.timeout)
        self.progress_bar.setValue(self.elapsed_time)
        self.progress_bar.setFormat(self._format_time(self.elapsed_time))
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 2px;
                background-color: #2b2b2b;
                height: 2px;
                color: white;
                font-size: 11px;
                text-align: right;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                                  stop: 0 #4CAF50, stop: 0.5 #45a049, stop: 1 #4CAF50);
                border-radius: 2px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_layout)
    
    def _handle_command_execution(self, command_content: str):
        """处理指令执行"""
        if command_content:
            self.command_executed.emit(command_content)
    
    def _execute_option_immediately(self, option_index: int):
        """立即执行选项"""
        self.option_executed.emit(option_index)
    
    def _show_command_popup(self):
        """显示指令弹窗"""
        try:
            # 确保输入框有焦点
            if self.feedback_text:
                self.feedback_text.setFocus()
                
                # 触发指令弹窗（默认显示项目指令）
                if hasattr(self.feedback_text, '_show_command_popup'):
                    self.feedback_text._show_command_popup("", "project")
                else:
                    QMessageBox.information(self, "提示", "指令功能暂不可用")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"显示指令弹窗失败: {str(e)}")

    def _on_text_changed(self):
        """文本变化处理"""
        if self.feedback_text and self.submit_button:
            # 根据文本内容动态改变按钮颜色 - 与原版保持一致
            has_text = bool(self.feedback_text.toPlainText().strip())
            if has_text:
                # 有内容时，按钮变为蓝色（与原版一致）
                self.submit_button.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        border: none;
                        height:30px;
                        line-height:30px;
                        text-align:center;
                        border-radius: 4px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #1976D2;
                    }
                    QPushButton:pressed {
                        background-color: #0D47A1;
                    }
                """)
            else:
                # 无内容时，按钮为灰色（与原版一致）
                self.submit_button.setStyleSheet("""
                    QPushButton {
                        background-color: #666666;
                        color: white;
                        border: none;
                        height:30px;
                        line-height:30px;
                        text-align:center;
                        border-radius: 4px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #777777;
                    }
                    QPushButton:pressed {
                        background-color: #555555;
                    }
                """)

        self.text_changed.emit()

    def _get_text_with_image_placeholders(self):
        """获取包含图片占位符的文本

        遍历文档内容，在图片位置插入占位符 [图片1]、[图片2] 等
        """
        if not self.feedback_text:
            return ""

        document = self.feedback_text.document()
        cursor = QTextCursor(document)
        cursor.movePosition(QTextCursor.Start)

        result_text = ""
        image_index = 1
        block = document.begin()

        # 遍历所有文本块
        while block.isValid():
            # 获取当前块的迭代器
            it = block.begin()

            # 遍历块中的所有片段
            while not it.atEnd():
                fragment = it.fragment()
                if fragment.isValid():
                    char_format = fragment.charFormat()

                    # 检查是否是图片格式
                    if char_format.isImageFormat():
                        # 插入图片占位符
                        result_text += f"[图片{image_index}]"
                        image_index += 1
                    else:
                        # 添加普通文本
                        result_text += fragment.text()

                it += 1

            # 添加块之间的换行符（除了最后一个块）
            block = block.next()
            if block.isValid():
                result_text += "\n"

        return result_text.strip()

    def _submit_feedback(self):
        """提交反馈"""
        if not self.feedback_text:
            return

        # 获取包含图片占位符的文本内容
        text_content = self._get_text_with_image_placeholders()

        # 在图片占位符文本基础上，解析大文本占位符
        if hasattr(self.feedback_text, 'resolve_large_text_placeholders'):
            text_content = self.feedback_text.resolve_large_text_placeholders(text_content)

        images = self.feedback_text.get_pasted_images() if hasattr(self.feedback_text, 'get_pasted_images') else []

        # 获取选中的预定义选项
        selected_options = []
        for i, checkbox in enumerate(self.option_checkboxes):
            if checkbox.isChecked():
                selected_options.append(self.predefined_options[i])

        # 检查是否有内容可发送：文本、图片或选中的选项
        if not text_content.strip() and not images and not selected_options:
            return  # 没有内容，不发送

        # 检查已选中的指令（优先使用新的指令标签机制）
        selected_command_content = ""
        if self.selected_command:
            # 使用新的指令标签机制
            selected_command_content = self.selected_command['content']
        elif hasattr(self, 'command_widget') and self.command_widget:
            # 兼容原有的指令选择方式
            for i in range(self.command_widget.count()):
                tab = self.command_widget.widget(i)
                # 检查是否有command_button_group（所有指令选项卡都有）
                if hasattr(tab, 'command_button_group'):
                    checked_button = tab.command_button_group.checkedButton()
                    if checked_button:
                        command_index = checked_button.property('command_index')
                        # 检查是否有commands数组（所有指令选项卡都有）
                        if (command_index is not None and
                            hasattr(tab, 'commands') and
                            0 <= command_index < len(tab.commands)):
                            selected_command_content = tab.commands[command_index]['content']
                            break  # 找到就停止查找

        # 构建结构化内容数组
        content_parts = []

        # 如果开启深度思考模式，在最前面添加提示
        if self.deep_thinking_mode:
            content_parts.append({
                "type": "text",
                "text": "**ultrathink**"
            })

        # 添加选中的预定义选项
        if selected_options:
            content_parts.append({
                "type": "options",
                "text": "; ".join(selected_options)
            })

        # 添加选中的指令内容
        if selected_command_content:
            content_parts.append({
                "type": "command",
                "text": selected_command_content
            })

        # 处理大文本：如果超过10k字符，保存为文件
        if text_content and len(text_content) > 10000:
            try:
                import tempfile
                from datetime import datetime

                # 使用与图片相同的目录
                if self.project_path:
                    tmp_dir = os.path.join(self.project_path, ".workspace", "chat_history", "tmp")
                    os.makedirs(tmp_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    txt_path = os.path.join(tmp_dir, f"{timestamp}_text.txt")
                else:
                    txt_path = tempfile.mktemp(suffix=".txt")

                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)

                # 使用文件路径替代原始文本
                content_parts.append({
                    "type": "text",
                    "text": f"[大文本已保存到文件: {txt_path}]"
                })
            except Exception:
                # 如果保存失败，仍然使用原始文本
                content_parts.append({
                    "type": "text",
                    "text": text_content
                })
        elif text_content:
            content_parts.append({
                "type": "text",
                "text": text_content
            })

        # 始终发送信号，即使content_parts为空（允许发送空反馈）
        self.feedback_submitted.emit(content_parts, images)

        # 提交后在后台清空草稿
        if self.history_manager:
            import threading
            threading.Thread(target=self.history_manager.clear_draft, daemon=True).start()

        # 提交后清空输入框和选项，避免超时/关闭时重复保存
        self.clear_feedback()
    
    def _format_time(self, seconds: int) -> str:
        """格式化时间显示"""
        if seconds < 60:
            return f"AI已等待: {seconds}秒"
        else:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"AI已等待: {minutes}分{remaining_seconds}秒"
    
    def update_progress(self, elapsed_time: int):
        """更新进度条"""
        self.elapsed_time = elapsed_time
        if self.progress_bar:
            self.progress_bar.setValue(elapsed_time)
            self.progress_bar.setFormat(self._format_time(elapsed_time))
    
    def get_feedback_text(self) -> str:
        """获取反馈文本"""
        if self.feedback_text:
            return self.feedback_text.toPlainText().strip()
        return ""
    
    def get_selected_options(self) -> List[str]:
        """获取选中的预定义选项"""
        selected = []
        for i, checkbox in enumerate(self.option_checkboxes):
            if checkbox.isChecked():
                selected.append(self.predefined_options[i])
        return selected
    
    def _toggle_deep_thinking(self):
        """切换深度思考模式"""
        self.deep_thinking_mode = self.deep_thinking_button.isChecked()
        
        # 保存状态到设置
        self._save_deep_thinking_mode(self.deep_thinking_mode)
        
        # 更新工具提示
        if self.deep_thinking_button:
            if self.deep_thinking_mode:
                self.deep_thinking_button.setToolTip("深度思考模式已开启 (点击关闭)")
            else:
                self.deep_thinking_button.setToolTip("深度思考模式 (点击开启)")
    
    def _load_stage_info(self):
        """加载工作空间阶段信息"""
        # 如果没有session_id和workspace_id，直接返回
        if not self.session_id and not self.workspace_id:
            return

        try:
            # 导入工作空间管理器
            import sys
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from workspace_manager import WorkspaceManager

            # 创建管理器实例
            manager = WorkspaceManager(self.project_path)

            # 优先使用workspace_id，如果没有则使用session_id
            self.stage_info = manager.get_stage_info(
                session_id=self.session_id,
                workspace_id=self.workspace_id
            )
        except Exception as e:
            # 静默处理加载失败，不影响主流程
            self.stage_info = None

    def _load_workspace_context(self):
        """加载工作空间上下文信息（goal和对话标题）"""
        if not self.session_id:
            return

        try:
            # 导入工作空间管理器函数
            import sys
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from workspace_manager import get_workspace_goal_for_session, get_session_title_for_session

            # 获取工作空间goal
            self.workspace_goal = get_workspace_goal_for_session(self.session_id, self.project_path)

            # 获取对话标题（优先从workspace.yml的sessions获取，如果没有再使用work_title）
            session_title = get_session_title_for_session(self.session_id, self.project_path)
            if session_title:
                self.dialog_title = session_title
            else:
                self.dialog_title = self.work_title

        except Exception as e:
            # 静默处理加载失败，不影响主流程
            pass
            self.workspace_goal = None
            self.dialog_title = self.work_title

    def _create_stage_buttons(self, layout):
        """创建阶段切换按钮"""
        if not self.stage_info:
            return

        # 创建按钮容器
        stage_buttons_container = QWidget()
        stage_buttons_layout = QHBoxLayout(stage_buttons_container)
        stage_buttons_layout.setContentsMargins(5, 5, 5, 5)
        stage_buttons_layout.setSpacing(10)

        # 创建上一阶段按钮
        if self.stage_info.get('prev_stage'):
            prev_stage = self.stage_info['prev_stage']
            # 截断过长的标题
            title = prev_stage.get('title', '')
            if len(title) > 10:
                title = title[:10] + "..."
            prev_btn = QPushButton(f"上一阶段: {title}")
            prev_btn.setToolTip(prev_stage.get('description', ''))
            prev_btn.setCursor(Qt.PointingHandCursor)
            prev_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 水平扩展
            prev_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(200, 200, 200, 25);
                    color: #AAA;
                    border: 1px solid rgba(200, 200, 200, 45);
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 13px;
                    text-align: center;
                    min-width: 0px;
                }
                QPushButton:hover {
                    background-color: rgba(200, 200, 200, 40);
                    border: 1px solid #BBB;
                    color: #888;
                }
                QPushButton:pressed {
                    background-color: rgba(200, 200, 200, 55);
                }
            """)
            prev_btn.clicked.connect(lambda: self._on_stage_button_clicked("请进入上一阶段"))
            stage_buttons_layout.addWidget(prev_btn, 1)  # 权重1，占50%
        else:
            # 如果没有上一阶段，添加一个占位空间
            stage_buttons_layout.addStretch(1)

        # 创建下一阶段按钮
        if self.stage_info.get('next_stage'):
            next_stage = self.stage_info['next_stage']
            # 截断过长的标题
            title = next_stage.get('title', '')
            if len(title) > 10:
                title = title[:10] + "..."
            next_btn = QPushButton(f"下一阶段: {title}")
            next_btn.setToolTip(next_stage.get('description', ''))
            next_btn.setCursor(Qt.PointingHandCursor)
            next_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 水平扩展
            next_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(76, 175, 80, 30);
                    color: #4CAF50;
                    border: 1px solid rgba(76, 175, 80, 50);
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 13px;
                    text-align: center;
                    min-width: 0px;
                }
                QPushButton:hover {
                    background-color: rgba(76, 175, 80, 50);
                    border: 1px solid #4CAF50;
                }
                QPushButton:pressed {
                    background-color: rgba(76, 175, 80, 70);
                }
            """)
            next_btn.clicked.connect(lambda: self._on_stage_button_clicked("请进入下一阶段"))
            stage_buttons_layout.addWidget(next_btn, 1)  # 权重1，占50%
        else:
            # 如果没有下一阶段，添加一个占位空间
            stage_buttons_layout.addStretch(1)

        layout.addWidget(stage_buttons_container)

    def _create_next_task_button(self, layout):
        """创建下一任务按钮（独立方法）"""
        if not self.next_task:
            return

        next_task_title = self.next_task.get('title', '')
        # 如果标题过长，截断
        if len(next_task_title) > 20:
            next_task_title = next_task_title[:20] + "..."

        next_task_btn = QPushButton(f"下一任务: {next_task_title}")
        next_task_btn.setCursor(Qt.PointingHandCursor)
        next_task_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        next_task_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 175, 80, 30);
                color: #4CAF50;
                border: 1px solid rgba(76, 175, 80, 50);
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 13px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(76, 175, 80, 50);
                border: 1px solid #4CAF50;
            }
            QPushButton:pressed {
                background-color: rgba(76, 175, 80, 70);
            }
        """)
        next_task_btn.clicked.connect(self._on_next_task_clicked)
        layout.addWidget(next_task_btn)

    def _on_stage_button_clicked(self, message):
        """处理阶段切换按钮点击"""
        # 作为文本内容提交
        content_parts = [{
            "type": "text",
            "text": message
        }]
        self.feedback_submitted.emit(content_parts, [])
        # 关闭窗口（如果有父窗口）
        if self.parent() and hasattr(self.parent(), 'close'):
            self.parent().close()

    def _load_deep_thinking_mode(self) -> bool:
        """从设置中加载深度思考模式状态"""
        from PySide6.QtCore import QSettings
        
        # 优先尝试加载项目级设置
        if self.project_path:
            project_settings_file = os.path.join(self.project_path, '.feedback_settings.json')
            if os.path.exists(project_settings_file):
                try:
                    with open(project_settings_file, 'r') as f:
                        settings = json.load(f)
                        return settings.get('deep_thinking_mode', False)
                except Exception:
                    pass  # 如果读取失败，使用全局设置
        
        # 使用全局QSettings
        settings = QSettings("FeedbackUI", "ChatTab")
        return settings.value("deep_thinking_mode", False, type=bool)
    
    def _save_deep_thinking_mode(self, enabled: bool):
        """保存深度思考模式状态到设置"""
        from PySide6.QtCore import QSettings
        
        # 保存到项目级设置（如果有项目路径）
        if self.project_path:
            project_settings_file = os.path.join(self.project_path, '.feedback_settings.json')
            settings = {}
            
            # 读取现有设置
            if os.path.exists(project_settings_file):
                try:
                    with open(project_settings_file, 'r') as f:
                        settings = json.load(f)
                except Exception:
                    settings = {}
            
            # 更新深度思考模式设置
            settings['deep_thinking_mode'] = enabled
            
            # 保存回文件
            try:
                with open(project_settings_file, 'w') as f:
                    json.dump(settings, f, indent=2)
            except Exception:
                pass  # 如果保存失败，至少保存到全局设置
        
        # 同时保存到全局QSettings
        settings = QSettings("FeedbackUI", "ChatTab")
        settings.setValue("deep_thinking_mode", enabled)
    
    def get_history_file_path(self) -> Optional[str]:
        """获取历史记录文件路径"""
        # 如果没有session_id,返回None
        if not self.session_id:
            return None

        if self.project_path:
            return os.path.join(self.project_path, '.workspace', 'chat_history', f'{self.session_id}.json')
        else:
            # 如果没有项目路径，使用脚本目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(script_dir, '..', '.workspace', 'chat_history', f'{self.session_id}.json')
    
    def save_response_to_history(self, response: str) -> bool:
        """保存AI回复到当前对话历史（新格式）

        Args:
            response: AI的回复内容

        Returns:
            bool: 保存是否成功
        """
        if not response.strip():
            return False

        try:
            print(f"[DEBUG save_response_to_history] project_path={self.project_path}", file=sys.stderr)
            print(f"[DEBUG save_response_to_history] session_id={self.session_id}", file=sys.stderr)

            # 写入调试日志文件
            debug_log_path = "/Users/yang/workspace/interactive-feedback-mcp/.workspace/debug_save_response.log"
            with open(debug_log_path, 'a', encoding='utf-8') as debug_f:
                debug_f.write(f"\n=== {datetime.now().isoformat()} ===\n")
                debug_f.write(f"project_path={self.project_path}\n")
                debug_f.write(f"session_id={self.session_id}\n")

            # 获取历史记录文件路径
            history_file = self.get_history_file_path()
            print(f"[DEBUG save_response_to_history] history_file={history_file}", file=sys.stderr)

            # 追加写入历史文件路径
            with open(debug_log_path, 'a', encoding='utf-8') as debug_f:
                debug_f.write(f"history_file={history_file}\n")

            # 如果没有session_id,静默跳过
            if not history_file:
                return False

            # 读取现有数据
            existing_data = {}
            if os.path.exists(history_file):
                try:
                    with open(history_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        print(f"[DEBUG] existing_data type: {type(existing_data)}", file=sys.stderr)
                        if isinstance(existing_data, dict):
                            print(f"[DEBUG] dialogues count: {len(existing_data.get('dialogues', []))}", file=sys.stderr)
                            agents = [d for d in existing_data.get('dialogues', []) if d.get('role') == 'agent']
                            print(f"[DEBUG] agent records: {len(agents)}", file=sys.stderr)

                        # 写入调试日志
                        with open(debug_log_path, 'a', encoding='utf-8') as debug_f:
                            debug_f.write(f"existing_data type: {type(existing_data)}\n")
                            if isinstance(existing_data, dict):
                                debug_f.write(f"dialogues count: {len(existing_data.get('dialogues', []))}\n")
                                agents = [d for d in existing_data.get('dialogues', []) if d.get('role') == 'agent']
                                debug_f.write(f"agent records loaded: {len(agents)}\n")
                        # 兼容旧格式：如果是数组，转换为新格式
                        if isinstance(existing_data, list):
                            dialogues = []
                            for record in existing_data:
                                if isinstance(record, dict):
                                    # 跳过 stop_hook_status 类型
                                    if record.get('type') == 'stop_hook_status':
                                        continue

                                    # 保留 agent 记录（直接添加）
                                    if record.get('role') == 'agent':
                                        dialogues.append(record)
                                        continue

                                    # 转换普通消息为对话格式
                                    dialogue = {
                                        'timestamp': record.get('timestamp', ''),
                                        'time_display': record.get('time_display', ''),
                                        'messages': record.get('messages', []) if 'messages' in record else [{
                                            'role': 'user',
                                            'content': record.get('content', ''),
                                            'time': record.get('time_display', '').split(' ')[-1] if 'time_display' in record else ''
                                        }]
                                    }
                                    dialogues.append(dialogue)
                            existing_data = {'dialogues': dialogues}
                except (json.JSONDecodeError, IOError):
                    existing_data = {}

            # 确保有dialogues数组
            if 'dialogues' not in existing_data:
                existing_data['dialogues'] = []

            dialogues = existing_data['dialogues']

            # 查找最后一个有messages字段的对话记录（跳过agent记录）
            last_dialogue_index = -1
            for i in range(len(dialogues) - 1, -1, -1):
                if 'messages' in dialogues[i]:
                    last_dialogue_index = i
                    break

            if last_dialogue_index >= 0:
                # 在最后一个对话记录中添加AI回复
                dialogues[last_dialogue_index]['messages'].append({
                    'role': 'assistant',
                    'content': response.strip(),
                    'time': datetime.now().strftime('%H:%M:%S')
                })
            else:
                # 没有找到对话记录，创建新的对话记录（仅包含AI回复）
                new_record = {
                    'timestamp': datetime.now().isoformat(),
                    'time_display': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'messages': [{
                        'role': 'assistant',
                        'content': response.strip(),
                        'time': datetime.now().strftime('%H:%M:%S')
                    }]
                }
                dialogues.append(new_record)

            # 保存到文件
            agents_after = [d for d in existing_data.get('dialogues', []) if d.get('role') == 'agent']
            print(f"[DEBUG] agent records before save: {len(agents_after)}", file=sys.stderr)

            # 写入调试日志
            with open(debug_log_path, 'a', encoding='utf-8') as debug_f:
                agents_after = [d for d in existing_data.get('dialogues', []) if d.get('role') == 'agent']
                debug_f.write(f"agent records before save: {len(agents_after)}\n")

            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)

            return True

        except Exception:
            # 静默处理保存失败，不影响主流程
            return False
    
    def load_history_from_file(self) -> List[Dict]:
        """从文件加载历史记录（兼容旧格式）"""
        try:
            history_file = self.get_history_file_path()

            # 如果没有session_id,静默跳过
            if not history_file:
                return []

            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # 新格式：{'dialogues': [...], 'control': {...}}
                    if isinstance(data, dict) and 'dialogues' in data:
                        # 直接返回dialogues数组（不含type字段）
                        return data.get('dialogues', [])

                    # 旧格式数组处理
                    if isinstance(data, list):
                        # 兼容旧格式：将旧格式转换为新的对话格式
                        converted_history = []
                        for record in data:
                            if isinstance(record, dict):
                                # 跳过control类型的记录
                                if record.get('type') == 'stop_hook_status':
                                    continue

                                # 保留 agent 记录（直接添加）
                                if record.get('role') == 'agent':
                                    converted_history.append(record)
                                    continue

                                # 转换普通消息为对话格式
                                if 'type' not in record or record.get('type') != 'dialogue':
                                    # 旧格式单条消息 - 转换为对话格式（不含type）
                                    converted_record = {
                                        'timestamp': record.get('timestamp', ''),
                                        'time_display': record.get('time_display', ''),
                                        'messages': [{
                                            'role': 'user',
                                            'content': record.get('content', ''),
                                            'time': record.get('time_display', '').split(' ')[-1] if 'time_display' in record else ''
                                        }]
                                    }
                                    converted_history.append(converted_record)
                                else:
                                    # 已经是对话格式 - 移除type字段
                                    dialogue = {
                                        'timestamp': record.get('timestamp', ''),
                                        'time_display': record.get('time_display', ''),
                                        'messages': record.get('messages', [])
                                    }
                                    converted_history.append(dialogue)
                        return converted_history

                    return []
            return []
        except Exception:
            # 静默处理加载失败，不影响主流程
            return []
    
    def get_recent_history(self, count: Optional[int] = None) -> List[Dict]:
        """获取最近的历史记录

        Args:
            count: 获取记录数量，如果为None则返回所有记录

        Returns:
            List[Dict]: 历史记录列表
        """
        history = self.load_history_from_file()
        if count is None:
            return history  # 返回所有历史记录
        return history[-count:]
    
    def save_input_to_history(self):
        """保存输入框内容到草稿（用于超时或关闭时自动保存）"""
        if not self.feedback_text or not self.history_manager:
            return

        text_content = self.feedback_text.toPlainText().strip()
        if text_content:
            self.history_manager.save_draft(text_content)
    
    def clear_feedback(self):
        """清空反馈内容"""
        if self.feedback_text:
            self.feedback_text.clear()
            if hasattr(self.feedback_text, 'clear_images'):
                self.feedback_text.clear_images()
        
        # 清空选项
        for checkbox in self.option_checkboxes:
            checkbox.setChecked(False)
        
        # 清空选中的指令
        self._clear_selected_command()

    def _get_configured_ide_or_prompt(self):
        """获取配置的IDE,如果未配置则弹出设置对话框,返回IDE名称或None"""
        try:
            from feedback_config import FeedbackConfig

            # 获取项目路径
            project_path = self.project_path if hasattr(self, 'project_path') else None
            if not project_path and hasattr(self, 'parent'):
                main_window = self.parent()
                while main_window and not hasattr(main_window, 'project_path'):
                    main_window = main_window.parent()
                if main_window:
                    project_path = main_window.project_path

            if not project_path:
                return None

            config_manager = FeedbackConfig(project_path)
            ide = config_manager.get_ide() or os.getenv('IDE')

            if not ide:
                # 弹出设置IDE对话框
                reply = QMessageBox.question(
                    self,
                    "未配置IDE",
                    "尚未配置默认IDE，是否现在设置？",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    # 获取主窗口并调用设置对话框
                    main_window = self.parent()
                    while main_window and not hasattr(main_window, '_show_ide_settings_dialog'):
                        main_window = main_window.parent()
                    if main_window:
                        main_window._show_ide_settings_dialog()
                        # 重新获取配置
                        ide = config_manager.get_ide()

            return ide
        except Exception as e:
            print(f"获取IDE配置失败: {e}")
            return None

    def _edit_selected_command(self):
        """在IDE中打开选中的指令文件"""
        if not self.selected_command:
            return

        # 优先使用保存的文件路径
        file_path = self.selected_command.get('full_path', '')

        # 如果没有保存路径，则尝试查找
        if not file_path:
            command_data = {
                'title': self.selected_command['title'],
                'content': self.selected_command['content'],
                'type': self.selected_command['type'],
            }
            file_path = self._find_command_file_path(command_data)

        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "打开失败", f"无法找到指令文件\n标题: {self.selected_command.get('title')}\n路径: {file_path or '未找到'}")
            return

        # 使用IDE打开文件
        try:
            # 导入ide_utils模块
            import sys
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from ide_utils import open_project_with_ide

            # 使用统一的IDE获取方法
            ide_name = self._get_configured_ide_or_prompt()

            if not ide_name:
                # 用户取消了设置IDE或无法获取配置
                return

            # 使用IDE打开文件
            success = open_project_with_ide(file_path, ide_name)

            if not success:
                # 如果IDE打开失败，提示用户重新配置IDE
                reply = QMessageBox.question(
                    self,
                    "IDE打开失败",
                    f"无法使用 '{ide_name}' 打开文件。\n\n可能的原因：\n1. IDE未正确安装\n2. IDE路径配置错误\n3. IDE不支持打开此类型文件\n\n是否重新设置IDE？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )

                if reply == QMessageBox.Yes:
                    # 获取主窗口并调用设置对话框
                    main_window = self.parent()
                    while main_window and not hasattr(main_window, '_show_ide_settings_dialog'):
                        main_window = main_window.parent()
                    if main_window:
                        main_window._show_ide_settings_dialog()

        except Exception as e:
            QMessageBox.critical(self, "打开失败", f"无法打开指令文件: {str(e)}")
    
    def _find_command_file_path(self, command_data):
        """查找指令文件路径"""
        import os

        # 获取项目路径
        project_path = self.project_path if hasattr(self, 'project_path') else None
        if not project_path:
            # 从父窗口获取
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'project_path'):
                main_window = main_window.parent()
            if main_window:
                project_path = main_window.project_path

        if not project_path:
            return None

        title = command_data['title']
        if title.endswith('.md'):
            title = title[:-3]

        # 根据指令类型确定搜索目录
        if command_data['type'] == 'project':
            search_dirs = [
                os.path.join(project_path, ".claude", "commands"),
                os.path.join(project_path, "_agent-local", "prompts"),
                os.path.join(project_path, ".cursor", "rules")
            ]
        elif command_data['type'] == 'personal':
            search_dirs = [
                os.path.join(project_path, "prompts"),
                os.path.expanduser("~/.claude/commands")
            ]
        else:  # system
            search_dirs = [
                os.path.join(project_path, ".claude", "commands"),
                os.path.join(project_path, "src-min")
            ]

        # 在各个目录中搜索文件
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue

            # 尝试不同的文件扩展名
            for ext in ['.md', '.mdc', '.txt']:
                file_path = os.path.join(search_dir, f"{title}{ext}")
                if os.path.exists(file_path):
                    return file_path

            # 递归搜索子目录
            try:
                for root, dirs, files in os.walk(search_dir):
                    for file in files:
                        if file.startswith(title) and file.endswith(('.md', '.mdc', '.txt')):
                            return os.path.join(root, file)
            except Exception:
                pass

        return None

    def _load_task_info(self):
        """加载任务信息"""
        if not self.session_id:
            return

        try:
            if not self.project_path:
                return

            # 构建任务文件路径
            task_file = os.path.join(self.project_path, '.workspace', 'tasks', f'{self.session_id}.json')
            if not os.path.exists(task_file):
                return

            # 读取任务文件
            with open(task_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                tasks = data.get('tasks', [])

            # 查找当前任务（state == "in_progress"）
            for task in tasks:
                if task.get('state') == 'in_progress':
                    self.current_task = {
                        'id': task.get('id'),
                        'title': task.get('title', ''),
                        'state': task.get('state')
                    }
                    break

            # 查找下一个任务（state == "pending"）
            for task in tasks:
                if task.get('state') == 'pending':
                    self.next_task = {
                        'id': task.get('id'),
                        'title': task.get('title', ''),
                        'state': task.get('state')
                    }
                    break

        except Exception:
            # 静默处理加载失败，不影响主流程
            pass

    def _create_current_task_label(self, layout):
        """创建当前任务显示标签"""
        if not self.current_task:
            return

        task_title = self.current_task.get('title', '')
        task_label = QLabel(f"📌 当前任务: {task_title}")
        task_label.setWordWrap(True)
        task_label.setAlignment(Qt.AlignCenter)
        task_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #FF8C00;
                padding: 6px;
                background-color: rgba(255, 140, 0, 10);
                border: 1px solid rgba(255, 140, 0, 30);
                border-radius: 4px;
                margin: 5px 0px;
            }
        """)
        layout.addWidget(task_label)

    def _on_next_task_clicked(self):
        """处理下一任务按钮点击"""
        content_parts = [{
            "type": "text",
            "text": "请开始任务列表中的下一个任务"
        }]
        self.feedback_submitted.emit(content_parts, [])
        # 关闭窗口（如果有父窗口）
        if self.parent() and hasattr(self.parent(), 'close'):
            self.parent().close()

    def _load_agent_tags(self):
        """加载并显示 agent 标签（垂直排列，每个标签一行）"""
        # 清空现有标签
        while self.agent_tags_layout.count():
            child = self.agent_tags_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 获取 agent 记录
        if not self.history_manager:
            self.agent_tags_container.hide()
            return

        agent_records = self.history_manager.get_agent_records_after_last_user()

        if not agent_records:
            self.agent_tags_container.hide()
            return

        # 为每个 agent 创建标签
        for record in agent_records:
            tag = self._create_agent_tag(record)
            self.agent_tags_layout.addWidget(tag)

        self.agent_tags_container.show()

    def _create_agent_tag(self, record: Dict) -> QPushButton:
        """创建 agent 标签按钮（100%宽度，不截断文本）"""
        subagent_type = record.get('subagent_type', 'unknown')
        description = record.get('description', '')
        label = f"{subagent_type}:{description}" if description else subagent_type

        # 完整显示标签，不截断
        tag = QPushButton(label)
        tag.setToolTip(f"点击查看详情: {label}")
        tag.setCursor(Qt.PointingHandCursor)
        # 设置宽度自动扩展到100%
        tag.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        tag.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 175, 80, 20);
                color: #4CAF50;
                border: 1px solid rgba(76, 175, 80, 40);
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
                text-align: left;
            }
            QPushButton:hover {
                background-color: rgba(76, 175, 80, 40);
                border: 1px solid #4CAF50;
            }
            QPushButton:pressed {
                background-color: rgba(76, 175, 80, 60);
            }
        """)
        tag.clicked.connect(lambda checked, r=record: self._show_agent_popup(r))
        return tag

    def _show_agent_popup(self, record: Dict):
        """显示 agent 内容弹窗"""
        try:
            from components.agent_popup import AgentPopup
        except ImportError:
            try:
                import sys
                parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                from components.agent_popup import AgentPopup
            except Exception:
                return

        popup = AgentPopup(self)
        popup.set_agent_data(record)

        # 计算弹窗位置
        tag_pos = self.agent_tags_container.mapToGlobal(
            self.agent_tags_container.rect().bottomLeft()
        )
        popup.show_at_position(QPoint(tag_pos.x(), tag_pos.y() + 5))

    def _restore_draft(self):
        """恢复草稿内容到输入框"""
        if not self.history_manager or not self.feedback_text:
            return

        draft = self.history_manager.get_latest_draft()
        if draft and draft.get('text'):
            self.feedback_text.setPlainText(draft['text'])
            self.history_manager.clear_draft()