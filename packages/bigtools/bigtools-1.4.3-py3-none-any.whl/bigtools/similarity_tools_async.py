# -*- coding: UTF-8 -*-
# @Time : 2025/10/13 16:35
# @Author : 刘洪波
"""
异步
计算相似度的工具
"""

import asyncio
from typing import Set, List, Tuple, Union, Optional
from bigtools.stop_words import stopwords
from bigtools.jieba_tools import jieba_tokenizer_async
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from bm25s.tokenization import Tokenized
from bigtools.similarity_tools import ReturnedTFIDFSimilarities


class TfidfChineseRetrieverAsync:
    def __init__(self, stop_words: Set[str] = stopwords,
                 ngram_range: Tuple[int, int] = (1, 1), max_features: int = None):
        """
        异步
        中文 TF-IDF 检索器
        :param stop_words: 停用词集合
        :param ngram_range: ngram 范围
        :param max_features: 最大特征数
        """
        self.stop_words = stop_words or set()
        self.ngram_range = ngram_range
        self.max_features = max_features
        self.vectorizer = None
        self.doc_vectors = None

    @classmethod
    async def create(cls, documents: List[str],
                     stop_words: Set[str] = None,
                     ngram_range: Tuple[int, int] = (1, 1),
                     max_features: int = None):
        """
        异步构造器
        """
        self = cls(stop_words=stop_words, ngram_range=ngram_range, max_features=max_features)
        tokenized_docs = await self.tokenize_docs_async(documents)
        await self._fit_transform(tokenized_docs)
        return self

    async def tokenize_doc(self, doc):
        return await jieba_tokenizer_async(doc, self.stop_words)

    async def tokenize_docs_async(self, docs: List[str]) -> List[List[str]]:
        """
        异步批量分词
        """
        return await asyncio.gather(*(self.tokenize_doc(doc) for doc in docs))

    async def _fit_transform(self, tokenized_docs: List[List[str]]):
        docs_as_strings = [" ".join(tokens) for tokens in tokenized_docs]

        def sync_fit_transform():
            self.vectorizer = TfidfVectorizer(
                tokenizer=lambda x: x.split(),
                ngram_range=self.ngram_range,
                max_features=self.max_features
            )
            return self.vectorizer.fit_transform(docs_as_strings)

        self.doc_vectors = await asyncio.to_thread(sync_fit_transform)

    async def _vectorize_query(self, query: Union[str, List[str]]):
        """
        支持单条字符串或列表
        """
        if isinstance(query, str):
            query = [query]

        tokenized_queries = await asyncio.gather(*(self.tokenize_doc(q) for q in query))
        query_as_strings = [" ".join(tokens) for tokens in tokenized_queries]

        def sync_transform():
            return self.vectorizer.transform(query_as_strings)

        return await asyncio.to_thread(sync_transform)

    async def query(self, query: Union[str, List[str]]) -> ReturnedTFIDFSimilarities:
        """
        查询文档相似度
        :param query: 查询文本（str 或 list[str]）
        :return: ReturnedTFIDFSimilarities 对象
        """
        return ReturnedTFIDFSimilarities(await self.query_similarity(query))

    async def query_similarity(self, query: Union[str, List[str]]):
        """
        查询文档相似度
        :param query: 查询文本（str 或 list[str]）
        :return:
        """
        query_vector = await self._vectorize_query(query)

        def sync_kernel():
            return linear_kernel(query_vector, self.doc_vectors).flatten()

        return await asyncio.to_thread(sync_kernel)

    async def query_topk(self, query: Union[str, List[str]], top_k: int = 10):
        """
        查询文档相似度， 返回前top_k个结果
        :param query: 查询文本（str 或 list[str]）
        :param top_k: 返回前 k 个结果（可选）
        :return: ReturnedSimilarities 对象
        """
        results = await self.query(query)
        return results.topk(top_k)


async def calculate_chinese_tfidf_similarity_async(query: list, documents: list, top_k: int = None, stop_words: Set[str] = stopwords,
                                       ngram_range=(1,1), max_features=None):
    """
    异步
    中文 TF-IDF 文档检索器，计算TF-IDF相似度
    :param query: 查询语句
    :param documents: 待查询的文本
    :param top_k: 返回前 k 个结果（可选）
    :param stop_words: 停用词
    :param ngram_range: tuple, ngram 范围
    :param max_features: 最大特征数
    :return:
    """
    retriever = await TfidfChineseRetrieverAsync.create(documents, stop_words, ngram_range, max_features)
    if top_k:
        return await retriever.query_topk(query, top_k)
    return await retriever.query(query)


class BM25ChineseRetrieverAsync:
    """
    异步
    中文 BM25 检索器
    Based on the paper, BM25S offers the following variants:
        Original (method="robertson")
        ATIRE (method="atire")
        BM25L (method="bm25l")
        BM25+ (method="bm25+")
        Lucene (method="lucene") - default
    """
    def __init__(self, method: str = "lucene", stop_words: Optional[set] = stopwords):
        """
        初始化中文 BM25 检索器
        :param method (str): BM25 变体，可选 "robertson", "atire", "bm25l", "bm25+", "lucene"（默认）
        :param stop_words (set, optional): 自定义停用词集合。默认使用内置 stopwords
        """
        self.method = method
        self.stop_words = stop_words
        self.documents = []
        self.corpus_tokens = []
        self.retriever = None

    @classmethod
    async def create(cls, documents: List[str], method: str = "lucene", stop_words: Optional[set] = None):
        """
        异步构造器
        :param documents: 文档
        """
        self = cls(method=method, stop_words=stop_words)
        self.documents = documents
        self.corpus_tokens = await self.tokenize_docs_async(documents)
        await self._build_index()
        return self

    async def tokenize_doc(self, text: str) -> List[str]:
        return await jieba_tokenizer_async(text, self.stop_words)

    async def tokenize_docs_async(self, texts: List[str]) -> List[List[str]]:
        """
        异步批量分词
        """
        return await asyncio.gather(*(self.tokenize_doc(text) for text in texts))

    async def _build_index(self):
        """
        异步构建 BM25 索引
        """
        def sync_build():
            import bm25s  # 确保在子线程中导入
            self.retriever = bm25s.BM25(method=self.method)
            self.retriever.index(self.corpus_tokens)
        await asyncio.to_thread(sync_build)

    async def tokenize(self, texts: Union[str, List[str]], return_ids: bool = True) -> Union[List[List[str]], Tokenized]:
        """
        对文本进行分词，支持返回 token 列表或 Tokenized 对象（含 vocab）。
        :param texts:  文本列表
        :param return_ids: 是否返回文本的ID
        :return:
        """
        if isinstance(texts, str):
            texts = [texts]

        if not return_ids:
            return await self.tokenize_docs_async(texts)

        # 构建 token 到 id 的映射
        token_to_index = {}
        corpus_ids = []

        for text in texts:
            tokens = await self.tokenize_doc(text)
            doc_ids = []
            for token in tokens:
                if token not in token_to_index:
                    token_to_index[token] = len(token_to_index)
                doc_ids.append(token_to_index[token])
            corpus_ids.append(doc_ids)

        return Tokenized(ids=corpus_ids, vocab=token_to_index)

    async def retrieve(self, queries: Union[str, List[str]], top_k: int = None) -> List[dict]:
        """
        检索最相关的文档。
        :param queries: 单个查询字符串或查询字符串列表
        :param top_k: 返回 top-k 结果
        :return: List of dicts, each with keys: 'query', 'scores', 'documents'
        """
        if isinstance(queries, str):
            queries = [queries]

        if not top_k:
            top_k = len(self.documents)
            if top_k > 10:
                top_k = 10

        results = []
        for query in queries:
            query_tokens = await self.tokenize(query, return_ids=False)

            def sync_retrieve():
                _docs, _scores = self.retriever.retrieve(query_tokens, k=top_k)
                return _docs, _scores

            docs, scores = await asyncio.to_thread(sync_retrieve)
            results.append({
                "query": query,
                "scores": scores[0].tolist(),
                "documents": docs[0].tolist()
            })
        return results


async def calculate_chinese_bm25_similarity_async(query: list, documents: list, method: str = "lucene",
                                      stop_words: Set[str] = stopwords, top_k: int = None):
    """
    异步
    计算中文 BM25 相似度
    :param query: 查询语句
    :param documents: 待查询的文本
    :param method: BM25 变体，可选 "robertson", "atire", "bm25l", "bm25+", "lucene"（默认）
    :param top_k: 返回前 k 个结果（可选）
    :param stop_words: 停用词
    :return:
    """
    # 初始化类, 构建索引
    retriever = await BM25ChineseRetrieverAsync.create(documents=documents, method=method, stop_words=stop_words)
    # 检索
    return await retriever.retrieve(query, top_k=top_k)
