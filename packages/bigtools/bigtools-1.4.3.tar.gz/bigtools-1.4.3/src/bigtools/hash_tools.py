# -*- coding: UTF-8 -*-
# @Time : 2023/10/19 14:20 
# @Author : 刘洪波
"""
note:
- 使用 hash_object.hexdigest() 得到十六进制结果
- 使用 hash_object.digest() 得到二进制结果
- hexdigest与digest的转换
    - 需要使用binascii模块的hexlify()和unhexlify()这两个方法。
    - hexlify()将二进制结果转换成十六进制结果，unhexlify()反之。
        import binascii
        binascii.hexlify()
        binascii.unhexlify()
"""


import hashlib
from typing import Optional


HASH_FUNCTIONS = {
        'md5': hashlib.md5,
        'sha1': hashlib.sha1,
        'sha224': hashlib.sha224,
        'sha256': hashlib.sha256,
        'sha384': hashlib.sha384,
        'sha512': hashlib.sha512,
        'sha3_224': hashlib.sha3_224,
        'sha3_256': hashlib.sha3_256,
        'sha3_384': hashlib.sha3_384,
        'sha3_512': hashlib.sha3_512,
        'shake_128': hashlib.shake_128, # 生成指定字符长度的哈希, 通过 hexdigest(100) 控制长度
        'shake_256': hashlib.shake_256, # 生成指定字符长度的哈希, 通过 hexdigest(100) 控制长度
        'blake2b': hashlib.blake2b, # 生成最高512位的任意长度哈希, 长度随机
        'blake2s': hashlib.blake2s, # 生成最高256位的任意长度哈希, 长度随机
    }


def generate_hash_value(input_str: str, hash_function: str = 'md5', length: int = None) -> str:
    """
    生成 hash 值
    :param input_str: 输入字符串
    :param hash_function: hash方法
    :param length: 生成的hash 长度，仅对 shake_128 和 shake_256 有效
    :return: 只能返回十六进制结果，不返回二进制结果
    """
    if hash_function not in HASH_FUNCTIONS:
        raise ValueError(f"Unsupported hash functions: {hash_function}")

    hash_object = HASH_FUNCTIONS[hash_function]()
    hash_object.update(input_str.encode())
    if hash_function.startswith("shake_"):
        if length is None:
            raise ValueError(f"{hash_function} needs to specify the length parameter")
        return hash_object.hexdigest(length)

    if length is not None:
        raise ValueError(f"{hash_function} does not support the length parameter")

    return hash_object.hexdigest()


class HashGenerator:
    """
    哈希生成器
    - 每个哈希算法都有独立实例方法，一行定义，末尾注释说明返回值
    - shake 系列需要传 length
    """
    def __init__(self, input_str: str):
        """
        :param input_str: 待哈希的字符串
        """
        self._input_str = input_str.encode()

    def _compute(self, func_name: str, length: Optional[int] = None) -> str:
        """
        内部计算哈希值
        :param func_name: hash方法
        :param length: 生成的hash 长度，仅对 shake_128 和 shake_256 有效
        :return: 只能返回十六进制结果，不返回二进制结果
        """

        if func_name not in HASH_FUNCTIONS:
            raise ValueError(f"Unsupported hash functions: {func_name}")

        hash_func = getattr(hashlib, func_name)()
        hash_func.update(self._input_str)

        if func_name.startswith("shake_"):
            if length is None:
                raise ValueError(f"{func_name} needs to specify the length parameter")
            result = hash_func.hexdigest(length)
        else:
            if length is not None:
                raise ValueError(f"{func_name} does not support the length parameter")
            result = hash_func.hexdigest()

        return result

    # ====== 哈希算法方法 ======
    def md5(self) -> str: return self._compute("md5")  # 返回 md5 哈希值

    def sha1(self) -> str: return self._compute("sha1")  # 返回 sha1 哈希值

    def sha224(self) -> str: return self._compute("sha224")  # 返回 sha224 哈希值

    def sha256(self) -> str: return self._compute("sha256")  # 返回 sha256 哈希值

    def sha384(self) -> str: return self._compute("sha384")  # 返回 sha384 哈希值

    def sha512(self) -> str: return self._compute("sha512")  # 返回 sha512 哈希值

    def sha3_224(self) -> str: return self._compute("sha3_224")  # 返回 sha3_224 哈希值

    def sha3_256(self) -> str: return self._compute("sha3_256")  # 返回 sha3_256 哈希值

    def sha3_384(self) -> str: return self._compute("sha3_384")  # 返回 sha3_384 哈希值

    def sha3_512(self) -> str: return self._compute("sha3_512")  # 返回 sha3_512 哈希值

    def shake_128(self, length: int) -> str: return self._compute("shake_128", length)  # 返回 shake_128 哈希值

    def shake_256(self, length: int) -> str: return self._compute("shake_256", length)  # 返回 shake_256 哈希值

    def blake2b(self) -> str: return self._compute("blake2b")  # 返回 blake2b 哈希值

    def blake2s(self) -> str: return self._compute("blake2s")  # 返回 blake2s 哈希值
