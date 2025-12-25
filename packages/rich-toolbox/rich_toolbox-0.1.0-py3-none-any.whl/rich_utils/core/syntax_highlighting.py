# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:51
# @Author  : fzf
# @FileName: syntax_highlighting.py
# @Software: PyCharm
from rich.console import Console
from rich.syntax import Syntax
from .base_handler import BaseHandler


class SyntaxHighlightingHandler(BaseHandler):
    def __init__(self, config):
        self.console = Console()
        self.language = config["language"]
        self.code = config["code"]

    def handle(self, **kwargs):
        """打印代码并进行高亮显示"""
        syntax = Syntax(self.code, self.language)
        self.console.print(syntax)
