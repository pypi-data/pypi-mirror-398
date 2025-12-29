"""
Agent 内容弹窗组件
"""

from typing import Dict
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QApplication
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QKeyEvent

from .markdown_display import MarkdownDisplayWidget


class AgentPopup(QFrame):
    """Agent 内容弹窗组件"""

    popup_closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
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
            }
        """)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(12, 8, 12, 8)

        self.title_label = QLabel()
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(self.title_label)

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

        # 内容区域
        self.content_widget = MarkdownDisplayWidget()
        self.content_widget.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e;
                border: none;
                padding: 12px;
                color: #e0e0e0;
                font-size: 13px;
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
        layout.addWidget(self.content_widget, 1)

        # 底部统计栏
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background: #2b2b2b;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
                padding: 8px;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)

        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 11px;
            }
        """)
        stats_layout.addWidget(self.stats_label, alignment=Qt.AlignCenter)

        layout.addWidget(stats_frame)

        # 整体样式
        self.setStyleSheet("""
            AgentPopup {
                background: #1e1e1e;
                border: 1px solid #444;
                border-radius: 8px;
            }
        """)

    def set_agent_data(self, agent_record: Dict):
        """设置 agent 数据"""
        subagent_type = agent_record.get('subagent_type', 'Agent')
        description = agent_record.get('description', '')
        content = agent_record.get('content', '')
        duration_ms = agent_record.get('duration_ms', 0)
        tokens = agent_record.get('tokens', 0)
        tool_calls = agent_record.get('tool_calls', 0)

        # 设置标题
        self.title_label.setText(f"{subagent_type}: {description}")

        # 设置内容
        self.content_widget.setMarkdownText(content)

        # 设置统计信息
        stats_text = f"耗时: {duration_ms}ms | Tokens: {tokens} | 工具调用: {tool_calls}次"
        self.stats_label.setText(stats_text)

    def show_at_position(self, position: QPoint):
        """在指定位置显示弹窗"""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()

        popup_width = 500
        popup_height = 700

        self.resize(popup_width, popup_height)

        if position and position.x() >= 0 and position.y() >= 0:
            x = position.x()
            y = position.y()

            if x + popup_width > screen_geometry.right():
                x = screen_geometry.right() - popup_width - 10
            if y + popup_height > screen_geometry.bottom():
                y = screen_geometry.bottom() - popup_height - 10
            if x < screen_geometry.x():
                x = screen_geometry.x()
            if y < screen_geometry.y():
                y = screen_geometry.y()
        else:
            x = screen_geometry.x() + (screen_geometry.width() - popup_width) // 2
            y = screen_geometry.y() + (screen_geometry.height() - popup_height) // 2

        self.move(x, y)
        self.show()
        self.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        """处理键盘事件"""
        if event.key() == Qt.Key_Escape:
            self.popup_closed.emit()
            self.close()
        else:
            super().keyPressEvent(event)
