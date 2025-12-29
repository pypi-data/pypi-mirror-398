#!/usr/bin/env python3
"""
Stop Hook处理脚本
智能处理stop事件，避免死循环
"""
import sys
import json
import os
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from session_manager import SessionManager
from context_formatter import format_for_stop_hook


def main():
    """主函数"""
    try:
        # 从stdin读取JSON输入
        input_data = json.load(sys.stdin)

        # 提取关键信息
        session_id = input_data.get('session_id', '')
        stop_hook_active = input_data.get('stop_hook_active', False)

        # 获取项目路径
        project_path = os.getcwd()

        # 创建会话管理器(传入project_path)
        manager = SessionManager(session_id=session_id, project_path=project_path)

        # 决策逻辑
        if session_id:
            # 1. 检查用户是否点击关闭按钮
            if manager.is_user_closed_by_button(session_id):
                # 用户主动点击关闭，完全不提示（静默允许停止）
                # 🔧 立即清除状态,避免死循环
                manager.clear_session(session_id)
                return 0

            # 2. 检查是否超时关闭
            if manager.is_timeout_closed(session_id):
                # 超时关闭场景，最多提示2次
                current_block_count = manager.get_block_count(session_id)
                MAX_BLOCK_COUNT = 2

                if current_block_count >= MAX_BLOCK_COUNT:
                    # 超过最大阻止次数，允许停止以避免死循环
                    manager.clear_session(session_id)
                    return 0

                # 未超过2次，继续提示并增加计数
                manager.increment_block_count(session_id)
            else:
                # 3. 正常场景（非关闭状态），重置计数
                # 这样每次正常的stop hook都会重新开始计数
                if manager.get_block_count(session_id) > 0:
                    manager.clear_session(session_id)

        # 4. 默认行为：阻止停止并提示使用feedback工具
        # 使用新的格式化上下文信息
        if session_id:
            reason_text = format_for_stop_hook(session_id, project_path)
        else:
            reason_text = "请你调用 feedback mcp tool 向用户反馈/请示。示例：使用 mcp__feedback__feedback 工具向用户汇报当前工作进度、完成状态或请求下一步指示。"

        result = {
            "decision": "block",
            "reason": reason_text
        }
        print(json.dumps(result, ensure_ascii=False))
        return 0

    except Exception as e:
        # 发生错误时，默认允许停止（避免卡死）
        error_result = {
            "decision": "approve",
            "reason": f"Hook处理出错: {str(e)}"
        }
        print(json.dumps(error_result, ensure_ascii=False), file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())