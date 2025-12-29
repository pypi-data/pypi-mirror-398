# -*- coding: UTF-8 -*-
# @Time : 2023/9/27 17:58 
# @Author : 刘洪波
import time
import random
import requests
import aiohttp
import aiofiles
import asyncio
import logging
from tqdm import tqdm
from tqdm.asyncio import tqdm as tqdm_async
from requests.adapters import HTTPAdapter
from bigtools.file_tools import get_file_size
from bigtools.default_data import headers as df_headers
from bigtools.exception_tools import RequestExceptionHandler


def get_requests_session(max_retries: int = 3):
    """
    使用requests Session，使抓取数据的时候可以重试
    # 默认设置重试次数为3次
    """
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=max_retries))
    session.mount('https://', HTTPAdapter(max_retries=max_retries))
    return session


def save_stream_data(response, total: int, file_path: str, initial: int = 0):
    """
    保存响应数据
    :param response: 请求响应
    :param total: 数据大小
    :param file_path: 保存的数据路径
    :param initial: 进度条初始化大小
    :return:
    """
    file_op = 'ab' if initial else 'wb'
    with open(file_path, file_op) as file, tqdm(
        desc=file_path,
        total=total,
        initial=initial,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)


# 下载数据
def download_stream_data(url: str, file_path: str, headers: dict = df_headers, read_timeout: int = 15,
             resume: bool = True, max_retries: int = 3, logger: logging.Logger = None):
    """
    下载流式传输的文件，比如：压缩包、音频、视频等等
    :param url: 文件下载链接
    :param file_path: 文件保存路径
    :param headers: 请求头
    :param read_timeout:
    :param resume: 是否断点续传，默认进行断点续传。值为True进行断点续传；值为False从头开始下载，不进行断点续传。
    :param max_retries: 最大重试次数，网络不好时增大 max_retries
    :param logger: 日志收集器
    :return:
    """
    if 'Range' in headers:
        del headers['Range']

    requests_session = get_requests_session(max_retries)

    @RequestExceptionHandler(logger=logger)
    def get_data():
        return requests_session.get(url, headers=headers, stream=True, timeout=(read_timeout, 5))

    response = get_data()
    if response:
        total = int(response.headers.get('content-length', 0))
        if resume:
            file_size = get_file_size(file_path)
            if file_size < total:
                if file_size:
                    headers['Range'] = f'bytes={file_size}-'
                time.sleep(random.random())
                save_stream_data(get_data(), total, file_path, file_size)
            else:
                if logger:
                    logger.info(f'{file_path} ✅')
                else:
                    print(file_path, ' ✅')
        else:
            save_stream_data(response, total, file_path)


async def save_stream_data_async(response: aiohttp.ClientResponse, total: int, file_path: str, initial: int = 0):
    """
    异步保存响应数据
    :param response: aiohttp ClientResponse
    :param total: 数据大小
    :param file_path: 保存路径
    :param initial: 初始进度
    """
    file_op = "ab" if initial else "wb"
    bar = tqdm_async(
        desc=file_path,
        total=total,
        initial=initial,
        unit="iB",
        unit_scale=True,
        unit_divisor=1024,
    )

    async with aiofiles.open(file_path, file_op) as file:
        async for chunk in response.content.iter_chunked(1024):
            await file.write(chunk)
            bar.update(len(chunk))
    bar.close()  # 下载完成关闭进度条


async def download_stream_data_async(
    url: str,
    file_path: str,
    headers: dict = df_headers,
    read_timeout: int = 15,
    resume: bool = True,
    max_retries: int = 3,
    logger: logging.Logger = None
):
    """
    异步下载流式传输的文件，比如：压缩包、音频、视频等等
    :param url: 文件下载链接
    :param file_path: 文件保存路径
    :param headers: 请求头
    :param read_timeout:
    :param resume: 是否断点续传，默认进行断点续传。值为True进行断点续传；值为False从头开始下载，不进行断点续传。
    :param max_retries: 最大重试次数，网络不好时增大 max_retries
    :param logger: 日志收集器
    :return:
    """
    # 清除用户上传的Range，避免干扰
    if 'Range' in headers:
        del headers['Range']

    timeout = aiohttp.ClientTimeout(total=None, sock_read=read_timeout)
    status = True
    attempt = 0
    while status:
        attempt += 1
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # 获取文件大小
                async with session.head(url, headers=headers) as head_resp:
                    total = int(head_resp.headers.get("Content-Length", 0))

                if resume:
                    file_size = get_file_size(file_path)
                    if file_size < total:
                        if file_size:
                            headers['Range'] = f'bytes={file_size}-'
                        await asyncio.sleep(random.random())
                        async with session.get(url, headers=headers) as response:
                            await save_stream_data_async(response, total, file_path, file_size)
                    else:
                        if logger:
                            logger.info(f'{file_path} ✅')
                        else:
                            print(file_path, ' ✅')
                else:
                    async with session.get(url, headers=headers) as response:
                        await save_stream_data_async(response, total, file_path)
            status = False
        except Exception as e:
            if logger:
                logger.warning(f"下载失败({attempt}/{max_retries}) {e}")
            else:
                print(f"下载失败({attempt}/{max_retries}) {e}")
            if attempt == max_retries:
                status = False
            await asyncio.sleep(2 ** attempt)  # 指数退避重试
