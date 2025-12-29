# -*- coding: UTF-8 -*-
# @Time : 2023/9/27 10:05 
# @Author : 刘洪波
import yaml


def load_yaml(file_path: str): return yaml.safe_load(open(file_path, 'r', encoding="utf-8"))


def load_all_yaml(file_path: str): return yaml.safe_load_all(open(file_path, 'r', encoding="utf-8"))


def write_yaml(data: dict, file_path: str, mode: str = 'w'):
    f = open(file_path, mode, encoding="utf-8")
    yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
    f.close()
