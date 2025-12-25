# -*- coding: utf-8 -*-
# @Time    : 2025/12/22 下午3:49
# @Author  : fzf
# @FileName: handler.py
# @Software: PyCharm
from typing import Union
from .enums import ModuleEnums


class RichToolbox:

    def __new__(cls, action: Union[ModuleEnums, str] = None, config=None):
        handler = ModuleEnums.get_handler(action, config)
        if not handler:
            raise ValueError(f"Unsupported action: {action}\n"
                             f"Supported actions are: {'|'.join([e for e in ModuleEnums.get_module_enums()])}")
        # 赋值给 cls.handler 确保处理器实例正确初始化
        instance = super().__new__(cls)
        # 将处理器实例赋值给实例
        instance.handler = handler
        return instance  # 返回实例

    def handle(self,
               message=None,
               level=None,
               text=None,
               style=None,
               total=None,
               interval=None,
               headers=None,
               rows=None,
               color_code=None,
               file_path=None,
               data=None,
               number=None,
               **kwargs):
        """根据对象的 action 执行对应操作"""
        self.handler.handle(message=message,
                            level=level,
                            text=text,
                            style=style,
                            total=total,
                            interval=interval,
                            headers=headers,
                            rows=rows,
                            color_code=color_code,
                            file_path=file_path,
                            data=data,
                            number=number,
                            **kwargs)  # 直接调用当前操作的处理器
        return self  # 支持链式调用


if __name__ == "__main__":
    logger = RichToolbox('log')
    logger.handle("Hello, Rich Logger!")
