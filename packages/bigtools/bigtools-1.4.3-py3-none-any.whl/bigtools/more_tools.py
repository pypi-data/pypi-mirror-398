# -*- coding: UTF-8 -*-
# @Time : 2023/9/27 17:50 
# @Author : 刘洪波
import socket
import os
import time
import inspect
import random
import string
import functools
import asyncio
from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio  # tqdm 异步版本
from typing import Any, List, Union, Callable
from bigtools.yaml_tools import load_yaml


def extract_ip() -> str:
    """
    获取本机局域网IP地址（非127.0.0.1）
    如果无法获取，返回空字符串。
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # 这里使用一个不会到达的地址来触发获取本机IP
            s.connect(('10.255.255.255', 1))
            return s.getsockname()[0]
    except Exception:
        return ''


def equally_split_list_or_str(data: Union[list, str], num: int) -> List[Union[list, str]]:
    """
    将一个 list 或 str 按长度 num 均分
    :param data: 输入的 list 或 str
    :param num: 每段的长度
    :return: 分割后的 list
    """
    if num <= 0:
        raise ValueError("num 必须大于 0")
    return [data[i:i + num] for i in range(0, len(data), num)]


def load_config(config_dir: str):
    """
    获取配置
    PYTHON_CONFIG 默认值是 dev  其他值有 prod test
    :param config_dir: 配置文件存储的文件夹
    :return: dict
    """
    config_path = os.path.join(config_dir, os.getenv('PYTHON_CONFIG', 'dev') + '.yaml')
    if os.path.exists(config_path):
        return load_yaml(config_path)
    raise ValueError(f'Path not found: {config_path}')


def set_env(env_dict: dict):
    """设置环境变量"""
    for k, v in env_dict.items():
        os.environ[k] = v


def load_env(envs):
    """
    获取环境变量
    :param envs:  type 可以是 list 也可以是 dict, 也可是 [str, str, {k:v, k2:v2}]
    :return:
    """
    if isinstance(envs, list):
        env = {}
        for i in envs:
            if isinstance(i, str):
                env[i] = os.getenv(i)
            elif isinstance(i, dict):
                for k, v in i.items():
                    env[k] = os.getenv(k, v)
            else:
                raise ValueError(f'type is error: item is {i}, the type of item can only be str or dict')
        return env
    elif isinstance(envs, dict):
        return {k: os.getenv(k, v) for k, v in envs.items()}
    else:
        raise ValueError('type is error: the type of envs can only be list or dict')


class FuncTimer:
    """装饰器类：统计函数运行时间，支持同步/异步"""

    def __init__(self, logger=None, threshold: float = 0.0):
        """
        :param logger: 日志对象，可选
        :param threshold: 运行时间超过阈值才输出日志（秒），默认0表示始终输出
        """
        self.logger = logger
        self.threshold = threshold

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.perf_counter()
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start
                self._log(func.__name__, duration)
                return result
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start = time.perf_counter()
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start
                self._log(func.__name__, duration)
                return result
            return sync_wrapper

    def _log(self, func_name: str, duration: float) -> None:
        """统一日志输出逻辑"""
        if duration >= self.threshold:
            msg = f'Function "{func_name}" required: {duration:.4f} seconds'
            if self.logger:
                self.logger.info(msg)
            else:
                print(msg)


def time_sleep(seconds: int, step: float = 1.0):
    """
    程序睡眠，有进度条显示

    :param seconds: 总睡眠时间（秒）
    :param step: 每步睡眠时间（秒），默认1秒
    """
    steps = int(seconds / step)
    for _ in tqdm(range(steps), desc=f'程序睡眠 {seconds} 秒'):
        time.sleep(step)


async def async_time_sleep(seconds: int, step: float = 1.0):
    """
    异步睡眠，有进度条显示
    :param seconds: 总睡眠时间（秒）
    :param step: 每步睡眠时间（秒），默认1秒
    """
    steps = int(seconds / step)
    for _ in tqdm_asyncio(range(steps), desc=f'程序异步睡眠 {seconds} 秒'):
        await asyncio.sleep(step)


def count_str_start_or_end_word_num(strings: str, matched_str: str, beginning: bool = True) -> int:
    """
    高性能统计字符串首尾连续出现某个子串的次数
    :param strings: 字符串
    :param matched_str: 待匹配子串
    :param beginning: True 从开头统计， False 从结尾统计
    :return: 每个字符串连续出现次数的列表
    """
    if not matched_str:
        return 0

    step = len(matched_str)
    count = 0

    i = 0 if beginning else len(strings) - step

    while 0 <= i <= len(strings) - step:
        segment = strings[i:i + step]
        if segment == matched_str:
            count += 1
            i = i + step if beginning else i - step
        else:
            break
    return count


def is_chinese(input_data: str):
    """检测字符串是否只由中文组成，不含标点"""
    for char in input_data:
        if not ('\u4e00' <= char <= '\u9fff'):
            return False
    return True


def is_english(input_data: str):
    """检测字符串是否只由英文组成，不含标点"""
    for char in input_data:
        if not ('a' <= char <= 'z' or 'A' <= char <= 'Z'):
            return False
    return True


def is_number(input_data: Union[str, int, float]) -> bool:
    """检测输入数据是否为数字（整数或浮点数），支持普通数字和Unicode数字"""
    try:
        # 尝试直接转换为 float
        float(input_data)
        return True
    except (ValueError, TypeError):
        # 尝试检测 Unicode 数字
        try:
            import unicodedata
            unicodedata.numeric(input_data)
            return True
        except (TypeError, ValueError):
            return False


def generate_random_string(length: int = 12):
    """
    生成随机长度的字符串
    :param length:
    :return:
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def sort_with_index(values, reverse: bool =True):
    """
    按数值降序排序，并保留原索引位置。
    :param values: alues (list[float | int]): 待排序的数值列表。
    :param reverse: 是否降序（默认 True）
    :return:
           tuple:
            - sorted_pairs (list[tuple[int, float]]): 排序后的 (index, value) 元组列表。
            - result (list[dict]): 结构化输出 [{"id": 原索引, "value": 值}, ...]。
    """

    # 使用 enumerate 生成 (index, value) 对并按 value 降序排序
    sorted_pairs = sorted(enumerate(values), key=lambda x: x[1], reverse=reverse)

    # 转为字典列表形式
    result = [{"id": idx, "value": val} for idx, val in sorted_pairs]

    return sorted_pairs, result

def sort_dict_by_value(d: dict, reverse: bool = True) -> dict:
    """
    按值对字典排序
    :param d: 待排序的字典
    :param reverse: 是否降序（默认 True）
    :return: 排序后的字典
    """
    return dict(sorted(d.items(), key=lambda item: item[1], reverse=reverse))
