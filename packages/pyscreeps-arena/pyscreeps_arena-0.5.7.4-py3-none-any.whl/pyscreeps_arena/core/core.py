# -*- coding: utf-8 -*-
#
# pyscreeps_arena - core.py
# Author: 我阅读理解一直可以的
# Template: V0.1
# Versions:
# .2025 01 01 - v0.1:
#   Created.
#

from pyscreeps_arena.core.utils import *


class __core__(PROJECT_EXCEPTION, metaclass=StaticMeta):
    @staticmethod
    def lprint(*args, sep=' ', end='\n', head="", ln='en') -> None:
        new_args = []
        for arg in args:
            if isinstance(arg, dict) and "en" in arg:
                new_args.append(str(arg.get(ln, arg)))
            else:
                new_args.append(arg)
        print(head, end="", sep="")
        print(*new_args, sep=sep, end=end)

    @staticmethod
    def ltrans(*args, auto:bool=True, ln='en') -> list:
        new_args = []
        if not args: return new_args
        for arg in args:
            if isinstance(arg, dict) and ln in arg:
                new_args.append(str(arg.get(ln, arg)))
            else:
                new_args.append(arg)
        return new_args[0] if auto and len(new_args) == 1 else new_args

    @staticmethod
    def lformat(element, formats:list) -> dict:
        new_element = {}
        if not element: return element
        if not isinstance(element, dict): return element
        if not formats: return element
        if 'en' not in element: return element
        for key, value in element.items():
            element[key] = value.format(*formats)
        return element

    @classmethod
    def log(cls, caller: str, *args, sep:str=" ", head:str="", end:str="\n", ln:str='en') -> None:
        """
        输出一条日志 | Output a log
        Args:
            caller: str 调用者 | Caller
            *args: str 日志信息 | Log message
            sep="  ": str 分隔符 | Separator
            head="" :  str 头部插入 | Head insert
            end='\n': str 结尾符 | End
            ln='en' : str 语言 | Language

        Returns:
            None
        """
        print(f"{head}{Fore.BLACK}[{cls.ltrans(caller, ln=ln)} {Fore.YELLOW}Log{Fore.BLACK}]:", *cls.ltrans(*args, auto=False, ln=ln), Fore.RESET, sep=sep, end=end)

    @classmethod
    def info(cls, caller: str, *args, sep:str=" ", head:str="", end:str="\n", ln:str='en') -> None:
        """
        输出一条信息 | Output an information
        Args:
            caller: str 调用者 | Caller
            *args: str 信息 | Information
            sep="  ": str 分隔符 | Separator
            head="" :  str 头部插入 | Head insert
            end='\n': str 结尾符 | End
            ln='en' : str 语言 | Language

        Returns:
            None
        """
        print(f"{head}{Fore.BLACK}[{cls.ltrans(caller, ln=ln)} {Fore.GREEN}Info{Fore.BLACK}]:", *cls.ltrans(*args, auto=False, ln=ln), Fore.RESET, sep=sep, end=end)

    @classmethod
    def warn(cls, caller: str, *args, sep:str=" ", head:str="", end:str="\n", ln:str='en') -> None:
        """
        输出一条警告 | Output a warning
        Args:
            caller: str 调用者 | Caller
            *args: str 警告信息 | Warning message
            sep="  ": str 分隔符 | Separator
            head="" :  str 头部插入 | Head insert
            end='\n': str 结尾符 | End
            ln='en' : str 语言 | Language

        Returns:
            None
        """
        print(f"{head}{Fore.BLACK}[{cls.ltrans(caller, ln=ln)} {Fore.YELLOW}Warn{Fore.BLACK}]:", *cls.ltrans(*args, auto=False, ln=ln), Fore.RESET, sep=sep, end=end)

    @classmethod
    def error(cls, caller: str, *args, sep:str=" ", head:str="", end:str="\n", ln:str='en', indent:int=1, error:bool=False, ecode:int=1) -> None:
        """
        生成一个异常并抛出 | Generate an exception and throw it
        Args:
            caller: str 调用者 | Caller
            *args: str 异常信息 | Exception message
            sep="  "    : str 分隔符 | Separator
            head=""     :  str 头部插入 | Head insert
            end='\n'    : str 结尾符 | End
            ln='en'     : str 语言 | Language
            indent=1    : int 在每一行的开头和其中所有超过一行的部分替换为\n + \t * indent |
                Replace at the beginning of each line and all parts that exceed one line with \n + \t * indent
            error=False : bool 是否抛出异常(False仅退出, True抛出异常) | Whether to throw an exception (False only exit, True throw an exception)
            ecode=1     : int 退出码(仅在error=False时有效) | Exit code (only valid when error=False)

        Returns:
            None
        """
        txts = [f"{head}{Fore.BLACK}[{cls.ltrans(caller, ln=ln)} {Fore.RED}Error{Fore.BLACK}]:"]
        txts.extend(cls.ltrans(*args, auto=False, ln=ln))
        txts.append(Fore.RESET)
        txt = sep.join(txts) + end
        if error:
            raise PROJECT_EXCEPTION(txt, indent=indent)
        else:
            print(txt, sep="", end="")
            sys.exit(ecode)

class core(__core__):
    pass

if __name__ == '__main__':
    core()
