# -*- coding: utf-8 -*-
#
# pyscreeps_arena - basic.py
# Author: 我阅读理解一直可以的
# Template: V0.1
# Versions:
# .2025 01 01 - v0.1:
#   Created.
#


import os
import sys
import shutil
import inspect
from colorama import Fore, Back
from pyscreeps_arena.core import const
from pyscreeps_arena.core import config


class __pyscreeps_arena_themeException(Exception):
    """
    具有__pyscreeps_arena_themeException主题的异常类 | Exception class with __pyscreeps_arena_themeException theme
    :param *args: str 异常信息 | Exception message
    :param indent=1: int 在每一行的开头和其中所有超过一行的部分替换为\n + \t * indent | Replace at the beginning of each line and all parts that exceed one line with \n + \t * indent
    """
    try:
        # 尝试获取终端的宽度 | Try to get the width of the terminal
        __TERMINAL_COLUMNS = shutil.get_terminal_size().columns
    except AttributeError:
        # 如果无法获取终端宽度，设置一个默认值 | If the terminal width cannot be obtained, set a default value
        __TERMINAL_COLUMNS = 80  # 通常终端的默认宽度是80个字符 | The default width of the terminal is usually 80 characters

    __SEPARATOR = "-" * __TERMINAL_COLUMNS

    def __init__(self, *args: str, indent: int = 1):
        txts = ["\n", self.__SEPARATOR, "\n"]
        # 现在我需要遍历每一个元素:
        # 首先，移除开头的所有\n，并确保在开头有且只有一个\n
        # 然后，将其中\n替换为\n + \t * indent
        ## Now I need to iterate every element:
        ## First, remove all \n at the beginning, and make sure there is only one \n at the beginning
        ## Then, replace the \n in it with \n + \t * indent
        for arg in args:
            tmp = arg.strip("\n\t\r ")
            if not tmp: continue
            replaced = "\n" + "\t" * indent
            tmp = replaced + tmp.replace("\n", replaced)
            txts.append(tmp)
        super().__init__("".join(txts))


# 不可实例化异常 | Cannot instantiate exception
class CannotInstantiate(__pyscreeps_arena_themeException):
    pass


# 静态类(不可实例化) | Static class
class StaticClass:
    def __new__(cls, *args, **kwargs):
        raise CannotInstantiate(
            f"Class:'{cls.__name__}' can not be instantiate, because it's marked as a static class."
        )

# 静态类Meta(不可实例化) | Static metaclass
class StaticMeta(type):
    def __call__(cls, *args, **kwargs):
        raise CannotInstantiate(
            f"Class:'{cls.__name__}' can not be instantiate, because it's marked as a static class."
        )

PROJECT_EXCEPTION = __pyscreeps_arena_themeException
