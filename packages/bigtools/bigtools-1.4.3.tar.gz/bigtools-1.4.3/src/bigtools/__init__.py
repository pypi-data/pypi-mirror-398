# -*- coding: UTF-8 -*-
# @Time : 2023/9/26 18:34 
# @Author : 刘洪波

"""加密验证工具"""
from bigtools.auth_tools import generate_api_key, compute_key_hmac, generate_hmac_signature, verify_hmac_signature
from bigtools.auth_tools import dict_to_urlsafe_b64, urlsafe_b64_to_dict, merge_method_dict, merge_str, SignatureGenerator
from bigtools.auth_tools import verify_signature, refresh_signature, build_jwt_token, build_and_encode_jwt_token
"""数据库工具"""
from bigtools.db_tools import mongo_client, async_mongo_client, MinioClient, RedisClient, AsyncElasticsearchClient
from bigtools.db_tools import ElasticsearchClient, AsyncElasticsearchClient
"""常用的一些数据"""
from bigtools.default_data import headers, random_headers, user_agents, ContentType, en_letter, numbers, DateType, RePattern
"""下载工具"""
from bigtools.download_tools import get_requests_session, download_stream_data, save_stream_data
from bigtools.download_tools import download_stream_data_async, save_stream_data_async
"""异常处理工具"""
from bigtools.exception_tools import RequestExceptionHandler, UniversalExceptionHandler
"""文件处理相关工具"""
from bigtools.file_tools import get_file_size, save_file, save_file_async, save_files_batch, load_file, load_file_async
"""hash工具"""
from bigtools.hash_tools import generate_hash_value, HASH_FUNCTIONS, HashGenerator
"""jieba工具"""
from bigtools.jieba_tools import get_keywords_from_text, get_keywords_from_text_async, jieba_tokenizer
"""json工具"""
from bigtools.json_tools import save_json_data, save_json_data_sync, save_json_data_async
from bigtools.json_tools import load_json_data, load_json_data_sync, load_json_data_async
from bigtools.json_tools import pretty_print_json, validate_json_schema, validate_json_string
from bigtools.json_tools import save_json_data_by_orjson, save_json_data_sync_by_orjson, save_json_data_async_by_orjson
from bigtools.json_tools import load_json_data_by_orjson, load_json_data_sync_by_orjson, load_json_data_async_by_orjson
from bigtools.json_tools import pretty_print_orjson, validate_orjson_string
"""日志工具"""
from bigtools.log_tools import set_log, SetLog
"""其他未分类的工具"""
from bigtools.more_tools import extract_ip, equally_split_list_or_str, load_config
from bigtools.more_tools import set_env, load_env, FuncTimer, time_sleep, count_str_start_or_end_word_num
from bigtools.more_tools import is_chinese, is_english, is_number, generate_random_string, sort_with_index, sort_dict_by_value
"""路径处理工具"""
from bigtools.path_tools import check_make_dir, get_execution_dir, get_file_type, get_execution_file_name
"""美化显示工具"""
from bigtools.print_tools import pretty_print
"""相似度计算工具"""
from bigtools.similarity_tools import cosine_similarity
from bigtools.similarity_tools import TfidfChineseRetriever, calculate_chinese_tfidf_similarity
from bigtools.similarity_tools import BM25ChineseRetriever, calculate_chinese_bm25_similarity
from bigtools.similarity_tools import calculate_chinese_keyword_similarity_simple, find_dense_keyword_groups
from bigtools.similarity_tools import EmbeddingSimilarity
"""相似度计算工具 异步"""
from bigtools.similarity_tools_async import TfidfChineseRetrieverAsync, calculate_chinese_tfidf_similarity_async
from bigtools.similarity_tools_async import BM25ChineseRetrieverAsync, calculate_chinese_bm25_similarity_async
"""停用词大全"""
from bigtools.stop_words import stopwords
"""yaml工具"""
from bigtools.yaml_tools import load_yaml, load_all_yaml, write_yaml


__all__ = [
    # 加密验证工具
    "generate_api_key", "compute_key_hmac", "generate_hmac_signature", "verify_hmac_signature",
    "dict_to_urlsafe_b64", "urlsafe_b64_to_dict", "merge_method_dict", "merge_str", "SignatureGenerator",
    "verify_signature", "refresh_signature", "build_jwt_token", "build_and_encode_jwt_token",
    # 数据库工具
    "mongo_client", "async_mongo_client", "MinioClient", "RedisClient", "AsyncElasticsearchClient",
    "ElasticsearchClient",
    # 常用的一些数据
    "headers", "random_headers", "user_agents", "ContentType", "en_letter", "numbers", "DateType", "RePattern",
    # 下载工具
    "get_requests_session", "download_stream_data", "save_stream_data",
    "download_stream_data_async", "save_stream_data_async",
    # 异常处理工具
    "RequestExceptionHandler", "UniversalExceptionHandler",
    # 文件处理相关工具
    "get_file_size", "save_file", "save_file_async", "save_files_batch", "load_file", "load_file_async",
    # hash工具
    "generate_hash_value", "HASH_FUNCTIONS", "HashGenerator",
    # jieba工具
    "get_keywords_from_text", "get_keywords_from_text_async", "jieba_tokenizer",
    # json工具
    "save_json_data", "save_json_data_sync", "save_json_data_async",
    "load_json_data", "load_json_data_sync", "load_json_data_async",
    "pretty_print_json", "validate_json_schema", "validate_json_string",
    "save_json_data_by_orjson", "save_json_data_sync_by_orjson", "save_json_data_async_by_orjson",
    "load_json_data_by_orjson", "load_json_data_sync_by_orjson", "load_json_data_async_by_orjson",
    "pretty_print_orjson", "validate_orjson_string",
    # 日志工具
    "set_log", "SetLog",
    # 其他未分类的工具
    "extract_ip", "equally_split_list_or_str", "load_config",
    "set_env", "load_env", "FuncTimer", "time_sleep", "count_str_start_or_end_word_num",
    "is_chinese", "is_english", "is_number", "generate_random_string", "sort_with_index", "sort_dict_by_value",
    # 路径处理工具
    "check_make_dir", "get_execution_dir", "get_file_type", "get_execution_file_name",
    # 美化显示工具
    "pretty_print",
    # 相似度计算工具
    "cosine_similarity",
    "TfidfChineseRetriever", "calculate_chinese_tfidf_similarity",
    "BM25ChineseRetriever", "calculate_chinese_bm25_similarity",
    "calculate_chinese_keyword_similarity_simple", "find_dense_keyword_groups",
    "EmbeddingSimilarity",
    # 相似度计算工具 异步
    "TfidfChineseRetrieverAsync", "calculate_chinese_tfidf_similarity_async",
    "BM25ChineseRetrieverAsync", "calculate_chinese_bm25_similarity_async",
    # 停用词大全
    "stopwords",
    # yaml工具
    "load_yaml", "load_all_yaml", "write_yaml",
]