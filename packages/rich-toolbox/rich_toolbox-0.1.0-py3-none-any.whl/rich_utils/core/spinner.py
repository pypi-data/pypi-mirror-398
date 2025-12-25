# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:51
# @Author  : fzf
# @FileName: spinner.py
# @Software: PyCharm
from rich.console import Console
from rich.spinner import Spinner
from .base_handler import BaseHandler


class SpinnerHandler(BaseHandler):
    def __init__(self, config):
        self.console = Console()
        self.spinner_style = config["spinner_style"]

    def handle(self, **kwargs):
        """显示转圈动画"""
        spinner = Spinner(self.spinner_style)
        self.console.print(f"[{self.spinner_style}] Loading...")
        self.console.show_spinner(spinner)
