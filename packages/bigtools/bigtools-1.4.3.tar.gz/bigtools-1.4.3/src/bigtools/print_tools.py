# -*- coding: UTF-8 -*-
# @Time : 2025/10/13 15:36 
# @Author : 刘洪波
"""
pretty_print.py - 彩色美观打印（终极版）
功能：
- 打印变量名或表达式的值
- 彩色区分变量名和值
- 支持列表/字典过长折叠输出（可控行数）
- 支持长字符串自动截断（可控长度）
"""

from pprint import pformat
import inspect


def pretty_print(*args, color=True, max_lines=None, max_str_len=None):
    """
    打印变量名或表达式及其值，彩色区分变量名和值

    参数:
        *args: 要打印的变量或表达式
        color (bool): 是否启用彩色输出，默认 True
        max_lines (int|None): 当列表/字典行数超过此值时折叠显示，None 表示不折叠
        max_str_len (int|None): 当字符串长度超过此值时截断显示，None 表示不截断
    """

    def truncate_formatted(_val):
        """处理列表/字典折叠和字符串截断"""
        # 字符串截断
        if isinstance(_val, str) and max_str_len and len(_val) > max_str_len:
            return repr(_val[:max_str_len] + '...')

        # 列表/字典折叠
        _formatted = pformat(val, indent=4, width=100, sort_dicts=False)
        lines = _formatted.splitlines()
        if max_lines and len(lines) > max_lines:
            truncated = lines[:max_lines]
            truncated.append(f"... (总长度: {len(lines)}行)")
            return "\n".join(truncated)
        return _formatted

    # 获取调用行的代码，提取表达式名
    frame = inspect.currentframe().f_back
    code_line = inspect.getframeinfo(frame).code_context[0].strip() if frame else ''
    inside = code_line[code_line.find('(') + 1: code_line.rfind(')')]
    exprs = [e.strip() for e in inside.split(',')] if inside else ['?'] * len(args)

    for expr, val in zip(exprs, args):
        formatted = truncate_formatted(val)
        if color:
            val_color = "\033[93m" if isinstance(val, str) else "\033[92m"
            print(f"\033[96m{expr}\033[0m: {val_color}{formatted}\033[0m\n")
        else:
            print(f"{expr}: {formatted}\n")