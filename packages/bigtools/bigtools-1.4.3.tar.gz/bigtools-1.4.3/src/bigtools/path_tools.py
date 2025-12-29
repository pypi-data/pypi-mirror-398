# -*- coding: UTF-8 -*-
# @Time : 2023/10/7 17:16 
# @Author : 刘洪波
import os
import sys
from pathlib import Path


def check_make_dir(dir_str: str):
    """检查路径是否存在，不存在就创建"""
    if not os.path.exists(dir_str):
        os.makedirs(dir_str)


def get_execution_dir():
    """获取执行代码的目录"""
    return sys.path[0]


def get_file_type(file_path: str, is_upper: bool = False):
    """获取文件类型"""
    file_type = Path(file_path).suffix
    if file_type:
        file_type = file_type.replace('.', '')
        if is_upper:
            file_type = file_type.upper()
    return file_type


def get_execution_file_name():
    """获取执行代码的文件名"""
    return sys.argv[0]
