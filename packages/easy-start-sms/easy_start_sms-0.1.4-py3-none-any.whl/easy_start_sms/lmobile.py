#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
微网通联短信发送客户端模块

该模块提供了与微网通联短信平台API交互的功能，支持同步和异步两种发送方式。
自动处理签名生成、请求参数构建和响应解析，简化短信发送流程。

典型用法:
    from easy_start_sms.lmobile import Sender
    
    # 初始化客户端
    sender = Sender(
        account_id="your_account_id",
        password="your_password",
        product_id="your_product_id"
    )
    
    # 同步发送短信
    success, response_json, response = sender.send_sms(
        phone_nos="13800138000",
        content="测试短信内容"
    )
    
    # 异步发送短信
    # import asyncio
    # async def send_async():
    #     success, response_json, response = await sender.async_send_sms(
    #         phone_nos="13800138000",
    #         content="测试短信内容"
    #     )
    # asyncio.run(send_async())
"""
import datetime
import hashlib
import random
import string
from typing import Union

import httpx
from jsonschema.validators import Draft202012Validator


class Sender:
    """微网通联短信发送客户端类
    
    用于与微网通联短信平台API交互，提供短信发送功能，支持同步和异步两种方式。
    自动处理签名生成、请求参数构建和响应解析。
    
    属性:
        base_url: API基础URL
        account_id: 账号ID
        password: 账号密码
        product_id: 产品ID
        smms_encrypt_key: 加密密钥
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
            base_url: API基础URL，默认使用微网通联短信平台地址
            account_id: 账号ID，用于API认证
            password: 账号密码，用于生成认证签名
            product_id: 产品ID，标识短信业务类型
            smms_encrypt_key: 加密密钥，用于密码加密
        """
        # 确保URL末尾没有斜杠，统一URL格式
        self.base_url = base_url[:-1] if base_url.endswith("/") else base_url
        self.account_id = account_id
        self.password = password
        self.product_id = product_id
        self.smms_encrypt_key = smms_encrypt_key

    def client(self, **kwargs):
        """创建同步HTTP客户端
        
        配置并返回一个带有默认设置的同步HTTP客户端实例，用于发送短信请求。
        
        Args:
            **kwargs: 传递给httpx.Client的额外参数，可以覆盖默认设置
            
        Returns:
            httpx.Client: 配置好的同步HTTP客户端实例
        """
        # 设置默认基础URL
        kwargs.setdefault("base_url", self.base_url)
        # 设置默认超时时间为120秒，确保有足够时间处理网络请求
        kwargs.setdefault("timeout", 120)
        return httpx.Client(**kwargs)

    def async_client(self, **kwargs):
        """创建异步HTTP客户端
        
        配置并返回一个带有默认设置的异步HTTP客户端实例，用于异步发送短信请求。
        
        Args:
            **kwargs: 传递给httpx.AsyncClient的额外参数，可以覆盖默认设置
            
        Returns:
            httpx.AsyncClient: 配置好的异步HTTP客户端实例
        """
        # 设置默认基础URL
        kwargs.setdefault("base_url", self.base_url)
        # 设置默认超时时间为120秒，确保有足够时间处理网络请求
        kwargs.setdefault("timeout", 120)
        return httpx.AsyncClient(**kwargs)

    def timestamp(self):
        """生成当前时间戳（毫秒）
        
        用于API请求中的时间戳参数，确保请求的时效性。
        
        Returns:
            int: 当前时间的毫秒时间戳
        """
        return int(datetime.datetime.now().timestamp() * 1000)

    def random_digits(self, length=10):
        """生成指定长度的随机数字字符串
        
        用于API请求中的随机数参数，增加请求的唯一性。
        
        Args:
            length: 随机数字的长度，默认10位
            
        Returns:
            int: 随机生成的数字
        """
        return int("".join(random.sample(string.digits, length)))

    def password_md5(self):
        """对密码进行MD5加密
        
        使用密码和加密密钥组合后进行MD5加密，用于API认证的密码部分。
        
        Returns:
            str: MD5加密后的密码字符串
        """
        return hashlib.md5(f"{self.password}{self.smms_encrypt_key}".encode('utf-8')).hexdigest()

    def sha256_signature(self, data: dict = dict()):
        """生成SHA256签名
        
        根据API要求的参数组合生成SHA256签名，用于请求认证，确保请求的安全性和完整性。
        
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

        # 构建签名字符串 - 按照API要求的顺序和格式拼接参数
        temp_string = "&".join([
            f"AccountId={data.get('AccountId', '')}",
            f"PhoneNos={str(data.get('PhoneNos', '')).split(',')[0]}",  # 只取第一个手机号用于签名
            f"Password={self.password_md5().upper()}",  # 密码使用MD5加密后转大写
            f"Random={data.get('Random', '')}",
            f"Timestamp={data.get('Timestamp', '')}",
        ])
        return hashlib.sha256(temp_string.encode("utf-8")).hexdigest()

    def send_sms(
            self,
            client: httpx.Client = None,
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
        
        调用微网通联短信平台API发送短信，支持批量发送和自定义参数。
        
        Args:
            client: 可选的HTTP客户端实例，如果不提供则自动创建
            validate_json_schema: JSON Schema 校验规则，用于验证API响应的有效性
            phone_nos: 手机号码，多个号码用逗号分隔
            content: 短信内容
            **kwargs: 传递给request方法的额外参数
            
        Returns:
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
        # 生成并设置访问密钥（签名）
        data.setdefault("AccessKey", self.sha256_signature(data))
        kwargs["data"] = data

        # 使用客户端发送请求
        if not isinstance(client, httpx.Client):
            # 如果没有提供客户端实例，则创建新实例并使用上下文管理器
            with self.client() as client:
                response = client.request(**kwargs)
        else:
            # 使用提供的客户端实例发送请求
            response = client.request(**kwargs)

        # 解析响应JSON
        response_json = response.json() if isinstance(response.json(), dict) else dict()

        return Draft202012Validator(validate_json_schema).is_valid(response_json), response_json, response

    async def async_send_sms(
            self,
            client: httpx.AsyncClient = None,
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
        
        异步调用微网通联短信平台API发送短信，支持批量发送和自定义参数。
        
        Args:
            client: 可选的异步HTTP客户端实例，如果不提供则自动创建
            validate_json_schema: JSON Schema 校验规则，用于验证API响应的有效性
            phone_nos: 手机号码，多个号码用逗号分隔
            content: 短信内容
            **kwargs: 传递给request方法的额外参数
            
        Returns:
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
        # 生成并设置访问密钥（签名）
        data.setdefault("AccessKey", self.sha256_signature(data))
        kwargs["data"] = data

        # 使用异步客户端发送请求
        if not isinstance(client, httpx.AsyncClient):
            # 如果没有提供异步客户端实例，则创建新实例并使用上下文管理器
            async with self.async_client() as client:
                response = await client.request(**kwargs)
        else:
            # 使用提供的异步客户端实例发送请求
            response = await client.request(**kwargs)

        # 解析响应JSON
        response_json = response.json() if isinstance(response.json(), dict) else dict()

        return Draft202012Validator(validate_json_schema).is_valid(response_json), response_json, response
