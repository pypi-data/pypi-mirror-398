#!/usr/bin/env python3
"""
会话状态管理器
用于管理stop hook和feedback UI之间的会话状态，避免死循环
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

class SessionManager:
    """管理会话状态，避免stop hook死循环

    状态保存在 .workspace/chat_history/{session_id}.json 中
    """

    def __init__(self, session_id: Optional[str] = None, project_path: Optional[str] = None):
        """初始化会话管理器

        Args:
            session_id: 会话ID
            project_path: 项目路径，用于定位.workspace目录
        """
        self.session_id = session_id
        self.project_path = project_path or os.getcwd()

        # 不再加载所有sessions，改为按需加载单个session
        # self.sessions = self._load_sessions()
        # self._cleanup_old_sessions()

    def _get_chat_history_path(self, session_id: str) -> Path:
        """获取指定session的chat_history文件路径

        Args:
            session_id: 会话ID

        Returns:
            Path: chat_history文件路径
        """
        workspace_dir = Path(self.project_path) / '.workspace' / 'chat_history'
        workspace_dir.mkdir(parents=True, exist_ok=True)
        return workspace_dir / f"{session_id}.json"

    def _load_session_data(self, session_id: str) -> list:
        """加载指定session的chat_history数据（兼容旧格式）

        Args:
            session_id: 会话ID

        Returns:
            list: chat_history数据数组（内部格式，用于兼容现有代码）
        """
        chat_file = self._get_chat_history_path(session_id)
        if not chat_file.exists():
            return []

        try:
            with open(chat_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # 新格式：{'dialogues': [...], 'control': {...}}
                if isinstance(data, dict) and 'dialogues' in data:
                    # 转换为内部数组格式
                    result = []

                    # 添加对话记录（自动添加type字段以兼容现有代码）
                    for dialogue in data.get('dialogues', []):
                        dialogue_with_type = dialogue.copy()
                        dialogue_with_type['type'] = 'dialogue'
                        result.append(dialogue_with_type)

                    # 添加control记录
                    if 'control' in data and data['control']:
                        result.append(data['control'])

                    return result

                # 旧格式：直接返回数组
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, IOError):
            return []

    def _save_session_data(self, session_id: str, data: list):
        """保存指定session的chat_history数据（新格式）

        Args:
            session_id: 会话ID
            data: chat_history数据数组
        """
        chat_file = self._get_chat_history_path(session_id)
        try:
            # 转换为新格式：dialogues数组
            new_format_data = {
                'dialogues': []
            }

            # 过滤出对话项
            for item in data:
                if isinstance(item, dict):
                    # 保留 agent 记录（直接添加）
                    if item.get('role') == 'agent':
                        new_format_data['dialogues'].append(item)
                        continue

                    item_type = item.get('type')
                    if item_type == 'dialogue':
                        # 创建新格式的对话项（移除type字段）
                        dialogue = {
                            'timestamp': item.get('timestamp', ''),
                            'time_display': item.get('time_display', ''),
                            'messages': item.get('messages', [])
                        }
                        new_format_data['dialogues'].append(dialogue)
                    elif item_type == 'stop_hook_status':
                        # 保留control字段（如果存在）
                        if 'control' not in new_format_data:
                            new_format_data['control'] = item

            with open(chat_file, 'w', encoding='utf-8') as f:
                json.dump(new_format_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving session data: {e}", file=sys.stderr)

    def _get_stop_hook_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取session的stop_hook状态

        Args:
            session_id: 会话ID

        Returns:
            Optional[Dict]: stop_hook状态数据，如果不存在则返回None
        """
        data = self._load_session_data(session_id)
        # 在数组末尾查找stop_hook_status元素
        for item in reversed(data):
            if isinstance(item, dict) and item.get('type') == 'stop_hook_status':
                return item
        return None

    def _set_stop_hook_status(self, session_id: str, status: str, action: Optional[str] = None):
        """设置session的stop_hook状态

        Args:
            session_id: 会话ID
            status: 状态值
            action: 动作描述
        """
        data = self._load_session_data(session_id)

        # 移除旧的stop_hook_status元素
        data = [item for item in data if not (isinstance(item, dict) and item.get('type') == 'stop_hook_status')]

        # 添加新的stop_hook_status元素
        data.append({
            'type': 'stop_hook_status',
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'last_action': action or status
        })

        self._save_session_data(session_id, data)

    def _clear_stop_hook_status(self, session_id: str):
        """清除session的stop_hook状态

        Args:
            session_id: 会话ID
        """
        data = self._load_session_data(session_id)
        # 移除stop_hook_status元素
        data = [item for item in data if not (isinstance(item, dict) and item.get('type') == 'stop_hook_status')]
        self._save_session_data(session_id, data)

    def get_session_status(self, session_id: str) -> Optional[str]:
        """获取会话状态

        Args:
            session_id: 会话ID

        Returns:
            会话状态: "user_closed_by_button", "timeout_closed", "active" 或 None
        """
        status_data = self._get_stop_hook_status(session_id)
        if status_data:
            return status_data.get("status")
        return None

    def set_session_status(self, session_id: str, status: str, action: Optional[str] = None):
        """设置会话状态

        Args:
            session_id: 会话ID
            status: 状态 ("user_closed_by_button", "timeout_closed", "active")
            action: 最后的动作描述
        """
        self._set_stop_hook_status(session_id, status, action)

    def is_feedback_closed(self, session_id: str) -> bool:
        """检查会话是否因用户关闭feedback而结束

        Args:
            session_id: 会话ID

        Returns:
            True如果用户主动关闭了feedback窗口
        """
        status = self.get_session_status(session_id)
        return status == "user_closed"

    def mark_feedback_closed(self, session_id: str):
        """标记feedback被用户关闭（通用方法，保留向后兼容）

        Args:
            session_id: 会话ID
        """
        self.set_session_status(session_id, "user_closed", "feedback_window_closed_by_user")

    def mark_user_closed_by_button(self, session_id: str):
        """标记用户点击关闭按钮

        Args:
            session_id: 会话ID
        """
        self.set_session_status(session_id, "user_closed_by_button", "user_clicked_close_button")

    def mark_timeout_closed(self, session_id: str):
        """标记超时自动关闭

        Args:
            session_id: 会话ID
        """
        self.set_session_status(session_id, "timeout_closed", "feedback_timeout_auto_closed")

    def is_user_closed_by_button(self, session_id: str) -> bool:
        """检查是否用户点击关闭按钮

        Args:
            session_id: 会话ID

        Returns:
            True如果用户点击关闭按钮
        """
        status = self.get_session_status(session_id)
        return status == "user_closed_by_button"

    def is_timeout_closed(self, session_id: str) -> bool:
        """检查是否超时关闭

        Args:
            session_id: 会话ID

        Returns:
            True如果超时自动关闭
        """
        status = self.get_session_status(session_id)
        return status == "timeout_closed"

    def reset_on_feedback_show(self, session_id: str):
        """feedback展示时重置状态

        Args:
            session_id: 会话ID
        """
        # 清除所有状态
        self.clear_session(session_id)

    def get_block_count(self, session_id: str) -> int:
        """获取会话的阻止次数

        Args:
            session_id: 会话ID

        Returns:
            阻止次数
        """
        status_data = self._get_stop_hook_status(session_id)
        if status_data:
            return status_data.get("block_count", 0)
        return 0

    def increment_block_count(self, session_id: str) -> int:
        """增加会话的阻止次数

        Args:
            session_id: 会话ID

        Returns:
            更新后的阻止次数
        """
        status_data = self._get_stop_hook_status(session_id)
        if status_data:
            new_count = status_data.get("block_count", 0) + 1
            status_data["block_count"] = new_count
            status_data["timestamp"] = datetime.now().isoformat()

            # 更新到chat_history
            data = self._load_session_data(session_id)
            # 移除旧的stop_hook_status
            data = [item for item in data if not (isinstance(item, dict) and item.get('type') == 'stop_hook_status')]
            # 添加更新后的status
            data.append(status_data)
            self._save_session_data(session_id, data)
            return new_count
        else:
            # 首次创建
            self._set_stop_hook_status(session_id, "active", "block_count_increment")
            data = self._load_session_data(session_id)
            # 找到刚创建的status并设置block_count
            for item in reversed(data):
                if isinstance(item, dict) and item.get('type') == 'stop_hook_status':
                    item["block_count"] = 1
                    break
            self._save_session_data(session_id, data)
            return 1

    def clear_session(self, session_id: str):
        """清除会话状态

        Args:
            session_id: 会话ID
        """
        self._clear_stop_hook_status(session_id)


def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='管理会话状态')
    parser.add_argument('action', choices=['get', 'set', 'check', 'mark_closed', 'clear'],
                        help='要执行的操作')
    parser.add_argument('session_id', help='会话ID')
    parser.add_argument('--status', help='设置的状态 (用于set操作)')
    parser.add_argument('--state-file', help='状态文件路径')
    
    args = parser.parse_args()
    
    manager = SessionManager(args.state_file)
    
    if args.action == 'get':
        status = manager.get_session_status(args.session_id)
        print(status if status else "none")
        
    elif args.action == 'set':
        if not args.status:
            print("Error: --status required for set action", file=sys.stderr)
            sys.exit(1)
        manager.set_session_status(args.session_id, args.status)
        print(f"Session {args.session_id} status set to {args.status}")
        
    elif args.action == 'check':
        is_closed = manager.is_feedback_closed(args.session_id)
        print("closed" if is_closed else "active")
        sys.exit(0 if not is_closed else 1)
        
    elif args.action == 'mark_closed':
        manager.mark_feedback_closed(args.session_id)
        print(f"Session {args.session_id} marked as closed by user")
        
    elif args.action == 'clear':
        manager.clear_session(args.session_id)
        print(f"Session {args.session_id} cleared")


if __name__ == "__main__":
    main()