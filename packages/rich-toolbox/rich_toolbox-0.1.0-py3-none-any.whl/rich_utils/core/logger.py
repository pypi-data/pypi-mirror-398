# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:50
# @Author  : fzf
# @FileName: logger.py
# @Software: PyCharm
import logging
from rich.logging import RichHandler

from .base_handler import BaseHandler


class LoggerHandler(BaseHandler):
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("rich_logger")
        log_config = self.config

        # 配置日志级别和输出格式
        logging.basicConfig(level=getattr(logging, log_config["level"].upper()),
                            format=log_config["log_format"],
                            handlers=[RichHandler()])

        # 如果有指定日志文件，则添加文件处理器
        if log_config.get('log_file', None):
            self.file_handler = logging.FileHandler(log_config["log_file"])
            self.logger.addHandler(self.file_handler)

    def handle(self, message: str = "", **kwargs):
        """
        处理日志记录
        :param level: 日志级别（info, debug, warning, error, critical）
        :param message: 日志消息
        """
        log_func = getattr(self.logger, self.config["level"], self.logger.info)
        log_func(message)
