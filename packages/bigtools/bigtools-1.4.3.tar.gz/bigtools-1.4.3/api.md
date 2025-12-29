# bigtools API 文档

本文档详细介绍了 `bigtools` 库的所有公开 API。

## 目录

- [加密验证工具](#加密验证工具)
- [数据库工具](#数据库工具)
- [常用数据](#常用数据)
- [下载工具](#下载工具)
- [异常处理工具](#异常处理工具)
- [文件处理工具](#文件处理工具)
- [Hash 工具](#hash-工具)
- [Jieba 工具](#jieba-工具)
- [JSON 工具](#json-工具)
- [日志工具](#日志工具)
- [其他工具](#其他工具)
- [路径处理工具](#路径处理工具)
- [美化显示工具](#美化显示工具)
- [相似度计算工具](#相似度计算工具)
- [相似度计算工具（异步）](#相似度计算工具异步)
- [停用词](#停用词)
- [YAML 工具](#yaml-工具)

---

## 加密验证工具

### `generate_api_key`

生成 URL-safe 的 API Key。

```python
generate_api_key(n_bytes: int = 32) -> str
```

**参数：**
- `n_bytes` (int): 字节数，默认 32（生成 43 个字符）

**返回：**
- `str`: URL-safe 的 API Key

**示例：**
```python
from bigtools import generate_api_key
api_key = generate_api_key()
```

---

### `compute_key_hmac`

计算用于存储的 HMAC（hex），一般与 user_id、api、create_time、expire_time 一起存储。

```python
compute_key_hmac(api_key: str, secret_key: str) -> str
```

**参数：**
- `api_key` (str): 用户的 api_key
- `secret_key` (str): 用户私有密钥

**返回：**
- `str`: HMAC 十六进制字符串

---

### `generate_hmac_signature`

使用 HMAC-SHA256 算法生成签名，并进行 URL 安全的 Base64 编码。

```python
generate_hmac_signature(secret_key: str, message: str) -> str
```

**参数：**
- `secret_key` (str): 签名所用的密钥
- `message` (str): 需要签名的消息内容

**返回：**
- `str`: URL 安全的 Base64 编码后的签名字符串（去掉了尾部 '=' 填充）

---

### `verify_hmac_signature`

验证给定的签名是否正确。

```python
verify_hmac_signature(secret_key: str, message: str, signature: str) -> bool
```

**参数：**
- `secret_key` (str): 签名所用的密钥
- `message` (str): 需要签名的消息内容
- `signature` (str): 需要验证的签名（URL 安全的 Base64 编码字符串）

**返回：**
- `bool`: True 表示验证成功，False 表示验证失败

---

### `dict_to_urlsafe_b64`

将 Python 字典编码为 URL-safe Base64 字符串。

```python
dict_to_urlsafe_b64(data: dict) -> str
```

**参数：**
- `data` (dict): 需要编码的字典

**返回：**
- `str`: URL-safe Base64 编码后的字符串（无填充符号）

---

### `urlsafe_b64_to_dict`

将 URL-safe Base64 字符串解码为 Python 字典。

```python
urlsafe_b64_to_dict(us_str: str) -> dict
```

**参数：**
- `us_str` (str): URL-safe Base64 编码的字符串（无 '=' 填充符号）

**返回：**
- `dict`: 解码后的字典

---

### `merge_str`

根据指定算法合并两个字符串。

```python
merge_str(str1: str, str2: str, merge_method: str = 'hybrid') -> str
```

**参数：**
- `str1` (str): 第一个字符串
- `str2` (str): 第二个字符串
- `merge_method` (str): 合并方式，可选 'hybrid'（交叉合并）、'ahead'（str2 插在 str1 前面）、'after'（str2 插在 str1 后面）

**返回：**
- `str`: 合并后的字符串

---

### `merge_method_dict`

合并方法字典，包含 'hybrid'、'ahead'、'after' 三种合并方式。

---

### `SignatureGenerator`

签名生成器类，用于生成带过期时间的签名。

```python
SignatureGenerator(payload: dict, secret_key: str, expire_seconds: int = 3600)
```

**参数：**
- `payload` (dict): 负载信息
- `secret_key` (str): 密钥
- `expire_seconds` (int): 过期时间（秒），默认 3600

**方法：**

- `insert(merge_method: str) -> tuple`: 通过传入 merge_method 进行 insert
  - `merge_method`: 合并方式（'universal'、'hybrid'、'ahead'、'after'）
  - 返回: `(payload_b64, signature)` 元组

- `insert_random() -> tuple`: 随机选择一个方式

- `insert_universal() -> tuple`: 使用 universal 方式

- `insert_hybrid() -> tuple`: 使用 hybrid 方式

- `insert_ahead() -> tuple`: 使用 ahead 方式

- `insert_after() -> tuple`: 使用 after 方式

---

### `verify_signature`

验证 signature。

```python
verify_signature(signature: str, payload_b64: str, secret_key: str, logger: logging.Logger = None) -> dict
```

**参数：**
- `signature` (str): b64 编码的 signature
- `payload_b64` (str): 生成 signature 所依赖的信息，一般是用户的信息
- `secret_key` (str): 用户的私有密钥
- `logger` (logging.Logger, 可选): 日志收集器

**返回：**
- `dict`: 包含 'payload'、'status'、'msg' 的字典

---

### `refresh_signature`

刷新 signature。

```python
refresh_signature(signature: str, payload_b64: str, secret_key: str, expire_seconds: int = 3600, 
                 forced_refresh: bool = False, threshold: int = 300, logger: logging.Logger = None) -> dict
```

**参数：**
- `signature` (str): b64 编码的 signature
- `payload_b64` (str): 生成 signature 所依赖的信息
- `secret_key` (str): 用户的私有密钥
- `expire_seconds` (int): 过期时间，默认 3600
- `forced_refresh` (bool): 是否强制刷新 signature，默认 False
- `threshold` (int): 过期前多久进行刷新（秒），默认 300
- `logger` (logging.Logger, 可选): 日志收集器

**返回：**
- `dict`: 包含 'signature'、'payload'、'status'、'msg' 的字典

---

### `build_jwt_token`

构造 JWT 标准 Token。

```python
build_jwt_token(payload: str, signature: str, separator: str = '.') -> str
```

**参数：**
- `payload` (str): 负载信息
- `signature` (str): 签名
- `separator` (str): 分隔符，默认为 "."，也可以指定其他的，例如：`#`、`|`

**返回：**
- `str`: JWT Token

---

### `build_and_encode_jwt_token`

构造 JWT 标准 Token 并再次编码。

```python
build_and_encode_jwt_token(payload: str, signature: str, separator: str = '.') -> str
```

**参数：**
- `payload` (str): 负载信息
- `signature` (str): 签名
- `separator` (str): 分隔符，默认为 "."

**返回：**
- `str`: 再次 Base64 编码后的 JWT Token

---

## 数据库工具

### `mongo_client`

创建 MongoDB 客户端（同步）。

```python
mongo_client(host: str, port: int, user: str = None, password: str = None,
             tz_aware: bool = False, tzinfo: str = 'Asia/Shanghai') -> MongoClient
```

**参数：**
- `host` (str): MongoDB 主机地址
- `port` (int): MongoDB 端口
- `user` (str, 可选): 用户名
- `password` (str, 可选): 密码
- `tz_aware` (bool): 是否时区感知，默认 False
- `tzinfo` (str): 时区信息，默认 'Asia/Shanghai'

**返回：**
- `MongoClient`: MongoDB 客户端实例

---

### `async_mongo_client`

创建 MongoDB 客户端（异步）。

```python
async_mongo_client(host: str, port: int, user: str = None, password: str = None,
                   tz_aware: bool = False, tzinfo: str = 'Asia/Shanghai') -> AsyncIOMotorClient
```

**参数：**
- `host` (str): MongoDB 主机地址
- `port` (int): MongoDB 端口
- `user` (str, 可选): 用户名
- `password` (str, 可选): 密码
- `tz_aware` (bool): 是否时区感知，默认 False
- `tzinfo` (str): 时区信息，默认 'Asia/Shanghai'

**返回：**
- `AsyncIOMotorClient`: 异步 MongoDB 客户端实例

---

### `MinioClient`

MinIO 客户端类。

```python
MinioClient(minio_endpoint: str, access_key: str, secret_key: str, secure: bool = False,
            logger: logging.Logger = None)
```

**参数：**
- `minio_endpoint` (str): 服务器地址
- `access_key` (str): 访问密钥
- `secret_key` (str): 秘密密钥
- `secure` (bool): 是否使用 HTTPS，默认 False
- `logger` (logging.Logger, 可选): 日志收集器

**方法：**

- `check_bucket(bucket_name: str, create: bool = True) -> bool`: 检查桶状态，也可以用于创建桶
  - `bucket_name`: bucket 名字
  - `create`: 默认为 True 创建该 bucket
  - 返回: 操作是否成功

- `get_bucket_list() -> list`: 获取所有 bucket 列表

---

### `RedisClient`

Redis 客户端类（同步）。

```python
RedisClient(host: str, port: int, password: str = None, logger: logging.Logger = None, 
            max_connections: int = 10)
```

**参数：**
- `host` (str): Redis 服务器地址
- `port` (int): Redis 服务器端口
- `password` (str, 可选): Redis 服务器密码
- `logger` (logging.Logger, 可选): 日志收集器
- `max_connections` (int): 最大连接数量，默认为 10

**方法：**

- `save(key: str, value: Any, ex_time: int = None) -> bool`: 保存键值对到 Redis（带过期时间）
- `get(key: str) -> Optional[str]`: 从 Redis 获取值
- `push_list(list_name: str, *values: Any, right_side: bool = False, ex_time: int = None) -> int`: 向列表添加元素
- `get_list(list_name: str, start: int = 0, end: int = -1) -> List[str]`: 获取列表范围元素
- `get_list_item(list_name: str, index: int) -> Optional[str]`: 获取列表指定位置的元素
- `list_length(list_name: str) -> int`: 获取列表长度
- `delete_key(key: str) -> int`: 删除指定的键（包括列表）
- `pop_list(list_name: str, right_side: bool = False) -> Optional[str]`: 从列表中弹出元素（移除并返回）
- `remove_list_value(list_name: str, value: str, count: int = 0) -> int`: 从列表中移除指定值的元素
- `trim_list(list_name: str, start: int, end: int) -> bool`: 修剪列表，只保留指定范围内的元素
- `close() -> None`: 关闭连接池

**上下文管理器支持：**
```python
with RedisClient(host, port) as redis:
    redis.save('key', 'value')
```

---

### `ElasticsearchClient`

Elasticsearch 客户端类（同步）。

```python
ElasticsearchClient(hosts: Union[str, List[str]], api_key: Optional[Union[str, Tuple[str, str]]] = None,
                    username: str = None, password: str = None, verify_certs: bool = False,
                    request_timeout: Optional[float] = 90, max_retries: int = 3,
                    retry_on_timeout: bool = True, es_client: Elasticsearch = None,
                    logger: logging.Logger = None)
```

**参数：**
- `hosts` (Union[str, List[str]]): Elasticsearch 服务的主机地址
- `api_key` (Optional[Union[str, Tuple[str, str]]], 可选): HTTP 基本身份验证的凭据
- `username` (str, 可选): Elasticsearch 用户名
- `password` (str, 可选): Elasticsearch 密码
- `verify_certs` (bool): 是否验证 SSL 证书，默认为 False
- `request_timeout` (Optional[float]): 每个请求的超时时间（秒），默认为 90 秒
- `max_retries` (int): 请求失败时的最大重试次数，默认为 3 次
- `retry_on_timeout` (bool): 是否在请求超时时进行重试，默认为 True
- `es_client` (Elasticsearch, 可选): 可传入 es_client
- `logger` (logging.Logger, 可选): 可传入 logger

**方法：**

- `ping() -> bool`: 检查 Elasticsearch 集群是否可用
- `index_exists(index_name: str) -> bool`: 检查索引是否存在
- `count_index(index_name: str, query: dict | None = None) -> int`: 获取指定 index 的文档数量，可带查询条件
- `create_index(index_name: str, mapping: Dict) -> bool`: 创建索引
- `delete_index(index_name: str) -> bool`: 删除索引
- `get_mapping(index_name: str) -> Dict`: 获取索引的 mapping
- `get_settings(index_name: str) -> Dict`: 获取索引的 settings
- `copy_index(source_index_name: str, target_index_name: str) -> bool`: 复制 Elasticsearch 索引（包括 mapping 和 settings）
- `search(index_name: str, body: Dict) -> Dict`: 执行搜索查询
- `get_document_by_id(index_name: str, _id: str) -> Optional[Dict]`: 通过 id 获取单个文档
- `get_many_documents_by_ids(index_name: str, ids: List[str], request_timeout: int = 90, _source: bool | dict | None = True, realtime: bool = True, refresh: bool = False) -> Optional[List[Dict]]`: 通过 ids 获取多个文档，支持 source filtering
- `create_or_update_document(index_name: str, document: dict, doc_id: str | None = None) -> Dict`: 创建或更新文档
- `delete_document(index_name: str, doc_id: str) -> bool`: 删除文档
- `bulk_update(index_name: str, documents: List[Dict], doc_as_upsert: bool = False) -> Tuple[int, List]`: 批量索引文档
- `bulk_delete_by_ids(index_name: str, ids: list) -> Tuple[int, List]`: 通过 ids 批量删除数据
- `close()`: 显式关闭连接

---

### `AsyncElasticsearchClient`

Elasticsearch 客户端类（异步）。

```python
AsyncElasticsearchClient(hosts: Union[str, List[str]], api_key: Optional[Union[str, Tuple[str, str]]] = None,
                         username: Optional[str] = None, password: Optional[str] = None,
                         verify_certs: bool = False, request_timeout: Optional[float] = 90,
                         max_retries: int = 3, retry_on_timeout: bool = True,
                         es_client: Optional[AsyncElasticsearch] = None,
                         logger: Optional[logging.Logger] = None)
```

**参数：** 与 `ElasticsearchClient` 相同

**方法：** 所有方法都是异步的，使用 `await` 调用

---

## 常用数据

### `headers`

默认 HTTP 请求头字典。

```python
headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}
```

---

### `random_headers`

随机 User-Agent 的请求头字典。

---

### `user_agents`

User-Agent 列表，包含多个常见的浏览器 User-Agent。

---

### `ContentType`

Content-Type 类，包含常用的 Content-Type 字符串和请求头。

**属性：**
- `app_json`: 'application/json'
- `app_xwfu`: 'application/x-www-form-urlencoded'
- `app_xml`: 'application/xml'
- `mul_fd`: 'multipart/form-data'
- `text_xml`: 'text/xml'
- `app_json_headers`: `{"Content-Type": "application/json;charset=utf-8"}`
- `app_xwfu_headers`: `{"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}`
- `app_xml_headers`: `{"Content-Type": "application/xml;charset=utf-8"}`
- `mul_fd_headers`: `{"Content-Type": "multipart/form-data;charset=utf-8"}`
- `text_xml_headers`: `{"Content-Type": "text/xml;charset=utf-8"}`

---

### `en_letter`

英文字母列表：['A', 'B', 'C', ..., 'Z']

---

### `numbers`

数字列表：['0', '1', '2', ..., '9']

---

### `DateType`

日期格式类型类，用于编写代码时提示。

**属性：**
- `type_1`: '%Y-%m-%d %H:%M:%S'        # YYYY-MM-DD HH:MM:SS
- `type_2`: '%Y年%m月%d日 %H时%M分%S秒'  # YYYY年MM月DD日 HH时MM分SS秒
- `type_3`: '%Y.%m.%d'                 # YYYY.MM.DD
- `type_4`: '%Y%m%d'                   # YYYYMMDD
- `type_5`: '%Y/%m/%d'                  # YYYY/MM/DD

---

### `RePattern`

正则表达式模式类。

**属性：**
- `window_INITIAL_STATE`: `r"window.__INITIAL_STATE__=(.*?}});"`

---

## 下载工具

### `get_requests_session`

使用 requests Session，使抓取数据的时候可以重试。

```python
get_requests_session(max_retries: int = 3) -> requests.Session
```

**参数：**
- `max_retries` (int): 默认设置重试次数为 3 次

**返回：**
- `requests.Session`: 配置了重试的 Session 对象

---

### `download_stream_data`

下载流式传输的文件，比如：压缩包、音频、视频等等。

```python
download_stream_data(url: str, file_path: str, headers: dict = df_headers, read_timeout: int = 15,
                    resume: bool = True, max_retries: int = 3, logger: logging.Logger = None)
```

**参数：**
- `url` (str): 文件下载链接
- `file_path` (str): 文件保存路径
- `headers` (dict): 请求头，默认使用 `df_headers`
- `read_timeout` (int): 读取超时时间，默认 15
- `resume` (bool): 是否断点续传，默认进行断点续传。值为 True 进行断点续传；值为 False 从头开始下载
- `max_retries` (int): 最大重试次数，网络不好时增大 max_retries
- `logger` (logging.Logger, 可选): 日志收集器

---

### `save_stream_data`

保存响应数据。

```python
save_stream_data(response, total: int, file_path: str, initial: int = 0)
```

**参数：**
- `response`: 请求响应
- `total` (int): 数据大小
- `file_path` (str): 保存的数据路径
- `initial` (int): 进度条初始化大小

---

### `download_stream_data_async`

异步下载流式传输的文件。

```python
async download_stream_data_async(url: str, file_path: str, headers: dict = df_headers,
                                  read_timeout: int = 15, resume: bool = True,
                                  max_retries: int = 3, logger: logging.Logger = None)
```

**参数：** 与 `download_stream_data` 相同

---

### `save_stream_data_async`

异步保存响应数据。

```python
async save_stream_data_async(response: aiohttp.ClientResponse, total: int, file_path: str, initial: int = 0)
```

**参数：**
- `response`: aiohttp ClientResponse
- `total` (int): 数据大小
- `file_path` (str): 保存路径
- `initial` (int): 初始进度

---

## 异常处理工具

### `RequestExceptionHandler`

处理 requests 请求异常并写日志，支持同步和异步函数。

```python
RequestExceptionHandler(logger: logging.Logger = None, level: int = logging.ERROR, 
                        with_traceback: bool = True)
```

**参数：**
- `logger` (logging.Logger, 可选): 日志对象，默认使用 `logging.getLogger(__name__)`
- `level` (int): 日志级别，默认 ERROR
- `with_traceback` (bool): 是否输出完整 traceback，默认 True

**使用示例：**
```python
@RequestExceptionHandler(logger=logger)
def get_data():
    return requests.get(url)
```

---

### `UniversalExceptionHandler`

通用异常处理装饰器，支持同步/异步函数及类方法。

```python
UniversalExceptionHandler(logger: Optional[logging.Logger] = None, level: int = logging.ERROR,
                          with_traceback: bool = True, default: Any = None)
```

**参数：**
- `logger` (logging.Logger, 可选): 日志对象，默认使用 `logging.getLogger(__name__)`
- `level` (int): 日志级别，默认 ERROR
- `with_traceback` (bool): 是否输出完整 traceback，默认 True
- `default` (Any): 出现异常时的默认返回值

**使用示例：**
```python
@UniversalExceptionHandler(logger=logger, default=None)
def risky_function():
    # ...
    pass
```

---

## 文件处理工具

### `save_file`

通用文件保存函数，支持 .txt, .md, .html 等。

```python
save_file(file_path: str, content: str, mode: str = 'w', encoding: str = 'utf-8',
          logger: logging.Logger = None, raise_on_error: bool = False) -> bool
```

**参数：**
- `file_path` (str): 文件路径，例如 'example.md'
- `content` (str): 文件内容
- `mode` (str): 写入模式，'w' 覆盖，'a' 追加
- `encoding` (str): 文件编码，默认 'utf-8'
- `logger` (logging.Logger, 可选): 日志收集器
- `raise_on_error` (bool): 是否在出错时抛出异常

**返回：**
- `bool`: 保存成功返回 True，否则 False

---

### `save_file_async`

异步通用文件保存函数。

```python
async save_file_async(file_path: str, content: str, mode: str = 'w', encoding: str = 'utf-8',
                       logger: logging.Logger = None, raise_on_error: bool = False) -> bool
```

**参数：** 与 `save_file` 相同

---

### `save_files_batch`

批量异步保存文件。

```python
async save_files_batch(file_data: List[Tuple[str, str]], max_concurrency: int = 10,
                       logger: logging.Logger = None)
```

**参数：**
- `file_data` (List[Tuple[str, str]]): List[(file_path, content)]
- `max_concurrency` (int): 最大并发数，默认 10
- `logger` (logging.Logger, 可选): 日志收集器

---

### `load_file`

通用文件读取函数，支持 .txt, .md, .html 等。

```python
load_file(file_path: str, mode: str = 'r', encoding: str = 'utf-8',
          logger: logging.Logger = None, raise_on_error: bool = False) -> str | None
```

**参数：**
- `file_path` (str): 文件路径，例如 'example.md'
- `mode` (str): 读取模式，'r'、'rb'
- `encoding` (str): 文件编码，默认 'utf-8'
- `logger` (logging.Logger, 可选): 日志收集器
- `raise_on_error` (bool): 是否在出错时抛出异常

**返回：**
- `str | None`: 文件内容字符串，失败时返回 None

---

### `load_file_async`

异步文件读取函数。

```python
async load_file_async(file_path: str, mode: str = 'r', encoding: str = 'utf-8',
                      logger: logging.Logger = None, raise_on_error: bool = False) -> str | None
```

**参数：** 与 `load_file` 相同

---

### `get_file_size`

获取文件大小。

```python
get_file_size(file_path: str) -> int
```

**参数：**
- `file_path` (str): 文件路径（带文件名）

**返回：**
- `int`: 文件大小（字节），文件不存在返回 0

---

## Hash 工具

### `generate_hash_value`

生成 hash 值。

```python
generate_hash_value(input_str: str, hash_function: str = 'md5', length: int = None) -> str
```

**参数：**
- `input_str` (str): 输入字符串
- `hash_function` (str): hash 方法，可选值：
  - 'md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512'
  - 'sha3_224', 'sha3_256', 'sha3_384', 'sha3_512'
  - 'shake_128', 'shake_256'（需要指定 length）
  - 'blake2b', 'blake2s'
- `length` (int, 可选): 生成的 hash 长度，仅对 shake_128 和 shake_256 有效

**返回：**
- `str`: 十六进制 hash 值

**示例：**
```python
from bigtools import generate_hash_value
hash_value = generate_hash_value('python工具箱')  # 默认使用 md5
sha256_value = generate_hash_value('python工具箱', 'sha256')
```

---

### `HASH_FUNCTIONS`

支持的哈希函数字典。

---

### `HashGenerator`

哈希生成器类。

```python
HashGenerator(input_str: str)
```

**参数：**
- `input_str` (str): 待哈希的字符串

**方法：**

- `md5() -> str`: 返回 md5 哈希值
- `sha1() -> str`: 返回 sha1 哈希值
- `sha224() -> str`: 返回 sha224 哈希值
- `sha256() -> str`: 返回 sha256 哈希值
- `sha384() -> str`: 返回 sha384 哈希值
- `sha512() -> str`: 返回 sha512 哈希值
- `sha3_224() -> str`: 返回 sha3_224 哈希值
- `sha3_256() -> str`: 返回 sha3_256 哈希值
- `sha3_384() -> str`: 返回 sha3_384 哈希值
- `sha3_512() -> str`: 返回 sha3_512 哈希值
- `shake_128(length: int) -> str`: 返回 shake_128 哈希值
- `shake_256(length: int) -> str`: 返回 shake_256 哈希值
- `blake2b() -> str`: 返回 blake2b 哈希值
- `blake2s() -> str`: 返回 blake2s 哈希值

**示例：**
```python
from bigtools import HashGenerator
gen = HashGenerator('python工具箱')
md5_hash = gen.md5()
sha256_hash = gen.sha256()
```

---

## Jieba 工具

### `get_keywords_from_text`

从文本中获取关键词。

```python
get_keywords_from_text(text: str, stop_words: Set[str] = stopwords) -> List[str]
```

**参数：**
- `text` (str): 待提取的文本
- `stop_words` (Set[str]): 停用词，默认使用内置 `stopwords`

**返回：**
- `List[str]`: 关键词列表

---

### `get_keywords_from_text_async`

异步从文本中获取关键词。

```python
async get_keywords_from_text_async(text: str, stop_words: Set[str] = stopwords) -> List[str]
```

**参数：** 与 `get_keywords_from_text` 相同

---

### `jieba_tokenizer`

中文分词并过滤停用词和空白词。

```python
jieba_tokenizer(text: str, stop_words: Set[str] = stopwords) -> List[str]
```

**参数：**
- `text` (str): 待分词的文本
- `stop_words` (Set[str]): 停用词，默认使用内置 `stopwords`

**返回：**
- `List[str]`: 分词结果列表

---

## JSON 工具

### `save_json_data`

保存 JSON 数据至文件（同步/异步通用）。

```python
save_json_data(json_data: Any, json_file_path: Union[str, Path], indent: int = 4,
               logger: logging.Logger = None)
```

**参数：**
- `json_data` (Any): 要保存的数据
- `json_file_path` (Union[str, Path]): 文件路径（str 或 Path）
- `indent` (int): JSON 缩进，默认 4
- `logger` (logging.Logger, 可选): 日志对象，若为空则使用 print

**返回：**
- `bool`: 是否保存成功（同步环境）或 coroutine（异步环境）

---

### `save_json_data_sync`

同步保存 JSON 数据至文件。

```python
save_json_data_sync(json_data: Any, json_file_path: Union[str, Path], indent: int = 4,
                    logger: logging.Logger = None) -> bool
```

---

### `save_json_data_async`

异步保存 JSON 数据至文件。

```python
async save_json_data_async(json_data: Any, json_file_path: Union[str, Path], indent: int = 4,
                            logger: logging.Logger = None) -> bool
```

---

### `load_json_data`

读取 JSON 数据（同步/异步通用）。

```python
load_json_data(json_file_path: Union[str, Path], logger: Optional[logging.Logger] = None)
```

**参数：**
- `json_file_path` (Union[str, Path]): 文件路径（str 或 Path）
- `logger` (Optional[logging.Logger]): 日志对象，若为空则使用 print

**返回：**
- 读取到的数据，失败时返回 None（同步环境）或 coroutine（异步环境）

---

### `load_json_data_sync`

同步读取 JSON 数据。

```python
load_json_data_sync(json_file_path: Union[str, Path], logger: Optional[logging.Logger] = None)
```

---

### `load_json_data_async`

异步读取 JSON 数据。

```python
async load_json_data_async(json_file_path: Union[str, Path], logger: Optional[logging.Logger] = None)
```

---

### `pretty_print_json`

返回格式化的 JSON 字符串（美化输出）。

```python
pretty_print_json(json_data: Any, indent: int = 4) -> str
```

**参数：**
- `json_data` (Any): JSON 数据
- `indent` (int): 缩进，默认 4

**返回：**
- `str`: 格式化的 JSON 字符串

---

### `validate_json_schema`

验证 json 是否符合模板规定的格式。

```python
validate_json_schema(schema: dict, json_data: dict) -> Tuple[bool, ValidationError | None]
```

**参数：**
- `schema` (dict): JSON Schema 模板
- `json_data` (dict): 待验证的 JSON 数据

**返回：**
- `Tuple[bool, ValidationError | None]`: (是否符合, 错误对象或 None)

---

### `validate_json_string`

验证字符串是否是合法 JSON。

```python
validate_json_string(json_string: str) -> bool
```

**参数：**
- `json_string` (str): 待验证的 JSON 字符串

**返回：**
- `bool`: 是否为合法 JSON

---

### `save_json_data_by_orjson`

使用 orjson 保存 JSON 数据（同步/异步通用）。

```python
save_json_data_by_orjson(json_data: Any, json_file_path: Union[str, Path],
                         options: int = DEFAULT_OPTIONS, logger: logging.Logger = None)
```

**参数：**
- `json_data` (Any): 要保存的数据
- `json_file_path` (Union[str, Path]): 文件路径
- `options` (int): orjson 配置参数，默认 `DEFAULT_OPTIONS`
- `logger` (logging.Logger, 可选): 日志对象

---

### `save_json_data_sync_by_orjson`

使用 orjson 同步保存 JSON 数据。

```python
save_json_data_sync_by_orjson(json_data: Any, json_file_path: Union[str, Path],
                               options: int = DEFAULT_OPTIONS, logger: logging.Logger = None) -> bool
```

---

### `save_json_data_async_by_orjson`

使用 orjson 异步保存 JSON 数据。

```python
async save_json_data_async_by_orjson(json_data: Any, json_file_path: Union[str, Path],
                                      options: int = DEFAULT_OPTIONS, logger: logging.Logger = None) -> bool
```

---

### `load_json_data_by_orjson`

使用 orjson 读取 JSON 数据（同步/异步通用）。

```python
load_json_data_by_orjson(json_file_path: Union[str, Path], logger: Optional[logging.Logger] = None)
```

---

### `load_json_data_sync_by_orjson`

使用 orjson 同步读取 JSON 数据。

```python
load_json_data_sync_by_orjson(json_file_path: Union[str, Path],
                               logger: Optional[logging.Logger] = None) -> Optional[Any]
```

---

### `load_json_data_async_by_orjson`

使用 orjson 异步读取 JSON 数据。

```python
async load_json_data_async_by_orjson(json_file_path: Union[str, Path],
                                      logger: Optional[logging.Logger] = None) -> Optional[Any]
```

---

### `pretty_print_orjson`

返回格式化的 JSON（美化输出），bytes 数据。

```python
pretty_print_orjson(json_data: Any) -> bytes
```

**参数：**
- `json_data` (Any): JSON 数据

**返回：**
- `bytes`: 格式化的 JSON bytes

---

### `validate_orjson_string`

验证 orjson 字符串是否是合法 JSON。

```python
validate_orjson_string(json_string: str) -> bool
```

---

## 日志工具

### `set_log`

配置日志（简单，适合轻量级项目）。

```python
set_log(log_path: str) -> logging.Logger
```

**参数：**
- `log_path` (str): 日志文件路径

**返回：**
- `logging.Logger`: 配置好的 logger

**功能：**
- 配置文件日志处理器（按天轮转，保留 180 天）
- 配置控制台日志处理器
- 日志级别设置为 INFO

---

### `SetLog`

配置日志（复杂，适合大型项目）。

```python
SetLog(log_config: str, log_path: str)
```

**参数：**
- `log_config` (str): 日志配置文件路径（YAML 格式）
- `log_path` (str): 日志文件存储路径

**静态方法：**

- `debug(msg)`: 记录 debug 级别日志
- `info(msg)`: 记录 info 级别日志
- `error(msg)`: 记录 error 级别日志（包含异常信息）

---

## 其他工具

### `extract_ip`

获取本机局域网 IP 地址（非 127.0.0.1）。

```python
extract_ip() -> str
```

**返回：**
- `str`: 本机 IP 地址，如果无法获取，返回空字符串

---

### `equally_split_list_or_str`

将一个 list 或 str 按长度 num 均分。

```python
equally_split_list_or_str(data: Union[list, str], num: int) -> List[Union[list, str]]
```

**参数：**
- `data` (Union[list, str]): 输入的 list 或 str
- `num` (int): 每段的长度

**返回：**
- `List[Union[list, str]]`: 分割后的 list

---

### `load_config`

获取配置。

```python
load_config(config_dir: str) -> dict
```

**参数：**
- `config_dir` (str): 配置文件存储的文件夹

**返回：**
- `dict`: 配置字典

**说明：**
- `PYTHON_CONFIG` 环境变量默认值是 `dev`，其他值有 `prod`、`test`
- 配置文件格式为 YAML

---

### `set_env`

设置环境变量。

```python
set_env(env_dict: dict)
```

**参数：**
- `env_dict` (dict): 环境变量字典

---

### `load_env`

获取环境变量。

```python
load_env(envs: Union[list, dict]) -> dict
```

**参数：**
- `envs` (Union[list, dict]): 
  - 可以是 list，例如：`['KEY1', 'KEY2', {'KEY3': 'default_value'}]`
  - 也可以是 dict，例如：`{'KEY1': 'default1', 'KEY2': 'default2'}`

**返回：**
- `dict`: 环境变量字典

---

### `FuncTimer`

装饰器类：统计函数运行时间，支持同步/异步。

```python
FuncTimer(logger=None, threshold: float = 0.0)
```

**参数：**
- `logger`: 日志对象，可选
- `threshold` (float): 运行时间超过阈值才输出日志（秒），默认 0 表示始终输出

**使用示例：**
```python
@FuncTimer(logger=logger, threshold=1.0)
def my_function():
    # ...
    pass
```

---

### `time_sleep`

程序睡眠，有进度条显示。

```python
time_sleep(seconds: int, step: float = 1.0)
```

**参数：**
- `seconds` (int): 总睡眠时间（秒）
- `step` (float): 每步睡眠时间（秒），默认 1 秒

---

### `count_str_start_or_end_word_num`

高性能统计字符串首尾连续出现某个子串的次数。

```python
count_str_start_or_end_word_num(strings: str, matched_str: str, beginning: bool = True) -> int
```

**参数：**
- `strings` (str): 字符串
- `matched_str` (str): 待匹配子串
- `beginning` (bool): True 从开头统计，False 从结尾统计

**返回：**
- `int`: 连续出现次数

---

### `is_chinese`

检测字符串是否只由中文组成，不含标点。

```python
is_chinese(input_data: str) -> bool
```

**参数：**
- `input_data` (str): 输入字符串

**返回：**
- `bool`: 是否只包含中文

---

### `is_english`

检测字符串是否只由英文组成，不含标点。

```python
is_english(input_data: str) -> bool
```

**参数：**
- `input_data` (str): 输入字符串

**返回：**
- `bool`: 是否只包含英文

---

### `is_number`

检测输入数据是否为数字（整数或浮点数），支持普通数字和 Unicode 数字。

```python
is_number(input_data: Union[str, int, float]) -> bool
```

**参数：**
- `input_data` (Union[str, int, float]): 输入数据

**返回：**
- `bool`: 是否为数字

---

### `generate_random_string`

生成随机长度的字符串。

```python
generate_random_string(length: int = 12) -> str
```

**参数：**
- `length` (int): 字符串长度，默认 12

**返回：**
- `str`: 随机字符串（包含字母和数字）

---

### `sort_with_index`

按数值降序排序，并保留原索引位置。

```python
sort_with_index(values: list, reverse: bool = True) -> Tuple[List[Tuple[int, float]], List[dict]]
```

**参数：**
- `values` (list): 待排序的数值列表（list[float | int]）
- `reverse` (bool): 是否降序（默认 True）

**返回：**
- `Tuple[List[Tuple[int, float]], List[dict]]`: 
  - `sorted_pairs`: 排序后的 (index, value) 元组列表
  - `result`: 结构化输出 `[{"id": 原索引, "value": 值}, ...]`

---

### `sort_dict_by_value`

按值对字典排序。

```python
sort_dict_by_value(d: dict, reverse: bool = True) -> dict
```

**参数：**
- `d` (dict): 待排序的字典
- `reverse` (bool): 是否降序（默认 True）

**返回：**
- `dict`: 排序后的字典

---

## 路径处理工具

### `check_make_dir`

检查路径是否存在，不存在就创建。

```python
check_make_dir(dir_str: str)
```

**参数：**
- `dir_str` (str): 目录路径

---

### `get_execution_dir`

获取执行代码的目录。

```python
get_execution_dir() -> str
```

**返回：**
- `str`: 执行代码的目录路径

---

### `get_file_type`

获取文件类型。

```python
get_file_type(file_path: str, is_upper: bool = False) -> str
```

**参数：**
- `file_path` (str): 文件路径
- `is_upper` (bool): 是否返回大写，默认 False

**返回：**
- `str`: 文件扩展名（不含点号）

---

### `get_execution_file_name`

获取执行代码的文件名。

```python
get_execution_file_name() -> str
```

**返回：**
- `str`: 执行代码的文件名

---

## 美化显示工具

### `pretty_print`

打印变量名或表达式及其值，彩色区分变量名和值。

```python
pretty_print(*args, color: bool = True, max_lines: int | None = None, max_str_len: int | None = None)
```

**参数：**
- `*args`: 要打印的变量或表达式
- `color` (bool): 是否启用彩色输出，默认 True
- `max_lines` (int | None): 当列表/字典行数超过此值时折叠显示，None 表示不折叠
- `max_str_len` (int | None): 当字符串长度超过此值时截断显示，None 表示不截断

**示例：**
```python
from bigtools import pretty_print
x = [1, 2, 3]
pretty_print(x)  # 会打印变量名 x 和它的值
```

---

## 相似度计算工具

### `cosine_similarity`

计算两个向量的余弦相似度（使用 sklearn 实现）。

```python
cosine_similarity(vector1: np.ndarray, vector2: np.ndarray) -> float
```

---

### `TfidfChineseRetriever`

中文 TF-IDF 检索器类。

```python
TfidfChineseRetriever(documents: List[str], stop_words: Set[str] = stopwords,
                      ngram_range: Tuple[int, int] = (1, 1), max_features: int = None)
```

**参数：**
- `documents` (List[str]): 文档列表
- `stop_words` (Set[str]): 停用词集合，默认使用内置 `stopwords`
- `ngram_range` (Tuple[int, int]): ngram 范围，默认 (1, 1)
- `max_features` (int, 可选): 最大特征数

**方法：**

- `query(query: List[str]) -> ReturnedTFIDFSimilarities`: 查询文档相似度
- `query_similarity(query: List[str]) -> np.ndarray`: 查询文档相似度，返回相似度数组
- `query_topk(query: List[str], top_k: int = 10) -> List[Tuple[int, float]]`: 查询文档相似度，返回前 top_k 个结果

---

### `calculate_chinese_tfidf_similarity`

中文 TF-IDF 文档检索器，计算 TF-IDF 相似度。

```python
calculate_chinese_tfidf_similarity(query: list, documents: list, top_k: int = None,
                                   stop_words: Set[str] = stopwords, ngram_range: Tuple[int, int] = (1, 1),
                                   max_features: int = None)
```

**参数：**
- `query` (list): 查询语句
- `documents` (list): 待查询的文本
- `top_k` (int, 可选): 返回前 k 个结果
- `stop_words` (Set[str]): 停用词
- `ngram_range` (Tuple[int, int]): ngram 范围
- `max_features` (int, 可选): 最大特征数

**返回：**
- `ReturnedTFIDFSimilarities` 对象（如果 top_k 为 None）或前 k 个结果列表

---

### `BM25ChineseRetriever`

中文 BM25 检索器类。

```python
BM25ChineseRetriever(documents: List[str], method: str = "lucene", stop_words: Optional[set] = stopwords)
```

**参数：**
- `documents` (List[str]): 文档
- `method` (str): BM25 变体，可选：
  - "robertson"（Original）
  - "atire"（ATIRE）
  - "bm25l"（BM25L）
  - "bm25+"（BM25+）
  - "lucene"（Lucene，默认）
- `stop_words` (Optional[set]): 自定义停用词集合，默认使用内置 `stopwords`

**方法：**

- `retrieve(queries: Union[str, List[str]], top_k: int = None) -> List[dict]`: 检索最相关的文档
  - 返回: List of dicts，每个包含 'query'、'scores'、'documents' 键

---

### `calculate_chinese_bm25_similarity`

计算中文 BM25 相似度。

```python
calculate_chinese_bm25_similarity(query: list, documents: list, method: str = "lucene",
                                  stop_words: Set[str] = stopwords, top_k: int = None)
```

**参数：**
- `query` (list): 查询语句
- `documents` (list): 待查询的文本
- `method` (str): BM25 变体，默认 "lucene"
- `stop_words` (Set[str]): 停用词
- `top_k` (int, 可选): 返回前 k 个结果

**返回：**
- `List[dict]`: 检索结果列表

---

### `calculate_chinese_keyword_similarity_simple`

计算文档与关键词列表的匹配相似度（布尔匹配）。

```python
calculate_chinese_keyword_similarity_simple(query_keywords: List[str], document: str,
                                           lowercase: bool = True, enable_tokenization: bool = False,
                                           stop_words: Optional[Set[str]] = stopwords) -> float
```

**参数：**
- `query_keywords` (List[str]): 查询关键词列表
- `document` (str): 文本内容
- `lowercase` (bool): 是否自动转小写（对英文友好），默认 True
- `enable_tokenization` (bool): 是否进行分词，句子过长建议进行，默认 False
- `stop_words` (Optional[Set[str]]): 停用词集合，仅 enable_tokenization 为 True 时有用

**返回：**
- `float`: 匹配比例（0~1）

---

### `find_dense_keyword_groups`

找出文本中关键词密集出现的区域，并返回关键词组及对应文本片段。

```python
find_dense_keyword_groups(query_keywords: List[str], text: str, split_size: int = 50,
                         min_keywords_per_group: int = 2, lowercase: bool = True) -> List[Dict[str, object]]
```

**参数：**
- `query_keywords` (List[str]): 关键词
- `text` (str): 文本
- `split_size` (int): 分割 text 的窗口大小，默认 50
- `min_keywords_per_group` (int): 最小密集组，默认 2
- `lowercase` (bool): 是否自动转小写（对英文友好），默认 True

**返回：**
- `List[Dict[str, object]]`: 每个密集区域包含：
  - `keywords`: 关键词集合
  - `text_snippet`: 对应的文本片段
  - `start`: 起始索引
  - `end`: 结束索引

---

### `EmbeddingSimilarity`

使用 Embedding 进行相似度计算的类。

```python
EmbeddingSimilarity(embedding_function: Callable[[Union[str, list[str]]], np.ndarray])
```

**参数：**
- `embedding_function`: 用于将文本转为向量的函数，可以是异步或同步的

**方法：**

- `calculate_similarity(query: str, documents: list[str]) -> list`: 计算相似度（同步）
- `calculate_similarity_async(query: str, documents: list[str]) -> list`: 计算相似度（异步）
- `calculate_similarity_by_dense_keyword_groups(query: str, query_keywords: list[str], documents: list[str], split_size: int = 50, min_keywords_per_group: int = 2, lowercase: bool = True) -> list`: 先找到关键词密集的文本，再进行 Embedding 与计算 Similarity（同步）
- `calculate_similarity_by_dense_keyword_groups_async(query: str, query_keywords: list[str], documents: list[str], split_size: int = 50, min_keywords_per_group: int = 2, lowercase: bool = True) -> list`: 先找到关键词密集的文本，再进行 Embedding 与计算 Similarity（异步）

---

## 相似度计算工具（异步）

### `TfidfChineseRetrieverAsync`

异步中文 TF-IDF 检索器类。

```python
TfidfChineseRetrieverAsync(stop_words: Set[str] = stopwords,
                           ngram_range: Tuple[int, int] = (1, 1), max_features: int = None)
```

**类方法：**

- `create(documents: List[str], stop_words: Set[str] = None, ngram_range: Tuple[int, int] = (1, 1), max_features: int = None) -> TfidfChineseRetrieverAsync`: 异步构造器

**方法：**

- `query(query: Union[str, List[str]]) -> ReturnedTFIDFSimilarities`: 查询文档相似度（异步）
- `query_similarity(query: Union[str, List[str]]) -> np.ndarray`: 查询文档相似度，返回相似度数组（异步）
- `query_topk(query: Union[str, List[str]], top_k: int = 10) -> List[Tuple[int, float]]`: 查询文档相似度，返回前 top_k 个结果（异步）

---

### `calculate_chinese_tfidf_similarity_async`

异步中文 TF-IDF 文档检索器，计算 TF-IDF 相似度。

```python
async calculate_chinese_tfidf_similarity_async(query: list, documents: list, top_k: int = None,
                                               stop_words: Set[str] = stopwords,
                                               ngram_range: Tuple[int, int] = (1, 1),
                                               max_features: int = None)
```

**参数：** 与 `calculate_chinese_tfidf_similarity` 相同

---

### `BM25ChineseRetrieverAsync`

异步中文 BM25 检索器类。

```python
BM25ChineseRetrieverAsync(method: str = "lucene", stop_words: Optional[set] = stopwords)
```

**类方法：**

- `create(documents: List[str], method: str = "lucene", stop_words: Optional[set] = None) -> BM25ChineseRetrieverAsync`: 异步构造器

**方法：**

- `retrieve(queries: Union[str, List[str]], top_k: int = None) -> List[dict]`: 检索最相关的文档（异步）

---

### `calculate_chinese_bm25_similarity_async`

异步计算中文 BM25 相似度。

```python
async calculate_chinese_bm25_similarity_async(query: list, documents: list, method: str = "lucene",
                                              stop_words: Set[str] = stopwords, top_k: int = None)
```

**参数：** 与 `calculate_chinese_bm25_similarity` 相同

---

## 停用词

### `stopwords`

停用词集合，包含常见的中文停用词。

```python
from bigtools import stopwords
```

---

## YAML 工具

### `load_yaml`

加载 YAML 文件。

```python
load_yaml(file_path: str) -> dict
```

**参数：**
- `file_path` (str): YAML 文件路径

**返回：**
- `dict`: 解析后的字典

---

### `load_all_yaml`

加载包含多个文档的 YAML 文件。

```python
load_all_yaml(file_path: str) -> Generator
```

**参数：**
- `file_path` (str): YAML 文件路径

**返回：**
- `Generator`: 生成器，每次 yield 一个文档

---

### `write_yaml`

写入 YAML 文件。

```python
write_yaml(data: dict, file_path: str, mode: str = 'w')
```

**参数：**
- `data` (dict): 要写入的数据
- `file_path` (str): YAML 文件路径
- `mode` (str): 写入模式，默认 'w'

---

## 版本信息

本文档基于 bigtools 最新版本编写。如有更新，请参考项目仓库。

## 许可证

请参考项目 LICENSE 文件。

