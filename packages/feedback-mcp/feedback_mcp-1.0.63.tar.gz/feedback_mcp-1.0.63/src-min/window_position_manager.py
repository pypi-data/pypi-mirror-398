"""
窗口位置管理器
用于管理多个 Feedback UI 窗口的位置，避免重叠
"""
import os
import json
import time
from typing import Tuple, List, Dict, Optional
from PySide6.QtGui import QGuiApplication


class WindowPositionManager:
    """管理多个窗口的位置，实现智能错位显示"""
    
    # 窗口位置记录文件
    POSITION_FILE = os.path.join(os.path.dirname(__file__), '.window_positions.json')
    
    # 窗口错位的偏移量
    OFFSET_X = 30  # 水平偏移
    OFFSET_Y = 30  # 垂直偏移
    MAX_CASCADE_COUNT = 10  # 最大级联数量
    
    # 窗口存活时间（秒），超过这个时间的记录会被清理
    WINDOW_TTL = 300  # 5分钟
    
    @classmethod
    def get_next_position(cls, window_type: str = 'main', default_x: int = None, default_y: int = None) -> Tuple[int, int]:
        """
        获取下一个窗口的位置
        
        Args:
            window_type: 窗口类型 ('main' 或 'compact')
            default_x: 默认 X 坐标
            default_y: 默认 Y 坐标
            
        Returns:
            (x, y) 坐标元组
        """
        # 清理过期的窗口记录
        cls._cleanup_old_positions()
        
        # 读取现有位置记录
        positions = cls._load_positions()
        
        # 获取当前窗口类型的记录
        type_positions = positions.get(window_type, [])
        
        # 获取屏幕信息
        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()
            screen_x = screen_geometry.x()
            screen_y = screen_geometry.y()
        else:
            # 默认屏幕尺寸
            screen_width = 1920
            screen_height = 1080
            screen_x = 0
            screen_y = 0
        
        # 计算基础位置
        if default_x is None or default_y is None:
            if window_type == 'compact':
                # 精简版默认在顶部居中
                base_x = screen_x + (screen_width - 250) // 2
                base_y = screen_y + 20
            else:
                # 主窗口默认在屏幕中央
                base_x = screen_x + (screen_width - 500) // 2
                base_y = screen_y + (screen_height - 900) // 2
        else:
            base_x = default_x
            base_y = default_y
        
        # 计算级联位置
        cascade_index = len(type_positions) % cls.MAX_CASCADE_COUNT
        
        # 计算最终位置
        final_x = base_x + (cascade_index * cls.OFFSET_X)
        final_y = base_y + (cascade_index * cls.OFFSET_Y)
        
        # 确保窗口不会超出屏幕边界
        window_width = 250 if window_type == 'compact' else 500
        window_height = 40 if window_type == 'compact' else 900
        
        # 调整 X 坐标
        if final_x + window_width > screen_x + screen_width:
            final_x = screen_x + screen_width - window_width - 20
        if final_x < screen_x:
            final_x = screen_x + 20
            
        # 调整 Y 坐标
        if final_y + window_height > screen_y + screen_height:
            final_y = screen_y + screen_height - window_height - 20
        if final_y < screen_y:
            final_y = screen_y + 20
        
        # 记录新位置
        cls._add_position(window_type, final_x, final_y)
        
        return (final_x, final_y)
    
    @classmethod
    def remove_position(cls, window_type: str, x: int, y: int):
        """
        移除窗口位置记录（窗口关闭时调用）
        
        Args:
            window_type: 窗口类型
            x: X 坐标
            y: Y 坐标
        """
        positions = cls._load_positions()
        
        if window_type in positions:
            # 移除匹配的位置记录
            positions[window_type] = [
                pos for pos in positions[window_type]
                if not (abs(pos['x'] - x) < 5 and abs(pos['y'] - y) < 5)
            ]
            
            # 如果该类型没有窗口了，删除键
            if not positions[window_type]:
                del positions[window_type]
            
            cls._save_positions(positions)
    
    @classmethod
    def _load_positions(cls) -> Dict[str, List[Dict]]:
        """加载位置记录"""
        if os.path.exists(cls.POSITION_FILE):
            try:
                with open(cls.POSITION_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    @classmethod
    def _save_positions(cls, positions: Dict[str, List[Dict]]):
        """保存位置记录"""
        try:
            with open(cls.POSITION_FILE, 'w') as f:
                json.dump(positions, f)
        except IOError:
            pass
    
    @classmethod
    def _add_position(cls, window_type: str, x: int, y: int):
        """添加位置记录"""
        positions = cls._load_positions()
        
        if window_type not in positions:
            positions[window_type] = []
        
        positions[window_type].append({
            'x': x,
            'y': y,
            'timestamp': time.time()
        })
        
        cls._save_positions(positions)
    
    @classmethod
    def _cleanup_old_positions(cls):
        """清理过期的位置记录"""
        positions = cls._load_positions()
        current_time = time.time()
        updated = False
        
        for window_type in list(positions.keys()):
            # 过滤掉过期的记录
            active_positions = [
                pos for pos in positions[window_type]
                if current_time - pos.get('timestamp', 0) < cls.WINDOW_TTL
            ]
            
            if len(active_positions) != len(positions[window_type]):
                updated = True
                if active_positions:
                    positions[window_type] = active_positions
                else:
                    del positions[window_type]
        
        if updated:
            cls._save_positions(positions)
    
    @classmethod
    def clear_all_positions(cls):
        """清除所有位置记录（用于调试）"""
        if os.path.exists(cls.POSITION_FILE):
            try:
                os.remove(cls.POSITION_FILE)
            except IOError:
                pass