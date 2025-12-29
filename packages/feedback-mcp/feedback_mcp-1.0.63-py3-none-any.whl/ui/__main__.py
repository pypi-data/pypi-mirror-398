"""
会话列表UI模块入口
支持: python -m src-min.ui (本地开发) 或 python -m ui (PyPI安装)
"""
import sys
from PySide6.QtWidgets import QApplication
from .session_list_ui import SessionListUI

def main():
    app = QApplication(sys.argv)
    window = SessionListUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
