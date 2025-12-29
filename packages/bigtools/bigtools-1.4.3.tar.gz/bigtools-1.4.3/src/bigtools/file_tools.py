# -*- coding: UTF-8 -*-
# @Time : 2025/9/16 18:18 
# @Author : 刘洪波
import os
import asyncio
import logging
import aiofiles
from pathlib import Path
from typing import List, Tuple


def save_file(file_path: str, content: str, mode: str = 'w', encoding: str = 'utf-8', logger: logging.Logger = None, raise_on_error: bool = False) -> bool:
    """
    通用文件保存函数，支持 .txt, .md, .html 等

    :param file_path: 文件路径，例如 'example.md'
    :param content: 文件内容
    :param mode: 写入模式，'w' 覆盖，'a' 追加
    :param encoding: 文件编码，默认 'utf-8'
    :param logger: 日志收集器
    :param raise_on_error: 是否在出错时抛出异常
    :return: 保存成功返回 True，否则 False
    """
    try:
        path = Path(file_path)
        # 检查文件名长度
        if len(str(path)) > 255:
            raise OSError(f"文件名过长: {file_path}")
        # 确保目录存在
        path.parent.mkdir(parents=True, exist_ok=True)
        # 保存文件
        with open(path, mode, encoding=encoding) as f:
            f.write(content)
        if logger:
            logger.info(f"文件保存成功: {file_path}")
        else:
            print(f"文件保存成功: {file_path}")
        return True
    except Exception as e:
        if logger:
            logger.error(f"文件保存失败: {file_path}, 错误: {e}", exc_info=True)
        else:
            print(f"文件保存失败: {file_path}, 错误: {e}")
        if raise_on_error:
            raise
        return False


async def save_file_async(
    file_path: str,
    content: str,
    mode: str = 'w',
    encoding: str = 'utf-8',
    logger: logging.Logger = None,
    raise_on_error: bool = False
) -> bool:
    """
    异步通用文件保存函数，支持 .txt, .md, .html 等

    :param file_path: 文件路径，例如 'example.md'
    :param content: 文件内容
    :param mode: 写入模式，'w' 覆盖，'a' 追加
    :param encoding: 文件编码，默认 'utf-8'
    :param logger: 日志收集器
    :param raise_on_error: 是否在出错时抛出异常
    :return: 保存成功返回 True，否则 False
    """
    try:
        path = Path(file_path)
        # 检查文件名长度
        if len(str(path)) > 255:
            raise OSError(f"文件名过长: {file_path}")

        # 确保目录存在
        path.parent.mkdir(parents=True, exist_ok=True)

        # 异步写入文件
        async with aiofiles.open(path, mode, encoding=encoding) as f:
            await f.write(content)

        if logger:
            logger.info(f"文件保存成功: {file_path}")
        else:
            print(f"文件保存成功: {file_path}")
        return True

    except Exception as e:
        if logger:
            logger.error(f"文件保存失败 [async]: {file_path}, 错误: {e}", exc_info=True)
        else:
            print(f"文件保存失败 [async]: {file_path}, 错误: {e}")
        if raise_on_error:
            raise
        return False


async def save_files_batch(file_data: List[Tuple[str, str]], max_concurrency: int = 10, logger: logging.Logger = None):
    """
    批量异步保存文件
    :param file_data: List[(file_path, content)]
    :param max_concurrency: 最大并发数
    :param logger: 日志收集器
    """
    semaphore = asyncio.Semaphore(max_concurrency)

    async def sem_save(file_path: str, content: str):
        async with semaphore:
            return await save_file_async(file_path, content, logger=logger)

    tasks = [sem_save(path, content) for path, content in file_data]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results


def load_file(file_path: str, mode: str = 'r', encoding: str = 'utf-8', logger: logging.Logger = None, raise_on_error: bool = False) -> str | None:
    """
    通用文件读取函数，支持 .txt, .md, .html 等

    :param file_path: 文件路径，例如 'example.md'
    :param mode: 读取模式，'r' 、'rb'
    :param encoding: 文件编码，默认 'utf-8'
    :param logger: 日志收集器
    :param raise_on_error: 是否在出错时抛出异常
    :return: 文件内容字符串，失败时返回 None
    """
    try:
        path = Path(file_path)
        # 检查文件是否存在
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        if not path.is_file():
            raise IsADirectoryError(f"路径不是文件: {file_path}")

        # 读取文件内容
        with open(path, mode, encoding=encoding) as f:
            content = f.read()

        if logger:
            logger.info(f"文件读取成功: {file_path}")
        else:
            print(f"文件读取成功: {file_path}")
        return content
    except Exception as e:
        if logger:
            logger.error(f"文件读取失败: {file_path}, 错误: {e}", exc_info=True)
        else:
            print(f"文件读取失败: {file_path}, 错误: {e}")
        if raise_on_error:
            raise
        return None


async def load_file_async(
    file_path: str,
    mode: str = 'r',
    encoding: str = 'utf-8',
    logger: logging.Logger = None,
    raise_on_error: bool = False
) -> str | None:
    """
    异步文件读取函数，支持 .txt, .md, .html 等

    :param file_path: 文件路径，例如 'example.md'
    :param mode: 读取模式，'r' 、'rb'
    :param encoding: 文件编码，默认 'utf-8'
    :param logger: 日志收集器
    :param raise_on_error: 是否在出错时抛出异常
    :return: 文件内容字符串，失败时返回 None
    """
    try:
        path = Path(file_path)
        # 检查文件是否存在
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        if not path.is_file():
            raise IsADirectoryError(f"路径不是文件: {file_path}")

        # 异步读取文件
        async with aiofiles.open(path, mode, encoding=encoding) as f:
            content = await f.read()

        if logger:
            logger.info(f"文件读取成功: {file_path}")
        else:
            print(f"文件读取成功: {file_path}")
        return content
    except Exception as e:
        if logger:
            logger.error(f"文件读取失败: {file_path}, 错误: {e}", exc_info=True)
        else:
            print(f"文件读取失败: {file_path}, 错误: {e}")
        if raise_on_error:
            raise
        return None


def get_file_size(file_path):
    """
    获取文件大小
    :param:  file_path:文件路径（带文件名）
    :return: file_size：文件大小
    """
    if os.path.exists(file_path):
        return os.path.getsize(file_path)
    else:
        return 0