# -*- coding: UTF-8 -*-
# @Time : 2023/9/27 15:58 
# @Author : 刘洪波
import logging
import logging.handlers
import sys
import logging.config
from bigtools.yaml_tools import load_yaml

"""
配置日志
第一种：set_log （简单，适合轻量级项目）
第二种：SetLog （复杂，适合大型项目）
"""


def set_log(log_path):
    logger = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s %(pathname)s %(lineno)d %(levelname)-8s: %(message)s')
    file_handler = logging.handlers.TimedRotatingFileHandler(log_path, when='D', interval=1, backupCount=180)
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.formatter = formatter
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)
    return logger


class SetLog(object):
    def __init__(self, log_config: str, log_path: str):
        """log_config 有专门模板"""
        config = load_yaml(log_config)
        config['handlers']['operation']['filename'] = f'{log_path}operation'
        config['handlers']['error']['filename'] = f'{log_path}error'
        config['handlers']['info']['filename'] = f'{log_path}info'
        logging.config.dictConfig(config)

    @staticmethod
    def debug(msg):
        logger = logging.getLogger('debug')
        logger.debug(msg)

    @staticmethod
    def info(msg):
        logger = logging.getLogger('info')
        logger.info(msg)

    @staticmethod
    def error(msg):
        logger = logging.getLogger('error')
        logger.error(msg, exc_info=True)
