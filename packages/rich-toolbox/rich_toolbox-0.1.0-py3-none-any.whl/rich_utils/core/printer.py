# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:50
# @Author  : fzf
# @FileName: printer.py
# @Software: PyCharm
from rich.console import Console
from rich.text import Text
from .base_handler import BaseHandler


class PrinterHandler(BaseHandler):
    def __init__(self, config):
        """初始化打印模块"""
        self.console = Console()  # 创建 rich 的 Console 实例
        self.style = config.get("style", "bold green")  # 默认样式
        self.text = config.get("text", "")  # 默认文本内容

    def handle(self, text=None, style=None, **kwargs):
        """处理文本输出"""
        text = text or self.text  # 如果没有传入文本，使用默认文本
        style = style or self.style  # 如果没有传入样式，使用默认样式

        # 创建一个 rich 的 Text 对象并应用样式
        rich_text = Text(text, style=style)

        # 输出到控制台
        self.console.print(rich_text)
