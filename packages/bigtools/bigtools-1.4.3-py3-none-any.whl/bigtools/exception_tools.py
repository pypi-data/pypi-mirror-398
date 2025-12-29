# -*- coding: UTF-8 -*-
# @Time : 2025/9/8 11:45 
# @Author : 刘洪波
import requests
import logging
import inspect
from functools import wraps
from typing import Callable, Any, Optional


class RequestExceptionHandler:
    """处理 requests 请求异常并写日志，支持同步和异步函数"""

    def __init__(self, logger: logging.Logger = None, level: int = logging.ERROR, with_traceback: bool = True):
        """
        :param logger: 日志对象，默认使用 logging.getLogger(__name__)
        :param level: 日志级别，默认 ERROR
        :param with_traceback: 是否输出完整 traceback，默认 True
        """
        self.logger = logger or logging.getLogger(__name__)
        self.level = level
        self.with_traceback = with_traceback

    def __call__(self, func: Callable):
        if inspect.iscoroutinefunction(func):
            # 异步函数
            @wraps(func)
            async def async_wrapped(*args, **kwargs):
                try:
                    response = await func(*args, **kwargs)
                    if isinstance(response, requests.Response):
                        response.raise_for_status()
                    return response
                except requests.RequestException as e:
                    self.logger.log(
                        self.level,
                        f"[DealException] {func.__name__} 出现异常: {e}",
                        exc_info=self.with_traceback,
                    )
                    return None
            return async_wrapped
        else:
            # 同步函数
            @wraps(func)
            def sync_wrapped(*args, **kwargs):
                try:
                    response = func(*args, **kwargs)
                    if isinstance(response, requests.Response):
                        response.raise_for_status()
                    return response
                except requests.RequestException as e:
                    self.logger.log(
                        self.level,
                        f"[DealException] {func.__name__} 出现异常: {e}",
                        exc_info=self.with_traceback,
                    )
                    return None
            return sync_wrapped


class UniversalExceptionHandler:
    """通用异常处理装饰器，支持同步/异步函数及类方法"""

    def __init__(self,
                 logger: Optional[logging.Logger] = None,
                 level: int = logging.ERROR,
                 with_traceback: bool = True,
                 default: Any = None):
        """
        :param logger: 日志对象，默认使用 logging.getLogger(__name__)
        :param level: 日志级别，默认 ERROR
        :param with_traceback: 是否输出完整 traceback，默认 True
        :param default: 出现异常时的默认返回值
        """
        self.logger = logger or logging.getLogger(__name__)
        self.level = level
        self.with_traceback = with_traceback
        self.default = default

    def __call__(self, obj: Any):
        if callable(obj) and not isinstance(obj, type):
            return self._wrap_function(obj)
        elif isinstance(obj, type):
            return self._wrap_class(obj)
        else:
            raise TypeError("UniversalExceptionHandler 只能用于函数或类")

    def _wrap_function(self, func: Callable):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    self.logger.log(
                        self.level,
                        f"[UniversalExceptionHandler] {func.__qualname__} 出现异常: {e}",
                        exc_info=self.with_traceback
                    )
                    return self.default
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.logger.log(
                        self.level,
                        f"[UniversalExceptionHandler] {func.__qualname__} 出现异常: {e}",
                        exc_info=self.with_traceback
                    )
                    return self.default
            return sync_wrapper

    def _wrap_class(self, cls: type):
        for attr_name, attr_value in cls.__dict__.items():
            if callable(attr_value) and not attr_name.startswith("__"):
                setattr(cls, attr_name, self._wrap_function(attr_value))
        return cls
