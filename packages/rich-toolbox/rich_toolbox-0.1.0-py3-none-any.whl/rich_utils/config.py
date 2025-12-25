# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午4:08
# @Author  : fzf
# @FileName: config.py
# @Software: PyCharm


class RichConfig:
    """配置 rich 相关的样式和行为"""

    def __init__(self):
        # 默认日志配置
        self.logger_config = {
            "level": "INFO",  # 默认日志级别
            # "log_file": "app.log",  # 默认日志文件
            "show_time": True,  # 是否显示时间
            "time_format": "%Y-%m-%d %H:%M:%S",  # 时间格式
            "log_format": "%(message)s",  # 日志格式
        }

        # 默认表格配置
        self.table_config = {
            "show_header": True,  # 是否显示表头
            "header_style": "bold magenta",  # 表头样式
            "row_style": "dim",  # 行样式
            "no_wrap": True,  # 是否自动换行
        }

        # 默认进度条配置
        self.progress_config = {
            "total": 100,
            "advance_step": 0.5,  # 每次进度增加的步长
            "interval": 0.1,  # 更新间隔
        }

        # 默认打印配置
        self.printer_config = {
            "style": "bold green",  # 默认样式
            "text": "Hello, Rich Printer!"  # 默认文本
        }

        # 默认代码高亮配置
        self.syntax_highlighting_config = {
            "language": "python",  # 默认语言
            "code": "print('Hello, World!')"  # 默认代码
        }

        # 默认布局配置
        self.layout_config = {
            "layout_type": "split",  # 默认布局
            "size": 1  # 默认大小
        }

        # 默认转圈动画配置
        self.spinner_config = {
            "spinner_style": "dots"  # 默认样式
        }

        # 默认颜色渐变配置
        self.color_gradients_config = {
            "start_color": "red",  # 默认开始颜色
            "end_color": "blue",  # 默认结束颜色
            "text": "Gradient Text"  # 默认文本
        }

        # 默认动态仪表盘配置
        self.dashboard_config = {
            "title": "Dashboard",  # 默认标题
            "content": "Loading..."  # 默认内容
        }

        # 默认统计和汇总配置
        self.stats_config = {
            "data": "Statistics data"  # 默认数据
        }

        # 默认计时器配置
        self.timer_config = {
            "start_time": 0,  # 默认开始时间
            "end_time": 60  # 默认结束时间
        }

        # 默认日志轮转配置
        self.rotate_log_config = {
            "log_file": "rotated_log.log",  # 默认日志文件
            "max_bytes": 10485760,  # 默认最大字节数
            "backup_count": 3  # 默认备份数量
        }

    def get_logger_config(self):
        return self.logger_config

    def get_table_config(self):
        return self.table_config

    def get_progress_config(self):
        return self.progress_config

    def get_printer_config(self):
        return self.printer_config

    def get_syntax_highlighting_config(self):
        return self.syntax_highlighting_config

    def get_layout_config(self):
        return self.layout_config

    def get_spinner_config(self):
        return self.spinner_config

    def get_color_gradients_config(self):
        return self.color_gradients_config

    def get_dashboard_config(self):
        return self.dashboard_config

    def get_stats_config(self):
        return self.stats_config

    def get_timer_config(self):
        return self.timer_config

    def get_rotate_log_config(self):
        return self.rotate_log_config

