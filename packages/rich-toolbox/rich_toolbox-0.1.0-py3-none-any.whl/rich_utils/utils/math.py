# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:50
# @Author  : fzf
# @FileName: math.py
# @Software: PyCharm
import math
from rich.console import Console
from ..core.base_handler import BaseHandler


class MathHandler(BaseHandler):

    def handle(self, number=None, **kwargs):
        """计算平方根"""
        console = Console()
        console.print(f"The square root of {number} is {math.sqrt(number)}")
