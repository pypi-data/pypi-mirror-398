# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:52
# @Author  : fzf
# @FileName: rotate_log.py
# @Software: PyCharm
import logging
from logging.handlers import RotatingFileHandler
from .base_handler import BaseHandler


class RotateLogHandler(BaseHandler):
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("rich_logger")
        self.handler = RotatingFileHandler(self.config["log_file"], maxBytes=10000, backupCount=5)
        self.logger.addHandler(self.handler)

    def handle(self, level="info", message="", **kwargs):
        """处理带有日志轮转的日志操作"""
        log_func = getattr(self.logger, level, self.logger.info)
        log_func(message)
