# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:52
# @Author  : fzf
# @FileName: timer.py
# @Software: PyCharm
import time

from rich.console import Console

from .base_handler import BaseHandler


class TimerHandler(BaseHandler):
    def __init__(self, config):
        self.console = Console()
        self.start_time = time.time()

    def handle(self, **kwargs):
        """计算并显示经过的时间"""
        elapsed_time = time.time() - self.start_time
        self.console.print(f"Elapsed time: {elapsed_time} seconds")
