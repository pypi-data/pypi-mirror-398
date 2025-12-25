# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:51
# @Author  : fzf
# @FileName: color_gradients.py
# @Software: PyCharm
from rich.console import Console
from rich.text import Text
from .base_handler import BaseHandler


class ColorGradientsHandler(BaseHandler):
    def __init__(self, config):
        self.console = Console()
        self.text = config["text"]
        self.start_color = config["start_color"]
        self.end_color = config["end_color"]

    def handle(self, **kwargs):
        """显示颜色渐变的文本"""
        gradient_text = Text(self.text, style=f"gradient({self.start_color}, {self.end_color})")
        self.console.print(gradient_text)
