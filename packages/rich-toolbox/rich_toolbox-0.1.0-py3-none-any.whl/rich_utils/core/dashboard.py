# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:51
# @Author  : fzf
# @FileName: dashboard.py
# @Software: PyCharm
from rich.console import Console
from rich.panel import Panel
from .base_handler import BaseHandler


class DashboardHandler(BaseHandler):
    def __init__(self, config):
        self.console = Console()
        self.title = config["title"]
        self.content = config["content"]

    def handle(self, **kwargs):
        """显示动态仪表盘"""
        panel = Panel(self.content, title=self.title)
        self.console.print(panel)
