"""
指令管理模块
包含指令的增删改查、UI组件等所有相关功能
"""

import os
import sys
import json
from typing import Optional, List, Dict, Any

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QScrollArea,
        QGridLayout, QRadioButton, QButtonGroup, QPushButton, QFrame,
        QLabel, QSizePolicy, QDialog
    )
    from PySide6.QtCore import Qt, Signal
except ImportError:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QScrollArea,
        QGridLayout, QRadioButton, QButtonGroup, QPushButton, QFrame,
        QLabel, QSizePolicy, QDialog
    )
    from PyQt5.QtCore import Qt, pyqtSignal as Signal

# 导入指令对话框
try:
    import add_command_dialog
    AddCommandDialog = add_command_dialog.AddCommandDialog
    EditCommandDialog = add_command_dialog.EditCommandDialog
except ImportError:
    try:
        from add_command_dialog import AddCommandDialog, EditCommandDialog
    except ImportError:
        print("Warning: 无法导入命令对话框组件")
        AddCommandDialog = None
        EditCommandDialog = None

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


class CommandManager:
    """指令数据管理类"""

    def __init__(self, project_path: str):
        self.project_path = project_path
        # 获取路径配置实例
        if PATH_CONFIG_AVAILABLE:
            self.path_config = get_path_config()
        else:
            self.path_config = None
        # 命令缓存
        self._cache = {}
        self._cache_enabled = False
    
    def enable_cache(self):
        """启用缓存模式"""
        self._cache_enabled = True
        self._cache.clear()

    def disable_cache(self):
        """禁用缓存模式"""
        self._cache_enabled = False
        self._cache.clear()

    def load_project_commands(self) -> List[Dict[str, Any]]:
        """加载项目指令（.cursor/rules/目录）"""
        if self._cache_enabled and 'project' in self._cache:
            return self._cache['project']

        commands = []
        if not self.project_path:
            return commands

        if self.path_config:
            prompts_dir = self.path_config.get_project_commands_dir(self.project_path)
            if prompts_dir:
                commands = self._load_commands_from_dir(prompts_dir, "项目")

        if self._cache_enabled:
            self._cache['project'] = commands
        return commands
    
    def load_personal_commands(self) -> List[Dict[str, Any]]:
        """个人指令已移除，返回空列表"""
        return []

    def load_plugin_commands(self) -> List[Dict[str, Any]]:
        """加载插件指令（从已启用插件的commands目录）"""
        if self._cache_enabled and 'plugin' in self._cache:
            return self._cache['plugin']

        commands = []

        if not self.path_config:
            return commands

        try:
            # 1. 读取 installed_plugins.json
            plugins_config_path = self.path_config.get_plugins_config_path()
            if not os.path.exists(plugins_config_path):
                if DEBUG_LOG_AVAILABLE:
                    logger = get_debug_logger()
                    logger.log("插件配置文件不存在", "WARN")
                return commands

            with open(plugins_config_path, 'r', encoding='utf-8') as f:
                plugins_data = json.load(f)

            installed_plugins = plugins_data.get('plugins', {})

            # 2. 读取 settings.json 获取启用状态
            settings_path = self.path_config.get_settings_path()
            enabled_plugins = {}
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
                enabled_plugins = settings_data.get('enabledPlugins', {})

            # 3. 遍历已启用的插件
            for plugin_id, plugin_info in installed_plugins.items():
                # 只加载已启用的插件
                if not enabled_plugins.get(plugin_id, False):
                    continue

                # plugin_info 可能是数组（新格式）或对象（旧格式）
                if isinstance(plugin_info, list) and len(plugin_info) > 0:
                    install_path = plugin_info[0].get('installPath')
                else:
                    install_path = plugin_info.get('installPath')
                if not install_path or not os.path.exists(install_path):
                    if DEBUG_LOG_AVAILABLE:
                        logger = get_debug_logger()
                        logger.log(f"插件路径不存在: {plugin_id}", "WARN")
                    continue

                # 4. 扫描插件的 commands/ 目录
                commands_dir = os.path.join(install_path, 'commands')
                if not os.path.exists(commands_dir):
                    continue

                # 5. 复用 _load_commands_from_dir 方法
                plugin_commands = self._load_commands_from_dir(commands_dir, "插件")

                # 6. 为每个指令添加插件标识
                plugin_name = plugin_id.split('@')[0] if '@' in plugin_id else plugin_id
                for cmd in plugin_commands:
                    cmd['plugin_id'] = plugin_id
                    cmd['plugin_name'] = plugin_name
                    # 修改 title 格式：title@plugin_name
                    original_title = cmd['title']
                    cmd['title'] = f"{original_title}@{plugin_name}"

                commands.extend(plugin_commands)

        except json.JSONDecodeError as e:
            sys.stderr.write(f"Error parsing plugin config JSON: {e}\n")
        except Exception as e:
            sys.stderr.write(f"Error loading plugin commands: {e}\n")

        if self._cache_enabled:
            self._cache['plugin'] = commands
        return commands

    def _load_commands_from_dir(self, prompts_dir: str, path_type: str) -> List[Dict[str, Any]]:
        """从指定目录加载指令（支持递归读取子目录）"""
        commands = []

        if DEBUG_LOG_AVAILABLE:
            logger = get_debug_logger()
            logger.log(f"_load_commands_from_dir: 目录={prompts_dir}, 类型={path_type}", "LOAD")

        if not os.path.exists(prompts_dir):
            if DEBUG_LOG_AVAILABLE:
                logger = get_debug_logger()
                logger.log_error("目录扫描", f"目录不存在: {prompts_dir}")
            return commands

        # 递归函数来读取目录和子目录
        def scan_directory(dir_path: str, relative_path: str = "") -> None:
            try:
                entries = os.listdir(dir_path)

                if DEBUG_LOG_AVAILABLE and dir_path == prompts_dir:
                    logger = get_debug_logger()
                    md_files = [f for f in entries if f.endswith('.md')]
                    logger.log_dir_scan(dir_path, entries, md_files)

                for entry in entries:
                    entry_path = os.path.join(dir_path, entry)

                    if os.path.isdir(entry_path):
                        # 递归读取子目录
                        new_relative = os.path.join(relative_path, entry) if relative_path else entry
                        scan_directory(entry_path, new_relative)
                    elif entry.endswith('.md'):
                        try:
                            with open(entry_path, 'r', encoding='utf-8') as f:
                                content = f.read().strip()

                            if not content:
                                continue

                            # 生成标题：使用冒号分隔的格式
                            file_title = entry.replace('.md', '')
                            if relative_path:
                                # 将路径分隔符替换为冒号
                                path_parts = relative_path.replace(os.sep, ':')
                                title = f"{path_parts}:{file_title}"
                            else:
                                title = file_title

                            description = ""
                            main_content = content
                            globs = ""
                            always_apply = False
                            argument_hint = ""  # 新增：参数提示字段

                            if content.startswith('---'):
                                # 分离frontmatter和内容
                                parts = content.split('---', 2)
                                if len(parts) >= 3:
                                    frontmatter = parts[1].strip()
                                    main_content = parts[2].strip()

                                    # 解析frontmatter中的各个字段
                                    for line in frontmatter.split('\n'):
                                        line = line.strip()
                                        if line.startswith('title:'):
                                            extracted_title = line.split('title:', 1)[1].strip()
                                            if extracted_title:  # 如果frontmatter中有title，使用它但保留路径前缀
                                                if relative_path:
                                                    path_parts = relative_path.replace(os.sep, ':')
                                                    title = f"{path_parts}:{extracted_title}"
                                                else:
                                                    title = extracted_title
                                        elif line.startswith('description:'):
                                            description = line.split('description:', 1)[1].strip()
                                        elif line.startswith('argument-hint:'):
                                            argument_hint = line.split('argument-hint:', 1)[1].strip()
                                        elif line.startswith('globs:'):
                                            globs = line.split('globs:', 1)[1].strip()
                                        elif line.startswith('alwaysApply:'):
                                            always_apply_str = line.split('alwaysApply:', 1)[1].strip().lower()
                                            always_apply = always_apply_str in ('true', 'yes', '1')
                            else:
                                # 没有frontmatter的文件，使用文件名作为描述，内容作为主体
                                description = f"来自文件: {os.path.join(relative_path, entry) if relative_path else entry}"

                            # 只有当有实际内容时才添加指令
                            if main_content:
                                commands.append({
                                    'title': title,
                                    'content': main_content,
                                    'description': description,
                                    'filename': entry,
                                    'path_type': path_type,
                                    'full_path': entry_path,
                                    'globs': globs,
                                    'always_apply': always_apply,
                                    'argument_hint': argument_hint,  # 新增：参数提示
                                    'relative_path': relative_path  # 添加相对路径信息
                                })
                        except Exception as e:
                            # Error loading file - log to stderr instead of stdout
                            sys.stderr.write(f"Error loading {entry} from {path_type}: {e}\n")
            except Exception as e:
                sys.stderr.write(f"Error scanning directory {dir_path}: {e}\n")

        # 开始递归扫描
        try:
            scan_directory(prompts_dir)
        except Exception as e:
            # Error reading directory - log to stderr instead of stdout  
            sys.stderr.write(f"Error reading {path_type} prompts directory: {e}\n")
        
        return commands


class CommandTabWidget(QTabWidget):
    """指令选项卡组件"""
    command_executed = Signal(str)  # 指令执行信号
    
    def __init__(self, project_path: str, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.command_manager = CommandManager(project_path)
        
        # 设置大小策略：优先按内容大小，但允许收缩
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        # 限制TabWidget的最大高度为200px，但允许按内容自适应
        self.setMaximumHeight(200)
        
        self._create_tabs()
        self._setup_tab_change_handler()
        # 设置初始按钮显示
        self._on_tab_changed(0)
        # 确保按钮容器正确初始化
        self._ensure_button_container_initialized()
    
    def _create_tabs(self):
        """创建项目指令和个人指令选项卡"""
        # 项目指令选项卡
        self.project_tab = ProjectCommandTab(self.project_path, self.command_manager, self)
        self.project_tab.command_executed.connect(self.command_executed.emit)
        self.project_tab.commands_changed.connect(self._on_commands_changed)
        self.addTab(self.project_tab, "🏢 项目指令")

        # 个人指令选项卡
        self.personal_tab = PersonalCommandTab(self.project_path, self.command_manager, self)
        self.personal_tab.command_executed.connect(self.command_executed.emit)
        self.personal_tab.commands_changed.connect(self._on_commands_changed)
        self.addTab(self.personal_tab, "👤 个人指令")

    
    def _setup_tab_change_handler(self):
        """设置选项卡切换处理"""
        self.currentChanged.connect(self._on_tab_changed)
    
    def _on_tab_changed(self, index):
        """选项卡切换时更新按钮"""
        print(f"🔄 选项卡切换到索引: {index}")
        
        # 获取当前选项卡
        current_tab = self.widget(index)
        if current_tab and hasattr(current_tab, 'get_button_container'):
            button_container = current_tab.get_button_container()
            if button_container:
                # 确保按钮容器可见
                button_container.setVisible(True)
                self.setCornerWidget(button_container, Qt.TopRightCorner)
                print(f"✅ 设置按钮容器成功，选项卡: {self.tabText(index)}")
            else:
                print(f"⚠️  当前选项卡 '{self.tabText(index)}' 没有按钮容器，保持现有按钮")
                # 如果当前选项卡没有按钮容器，不要清空现有的cornerWidget
                # 这样可以保持之前有按钮的选项卡的按钮仍然可见
        else:
            print(f"❌ 选项卡 '{self.tabText(index)}' 没有get_button_container方法")
    
    def _on_commands_changed(self):
        """指令变化时的处理"""
        # 刷新所有选项卡的数据
        self.project_tab.refresh_commands()
        self.personal_tab.refresh_commands()

    def refresh_all_commands(self):
        """刷新所有指令"""
        self.project_tab.refresh_commands()
        self.personal_tab.refresh_commands()
    
    def _ensure_button_container_initialized(self):
        """确保按钮容器正确初始化"""
        # 强制设置第一个有按钮容器的选项卡的按钮
        for i in range(self.count()):
            tab = self.widget(i)
            if tab and hasattr(tab, 'get_button_container'):
                button_container = tab.get_button_container()
                if button_container:
                    button_container.setVisible(True)
                    self.setCornerWidget(button_container, Qt.TopRightCorner)
                    print(f"✅ 初始化按钮容器成功，选项卡索引: {i}")
                    break


class BaseCommandTab(QWidget):
    """指令选项卡基类"""
    command_executed = Signal(str)  # 指令执行信号
    commands_changed = Signal()     # 指令变化信号
    
    def __init__(self, project_path: str, command_manager: CommandManager, command_type: str, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.command_manager = command_manager
        self.command_type = command_type  # "项目" 或 "个人"
        self.commands = []
        self.command_button_group = QButtonGroup()
        self.command_button_group.setExclusive(False)  # Allow deselection
        self.command_radios = []
        self.button_container = None
        
        self._create_ui()
        self._create_button_container()
        self.refresh_commands()
    
    def _create_ui(self):
        """创建UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 创建主内容区域
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(5)
        
        layout.addWidget(self.content_widget)
    
    def _create_button_container(self):
        """创建按钮容器 - 已禁用所有管理按钮"""
        # 不再创建添加、编辑按钮,用户需直接编辑 .md 文件来管理指令
        self.button_container = None
    
    def get_button_container(self):
        """获取按钮容器 - 已禁用"""
        return None  # 不再提供按钮容器
    
    def _load_commands(self) -> List[Dict[str, Any]]:
        """加载指令（子类实现）"""
        raise NotImplementedError
    
    def _get_default_command_type_for_dialog(self) -> str:
        """获取对话框的默认指令类型（子类实现）"""
        raise NotImplementedError
    
    def refresh_commands(self):
        """刷新指令列表"""
        # 清除旧的UI组件
        for i in reversed(range(self.content_layout.count())):
            child = self.content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # 清除按钮组
        self.command_radios.clear()
        
        # 重新加载指令
        self.commands = self._load_commands()

        # 编辑按钮已移除,不再更新状态
        
        if self.commands:
            self._create_command_list()
        else:
            self._create_empty_state()
    
    def _create_command_list(self):
        """创建指令列表"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        commands_widget = QWidget()
        commands_layout = QGridLayout(commands_widget)
        commands_layout.setContentsMargins(5, 5, 5, 5)
        commands_layout.setSpacing(5)
        
        # 计算网格布局
        total_commands = len(self.commands)
        columns = 2  # 两列布局
        
        for i, command in enumerate(self.commands):
            row = i // columns
            col = i % columns
            
            # Create frame for each command item
            command_frame = QFrame()
            command_item_layout = QHBoxLayout(command_frame)
            command_item_layout.setContentsMargins(5, 2, 5, 2)
            
            # Radio button
            radio = QRadioButton(command['title'])
            radio.setProperty('command_index', i)
            radio.clicked.connect(lambda checked, r=radio: self._handle_radio_click(r))
            # 设置选中效果样式，与插件指令保持一致
            radio.setStyleSheet("""
                QRadioButton {
                    padding: 4px 8px;
                    border-radius: 3px;
                }
                QRadioButton:checked {
                    background-color: rgba(0, 120, 212, 0.15);
                }
                QRadioButton:hover {
                    background-color: rgba(0, 120, 212, 0.08);
                }
                QRadioButton::indicator {
                    width: 14px;
                    height: 14px;
                    border-radius: 7px;
                    border: 2px solid #666666;
                }
                QRadioButton::indicator:checked {
                    background-color: #0078d4;
                    border-color: #0078d4;
                }
                QRadioButton::indicator:hover {
                    border-color: #0078d4;
                }
            """)
            self.command_button_group.addButton(radio)
            self.command_radios.append(radio)
            
            # Button container
            button_layout = QHBoxLayout()
            button_layout.setSpacing(10)
            
            # Execute button
            execute_btn = QPushButton("▶️")
            execute_btn.setMaximumSize(30, 30)
            execute_btn.setProperty('command_index', i)
            execute_btn.clicked.connect(lambda checked, idx=i: self._execute_command(idx))
            execute_btn.setToolTip("立即执行")
            execute_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: rgba(76, 175, 80, 0.1);
                    border-radius: 3px;
                }
                QPushButton:pressed {
                    background-color: rgba(76, 175, 80, 0.2);
                    border-radius: 3px;
                }
            """)
            button_layout.addWidget(execute_btn)
            
            # Add to frame layout
            command_item_layout.addWidget(radio)
            command_item_layout.addStretch()
            command_item_layout.addLayout(button_layout)
            
            # Add frame to grid layout
            commands_layout.addWidget(command_frame, row, col)
        
        commands_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        scroll_area.setWidget(commands_widget)
        self.content_layout.addWidget(scroll_area)
    
    def _create_empty_state(self):
        """创建空状态提示"""
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setContentsMargins(20, 20, 20, 20)
        
        empty_layout.addStretch()
        
        # 主提示标签
        empty_label = QLabel(f"💡 暂无{self.command_type}指令")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #666666;
                margin-bottom: 10px;
            }
        """)
        empty_layout.addWidget(empty_label)
        
        # 操作提示标签
        help_label = QLabel("点击右上角 ➕ 按钮添加您的第一个指令")
        help_label.setAlignment(Qt.AlignCenter)
        help_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #888888;
                margin-top: 5px;
            }
        """)
        empty_layout.addWidget(help_label)
        
        empty_layout.addStretch()
        
        self.content_layout.addWidget(empty_widget)
    
    def _handle_radio_click(self, radio_button):
        """处理radio按钮点击"""
        if radio_button.isChecked():
            # 取消其他radio的选中状态
            for other_radio in self.command_radios:
                if other_radio != radio_button and other_radio.isChecked():
                    other_radio.setChecked(False)

        # 编辑按钮已移除,不再更新状态
    
    def _execute_command(self, command_index: int):
        """执行指令"""
        if 0 <= command_index < len(self.commands):
            command_content = self.commands[command_index]['content']
            if command_content:
                self.command_executed.emit(command_content)
    
    # 添加/编辑指令方法已移除
    # 用户需要直接编辑 .md 文件来管理指令


class ProjectCommandTab(BaseCommandTab):
    """项目指令选项卡"""
    
    def __init__(self, project_path: str, command_manager: CommandManager, parent=None):
        super().__init__(project_path, command_manager, "项目", parent)
    
    def _load_commands(self) -> List[Dict[str, Any]]:
        """加载项目指令"""
        return self.command_manager.load_project_commands()
    
    def _get_default_command_type_for_dialog(self) -> str:
        """获取对话框的默认指令类型"""
        return "project"
    



class PersonalCommandTab(BaseCommandTab):
    """个人指令选项卡"""
    
    def __init__(self, project_path: str, command_manager: CommandManager, parent=None):
        super().__init__(project_path, command_manager, "个人", parent)
    
    def _load_commands(self) -> List[Dict[str, Any]]:
        """加载个人指令"""
        return self.command_manager.load_personal_commands()
    
    def _get_default_command_type_for_dialog(self) -> str:
        """获取对话框的默认指令类型"""
        return "private"
 