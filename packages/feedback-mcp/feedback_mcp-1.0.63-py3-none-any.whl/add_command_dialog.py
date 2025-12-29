"""
添加指令对话框组件
独立的UI组件，用于创建自定义指令文件
"""

import os
import sys
import re
from typing import Optional, Dict, Any

try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
        QTextEdit, QPushButton, QMessageBox, QFormLayout, QRadioButton, QButtonGroup, QWidget, QApplication
    )
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QFont
except ImportError:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
        QTextEdit, QPushButton, QMessageBox, QFormLayout, QRadioButton, QButtonGroup, QWidget, QApplication
    )
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QFont

# 导入路径配置模块
try:
    from path_config import get_path_config
    PATH_CONFIG_AVAILABLE = True
except ImportError:
    PATH_CONFIG_AVAILABLE = False

# 导入调试日志模块
try:
    from debug_logger import get_debug_logger
    DEBUG_LOG_AVAILABLE = True
except ImportError:
    DEBUG_LOG_AVAILABLE = False


class AddCommandDialog(QDialog):
    """添加指令对话框"""
    
    def __init__(self, project_path: str, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        # 获取路径配置实例
        if PATH_CONFIG_AVAILABLE:
            self.path_config = get_path_config()
        else:
            self.path_config = None
        
        self.setWindowTitle("添加新指令")
        self.setModal(True)
        self.resize(500, 400)
        
        self._create_ui()
        self._apply_styles()
        
        # 连接信号
        self.title_input.textChanged.connect(self._update_button_state)
        self.content_input.textChanged.connect(self._update_button_state)
        
        # 设置初始状态
        self._update_button_state()
    
    def _create_ui(self):
        """创建对话框UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 表单区域
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # 指令保存位置说明
        location_label = QLabel()
        display_path = self.path_config.get_project_commands_display_path() if self.path_config else ".claude/commands/"
        location_label.setText(f"指令将保存到: {display_path}")
        location_label.setStyleSheet("color: #888; font-style: italic;")
        form_layout.addRow("保存位置:", location_label)
        
        # 指令标题输入
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("请输入指令标题（将作为文件名）")
        self.title_input.setMinimumHeight(35)
        form_layout.addRow("指令标题:", self.title_input)
        
        layout.addLayout(form_layout)
        
        # 指令内容输入
        content_label = QLabel("指令内容:")
        content_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(content_label)
        
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("请输入指令的具体内容...\n\n例如：\n请分析用户的需求并提供解决方案\n注意事项：\n1. 分析要全面\n2. 方案要可行\n3. 考虑用户体验")
        self.content_input.setMinimumHeight(200)
        layout.addWidget(self.content_input)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.setMinimumSize(80, 35)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # 确定按钮
        self.ok_button = QPushButton("创建指令")
        self.ok_button.setMinimumSize(80, 35)
        self.ok_button.clicked.connect(self._save_command)
        self.ok_button.setDefault(True)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: white;
            }
            QLabel {
                color: white;
                font-size: 12px;
            }
            QLineEdit {
                background-color: #404040;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                color: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
            QTextEdit {
                background-color: #404040;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                color: white;
                font-size: 12px;
            }
            QTextEdit:focus {
                border-color: #2196F3;
            }
            QPushButton {
                background-color: #666666;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #777777;
            }
            QPushButton:pressed {
                background-color: #555555;
            }
            QPushButton:disabled {
                background-color: #444444;
                color: #888888;
            }
            QPushButton#create_button {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton#create_button:hover {
                background-color: #45a049;
                color: white;
            }
            QPushButton#create_button:pressed {
                background-color: #3d8b40;
                color: white;
            }
        """)
        
        # 设置创建按钮的特殊样式
        self.ok_button.setObjectName("create_button")
    
    def _update_button_state(self):
        """更新按钮状态"""
        title = self.title_input.text().strip()
        content = self.content_input.toPlainText().strip()
        
        # 只有标题和内容都不为空时才启用按钮
        self.ok_button.setEnabled(bool(title and content))
    
    def _save_command(self):
        """保存新指令"""
        title = self.title_input.text().strip()
        content = self.content_input.toPlainText().strip()
        
        # 记录开始保存
        if DEBUG_LOG_AVAILABLE:
            logger = get_debug_logger()
            logger.log(f"开始保存指令: 标题='{title}', 内容长度={len(content)}", "SAVE")
        
        # 验证输入
        if not title:
            if DEBUG_LOG_AVAILABLE:
                logger = get_debug_logger()
                logger.log_error("指令保存", "标题为空")
            QMessageBox.warning(self, "输入错误", "请输入指令标题")
            return
        
        if not content:
            if DEBUG_LOG_AVAILABLE:
                logger = get_debug_logger()
                logger.log_error("指令保存", "内容为空")
            QMessageBox.warning(self, "输入错误", "请输入指令内容")
            return
        
        # 检查文件名是否合法
        if not self._is_valid_filename(title):
            if DEBUG_LOG_AVAILABLE:
                logger = get_debug_logger()
                logger.log_error("指令保存", f"文件名非法: '{title}'")
            QMessageBox.warning(self, "文件名错误", 
                              "文件名包含非法字符，请使用字母、数字、下划线或中文")
            return
        
        try:
            # 根据选择的类型确定保存目录
            # 只支持项目指令
            if True:  # 始终保存为项目指令
                # 项目指令：使用路径配置
                if not self.path_config:
                    QMessageBox.critical(self, "配置错误", "路径配置不可用，无法保存项目指令")
                    return
                prompts_dir = self.path_config.ensure_project_commands_dir(self.project_path)
                if DEBUG_LOG_AVAILABLE:
                    logger.log(f"使用路径配置保存项目指令: {prompts_dir}", "SAVE")
                path_type = "项目"
            else:
                # 私有指令：保存到与脚本同目录的prompts/
                if self.path_config:
                    prompts_dir = self.path_config.ensure_personal_commands_dir()
                    if DEBUG_LOG_AVAILABLE:
                        logger.log(f"使用路径配置保存个人指令: {prompts_dir}", "SAVE")
                else:
                    # 降级处理
                    prompts_dir = os.path.join(self.project_path, "prompts")
                    os.makedirs(prompts_dir, exist_ok=True)
                    if DEBUG_LOG_AVAILABLE:
                        logger.log(f"使用降级路径保存个人指令: {prompts_dir}", "SAVE")
                path_type = "私有"
            
            # 生成文件路径
            filename = f"{title}.md"
            file_path = os.path.join(prompts_dir, filename)
            
            if DEBUG_LOG_AVAILABLE:
                logger = get_debug_logger()
                logger.log(f"生成文件路径: {file_path}", "SAVE")
            
            # 检查文件是否已存在
            if os.path.exists(file_path):
                if DEBUG_LOG_AVAILABLE:
                    logger.log(f"文件已存在，询问是否覆盖: {file_path}", "SAVE")
                reply = QMessageBox.question(
                    self, "文件已存在", 
                    f"指令文件 '{filename}' 已存在，是否覆盖？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    if DEBUG_LOG_AVAILABLE:
                        logger.log("用户选择不覆盖，取消保存", "SAVE")
                    return
            
            # 创建文件内容
            file_content = self._generate_file_content(content)
            if DEBUG_LOG_AVAILABLE:
                logger.log(f"生成文件内容，长度: {len(file_content)}", "SAVE")
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            # 记录保存成功
            if DEBUG_LOG_AVAILABLE:
                logger.log_save_operation(f"{path_type}指令", file_path, True)
            
            # 先关闭对话框，确保界面刷新
            if DEBUG_LOG_AVAILABLE:
                logger.log("准备关闭对话框并发出变更信号", "SAVE")
            self.accept()  # 先关闭对话框，触发刷新
            
            # 然后显示成功消息（即使失败也不影响功能）
            try:
                try:
                    relative_path = os.path.relpath(file_path)
                except ValueError:
                    relative_path = file_path
                
                QMessageBox.information(
                    self, "创建成功", 
                    f"{path_type}指令文件已创建: {filename}\n位置: {relative_path}"
                )
            except Exception as msg_error:
                if DEBUG_LOG_AVAILABLE:
                    logger.log_error("消息框显示", str(msg_error))
            
        except Exception as e:
            if DEBUG_LOG_AVAILABLE:
                logger = get_debug_logger()
                logger.log_save_operation("指令", file_path if 'file_path' in locals() else 'unknown', False, str(e))
            QMessageBox.critical(
                self, "创建失败", 
                f"创建指令文件时发生错误:\n{str(e)}"
            )
    
    def _is_valid_filename(self, filename: str) -> bool:
        """检查文件名是否合法"""
        # 禁止的字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            if char in filename:
                return False
        
        # 禁止的文件名
        invalid_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        if filename.upper() in invalid_names:
            return False
        
        # 不能为空或只有空格
        if not filename.strip():
            return False
        
        return True
    
    def _generate_file_content(self, content: str) -> str:
        """生成.md文件内容"""
        # 从内容中提取前50个字符作为描述
        description = content[:50].replace('\n', ' ').strip()
        if len(content) > 50:
            description += "..."
        
        # 生成YAML前置内容
        yaml_content = f"""---
description: {description}
globs:
alwaysApply: false
---
{content}
"""
        return yaml_content


class EditCommandDialog(QDialog):
    """编辑指令对话框"""
    
    def __init__(self, project_path: str, command_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.command_data = command_data
        self.original_file_path = command_data.get('full_path', '')
        
        # 获取路径配置实例
        if PATH_CONFIG_AVAILABLE:
            self.path_config = get_path_config()
        else:
            self.path_config = None
        
        self.setWindowTitle("编辑指令")
        self.setModal(True)
        self.resize(500, 450)
        
        self._create_ui()
        self._apply_styles()
        self._load_command_data()
        
        # 连接信号
        self.title_input.textChanged.connect(self._update_button_state)
        self.content_input.textChanged.connect(self._update_button_state)
        
        # 设置初始状态
        self._update_button_state()
    
    def _create_ui(self):
        """创建对话框UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("编辑自定义指令")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 表单区域
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # 指令类型选择（第一行）
        type_widget = QWidget()
        type_layout = QHBoxLayout(type_widget)
        type_layout.setContentsMargins(0, 0, 0, 0)
        self.type_button_group = QButtonGroup()
        
        # 项目指令选项
        self.project_radio = QRadioButton("项目指令")
        display_path = self.path_config.get_project_commands_display_path() if self.path_config else ".cursor/rules/"
        self.project_radio.setToolTip(f"保存到 {display_path} 目录，仅当前项目可用")
        self.type_button_group.addButton(self.project_radio, 0)
        type_layout.addWidget(self.project_radio)
        
        # 私有指令选项
        self.private_radio = QRadioButton("私有指令")
        self.private_radio.setToolTip("保存到 prompts/ 目录，个人全局可用")
        self.type_button_group.addButton(self.private_radio, 1)
        type_layout.addWidget(self.private_radio)
        
        type_layout.addStretch()  # 推送按钮到左侧
        form_layout.addRow("指令类型:", type_widget)
        
        # 指令标题输入
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("请输入指令标题（将作为文件名）")
        self.title_input.setMinimumHeight(35)
        form_layout.addRow("指令标题:", self.title_input)
        
        layout.addLayout(form_layout)
        
        # 指令内容输入
        content_label = QLabel("指令内容:")
        content_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(content_label)
        
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("请输入指令的具体内容...")
        self.content_input.setMinimumHeight(200)
        layout.addWidget(self.content_input)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 删除按钮已移除 - 用户需直接删除 .md 文件

        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.setMinimumSize(80, 35)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        # 保存按钮
        self.save_button = QPushButton("💾 保存修改")
        self.save_button.setMinimumSize(100, 35)
        self.save_button.clicked.connect(self._save_command)
        self.save_button.setDefault(True)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: white;
            }
            QLabel {
                color: white;
                font-size: 12px;
            }
            QLineEdit {
                background-color: #404040;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                color: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
            QTextEdit {
                background-color: #404040;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                color: white;
                font-size: 12px;
            }
            QTextEdit:focus {
                border-color: #2196F3;
            }
            QPushButton {
                background-color: #666666;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #777777;
            }
            QPushButton:pressed {
                background-color: #555555;
            }
            QPushButton:disabled {
                background-color: #444444;
                color: #888888;
            }
            QPushButton#create_button {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton#create_button:hover {
                background-color: #45a049;
                color: white;
            }
            QPushButton#create_button:pressed {
                background-color: #3d8b40;
                color: white;
            }
        """)
        
        # 设置保存按钮的特殊样式
        self.save_button.setObjectName("create_button")
    
    def _load_command_data(self):
        """加载现有指令数据"""
        try:
            # 设置标题
            title = self.command_data.get('title', '')
            # 移除.md扩展名（如果存在）
            if title.endswith('.md'):
                title = title[:-4]
            self.title_input.setText(title)
            
            # 设置指令类型（根据路径判断）
            path_type = self.command_data.get('path_type', '')
            # 始终为项目指令（已移除私有指令）
            
            # 加载文件内容
            if self.original_file_path and os.path.exists(self.original_file_path):
                with open(self.original_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 解析YAML前置内容
                if content.startswith('---'):
                    # 找到第二个---的位置
                    end_yaml = content.find('---', 3)
                    if end_yaml != -1:
                        # 提取实际内容（去掉YAML前置部分）
                        actual_content = content[end_yaml + 3:].strip()
                        self.content_input.setPlainText(actual_content)
                    else:
                        # 如果格式不正确，显示整个文件内容
                        self.content_input.setPlainText(content)
                else:
                    # 如果没有YAML前置，显示整个文件内容
                    self.content_input.setPlainText(content)
            
        except Exception as e:
            QMessageBox.warning(
                self, "加载失败", 
                f"加载指令文件时发生错误:\n{str(e)}"
            )
    
    def _update_button_state(self):
        """更新按钮状态"""
        title = self.title_input.text().strip()
        content = self.content_input.toPlainText().strip()
        
        # 只有标题和内容都不为空时才启用保存按钮
        self.save_button.setEnabled(bool(title and content))
    
    def _save_command(self):
        """保存指令修改"""
        title = self.title_input.text().strip()
        content = self.content_input.toPlainText().strip()
        
        # 验证输入
        if not title:
            QMessageBox.warning(self, "输入错误", "请输入指令标题")
            return
        
        if not content:
            QMessageBox.warning(self, "输入错误", "请输入指令内容")
            return
        
        # 检查文件名是否合法
        if not self._is_valid_filename(title):
            QMessageBox.warning(self, "文件名错误", 
                              "文件名包含非法字符，请使用字母、数字、下划线或中文")
            return
        
        try:
            # 根据选择的类型确定保存目录
            if self.project_radio.isChecked():
                # 项目指令：使用路径配置
                if not self.path_config:
                    QMessageBox.critical(self, "配置错误", "路径配置不可用，无法保存项目指令")
                    return
                prompts_dir = self.path_config.ensure_project_commands_dir(self.project_path)
                path_type = "项目"
            else:
                # 私有指令：保存到与脚本同目录的prompts/
                if self.path_config:
                    prompts_dir = self.path_config.ensure_personal_commands_dir()
                else:
                    # 降级处理
                    prompts_dir = os.path.join(self.project_path, "prompts")
                    os.makedirs(prompts_dir, exist_ok=True)
                path_type = "私有"
            
            # 生成新的文件路径
            filename = f"{title}.md"
            new_file_path = os.path.join(prompts_dir, filename)
            
            # 如果文件路径或名称改变了，需要处理原文件
            if new_file_path != self.original_file_path:
                # 检查新文件是否已存在
                if os.path.exists(new_file_path):
                    reply = QMessageBox.question(
                        self, "文件已存在", 
                        f"指令文件 '{filename}' 已存在，是否覆盖？",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return
                
                # 删除原文件（如果存在且不同于新文件）
                if os.path.exists(self.original_file_path):
                    os.remove(self.original_file_path)
            
            # 创建文件内容
            file_content = self._generate_file_content(content)
            
            # 写入文件
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            # 显示成功消息
            relative_path = os.path.relpath(new_file_path, os.getcwd()) if self.project_path else new_file_path
            QMessageBox.information(
                self, "保存成功", 
                f"{path_type}指令文件已保存: {filename}\n位置: {relative_path}"
            )
            
            # 关闭对话框
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self, "保存失败", 
                f"保存指令文件时发生错误:\n{str(e)}"
            )
    
    # 删除指令方法已移除 - 用户需直接删除 .md 文件

    def _is_valid_filename(self, filename: str) -> bool:
        """检查文件名是否合法"""
        # 禁止的字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            if char in filename:
                return False
        
        # 禁止的文件名
        invalid_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        if filename.upper() in invalid_names:
            return False
        
        # 不能为空或只有空格
        if not filename.strip():
            return False
        
        return True
    
    def _generate_file_content(self, content: str) -> str:
        """生成.md文件内容"""
        # 从内容中提取前50个字符作为描述
        description = content[:50].replace('\n', ' ').strip()
        if len(content) > 50:
            description += "..."
        
        # 生成YAML前置内容
        yaml_content = f"""---
description: {description}
globs:
alwaysApply: false
---
{content}
"""
        return yaml_content 