# -*- coding: UTF-8 -*-
# @Time : 2023/11/15 16:35 
# @Author : 刘洪波
"""
计算相似度的工具
"""
import jieba
import numpy as np
from typing import Set, List, Tuple, Union, Optional, Dict, Callable
from bigtools.stop_words import stopwords
from bigtools.jieba_tools import jieba_tokenizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import bm25s
from bm25s.tokenization import Tokenized
from sklearn.metrics.pairwise import cosine_similarity

# sklearn里的更好，这个太简单了
# def cosine_similarity(vector1: np.array, vector2: np.array):
#     """计算两个向量的余弦相似度"""
#     return vector1.dot(vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))


class ReturnedTFIDFSimilarities:
    def __init__(self, similarities):
        self.similarities = similarities

    def tolist(self):
        return self.similarities.tolist()

    def argsorted(self, reverse=True):
        if reverse:
            return self.similarities.argsort()[::-1]
        else:
            return self.similarities.argsort()

    def sort(self, reverse=True):
        data = list(enumerate(self.similarities))
        data.sort(key=lambda x: x[1], reverse=reverse)
        return data

    def topk(self, k=10):
        return self.sort()[:k]


class TfidfChineseRetriever:
    def __init__(self, documents: List[str], stop_words: Set[str] = stopwords,
                 ngram_range: Tuple[int, int] = (1, 1), max_features: int = None):
        """
        中文 TF-IDF 检索器
        :param documents: 文档列表
        :param stop_words: 停用词集合
        :param ngram_range: ngram 范围
        :param max_features: 最大特征数
        """
        self.vectorizer = TfidfVectorizer(tokenizer=lambda text: jieba_tokenizer(text, stop_words),
                                          ngram_range=ngram_range, max_features=max_features)
        self.doc_vectors = self.vectorizer.fit_transform(documents)

    def query(self, query: List[str]) -> ReturnedTFIDFSimilarities:
        """
        查询文档相似度
        :param query: 查询文本（str 或 list[str]）
        :return: ReturnedTFIDFSimilarities 对象
        """
        return ReturnedTFIDFSimilarities(self.query_similarity(query))

    def query_similarity(self, query: List[str]):
        """
        查询文档相似度
        :param query: 查询文本（str 或 list[str]）
        :return:
        """
        query_vector = self.vectorizer.transform(query)
        similarities = linear_kernel(query_vector, self.doc_vectors).flatten()
        return similarities

    def query_topk(self, query: List[str], top_k: int = 10):
        """
        查询文档相似度， 返回前top_k个结果
        :param query: 查询文本（str 或 list[str]）
        :param top_k: 返回前 k 个结果（可选）
        :return: ReturnedSimilarities 对象
        """
        return self.query(query).topk(top_k)


def calculate_chinese_tfidf_similarity(query: list, documents: list, top_k: int = None, stop_words: Set[str] = stopwords,
                                       ngram_range=(1,1), max_features=None):
    """
    中文 TF-IDF 文档检索器，计算TF-IDF相似度
    :param query: 查询语句
    :param documents: 待查询的文本
    :param top_k: 返回前 k 个结果（可选）
    :param stop_words: 停用词
    :param ngram_range: tuple, ngram 范围
    :param max_features: 最大特征数
    :return:
    """
    tf = TfidfChineseRetriever(documents, stop_words, ngram_range, max_features)
    if top_k:
        return tf.query_topk(query, top_k)
    return tf.query(query)


class BM25ChineseRetriever:
    """
    中文 BM25 检索器
    Based on the paper, BM25S offers the following variants:
        Original (method="robertson")
        ATIRE (method="atire")
        BM25L (method="bm25l")
        BM25+ (method="bm25+")
        Lucene (method="lucene") - default
    """
    def __init__(self, documents: List[str], method: str = "lucene", stop_words: Optional[set] = stopwords):
        """
        初始化中文 BM25 检索器
        :param documents: 文档
        :param method (str): BM25 变体，可选 "robertson", "atire", "bm25l", "bm25+", "lucene"（默认）
        :param stop_words (set, optional): 自定义停用词集合。默认使用内置 stopwords
        """
        self.method = method
        self.stop_words = stop_words
        self.documents = documents
        self.corpus_tokens = self.tokenize(self.documents)
        self.retriever = bm25s.BM25(method=method)
        self.retriever.index(self.corpus_tokens)

    def tokenize(self, texts: Union[str, List[str]], return_ids: bool = True) -> Union[List[List[str]], Tokenized]:
        """
        对文本进行分词，支持返回 token 列表或 Tokenized 对象（含 vocab）。
        :param texts:  文本列表
        :param return_ids: 是否返回文本的ID
        :return:
        """
        if isinstance(texts, str):
            texts = [texts]

        if not return_ids:
            return [jieba_tokenizer(text, self.stop_words) for text in texts]

        # 构建 token 到 id 的映射
        token_to_index = {}
        corpus_ids = []

        for text in texts:
            tokens = jieba_tokenizer(text, self.stop_words)
            doc_ids = []
            for token in tokens:
                if token not in token_to_index:
                    token_to_index[token] = len(token_to_index)
                doc_ids.append(token_to_index[token])
            corpus_ids.append(doc_ids)

        return Tokenized(ids=corpus_ids, vocab=token_to_index)

    def retrieve(self, queries: Union[str, List[str]], top_k: int = None) -> List[dict]:
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
            query_tokens = self.tokenize(query, return_ids=False)
            docs, scores = self.retriever.retrieve(query_tokens, k=top_k)
            results.append({
                "query": query,
                "scores": scores[0].tolist(),
                "documents": docs[0].tolist()
            })
        return results


def calculate_chinese_bm25_similarity(query: list, documents: list, method: str = "lucene",
                                      stop_words: Set[str] = stopwords, top_k: int = None):
    """
    计算中文 BM25 相似度
    :param query: 查询语句
    :param documents: 待查询的文本
    :param method: BM25 变体，可选 "robertson", "atire", "bm25l", "bm25+", "lucene"（默认）
    :param top_k: 返回前 k 个结果（可选）
    :param stop_words: 停用词
    :return:
    """
    # 初始化类, 构建索引
    retriever = BM25ChineseRetriever(documents=documents, method=method, stop_words=stop_words)
    # 检索
    return retriever.retrieve(query, top_k=top_k)


def calculate_chinese_keyword_similarity_simple(query_keywords: List[str], document: str,
                                                lowercase: bool = True,
                                                enable_tokenization: bool = False,
                                                stop_words: Optional[Set[str]] = stopwords,
                                                ) -> float:
    """
    计算文档与关键词列表的匹配相似度。
    布尔匹配（Boolean Match）
    思想：只要文档包含任意一个关键词就算匹配，并计数。
    :param query_keywords: 查询关键词列表
    :param document: 文本内容
    :param lowercase: 是否自动转小写（对英文友好）
    :param enable_tokenization: 是否进行分词，句子过长建议进行。
    :param stop_words: 可选，停用词集合，用于过滤无意义词，仅enable_tokenization为True时有用
    :return: 匹配比例（0~1）
    """
    # === Step 1: 关键词标准化 ===
    if not query_keywords:
        return 0.0

    normalized_keywords = [
        kw.strip().lower() if lowercase else kw.strip()
        for kw in query_keywords
        if kw.strip()
    ]
    if not normalized_keywords:
        return 0.0

    # === Step 2: 文本标准化 ===
    if lowercase:
        document = document.lower()
    doc_words = document

    # === Step 3: 是否进行文本分词 ===
    if enable_tokenization:
        # tokens = jieba.lcut(document)
        # if lowercase:
        #     tokens = [w.lower() for w in tokens]
        tokens = jieba.lcut(document)

        # 停用词过滤 + 去重 ===
        if stop_words:
            doc_words = set(w for w in tokens if w.strip() and w not in stop_words)
        else:
            doc_words = set(w for w in tokens if w.strip())

        if not doc_words:
            return 0.0

    # === Step 4: 匹配计数 ===
    matched = sum(1 for kw in normalized_keywords if kw in doc_words)
    return matched / len(normalized_keywords)


def find_dense_keyword_groups(query_keywords: List[str], text: str, split_size: int = 50, min_keywords_per_group: int = 2,
                              lowercase: bool = True) -> List[Dict[str, object]]:
    """
    找出文本中关键词密集出现的区域，并返回关键词组及对应文本片段。
    :param query_keywords: 关键词
    :param text: 文本
    :param split_size: 分割text的窗口大小，
    :param min_keywords_per_group: 最小密集组
    :param lowercase: 是否自动转小写（对英文友好）
    :return:
        返回每个密集区域的：
          - keywords: 关键词集合
          - text_snippet: 对应的文本片段
          - start: 起始索引
          - end: 结束索引
    """
    if not text or not query_keywords:
        return []

    normalized_keywords = [
        kw.strip().lower() if lowercase else kw.strip()
        for kw in query_keywords
        if kw.strip()
    ]
    if not normalized_keywords:
        return []

    if lowercase:
        text = text.lower()

    text_len = len(text)
    all_matches = []
    for i in range(int(len(text) / split_size)):
        start, end = i * split_size, (i + 1) * split_size if (i + 1) * split_size else text_len
        text_snippet = text[start: end]
        region_keywords = []
        for kk in normalized_keywords:
            if kk in text_snippet:
                region_keywords.append(kk)
        if len(region_keywords) >= min_keywords_per_group:
            all_matches.append({
                'keywords': region_keywords,
                'text_snippet': text_snippet,
                'start': start,
                'end': end
            })
    return all_matches


class EmbeddingSimilarity:
    """
    使用 Embedding 进行相似度计算
    适合排序，不适合大规模检索
    """
    def __init__(self, embedding_function: Callable[[Union[str, list[str]]], np.ndarray]):
        """
        初始化 EmbeddingSimilarity
        :param embedding_function: 用于将文本转为向量的函数，可以是异步或同步的，也必须使用相应的类方法
                    1. 同步 (def embedding_function(texts) -> np.ndarray)
                    2. 异步 (async def embedding_function(texts) -> np.ndarray)
        """
        self.embedding_function = embedding_function

    def calculate_similarity(self, query: str, documents: list[str]) -> list:
        """
        计算相似度
        :param query: 查询的文本
        :param documents: 文档
        :return:
        """
        query_emb = self.embedding_function(query).reshape(1, -1)
        documents_emb = self.embedding_function(documents)
        sims = cosine_similarity(query_emb, documents_emb)[0]
        return sims.tolist()

    def calculate_similarity_by_dense_keyword_groups(self, query: str, query_keywords: list[str], documents: list[str],
                                                     split_size: int = 50, min_keywords_per_group: int = 2,
                                                     lowercase: bool = True) -> list:
        """
        先找到关键词密集的文本，再进行Embedding 与 计算Similarity
        :param query: 查询的语句
        :param query_keywords: 关键词
        :param documents:
        :param split_size: 分割text的窗口大小，
        :param min_keywords_per_group: 最小密集组
        :param lowercase: 是否自动转小写（对英文友好）
        :return:
        """
        # 获取 query 向量
        query_emb = self.embedding_function([query]).reshape(1, -1)

        max_list = []

        for doc in documents:
            # === Step 1: 计算分组窗口宽度 ===
            len_test_text = len(doc)
            avg_sentence_len = len_test_text / max(1, len(doc.split('。')))
            wd = int(avg_sentence_len / split_size + 1) * split_size

            # === Step 2: 找出关键词密集片段 ===
            keyword_groups = find_dense_keyword_groups(query_keywords, doc, wd, min_keywords_per_group, lowercase)
            if not keyword_groups:
                max_list.append(0.0)
                continue

            # === Step 3: 批量提取文本片段 ===
            snippets = [v["text_snippet"] for v in keyword_groups]

            # === Step 4: 批量获取嵌入（一次性） ===
            text_embs = self.embedding_function(snippets)

            # === Step 5: 一次性计算所有相似度 ===
            sims = cosine_similarity(query_emb, text_embs)[0]

            # === Step 6: 取最大相似度作为该文档得分 ===
            max_list.append(float(np.max(sims)))
        return max_list

    async def calculate_similarity_async(self, query: str, documents: list[str]) -> list:
        """
        异步
        计算相似度
        :param query: 查询的文本
        :param documents: 文档
        :return:
        """
        query_emb = (await self.embedding_function(query)).reshape(1, -1)
        documents_emb = await self.embedding_function(documents)
        sims = cosine_similarity(query_emb, documents_emb)[0]
        return sims.tolist()

    async def calculate_similarity_by_dense_keyword_groups_async(self, query: str, query_keywords: list[str],
                                                                 documents: list[str], split_size: int = 50,
                                                                 min_keywords_per_group: int = 2,
                                                                 lowercase: bool = True) -> list:
        """
        :param query: 查询的语句
        :param query_keywords: 关键词
        :param documents:
        :param split_size: 分割text的窗口大小，
        :param min_keywords_per_group: 最小密集组
        :param lowercase: 是否自动转小写（对英文友好）
        :return:
        """
        # 获取 query 向量
        query_emb = (await self.embedding_function([query])).reshape(1, -1)

        max_list = []

        for doc in documents:
            # === Step 1: 计算分组窗口宽度 ===
            len_test_text = len(doc)
            avg_sentence_len = len_test_text / max(1, len(doc.split('。')))
            wd = int(avg_sentence_len / split_size + 1) * split_size

            # === Step 2: 找出关键词密集片段 ===
            keyword_groups = find_dense_keyword_groups(query_keywords, doc, wd, min_keywords_per_group, lowercase)
            if not keyword_groups:
                max_list.append(0.0)
                continue

            # === Step 3: 批量提取文本片段 ===
            snippets = [v["text_snippet"] for v in keyword_groups]

            # === Step 4: 批量获取嵌入（一次性） ===
            text_embs = await self.embedding_function(snippets)

            # === Step 5: 一次性计算所有相似度 ===
            sims = cosine_similarity(query_emb, text_embs)[0]

            # === Step 6: 取最大相似度作为该文档得分 ===
            max_list.append(float(np.max(sims)))
        return max_list
