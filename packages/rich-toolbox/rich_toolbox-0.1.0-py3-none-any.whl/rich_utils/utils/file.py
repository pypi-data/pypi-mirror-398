# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:50
# @Author  : fzf
# @FileName: file.py
# @Software: PyCharm
import os
from rich.console import Console
from ..core.base_handler import BaseHandler


class FileHandler(BaseHandler):
    def handle(self, file_path=None, **kwargs):
        """读取并打印文件内容"""
        console = Console()
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                console.print(file.read())
        else:
            console.print(f"File {file_path} does not exist.")
