# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午4:56
# @Author  : fzf
# @FileName: enums.py
# @Software: PyCharm
from rich_utils.config import RichConfig
from rich_utils.core import (LoggerHandler, ProgressHandler, TableHandler,
                             SyntaxHighlightingHandler, LayoutHandler, SpinnerHandler,
                             ColorGradientsHandler, DashboardHandler, StatsHandler,
                             TimerHandler, RotateLogHandler)

from rich_utils.utils import (ColorHandler,
                              FileHandler,
                              FormattingHandler,
                              MathHandler)


class ModuleEnums(object):
    LOG = "log"
    PROGRESS = "progress"
    TABLE = "table"
    SYNTAX_HIGHLIGHTING = "syntax_highlighting"
    LAYOUT = "layout"
    SPINNER = "spinner"
    COLOR_GRADIENTS = "color_gradients"
    DASHBOARD = "dashboard"
    STATS = "stats"
    TIMER = "timer"
    ROTATE_LOG = "rotate_log"
    COLOR = "color"
    FILE = 'file'
    FORMATTING = "formatting"
    MATH = "math"

    @classmethod
    def get_module_enums(cls):
        return [getattr(cls, e) for e in cls.__dict__ if not e.startswith("__") and not callable(getattr(cls, e))]

    @classmethod
    def get_handler(cls, action: str, config: RichConfig = None):
        """根据 action 类型动态创建对象并执行相关操作"""
        config = config or RichConfig()

        handlers_map = {
            cls.LOG: LoggerHandler(config.get_logger_config()),
            cls.PROGRESS: ProgressHandler(config.get_progress_config()),
            cls.TABLE: TableHandler(config.get_table_config()),
            cls.SYNTAX_HIGHLIGHTING: SyntaxHighlightingHandler(config.get_syntax_highlighting_config()),
            cls.LAYOUT: LayoutHandler(config.get_layout_config()),
            cls.SPINNER: SpinnerHandler(config.get_spinner_config()),
            cls.COLOR_GRADIENTS: ColorGradientsHandler(config.get_color_gradients_config()),
            cls.DASHBOARD: DashboardHandler(config.get_dashboard_config()),
            cls.STATS: StatsHandler(config.get_stats_config()),
            cls.TIMER: TimerHandler(config.get_timer_config()),
            cls.ROTATE_LOG: RotateLogHandler(config.get_rotate_log_config()),
            cls.COLOR: ColorHandler(),
            cls.FILE: FileHandler(),
            cls.FORMATTING: FormattingHandler(),
            cls.MATH: MathHandler(),
        }

        # 返回对应的处理器实例
        return handlers_map.get(action, None)
