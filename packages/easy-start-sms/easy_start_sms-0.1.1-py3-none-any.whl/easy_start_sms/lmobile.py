#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
中国移动短信发送客户端模块

该模块提供了与中国移动短信平台API交互的功能，支持同步和异步两种发送方式。
自动处理签名生成、请求参数构建和响应解析，简化短信发送流程。
"""
import datetime
import hashlib
import random
import string
from typing import Union

import httpx
from jsonschema.validators import Draft202012Validator


class Sender:
    """中国移动短信发送客户端类
    
    用于与中国移动短信平台API交互，提供短信发送功能，支持同步和异步两种方式。
    自动处理签名生成、请求参数构建和响应解析。
    """

    def __init__(
            self,
            base_url: str = "https://api.51welink.com/",
            account_id: str = "",
            password: str = "",
            product_id: Union[int, str] = 0,
            smms_encrypt_key: str = "SMmsEncryptKey"
    ):
        """初始化Sender实例
        
        Args:
            base_url: API基础URL，默认使用中国移动短信平台地址
            account_id: 账号ID，用于API认证
            password: 账号密码，用于生成认证签名
            product_id: 产品ID，标识短信业务类型
            smms_encrypt_key: 加密密钥，用于密码加密
        """
        # 确保URL末尾没有斜杠
        self.base_url = base_url[:-1] if base_url.endswith("/") else base_url
        self.account_id = account_id
        self.password = password
        self.product_id = product_id
        self.smms_encrypt_key = smms_encrypt_key

    def client(self, **kwargs):
        """创建同步HTTP客户端
        
        Args:
            **kwargs: 传递给httpx.Client的额外参数
            
        Returns:
            httpx.Client: 配置好的同步HTTP客户端实例
        """
        # 设置默认基础URL
        kwargs.setdefault("base_url", self.base_url)
        # 设置默认超时时间为120秒
        kwargs.setdefault("timeout", 120)
        return httpx.Client(**kwargs)

    def async_client(self, **kwargs):
        """创建异步HTTP客户端
        
        Args:
            **kwargs: 传递给httpx.AsyncClient的额外参数
            
        Returns:
            httpx.AsyncClient: 配置好的异步HTTP客户端实例
        """
        # 设置默认基础URL
        kwargs.setdefault("base_url", self.base_url)
        # 设置默认超时时间为120秒
        kwargs.setdefault("timeout", 120)
        return httpx.AsyncClient(**kwargs)

    def timestamp(self):
        """生成当前时间戳（毫秒）
        
        Returns:
            int: 当前时间的毫秒时间戳
        """
        return int(datetime.datetime.now().timestamp() * 1000)

    def random_digits(self, length=10):
        """生成指定长度的随机数字字符串
        
        Args:
            length: 随机数字的长度，默认10位
            
        Returns:
            int: 随机生成的数字
        """
        return int("".join(random.sample(string.digits, length)))

    def password_md5(self):
        """对密码进行MD5加密
        
        使用密码和加密密钥组合后进行MD5加密，用于API认证
        
        Returns:
            str: MD5加密后的密码字符串
        """
        return hashlib.md5(f"{self.password}{self.smms_encrypt_key}".encode('utf-8')).hexdigest()

    def sha256_signature(self, data: dict = dict()):
        """生成SHA256签名
        
        根据API要求的参数组合生成SHA256签名，用于请求认证
        
        Args:
            data: 包含短信发送参数的字典
            
        Returns:
            str: SHA256加密后的签名字符串
        """
        data = data if isinstance(data, dict) else dict()
        # 设置默认参数
        data.setdefault("AccountId", self.account_id)
        data.setdefault("Timestamp", self.timestamp())
        data.setdefault("Random", self.random_digits())
        data.setdefault("ProductId", self.product_id)
        data.setdefault("PhoneNos", "")
        data.setdefault("Content", "")

        # 构建签名字符串
        temp_string = "&".join([
            f"AccountId={data.get("AccountId", "")}",
            f"PhoneNos={str(data.get("PhoneNos", "")).split(",")[0]}",
            f"Password={self.password_md5().upper()}",
            f"Random={data.get('Random', '')}",
            f"Timestamp={data.get('Timestamp', '')}",
        ])
        return hashlib.sha256(temp_string.encode("utf-8")).hexdigest()

    def send_sms(
            self,
            client: httpx.Client = None,
            multiple_return_values: bool = False,
            validate_json_schema: dict = {
                "type": "object",
                "properties": {
                    "Result": {"type": "string", "const": "succ"},
                },
                "required": ["Result"]
            },
            phone_nos: str = "",
            content: str = "",
            **kwargs
    ):
        """发送短信（同步方式）
        
        Args:
            client: 可选的HTTP客户端实例，如果不提供则自动创建
            multiple_return_values: 是否返回多个值，默认False
            validate_json_schema: JSON Schema 校验规则，默认校验 Result 字段为 "succ"
            phone_nos: 手机号码，多个号码用逗号分隔
            content: 短信内容
            **kwargs: 传递给request方法的额外参数
            
        Returns:
            bool: 发送结果，True表示发送成功，False表示失败
            tuple: (发送结果, 响应JSON, 响应对象)
                - 发送结果: bool，True表示发送成功，False表示失败
                - 响应JSON: dict，API返回的JSON数据
                - 响应对象: httpx.Response，原始响应对象
        """
        # 设置默认请求方法为POST
        kwargs.setdefault("method", "POST")
        # 设置默认API路径
        kwargs.setdefault("url", "/EncryptionSubmit/SendSms.ashx")
        data = kwargs.get("data", dict())
        # 设置必要的请求参数
        data.setdefault("AccountId", self.account_id)
        data.setdefault("Timestamp", self.timestamp())
        data.setdefault("Random", self.random_digits())
        data.setdefault("ProductId", self.product_id)
        data.setdefault("PhoneNos", phone_nos)
        data.setdefault("Content", content)
        # 生成并设置访问密钥
        data.setdefault("AccessKey", self.sha256_signature(data))
        kwargs["data"] = data
        # 如果没有提供客户端实例，则创建新实例并使用上下文管理器
        if not isinstance(client, httpx.Client):
            with self.client() as client:
                response = client.request(**kwargs)
        else:
            # 使用提供的客户端实例发送请求
            response = client.request(**kwargs)
        # 解析响应JSON
        response_json = response.json() if isinstance(response.json(), dict) else dict()
        # 如果请求返回多个值，返回状态、响应JSON和原始响应对象
        if multiple_return_values:
            return Draft202012Validator(validate_json_schema).is_valid(response_json), response_json, response
        # 否则仅返回状态
        return Draft202012Validator(validate_json_schema).is_valid(response_json)

    async def async_send_sms(
            self,
            client: httpx.AsyncClient = None,
            multiple_return_values: bool = False,
            validate_json_schema: dict = {
                "type": "object",
                "properties": {
                    "Result": {"type": "string", "const": "succ"},
                },
                "required": ["Result"]
            },
            phone_nos: str = "",
            content: str = "",
            **kwargs
    ):
        """发送短信（异步方式）
        
        Args:
            client: 可选的异步HTTP客户端实例，如果不提供则自动创建
            multiple_return_values: 是否返回多个值，默认False
            validate_json_schema: JSON Schema 校验规则，默认校验 Result 字段为 "succ"
            phone_nos: 手机号码，多个号码用逗号分隔
            content: 短信内容
            **kwargs: 传递给request方法的额外参数
            
        Returns:
            bool: 发送结果，True表示发送成功，False表示失败
            tuple: (发送结果, 响应JSON, 响应对象)
                - 发送结果: bool，True表示发送成功，False表示失败
                - 响应JSON: dict，API返回的JSON数据
                - 响应对象: httpx.Response，原始响应对象
        """
        kwargs = kwargs if isinstance(kwargs, dict) else kwargs
        # 设置默认请求方法为POST
        kwargs.setdefault("method", "POST")
        # 设置默认API路径
        kwargs.setdefault("url", "/EncryptionSubmit/SendSms.ashx")
        data = kwargs.get("data", dict())
        # 设置必要的请求参数
        data.setdefault("AccountId", self.account_id)
        data.setdefault("Timestamp", self.timestamp())
        data.setdefault("Random", self.random_digits())
        data.setdefault("ProductId", self.product_id)
        data.setdefault("PhoneNos", phone_nos)
        data.setdefault("Content", content)
        # 生成并设置访问密钥
        data.setdefault("AccessKey", self.sha256_signature(data))
        kwargs["data"] = data
        # 如果没有提供异步客户端实例，则创建新实例并使用上下文管理器
        if not isinstance(client, httpx.AsyncClient):
            async with self.async_client() as client:
                response = await client.request(**kwargs)
        else:
            # 使用提供的异步客户端实例发送请求
            response = await client.request(**kwargs)

        # 解析响应JSON
        response_json = response.json() if isinstance(response.json(), dict) else dict()
        # 如果请求返回多个值，返回状态、响应JSON和原始响应对象
        if multiple_return_values:
            return Draft202012Validator(validate_json_schema).is_valid(response_json), response_json, response
        # 否则仅返回状态
        return Draft202012Validator(validate_json_schema).is_valid(response_json)
