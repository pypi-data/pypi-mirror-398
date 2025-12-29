"""
指令弹窗组件 - 当用户在输入框中输入"/"时显示可用指令列表
"""

from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QListWidget, QListWidgetItem, 
    QLabel, QApplication, QScrollArea, QWidget, QGridLayout, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal, QPoint, QTimer
from PySide6.QtGui import QKeyEvent, QFont



class CommandPopup(QFrame):
    """指令弹窗组件"""
    
    # 信号定义
    command_selected = Signal(str, dict)  # 选中指令内容, 完整指令数据
    popup_closed = Signal()        # 弹窗关闭
    add_command_requested = Signal(str, str)  # 请求添加指令，参数：project_path, command_type
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.commands = []  # 存储指令数据
        self.filtered_commands = []  # 过滤后的指令
        self.filter_text = ""  # 过滤文本
        
        # 导航相关属性
        self.current_index = -1  # 当前选中的按钮索引
        self.command_buttons = []  # 存储指令按钮
        
        # 存储项目路径和指令类型，用于添加指令
        self.project_path = ""
        self.command_type = ""
        
        self._setup_ui()
        self._setup_style()
        
        # 设置窗口属性 - 使用 Tool 而不是 Popup，避免抢夺焦点
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # 显示时不激活窗口
        # 不设置 WA_DeleteOnClose，我们手动管理对象生命周期
        
    def set_project_path(self, project_path: str):
        """设置项目路径"""
        self.project_path = project_path
        
    def set_command_type(self, command_type: str):
        """设置指令类型"""
        self.command_type = command_type
        # 更新添加按钮的可见性
        if hasattr(self, 'add_button'):
            # 系统指令不显示添加按钮（不可编辑）
            self.add_button.setVisible(command_type in ['project', 'personal'])
        
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        
        # 标题区域 - 包含标题和添加按钮
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(8, 4, 8, 4)
        title_layout.setSpacing(8)
        
        # 标题标签（左对齐）
        self.title_label = QLabel("📝 选择指令")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.title_label.setFont(font)
        title_layout.addWidget(self.title_label)

        # 添加指令按钮已移除
        # 用户需要直接编辑 .md 文件来管理指令

        layout.addWidget(title_widget)
        
        # 指令网格容器
        self.scroll_area = QScrollArea()
        self.scroll_area.setMaximumHeight(400)  # 减小最大高度
        self.scroll_area.setMinimumHeight(150)  # 减小最小高度
        self.scroll_area.setMinimumWidth(300)   # 减小宽度从400到300
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 网格容器widget
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(4)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        
        self.scroll_area.setWidget(self.grid_widget)
        layout.addWidget(self.scroll_area)
        
        # 提示标签
        self.hint_label = QLabel("↑↓ 方向键选择 | 1-9 数字快速选择 | Enter 确认 | Esc 取消")
        self.hint_label.setAlignment(Qt.AlignCenter)
        hint_font = QFont()
        hint_font.setPointSize(8)
        self.hint_label.setFont(hint_font)
        layout.addWidget(self.hint_label)

    # 添加指令方法已移除
    # 用户需要直接编辑 .md 文件来管理指令

    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            CommandPopup {
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
                padding: 4px 8px;  /* 减小内边距从8px 12px */
                text-align: left;
                min-height: 16px;  /* 减小最小高度从20px */
                max-height: 24px;  /* 设置最大高度 */
                font-size: 11px;   /* 减小字体从12px */
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
            /* 添加指令小图标按钮样式 */
            QPushButton#add_command_icon_button {
                background-color: #4CAF50;
                border: 1px solid #4CAF50;
                border-radius: 12px;  /* 圆形按钮 24px/2 = 12px */
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 0px;
                text-align: center;
                min-height: 22px;
                max-height: 22px;
                min-width: 22px;
                max-width: 22px;
            }
            QPushButton#add_command_icon_button:hover {
                background-color: #45a049;
                border-color: #45a049;
            }
            QPushButton#add_command_icon_button:pressed {
                background-color: #3d8b40;
                border-color: #3d8b40;
            }
        """)
    
    def set_commands(self, commands: List[Dict[str, Any]]):
        """设置指令列表"""
        self.commands = commands
        self._update_filtered_commands()
    
    def set_filter(self, filter_text: str):
        """设置过滤文本"""
        self.filter_text = filter_text.lower()
        self._update_filtered_commands()
    
    def _update_filtered_commands(self):
        """更新过滤后的指令列表"""
        # 过滤指令
        if self.filter_text:
            self.filtered_commands = [
                cmd for cmd in self.commands
                if (self.filter_text in cmd.get('title', '').lower() or 
                    self.filter_text in cmd.get('content', '').lower())
            ]
        else:
            self.filtered_commands = self.commands.copy()
        
        # 更新UI
        self._update_list_widget()
    
    def _update_list_widget(self):
        """更新网格布局 - 支持分类显示"""
        # 清空现有按钮
        for button in self.command_buttons:
            button.deleteLater()
        self.command_buttons.clear()
        
        # 清空布局
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not self.filtered_commands:
            # 显示空状态
            empty_label = QLabel("😔 没有找到匹配的指令")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #888888; padding: 20px;")
            self.grid_layout.addWidget(empty_label, 0, 0, 1, 2)
            return
        
        # 按类别分组指令
        categories = {}
        for cmd in self.filtered_commands:
            category = cmd.get('category', None)  # 允许 None,不设置默认值
            if category not in categories:
                categories[category] = []
            categories[category].append(cmd)

        # 显示所有指令（按分类）
        row = 0
        button_index = 0

        for category, commands in categories.items():
            # 只有存在有效 category 时才显示分类标题
            if category:  # None 或空字符串时跳过标题
                category_label = QLabel(category)
                category_label.setStyleSheet("""
                    QLabel {
                        color: #4CAF50;
                        font-weight: bold;
                        padding: 4px 0px;
                        font-size: 11px;
                    }
                """)
                self.grid_layout.addWidget(category_label, row, 0, 1, 2)
                row += 1
            
            # 添加该分类下的指令按钮
            for i, command in enumerate(commands):
                title = command.get('title', '未命名指令')
                
                # 使用数字序号，更直观
                sequence_num = button_index + 1
                display_text = f"{sequence_num}. {title}"
                
                button = QPushButton(display_text)
                button.setToolTip(command.get('content', ''))
                button.clicked.connect(lambda checked, cmd=command, idx=button_index: self._on_button_clicked(cmd, idx))
                
                # 设置按钮属性用于键盘导航
                button.setProperty('button_index', button_index)
                
                # 单列布局 - 所有按钮都在第0列，跨两列显示
                self.grid_layout.addWidget(button, row, 0, 1, 2)  # row, col, rowspan, colspan
                self.command_buttons.append(button)
                button_index += 1
                row += 1
        
    def _on_button_clicked(self, command: Dict[str, Any], index: int):
        """处理按钮点击"""
        # 日志记录已移除
        self._select_command(command)
    
    def _select_command(self, command: Dict[str, Any]):
        """选择指令"""
        content = command.get('content', '')
        # 日志记录已移除
        if content:
            # 发出信号时同时传递内容和完整的指令数据
            self.command_selected.emit(content, command)
        self.close()
    
    def keyPressEvent(self, event: QKeyEvent):
        """处理键盘事件 - 支持方向键和数字键"""
        if event.key() == Qt.Key_Escape:
            # ESC键关闭弹窗
            self.popup_closed.emit()
            self.close()
            
        elif event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            # 方向键导航
            self._handle_arrow_navigation(event.key())
            event.accept()
            
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Enter键确认选择
            self._confirm_selection()
            event.accept()
            
        elif event.text().isdigit():
            # 数字键快速选择（1-9）
            num = int(event.text())
            if num > 0 and num <= len(self.filtered_commands):
                command = self.filtered_commands[num - 1]
                self._select_command(command)
            event.accept()
            
        else:
            super().keyPressEvent(event)
    
    def show_at_position(self, position: QPoint):
        """在指定位置显示弹窗"""
        # 调整位置确保弹窗完全可见
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        popup_size = self.sizeHint()
        
        # 调整X坐标
        if position.x() + popup_size.width() > screen_geometry.right():
            position.setX(screen_geometry.right() - popup_size.width())
        if position.x() < screen_geometry.left():
            position.setX(screen_geometry.left())
            
        # 调整Y坐标 - 默认在对话框上方显示
        position.setY(position.y() - popup_size.height() - 10)  # 显示在上方，留10px间距
        
        # 如果上方空间不够，则显示在下方
        if position.y() < screen_geometry.top():
            position.setY(position.y() + popup_size.height() + 35)  # 显示在下方
        
        self.move(position)
        self.show()
        # 不获取焦点，让输入框保持焦点
        # self.setFocus()
    
    def _handle_arrow_navigation(self, key):
        """处理方向键导航"""
        if not self.command_buttons:
            return
            
        # 初始化或更新当前索引
        if self.current_index == -1:
            self.current_index = 0
        else:
            if key == Qt.Key_Up:
                # 向上移动（单列布局）
                if self.current_index > 0:
                    self.current_index -= 1
            elif key == Qt.Key_Down:
                # 向下移动（单列布局）
                if self.current_index < len(self.command_buttons) - 1:
                    self.current_index += 1
            # 单列布局不需要左右导航
        
        # 更新按钮焦点和样式
        self._update_button_focus()
    
    def _update_button_focus(self):
        """更新按钮焦点状态"""
        for i, button in enumerate(self.command_buttons):
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
                # 确保选中的按钮在可视区域内
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
        if self.current_index >= 0 and self.current_index < len(self.filtered_commands):
            command = self.filtered_commands[self.current_index]
            self._select_command(command)
    
