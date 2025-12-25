# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:55
# @Author  : fzf
# @FileName: base_handler.py
# @Software: PyCharm

from abc import ABC, abstractmethod


class BaseHandler(ABC):

    @abstractmethod
    def handle(self, *args, **kwargs):
        """所有子类必须实现的处理方法"""
        pass
