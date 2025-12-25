# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:50
# @Author  : fzf
# @FileName: progress.py
# @Software: PyCharm
import time
from rich.console import  Console
from rich.progress import Progress

from .base_handler import BaseHandler


class ProgressHandler(BaseHandler):
    def __init__(self, config):
        self.config = config
        self.console = Console()

    def handle(self, total=None, interval=None, **kwargs):
        """
        处理进度条
        :param total: 总任务数
        :param interval: 更新间隔（秒）
        """
        total = total or self.config["total"]
        interval = interval or self.config["interval"]
        with Progress(console=self.console) as progress:
            task = progress.add_task("[green]Processing...", total=total)
            while not progress.finished:
                progress.update(task, advance=self.config["advance_step"])
                time.sleep(interval)
