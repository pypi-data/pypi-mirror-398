# -*- coding: UTF-8 -*-
# @Time : 2022/8/17 15:44 
# @Author : 刘洪波
import random


headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}

user_agents = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

random_headers = {
    'user-agent': random.choice(user_agents),
}


class ContentType(object):
    app_json = 'application/json',
    app_xwfu = 'application/x-www-form-urlencoded',
    app_xml = 'application/xml',
    mul_fd = 'multipart/form-data',
    text_xml = 'text/xml'
    app_json_headers = {"Content-Type": "application/json;charset=utf-8"}
    app_xwfu_headers = {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}
    app_xml_headers = {"Content-Type": "application/xml;charset=utf-8"}
    mul_fd_headers = {"Content-Type": "multipart/form-data;charset=utf-8"}
    text_xml_headers = {"Content-Type": "text/xml;charset=utf-8"}


en_letter = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
             'V', 'W', 'X', 'Y', 'Z']

numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']


class DateType(object):
    """
    用于编写代码时提示，不建议写入代码里。写入会代码增加阅读难度。
    """
    type_1 = '%Y-%m-%d %H:%M:%S'        # YYYY-MM-DD
    type_2 = '%Y年%m月%d日 %H时%M分%S秒'  # YYYY年MM月DD日
    type_3 = '%Y.%m.%d'                 # YYYY.MM.DD
    type_4 = '%Y%m%d'                   # YYYYMMDD
    type_5 = '%Y/%m/%d'                 # YYYY/MM/DD


class RePattern(object):
    window_INITIAL_STATE = r"window.__INITIAL_STATE__=(.*?}});"
