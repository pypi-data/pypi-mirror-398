# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:51
# @Author  : fzf
# @FileName: stats.py
# @Software: PyCharm
from rich.console import Console
from rich.text import Text
from .base_handler import BaseHandler


class StatsHandler(BaseHandler):
    def __init__(self, config):
        self.console = Console()
        self.data = config["data"]

    def handle(self, **kwargs):
        """显示统计和汇总信息"""
        stats = Text(f"Summary: {self.data}")
        self.console.print(stats)
