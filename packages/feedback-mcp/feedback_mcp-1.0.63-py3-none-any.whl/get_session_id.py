#!/usr/bin/env python3
"""
获取当前Claude会话ID的辅助脚本
通过多种方式尝试获取session_id
"""
import os
import json
import glob
from pathlib import Path
from datetime import datetime, timedelta

def get_claude_session_id():
    """获取当前Claude会话ID"""
    
    # 方法1: 从环境变量获取
    session_id = os.environ.get('CLAUDE_SESSION_ID')
    if session_id:
        return session_id
    
    # 方法2: 从最新的transcript文件获取
    try:
        claude_dir = Path.home() / '.claude'
        projects_dir = claude_dir / 'projects'
        
        if projects_dir.exists():
            # 查找所有transcript文件
            transcript_files = []
            for project_dir in projects_dir.iterdir():
                if project_dir.is_dir():
                    jsonl_files = list(project_dir.glob('*.jsonl'))
                    transcript_files.extend(jsonl_files)
            
            if transcript_files:
                # 按修改时间排序，获取最新的
                latest_file = max(transcript_files, key=lambda f: f.stat().st_mtime)
                
                # 检查是否是最近24小时内的文件
                file_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
                if datetime.now() - file_time < timedelta(hours=24):
                    # 使用文件名作为session_id（去除.jsonl后缀）
                    session_id = latest_file.stem
                    return session_id
    except Exception:
        pass
    
    # 方法3: 从进程ID生成一个临时session_id
    # 这确保同一进程内的所有调用使用相同的session_id
    pid = os.getpid()
    return f"pid-{pid}-session"

if __name__ == "__main__":
    session_id = get_claude_session_id()
    print(session_id)