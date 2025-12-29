"""
会话列表UI - 显示所有等待回复的会话
"""
import os
import sys
import socket
import json
import threading
import time
import subprocess
import tempfile
import pickle
from typing import Optional, List, Dict
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QProgressBar, QPushButton
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication

# 添加路径以导入session_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from session_manager import SessionManager
except ImportError:
    SessionManager = None


class SessionListUI(QMainWindow):
    """会话列表UI - 单例模式"""

    _instance: Optional['SessionListUI'] = None
    SOCKET_HOST = "127.0.0.1"
    SOCKET_PORT = 19876

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        super().__init__()
        self._initialized = True

        # 用于拖动窗口
        self.dragging = False
        self.drag_start_pos = None
        self.mouse_press_time = 0
        self.mouse_press_pos = None

        # 折叠状态
        self.is_collapsed = False
        self.expanded_height = 400

        # 呼吸动画状态
        self.glow_phase = 0
        self.has_new_feedback = False

        # 会话数据管理
        self.sessions: Dict[str, Dict] = {}  # request_id -> session_data
        self.session_sockets: Dict[str, socket.socket] = {}  # request_id -> socket
        self.feedback_processes: Dict[str, subprocess.Popen] = {}  # request_id -> process
        self.sessions_lock = threading.Lock()

        # 设置窗口属性
        self.setWindowTitle("等待回复")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(280, 400)
        self.setWindowOpacity(0.95)

        # 设置窗口位置
        self._set_position()

        # 创建UI
        self._create_ui()

        # 启动定时器更新会话列表
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_sessions)
        self.update_timer.start(1000)  # 每秒更新

        # 启动Socket服务器
        self.socket_thread = threading.Thread(target=self._run_socket_server, daemon=True)
        self.socket_thread.start()

    def _create_ui(self):
        """创建UI布局"""
        # 加载QSS样式表
        qss_path = os.path.join(os.path.dirname(__file__), 'styles', 'session_list.qss')
        if os.path.exists(qss_path):
            with open(qss_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())

        central_widget = QWidget()
        central_widget.setObjectName("mainContainer")
        central_widget.setStyleSheet("background-color: rgba(35, 35, 35, 240); border-radius: 16px;")
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题栏
        title_bar = self._create_title_bar()
        layout.addWidget(title_bar)

        # 会话列表区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("scrollArea")
        self.scroll_area.setWidgetResizable(True)

        self.session_container = QWidget()
        self.session_container.setObjectName("sessionContainer")
        self.session_layout = QVBoxLayout(self.session_container)
        self.session_layout.setContentsMargins(10, 10, 10, 10)
        self.session_layout.setSpacing(8)
        self.session_layout.addStretch()

        self.scroll_area.setWidget(self.session_container)
        layout.addWidget(self.scroll_area)

    def _create_title_bar(self) -> QWidget:
        """创建标题栏"""
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("background-color: rgba(60, 60, 60, 255); border-top-left-radius: 15px; border-top-right-radius: 15px;")
        title_bar.setCursor(Qt.PointingHandCursor)
        # 保存title_bar引用以便在鼠标事件中识别
        self.title_bar = title_bar

        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(15, 0, 15, 0)

        self.title_label = QLabel("📋 等待回复 (0)")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setStyleSheet("color: white; font-size: 13px; font-weight: bold; background-color: transparent;")
        layout.addWidget(self.title_label, alignment=Qt.AlignVCenter)

        layout.addStretch()

        self.collapse_btn = QPushButton("▼")
        self.collapse_btn.setObjectName("collapseButton")
        self.collapse_btn.setFixedSize(24, 24)
        self.collapse_btn.setStyleSheet("background-color: transparent; color: rgba(255, 255, 255, 180); border: none; font-size: 12px;")
        self.collapse_btn.clicked.connect(self._toggle_collapse)
        layout.addWidget(self.collapse_btn, alignment=Qt.AlignVCenter)

        # 呼吸动画定时器
        self.glow_timer = QTimer()
        self.glow_timer.timeout.connect(self._update_glow_effect)

        return title_bar

    def _toggle_collapse(self):
        """切换折叠/展开状态"""
        self.is_collapsed = not self.is_collapsed

        if self.is_collapsed:
            self.collapse_btn.setText("▲")
            self.scroll_area.hide()
            self.setFixedHeight(40)
            self.setWindowOpacity(0.5)
        else:
            self.collapse_btn.setText("▼")
            self.scroll_area.show()
            self.setFixedHeight(self.expanded_height)
            self.setWindowOpacity(1.0)

    def _update_glow_effect(self):
        """更新呼吸发光效果"""
        self.glow_phase = (self.glow_phase + 2) % 100

        import math
        alpha = int(255 * abs(math.sin(self.glow_phase * math.pi / 100)))

        self.title_bar.setStyleSheet(f"""
            QWidget#titleBar {{
                background-color: rgba(60, 60, 60, 255);
                border-top-left-radius: 15px;
                border-top-right-radius: 15px;
                border: 3px solid rgba(0, 200, 80, {alpha});
            }}
            QLabel#titleLabel {{
                color: white;
                font-size: 13px;
                font-weight: bold;
                background-color: transparent;
                border: none;
            }}
            QPushButton#collapseButton {{
                background-color: transparent;
                color: rgba(255, 255, 255, 180);
                border: none;
                font-size: 12px;
            }}
        """)

    def _create_session_item(self, session: Dict) -> QWidget:
        """创建会话项"""
        item = QWidget()
        item.setObjectName("sessionCard")
        item.setAttribute(Qt.WA_Hover, True)  # 启用hover事件
        item.setCursor(Qt.PointingHandCursor)  # 鼠标指针变为手型
        is_new = session.get('is_new', False)
        border_color = "#4CAF50" if is_new else "rgba(255, 255, 255, 10)"
        hover_border = "#66BB6A" if is_new else "rgba(255, 255, 255, 25)"
        # 使用精确选择器，包含hover效果
        item.setStyleSheet(f"""
            QWidget#sessionCard {{
                background-color: rgba(60, 60, 60, 200);
                border-radius: 8px;
                border: 1px solid {border_color};
            }}
            QWidget#sessionCard:hover {{
                background-color: rgba(75, 75, 75, 230);
                border: 1px solid {hover_border};
            }}
        """)

        # 设置鼠标点击事件，使用request_id而非session副本
        request_id = session.get('request_id')
        item.mousePressEvent = lambda event, rid=request_id: self._on_session_clicked(rid)

        layout = QVBoxLayout(item)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        # 第一行：项目名称 + 关闭按钮
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        # 项目名称
        project_path = session.get('project_path', '')
        project_name = os.path.basename(project_path) if project_path else '未知'
        if len(project_name) > 25:
            project_name = project_name[:23] + ".."
        project_label = QLabel(f"📁 项目: {project_name}")
        project_label.setStyleSheet("color: #FF9800; font-size: 11px; background-color: transparent;")
        header_layout.addWidget(project_label)

        header_layout.addStretch()

        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(18, 18)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888;
                border: none;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ff5555;
            }
        """)
        close_btn.clicked.connect(lambda checked, rid=request_id: self._on_close_clicked(rid))
        header_layout.addWidget(close_btn)

        layout.addWidget(header_widget)

        # 工作空间名称
        workspace = session.get('workspace_id') or session.get('work_title', '未知')
        workspace_label = QLabel(f"📦 工作空间: {workspace}")
        workspace_label.setStyleSheet("color: #4CAF50; font-size: 11px; background-color: transparent;")
        workspace_label.setMaximumWidth(260)
        font_metrics = workspace_label.fontMetrics()
        elided_text = font_metrics.elidedText(f"📦 工作空间: {workspace}", Qt.ElideRight, 255)
        workspace_label.setText(elided_text)
        layout.addWidget(workspace_label)

        # 阶段信息
        stage = session.get('stage', '未知')
        stage_label = QLabel(f"📍 阶段: {stage}")
        stage_label.setStyleSheet("color: #64B5F6; font-size: 11px; background-color: transparent;")
        layout.addWidget(stage_label)

        # 对话标题
        conversation = session.get('session_title') or session.get('work_title', '无标题')
        conversation_label = QLabel(f"💬 对话: {conversation}")
        conversation_label.setStyleSheet("color: white; font-size: 11px; background-color: transparent;")
        conversation_label.setMaximumWidth(260)
        font_metrics = conversation_label.fontMetrics()
        elided_text = font_metrics.elidedText(f"💬 对话: {conversation}", Qt.ElideRight, 255)
        conversation_label.setText(elided_text)
        layout.addWidget(conversation_label)

        # 进度条和计时
        elapsed = session.get('elapsed_time', 0)
        timeout = session.get('timeout', 3600)
        progress = min(int((elapsed / timeout) * 100), 100)

        progress_container = QWidget()
        progress_container.setStyleSheet("background-color: transparent;")
        progress_layout = QHBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 2, 0, 0)
        progress_layout.setSpacing(8)

        progress_bar = QProgressBar()
        progress_bar.setMaximum(100)
        progress_bar.setValue(progress)
        progress_bar.setTextVisible(False)
        progress_bar.setFixedHeight(4)
        progress_bar.setStyleSheet("""
            QProgressBar { background-color: rgba(255, 255, 255, 10); border: none; border-radius: 2px; }
            QProgressBar::chunk { background-color: #4CAF50; border-radius: 2px; }
        """)
        progress_layout.addWidget(progress_bar)

        time_label = QLabel(f"{elapsed // 60}:{elapsed % 60:02d}")
        time_label.setStyleSheet("color: rgba(255, 255, 255, 180); font-size: 10px; background-color: transparent;")
        time_label.setFixedWidth(35)
        progress_layout.addWidget(time_label)

        layout.addWidget(progress_container)

        return item

    def _format_time(self, seconds: int) -> str:
        """格式化时间显示"""
        if seconds < 60:
            return f"{seconds}秒"
        else:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}分{secs}秒"

    def _on_session_clicked(self, request_id: str):
        """处理会话项点击事件"""
        # 检查是否已在处理中，防止重复点击
        with self.sessions_lock:
            if request_id not in self.sessions:
                print(f"会话 {request_id} 不存在")
                return
            if self.sessions[request_id].get('is_processing'):
                print(f"会话 {request_id} 已在处理中，忽略重复点击")
                return
            self.sessions[request_id]['is_processing'] = True
            self.sessions[request_id]['is_new'] = False
            # 获取会��数据的副本
            session = self.sessions[request_id].copy()

        print(f"点击会话: {request_id}")

        # 在新线程中启动FeedbackUI
        threading.Thread(
            target=self._launch_feedback_ui,
            args=(session,),
            daemon=True
        ).start()

    def _on_close_clicked(self, request_id: str):
        """处理关闭按钮点击，发送STOP消息"""
        with self.sessions_lock:
            if request_id not in self.sessions:
                return
            session = self.sessions[request_id].copy()

            # 关闭对应的FeedbackUI进程（如果存在）
            if request_id in self.feedback_processes:
                try:
                    process = self.feedback_processes[request_id]
                    process.terminate()
                    del self.feedback_processes[request_id]
                except Exception:
                    pass

        # 记录用户主动关闭状态
        session_id = session.get('session_id')
        project_path = session.get('project_path')
        if session_id and SessionManager:
            try:
                manager = SessionManager(session_id=session_id, project_path=project_path)
                manager.mark_user_closed_by_button(session_id)
            except Exception:
                pass

        # 发送STOP消息
        result = {
            'interactive_feedback': 'STOP!请立即停止任何工作，不要再调用任何工具、回复任何消息。STOP!',
            'images': []
        }
        self.send_response(request_id, result)

    def _launch_feedback_ui(self, session: Dict):
        """启动FeedbackUI子进程"""
        try:
            request_id = session.get('request_id')

            # 创建临时文件接收结果
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pkl') as f:
                output_file = f.name

            # 构建FeedbackUI启动命令
            feedback_script = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'feedback_ui.py'
            )

            # 构建命令行参数
            cmd = [
                sys.executable,
                feedback_script,
                '--prompt', session.get('message', ''),
                '--project-path', session.get('project_path', ''),
                '--work-title', session.get('work_title', ''),
                '--timeout', str(session.get('timeout', 3600)),
                '--output-file', output_file,
                '--skip-init-check'
            ]

            # 添加可选参数
            if session.get('session_id'):
                cmd.extend(['--session-id', session.get('session_id')])

            if session.get('predefined_options'):
                options_str = '|||'.join(session.get('predefined_options'))
                cmd.extend(['--predefined-options', options_str])

            if session.get('files'):
                files_str = '|||'.join(session.get('files'))
                cmd.extend(['--files', files_str])

            if session.get('workspace_id'):
                cmd.extend(['--workspace-id', session.get('workspace_id')])

            print(f"启动FeedbackUI: {' '.join(cmd)}")

            # 启动子进程
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # 保存进程引用，以便可以从外部终止
            with self.sessions_lock:
                self.feedback_processes[request_id] = process

            # 等待子进程完成
            process.wait()

            # 清理进程引用
            with self.sessions_lock:
                if request_id in self.feedback_processes:
                    del self.feedback_processes[request_id]

            # 读取结果
            result = None
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'rb') as f:
                        result = pickle.load(f)
                    os.unlink(output_file)
                except Exception as e:
                    print(f"读取结果文件失败: {e}")

            # 发送结果给MCP服务器
            if result:
                self.send_response(request_id, result)
            else:
                # 用户关闭了窗口，不发送响应，保留会话项
                print(f"用户关闭了FeedbackUI，保留会话: {request_id}")
                # 重置处理状态，允许再次点击
                with self.sessions_lock:
                    if request_id in self.sessions:
                        self.sessions[request_id]['is_processing'] = False

        except Exception as e:
            print(f"启动FeedbackUI失败: {e}")
            import traceback
            traceback.print_exc()
            # 异常时也重置处理状态
            with self.sessions_lock:
                if request_id in self.sessions:
                    self.sessions[request_id]['is_processing'] = False

    def _run_socket_server(self):
        """运行Socket服务器"""
        # 创建TCP Socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.SOCKET_HOST, self.SOCKET_PORT))
        server_socket.listen(5)
        print(f"Socket服务器启动: {self.SOCKET_HOST}:{self.SOCKET_PORT}")

        while True:
            try:
                client_socket, _ = server_socket.accept()
                # 为每个连接创建新线程处理
                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket,),
                    daemon=True
                ).start()
            except Exception as e:
                print(f"Socket服务器错误: {e}")
                break

    def _handle_client(self, client_socket: socket.socket):
        """处理客户端请求"""
        try:
            # 接收数据
            data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                # 简单判断：如果收到完整JSON（以}结尾），则停止接收
                try:
                    json.loads(data.decode('utf-8'))
                    break
                except:
                    continue

            if not data:
                return

            # 解析请求
            request = json.loads(data.decode('utf-8'))
            action = request.get('action')

            if action == 'add_session':
                self._handle_add_session(request, client_socket)
            else:
                # 未知操作
                response = {
                    "request_id": request.get('request_id'),
                    "status": "error",
                    "error": f"Unknown action: {action}"
                }
                client_socket.sendall(json.dumps(response).encode('utf-8'))
                client_socket.close()

        except Exception as e:
            print(f"处理客户端请求失败: {e}")
            try:
                client_socket.close()
            except:
                pass

    def _handle_add_session(self, request: Dict, client_socket: socket.socket):
        """处理添加会话请求"""
        request_id = request.get('request_id')

        with self.sessions_lock:
            # 保存会话数据
            self.sessions[request_id] = {
                'request_id': request_id,
                'session_id': request.get('session_id'),
                'project_path': request.get('project_path'),
                'work_title': request.get('work_title'),
                'message': request.get('message'),
                'predefined_options': request.get('predefined_options', []),
                'files': request.get('files', []),
                'timeout': request.get('timeout', 3600),
                'start_time': time.time(),
                'elapsed_time': 0,
                'workspace_id': request.get('workspace_id'),
                'stage': request.get('stage'),
                'session_title': request.get('session_title'),
                'is_new': True
            }

            # 保存socket连接
            self.session_sockets[request_id] = client_socket

        print(f"添加会话: {request_id} - {request.get('work_title')}")

    def add_session(self, request_id: str, session_data: Dict):
        """添加会话（供外部调用）"""
        with self.sessions_lock:
            self.sessions[request_id] = session_data

    def remove_session(self, request_id: str):
        """移除会话"""
        with self.sessions_lock:
            if request_id in self.sessions:
                del self.sessions[request_id]
            if request_id in self.session_sockets:
                try:
                    self.session_sockets[request_id].close()
                except:
                    pass
                del self.session_sockets[request_id]

    def get_session(self, request_id: str) -> Optional[Dict]:
        """查询会话"""
        with self.sessions_lock:
            return self.sessions.get(request_id)

    def send_response(self, request_id: str, result: Dict):
        """发送响应给MCP Server"""
        with self.sessions_lock:
            if request_id not in self.session_sockets:
                print(f"未找到会话socket: {request_id}")
                # 清理会话，确保从列表中移除
                if request_id in self.sessions:
                    del self.sessions[request_id]
                return False

            client_socket = self.session_sockets[request_id]

            try:
                response = {
                    "request_id": request_id,
                    "status": "success",
                    "result": result
                }
                client_socket.sendall(json.dumps(response).encode('utf-8'))
                client_socket.close()

                # 清理会话
                del self.session_sockets[request_id]
                if request_id in self.sessions:
                    del self.sessions[request_id]

                return True
            except Exception as e:
                print(f"发送响应失败: {e}")
                # 发送失败也要清理会话
                if request_id in self.session_sockets:
                    del self.session_sockets[request_id]
                if request_id in self.sessions:
                    del self.sessions[request_id]
                return False

    def _update_sessions(self):
        """更新会话列表"""
        try:
            with self.sessions_lock:
                # 更新每个会话的等待时间
                current_time = time.time()
                for session in self.sessions.values():
                    session['elapsed_time'] = int(current_time - session['start_time'])

                # 获取会话列表
                sessions = list(self.sessions.values())

            # 更新标题
            count = len(sessions)
            new_count = sum(1 for s in sessions if s.get('is_new', False))
            if new_count > 0:
                self.title_label.setText(f"📋 等待回复({count}) / 新反馈({new_count})")
                if not self.has_new_feedback:
                    self.has_new_feedback = True
                    self.glow_timer.start(50)
            else:
                self.title_label.setText(f"📋 等待回复 ({count})")
                if self.has_new_feedback:
                    self.has_new_feedback = False
                    self.glow_timer.stop()
                    self.glow_phase = 0
                    self.title_bar.setStyleSheet("""
                        QWidget#titleBar {
                            background-color: rgba(60, 60, 60, 255);
                            border-top-left-radius: 15px;
                            border-top-right-radius: 15px;
                        }
                        QLabel#titleLabel {
                            color: white;
                            font-size: 13px;
                            font-weight: bold;
                            background-color: transparent;
                            border: none;
                        }
                        QPushButton#collapseButton {
                            background-color: transparent;
                            color: rgba(255, 255, 255, 180);
                            border: none;
                            font-size: 12px;
                        }
                    """)

            # 清空现有会话项
            while self.session_layout.count() > 1:  # 保留最后的stretch
                item = self.session_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # 添加新会话项
            for session in sessions:
                session_item = self._create_session_item(session)
                self.session_layout.insertWidget(self.session_layout.count() - 1, session_item)

            # 如果没有会话，隐藏窗口
            if count == 0:
                self.hide()
            else:
                self.show()

        except Exception as e:
            print(f"更新会话列表失败: {e}")

    def _set_position(self):
        """设置窗口位置 - 屏幕右侧，距右边缘20px"""
        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()
            screen_x = screen_geometry.x()
            screen_y = screen_geometry.y()
        else:
            screen_width = 1920
            screen_height = 1080
            screen_x = 0
            screen_y = 0

        # 窗口尺寸
        window_width = 320
        window_height = 400
        margin = 20

        # 计算位置：右侧，垂直居中
        x = screen_x + screen_width - window_width - margin
        y = screen_y + (screen_height - window_height) // 2

        self.move(x, y)

    def mousePressEvent(self, event):
        """处理鼠标按下事件 - 记录起始状态"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.mouse_press_time = time.time()
            self.mouse_press_pos = event.globalPosition().toPoint()
            self.drag_start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件 - 拖动窗口"""
        if event.buttons() == Qt.LeftButton and self.mouse_press_pos:
            current_pos = event.globalPosition().toPoint()
            distance = (current_pos - self.mouse_press_pos).manhattanLength()
            # 移动距离超过5像素才开始拖动
            if distance > 5:
                self.dragging = True
                self.move(current_pos - self.drag_start_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件 - 判断点击或拖动"""
        if event.button() == Qt.LeftButton and self.mouse_press_pos:
            elapsed = time.time() - self.mouse_press_time
            current_pos = event.globalPosition().toPoint()
            distance = (current_pos - self.mouse_press_pos).manhattanLength()
            # 短按且移动距离小 = 点击，触发展开/收起
            if elapsed < 0.3 and distance < 5:
                # 检查点击位置是否在标题栏区域
                title_bar_rect = self.title_bar.geometry()
                click_pos = event.position().toPoint()
                if click_pos.y() < title_bar_rect.height():
                    self._toggle_collapse()
        self.dragging = False
        self.mouse_press_pos = None
        event.accept()

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止定时器
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()

        # 清理Socket连接
        with self.sessions_lock:
            for client_socket in self.session_sockets.values():
                try:
                    client_socket.close()
                except:
                    pass
            self.session_sockets.clear()
            self.sessions.clear()


        event.accept()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = SessionListUI()
    window.show()
    sys.exit(app.exec())
