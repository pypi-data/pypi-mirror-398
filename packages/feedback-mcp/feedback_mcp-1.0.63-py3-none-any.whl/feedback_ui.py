"""
重构后的反馈UI - 使用模块化架构
"""
import os
import sys
import json
import argparse
import base64
# 移除不必要的导入
# import markdown - 未使用
# import requests - 未使用  
# import yaml - 未使用
# import glob - 未使用
# from io import BytesIO - 未使用
# from datetime import datetime, timedelta - 未使用
# from pathlib import Path - 未使用
from typing import Optional, TypedDict, List, Dict

# 导入窗口位置管理器
try:
    from window_position_manager import WindowPositionManager
except ImportError:
    WindowPositionManager = None

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QTabWidget, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QSettings, Signal, QThread
from PySide6.QtGui import QPalette, QColor, QGuiApplication

# 导入统一日志系统
from debug_logger import get_debug_logger
from session_manager import SessionManager

# 导入IDE工具
try:
    from ide_utils import focus_cursor_to_project, is_macos
except ImportError:
    # 如果导入失败，设置默认函数
    def focus_cursor_to_project(project_path: str) -> bool:
        return False
    def is_macos() -> bool:
        return False

# 导入模块化组件 - 修复PyArmor加密环境下的导入问题
import sys
import os

# 确保当前目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # 只导入必要的ChatTab、WorkspaceTab和ChatHistoryTab
    from tabs import ChatTab, WorkspaceTab, ChatHistoryTab
except ImportError as e:
    # 如果导入失败，设置为None
    ChatTab = None
    WorkspaceTab = None
    ChatHistoryTab = None





class FeedbackResult(TypedDict):
    content: List[Dict[str, str]]  # 结构化内容数组，每个元素包含type和text
    images: Optional[List[str]]  # Base64 encoded images

class VersionCheckThread(QThread):
    """版本检查线程 - 在独立线程中执行网络请求"""

    # 定义信号：参数为(latest_version, current_version)
    version_checked = Signal(str, str)

    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self.current_version = current_version
        self._stop_requested = False

    def request_stop(self):
        """请求停止线程"""
        self._stop_requested = True

    def run(self):
        """在独立线程中执行版本检查"""
        try:
            if self._stop_requested:
                return
            import requests
            resp = requests.get('https://pypi.org/pypi/feedback-mcp/json', timeout=5)
            if self._stop_requested:
                return
            if resp.status_code == 200:
                latest = resp.json()['info']['version']
                # 发送信号到主线程
                self.version_checked.emit(latest, self.current_version)
        except Exception:
            # 静默处理错误，不发送信号
            pass


def get_dark_mode_palette(app: QApplication):
    darkPalette = app.palette()
    darkPalette.setColor(QPalette.Window, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.WindowText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.Base, QColor(42, 42, 42))
    darkPalette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
    darkPalette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.ToolTipText, Qt.white)
    darkPalette.setColor(QPalette.Text, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.Dark, QColor(35, 35, 35))
    darkPalette.setColor(QPalette.Shadow, QColor(20, 20, 20))
    darkPalette.setColor(QPalette.Button, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.ButtonText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.BrightText, Qt.red)
    darkPalette.setColor(QPalette.Link, QColor(42, 130, 218))
    darkPalette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    darkPalette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
    darkPalette.setColor(QPalette.HighlightedText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.PlaceholderText, QColor(127, 127, 127))
    return darkPalette


class FeedbackUI(QMainWindow):
    """重构后的反馈UI主界面"""
    
    def __init__(self, prompt: str, predefined_options: Optional[List[str]] = None, project_path: Optional[str] = None, work_title: Optional[str] = None, timeout: int = 60, skip_auth_check: bool = False, skip_init_check: bool = False, session_id: Optional[str] = None, workspace_id: Optional[str] = None, files: Optional[List[str]] = None, bugdetail: Optional[str] = None, ide: Optional[str] = None):
        super().__init__()

        # 基本参数
        self.prompt = prompt
        self.predefined_options = predefined_options or []
        self.project_path = project_path
        self.work_title = work_title or ""
        self.timeout = timeout
        self.skip_init_check = skip_init_check
        self.elapsed_time = 0
        self.session_id = session_id  # 保存会话ID
        self.workspace_id = workspace_id  # 保存工作空间ID
        self.files = files or []  # 保存文件列表
        self.bugdetail = bugdetail  # 保存bug详情
        self.ide = ide  # 保存指定的IDE

        # 如果传入了IDE参数，设置环境变量以便其他模块使用
        if ide:
            os.environ['IDE'] = ide
            try:
                logger = get_debug_logger()
                logger.info(f"设置IDE环境变量: {ide}")
            except:
                pass  # 忽略日志错误

        # 展示feedback时，重置stop hook状态
        if self.session_id:
            try:
                manager = SessionManager(session_id=self.session_id, project_path=self.project_path)
                manager.reset_on_feedback_show(self.session_id)
            except Exception as e:
                try:
                    logger = get_debug_logger()
                    logger.log_warning(f"Failed to reset stop hook state: {e}", "UI")
                except:
                    pass  # 忽略日志错误

        # 结果存储
        self.feedback_result = None
        self.is_temp_close = False  # 临时关闭标记（精简版按钮）

        # 定时器
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self._update_countdown)
        self.countdown_timer.setSingleShot(False)  # 确保定时器可以重复触发
        
        # 双击ESC关闭的计时器
        self.esc_timer = QTimer()
        self.esc_timer.setSingleShot(True)
        self.esc_timer.timeout.connect(self._reset_esc_count)
        self.esc_press_count = 0
        
        # UI组件
        self.main_tab_widget = None
        self.chat_tab = None
        self.chat_history_tab = None
        self.memory_tab = None
        self.rules_tab = None
        self.todos_tab = None
        self.checkpoints_tab = None
        self.stats_tab = None
        self.workflow_tab = None
        self.taskflow_tab = None
        self.new_work_tab = None
        
        # 设置窗口
        if project_path:
            project_name = os.path.basename(os.path.normpath(project_path))
            if self.work_title:
                self.setWindowTitle(f"{project_name} - {self.work_title}")
            else:
                self.setWindowTitle(project_name)
        else:
            if self.work_title:
                self.setWindowTitle(f"Interactive Feedback - {self.work_title}")
            else:
                self.setWindowTitle("Interactive Feedback")
        self.setMinimumSize(550, 600)
        self.resize(550, 900)
        
        # 设置窗口始终置顶
        from PySide6.QtCore import Qt
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # 检查项目初始化状态
        self.project_initialized = True if skip_init_check else self._check_project_initialization()
        
        # 直接创建UI，不再进行认证检查
        self._create_ui()
        
        # 设置智能窗口位置（避免重叠）
        self._set_smart_position()
        
        # Start countdown timer (无论认证状态如何都启动)
        if self.timeout > 0:
            try:
                self.countdown_timer.start(1000)  # Update every second
            except Exception as e:
                logger = get_debug_logger()
                logger.log_error(f"启动倒计时器失败: {e}", "UI")
        
        # 设置快捷键
        self._setup_shortcuts()

        # 初始化版本检查线程
        self.version_check_thread = None

        # 30秒后在独立线程中检查新版本
        if self.timeout > 0:
            QTimer.singleShot(30000, self._start_version_check)

    def _get_version(self):
        """获取版本号 - 优先从包元数据读取，然后从文件读取"""
        # 方案1: 从包元数据读取（适用于pip安装后）
        try:
            from importlib.metadata import version
            return version('feedback-mcp')
        except Exception:
            pass

        # 方案2: 从version.txt读取（适用于开发环境）
        try:
            from pathlib import Path
            version_file = Path(__file__).parent.parent / 'version.txt'
            if version_file.exists():
                return version_file.read_text().strip()
        except Exception:
            pass

        # 方案3: 从pyproject.toml读取（适用于开发环境）
        try:
            from pathlib import Path
            pyproject_file = Path(__file__).parent.parent / 'pyproject.toml'
            if pyproject_file.exists():
                content = pyproject_file.read_text()
                for line in content.split('\n'):
                    if line.startswith('version ='):
                        return line.split('=')[1].strip().strip('"')
        except Exception:
            pass

        # 最终降级方案
        return "1.0.0"

    def _start_version_check(self):
        """启动版本检查线程"""
        try:
            current_version = self._get_version()
            # 创建并启动版本检查线程
            self.version_check_thread = VersionCheckThread(current_version)  # 移除 parent
            # 连接信号到槽函数
            self.version_check_thread.version_checked.connect(self._on_version_checked)
            # 线程结束后清理引用并删除对象
            self.version_check_thread.finished.connect(self._on_version_check_finished)
            # 启动线程
            self.version_check_thread.start()
        except Exception:
            pass  # 静默处理错误

    def _on_version_check_finished(self):
        """版本检查线程结束的回调"""
        try:
            if self.version_check_thread:
                self.version_check_thread.deleteLater()
                self.version_check_thread = None
        except Exception:
            pass

    def _on_version_checked(self, latest: str, current: str):
        """版本检查完成的回调（在主线程中执行）"""
        try:
            # 版本比较：只有当latest > current时才提示更新
            if self._version_compare(latest, current) > 0:
                # 更新版本标签文本和样式
                self.version_label.setText(f"当前版本 {current} | 🔔 有新版本 {latest}")
                self.version_label.setStyleSheet("""
                    QLabel {
                        color: #4CAF50;
                        font-size: 10px;
                        padding: 2px 6px;
                        text-decoration: underline;
                    }
                """)
                # 更新tooltip，提示可以点击
                self.version_label.setToolTip(f"发现新版本 v{latest}\n点击复制更新命令")
                # 设置鼠标指针为手型
                self.version_label.setCursor(Qt.PointingHandCursor)
                # 启用鼠标事件
                self.version_label.setMouseTracking(True)
                # 保存最新版本号，供点击事件使用
                self.latest_version = latest
                # 添加点击事件
                self.version_label.mousePressEvent = self._on_version_label_clicked
        except Exception:
            pass  # 静默处理错误

    def _on_version_label_clicked(self, event):
        """处理版本标签点击事件 - 复制更新命令并弹窗提示"""
        from PySide6.QtWidgets import QApplication, QMessageBox
        if hasattr(self, 'latest_version'):
            # 复制更新命令到剪贴板
            update_command = f"pip install --upgrade feedback-mcp"
            QApplication.clipboard().setText(update_command)

            # 显示弹窗提示
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("版本更新")
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setText(f"已复制更新指令到剪贴板，请升级\n\n更新命令：{update_command}")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

            # 应用暗色主题样式
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QMessageBox QLabel {
                    color: #ffffff;
                }
                QMessageBox QPushButton {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 5px 15px;
                    border-radius: 3px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #4a4a4a;
                }
                QMessageBox QPushButton:pressed {
                    background-color: #2a2a2a;
                }
            """)

            msg_box.exec()

    def _check_project_initialization(self) -> bool:
        """检查项目是否已初始化（检查.agent和_agent-local目录是否存在）"""
        if not self.project_path:
            return False
        
        agent_dir = os.path.join(self.project_path, ".agent")
        agent_local_dir = os.path.join(self.project_path, "_agent-local")
        
        return os.path.exists(agent_dir) and os.path.exists(agent_local_dir)
    
    def _create_initialization_status_widget(self, header_layout):
        """创建项目初始化状态显示组件"""
        if not self.project_path:
            return
        
        # 如果跳过初始化检查，不显示初始化组件
        if self.skip_init_check:
            return
        
        # 只有未初始化时才显示组件，已初始化时保持界面简洁
        if not self.project_initialized:
            # 未初始化，显示初始化按钮，样式与其他header按钮保持一致
            init_button = QPushButton("项目初始化")
            init_button.setMaximumWidth(100)
            init_button.clicked.connect(self._show_initialization_command)
            # 使用与精简版按钮相同的样式风格，但使用警告色调
            init_button.setStyleSheet("""
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
            header_layout.addWidget(init_button)
    
    def _show_initialization_dialog(self):
        """显示项目初始化提示弹窗（优化版：去除延迟，直接显示）"""
        from PySide6.QtWidgets import QMessageBox
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("项目未初始化")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        
        # 将详细信息直接放在主文本中，不使用详细文本
        main_text = """检测到当前项目尚未初始化"""
        
        msg_box.setText(main_text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # 应用暗色主题样式
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMessageBox QLabel {
                color: #ffffff;
            }
            QMessageBox QPushButton {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QMessageBox QPushButton:hover {
                background-color: #4a4a4a;
            }
            QMessageBox QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """)
        
        # 直接显示对话框，去除延迟
        try:
            result = msg_box.exec()
            if result == QMessageBox.StandardButton.Ok:
                # 用户点击确定，自动发送初始化命令反馈
                init_message = "请执行命令初始化该项目的AI工具 npm exec --registry=https://omp-npm.acewill.net/ -- workflow-mcp-init"
                self.feedback_result = {
                    'content': [{"type": "text", "text": init_message}],
                    'images': []
                }
                # 关闭当前窗口，返回反馈
                self.close()
        except Exception as e:
            logger = get_debug_logger()
            logger.log_error(f"显示初始化对话框失败: {e}", "UI")
    
    def _show_initialization_command(self):
        """显示初始化命令信息对话框"""
        from PySide6.QtWidgets import QMessageBox
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("项目初始化")
        msg_box.setIcon(QMessageBox.Icon.Information)
        
        command_text = "npm exec --registry=https://omp-npm.acewill.net/ -- workflow-mcp-init"
        
        # 将详细信息直接放在主文本中，不使用详细文本
        main_text = f"""请在项目根目录下执行以下命令：

{command_text}

命令执行完成后，将会创建以下目录：
• .agent/ - 代理配置目录
• _agent-local/ - 本地代理数据目录

初始化完成后，请重新打开此界面以使用完整功能。"""
        
        msg_box.setText(main_text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # 应用暗色主题样式
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMessageBox QLabel {
                color: #ffffff;
            }
            QMessageBox QPushButton {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QMessageBox QPushButton:hover {
                background-color: #4a4a4a;
            }
            QMessageBox QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """)
        
        result = msg_box.exec()
        if result == QMessageBox.StandardButton.Ok:
            # 用户点击确定，自动发送初始化命令反馈
            init_message = "请执行命令初始化该项目的AI工具 npm exec --registry=https://omp-npm.acewill.net/ -- workflow-mcp-init"
            self.feedback_result = {
                'content': [{"type": "text", "text": init_message}],
                'images': []
            }
            # 关闭当前窗口，返回反馈
            self.close()
    
    def _create_ui(self):
        """创建主界面"""
        # 设置中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 添加状态栏
        self.statusBar().showMessage("就绪", 2000)
        
        # Header with GitLab auth status
        header_layout = QHBoxLayout()

        # 版本号标签 - 左上角
        self.version_label = QLabel(f"v{self._get_version()}")
        self.version_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 9px;
                padding: 2px 6px;
            }
        """)
        self.version_label.setToolTip("当前版本")
        header_layout.addWidget(self.version_label)

        # 已移除GitLab认证状态显示
        
        # 项目初始化状态显示
        self._create_initialization_status_widget(header_layout)
        
        header_layout.addStretch()  # Push content to center
        
        # IDE设置按钮（放在注销按钮右侧，显示IDE按钮左侧）
        self.ide_settings_button = QPushButton("设置IDE")
        self.ide_settings_button.setMaximumWidth(80)
        self.ide_settings_button.clicked.connect(self._show_ide_settings_dialog)
        self.ide_settings_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.ide_settings_button.setToolTip("设置默认IDE")
        header_layout.addWidget(self.ide_settings_button)
        
        # 显示IDE按钮
        # 优先使用配置文件，其次使用传入的ide参数（环境变量）
        # DEBUG: 打印IDE参数状态
        print(f"[DEBUG] FeedbackUI初始化 - self.ide={self.ide}, 环境变量IDE={os.getenv('IDE')}")

        # 尝试从配置文件读取IDE
        ide_from_config = None
        if self.project_path:
            try:
                from feedback_config import FeedbackConfig
                config_manager = FeedbackConfig(self.project_path)
                ide_from_config = config_manager.get_ide()
            except Exception:
                pass  # 忽略错误，使用默认值

        # 确定最终使用的IDE：配置文件 > 环境变量参数 > 默认
        final_ide = ide_from_config or self.ide

        if final_ide:
            # 动态生成IDE显示名称
            # 如果IDE名称全小写，则首字母大写；否则保留原样
            ide_display_name = final_ide if any(c.isupper() for c in final_ide) else final_ide.capitalize()
            if final_ide.lower() == "vscode":
                ide_display_name = "VSCode"
            try:
                logger = get_debug_logger()
                logger.info(f"使用IDE: {final_ide} -> 显示名称: {ide_display_name}")
            except:
                pass  # 忽略日志错误
        else:
            # 没有配置IDE
            ide_display_name = "IDE"
            try:
                logger = get_debug_logger()
                logger.info("未配置IDE")
            except:
                pass  # 忽略日志错误

        self.ide_button = QPushButton(f"打开{ide_display_name}")
        self.ide_button.setMaximumWidth(100)
        self.ide_button.clicked.connect(self._open_cursor_ide)
        self.ide_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.ide_button.setToolTip(f"使用 {ide_display_name} 打开当前项目")
        header_layout.addWidget(self.ide_button)
        
        # 稍后处理按钮（临时关闭）
        self.compact_button = QPushButton("稍后处理")
        self.compact_button.setMaximumWidth(80)
        self.compact_button.clicked.connect(self._temp_close)
        self.compact_button.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #546E7A;
            }
            QPushButton:pressed {
                background-color: #455A64;
            }
        """)
        header_layout.addWidget(self.compact_button)
        
        layout.addLayout(header_layout)
        
        # 创建标签页容器 - 与原版保持一致的命名
        self.main_tab_widget = QTabWidget()
        self.main_tab_widget.currentChanged.connect(self._on_main_tab_changed)
        
        # 注意：与原版保持一致，不设置自定义样式，使用系统默认QTabWidget样式

                # 只创建必要的对话标签页
        self._create_chat_tab()         # 反馈
        self._create_chat_history_tab() # 对话记录

        # 如果传入了workspace_id，创建工作空间tab
        if self.workspace_id:
            self._create_workspace_tab()

        layout.addWidget(self.main_tab_widget)
        
        # 🆕 如果项目未初始化，显示弹窗提示（与原版保持一致）
        if not self.skip_init_check and not self.project_initialized:
            self._show_initialization_dialog()
    
    def _create_chat_tab(self):
        """创建聊天标签页"""
        self.chat_tab = ChatTab(
            prompt=self.prompt,
            predefined_options=self.predefined_options,
            project_path=self.project_path,
            work_title=self.work_title,
            timeout=self.timeout,
            files=self.files,
            bugdetail=self.bugdetail,
            session_id=self.session_id,
            workspace_id=self.workspace_id,
            parent=self
        )
        
        # 连接信号
        self.chat_tab.feedback_submitted.connect(self._handle_feedback_submitted)
        self.chat_tab.command_executed.connect(self._handle_command_execution)
        self.chat_tab.option_executed.connect(self._execute_option_immediately)
        self.chat_tab.text_changed.connect(self._on_text_changed)

        self.main_tab_widget.addTab(self.chat_tab, "反馈")

    def _create_chat_history_tab(self):
        """创建对话记录标签页"""
        if ChatHistoryTab:
            self.chat_history_tab = ChatHistoryTab(
                project_path=self.project_path,
                session_id=self.session_id,
                workspace_id=self.workspace_id,
                parent=self
            )
            self.main_tab_widget.addTab(self.chat_history_tab, "对话记录")

    def _create_workspace_tab(self):
        """创建工作空间标签页

        只有在以下条件都满足时才创建工作空间tab:
        1. WorkspaceTab类可用
        2. 传入了workspace_id
        3. 能够成功加载工作空间配置
        """
        if not WorkspaceTab or not self.workspace_id:
            return

        # 验证是否能加载工作空间配置
        try:
            from workspace_manager import WorkspaceManager
            manager = WorkspaceManager(self.project_path)
            config = manager.load_workspace_config(self.workspace_id)

            # 只有成功加载到配置时才创建tab
            if config:
                self.workspace_tab = WorkspaceTab(
                    workspace_id=self.workspace_id,
                    project_path=self.project_path,
                    parent=self
                )
                self.main_tab_widget.addTab(self.workspace_tab, "工作空间")
        except Exception:
            # 加载失败时不创建tab
            pass
    
    def _create_memory_tab(self):
        """创建记忆选项卡"""
        if MemoryTab and self.project_path:
            self.memory_tab = MemoryTab(self.project_path, parent=self)
            self.main_tab_widget.addTab(self.memory_tab, "记忆")
    
    def _create_rules_tab(self):
        """创建规则选项卡"""
        if RulesTab and self.project_path:
            self.rules_tab = RulesTab(self.project_path, parent=self)
            self.main_tab_widget.addTab(self.rules_tab, "规则")
    
    def _create_todos_tab_deprecated(self):
        """创建Todos选项卡"""
        # 确保正确导入TodosTab
        try:
            from tabs.todos_tab import TodosTab as LocalTodosTab
        except ImportError:
            LocalTodosTab = None
            
        if LocalTodosTab and self.project_path:
            try:
                self.todos_tab = LocalTodosTab()
                # 初始化项目路径
                self.todos_tab.initialize_manager(self.project_path)
                self.main_tab_widget.addTab(self.todos_tab, "Todos")
                # 临时隐藏todos选项卡
                self.todos_tab_index = self.main_tab_widget.count() - 1
                self.main_tab_widget.setTabVisible(self.todos_tab_index, False)
            except Exception as e:
                self.todos_tab = None
        else:
            # 如果导入失败或没有项目路径，设置为None
            self.todos_tab = None
    
    def _create_checkpoints_tab_deprecated(self):
        """创建检查点选项卡"""
        if CheckpointsTab and self.project_path:
            self.checkpoints_tab = CheckpointsTab(self.project_path, parent=self)
            self.main_tab_widget.addTab(self.checkpoints_tab, "检查点")
    
    def _create_workflow_tabs_deprecated(self):
        """创建工作流相关标签页"""
        # 当前工作流标签页
        try:
            current_workflow_tab = CurrentWorkflowWidget(project_path=self.project_path)
            self.main_tab_widget.addTab(current_workflow_tab, "当前工作流")
            self.current_workflow_tab_index = self.main_tab_widget.count() - 1
            self.current_workflow_tab_widget = current_workflow_tab
        except ImportError:
            # 如果无法导入，创建空白标签页占位
            from PySide6.QtWidgets import QWidget
            current_workflow_tab = QWidget()
            self.main_tab_widget.addTab(current_workflow_tab, "当前工作流")
            self.current_workflow_tab_index = self.main_tab_widget.count() - 1
            self.current_workflow_tab_widget = current_workflow_tab
        
        # 当前任务流标签页
        try:
            current_taskflow_tab = CurrentTaskflowWidget(project_path=self.project_path)
            self.main_tab_widget.addTab(current_taskflow_tab, "当前任务流")
            self.current_taskflow_tab_index = self.main_tab_widget.count() - 1
            self.current_taskflow_tab_widget = current_taskflow_tab
        except ImportError:
            # 如果无法导入，创建空白标签页占位
            from PySide6.QtWidgets import QWidget
            current_taskflow_tab = QWidget()
            self.main_tab_widget.addTab(current_taskflow_tab, "当前任务流")
            self.current_taskflow_tab_index = self.main_tab_widget.count() - 1
            self.current_taskflow_tab_widget = current_taskflow_tab
        
        # 注意：根据原版UI，默认只显示"对话"、"新工作"、"统计"三个标签页
        # "当前工作流"和"当前任务流"标签页保持隐藏状态，但功能保留以备需要时显示
        self.main_tab_widget.setTabVisible(self.current_workflow_tab_index, False)
        self.main_tab_widget.setTabVisible(self.current_taskflow_tab_index, False)
    
    def _create_new_project_tab_deprecated(self):
        """创建新项目选项卡"""
        if NewProjectTab:
            self.new_project_tab = NewProjectTab(parent=self)
            self.main_tab_widget.addTab(self.new_project_tab, "新项目")
            # 临时隐藏新项目选项卡
            self.new_project_tab_index = self.main_tab_widget.count() - 1
            self.main_tab_widget.setTabVisible(self.new_project_tab_index, False)
        else:
            # 如果导入失败，设置为None
            self.new_project_tab = None

    def _create_new_work_tab(self):
        """创建新工作标签页"""
        self.new_work_tab = NewWorkTab(self.project_path, parent=self)
        
        # 连接信号
        self.new_work_tab.workflow_executed.connect(self._execute_workflow)
        self.new_work_tab.taskflow_executed.connect(self._execute_taskflow)
        
        self.main_tab_widget.addTab(self.new_work_tab, "新工作")
    
    def _create_config_tab(self):
        """创建配置标签页"""
        # 配置功能已移除，IDE现在只从环境变量读取
        from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
        config_widget = QWidget()
        layout = QVBoxLayout(config_widget)
        label = QLabel("IDE配置请通过环境变量设置\n\n例如: IDE=cursor")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #888888; font-size: 14px;")
        layout.addWidget(label)
        self.main_tab_widget.addTab(config_widget, "配置")

    def _create_stats_tab(self):
        """创建统计标签页"""
        self.stats_tab = StatsTab(project_path=self.project_path, parent=self)
        self.main_tab_widget.addTab(self.stats_tab, "统计")
    
    def _on_ide_config_changed(self, ide_name: str):
        """IDE配置变更时的处理"""
        # IDE配置已改为从环境变量读取，此函数保留为空实现
        pass

    def _handle_feedback_submitted(self, content_parts: List[Dict[str, str]], images: List[str]):
        """处理反馈提交"""
        # 停止倒计时
        if self.countdown_timer.isActive():
            self.countdown_timer.stop()

        # 用户正常提交，在后台清除stop hook状态
        if self.session_id:
            import threading
            def clear_session_bg():
                try:
                    manager = SessionManager(session_id=self.session_id, project_path=self.project_path)
                    manager.clear_session(self.session_id)
                except Exception as e:
                    logger = get_debug_logger()
                    logger.log_warning(f"Failed to clear session on submit: {e}", "UI")
            threading.Thread(target=clear_session_bg, daemon=True).start()

        # 设置结果
        self.feedback_result = {
            'content': content_parts,
            'images': images
        }

        self.close()
    
    def _handle_command_execution(self, command_content: str):
        """处理指令执行"""
        if command_content:
            # 构建指令内容的结构化格式
            content_parts = [{"type": "command", "text": command_content}]

            self.feedback_result = {
                'content': content_parts,
                'images': []
            }
            self.close()
    
    def _execute_option_immediately(self, option_index: int):
        """立即执行选项"""
        if 0 <= option_index < len(self.predefined_options):
            option_text = self.predefined_options[option_index]

            content_parts = [{"type": "options", "text": option_text}]
            self._handle_feedback_submitted(content_parts, [])
    
    def _execute_workflow(self, workflow_name: str):
        """执行工作流"""
        command = f"/work use {workflow_name}"
        self._handle_command_execution(command)
    
    def _execute_taskflow(self, taskflow_name: str):
        """执行任务流"""
        command = f"/task use {taskflow_name}"
        self._handle_command_execution(command)
    
    def _on_text_changed(self):
        """文本变化处理（委托给聊天标签页）"""
        pass
    
    def _on_main_tab_changed(self, index):
        """主标签页切换处理 - 优化版：减少QTimer使用，改为直接同步调用"""
        # 当切换到当前工作流选项卡时，直接刷新数据和显示
        if hasattr(self, 'current_workflow_tab_index') and index == self.current_workflow_tab_index and hasattr(self, 'current_workflow_tab_widget'):
            try:
                # 直接刷新，不使用QTimer延迟
                if hasattr(self.current_workflow_tab_widget, 'refresh_data'):
                    self.current_workflow_tab_widget.refresh_data()
                self.current_workflow_tab_widget.show()
                self.current_workflow_tab_widget.update()
            except Exception as e:
                logger = get_debug_logger()
                logger.log_error(f"Error refreshing current workflow tab: {e}", "UI")
        
        # 当切换到当前任务流选项卡时，直接刷新数据和显示
        if hasattr(self, 'current_taskflow_tab_index') and index == self.current_taskflow_tab_index and hasattr(self, 'current_taskflow_tab_widget'):
            try:
                # 直接刷新，不使用QTimer延迟
                if hasattr(self.current_taskflow_tab_widget, 'refresh_data'):
                    self.current_taskflow_tab_widget.refresh_data()
                self.current_taskflow_tab_widget.show()
                self.current_taskflow_tab_widget.update()
            except Exception as e:
                logger = get_debug_logger()
                logger.log_error(f"Error refreshing current taskflow tab: {e}", "UI")
                
        # 当切换到统计选项卡时，刷新数据（统计是最后一个选项卡）
        if hasattr(self, 'stats_tab') and self.main_tab_widget.tabText(index) == "统计":
            self.stats_tab.refresh_data()
    
    def _open_cursor_ide(self):
        """打开配置的IDE"""
        try:
            if not self.project_path:
                self.statusBar().showMessage("❌ 请先选择项目路径", 3000)
                return

            # 获取当前配置的IDE
            try:
                from ide_utils import open_project_with_ide
                from feedback_config import FeedbackConfig

                # 优先从配置文件读取，其次使用传入的IDE参数（来自环境变量）
                config_manager = FeedbackConfig(self.project_path)
                ide_to_use = config_manager.get_ide() or self.ide

                # 如果没有IDE配置，提示用户配置
                if not ide_to_use:
                    reply = QMessageBox.question(
                        self,
                        "未配置IDE",
                        "尚未配置默认IDE，是否现在设置？",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self._show_ide_settings_dialog()
                    return

                success = open_project_with_ide(self.project_path, ide_to_use)

                # 动态获取IDE显示名称
                # 如果是动态IDE，直接使用名称
                if ide_to_use:
                    ide_display = ide_to_use if any(c.isupper() for c in ide_to_use) else ide_to_use.capitalize()
                else:
                    ide_display = 'IDE'

                if success:
                    self.statusBar().showMessage(f"✅ {ide_display} 已打开", 3000)
                else:
                    # 提供更详细的错误提示
                    from ide_utils import is_ide_available

                    if not is_ide_available(ide_to_use):
                        self.statusBar().showMessage(f"❌ {ide_display} 未安装或不在PATH中", 3000)
                    else:
                        self.statusBar().showMessage(f"❌ 打开 {ide_display} 失败", 3000)
                        
            except ImportError:
                # 回退到原来的Cursor逻辑
                success = focus_cursor_to_project(self.project_path)
                if success:
                    self.statusBar().showMessage("✅ Cursor IDE 已打开", 3000)
                else:
                    if not is_macos():
                        self.statusBar().showMessage("❌ 此功能仅支持 macOS", 3000)
                    else:
                        self.statusBar().showMessage("❌ 打开 Cursor IDE 失败", 3000)
                        
        except Exception as e:
            self.statusBar().showMessage(f"❌ 打开IDE出错: {e}", 3000)
    
    def _show_ide_settings_dialog(self):
        """显示IDE设置对话框"""
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QRadioButton, QLineEdit,
            QPushButton, QLabel, QButtonGroup, QHBoxLayout
        )

        try:
            from feedback_config import FeedbackConfig
        except ImportError:
            QMessageBox.warning(self, "导入错误", "无法加载配置模块")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("设置IDE")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)

        # 加载当前配置
        config_manager = FeedbackConfig(self.project_path)
        current_ide = config_manager.get_ide()

        # 说明文字
        info_label = QLabel("选择默认IDE（用于打开项目）：")
        layout.addWidget(info_label)

        # 常用IDE单选按钮组
        button_group = QButtonGroup(dialog)
        button_group.setExclusive(False)  # 允许取消勾选
        radio_buttons = {}

        ides = ["cursor", "vscode", "kiro", "qoder", "pycharm", "intellij"]
        for ide in ides:
            rb = QRadioButton(ide.capitalize() if ide != "vscode" else "VSCode")
            rb.setProperty("ide_value", ide)
            radio_buttons[ide] = rb
            button_group.addButton(rb)
            layout.addWidget(rb)

            # 如果当前配置匹配，选中该按钮
            if current_ide and current_ide.lower() == ide:
                rb.setChecked(True)

        # 分隔线
        layout.addSpacing(10)
        separator_label = QLabel("或输入自定义IDE命令：")
        layout.addWidget(separator_label)

        # 自定义IDE输入框
        custom_input = QLineEdit()
        custom_input.setPlaceholderText("例如：code, idea, sublime")

        # 如果当前配置是自定义的，填充到输入框
        if current_ide and current_ide.lower() not in ides:
            custom_input.setText(current_ide)

        layout.addWidget(custom_input)

        # 添加交互联动
        def on_radio_clicked(clicked_button):
            """当点击单选按钮时的处理"""
            # 如果点击的是已选中的按钮，取消选中
            if clicked_button.isChecked():
                # 取消其他所有按钮的选中状态（实现互斥）
                for rb in radio_buttons.values():
                    if rb != clicked_button:
                        rb.setChecked(False)
                # 清空自定义输入框
                custom_input.clear()

        def on_custom_input_changed():
            """当输入自定义命令时，取消所有预设单选按钮的选中"""
            if custom_input.text().strip():
                for rb in radio_buttons.values():
                    rb.setChecked(False)

        # 连接信号
        for rb in radio_buttons.values():
            rb.clicked.connect(lambda checked=False, btn=rb: on_radio_clicked(btn))
        custom_input.textChanged.connect(on_custom_input_changed)

        # 按钮行
        button_layout = QHBoxLayout()

        clear_button = QPushButton("清除配置")
        clear_button.clicked.connect(lambda: self._clear_ide_config(dialog, config_manager))

        ok_button = QPushButton("确定")
        ok_button.setDefault(True)

        cancel_button = QPushButton("取消")

        button_layout.addWidget(clear_button)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        # 连接信号
        def save_and_close():
            ide_name = None

            # 优先检查预设单选按钮
            selected_preset = None
            for ide, rb in radio_buttons.items():
                if rb.isChecked():
                    selected_preset = ide
                    break

            if selected_preset:
                # 使用预设IDE
                config_manager.set_ide(ide=selected_preset)
                ide_name = selected_preset
                self.statusBar().showMessage(f"✅ IDE已设置为: {selected_preset.capitalize()}", 3000)
            else:
                # 检查自定义输入框
                custom_text = custom_input.text().strip()
                if custom_text:
                    config_manager.set_ide(custom_command=custom_text)
                    ide_name = custom_text
                    self.statusBar().showMessage(f"✅ IDE已设置为: {custom_text}", 3000)

            # 更新打开IDE按钮的文本
            if ide_name:
                ide_display = ide_name if any(c.isupper() for c in ide_name) else ide_name.capitalize()
                if ide_name.lower() == "vscode":
                    ide_display = "VSCode"
                self.ide_button.setText(f"打开{ide_display}")

            dialog.accept()

        ok_button.clicked.connect(save_and_close)
        cancel_button.clicked.connect(dialog.reject)

        # 应用暗色主题
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QRadioButton {
                color: #ffffff;
            }
            QLineEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """)

        dialog.exec()

    def _clear_ide_config(self, dialog, config_manager):
        """清除IDE配置"""
        config_manager.clear_ide()
        self.statusBar().showMessage("✅ IDE配置已清除", 3000)
        # 恢复默认按钮文本
        self.ide_button.setText("打开IDE")
        dialog.accept()

    def _check_updates(self):
        """检查更新"""
        import requests
        import subprocess
        from PySide6.QtWidgets import QMessageBox
        
        try:
            # 获取GitLab认证
            if hasattr(self, 'auth_status_widget') and self.auth_status_widget:
                auth = self.auth_status_widget.auth
                if not auth.is_authenticated():
                    QMessageBox.warning(self, "需要认证", "请先进行GitLab认证")
                    return
            else:
                QMessageBox.warning(self, "认证错误", "无法获取GitLab认证状态")
                return
            
            # 禁用按钮，防止重复点击
            self.update_button.setEnabled(False)
            self.update_button.setText("检查中...")
            
            # 获取远程version.txt
            url = "https://gitlab.acewill.cn/api/v4/projects/ai%2Fagent-dev/repository/files/version.txt/raw?ref=3.5"
            headers = {"Authorization": f"Bearer {auth.load_token()}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                self._reset_update_button()
                QMessageBox.warning(self, "获取失败", f"无法获取远程版本信息: {response.status_code}")
                return
            
            remote_version = response.text.strip()
            
            # 读取本地version.txt
            try:
                if self.project_path:
                    version_file = os.path.join(self.project_path, "version.txt")
                else:
                    version_file = "version.txt"
                    
                with open(version_file, "r", encoding="utf-8") as f:
                    local_version = f.read().strip()
            except:
                local_version = "1.0.0"
            
            self._reset_update_button()
            
            # 比较版本 - 使用版本号解析比较
            if self._version_compare(remote_version, local_version) > 0:
                # 检查是否有更新对话框可用
                if UpdateInfoDialog:
                    # 显示详细的更新信息对话框
                    update_dialog = UpdateInfoDialog(local_version, remote_version, self.project_path, self)
                    if update_dialog.exec() == QDialog.Accepted and update_dialog.should_update:
                        # 用户确认更新，继续执行git pull
                        pass
                    else:
                        return  # 用户取消更新
                else:
                    # 回退到原有的简单对话框
                    reply = QMessageBox.question(
                        self, "发现更新", 
                        f"本地版本: {local_version}\n远程版本: {remote_version}\n\n是否立即更新?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        return
                    # 执行git pull - 在server.py脚本所在目录执行
                    try:
                        # 获取server.py脚本所在的目录
                        server_dir = os.path.dirname(os.path.abspath(__file__))
                        
                        result = subprocess.run(
                            ["git", "pull"], 
                            capture_output=True, 
                            text=True, 
                            cwd=server_dir,
                            timeout=30
                        )
                        if result.returncode == 0:
                            QMessageBox.information(self, "更新成功", "代码已更新到最新版本")
                        else:
                            QMessageBox.critical(self, "更新失败", f"git pull失败:\n{result.stderr}")
                    except subprocess.TimeoutExpired:
                        QMessageBox.critical(self, "更新失败", "git pull超时")
                    except Exception as e:
                        QMessageBox.critical(self, "更新失败", f"执行git pull失败: {e}")
            else:
                QMessageBox.information(self, "已是最新", "当前已是最新版本")
                
        except requests.RequestException as e:
            self._reset_update_button()
            QMessageBox.critical(self, "网络错误", f"检查更新失败: {e}")
        except Exception as e:
            self._reset_update_button()
            QMessageBox.critical(self, "检查失败", f"检查更新失败: {e}")
    
    def _reset_update_button(self):
        """重置更新按钮状态"""
        self.update_button.setEnabled(True)
        self.update_button.setText("检查更新")
    
    def _version_compare(self, version1: str, version2: str) -> int:
        """
        比较两个版本号
        
        Args:
            version1: 第一个版本号
            version2: 第二个版本号
        
        Returns:
            int: 1 if version1 > version2, -1 if version1 < version2, 0 if equal
        """
        try:
            # 解析版本号为整数列表
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # 补齐较短的版本号（比如 1.0 补齐为 1.0.0）
            max_length = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_length - len(v1_parts)))
            v2_parts.extend([0] * (max_length - len(v2_parts)))
            
            # 逐位比较
            for v1, v2 in zip(v1_parts, v2_parts):
                if v1 > v2:
                    return 1
                elif v1 < v2:
                    return -1
            
            return 0  # 版本号相等
            
        except ValueError:
            # 如果无法解析版本号，回退到字符串比较
            if version1 > version2:
                return 1
            elif version1 < version2:
                return -1
            else:
                return 0
    
    def _set_smart_position(self):
        """设置智能窗口位置，避免多窗口重叠"""
        if WindowPositionManager:
            try:
                # 获取下一个窗口位置
                x, y = WindowPositionManager.get_next_position('main')
                self.move(x, y)
                # 保存当前位置供后续清理
                self._window_position = (x, y)
            except Exception as e:
                print(f"设置窗口位置失败: {e}")
                # 如果失败，使用默认居中
                self._center_window()
        else:
            # 没有位置管理器时，使用默认居中
            self._center_window()
    
    def _center_window(self):
        """将窗口居中显示"""
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = screen_geometry.x() + (screen_geometry.width() - self.width()) // 2
            y = screen_geometry.y() + (screen_geometry.height() - self.height()) // 2
            self.move(x, y)

    
    def _update_countdown(self):
        """更新倒计时 - 优化版：增强错误处理，避免加密环境下的异常"""
        try:
            self.elapsed_time += 1
            
            # 更新聊天标签页的进度条（增加安全检查）
            if self.chat_tab and hasattr(self.chat_tab, 'update_progress'):
                try:
                    self.chat_tab.update_progress(self.elapsed_time)
                except Exception as e:
                    logger = get_debug_logger()
                    logger.log_warning(f"Failed to update chat progress: {e}", "UI")
            
            # 检查是否超时
            if self.elapsed_time >= self.timeout:
                self.countdown_timer.stop()
                # 超时前检查输入框是否有内容，如果有则保存到历史记录
                if self.chat_tab and hasattr(self.chat_tab, 'save_input_to_history'):
                    try:
                        self.chat_tab.save_input_to_history()
                    except Exception as e:
                        logger = get_debug_logger()
                        logger.log_warning(f"Failed to save input to history on timeout: {e}", "UI")
                # 自动提交空反馈
                self._handle_feedback_submitted([], [])
        except Exception as e:
            logger = get_debug_logger()
            logger.log_error(f"倒计时更新失败: {e}", "UI")
            # 确保定时器停止，避免无限循环
            if self.countdown_timer.isActive():
                self.countdown_timer.stop()
    

    
    def _temp_close(self):
        """临时关闭（精简版按钮），不写入结果"""
        self.is_temp_close = True
        self.close()

    def closeEvent(self, event):
        """关闭事件处理"""
        # 清理窗口位置记录
        if WindowPositionManager and hasattr(self, '_window_position'):
            try:
                x, y = self._window_position
                WindowPositionManager.remove_position('main', x, y)
            except Exception:
                pass  # 静默处理错误

        # 停止并等待版本检查线程结束
        try:
            if self.version_check_thread is not None:
                if self.version_check_thread.isRunning():
                    self.version_check_thread.request_stop()
                    # 等待线程结束，超时后强制终止
                    if not self.version_check_thread.wait(3000):  # 等待3秒
                        # 超时，强制终止线程
                        self.version_check_thread.terminate()
                        self.version_check_thread.wait(1000)  # 等待终止完成
                # 清理引用
                self.version_check_thread = None
        except (RuntimeError, AttributeError):
            pass  # 对象可能已被删除

        # 停止定时器
        if self.countdown_timer.isActive():
            self.countdown_timer.stop()

        # 停止ESC定时器
        if hasattr(self, 'esc_timer') and self.esc_timer.isActive():
            self.esc_timer.stop()

        # 清理 chat_tab 中的弹窗等子控件，避免 Qt 对象销毁顺序问题
        if self.chat_tab:
            try:
                # 清理输入框的指令弹窗和文件弹窗
                if hasattr(self.chat_tab, 'input_text'):
                    input_text = self.chat_tab.input_text
                    if hasattr(input_text, '_close_command_popup'):
                        input_text._close_command_popup()
                    if hasattr(input_text, '_close_file_popup'):
                        input_text._close_file_popup()
            except Exception:
                pass  # 静默处理错误

        # 处理延迟删除队列，确保 deleteLater 的对象被正确删除
        try:
            QApplication.processEvents()
        except Exception:
            pass

        # 在关闭前保存输入框内容到历史记录（无论是超时还是用户主动关闭）
        if self.chat_tab and hasattr(self.chat_tab, 'save_input_to_history'):
            try:
                self.chat_tab.save_input_to_history()
            except Exception as e:
                logger = get_debug_logger()
                logger.log_warning(f"Failed to save input to history on close: {e}", "UI")

        # 临时关闭（精简版按钮）：不写入结果，直接关闭
        if self.is_temp_close:
            event.accept()
            return

        # 如果没有反馈结果（说明是用户主动关闭，而不是正常提交或超时），设置特定的反馈结果
        if not self.feedback_result:
            # 区分关闭方式
            if self.session_id:
                try:
                    manager = SessionManager(session_id=self.session_id, project_path=self.project_path)

                    # 判断是超时关闭还是用户点击关闭
                    if self.elapsed_time >= self.timeout:
                        # 超时自动关闭
                        manager.mark_timeout_closed(self.session_id)
                    else:
                        # 用户主动关闭（点击关闭按钮或快捷键）
                        manager.mark_user_closed_by_button(self.session_id)
                except Exception as e:
                    logger = get_debug_logger()
                    logger.log_warning(f"Failed to mark session close type: {e}", "UI")

            self.feedback_result = {
                'content': [{"type": "text", "text": "STOP!请立即停止任何工作，不要再调用任何工具、回复任何消息。STOP!"}],
                'images': []
            }
        
        # 保存设置
        settings = QSettings("FeedbackUI", "MainWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("state", self.saveState())
        
        event.accept()
    
    def _setup_shortcuts(self):
        """设置快捷键"""
        from PySide6.QtGui import QShortcut, QKeySequence
        
        # Cmd+W 或 Ctrl+W 关闭窗口
        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self._handle_close_shortcut)
        
        # macOS 上的 Cmd+W
        if sys.platform == "darwin":
            cmd_close_shortcut = QShortcut(QKeySequence("Meta+W"), self)
            cmd_close_shortcut.activated.connect(self._handle_close_shortcut)
    
    def _handle_close_shortcut(self):
        """处理关闭快捷键"""
        # 直接关闭窗口，让closeEvent处理统一逻辑
        self.close()
    
    def keyPressEvent(self, event):
        """处理按键事件"""
        from PySide6.QtCore import Qt
        
        # 检测双击ESC
        if event.key() == Qt.Key_Escape:
            self.esc_press_count += 1
            
            if self.esc_press_count == 1:
                # 第一次按ESC，启动计时器（500ms内需要再按一次）
                self.esc_timer.start(500)
            elif self.esc_press_count == 2:
                # 第二次按ESC，关闭窗口
                self.esc_timer.stop()
                self.esc_press_count = 0
                
                # 直接关闭窗口，让closeEvent处理统一逻辑
                self.close()
                return  # 避免事件继续传播
        
        # 调用父类处理
        super().keyPressEvent(event)
    
    def _reset_esc_count(self):
        """重置ESC计数器"""
        self.esc_press_count = 0
    
    def run(self) -> FeedbackResult:
        """运行反馈界面并返回结果"""
        # 确保窗口显示在最前面
        self.show()
        self.raise_()  # 把窗口提到前台
        self.activateWindow()  # 激活窗口
        
        # 在macOS上确保窗口获得焦点
        import platform
        if platform.system() == 'Darwin':  # macOS
            self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        
        # 启动事件循环
        app = QApplication.instance()
        app.exec()
        
        # 临时关闭时返回None，不写入结果
        if self.is_temp_close:
            return None
        return self.feedback_result or {"content": [], "images": []}


def feedback_ui(prompt: str, predefined_options: Optional[List[str]] = None, output_file: Optional[str] = None, project_path: Optional[str] = None, work_title: Optional[str] = None, timeout: int = 60, skip_init_check: bool = False, session_id: Optional[str] = None, workspace_id: Optional[str] = None, files: Optional[List[str]] = None, bugdetail: Optional[str] = None, ide: Optional[str] = None) -> Optional[FeedbackResult]:
    """
    创建并显示反馈UI界面
    
    Args:
        prompt: 显示给用户的提示信息
        predefined_options: 预定义的选项列表
        output_file: 输出文件路径（暂未使用）
        project_path: 项目路径
        timeout: 超时时间（秒）
    
    Returns:
        FeedbackResult: 包含用户反馈和图片的结果
    """
    # 首先确保有QApplication实例 - 这在PyArmor加密环境中非常重要
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        # 设置应用程序退出策略，避免在加密环境中出现问题
        app.setQuitOnLastWindowClosed(True)
    
    # 设置暗色主题
    try:
        app.setPalette(get_dark_mode_palette(app))
        app.setStyle("Fusion")  # 与原版保持一致：设置Fusion样式
    except Exception as e:
        logger = get_debug_logger()
        logger.log_warning(f"主题设置失败: {e}", "UI")
    
    # 创建反馈UI（现在QApplication已经存在）
    try:
        ui = FeedbackUI(prompt, predefined_options, project_path, work_title, timeout, skip_auth_check=False, skip_init_check=skip_init_check, session_id=session_id, workspace_id=workspace_id, files=files, bugdetail=bugdetail, ide=ide)  # 恢复认证检查
    except Exception as e:
        logger = get_debug_logger()
        logger.log_error(f"FeedbackUI创建失败: {e}", "UI")
        import traceback
        traceback.print_exc()
        return {"content": [], "images": []}
    
    # 运行并获取结果
    try:
        result = ui.run()
        return result
    except Exception as e:
        logger = get_debug_logger()
        logger.log_error(f"UI运行失败: {e}", "UI")
        import traceback
        traceback.print_exc()
        return {"content": [], "images": []}


if __name__ == "__main__":
    import argparse
    import pickle
    
    parser = argparse.ArgumentParser(description='Feedback UI')
    parser.add_argument('--prompt', required=True, help='显示给用户的提示信息')
    parser.add_argument('--predefined-options', help='预定义选项（用|||分隔）')
    parser.add_argument('--project-path', help='项目路径')
    parser.add_argument('--work-title', help='当前工作标题')
    parser.add_argument('--timeout', type=int, default=60, help='超时时间（秒）')
    parser.add_argument('--skip-init-check', action='store_true', help='跳过项目初始化检查')
    parser.add_argument('--session-id', help='Claude Code会话ID')
    parser.add_argument('--workspace-id', help='工作空间ID')
    parser.add_argument('--files', help='AI创建或修改的文件路径（用|||分隔）')
    parser.add_argument('--bugdetail', help='正在修复的bug简介')
    parser.add_argument('--ide', help='指定使用的IDE（例如：cursor/vscode/kiro/qoder等）')
    parser.add_argument('--output-file', help='输出文件路径')
    
    args = parser.parse_args()
    
    # 解析预定义选项
    predefined_options = None
    if args.predefined_options:
        predefined_options = args.predefined_options.split('|||')

    # 解析文件列表
    files = None
    if args.files:
        files = args.files.split('|||')
    
    # 调用反馈UI
    result = feedback_ui(
        prompt=args.prompt,
        predefined_options=predefined_options,
        project_path=args.project_path,
        work_title=args.work_title,
        timeout=args.timeout,
        skip_init_check=args.skip_init_check,
        session_id=args.session_id,
        workspace_id=args.workspace_id,
        files=files,
        bugdetail=args.bugdetail,
        ide=args.ide
    )
    
    # 如果指定了输出文件且有结果，写入文件
    if args.output_file and result is not None:
        try:
            with open(args.output_file, 'wb') as f:
                pickle.dump(result, f)
        except Exception as e:
            print(f"写入输出文件失败: {e}", file=sys.stderr)
            sys.exit(1)
    elif result is not None:
        print(f"结果: {result}") 