"""
选项卡基础类

定义所有选项卡的通用接口和行为。
"""

from abc import ABC, abstractmethod, ABCMeta
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject


class BaseTabMeta(type(QWidget), ABCMeta):
    """解决QWidget和ABC的元类冲突"""
    pass


class BaseTab(QWidget, ABC, metaclass=BaseTabMeta):
    """选项卡基础类
    
    所有选项卡都应该继承此类，并实现_setup_ui方法。
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    @abstractmethod
    def _setup_ui(self):
        """子类必须实现的UI创建方法"""
        pass
    
    def refresh_data(self):
        """刷新数据的通用方法，子类可以重写"""
        pass 