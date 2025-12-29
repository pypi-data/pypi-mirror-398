"""
Markdown显示组件

用于渲染和显示Markdown内容的只读文本框。
"""

import sys
import re
import markdown
import os

from PySide6.QtWidgets import QTextEdit, QDialog, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QPixmap, QMouseEvent, QTextDocument, QDesktopServices


class ImageViewerDialog(QDialog):
    """简单的图片查看对话框"""
    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("图片查看")
        self.setModal(True)

        layout = QVBoxLayout(self)
        label = QLabel()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # 限制最大尺寸为屏幕的80%
            screen = self.screen().geometry()
            max_width = int(screen.width() * 0.8)
            max_height = int(screen.height() * 0.8)
            if pixmap.width() > max_width or pixmap.height() > max_height:
                pixmap = pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(pixmap)
        layout.addWidget(label)
        self.resize(pixmap.width(), pixmap.height())


class MarkdownDisplayWidget(QTextEdit):
    """支持Markdown格式显示的组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setMouseTracking(True)  # 启用鼠标追踪以支持hover效果

        # 设置样式，去掉边框，更简洁的文档显示区域
        self.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                border: none;
                padding: 0px;
                color: white;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 13px;
                line-height: 1.4;
            }
        """)
    
    def setMarkdownText(self, markdown_text: str):
        """设置Markdown文本并渲染为HTML"""
        try:
            # 预处理：转换图片路径为HTML
            def _convert_image_paths(text: str) -> tuple[str, list[str]]:
                pattern = r'\[图片(\d+):\s*(.+?)\]'
                image_paths = []
                def replace_image(match):
                    img_num = match.group(1)
                    img_path = match.group(2).strip()
                    if os.path.exists(img_path):
                        image_paths.append(img_path)
                        return f'''<div class="image-container">
<img src="{img_path}" style="max-width:400px;cursor:pointer;">
<div class="image-path">[图片{img_num}: {img_path}]</div>
</div>'''
                    return match.group(0)
                return re.sub(pattern, replace_image, text), image_paths

            markdown_text, image_paths = _convert_image_paths(markdown_text)

            # 预处理：修正嵌套列表的缩进（避免无序子项被识别为有序项）
            # 一些编辑器/模型会在有序列表下的无序子项前仅缩进1-3个空格，
            # Python-Markdown 需至少4个空格才会解析为嵌套列表。
            def _normalize_markdown_lists(md: str) -> str:
                lines = md.splitlines()
                in_ol_block = False
                in_code_block = False
                fence_pat = re.compile(r"^\s*(```|~~~)")
                ol_pat = re.compile(r"^\s*\d+[\.)]\s")
                unordered_child_pat = re.compile(r"^ {1,3}[-*+]\s")

                for i, line in enumerate(lines):
                    # 代码块内不处理
                    if fence_pat.match(line):
                        in_code_block = not in_code_block
                        if in_code_block:
                            in_ol_block = False
                        continue
                    if in_code_block:
                        continue

                    # 空行或标题重置状态
                    if not line.strip() or line.lstrip().startswith('#'):
                        in_ol_block = False
                        continue

                    # 新的有序列表项开始
                    if ol_pat.match(line):
                        in_ol_block = True
                        continue

                    # 在有序列表块中，将1-3空格缩进的无序项提升为4空格
                    if in_ol_block and unordered_child_pat.match(line):
                        lines[i] = '    ' + line.lstrip()

                return '\n'.join(lines)

            markdown_text = _normalize_markdown_lists(markdown_text)

            # 配置markdown扩展
            md = markdown.Markdown(extensions=[
                'fenced_code',      # 代码块支持
                'tables',           # 表格支持  
                'nl2br',           # 换行转换
                'codehilite'       # 代码高亮
            ])
            
            # 转换markdown为HTML
            html_content = md.convert(markdown_text)
            
            # 添加CSS样式来美化HTML显示
            styled_html = f"""
            <style>
                body {{
                    font-family: 'Segoe UI', 'Arial', sans-serif;
                    line-height: 1.6;
                    color: #ffffff;
                    margin: 0;
                    padding: 5px;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: #ffffff;
                    margin-top: 20px;
                    margin-bottom: 10px;
                }}
                h1 {{ border-bottom: 2px solid #444; padding-bottom: 8px; }}
                h2 {{ border-bottom: 1px solid #444; padding-bottom: 4px; }}
                code {{
                    background-color: #2d2d2d;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: 'Consolas', 'Monaco', monospace;
                    color: #ffa500;
                }}
                pre {{
                    background-color: #2d2d2d;
                    padding: 12px;
                    border-radius: 6px;
                    border-left: 4px solid #007bff;
                    overflow-x: auto;
                }}
                pre code {{
                    background-color: transparent;
                    padding: 0;
                    color: #ffffff;
                }}
                blockquote {{
                    border-left: 4px solid #007bff;
                    margin: 16px 0;
                    padding-left: 16px;
                    color: #cccccc;
                    font-style: italic;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 16px 0;
                }}
                th, td {{
                    border: 1px solid #444;
                    padding: 8px 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #333;
                    font-weight: bold;
                }}
                ul, ol {{
                    padding-left: 20px;
                    margin: 12px 0;
                }}
                li {{
                    margin: 4px 0;
                }}
                a {{
                    color: #4da6ff;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                .image-container {{
                    margin: 8px 0;
                }}
                .image-path {{
                    font-size: 11px;
                    color: #888;
                    margin-top: 4px;
                    word-break: break-all;
                }}
                img {{
                    border-radius: 4px;
                }}
            </style>
            {html_content}
            """

            # 先添加图片资源到文档（必须在setHtml之前）
            for path in image_paths:
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    self.document().addResource(QTextDocument.ResourceType.ImageResource, QUrl(path), pixmap)

            self.setHtml(styled_html)
            
        except Exception as e:
            # 如果markdown解析失败，回退到纯文本显示
            self.setPlainText(markdown_text)
            sys.stderr.write(f"Markdown parsing error: {e}\n")

    def mousePressEvent(self, event: QMouseEvent):
        """处理鼠标点击事件，支持点击图片放大和链接打开"""
        if event.button() == Qt.LeftButton:
            # 检查是否点击了链接
            anchor = self.anchorAt(event.pos())
            if anchor:
                QDesktopServices.openUrl(QUrl(anchor))
                return

            cursor = self.cursorForPosition(event.pos())
            char_format = cursor.charFormat()

            # 检查是否点击了图片
            if char_format.isImageFormat():
                img_path = char_format.toImageFormat().name()
                if os.path.exists(img_path):
                    dialog = ImageViewerDialog(img_path, self)
                    dialog.exec()
                    return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """处理鼠标移动事件，链接上显示手型光标"""
        anchor = self.anchorAt(event.pos())
        if anchor:
            self.viewport().setCursor(Qt.PointingHandCursor)
        else:
            self.viewport().setCursor(Qt.IBeamCursor)
        super().mouseMoveEvent(event)
