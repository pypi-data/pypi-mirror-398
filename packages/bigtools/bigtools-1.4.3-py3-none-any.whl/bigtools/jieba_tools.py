# -*- coding: UTF-8 -*-
# @Time : 2023/11/15 18:18 
# @Author : 刘洪波
import jieba
from bigtools.stop_words import stopwords
from typing import List, Set


def get_keywords_from_text(text: str, stop_words: Set[str] = stopwords) -> List[str]:
    """
    从文本中获取关键词
    :param text:  待提取的文本
    :param stop_words: 停用词
    :return:
    """
    return [i.strip() for i in jieba.cut(text) if i.strip() and i.strip() not in stop_words]


async def get_keywords_from_text_async(text: str, stop_words: Set[str] = stopwords):
    """
    异步从文本中获取关键词
    :param text:  待提取的文本
    :param stop_words: 停用词
    :return:
    """
    return [i.strip() for i in jieba.cut(text) if i.strip() and i.strip() not in stop_words]


def jieba_tokenizer(text: str, stop_words: Set[str] = stopwords) -> List[str]:
    """
    中文分词并过滤停用词和空白词。
    :param text:  待分词的文本
    :param stop_words: 停用词
    :return:
    """
    return [word for word in jieba.lcut(text) if word.strip() and word not in stop_words]


async def jieba_tokenizer_async(text: str, stop_words: Set[str] = stopwords) -> List[str]:
    """
    中文分词并过滤停用词和空白词。
    :param text:  待分词的文本
    :param stop_words: 停用词
    :return:
    """
    return [word for word in jieba.lcut(text) if word.strip() and word not in stop_words]
