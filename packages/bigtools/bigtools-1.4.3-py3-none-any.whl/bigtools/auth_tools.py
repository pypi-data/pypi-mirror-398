# -*- coding: UTF-8 -*-
# @Time : 2025/9/19 17:29 
# @Author : 刘洪波
import hmac
import hashlib
import base64
import json
import time
import logging
import secrets
from typing import Callable, Dict


def generate_api_key(n_bytes: int = 32) -> str:
    """
    生成 URL-safe 的 API Key（32 bytes -> 43 chars）
    最好只在前端展示一次
    """
    return secrets.token_urlsafe(n_bytes)


def compute_key_hmac(api_key: str, secret_key: str) -> str:
    """
    计算用于存储的 HMAC（hex）, 一般与 user_id 、api、create_time、expire_time 一起存储
    :param api_key: 用户的api_key
    :param secret_key: 用户私有密钥
    :return:
    """
    return hmac.new(secret_key.encode('utf-8'), api_key.encode('utf-8'), hashlib.sha256).hexdigest()


def generate_hmac_signature(secret_key: str, message: str) -> str:
    """
    使用 HMAC-SHA256 算法生成签名，并进行 URL 安全的 Base64 编码。
    :param secret_key: 签名所用的密钥
    :param message: 需要签名的消息内容
    :return: URL 安全的 Base64 编码后的签名字符串（去掉了尾部 '=' 填充）
    """
    raw_signature = hmac.new(secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw_signature).rstrip(b"=").decode("utf-8")


def verify_hmac_signature(secret_key: str, message: str, signature: str) -> bool:
    """
    验证给定的签名是否正确。
    :param secret_key: 签名所用的密钥
    :param message: 需要签名的消息内容
    :param signature: 需要验证的签名（URL 安全的 Base64 编码字符串）
    :return: True 表示验证成功，False 表示验证失败
    """
    # 重新生成签名
    expected_signature = generate_hmac_signature(secret_key, message)
    # 使用 hmac.compare_digest 避免时序攻击
    return hmac.compare_digest(expected_signature, signature)


def dict_to_urlsafe_b64(data: dict) -> str:
    """
    将 Python 字典编码为 URL-safe Base64 字符串。

    编码流程：
    1. 使用 `json.dumps` 将字典转换为 JSON 字符串，并去除多余空格（separators=(",", ":")）。
    2. 将 JSON 字符串以 UTF-8 编码为字节。
    3. 使用 `base64.urlsafe_b64encode` 进行 URL-safe Base64 编码。
    4. 去掉 Base64 编码末尾的填充符号 '='。
    5. 返回最终的字符串结果。

    :param data: 需要编码的字典
    :return: URL-safe Base64 编码后的字符串（无填充符号）
    """
    json_data = json.dumps(data, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(json_data).rstrip(b"=").decode("utf-8")


def urlsafe_b64_to_dict(us_str: str) -> dict:
    """
    将 URL-safe Base64 字符串解码为 Python 字典。

    解码流程：
    1. 还原缺失的 '=' 填充符号（Base64 要求长度必须是 4 的倍数）。
    2. 使用 `base64.urlsafe_b64decode` 解码为字节。
    3. 将字节按 UTF-8 解码为 JSON 字符串。
    4. 使用 `json.loads` 转换为字典。

    :param us_str: URL-safe Base64 编码的字符串（无 '=' 填充符号）
    :return: 解码后的字典
    """
    # 补齐缺失的 '='，确保长度为 4 的倍数
    padding = '=' * (-len(us_str) % 4)
    decoded_bytes = base64.urlsafe_b64decode(us_str + padding)
    return json.loads(decoded_bytes.decode("utf-8"))


def insert_hybrid(str1: str, str2: str) -> str:
    """交叉合并两个字符串"""
    length = min(len(str1), len(str2))
    result = [str1[i] + str2[i] for i in range(length)]
    result.append(str1[length:])
    result.append(str2[length:])
    return ''.join(result)


def insert_ahead(str1: str, str2: str) -> str:
    """str2 插在 str1 前面"""
    return str2 + str1


def insert_after(str1: str, str2: str) -> str:
    """str2 插在 str1 后面"""
    return str1 + str2


merge_method_dict: Dict[str, Callable[[str, str], str]] = {
    'hybrid': insert_hybrid,
    'ahead': insert_ahead,
    'after': insert_after
}


def merge_str(str1, str2, merge_method: str = 'hybrid') -> str:
    """
    根据指定算法合并两个字符串
    :param str1: 第一个字符串
    :param str2: 第二个字符串
    :param merge_method: 合并方式 ('hybrid', 'ahead', 'after')
    :return: 合并后的字符串
    """
    if str1 and str2 and merge_method:
        if merge_method in merge_method_dict:
            return merge_method_dict[merge_method](str1, str2)
        else:
            raise ValueError('Error: The input parameter algorithm is incorrect!')
    else:
        raise ValueError('Error: Input parameter error, please check!')


class SignatureGenerator:
    def __init__(self, payload: dict, secret_key: str, expire_seconds: int = 3600):
        self.payload = payload
        self.secret_key = secret_key
        self.expire_seconds = expire_seconds
        self.hybrid_method = [self.insert_universal, self.insert_hybrid, self.insert_ahead, self.insert_after]
        self.payload_copy = payload.copy()
        self.payload_copy["exp"] = int(time.time()) + expire_seconds

    def insert(self, merge_method: str):
        """
        通过传入merge_method进行insert
        :param merge_method: 合并方式 ('universal'，'hybrid', 'ahead', 'after')
        :return:
        """
        functions = {
            'universal': self.insert_universal,
            'hybrid': self.insert_hybrid,
            'ahead': self.insert_ahead,
            'after': self.insert_after,
        }
        return functions[merge_method]()

    def insert_random(self):
        """随机选择一个方式"""
        return secrets.choice(self.hybrid_method)()

    def insert_universal(self):
        self.payload_copy["merge_method"] = 'universal'
        payload_json = json.dumps(self.payload_copy, separators=(",", ":"))  # separators=(',', ':') 可以生成更紧凑的 JSON，去掉不必要的空格。
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode('utf-8')).rstrip(b"=").decode('utf-8')
        signature = generate_hmac_signature(self.secret_key, payload_json)
        return payload_b64, signature

    def insert_hybrid(self):
        self.payload_copy["merge_method"] = 'hybrid'
        payload_json = json.dumps(self.payload_copy, separators=(",", ":"))
        return self.hmac_and_base64(insert_hybrid(self.secret_key, payload_json))

    def insert_ahead(self):
        self.payload_copy["merge_method"] = 'ahead'
        payload_json = json.dumps(self.payload_copy, separators=(",", ":"))
        return self.hmac_and_base64(insert_ahead(self.secret_key, payload_json))

    def insert_after(self):
        self.payload_copy["merge_method"] = 'after'
        payload_json = json.dumps(self.payload_copy, separators=(",", ":"))
        return self.hmac_and_base64(insert_after(self.secret_key, payload_json))

    def hmac_and_base64(self, merged_key: str):
        payload_b64 = dict_to_urlsafe_b64(self.payload_copy)
        signature = generate_hmac_signature(merged_key, '')
        return payload_b64, signature


def verify_signature(signature: str, payload_b64: str, secret_key: str, logger: logging.Logger = None) -> dict:
    """
    验证 signature
    :param signature: b64编码的signature
    :param payload_b64: 生成signature所依赖的信息，一般是用户的信息
    :param secret_key: 用户的私有密钥
    :param logger: 日志收集器
    :return:
    """
    try:
        payload_str = base64.urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4)).decode('utf-8')
        payload_json = json.loads(payload_str)
        if payload_json.get("exp", 0) < int(time.time()):
            return {'payload': {}, 'status': False, 'msg': 'Verification failed: token has expired'}

        new_secret_key = secret_key
        new_payload_str = payload_str
        merge_method = payload_json['merge_method']
        merge_func = merge_method_dict.get(merge_method)
        if merge_func:
            new_secret_key = merge_func(secret_key, payload_str)
            new_payload_str = ''
        if not verify_hmac_signature(new_secret_key, new_payload_str, signature):
            return {'payload': {}, 'status': False, 'msg': 'Verification failed: token mismatch'}

        return {'payload': payload_json, 'status': True, 'msg': ''}
    except Exception as e:
        error_info = f'Verification failed: {e}'
        if logger:
            logger.error(error_info, exc_info=True)
        else:
            print(error_info)
        return {'payload': {}, 'status': False, 'msg': error_info}


def refresh_signature(signature: str, payload_b64: str, secret_key: str, expire_seconds: int = 3600, forced_refresh: bool = False,
                  threshold: int = 300, logger: logging.Logger = None) -> dict:
    """
    刷新 signature
    :param signature: b64编码的signature
    :param payload_b64: 生成signature所依赖的信息，一般是用户的信息
    :param secret_key: 用户的私有密钥
    :param expire_seconds: 过期时间
    :param forced_refresh: 是否强制刷新signature, 默认不强制
    :param threshold: 过期前多久进行刷新
    :param logger: 日志收集器
    :return:
    """
    verify_result = verify_signature(signature, payload_b64, secret_key, logger=logger)
    if not verify_result['status']:
        verify_result['signature'] = ''
        return verify_result

    payload_json = verify_result['payload']
    msg = f'The signature has been refreshed. Remaining time: {expire_seconds} seconds'
    merge_method = payload_json['merge_method']
    if forced_refresh:
        # 强制刷新 token
        payload_json.pop("exp", None)
        new_payload, new_signature = SignatureGenerator(payload_json, secret_key, expire_seconds).insert(merge_method)
    else:
        # 过期前多久进行刷新
        remaining = payload_json["exp"] - int(time.time())
        if remaining < threshold:
            # 接近过期时间进行刷新
            payload_json.pop("exp", None)
            new_payload, new_signature = SignatureGenerator(payload_json, secret_key, expire_seconds).insert(merge_method)
        else:
            # 还在有效期则不刷新
            new_payload, new_signature = payload_b64, signature
            msg = f'The signature has not been refreshed. Remaining time: {remaining} seconds'
    return {'signature': new_signature, 'payload': new_payload, 'status': True, 'msg': msg}


def build_jwt_token(payload: str , signature: str, separator: str = '.'):
    """
    构造JWT 标准 Token
    :param payload: 负载信息
    :param signature: 签名
    :param separator: 分隔符，默认为“.” , 也可以指定其他的，例如： # ｜
    :return:
    """
    return payload + separator + signature


def build_and_encode_jwt_token(payload: str , signature: str, separator: str = '.'):
    """
    构造JWT 标准 Token 并再次编码
    :param payload: 负载信息
    :param signature: 签名
    :param separator: 分隔符，默认为“.” , 也可以指定其他的，例如： # ｜
    :return:
    """
    return base64.urlsafe_b64encode((payload + separator + signature).encode('utf-8')).rstrip(b"=").decode("utf-8")
