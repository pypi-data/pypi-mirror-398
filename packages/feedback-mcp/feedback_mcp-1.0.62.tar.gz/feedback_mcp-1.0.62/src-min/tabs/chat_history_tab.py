"""
对话记录标签页 - 展示所有对话内容
"""
import sys
import os
import json
import weakref
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QLabel, QSizePolicy, QPushButton
)
from PySide6.QtCore import Qt, QFile, QTextStream, QTimer
import pyperclip

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


class ChatHistoryTab(BaseTab):
    """对话记录标签页 - 展示所有对话内容"""

    def __init__(self, project_path: Optional[str] = None, session_id: Optional[str] = None, workspace_id: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.session_id = session_id
        self.workspace_id = workspace_id

        # 计算 workspace_path
        if workspace_id and project_path:
            self.workspace_path = os.path.join(project_path, '.workspace', workspace_id)
        else:
            self.workspace_path = None

        # UI组件
        self.scroll_area = None
        self.messages_container = None
        self.messages_layout = None
        self.load_more_button = None

        # 历史记录管理
        self.all_history = []
        self.displayed_count = 10
        self.current_start_idx = -1  # 当前显示的起始索引，用于增量加载
        self._loaded = False  # 延迟加载标志

        self.create_ui()

    def create_ui(self):
        """创建对话记录Tab的UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 容器
        self.messages_container = QWidget()
        self.messages_container.setObjectName("messagesContainer")
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(15, 15, 15, 15)
        self.messages_layout.setSpacing(5)
        self.messages_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area)

        # 加载样式表
        self._load_stylesheet()

    def _load_stylesheet(self):
        """加载QSS样式表"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            qss_path = os.path.join(current_dir, "chat_history_style.qss")
            qss_file = QFile(qss_path)
            if qss_file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(qss_file)
                self.setStyleSheet(stream.readAll())
                qss_file.close()
            else:
                print(f"无法加载样式表: {qss_path}", file=sys.stderr)
        except Exception as e:
            print(f"加载样式表出错: {e}", file=sys.stderr)

    def load_history(self):
        """加载并显示对话历史记录"""
        # 清空现有消息
        self._clear_messages()

        # 读取历史记录
        self.all_history = self._load_history_from_file()

        if not self.all_history:
            # 如果没有历史记录,显示提示
            self._show_empty_message()
            return

        # 显示最后5条记录
        self._display_records()

    def _display_records(self):
        """显示记录(从最新的开始显示指定数量)"""
        # 清空所有现有消息
        self._clear_messages()
        self.load_more_button = None

        total = len(self.all_history)
        # 计算要显示的记录范围
        start_idx = max(0, total - self.displayed_count)
        self.current_start_idx = start_idx
        records_to_show = self.all_history[start_idx:]

        # 如果还有更多记录,显示"加载更多"按钮
        if start_idx > 0:
            self._add_load_more_button()

        # 显示记录
        for record in records_to_show:
            self._render_record(record)

    def _render_record(self, record):
        """渲染单条记录"""
        role = record.get('role')
        if role == 'user':
            self._add_user_message(record.get('content', ''))
        elif role == 'assistant':
            self._add_assistant_message(record.get('content', ''))
        elif role == 'tool':
            name = record.get('name', '')
            # feedback 工具拆分为两条消息
            if 'feedback' in name.lower():
                self._add_feedback_messages(record)
            else:
                self._add_tool_message(
                    name,
                    record.get('input', {}),
                    record.get('output', ''),
                    record.get('timestamp', '')
                )

    def _add_load_more_button(self):
        """添加加载更多按钮"""
        self.load_more_button = QPushButton("点击查看更多")
        self.load_more_button.setObjectName("loadMoreButton")
        self.load_more_button.clicked.connect(self._load_more)
        self.load_more_button.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        self.messages_layout.insertWidget(0, self.load_more_button)

    def _load_more(self):
        """增量加载更多记录，保持滚动位置"""
        if self.current_start_idx <= 0:
            return

        # 记录当前滚动位置
        scrollbar = self.scroll_area.verticalScrollBar()
        old_scroll_value = scrollbar.value()
        old_max = scrollbar.maximum()

        # 计算新的起始索引
        new_start_idx = max(0, self.current_start_idx - 10)
        new_records = self.all_history[new_start_idx:self.current_start_idx]
        self.current_start_idx = new_start_idx
        self.displayed_count += len(new_records)

        # 移除旧的"加载更多"按钮
        if self.load_more_button:
            self.messages_layout.removeWidget(self.load_more_button)
            self.load_more_button.deleteLater()
            self.load_more_button = None

        # 如果还有更多记录，添加新的"加载更多"按钮
        if new_start_idx > 0:
            self._add_load_more_button()

        # 记录插入位置（在"加载更多"按钮之后）
        insert_pos = 1 if self.load_more_button else 0

        # 在顶部插入新记录
        for record in new_records:
            count_before = self.messages_layout.count()
            self._render_record_at_position(record, insert_pos)
            widgets_added = self.messages_layout.count() - count_before
            insert_pos += widgets_added

        # 恢复滚动位置（使用两次延迟确保布局完全更新）
        def restore_scroll():
            # 强制处理布局更新
            self.messages_container.updateGeometry()
            # 再次延迟以确保滚动条范围已更新
            def do_restore():
                new_max = scrollbar.maximum()
                height_diff = new_max - old_max
                scrollbar.setValue(old_scroll_value + height_diff)
            QTimer.singleShot(50, do_restore)

        QTimer.singleShot(0, restore_scroll)

    def _render_record_at_position(self, record, position):
        """在指定位置渲染记录（用于增量加载）

        复用现有的 _render_record 方法，然后将新添加的 widget 移动到指定位置
        """
        # 记录当前 widget 数量
        count_before = self.messages_layout.count()

        # 使用现有方法添加记录（会添加到末尾）
        self._render_record(record)

        # 计算新添加的 widget 数量
        count_after = self.messages_layout.count()
        widgets_added = count_after - count_before

        # 从末尾取出新添加的 widgets，插入到指定位置
        for i in range(widgets_added):
            item = self.messages_layout.takeAt(count_before)
            if item and item.widget():
                self.messages_layout.insertWidget(position + i, item.widget())

    def _clear_messages(self):
        """清空所有消息"""
        while self.messages_layout.count():
            child = self.messages_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _show_empty_message(self):
        """显示无历史记录提示"""
        empty_label = QLabel("暂无对话记录")
        empty_label.setObjectName("emptyStateLabel")
        empty_label.setAlignment(Qt.AlignCenter)
        self.messages_layout.addWidget(empty_label)

    def _setup_content_display(self, content: str) -> MarkdownDisplayWidget:
        """创建并配置内容显示组件（使用MarkdownDisplayWidget）"""
        content_display = MarkdownDisplayWidget()
        content_display.setMarkdownText(content)
        content_display.setStyleSheet('''
            QTextEdit {
                background-color: transparent;
                border: none;
                padding: 0px;
                color: #e0e0e0;
            }
        ''')
        content_display.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content_display.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        # 根据内容自适应高度
        doc = content_display.document()
        doc.setTextWidth(content_display.viewport().width() if content_display.viewport().width() > 0 else 400)
        height = int(doc.size().height()) + 10
        content_display.setFixedHeight(height)

        return content_display

    def _create_avatar(self, text: str) -> QLabel:
        """创建头像标签"""
        label = QLabel(text)
        label.setObjectName("avatarLabel")
        label.setFixedSize(32, 32)
        label.setAlignment(Qt.AlignCenter)
        return label

    def _safe_set_text_later(self, widget, text: str, delay: int = 1000):
        """安全地延迟设置文本，使用弱引用避免访问已销毁对象"""
        weak_widget = weakref.ref(widget)

        def restore():
            w = weak_widget()
            if w is not None:
                try:
                    w.setText(text)
                except RuntimeError:
                    pass  # 对象已销毁

        QTimer.singleShot(delay, restore)

    def _copy_content(self, content: str, button: QPushButton):
        """复制内容到剪贴板"""
        try:
            pyperclip.copy(content)
            button.setText("✓")
            self._safe_set_text_later(button, "📋")
        except Exception as e:
            print(f"复制失败: {e}", file=sys.stderr)

    def _quote_content(self, msg_type: str, content: str, button: QPushButton):
        """生成引用格式并复制到剪贴板"""
        truncated = content[:100] + "..." if len(content) > 100 else content
        truncated = truncated.replace('\n', '\n> ')
        quote = f"----请回忆如下引用的历史对话内容----\n```quote\n[{msg_type}]\n{truncated}\n```\n---------"
        pyperclip.copy(quote)
        button.setText("✓")
        self._safe_set_text_later(button, "📎")

    def _save_content(self, content: str):
        """弹窗输入标题，保存为.md文件"""
        from PySide6.QtWidgets import QInputDialog
        title, ok = QInputDialog.getText(self, "保存文档", "请输入文档标题:")
        if ok and title:
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            if not safe_title:
                safe_title = "untitled"

            # 优先使用 workspace_path，否则回退到 project_path/.workspace/
            if self.workspace_path and os.path.exists(self.workspace_path):
                save_dir = self.workspace_path
            else:
                save_dir = os.path.join(self.project_path, '.workspace') if self.project_path else '.'

            os.makedirs(save_dir, exist_ok=True)
            file_path = os.path.join(save_dir, f"{safe_title}.md")

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)



    def _add_user_message(self, content: str):
        """添加用户消息（居左展示，与AI消息样式相同）"""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 5, 0, 5)
        row_layout.setSpacing(10)

        # 1. 头像
        avatar = self._create_avatar("👤")
        row_layout.addWidget(avatar, alignment=Qt.AlignTop)

        # 2. 消息气泡容器
        bubble_container = QWidget()
        bubble_layout = QVBoxLayout(bubble_container)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.setSpacing(2)

        # 角色标签和按钮
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        role_label = QLabel("User")
        role_label.setObjectName("roleLabel")
        header_layout.addWidget(role_label)

        copy_btn = QPushButton("📋")
        copy_btn.setFixedSize(24, 24)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
        """)
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.clicked.connect(lambda: self._copy_content(content, copy_btn))
        header_layout.addWidget(copy_btn)

        quote_btn = QPushButton("📎")
        quote_btn.setFixedSize(24, 24)
        quote_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
        """)
        quote_btn.setCursor(Qt.PointingHandCursor)
        quote_btn.clicked.connect(lambda: self._quote_content("用户消息", content, quote_btn))
        header_layout.addWidget(quote_btn)
        header_layout.addStretch()

        bubble_layout.addWidget(header_widget)

        # 气泡
        bubble = QFrame()
        bubble.setObjectName("aiBubble")  # 使用与AI相同的样式
        bubble_content_layout = QVBoxLayout(bubble)
        bubble_content_layout.setContentsMargins(12, 8, 12, 8)

        if content:
            content_display = self._setup_content_display(content)
            bubble_content_layout.addWidget(content_display)

        bubble_layout.addWidget(bubble)

        row_layout.addWidget(bubble_container, stretch=1)

        # 3. 右侧占位
        row_layout.addStretch(0)

        self.messages_layout.addWidget(row_widget)

    def _add_assistant_message(self, content: str):
        """添加AI消息"""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 5, 0, 5)
        row_layout.setSpacing(10)

        # 1. 头像
        avatar = self._create_avatar("🤖")
        row_layout.addWidget(avatar, alignment=Qt.AlignTop)

        # 2. 消息气泡容器
        bubble_container = QWidget()
        bubble_layout = QVBoxLayout(bubble_container)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.setSpacing(2)

        # 角色标签和复制按钮
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        role_label = QLabel("AI Assistant")
        role_label.setObjectName("roleLabel")
        header_layout.addWidget(role_label)

        copy_btn = QPushButton("📋")
        copy_btn.setFixedSize(24, 24)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
        """)
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.clicked.connect(lambda: self._copy_content(content, copy_btn))
        header_layout.addWidget(copy_btn)

        quote_btn = QPushButton("📎")
        quote_btn.setFixedSize(24, 24)
        quote_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
        """)
        quote_btn.setCursor(Qt.PointingHandCursor)
        quote_btn.clicked.connect(lambda: self._quote_content("AI回复", content, quote_btn))
        header_layout.addWidget(quote_btn)

        save_btn = QPushButton("💾")
        save_btn.setFixedSize(24, 24)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
        """)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(lambda: self._save_content(content))
        header_layout.addWidget(save_btn)
        header_layout.addStretch()

        bubble_layout.addWidget(header_widget)

        # 气泡
        bubble = QFrame()
        bubble.setObjectName("aiBubble")
        bubble_content_layout = QVBoxLayout(bubble)
        bubble_content_layout.setContentsMargins(12, 8, 12, 8)

        if content:
            content_display = self._setup_content_display(content)
            bubble_content_layout.addWidget(content_display)

        bubble_layout.addWidget(bubble)

        row_layout.addWidget(bubble_container, stretch=1)

        # 3. 右侧占位
        row_layout.addStretch(0)

        self.messages_layout.addWidget(row_widget)

    def _add_feedback_messages(self, record: Dict):
        """将 feedback 工具拆分为两条消息：AI反馈 + 用户回复"""
        input_data = record.get('input', {})
        output = record.get('output', '')

        # 消息1: AI 反馈 (使用 assistant 样式)
        work_title = input_data.get('work_title', '')
        message = input_data.get('message', '')
        options = input_data.get('predefined_options', [])
        files = input_data.get('files', [])

        parts = []
        if work_title:
            parts.append(f"📢 **{work_title}**")
        if message:
            parts.append(message)
        if options:
            parts.append(f"**选项**: {' | '.join(options)}")
        if files:
            file_list = ', '.join([f"`{f}`" for f in files])
            parts.append(f"**相关文件**: {file_list}")

        ai_content = '\n\n'.join(parts) if parts else ''
        if ai_content:
            self._add_assistant_message(ai_content)

        # 消息2: 用户回复 (使用 user 样式)
        user_content = self._extract_user_feedback(output)
        if user_content:
            self._add_user_message(user_content)

    def _extract_user_feedback(self, output: str) -> str:
        """从 feedback output 中提取用户输入"""
        if not output:
            return ''
        # 提取 💬 用户输入 或 🔘 用户选择 后面的内容
        for marker in ['💬 用户输入：\n', '🔘 用户选择的选项：\n']:
            if marker in output:
                idx = output.find(marker)
                content = output[idx + len(marker):]
                # 截断到 💡 请注意 之前
                if '💡 请注意' in content:
                    end_idx = content.find('💡 请注意')
                    content = content[:end_idx].strip()
                return content
        return ''

    def _format_tool_input(self, name: str, input_data: Dict) -> str:
        """格式化工具输入为 markdown"""
        if name == 'Task':
            desc = input_data.get('description', '')
            prompt = input_data.get('prompt', '')
            agent_type = input_data.get('subagent_type', '')
            parts = []
            # 格式: Agent(agent名称):描述
            if agent_type and desc:
                parts.append(f"**Agent**({agent_type}):{desc}")
            elif agent_type:
                parts.append(f"**Agent**({agent_type})")
            elif desc:
                parts.append(f"**描述**: {desc}")
            if prompt:
                parts.append(f"**Prompt**:\n{prompt}")
            return '\n\n'.join(parts) if parts else str(input_data)
        elif name in ('Read', 'Glob', 'Grep'):
            file_path = input_data.get('file_path', input_data.get('path', ''))
            pattern = input_data.get('pattern', '')
            parts = []
            if file_path:
                parts.append(f"**路径**: `{file_path}`")
            if pattern:
                parts.append(f"**模式**: `{pattern}`")
            return '\n'.join(parts) if parts else str(input_data)
        elif name in ('Edit', 'Write'):
            file_path = input_data.get('file_path', '')
            return f"**文件**: `{file_path}`" if file_path else str(input_data)
        elif name == 'Hook':
            cmd = input_data.get('command', '')
            return f"**命令**: `{cmd}`" if cmd else str(input_data)
        elif 'feedback' in name.lower():
            # feedback 工具特殊处理
            work_title = input_data.get('work_title', '')
            message = input_data.get('message', '')
            options = input_data.get('predefined_options', [])
            files = input_data.get('files', [])
            parts = []
            if work_title:
                parts.append(f"📢 **{work_title}**")
            if message:
                parts.append(message)
            if options:
                parts.append(f"**选项**: {' | '.join(options)}")
            if files:
                parts.append(f"**相关文件**: {', '.join(files)}")
            return '\n\n'.join(parts) if parts else str(input_data)
        else:
            # 其他工具显示简化的 JSON
            input_str = json.dumps(input_data, ensure_ascii=False, indent=2)
            if len(input_str) > 300:
                input_str = input_str[:300] + "..."
            return f"```json\n{input_str}\n```"

    def _format_feedback_output(self, output: str) -> str:
        """格式化 feedback 工具的输出，提取用户输入"""
        if not output:
            return ''
        # 提取 💬 用户输入 或 🔘 用户选择 后面的内容
        for marker in ['💬 用户输入：\n', '🔘 用户选择的选项：\n']:
            if marker in output:
                idx = output.find(marker)
                content = output[idx + len(marker):]
                # 截断到 💡 请注意 之前
                if '💡 请注意' in content:
                    end_idx = content.find('💡 请注意')
                    content = content[:end_idx].strip()
                return f"**用户反馈**: {content}" if content else ''
        return ''

    def _add_tool_message(self, name: str, input_data: Dict, output: str, timestamp: str):
        """添加工具调用消息（默认折叠，feedback 默认展开）"""
        is_feedback = 'feedback' in name.lower()

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 2, 0, 2)
        row_layout.setSpacing(10)

        # 1. 头像
        avatar = self._create_avatar("💬" if is_feedback else "⚙️")
        row_layout.addWidget(avatar, alignment=Qt.AlignTop)

        # 2. 消息气泡容器
        bubble_container = QWidget()
        bubble_layout = QVBoxLayout(bubble_container)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.setSpacing(2)

        # 生成标题文本
        # Task 工具特殊处理：显示 Agent(agent_type): description
        if name == 'Task':
            agent_type = input_data.get('subagent_type', '')
            desc = input_data.get('description', '')
            if agent_type and desc:
                header_title = f"Agent({agent_type}): {desc}"
            elif agent_type:
                header_title = f"Agent({agent_type})"
            else:
                header_title = f"Tool: {name}"
        else:
            header_title = f"Tool: {name}"

        # 可点击的标题（用于展开/折叠）+ 复制按钮
        # feedback 默认展开，其他默认折叠
        initial_expanded = is_feedback

        # Header 容器（包含折叠按钮和复制按钮）
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        header_btn = QPushButton(f"{'▼' if initial_expanded else '▶'} {header_title}")
        header_btn.setObjectName("toolHeaderButton")
        # Task/Agent 使用绿色，其他工具使用灰色
        header_color = "#4CAF50" if name == 'Task' else "#888"
        header_hover_color = "#66BB6A" if name == 'Task' else "#aaa"
        header_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {header_color};
                border: none;
                text-align: left;
                padding: 2px 0;
                font-size: 12px;
            }}
            QPushButton:hover {{
                color: {header_hover_color};
                cursor: pointer;
            }}
        """)
        header_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(header_btn)

        # 复制按钮
        copy_btn = QPushButton("📋")
        copy_btn.setFixedSize(24, 24)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
        """)
        copy_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(copy_btn)

        # 引用按钮
        quote_btn = QPushButton("📎")
        quote_btn.setFixedSize(24, 24)
        quote_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
        """)
        quote_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(quote_btn)

        # 保存按钮
        save_btn = QPushButton("💾")
        save_btn.setFixedSize(24, 24)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
        """)
        save_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(save_btn)
        header_layout.addStretch()

        bubble_layout.addWidget(header_widget)

        # 气泡（feedback 默认显示，其他默认隐藏）
        bubble = QFrame()
        bubble.setObjectName("aiBubble")
        bubble.setVisible(initial_expanded)
        bubble_content_layout = QVBoxLayout(bubble)
        bubble_content_layout.setContentsMargins(12, 8, 12, 8)

        # 格式化输入
        input_str = self._format_tool_input(name, input_data)

        # 输出内容
        output_str = str(output) if output else ''

        # 过滤掉 agentId 行（Agent 调用结果中的元信息）
        if output_str:
            lines = output_str.split('\n')
            filtered_lines = [line for line in lines if not line.strip().startswith('agentId:')]
            output_str = '\n'.join(filtered_lines).strip()

        # 处理 base64 图片 (只有真正的 base64 数据才替换)
        # 真正的 base64 图片数据通常包含 data:image 或者是纯 base64 编码的长字符串
        if output_str and len(output_str) > 500:
            # 检测是否为 base64 图片数据
            is_base64_image = (
                'data:image' in output_str.lower() or
                (output_str.startswith('/9j/') or output_str.startswith('iVBOR'))  # JPEG/PNG base64 头
            )
            if is_base64_image:
                output_str = "[图片]"

        # feedback 工具特殊处理输出
        if is_feedback:
            output_str = self._format_feedback_output(output_str)

        # 构建内容（不再截断，展示完整内容）
        content_parts = [f"**Input:**\n{input_str}"]
        if output_str:
            content_parts.append(f"**Output:**\n{output_str}")
        else:
            content_parts.append("**Output:** (无输出)")
        content = '\n\n'.join(content_parts)
        content_display = self._setup_content_display(content)
        bubble_content_layout.addWidget(content_display)

        bubble_layout.addWidget(bubble)

        # 复制按钮点击事件（复制完整内容：Input + Output）
        copy_btn.clicked.connect(lambda: self._copy_content(content, copy_btn))

        # 引用按钮点击事件
        quote_btn.clicked.connect(lambda: self._quote_content(f"工具调用: {name}", content, quote_btn))

        # 保存按钮点击事件
        save_btn.clicked.connect(lambda: self._save_content(content))

        # 点击展开/折叠
        def toggle_content():
            is_visible = bubble.isVisible()
            bubble.setVisible(not is_visible)
            header_btn.setText(f"{'▼' if not is_visible else '▶'} {header_title}")

        header_btn.clicked.connect(toggle_content)

        row_layout.addWidget(bubble_container, stretch=1)

        # 3. 右侧占位
        row_layout.addStretch(0)

        self.messages_layout.addWidget(row_widget)

    def _load_history_from_file(self) -> List[Dict]:
        """从Claude Code的session .jsonl文件加载历史记录"""
        try:
            if not self.session_id or not self.project_path:
                return []

            # 编码项目路径 (Claude Code 将 / 和 _ 都替换为 -)
            encoded_path = self.project_path.replace('/', '-').replace('_', '-')

            # 构建 .jsonl 文件路径
            home_dir = os.path.expanduser('~')
            jsonl_file = os.path.join(home_dir, '.claude', 'projects', encoded_path, f'{self.session_id}.jsonl')

            if not os.path.exists(jsonl_file):
                return []

            # 读取所有行
            lines = []
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 第一遍：收集所有 tool_results
            tool_results = {}
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    message = entry.get('message', {})
                    if message.get('role') != 'user':
                        continue
                    content = message.get('content', [])
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get('type') == 'tool_result':
                                tool_use_id = item.get('tool_use_id')
                                tool_content = item.get('content', '')
                                # 处理 content 为数组的情况
                                if isinstance(tool_content, list):
                                    texts = []
                                    for c in tool_content:
                                        if isinstance(c, dict) and c.get('type') == 'text':
                                            texts.append(c.get('text', ''))
                                    tool_content = '\n'.join(texts)
                                if tool_use_id:
                                    tool_results[tool_use_id] = tool_content
                except json.JSONDecodeError:
                    continue

            # 第二遍：构建消息列表
            messages = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                    message = entry.get('message', {})
                    role = message.get('role')

                    # 处理 system 消息 (hook)
                    entry_type = entry.get('type')
                    if entry_type == 'system':
                        subtype = entry.get('subtype', '')
                        if subtype == 'stop_hook_summary':
                            hook_infos = entry.get('hookInfos', [])
                            hook_errors = entry.get('hookErrors', [])
                            hook_cmd = hook_infos[0].get('command', '') if hook_infos else ''
                            # hookErrors 实际上是 hook 的输出内容
                            hook_output = '\n'.join(hook_errors) if hook_errors else '执行完成'
                            messages.append({
                                'role': 'tool',
                                'name': 'Hook',
                                'input': {'command': hook_cmd},
                                'output': hook_output,
                                'timestamp': entry.get('timestamp', '')
                            })
                        continue

                    if role not in ['user', 'assistant']:
                        continue

                    timestamp = entry.get('timestamp', '')
                    content = message.get('content', [])

                    # 处理 user 消息
                    if role == 'user':
                        if isinstance(content, str):
                            # 过滤 hook 注入的内容（在 "Stop hook feedback:" 或 "hook feedback:" 后面）
                            user_content = content
                            for marker in ['Stop hook feedback:\n', 'hook feedback:\n']:
                                if marker in user_content:
                                    # 只保留 marker 之前的内容 + marker 本身
                                    idx = user_content.find(marker)
                                    user_content = user_content[:idx + len(marker)].rstrip()
                                    break
                            if user_content:
                                messages.append({'role': 'user', 'content': user_content, 'timestamp': timestamp})
                        # tool_result 不作为独立消息显示

                    # 处理 assistant 消息
                    elif role == 'assistant':
                        if isinstance(content, list):
                            for item in content:
                                if not isinstance(item, dict):
                                    continue

                                item_type = item.get('type')

                                # 文本消息
                                if item_type == 'text':
                                    text = item.get('text', '')
                                    if text:
                                        messages.append({'role': 'assistant', 'content': text, 'timestamp': timestamp})

                                # 工具调用
                                elif item_type == 'tool_use':
                                    tool_id = item.get('id')
                                    tool_name = item.get('name', '')
                                    tool_input = item.get('input', {})
                                    tool_output = tool_results.get(tool_id, '')

                                    messages.append({
                                        'role': 'tool',
                                        'name': tool_name,
                                        'input': tool_input,
                                        'output': tool_output,
                                        'timestamp': timestamp
                                    })

                except json.JSONDecodeError:
                    continue

            return messages

        except Exception as e:
            print(f"加载历史记录失败: {e}", file=sys.stderr)
            return []


    def refresh_history(self):
        """刷新历史记录"""
        self.load_history()
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        """滚动到底部"""
        weak_scroll = weakref.ref(self.scroll_area)

        def do_scroll():
            scroll = weak_scroll()
            if scroll is not None:
                try:
                    scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
                except RuntimeError:
                    pass  # 对象已销毁

        QTimer.singleShot(100, do_scroll)

    def showEvent(self, event):
        """Tab显示时加载历史记录并滚动到底部"""
        super().showEvent(event)
        if not self._loaded:
            self._loaded = True
            self.load_history()
        self._scroll_to_bottom()
