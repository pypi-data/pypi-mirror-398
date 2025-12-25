# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:51
# @Author  : fzf
# @FileName: layout.py
# @Software: PyCharm
from rich.console import Console
from rich.layout import Layout
from .base_handler import BaseHandler


class LayoutHandler(BaseHandler):
    def __init__(self, config):
        self.console = Console()
        self.layout = Layout()

    def handle(self, **kwargs):
        """布局显示"""
        self.layout.split_column(
            Layout(name="main", size=1),
            Layout(name="footer", size=3)
        )
        self.console.print(self.layout)
