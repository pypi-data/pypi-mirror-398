"""
文件选择弹窗组件 - 用于选择项目文件
"""

import os
import fnmatch
from typing import List, Dict, Any, Set
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QScrollArea, QWidget, QGridLayout, QPushButton, QLabel
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QKeyEvent, QFont


class FilePopup(QFrame):
    """文件选择弹窗组件"""

    # 信号定义
    file_selected = Signal(str)  # 选中文件路径
    popup_closed = Signal()      # 弹窗关闭

    # 默认排除的目录
    DEFAULT_EXCLUDED = {'.git', 'node_modules', '__pycache__', '.venv', 'venv',
                        'dist', 'build', '.idea', '.vscode', '.workspace'}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.files = []  # 存储文件数据
        self.filtered_files = []  # 过滤后的文件
        self.filter_text = ""  # 过滤文本
        self.project_dir = ""  # 项目目录

        # 导航相关属性
        self.current_index = -1
        self.file_buttons = []

        # 分页相关
        self.page_size = 50
        self.current_page = 0

        self._setup_ui()
        self._setup_style()

        # 设置窗口属性
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        # 标题
        self.title_label = QLabel("📁 选择文件")
        self.title_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.title_label.setFont(font)
        layout.addWidget(self.title_label)

        # 文件列表容器
        self.scroll_area = QScrollArea()
        self.scroll_area.setMaximumHeight(500)
        self.scroll_area.setMinimumHeight(100)
        self.scroll_area.setMinimumWidth(450)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 网格容器
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(4)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)

        self.scroll_area.setWidget(self.grid_widget)
        layout.addWidget(self.scroll_area)

        # 提示标签
        self.hint_label = QLabel("↑↓ 方向键选择 | Enter 确认 | Esc 取消")
        self.hint_label.setAlignment(Qt.AlignCenter)
        hint_font = QFont()
        hint_font.setPointSize(8)
        self.hint_label.setFont(hint_font)
        layout.addWidget(self.hint_label)

    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            FilePopup {
                background-color: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            QLabel {
                color: #ffffff;
                padding: 4px;
            }
            QScrollArea {
                background-color: #2b2b2b;
                border: none;
            }
            QPushButton {
                background-color: #2b2b2b;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                color: #cccccc;
                padding: 4px 8px;
                text-align: left;
                min-height: 16px;
                max-height: 24px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #353535;
                border-color: #4a4a4a;
            }
            QPushButton:focus {
                background-color: #0078d4;
                border-color: #0078d4;
                color: white;
            }
        """)

    def set_project_dir(self, project_dir: str):
        """设置项目目录并扫描文件"""
        self.project_dir = project_dir
        self._load_gitignore()
        self._scan_files()

    def _load_gitignore(self):
        """加载 .gitignore 规则"""
        self.gitignore_patterns = []
        if not self.project_dir:
            return
        gitignore_path = os.path.join(self.project_dir, '.gitignore')
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            self.gitignore_patterns.append(line)
            except Exception:
                pass

    def _is_ignored(self, rel_path: str, is_dir: bool) -> bool:
        """检查路径是否被 gitignore 忽略"""
        # 检查默认排除
        parts = rel_path.split(os.sep)
        for part in parts:
            if part in self.DEFAULT_EXCLUDED:
                return True
        # 检查 gitignore 规则
        for pattern in self.gitignore_patterns:
            # 处理目录模式
            if pattern.endswith('/'):
                if is_dir and fnmatch.fnmatch(rel_path, pattern[:-1]):
                    return True
                if fnmatch.fnmatch(rel_path + '/', '*' + pattern):
                    return True
            # 通用匹配
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(rel_path, '*/' + pattern):
                return True
            if fnmatch.fnmatch(os.path.basename(rel_path), pattern):
                return True
        return False

    def _scan_files(self):
        """扫描项目目录中的文件"""
        self.files = []
        if not self.project_dir or not os.path.exists(self.project_dir):
            return

        for root, dirs, files in os.walk(self.project_dir):
            rel_root = os.path.relpath(root, self.project_dir)
            if rel_root == '.':
                rel_root = ''

            # 排除目录
            dirs[:] = [d for d in dirs if not self._is_ignored(
                os.path.join(rel_root, d) if rel_root else d, True)]

            # 添加目录
            for dir_name in dirs:
                rel_path = os.path.join(rel_root, dir_name) if rel_root else dir_name
                self.files.append({
                    "path": os.path.join(root, dir_name),
                    "name": dir_name,
                    "rel_path": rel_path,
                    "is_dir": True
                })

            # 添加文件
            for file_name in files:
                rel_path = os.path.join(rel_root, file_name) if rel_root else file_name
                if not self._is_ignored(rel_path, False):
                    self.files.append({
                        "path": os.path.join(root, file_name),
                        "name": file_name,
                        "rel_path": rel_path,
                        "is_dir": False
                    })

        # 按路径排序
        self.files.sort(key=lambda x: x["rel_path"])
        self._update_filtered_files()

    def set_filter(self, filter_text: str):
        """设置过滤文本"""
        self.filter_text = filter_text.lower()
        self.current_page = 0
        self._update_filtered_files()

    def _calc_match_score(self, file_info: Dict[str, Any], keyword: str) -> int:
        """计算匹配度分数（分数越小优先级越高）"""
        name = file_info["name"].lower()
        rel_path = file_info["rel_path"].lower()
        is_dir = file_info["is_dir"]

        # 基础分数（文件夹优先）
        base = 0 if is_dir else 1000

        # 名称完全匹配
        if name == keyword or name.rstrip("/\\") == keyword:
            return base + 0
        # 名称开头匹配
        if name.startswith(keyword):
            return base + 100
        # 名称包含匹配
        if keyword in name:
            return base + 200
        # 路径包含匹配（按位置，越靠左优先级越高）
        pos = rel_path.find(keyword)
        if pos >= 0:
            return base + 300 + pos
        return base + 10000

    def _update_filtered_files(self):
        """更新过滤后的文件列表"""
        if self.filter_text:
            # 过滤匹配的文件
            matched = [
                f for f in self.files
                if self.filter_text in f["name"].lower() or
                   self.filter_text in f["rel_path"].lower()
            ]
            # 按匹配度排序
            self.filtered_files = sorted(
                matched,
                key=lambda f: (self._calc_match_score(f, self.filter_text), len(f["rel_path"]), f["rel_path"])
            )
        else:
            self.filtered_files = self.files.copy()

        self._update_list_widget()

    def _update_list_widget(self):
        """更新文件列表显示"""
        # 清空现有按钮
        for button in self.file_buttons:
            button.deleteLater()
        self.file_buttons.clear()

        # 清空布局
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.filtered_files:
            empty_label = QLabel("😔 没有找到匹配的文件")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #888888; padding: 20px;")
            self.grid_layout.addWidget(empty_label, 0, 0, 1, 2)
            return

        # 分页显示
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.filtered_files))
        page_files = self.filtered_files[start_idx:end_idx]

        # 显示文件
        for i, file_info in enumerate(page_files):
            icon = "📁" if file_info["is_dir"] else "📄"
            display_text = f"{i + 1}. {icon} {file_info['rel_path']}"

            button = QPushButton(display_text)
            button.setToolTip(file_info["path"])
            button.clicked.connect(lambda checked, f=file_info: self._on_file_clicked(f))

            self.grid_layout.addWidget(button, i, 0, 1, 2)
            self.file_buttons.append(button)

        # 更新标题显示分页信息
        total_pages = (len(self.filtered_files) + self.page_size - 1) // self.page_size
        if total_pages > 1:
            self.title_label.setText(
                f"📁 选择文件 (第 {self.current_page + 1}/{total_pages} 页)"
            )
        else:
            self.title_label.setText("📁 选择文件")

    def _on_file_clicked(self, file_info: Dict[str, Any]):
        """处理文件点击"""
        self.file_selected.emit(file_info["path"])
        self.close()

    def keyPressEvent(self, event: QKeyEvent):
        """处理键盘事件"""
        if event.key() == Qt.Key_Escape:
            self.popup_closed.emit()
            self.close()

        elif event.key() in (Qt.Key_Up, Qt.Key_Down):
            self._handle_arrow_navigation(event.key())
            event.accept()

        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._confirm_selection()
            event.accept()

        elif event.text().isdigit():
            num = int(event.text())
            if num > 0 and num <= len(self.file_buttons):
                start_idx = self.current_page * self.page_size
                file_info = self.filtered_files[start_idx + num - 1]
                self._on_file_clicked(file_info)
            event.accept()

        else:
            super().keyPressEvent(event)

    def _handle_arrow_navigation(self, key):
        """处理方向键导航"""
        if not self.file_buttons:
            return

        if self.current_index == -1:
            self.current_index = 0
        else:
            if key == Qt.Key_Up and self.current_index > 0:
                self.current_index -= 1
            elif key == Qt.Key_Down and self.current_index < len(self.file_buttons) - 1:
                self.current_index += 1

        self._update_button_focus()

    def _update_button_focus(self):
        """更新按钮焦点状态"""
        for i, button in enumerate(self.file_buttons):
            if i == self.current_index:
                button.setFocus()
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #0078d4;
                        border: 1px solid #0078d4;
                        color: white;
                        padding: 4px 8px;
                        text-align: left;
                        min-height: 16px;
                        max-height: 24px;
                        font-size: 11px;
                    }
                """)
                self.scroll_area.ensureWidgetVisible(button)
            else:
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #2b2b2b;
                        border: 1px solid #3a3a3a;
                        color: #cccccc;
                        padding: 4px 8px;
                        text-align: left;
                        min-height: 16px;
                        max-height: 24px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #353535;
                        border-color: #4a4a4a;
                    }
                """)

    def _confirm_selection(self):
        """确认当前选择"""
        if self.current_index >= 0 and self.current_index < len(self.file_buttons):
            start_idx = self.current_page * self.page_size
            file_info = self.filtered_files[start_idx + self.current_index]
            self._on_file_clicked(file_info)

    def show_at_position(self, position: QPoint):
        """在指定位置显示弹窗"""
        from PySide6.QtWidgets import QApplication

        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()

        popup_size = self.sizeHint()

        # 调整X坐标
        if position.x() + popup_size.width() > screen_geometry.right():
            position.setX(screen_geometry.right() - popup_size.width())
        if position.x() < screen_geometry.left():
            position.setX(screen_geometry.left())

        # 调整Y坐标 - 默认在上方显示
        position.setY(position.y() - popup_size.height() - 10)

        # 如果上方空间不够，则显示在下方
        if position.y() < screen_geometry.top():
            position.setY(position.y() + popup_size.height() + 35)

        self.move(position)
        self.show()
