# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:48
# @Author  : fzf
# @FileName: __init__.py
# @Software: PyCharm
r"""
    ____  ____________  __   __________  ____  __   _____
   / __ \/  _/ ____/ / / /  /_  __/ __ \/ __ \/ /  / ___/
  / /_/ // // /   / /_/ /    / / / / / / / / / /   \__ \
 / _, _// // /___/ __  /    / / / /_/ / /_/ / /______/ /
/_/ |_/___/\____/_/ /_/    /_/  \____/\____/_____/____/
"""

__title__ = 'Rich Tools'
__version__ = '0.1.0'  # 您可以根据版本进行修改
__author__ = 'fzf'
__license__ = 'BSD 3-Clause'
__copyright__ = 'Copyright 2025 fzf'
# Version synonym
VERSION = __version__

__all__ = [
    'RichToolbox',
]

from .handler import RichToolbox
