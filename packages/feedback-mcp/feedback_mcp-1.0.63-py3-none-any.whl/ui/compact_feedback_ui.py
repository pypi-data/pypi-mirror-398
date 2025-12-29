"""
紧凑反馈界面 - 精简版反馈界面，只显示进度条和基本操作
"""
import os
import sys
from typing import Optional, List, TypedDict
# 添加路径以导入session_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from session_manager import SessionManager
except ImportError:
    SessionManager = None
try:
    from window_position_manager import WindowPositionManager
except ImportError:
    WindowPositionManager = None
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon, QGuiApplication

class FeedbackResult(TypedDict):
    interactive_feedback: str
    images: Optional[List[str]]  # Base64 encoded images


class CompactFeedbackUI(QMainWindow):
    """精简版反馈界面，只显示进度条和基本操作"""
    
    # 信号定义
    feedback_submitted = Signal(str, list)  # 反馈内容, 图片列表
    restore_main_ui = Signal()  # 恢复主界面
    
    def __init__(self, main_ui, timeout: int = 60, parent=None):
        super().__init__(parent)
        self.main_ui = main_ui
        self.timeout = timeout
        # 继承主界面的已过时间
        self.elapsed_time = getattr(main_ui, 'elapsed_time', 0)
        # 标记是否正在恢复主界面（用于区分关闭原因）
        self.is_restoring = False
        
        # 用于拖动窗口
        self.dragging = False
        self.drag_start_pos = None
        
        # 双击ESC关闭的计时器
        self.esc_timer = QTimer()
        self.esc_timer.setSingleShot(True)
        self.esc_timer.timeout.connect(self._reset_esc_count)
        self.esc_press_count = 0
        
        # 设置窗口属性 - 隐藏标题栏，设置圆角
        # 使用主窗口的work_title
        if hasattr(main_ui, 'work_title') and main_ui.work_title:
            self.setWindowTitle(main_ui.work_title)
        elif hasattr(main_ui, 'project_path') and main_ui.project_path:
            project_name = os.path.basename(os.path.normpath(main_ui.project_path))
            self.setWindowTitle(project_name)
        else:
            self.setWindowTitle("Feedback")
        
        # 隐藏标题栏和边框，保持置顶
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        # 设置窗口背景透明，让CSS圆角生效
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置固定尺寸
        self.setFixedSize(170, 60)
        
        # 设置窗口透明度
        self.setWindowOpacity(0.95)
        
        # 设置智能窗口位置（避免重叠）
        self._set_smart_position()
        
        # 创建UI
        self._create_compact_ui()
        
        # 精简版不启动自己的计时器，通过定时器从主界面同步时间
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self._sync_from_main)
        if self.timeout > 0:
            self.sync_timer.start(1000)  # 每秒同步一次
        
        # 设置快捷键
        self._setup_shortcuts()
    
    def _create_compact_ui(self):
        from PySide6.QtWidgets import QLabel
        from PySide6.QtCore import Qt
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 设置中央部件的背景和圆角
        central_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(43, 43, 43, 255);
                border-radius: 25px;
            }
        """)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(3)
        
        # 标题文字在上方
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 11px;
                background-color: transparent;
            }
        """)
        # 获取标题文本
        title_text = self._get_title_text()
        self.title_label.setText(title_text)
        layout.addWidget(self.title_label)
        
        # 进度条在下方，显示时间
        if self.timeout > 0:
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, self.timeout)
            self.progress_bar.setValue(self.elapsed_time)
            self.progress_bar.setTextVisible(True)  # 显示进度条内的时间
            self.progress_bar.setFormat(self._format_time(self.elapsed_time))
            self.progress_bar.setAlignment(Qt.AlignCenter)
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border-radius: 10px;
                    background-color: rgba(255, 255, 255, 30);
                    height: 16px;
                    border: none;
                    color: white;
                    font-size: 10px;
                    font-weight: 500;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 10px;
                }
            """)
            
            # 设置提示信息
            self.setToolTip("双击切换到完整版")
            
            layout.addWidget(self.progress_bar)
    
    def _sync_from_main(self):
        """从主界面同步时间"""
        if hasattr(self.main_ui, 'elapsed_time'):
            self.elapsed_time = self.main_ui.elapsed_time
            self._update_display()

    def _update_display(self):
        """更新显示（不增加时间，只更新显示）"""
        # 更新标题文字（如果需要）
        if hasattr(self, 'title_label'):
            title_text = self._get_title_text()
            self.title_label.setText(title_text)
        
        # 更新进度条的值和时间文字
        if hasattr(self, 'progress_bar'):
            if self.elapsed_time >= self.timeout:
                self.progress_bar.setValue(self.timeout)
            else:
                self.progress_bar.setValue(self.elapsed_time)
            # 更新进度条内的时间文字
            self.progress_bar.setFormat(self._format_time(self.elapsed_time))
    
    def _get_title_text(self) -> str:
        """获取标题文本"""
        # 优先使用work_title，其次是项目名称
        if hasattr(self.main_ui, 'work_title') and self.main_ui.work_title:
            title = self.main_ui.work_title
        elif hasattr(self.main_ui, 'project_path') and self.main_ui.project_path:
            title = os.path.basename(os.path.normpath(self.main_ui.project_path))
        else:
            title = "等待中"
        
        # 如果标题太长，适当截断
        if len(title) > 15:
            title = title[:13] + ".."
        
        return title
    
    def _format_time(self, seconds: int) -> str:
        """格式化时间显示"""
        if seconds < 60:
            return f"{seconds}s"
        else:
            minutes = seconds // 60
            return f"{minutes}m"
    
    def _set_smart_position(self):
        """设置智能窗口位置 - 靠右侧垂直排列"""
        # 获取屏幕信息
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
        window_width = 170
        window_height = 60
        margin = 0  # 紧贴右侧，无间隙
        spacing = 5  # 窗口间距
        start_y = 200  # 起始 Y 位置
        
        # 计算右侧位置（紧贴右边缘）
        x = screen_x + screen_width - window_width - margin
        
        if WindowPositionManager:
            try:
                # 获取已有的精简版窗口数量
                positions = WindowPositionManager._load_positions()
                compact_count = len(positions.get('compact', []))
                
                # 计算垂直位置（从 top 200px 开始向下排列）
                y = screen_y + start_y + (compact_count * (window_height + spacing))
                
                # 检查是否超出屏幕底部
                if y + window_height > screen_y + screen_height:
                    # 如果超出，从第二列开始
                    x -= (window_width + spacing)
                    y = screen_y + start_y
                
                self.move(x, y)
                # 保存位置记录
                WindowPositionManager._add_position('compact', x, y)
                self._window_position = (x, y)
            except Exception as e:
                print(f"设置精简版窗口位置失败: {e}")
                # 如果失败，使用默认位置
                self.move(x, screen_y + start_y)
        else:
            # 没有位置管理器时，直接放在右侧起始位置
            self.move(x, screen_y + start_y)
    
    def _restore_main_ui(self):
        """恢复到完整版界面"""
        # 停止精简版同步计时器
        if hasattr(self, 'sync_timer'):
            self.sync_timer.stop()
        
        # 标记正在恢复，避免closeEvent中停止主界面计时器
        self.is_restoring = True
        
        # 发送恢复信号
        self.restore_main_ui.emit()
        
        # 关闭精简版窗口
        self.close()
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件 - 开始拖动"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件 - 拖动窗口"""
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_start_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件 - 结束拖动"""
        self.dragging = False
        event.accept()
    
    def mouseDoubleClickEvent(self, event):
        """处理双击事件 - 切换到完整版"""
        if event.button() == Qt.LeftButton:
            self._restore_main_ui()
            event.accept()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 清理窗口位置记录
        if WindowPositionManager and hasattr(self, '_window_position'):
            try:
                x, y = self._window_position
                WindowPositionManager.remove_position('compact', x, y)
            except Exception:
                pass  # 静默处理错误
        
        # 停止同步计时器
        if hasattr(self, 'sync_timer'):
            self.sync_timer.stop()
        
        # 只有在非恢复状态下才处理关闭（避免意外操作主界面）
        if not getattr(self, 'is_restoring', False):
            # 停止主界面计时器
            if hasattr(self.main_ui, 'countdown_timer'):
                self.main_ui.countdown_timer.stop()
            
            # 如果主界面没有反馈结果，设置用户关闭窗口的结果
            if not getattr(self.main_ui, 'feedback_result', None):
                # 标记会话为用户关闭状态
                if SessionManager and hasattr(self.main_ui, 'session_id') and self.main_ui.session_id:
                    try:
                        session_manager = SessionManager()
                        session_manager.mark_feedback_closed(self.main_ui.session_id)
                    except Exception:
                        pass  # 静默处理错误
                
                self.main_ui.feedback_result = {
                    'content': [{"type": "text", "text": "STOP!请立即停止任何工作，不要再调用任何工具、回复任何消息。STOP!"}],
                    'images': []
                }
            
            # 关闭主界面
            self.main_ui.close()
        
        event.accept()
    
    def _setup_shortcuts(self):
        """设置快捷键"""
        from PySide6.QtGui import QShortcut, QKeySequence
        
        # Cmd+W 或 Ctrl+W 关闭窗口
        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self._handle_close_shortcut)
        
        # macOS 上的 Cmd+W
        import sys
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