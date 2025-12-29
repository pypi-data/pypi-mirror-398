# bigtools

python 工具箱，实现了一些实用的函数、类和赋值了一批常用变量，方便调用，减少工程代码量。

## Documentation

完整的 API 文档请查看 [api.md](api.md)。

## Installation

```bash
pip install bigtools
```

## Usage

### 导入方式

每个函数、类、变量均支持两种导入方式，可根据实际需求选择：

```python
# 方式一：简单直接（推荐）
from bigtools import generate_hash_value

# 方式二：包路径清晰
from bigtools.hash_tools import generate_hash_value
```

## 使用函数或类

### 示例：生成 Hash 值

```python
from bigtools import generate_hash_value
# 或
# from bigtools.hash_tools import generate_hash_value

# 默认使用 md5，可选 sha1、sha256 等
hash_value = generate_hash_value('python工具箱')
print(hash_value)
```

### 示例：文件操作

```python
from bigtools import save_file, load_file

# 保存文件
save_file('example.txt', '文件内容')

# 读取文件
content = load_file('example.txt')
print(content)
```

### 示例：JSON 操作

```python
from bigtools import save_json_data, load_json_data

# 保存 JSON 数据
data = {'name': 'bigtools', 'version': '1.4.2'}
save_json_data(data, 'data.json')

# 读取 JSON 数据
loaded_data = load_json_data('data.json')
print(loaded_data)
```

## 使用变量

### 使用 headers

```python
from bigtools import headers
# 或
# from bigtools.default_data import headers

import requests
url = 'https://example.com'
response = requests.get(url=url, headers=headers)
print(response)
```

### 使用 ContentType

大写字母开头的是类（type is class），类里包含已赋值的变量，可用 `.` 来访问变量。

```python
from bigtools import ContentType
# 或
# from bigtools.default_data import ContentType

# 发送 POST 请求
import requests
url = 'https://example.com/api'
data = {'key': 'value'}
response = requests.post(
    url=url, 
    data=data, 
    headers=ContentType.app_json_headers
)
print(response)
```

## Async usage

bigtools 提供了丰富的异步函数，适用于异步编程场景。

### 异步文件操作

```python
import asyncio
from bigtools import save_file_async, load_file_async

async def main():
    # 异步保存文件
    await save_file_async('example.txt', '文件内容')
    
    # 异步读取文件
    content = await load_file_async('example.txt')
    print(content)

asyncio.run(main())
```

### 异步 JSON 操作

```python
import asyncio
from bigtools import save_json_data_async, load_json_data_async

async def main():
    # 异步保存 JSON 数据
    data = {'name': 'bigtools', 'version': '1.4.2'}
    await save_json_data_async(data, 'data.json')
    
    # 异步读取 JSON 数据
    loaded_data = await load_json_data_async('data.json')
    print(loaded_data)

asyncio.run(main())
```

### 异步文本处理

```python
import asyncio
from bigtools import get_keywords_from_text_async

async def main():
    text = '这是一个用于测试的文本'
    keywords = await get_keywords_from_text_async(text)
    print(keywords)

asyncio.run(main())
```

### 异步相似度计算

```python
import asyncio
from bigtools import TfidfChineseRetrieverAsync, calculate_chinese_tfidf_similarity_async

async def main():
    # 创建异步 TF-IDF 检索器
    documents = ['文档1的内容', '文档2的内容', '文档3的内容']
    retriever = await TfidfChineseRetrieverAsync.create(documents)
    
    # 计算相似度
    query = '查询内容'
    similarities = await retriever.search(query, top_k=2)
    print(similarities)

asyncio.run(main())
```

### 异步数据库操作

```python
import asyncio
from bigtools import async_mongo_client, AsyncElasticsearchClient

async def main():
    # 异步 MongoDB 客户端
    mongo = async_mongo_client(host='localhost', port=27017)
    db = mongo['mydb']
    collection = db['mycollection']
    
    # 异步 Elasticsearch 客户端
    es = AsyncElasticsearchClient(hosts=['localhost:9200'])
    # 使用 es 进行异步操作...

asyncio.run(main())
```

