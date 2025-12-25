# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:50
# @Author  : fzf
# @FileName: table.py
# @Software: PyCharm
from rich.console import Console
from rich.table import Table

from .base_handler import BaseHandler


class TableHandler(BaseHandler):
    def __init__(self, config):
        self.config = config
        self.console = Console()

    def handle(self, headers=None, rows=None, **kwargs):
        """
        处理表格打印
        :param headers: 表格头
        :param rows: 表格行数据
        """
        table = Table(show_header=self.config["show_header"], header_style=self.config["header_style"])
        for header in headers or ["ID", "Name", "Age"]:
            table.add_column(header)
        for row in rows or [["1", "Alice", "24"], ["2", "Bob", "30"]]:
            table.add_row(*row)
        self.console.print(table)
