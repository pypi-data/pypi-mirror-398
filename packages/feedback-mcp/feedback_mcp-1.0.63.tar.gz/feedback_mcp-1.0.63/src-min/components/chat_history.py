"""
聊天历史记录管理模块

功能：
1. 保存用户输入的聊天内容
2. 加载和显示历史记录
3. 提供弹窗方式显示历史记录
4. 支持插入和复制功能
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QPoint

# 导入历史记录弹窗组件
try:
    from .history_popup import HistoryPopup
    HISTORY_POPUP_AVAILABLE = True
except ImportError:
    try:
        from history_popup import HistoryPopup
        HISTORY_POPUP_AVAILABLE = True
    except ImportError:
        HISTORY_POPUP_AVAILABLE = False
        print("Warning: HistoryPopup component not available")


class ChatHistoryManager:
    """聊天历史记录管理器"""
    
    def __init__(self, project_path: Optional[str] = None, session_id: Optional[str] = None):
        self.project_path = project_path
        self.session_id = session_id
    
    def get_history_file_path(self) -> Optional[str]:
        """获取历史记录文件路径"""
        # 如果没有session_id,返回None
        if not self.session_id:
            return None

        if self.project_path:
            return os.path.join(self.project_path, '.workspace', 'chat_history', f'{self.session_id}.json')
        else:
            # 如果没有项目路径，使用脚本目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(script_dir, '..', '.workspace', 'chat_history', f'{self.session_id}.json')
    
    def save_to_history(self, content: str) -> bool:
        """保存内容到历史记录

        Args:
            content: 要保存的内容

        Returns:
            bool: 保存是否成功
        """
        if not content.strip():
            return False

        try:
            # 获取历史记录文件路径
            history_file = self.get_history_file_path()

            # 如果没有session_id,静默跳过
            if not history_file:
                return False

            # 读取完整的文件数据
            file_data = {}
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # 新格式：{'dialogues': [...], 'control': {...}}
                    if isinstance(data, dict) and 'dialogues' in data:
                        file_data = data
                    # 旧格式数组，转换为新格式
                    elif isinstance(data, list):
                        file_data = {
                            'dialogues': [record for record in data if isinstance(record, dict) and record.get('type') != 'stop_hook_status']
                        }
                    else:
                        file_data = {'dialogues': []}
            else:
                # 文件不存在，初始化为新格式
                file_data = {'dialogues': []}

            # 添加新记录到dialogues数组
            new_record = {
                'content': content.strip(),
                'timestamp': datetime.now().isoformat(),
                'time_display': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # 确保dialogues字段存在
            if 'dialogues' not in file_data:
                file_data['dialogues'] = []

            file_data['dialogues'].append(new_record)

            # 保存完整的文件数据
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"保存历史记录失败: {e}")
            return False
    
    def load_history_from_file(self) -> List[Dict]:
        """从文件加载历史记录（兼容旧格式和新格式）"""
        try:
            history_file = self.get_history_file_path()

            # 如果没有session_id,返回空列表
            if not history_file:
                return []

            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # 新格式：{'dialogues': [...], 'control': {...}}
                    if isinstance(data, dict) and 'dialogues' in data:
                        # 返回dialogues数组
                        return data.get('dialogues', [])

                    # 旧格式数组
                    if isinstance(data, list):
                        # 过滤掉control记录，保留对话记录
                        return [record for record in data if isinstance(record, dict) and record.get('type') != 'stop_hook_status']

                    return []
            return []
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            return []
    
    def get_recent_history(self, count: Optional[int] = None) -> List[Dict]:
        """获取最近的历史记录

        Args:
            count: 获取记录数量，如果为None则返回所有记录

        Returns:
            List[Dict]: 历史记录列表
        """
        history = self.load_history_from_file()
        if count is None:
            return history  # 返回所有历史记录
        return history[-count:]

    def get_agent_records_after_last_user(self) -> List[Dict]:
        """获取最后一条用户消息之后的所有 agent 记录"""
        history = self.load_history_from_file()

        # 找到最后一条用户消息的索引
        last_user_idx = -1
        for i, record in enumerate(history):
            if record.get('role') == 'user' or 'messages' in record:
                last_user_idx = i

        # 返回之后的所有 agent 记录
        if last_user_idx >= 0:
            return [r for r in history[last_user_idx + 1:] if r.get('role') == 'agent']

        # 如果没有用户消息，返回所有 agent 记录
        return [r for r in history if r.get('role') == 'agent']

    def _get_draft_file_path(self) -> Optional[str]:
        """获取草稿文件路径（独立文件，避免被其他代码覆盖）"""
        if not self.project_path or not self.session_id:
            return None
        return os.path.join(self.project_path, '.workspace', 'chat_history', f'{self.session_id}_draft.json')

    def get_latest_draft(self) -> Optional[dict]:
        """获取最近的未提交草稿"""
        try:
            draft_file = self._get_draft_file_path()
            if not draft_file or not os.path.exists(draft_file):
                return None

            with open(draft_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def save_draft(self, text: str) -> bool:
        """保存草稿到独立文件"""
        try:
            draft_file = self._get_draft_file_path()
            if not draft_file:
                return False

            os.makedirs(os.path.dirname(draft_file), exist_ok=True)
            with open(draft_file, 'w', encoding='utf-8') as f:
                json.dump({'text': text}, f, ensure_ascii=False)

            return True
        except Exception:
            return False

    def clear_draft(self) -> bool:
        """删除草稿文件"""
        try:
            draft_file = self._get_draft_file_path()
            if draft_file and os.path.exists(draft_file):
                os.remove(draft_file)
            return True
        except Exception:
            return False
    
    def show_history_dialog(self, parent=None) -> None:
        """显示历史记录弹窗
        
        Args:
            parent: 父窗口
        """
        try:
            # 加载历史记录
            history = self.get_recent_history()
            
            if not history:
                QMessageBox.information(parent, "历史记录", "暂无历史记录")
                return
            
            # 检查弹窗组件是否可用
            if not HISTORY_POPUP_AVAILABLE:
                QMessageBox.critical(parent, "错误", "历史记录弹窗组件不可用")
                return
            
            # 显示历史记录弹窗
            self._show_history_popup(parent, history)
            
        except Exception as e:
            print(f"显示历史记录失败: {e}")
            QMessageBox.critical(parent, "错误", f"显示历史记录失败: {str(e)}")
    
    def _show_history_popup(self, parent, history: List[Dict]):
        """显示历史记录弹窗"""
        try:
            # 创建弹窗
            popup = HistoryPopup(parent)
            
            # 设置历史记录数据
            popup.set_history_records(history, parent)
            
            # 连接信号
            popup.content_inserted.connect(lambda content: print(f"✅ 内容已插入: {content[:50]}..."))
            popup.content_copied.connect(lambda content: print(f"✅ 内容已复制: {content[:50]}..."))
            popup.popup_closed.connect(lambda: print("📝 历史记录弹窗已关闭"))
            
            # 计算弹窗位置（在历史按钮附近）
            if hasattr(parent, 'history_button'):
                button = parent.history_button
                # 获取按钮的全局位置
                button_pos = button.mapToGlobal(button.rect().bottomLeft())
                # 稍微偏移一下位置
                popup_pos = QPoint(button_pos.x() - 200, button_pos.y() + 5)
            else:
                # 如果找不到按钮，在父窗口中央显示
                if parent:
                    parent_rect = parent.geometry()
                    popup_pos = QPoint(
                        parent_rect.x() + parent_rect.width() // 2 - 250,
                        parent_rect.y() + parent_rect.height() // 2 - 200
                    )
                else:
                    popup_pos = QPoint(100, 100)
            
            # 显示弹窗
            popup.show_at_position(popup_pos)
            
        except Exception as e:
            print(f"显示历史记录弹窗失败: {e}")
            QMessageBox.critical(parent, "错误", f"显示历史记录弹窗失败: {str(e)}") 