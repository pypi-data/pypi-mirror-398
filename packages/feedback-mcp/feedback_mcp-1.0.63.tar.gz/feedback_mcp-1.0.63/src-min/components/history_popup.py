"""
历史记录弹窗组件 - 聊天对话样式展示历史记录
"""

import logging
from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QScrollArea, QWidget, QLabel, QPushButton, QHBoxLayout,
    QApplication, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QKeyEvent, QFont, QTextCursor

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class HistoryPopup(QFrame):
    """历史记录弹窗组件 - 聊天对话样式"""

    # 信号定义
    content_inserted = Signal(str)     # 内容插入信号
    content_copied = Signal(str)       # 内容复制信号
    popup_closed = Signal()            # 弹窗关闭信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_records = []  # 存储历史记录数据
        self.parent_window = None  # 父窗口引用，用于访问输入框

        self._setup_ui()
        self._setup_style()

        # 设置窗口属性
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose)

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题栏
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 12px;
            }
        """)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(12, 8, 12, 8)

        self.title_label = QLabel("💬 聊天历史")
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(self.title_label)

        # 关闭按钮
        close_button = QPushButton("✕")
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 10px;
            }
        """)
        close_button.clicked.connect(self.close)
        title_layout.addWidget(close_button)

        layout.addWidget(title_frame)

        # 聊天记录滚动容器
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: #1e1e1e;
                border: none;
            }
            QScrollBar:vertical {
                background: #2b2b2b;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666;
            }
        """)

        # 内容容器widget
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: #1e1e1e;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(12)
        self.content_layout.setContentsMargins(12, 12, 12, 12)

        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)

        # 底部提示栏
        hint_frame = QFrame()
        hint_frame.setStyleSheet("""
            QFrame {
                background: #2b2b2b;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
                padding: 8px;
            }
        """)
        hint_layout = QHBoxLayout(hint_frame)

        self.hint_label = QLabel("💡 点击消息可插入或复制 | ESC 关闭")
        self.hint_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 11px;
            }
        """)
        hint_layout.addWidget(self.hint_label, alignment=Qt.AlignCenter)

        layout.addWidget(hint_frame)

    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            HistoryPopup {
                background: #1e1e1e;
                border: 1px solid #444;
                border-radius: 8px;
            }
        """)

    def set_history_records(self, records: List[Dict[str, Any]], parent_window=None):
        """设置历史记录列表

        Args:
            records: 历史记录列表，每个记录包含content, time_display等字段
            parent_window: 父窗口引用，用于访问输入框
        """
        self.history_records = records
        self.parent_window = parent_window
        self._update_history_list()

    def _update_history_list(self):
        """更新历史记录列表"""
        # 清空现有内容
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.history_records:
            # 显示空状态
            empty_label = QLabel("暂无聊天记录")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("""
                QLabel {
                    color: #666;
                    padding: 40px;
                    font-size: 14px;
                }
            """)
            self.content_layout.addWidget(empty_label)
            return

        # 添加历史记录项（最新的在下面，模拟聊天界面）
        for record in self.history_records:
            self._create_dialogue_item(record)

        # 添加空白占位，让内容可以滚动到底部
        spacer = QWidget()
        spacer.setFixedHeight(20)
        self.content_layout.addWidget(spacer)

    def _create_dialogue_item(self, record: Dict[str, Any]):
        """创建对话记录项（兼容旧格式和新格式）

        Args:
            record: 记录数据
        """
        try:
            # 新格式：不含type字段，直接包含messages数组
            if 'messages' in record and isinstance(record.get('messages'), list):
                # 显示时间分隔线
                if record.get('time_display'):
                    time_label = QLabel(record['time_display'])
                    time_label.setAlignment(Qt.AlignCenter)
                    time_label.setStyleSheet("""
                        QLabel {
                            color: #666;
                            font-size: 10px;
                            padding: 4px;
                            margin: 8px 0;
                        }
                    """)
                    self.content_layout.addWidget(time_label)

                # 显示对话消息
                for msg in record['messages']:
                    self._create_message_bubble(msg)
            else:
                # 兼容旧格式的单条消息
                msg = {
                    'role': 'user',
                    'content': record.get('content', ''),
                    'time': record.get('time_display', '').split(' ')[-1] if 'time_display' in record else ''
                }
                self._create_message_bubble(msg)

        except Exception as e:
            logger.error(f"创建对话记录项失败: {e}")

    def _create_message_bubble(self, msg: Dict[str, Any]):
        """创建消息气泡

        Args:
            msg: 消息数据
        """
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        time = msg.get('time', '')

        # 创建消息容器
        msg_container = QWidget()
        msg_layout = QHBoxLayout(msg_container)
        msg_layout.setContentsMargins(0, 4, 0, 4)
        msg_layout.setSpacing(10)
        msg_layout.setAlignment(Qt.AlignLeft)  # 统一左对齐

        # 头像 - 根据角色显示不同的图标和背景
        if role == 'user':
            avatar_label = QLabel("👤")
            avatar_bg = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        else:
            avatar_label = QLabel("🤖")
            avatar_bg = "linear-gradient(135deg, #00c853 0%, #00897b 100%)"

        avatar_label.setFixedSize(36, 36)
        avatar_label.setAlignment(Qt.AlignCenter)
        avatar_label.setStyleSheet(f"""
            QLabel {{
                background: {avatar_bg};
                border-radius: 18px;
                font-size: 18px;
            }}
        """)
        msg_layout.addWidget(avatar_label, alignment=Qt.AlignTop)

        # 消息内容区域
        content_frame = QFrame()
        # 移除最大宽度限制，让内容框架填充整个可用宽度
        content_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)

        # 用户名称和时间行
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # 用户名称
        name_label = QLabel("用户" if role == 'user' else "AI助手")
        name_label.setStyleSheet("""
            QLabel {
                color: #fff;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(name_label)

        # 时间标签
        if time:
            time_label = QLabel(time)
            time_label.setStyleSheet("""
                QLabel {
                    color: #888;
                    font-size: 10px;
                }
            """)
            header_layout.addWidget(time_label)

        header_layout.addStretch()
        content_layout.addLayout(header_layout)

        # 消息内容框架
        bubble_frame = QFrame()
        bubble_frame.setStyleSheet("""
            QFrame {
                background: #2b2b2b;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                padding: 10px 12px;
            }
        """)

        bubble_layout = QVBoxLayout(bubble_frame)
        bubble_layout.setContentsMargins(0, 0, 0, 0)

        # 消息内容
        content_label = QLabel(content[:300] + "..." if len(content) > 300 else content)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        if len(content) > 300:
            content_label.setToolTip(content)
        bubble_layout.addWidget(content_label)

        content_layout.addWidget(bubble_frame)

        # 添加操作按钮（悬浮显示）
        self._add_hover_buttons(bubble_frame, content)

        msg_layout.addWidget(content_frame, 1)  # 设置stretch factor为1，让内容框架占据所有可用空间

        self.content_layout.addWidget(msg_container)

    def _add_hover_buttons(self, bubble_frame, content):
        """添加悬浮操作按钮

        Args:
            bubble_frame: 消息气泡框架
            content: 消息内容
        """
        # 创建按钮容器
        button_container = QWidget(bubble_frame)
        button_container.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.8);
                border-radius: 4px;
            }
        """)
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(4, 4, 4, 4)
        button_layout.setSpacing(4)

        # 插入按钮
        insert_btn = QPushButton("📥")
        insert_btn.setToolTip("插入到输入框")
        insert_btn.setFixedSize(24, 24)
        insert_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        insert_btn.clicked.connect(lambda: self._handle_insert(content))
        button_layout.addWidget(insert_btn)

        # 复制按钮
        copy_btn = QPushButton("📋")
        copy_btn.setToolTip("复制到剪贴板")
        copy_btn.setFixedSize(24, 24)
        copy_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        copy_btn.clicked.connect(lambda: self._handle_copy(content))
        button_layout.addWidget(copy_btn)

        # 初始隐藏，悬浮时显示
        button_container.hide()
        button_container.raise_()  # 确保按钮在最上层

        # 设置悬浮事件
        def show_buttons(event):
            # 计算按钮位置（右上角）
            button_container.move(
                bubble_frame.width() - button_container.width() - 8,
                8
            )
            button_container.show()

        def hide_buttons(event):
            button_container.hide()

        bubble_frame.enterEvent = show_buttons
        bubble_frame.leaveEvent = hide_buttons

    def _handle_insert(self, content: str):
        """处理插入操作"""
        try:
            # 尝试直接插入到输入框
            if self._insert_to_textbox(content):
                # 插入成功，发出信号并关闭弹窗
                self.content_inserted.emit(content)
                self.close()
            else:
                # 插入失败，回退到复制功能
                logger.warning("插入失败，回退到复制功能")
                self._handle_copy(content)
        except Exception as e:
            logger.error(f"插入内容失败: {e}")
            # 出错时回退到复制功能
            self._handle_copy(content)

    def _handle_copy(self, content: str):
        """处理复制操作"""
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(content)

            # 发出信号并关闭弹窗
            self.content_copied.emit(content)
            self.close()

        except Exception as e:
            logger.error(f"复制到剪贴板失败: {e}")

    def _insert_to_textbox(self, content: str) -> bool:
        """将内容插入到对话框输入框中

        Args:
            content: 要插入的内容

        Returns:
            bool: 插入是否成功
        """
        try:
            # 尝试获取主窗口的聊天标签页和输入框
            if self.parent_window:
                # 方法1：通过parent_window查找chat_tab
                if hasattr(self.parent_window, 'chat_tab') and self.parent_window.chat_tab:
                    feedback_text = self.parent_window.chat_tab.feedback_text
                    if feedback_text:
                        return self._do_insert(feedback_text, content)

                # 方法2：向上查找包含FeedbackTextEdit的窗口
                from PySide6.QtWidgets import QTextEdit
                parent = self.parent_window
                while parent:
                    # 在所有子控件中查找FeedbackTextEdit
                    feedback_widgets = parent.findChildren(QTextEdit)
                    for widget in feedback_widgets:
                        if hasattr(widget, 'pasted_images'):  # FeedbackTextEdit特有属性
                            return self._do_insert(widget, content)

                    parent = parent.parent()

            return False

        except Exception as e:
            logger.error(f"查找输入框失败: {e}")
            return False

    def _do_insert(self, text_widget, content: str) -> bool:
        """执行插入操作

        Args:
            text_widget: 文本输入控件
            content: 要插入的内容

        Returns:
            bool: 插入是否成功
        """
        try:
            # 获取当前文本
            current_text = text_widget.toPlainText()

            # 如果输入框有内容，在末尾添加换行后插入新内容
            if current_text.strip():
                new_text = current_text + "\n\n" + content
            else:
                new_text = content

            # 设置新文本
            text_widget.setPlainText(new_text)

            # 设置焦点到输入框
            text_widget.setFocus()

            # 将光标移动到末尾
            cursor = text_widget.textCursor()
            cursor.movePosition(QTextCursor.End)
            text_widget.setTextCursor(cursor)

            logger.info(f"成功插入内容: {content[:50]}...")
            return True

        except Exception as e:
            logger.error(f"执行插入操作失败: {e}")
            return False

    def keyPressEvent(self, event: QKeyEvent):
        """处理键盘事件"""
        if event.key() == Qt.Key_Escape:
            # ESC键关闭弹窗
            self.popup_closed.emit()
            self.close()
        else:
            super().keyPressEvent(event)

    def show_at_position(self, position: QPoint):
        """在指定位置显示弹窗"""
        # 获取屏幕信息
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()

        # 设置弹窗大小与feedback UI一致：500x700
        popup_width = 500
        popup_height = 700

        # 设置弹窗大小
        self.resize(popup_width, popup_height)

        # 使用传入的位置（左边缘对齐）
        if position and position.x() >= 0 and position.y() >= 0:
            x = position.x()  # 使用传入的x坐标（已经是左对齐）
            y = position.y()  # 使用传入的y坐标

            # 确保不超出屏幕右边界
            if x + popup_width > screen_geometry.right():
                x = screen_geometry.right() - popup_width - 10

            # 确保不超出屏幕底部
            if y + popup_height > screen_geometry.bottom():
                y = screen_geometry.bottom() - popup_height - 10

            # 确保不超出屏幕左边界和顶部
            if x < screen_geometry.x():
                x = screen_geometry.x()
            if y < screen_geometry.y():
                y = screen_geometry.y()
        else:
            # 居中显示
            x = screen_geometry.x() + (screen_geometry.width() - popup_width) // 2
            y = screen_geometry.y() + (screen_geometry.height() - popup_height) // 2

        self.move(x, y)
        self.show()
        self.setFocus()

        # 滚动到底部显示最新消息
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

        logger.info(f"历史记录弹窗显示在位置: ({x}, {y}), 大小: {popup_width}x{popup_height}")