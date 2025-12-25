# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:50
# @Author  : fzf
# @FileName: color.py
# @Software: PyCharm
from rich.color import Color
from rich.console import Console
from ..core.base_handler import BaseHandler


class ColorHandler(BaseHandler):
    def handle(self, color_code=None, **kwargs):
        """转换颜色代码"""
        console = Console()
        color = Color.from_rgb(*color_code)
        console.print(color)
