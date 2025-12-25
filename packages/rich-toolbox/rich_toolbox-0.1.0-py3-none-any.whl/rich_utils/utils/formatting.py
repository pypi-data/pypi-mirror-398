# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:50
# @Author  : fzf
# @FileName: formatting.py
# @Software: PyCharm
from rich.console import Console
from rich.table import Table
from ..core.base_handler import BaseHandler


class FormattingHandler(BaseHandler):
    def handle(self, data=None, **kwargs):
        """格式化表格"""
        table = Table(show_header=True)
        for row in data:
            table.add_row(*row)
        console = Console()
        console.print(table)
