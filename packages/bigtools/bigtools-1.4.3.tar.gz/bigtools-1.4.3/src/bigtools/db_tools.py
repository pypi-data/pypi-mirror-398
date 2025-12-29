# -*- coding: UTF-8 -*-
# @Time : 2023/9/27 16:28 
# @Author : 刘洪波
import redis
import logging
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from pytz import timezone
from minio.error import S3Error
from minio import Minio
import redis.asyncio as aioredis  # redis-py 4.2+ 提供 asyncio 支持
from typing import Any, List, Optional, Union, Dict, Tuple
from elasticsearch import Elasticsearch, helpers, NotFoundError, ConnectionError, AsyncElasticsearch


def mongo_client(host: str, port, user: str = None, password: str = None,
                 tz_aware: bool = False, tzinfo: str = 'Asia/Shanghai'):
    uri = f"mongodb://{host}:{port}"
    if user and password:
        uri = f"mongodb://{user}:{password}@{host}:{port}"
    elif user:
        raise ValueError('Please check user and password')
    elif password:
        raise ValueError('Please check user and password')
    if tz_aware:
        return MongoClient(uri, tz_aware=tz_aware, tzinfo=timezone(tzinfo))
    return MongoClient(uri)


def async_mongo_client(host: str, port, user: str = None, password: str = None,
                       tz_aware: bool = False, tzinfo: str = 'Asia/Shanghai'):
    uri = f"mongodb://{host}:{port}"
    if user and password:
        uri = f"mongodb://{user}:{password}@{host}:{port}"
    elif user:
        raise ValueError('Please check user and password')
    elif password:
        raise ValueError('Please check user and password')
    if tz_aware:
        return AsyncIOMotorClient(uri, tz_aware=tz_aware, tzinfo=timezone(tzinfo))
    return AsyncIOMotorClient(uri)


class MinioClient(object):
    def __init__(self, minio_endpoint: str, access_key: str, secret_key: str, secure: bool = False,
                 logger: logging.Logger = None):
        """
        Minio客户端
        :param minio_endpoint: 服务器地址
        :param access_key:  访问密钥
        :param secret_key:  秘密密钥
        :param secure: 是否使用 HTTPS，默认False 不使用
        :param logger: 日志收集器
        """
        self.clinet = Minio(
                    endpoint=minio_endpoint,
                    access_key=access_key,
                    secret_key=secret_key,
                    secure=secure
                )

        self.logger = logger or logging.getLogger(__name__)

    def check_bucket(self, bucket_name: str, create: bool=True):
        """
        检查桶状态，也可以用于创建桶， 默认创建
        注：创建桶命名限制：小写字母，句点，连字符和数字是唯一允许使用的字符（使用大写字母、下划线等命名会报错），长度至少应为3个字符
        :param bucket_name: bucket名字
        :param create:  默认为True 创建该bucket
        """
        try:
            # bucket_exists：检查桶是否存在
            if self.clinet.bucket_exists(bucket_name=bucket_name):
                self.logger.info(f"The {bucket_name} bucket already exists.")
            elif create: # 桶不存在时，create为True时创建，为False不创建
                self.clinet.make_bucket(bucket_name)
                self.logger.info(f"The {bucket_name} bucket has been created successfully.")
            return True
        except S3Error as e:
            self.logger.error(e)
        return False

    def get_bucket_list(self):
        buckets_list = []
        try:
            buckets = self.clinet.list_buckets()
            buckets_list = [{'name': bucket.name, 'creation_date': bucket.creation_date} for bucket in buckets]
            self.logger.info(f'buckets_list: {buckets_list}')
        except S3Error as e:
            self.logger.error(e)
        return buckets_list


class RedisClient:
    def __init__(self, host: str, port: int, password: str = None, logger: logging.Logger = None, max_connections: int=10):
        """
        初始化Redis客户端
        :param host: Redis服务器地址
        :param port: Redis服务器端口
        :param password: Redis服务器密码
        :param logger: 日志收集器
        :param max_connections: 最大连接数量，默认为10
        """
        self.pool = redis.ConnectionPool(
            host=host,
            port=port,
            password=password,  # 密码参数
            decode_responses=False,
            max_connections=max_connections  # 连接池容量
        )
        self.conn = redis.Redis(connection_pool=self.pool)
        self.logger = logger or logging.getLogger(__name__)

    def save(self, key: str, value: Any, ex_time: int = None) -> bool:
        """
        保存键值对到Redis（带过期时间）
        :param key: 键名
        :param value: 值
        :param ex_time: 过期时间（秒）
        :return: 操作是否成功
        """
        try:
            return self.conn.set(key, value, ex=ex_time)
        except redis.RedisError as e:
            self.logger.error(f"Redis save error: {e}")
            return False

    def get(self, key: str) -> Optional[str]:
        """
        从Redis获取值
        :param key: 键名
        :return: 值或None
        """
        try:
            return self.conn.get(key)
        except redis.RedisError as e:
            self.logger.error(f"Redis get error: {e}")
            return None

    def push_list(self, list_name: str, *values: Any, right_side: bool = False, ex_time: int = None) -> int:
        """
        向列表添加元素
        :param list_name: 列表名称
        :param values: 要添加的值
        :param right_side: 是否从右侧添加（默认左侧添加）
        :param ex_time: 过期时间（秒）
        :return: 操作后的列表长度
        """
        try:
            if right_side:
                res = self.conn.rpush(list_name, *values)
            else:
                res = self.conn.lpush(list_name, *values)
            if ex_time:
                self.conn.expire(list_name, ex_time)
            return res
        except redis.RedisError as e:
            self.logger.error(f"Redis list push error: {e}")
            return 0

    def get_list(self, list_name: str, start: int = 0, end: int = -1) -> List[str]:
        """
        获取列表范围元素
        :param list_name: 列表名称
        :param start: 起始索引
        :param end: 结束索引
        :return: 元素列表
        """
        try:
            return self.conn.lrange(list_name, start, end)
        except redis.RedisError as e:
            self.logger.error(f"Redis list range error: {e}")
            return []

    def get_list_item(self, list_name: str, index: int) -> Optional[str]:
        """
        获取列表指定位置的元素
        :param list_name: 列表名称
        :param index: 元素索引
        :return: 元素值或None
        """
        try:
            return self.conn.lindex(list_name, index)
        except redis.RedisError as e:
            self.logger.error(f"Redis list index error: {e}")
            return None

    def list_length(self, list_name: str) -> int:
        """
        获取列表长度
        :param list_name: 列表名称
        :return: 列表长度
        """
        try:
            return self.conn.llen(list_name)
        except redis.RedisError as e:
            self.logger.error(f"Redis list length error: {e}")
            return 0

    def delete_key(self, key: str) -> int:
        """
        删除指定的键（包括列表）
        :param key: 键名
        :return: 删除的键数量 (1=成功, 0=键不存在)
        """
        try:
            return self.conn.delete(key)
        except redis.RedisError as e:
            self.logger.error(f"Redis delete key error: {e}")
            return 0

    def pop_list(self, list_name: str, right_side: bool = False) -> Optional[str]:
        """
        从列表中弹出元素（移除并返回）
        :param list_name: 列表名称
        :param right_side: 是否从右侧弹出（默认左侧弹出）
        :return: 弹出的元素值或None（列表为空时）
        """
        try:
            if right_side:
                return self.conn.rpop(list_name)
            return self.conn.lpop(list_name)
        except redis.RedisError as e:
            self.logger.error(f"Redis list pop error: {e}")
            return None

    def remove_list_value(self, list_name: str, value: str, count: int = 0) -> int:
        """
        从列表中移除指定值的元素
        :param list_name: 列表名称
        :param value: 要移除的值
        :param count: 移除数量控制:
            count > 0 : 从头到尾移除最多count个匹配元素
            count < 0 : 从尾到头移除最多count个匹配元素
            count = 0 : 移除所有匹配元素
        :return: 实际移除的元素数量
        """
        try:
            return self.conn.lrem(list_name, count, value)
        except redis.RedisError as e:
            self.logger.error(f"Redis list remove error: {e}")
            return 0

    def trim_list(self, list_name: str, start: int, end: int) -> bool:
        """
        修剪列表，只保留指定范围内的元素
        :param list_name: 列表名称
        :param start: 起始索引
        :param end: 结束索引
        :return: 操作是否成功
        """
        try:
            self.conn.ltrim(list_name, start, end)
            return True
        except redis.RedisError as e:
            self.logger.error(f"Redis list trim error: {e}")
            return False

    def close(self) -> None:
        """关闭连接池"""
        self.pool.disconnect()

    # ---------------- 上下文管理器支持 ----------------
    def __enter__(self):
        """进入上下文时返回自身"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时自动关闭连接"""
        self.close()


class AsyncRedisClient:
    def __init__(self, host: str, port: int, password: str = None, logger: logging.Logger = None, max_connections: int=10):
        """
        初始化异步 Redis 客户端
        :param host: Redis服务器地址
        :param port: Redis服务器端口
        :param password: 密码
        :param logger: 日志收集器
        :param max_connections: 最大连接数量，默认为10
        """
        self.pool = aioredis.ConnectionPool(
            host=host,
            port=port,
            password=password,
            decode_responses=False,
            max_connections=max_connections
        )
        self.conn = aioredis.Redis(connection_pool=self.pool)
        self.logger = logger or logging.getLogger(__name__)

    async def save(self, key: str, value: Any, ex_time: int = None) -> bool:
        """保存键值对到Redis"""
        try:
            return await self.conn.set(key, value, ex=ex_time)
        except aioredis.RedisError as e:
            self.logger.error(f"Redis save error: {e}")
            return False

    async def get(self, key: str) -> Optional[str]:
        """获取键值"""
        try:
            return await self.conn.get(key)
        except aioredis.RedisError as e:
            self.logger.error(f"Redis get error: {e}")
            return None

    async def push_list(self, list_name: str, *values: Any, right_side: bool = False, ex_time: int = None) -> int:
        """向列表添加元素"""
        try:
            if right_side:
                res = await self.conn.rpush(list_name, *values)
            else:
                res = await self.conn.lpush(list_name, *values)
            if ex_time:
                await self.conn.expire(list_name, ex_time)
            return res
        except aioredis.RedisError as e:
            self.logger.error(f"Redis list push error: {e}")
            return 0

    async def get_list(self, list_name: str, start: int = 0, end: int = -1) -> List[str]:
        """获取列表范围元素"""
        try:
            return await self.conn.lrange(list_name, start, end)
        except aioredis.RedisError as e:
            self.logger.error(f"Redis list range error: {e}")
            return []

    async def get_list_item(self, list_name: str, index: int) -> Optional[str]:
        """获取列表指定索引元素"""
        try:
            return await self.conn.lindex(list_name, index)
        except aioredis.RedisError as e:
            self.logger.error(f"Redis list index error: {e}")
            return None

    async def list_length(self, list_name: str) -> int:
        """获取列表长度"""
        try:
            return await self.conn.llen(list_name)
        except aioredis.RedisError as e:
            self.logger.error(f"Redis list length error: {e}")
            return 0

    async def delete_key(self, key: str) -> int:
        """删除键"""
        try:
            return await self.conn.delete(key)
        except aioredis.RedisError as e:
            self.logger.error(f"Redis delete key error: {e}")
            return 0

    async def pop_list(self, list_name: str, right_side: bool = False) -> Optional[str]:
        """弹出列表元素"""
        try:
            if right_side:
                return await self.conn.rpop(list_name)
            return await self.conn.lpop(list_name)
        except aioredis.RedisError as e:
            self.logger.error(f"Redis list pop error: {e}")
            return None

    async def remove_list_value(self, list_name: str, value: str, count: int = 0) -> int:
        """移除列表中指定值"""
        try:
            return await self.conn.lrem(list_name, count, value)
        except aioredis.RedisError as e:
            self.logger.error(f"Redis list remove error: {e}")
            return 0

    async def trim_list(self, list_name: str, start: int, end: int) -> bool:
        """修剪列表"""
        try:
            await self.conn.ltrim(list_name, start, end)
            return True
        except aioredis.RedisError as e:
            self.logger.error(f"Redis list trim error: {e}")
            return False

    async def close(self) -> None:
        """关闭连接池"""
        await self.pool.disconnect()

    # ---------------- 异步上下文管理器 ----------------
    async def __aenter__(self):
        """进入上下文时返回自身"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时自动关闭连接池"""
        await self.close()


class ElasticsearchClient:
    def __init__(self, hosts: Union[str, List[str]], api_key: Optional[Union[str, Tuple[str, str]]] = None, username: str = None,
                 password: str = None, verify_certs=False, request_timeout: Optional[float] = 90, max_retries: int = 3,
                 retry_on_timeout: bool = True, es_client: Elasticsearch = None, logger: logging.Logger = None):
        """
        初始化 Elasticsearch 客户端实例，用于与 Elasticsearch 集群进行交互（如更新数据等操作）。

        参数优先级说明：
        - 若同时提供了 `api_key` 和 (`username`, `password`)，则以 `api_key` 为准。
        - 若未提供 `api_key`，则必须同时提供 `username` 和 `password`，否则抛出 ValueError。

        :param hosts: Elasticsearch 服务的主机地址。可以是单个字符串（如 "http://localhost:9200"），
                      也可以是多个地址组成的列表（如 ["http://es1:9200", "http://es2:9200"]）。
        :param api_key: 可选，HTTP 基本身份验证的凭据。
        :param username: 可选，Elasticsearch 用户名。若未提供 api_key，则必须与 password 一起提供。
        :param password: 可选，Elasticsearch 密码。若未提供 api_key，则必须与 username 一起提供。
        :param verify_certs: 是否验证 SSL 证书，默认为 False（适用于自签名证书或测试环境）。
        :param request_timeout: 每个请求的超时时间（秒），默认为 90 秒。
        :param max_retries: 请求失败时的最大重试次数，默认为 3 次。
        :param retry_on_timeout: 是否在请求超时时进行重试，默认为 True。
        :param es_client: 可传入 es_client
        :param logger: 可传入 logger
        :raises ValueError: 当既未提供 api_key，也未同时提供 username 和 password 时抛出。
        """
        basic_auth = None
        if username and password: # 以此为主
            basic_auth = (username, password)
            api_key = None
        else:
            if api_key is None:
                raise ValueError(f'api_key or (username and password) is required')
        self.es = Elasticsearch(hosts=hosts, api_key=api_key, basic_auth= basic_auth, verify_certs=verify_certs,
                                request_timeout=request_timeout, max_retries=max_retries, retry_on_timeout=retry_on_timeout)  \
            if not es_client else es_client
        self.logger = logger or logging.getLogger(__name__)

    def ping(self) -> bool:
        """检查Elasticsearch集群是否可用"""
        return self.es.ping()

    def index_exists(self, index_name: str) -> bool:
        """检查索引是否存在"""
        return self.es.indices.exists(index=index_name)

    def count_index(self, index_name: str, query: dict | None = None) -> int:
        """
        获取指定 index 的文档数量，可带查询条件。
        :param index_name: 索引名称
        :param query: 查询条件（可选）
        :return: 文档数量（int）
        """
        try:
            body = {"query": query or {"match_all": {}}}
            return self.es.count(index=index_name, body=body)["count"]
        except Exception as e:
            self.logger.error(f"Index does not exist: {e}")
            return 0

    def create_index(self, index_name: str, mapping: Dict) -> bool:
        """
        创建索引

        :param index_name: 索引名称
        :param mapping: 索引映射配置
        :return: 是否创建成功
        """
        if not self.index_exists(index_name):
            self.es.indices.create(index=index_name, body=mapping)
            return True
        return False

    def delete_index(self, index_name: str) -> bool:
        """删除索引"""
        if self.index_exists(index_name):
            self.es.indices.delete(index=index_name)
            return True
        return False

    def get_mapping(self, index_name: str) -> Dict:
        """获取索引的 mapping"""
        mapping_response = self.es.indices.get_mapping(index=index_name)
        mapping = mapping_response[index_name]["mappings"]
        return mapping

    def get_settings(self, index_name: str) -> Dict:
        """获取索引的index"""
        index_info = self.es.indices.get(index=index_name)[index_name]

        source_settings = index_info["settings"]["index"]
        # 清理不能直接用于创建 index 的字段
        # ------------------------------------------
        # settings.index 里某些字段必须删除，否则创建 index 会报错
        # 比如：uuid, creation_date, provided_name, version, routing 等
        blocked_keys = [
            "uuid", "creation_date", "provided_name", "version",
            "routing", "creation_date_string"
        ]
        settings = {
            k: v for k, v in source_settings.items()
            if k not in blocked_keys
        }
        return settings

    def copy_index(self, source_index_name: str, target_index_name: str) -> bool:
        """
        复制 Elasticsearch 索引（包括 mapping 和 settings）。

        步骤：
            1. 检查目标索引是否已存在，若存在则直接返回 True。
            2. 检查源索引是否存在，若不存在则返回 False。
            3. 获取源索引的 mapping 和 settings。
            4. 创建目标索引并应用 mapping 和 settings。

        :param source_index_name: 源索引名称
        :param target_index_name: 目标索引名称
        :return: 复制成功返回 True，失败返回 False
        """
        self.logger.info(f"Start copying index: '{source_index_name}' -> '{target_index_name}'")

        if self.index_exists(target_index_name):
            self.logger.info(f"Target index '{target_index_name}' already exists. Skipping creation.")
            return True

        if not self.index_exists(source_index_name):
            self.logger.info(f"Source index '{source_index_name}' does not exist. Copy aborted.")
            return False

        try:
            # Retrieve source index mappings
            mapping = self.get_mapping(source_index_name)
            self.logger.debug(f"Retrieved mapping for source index '{source_index_name}': {mapping}")

            # Retrieve source index settings
            settings = self.get_settings(source_index_name)
            self.logger.debug(f"Retrieved settings for source index '{source_index_name}': {settings}")

            # Create target index
            self.es.indices.create(
                index=target_index_name,
                mappings=mapping,
                settings=settings
            )
            self.logger.info(f"Index copy successful: '{source_index_name}' -> '{target_index_name}'")
            return True

        except Exception as e:
            self.logger.error(
                f"Error occurred while copying index '{source_index_name}' "
                f"to '{target_index_name}': {e}"
            )
            return False

    def search(self, index_name: str, body: Dict) -> Dict:
        """
        执行搜索查询
        :param index_name: 索引名称
        :param body: 查询DSL
        :return: 搜索结果字典，包含hits和total信息
        """
        try:
            response = self.es.search(index=index_name, body=body)
            hits = response.get("hits", {})
            return hits
        except NotFoundError:
            # 索引不存在
            self.logger.error(f"Index '{index_name}' does not exist")
            return {}

        except ConnectionError:
            # ES 链路问题
            self.logger.error(f"Error: Elasticsearch connection failed")
            return {}

        except Exception as e:
            # 其他未知错误
            self.logger.error(f"Error: {str(e)}")
            return {}

    def get_document_by_id(self, index_name: str, _id: str):
        """
        通过id 获取单个文档
        :param index_name: 索引名称
        :param _id: ID
        :return: 文档内容或None
        """
        try:
            return self.es.get(index=index_name, id=_id)
        except Exception as e:
            self.logger.info(f"Error getting document (_id: {_id}) from index {index_name}: {e}")
            return None

    def get_many_documents_by_ids(self, index_name: str, ids: List[str], request_timeout: int = 90,
                                  _source: bool | dict | None = True, realtime: bool = True, refresh: bool = False):
        """
        通过ids 获取多个文档, 支持 source filtering
        :param index_name: 索引名称
        :param ids: ID
        :param request_timeout: ID
        :param _source: True 返回 _source 字段， False 不返回可节省带宽
                source filtering时需传入 _source={'includes': [...], 'excludes': [...]}
        :param realtime: True 实时读取（默认），若可容忍近实时可设为 False 提升性能
        :param refresh: 不强制 refresh（避免性能损耗）
        :return: 文档内容或None
        """
        try:
            es_opt = self.es.options(request_timeout=request_timeout)
            # 如果 _source 是 dict，则拆成 includes/excludes
            if isinstance(_source, dict):
                includes = _source.get("includes")
                excludes = _source.get("excludes")
                response = es_opt.mget(index=index_name, ids=ids, _source_includes=includes,
                                       _source_excludes=excludes, realtime=realtime, refresh=refresh)
            else: # True / False 直接使用
                response = es_opt.mget(index=index_name, ids=ids, _source=_source, realtime=realtime, refresh=refresh)
            return response['docs']
        except Exception as e:
            self.logger.info(f"Error getting many documents (len: {len(ids)}) from index {index_name}: {e}")
            return None

    def create_or_update_document(self, index_name: str, document: dict, doc_id: str | None = None):
        """
        创建或更新文档。
        :param index_name: 索引名称
        :param document: 文档内容
        :param doc_id: 文档ID（可选）
        """
        try:
            resp = self.es.index(index=index_name,id=doc_id,document=document, refresh=True)
            self.logger.info(f"Document indexed. index={index_name}, id={resp.get('_id')}")
            return resp
        except Exception as e:
            self.logger.error(f"Error creating or updating document. index={index_name}, id={doc_id}, error={e}")
            return {}

    def delete_document(self, index_name: str, doc_id: str) -> bool:
        """
        删除文档
        :param index_name: 索引名称
        :param doc_id: 文档ID
        """
        try:
            self.es.delete(index=index_name, id=doc_id, refresh=True)
            self.logger.info(f"Document deleted. index={index_name}, id={doc_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete document. index={index_name}, id={doc_id}, error={e}")
            return False

    def bulk_update(self, index_name: str, documents: List[Dict], doc_as_upsert: bool=False):
        """
        批量索引文档
        :param index_name: 索引名称
        :param documents: 文档列表
        :param doc_as_upsert: 文档不存在是否插入
        :return: Elasticsearch批量响应
        """
        actions = []
        for doc in documents:
            actions.append({
                "_op_type": "update",
                "_index": index_name,
                "_id": doc['_id'],
                "doc": doc['_source'],
                "doc_as_upsert": doc_as_upsert,  # 若不存在则也不插入
            })
        self.logger.info(f"Starting bulk update, total {len(actions)} documents...")
        success, failed = helpers.bulk(self.es, actions, raise_on_error=False)
        self.logger.info(f"bulk_update: ✅ Success: {success}, ❌ Failed: {len(failed)}")
        if failed:
            self.logger.warning(f"Sample failed ({min(3, len(failed))}): {failed[:3]}")
        return success, failed

    def bulk_delete_by_ids(self, index_name: str, ids: list):
        """
        通过ids 批量删除数据
        :param index_name:
        :param ids:
        :return:
        """
        self.logger.info(f"Deleted {len(ids)} documents from index {index_name}")
        if not ids:
            return 0, []

        actions = [
            {
                "_op_type": "delete",
                "_index": index_name,
                "_id": _id
            }
            for _id in ids
        ]

        success, failed = helpers.bulk(self.es, actions)
        self.logger.info(f"bulk_delete_by_ids: ✅ Success: {success}, ❌ Failed: {len(failed)}")
        if failed:
            self.logger.warning(f"Sample failed ({min(3, len(failed))}): {failed[:3]}")
        return success, failed

    def close(self):
        """显式关闭连接（推荐在程序退出前调用）"""
        self.es.close()

    def __aenter__(self):
        return self

    def __aexit__(self, exc_type, exc_val, exc_tb):
        self.close()


class AsyncElasticsearchClient:
    def __init__(
        self,
        hosts: Union[str, List[str]],
        api_key: Optional[Union[str, Tuple[str, str]]] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        verify_certs: bool = False,
        request_timeout: Optional[float] = 90,
        max_retries: int = 3,
        retry_on_timeout: bool = True,
        es_client: Optional[AsyncElasticsearch] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        初始化 异步 Elasticsearch 客户端实例。

        参数优先级：
        - 若同时提供 api_key 和 (username, password)，以 api_key 为准。
        - 若未提供 api_key，则必须同时提供 username 和 password。

        :param hosts: Elasticsearch 服务的主机地址。可以是单个字符串（如 "http://localhost:9200"），
                      也可以是多个地址组成的列表（如 ["http://es1:9200", "http://es2:9200"]）。
        :param api_key: 可选，HTTP 基本身份验证的凭据。
        :param username: 可选，Elasticsearch 用户名。若未提供 api_key，则必须与 password 一起提供。
        :param password: 可选，Elasticsearch 密码。若未提供 api_key，则必须与 username 一起提供。
        :param verify_certs: 是否验证 SSL 证书，默认为 False（适用于自签名证书或测试环境）。
        :param request_timeout: 每个请求的超时时间（秒），默认为 90 秒。
        :param max_retries: 请求失败时的最大重试次数，默认为 3 次。
        :param retry_on_timeout: 是否在请求超时时进行重试，默认为 True。
        :param es_client: 可传入 es_client
        :param logger: 可传入 logger

        :raises ValueError: 凭据缺失时抛出。
        """
        basic_auth = None
        if api_key is not None:
            # api_key 优先；支持 str 或 (id, api_key) tuple
            pass
        elif username and password:
            basic_auth = (username, password)
            api_key = None
        else:
            raise ValueError("Either `api_key` or both `username` and `password` must be provided.")

        self.es: AsyncElasticsearch = (
            es_client
            or AsyncElasticsearch(
                hosts=hosts,
                api_key=api_key,
                basic_auth=basic_auth,
                verify_certs=verify_certs,
                request_timeout=request_timeout,
                max_retries=max_retries,
                retry_on_timeout=retry_on_timeout,
            )
        )
        self.logger = logger or logging.getLogger(__name__)

    async def ping(self) -> bool:
        """异步检查 Elasticsearch 集群是否可用"""
        try:
            return await self.es.ping()
        except Exception as e:
            self.logger.error(f"Ping failed: {e}")
            return False

    async def index_exists(self, index_name: str) -> bool:
        """异步检查索引是否存在"""
        try:
            return await self.es.indices.exists(index=index_name)
        except NotFoundError:
            return False
        except Exception as e:
            self.logger.error(f"Error checking index existence '{index_name}': {e}")
            return False

    async def count_index(self, index_name: str, query: Optional[Dict] = None) -> int:
        """异步获取指定索引的文档数量"""
        try:
            body = {"query": query or {"match_all": {}}}
            resp = await self.es.count(index=index_name, body=body)
            return resp["count"]
        except Exception as e:
            self.logger.error(f"Count failed for index '{index_name}': {e}")
            return 0

    async def create_index(self, index_name: str, mapping: Dict) -> bool:
        """异步创建索引"""
        if await self.index_exists(index_name):
            return False
        try:
            await self.es.indices.create(index=index_name, body=mapping)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create index '{index_name}': {e}")
            return False

    async def delete_index(self, index_name: str) -> bool:
        """异步删除索引"""
        if not await self.index_exists(index_name):
            return False
        try:
            await self.es.indices.delete(index=index_name)
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete index '{index_name}': {e}")
            return False

    async def get_mapping(self, index_name: str) -> Dict:
        """异步获取索引 mapping"""
        try:
            resp = await self.es.indices.get_mapping(index=index_name)
            return resp[index_name]["mappings"]
        except Exception as e:
            self.logger.error(f"Failed to get mapping for '{index_name}': {e}")
            raise

    async def get_settings(self, index_name: str) -> Dict:
        """异步获取清洗后的 settings（可复用）"""
        try:
            index_info = (await self.es.indices.get(index=index_name))[index_name]
            source_settings = index_info["settings"]["index"]

            blocked_keys = [
                "uuid", "creation_date", "provided_name", "version",
                "routing", "creation_date_string"
            ]
            return {
                k: v for k, v in source_settings.items()
                if k not in blocked_keys
            }
        except Exception as e:
            self.logger.error(f"Failed to get settings for '{index_name}': {e}")
            raise

    async def copy_index(self, source_index_name: str, target_index_name: str) -> bool:
        """异步复制索引（mapping + settings）"""
        self.logger.info(f"Start async copying index: '{source_index_name}' → '{target_index_name}'")

        if await self.index_exists(target_index_name):
            self.logger.info(f"Target index '{target_index_name}' already exists. Skipping.")
            return True

        if not await self.index_exists(source_index_name):
            self.logger.warning(f"Source index '{source_index_name}' does not exist.")
            return False

        try:
            mapping = await self.get_mapping(source_index_name)
            settings = await self.get_settings(source_index_name)

            await self.es.indices.create(
                index=target_index_name,
                mappings=mapping,
                settings=settings
            )
            self.logger.info(f"Index copy succeeded: '{source_index_name}' → '{target_index_name}'")
            return True
        except Exception as e:
            self.logger.error(f"Index copy failed: {e}")
            return False

    async def search(self, index_name: str, body: Dict) -> Dict[str, Any]:
        """异步搜索"""
        try:
            response = await self.es.search(index=index_name, body=body)
            return response.get("hits", {})
        except NotFoundError:
            self.logger.error(f"Index '{index_name}' not found.")
            return {}
        except ConnectionError:
            self.logger.error("Elasticsearch connection failed.")
            return {}
        except Exception as e:
            self.logger.error(f"Search error on '{index_name}': {e}")
            return {}

    async def get_document_by_id(self, index_name: str, _id: str) -> Optional[Dict]:
        """异步获取单文档"""
        try:
            return await self.es.get(index=index_name, id=_id)
        except NotFoundError:
            self.logger.info(f"Document not found: index={index_name}, id={_id}")
            return None
        except Exception as e:
            self.logger.error(f"Get doc error (id={_id}): {e}")
            return None

    async def get_many_documents_by_ids(
        self,
        index_name: str,
        ids: List[str],
        request_timeout: int = 90,
        _source: Union[bool, Dict] = True,
        realtime: bool = True,
        refresh: bool = False,
    ) -> Optional[List[Dict]]:
        """异步批量获取文档（支持 source filtering）"""
        try:
            es_opt = self.es.options(request_timeout=request_timeout)

            kwargs = {
                "index": index_name,
                "ids": ids,
                "realtime": realtime,
                "refresh": refresh,
            }

            if isinstance(_source, dict):
                includes = _source.get("includes")
                excludes = _source.get("excludes")
                kwargs["_source_includes"] = includes
                kwargs["_source_excludes"] = excludes
            else:
                kwargs["_source"] = _source

            response = await es_opt.mget(**kwargs)
            return response["docs"]
        except Exception as e:
            self.logger.error(f"mget failed (len={len(ids)}): {e}")
            return None

    async def create_or_update_document(
        self,
        index_name: str,
        document: Dict,
        doc_id: Optional[str] = None,
    ) -> Dict:
        """异步创建或更新单文档（带 refresh）"""
        try:
            resp = await self.es.index(
                index=index_name,
                id=doc_id,
                document=document,
                refresh=True
            )
            self.logger.info(f"Document indexed: index={index_name}, id={resp.get('_id')}")
            return resp
        except Exception as e:
            self.logger.error(f"Index doc failed: index={index_name}, id={doc_id}, error={e}")
            return {}

    async def delete_document(self, index_name: str, doc_id: str) -> bool:
        """异步删除文档"""
        try:
            await self.es.delete(index=index_name, id=doc_id, refresh=True)
            self.logger.info(f"Document deleted: index={index_name}, id={doc_id}")
            return True
        except Exception as e:
            self.logger.error(f"Delete doc failed: index={index_name}, id={doc_id}, error={e}")
            return False

    async def bulk_update(
        self,
        index_name: str,
        documents: List[Dict],
        doc_as_upsert: bool = False,
    ) -> Tuple[int, List[Dict]]:
        """
        异步批量 update 文档（支持 upsert）
        documents 格式示例：
          [{"_id": "1", "_source": {"title": "x"}}, ...]
        """
        actions = [
            {
                "_op_type": "update",
                "_index": index_name,
                "_id": doc["_id"],
                "doc": doc["_source"],
                "doc_as_upsert": doc_as_upsert,
            }
            for doc in documents
        ]

        self.logger.info(f"Starting async bulk update: {len(actions)} docs...")

        try:
            success, failed = await helpers.async_bulk(
                self.es,
                actions,
                raise_on_error=False,
                stats_only=False,
            )
            self.logger.info(f"bulk_update: ✅ Success: {success}, ❌ Failed: {len(failed)}")
            if failed:
                self.logger.warning(f"Sample failed ({min(3, len(failed))}): {failed[:3]}")
            return success, failed
        except Exception as e:
            self.logger.error(f"Bulk update failed: {e}")
            return 0, [{"error": str(e)}]

    async def bulk_delete_by_ids(self, index_name: str, ids: List[str]) -> Tuple[int, List]:
        """异步批量删除文档 by IDs"""
        self.logger.info(f"Deleted {len(ids)} documents from index {index_name}")
        if not ids:
            return 0, []

        actions = [
            {"_op_type": "delete", "_index": index_name, "_id": _id}
            for _id in ids
        ]

        try:
            success, failed = await helpers.async_bulk(
                self.es,
                actions,
                raise_on_error=False,
                stats_only=False,
            )
            self.logger.info(f"bulk_delete_by_ids: ✅ Success: {success}, ❌ Failed: {len(failed)}")
            if failed:
                self.logger.warning(f"Sample failed ({min(3, len(failed))}): {failed[:3]}")
            return success, failed
        except Exception as e:
            self.logger.error(f"Bulk delete failed: {e}")
            return 0, [{"error": str(e)}]

    async def close(self):
        """显式关闭连接（推荐在程序退出前调用）"""
        await self.es.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
