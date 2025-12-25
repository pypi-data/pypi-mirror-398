#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
停车系统API客户端模块
该模块提供了与停车系统API交互的功能，支持同步和异步请求方式
主要功能包括：
- 生成请求签名
- 发送同步和异步API请求
- 创建配置好的HTTP客户端（同步/异步）
- 验证API响应的JSON schema

依赖库：
- httpx: 用于发送HTTP请求
- hashlib: 用于生成MD5签名
- datetime: 用于生成时间戳
- jsonschema: 用于验证API响应格式
"""

import hashlib
from datetime import datetime

import httpx
from jsonschema.validators import Draft202012Validator


class Pklot:
    """
    停车系统API客户端类
    用于与停车系统API进行交互，提供签名生成和请求发送功能
    支持同步和异步两种请求模式，可复用HTTP客户端以提高性能
    """

    def __init__(
            self,
            base_url: str = "http://ykt.test.cxyun.net.cn:7303",
            parking_id: str = "",
            app_key: str = "",
    ):
        """
        初始化停车系统API客户端

        参数:
            base_url (str): API基础URL，默认值为测试环境地址
            parking_id (str): 停车场ID，用于标识特定的停车场
            app_key (str): API应用密钥，用于生成请求签名，确保请求的安全性

        示例:
            >>> pklot_client = Pklot(
            ...     base_url="http://ykt.test.cxyun.net.cn:7303",
            ...     parking_id="your_parking_id",
            ...     app_key="your_app_key"
            ... )
        """
        # 处理URL末尾的斜杠，确保格式统一，避免后续请求拼接时出现问题
        self.base_url = base_url[:-1] if base_url.endswith("/") else base_url
        self.parking_id = parking_id  # 停车场ID，API请求的公共参数之一
        self.app_key = app_key  # API应用密钥，用于生成请求签名

    def client(self, **kwargs):
        """
        创建配置好的同步HTTP客户端

        参数:
            **kwargs: 传递给httpx.Client的额外参数，可用于覆盖默认配置

        返回:
            httpx.Client: 配置好基础URL和超时时间的同步HTTP客户端

        示例:
            >>> client = pklot_client.client(timeout=30)  # 自定义超时时间为30秒
        """
        # 设置默认基础URL，确保所有请求都指向正确的API地址
        kwargs.setdefault("base_url", self.base_url)
        # 设置默认超时时间为120秒，以适应可能的长时间请求
        kwargs.setdefault("timeout", 120)
        return httpx.Client(**kwargs)

    def async_client(self, **kwargs):
        """
        创建配置好的异步HTTP客户端

        参数:
            **kwargs: 传递给httpx.AsyncClient的额外参数，可用于覆盖默认配置

        返回:
            httpx.AsyncClient: 配置好基础URL和超时时间的异步HTTP客户端

        示例:
            >>> async_client = pklot_client.async_client(max_connections=50)  # 自定义最大连接数
        """
        # 设置默认基础URL，确保所有请求都指向正确的API地址
        kwargs.setdefault("base_url", self.base_url)
        # 设置默认超时时间为120秒，以适应可能的长时间请求
        kwargs.setdefault("timeout", 120)
        return httpx.AsyncClient(**kwargs)

    def signature(self, data: dict = dict()):
        """
        生成请求签名，用于验证API请求的合法性和完整性

        参数:
            data (dict): 需要签名的数据字典，包含API请求的参数

        返回:
            str: 生成的MD5签名字符串（大写），用于API请求的sign参数

        签名算法说明:
            1. 排除数据中的appKey字段
            2. 对剩余字段按键名进行排序
            3. 将排序后的字段以"key=value"格式用"&"连接
            4. 尾部拼接appKey的MD5值（大写）
            5. 对拼接后的字符串进行MD5计算并转为大写

        示例:
            >>> sign = pklot_client.signature({"parkingId": "123", "timestamp": 1234567890})
        """
        temp_string = ""
        # 确保data是字典类型，避免后续操作出错
        data = data if isinstance(data, dict) else dict()

        # 如果有数据需要签名
        if len(data.keys()):
            # 对字典键进行排序，确保签名的一致性
            data_sorted = sorted(data.keys())
            if isinstance(data_sorted, list):
                # 构建待签名字符串，排除appKey字段
                temp_string = "&".join([
                    f"{i}={data[i]}"
                    for i in data_sorted if i != "appKey"  # 排除appKey字段，避免重复签名
                ]) + f"{hashlib.md5(self.app_key.encode('utf-8')).hexdigest().upper()}"

        # 生成MD5签名并转换为大写格式
        return hashlib.md5(temp_string.encode('utf-8')).hexdigest().upper()

    def request(
            self,
            client: httpx.Client = None,
            validate_json_schema: dict = {
                "properties": {
                    "status": {
                        "oneOf": [
                            {"type": "integer", "const": 1},
                            {"type": "string", "const": "1"},
                        ]
                    },
                },
            },
            **kwargs
    ):
        """
        发送同步API请求，并验证响应格式

        参数:
            client (httpx.Client): 可选的HTTP客户端，如果不提供则创建新客户端
            validate_json_schema (dict): 可选的JSON schema验证规则，用于验证响应格式
            **kwargs: 传递给client.request的额外参数，如url、headers等

        返回:
            tuple: (请求是否成功, 响应JSON数据, 原始响应对象)
                - 请求是否成功: bool类型，根据响应的status字段判断
                - 响应JSON数据: dict类型，API返回的JSON数据
                - 原始响应对象: httpx.Response类型，包含完整的响应信息

        示例:
            >>> success, data, response = pklot_client.request(
            ...     url="/api/parking/info",
            ...     json={"carNumber": "京A12345"}
            ... )
        """
        # 默认使用POST方法，停车系统API通常使用POST方式接收参数
        kwargs.setdefault("method", "POST")
        # 生成当前时间戳（毫秒），用于请求签名和API的时效性验证
        timestamp = int(datetime.now().timestamp() * 1000)
        # 默认JSON数据为空字典，确保后续操作不会出错
        kwargs.setdefault("json", dict())

        # 构建请求JSON数据，包含公共参数（parkingId、timestamp、sign）
        kwargs["json"] = {
            **{
                "parkingId": self.parking_id,  # 停车场ID，必填公共参数
                "timestamp": timestamp,  # 时间戳，用于请求的时效性验证
                "sign": self.signature({  # 生成请求签名
                    "parkingId": self.parking_id,
                    "timestamp": timestamp,
                })
            },
            **kwargs["json"],  # 合并用户提供的请求参数
        }

        # 如果没有提供客户端，则创建新客户端并使用上下文管理器（自动关闭）
        if not isinstance(client, httpx.Client):
            with self.client() as client:
                response = client.request(**kwargs)
        else:
            response = client.request(**kwargs)

        # 解析响应JSON数据，如果请求失败则返回空字典
        response_json = response.json() if response.is_success else dict()

        return Draft202012Validator(validate_json_schema).is_valid(response_json), response_json, response

    async def async_request(
            self,
            client: httpx.AsyncClient = None,
            validate_json_schema: dict = {
                "properties": {
                    "status": {
                        "oneOf": [
                            {"type": "integer", "const": 1},
                            {"type": "string", "const": "1"},
                        ]
                    },
                },
            },
            **kwargs
    ):
        """
        发送异步API请求，并验证响应格式

        参数:
            client (httpx.AsyncClient): 可选的异步HTTP客户端，如果不提供则创建新客户端
            validate_json_schema (dict): 可选的JSON schema验证规则，用于验证响应格式
            **kwargs: 传递给client.request的额外参数，如url、headers等

        返回:
            tuple: (请求是否成功, 响应JSON数据, 原始响应对象)
                - 请求是否成功: bool类型，根据响应的status字段判断
                - 响应JSON数据: dict类型，API返回的JSON数据
                - 原始响应对象: httpx.Response类型，包含完整的响应信息

        示例:
            >>> import asyncio
            >>>
            >>> async def get_parking_info():
            ...     success, data, response = await pklot_client.async_request(
            ...         url="/api/parking/info",
            ...         json={"carNumber": "京A12345"}
            ...     )
            ...     return data
            >>>
            >>> result = asyncio.run(get_parking_info())
        """
        # 确保kwargs是字典类型，避免后续操作出错
        kwargs = kwargs if isinstance(kwargs, dict) else dict()
        # 默认使用POST方法，停车系统API通常使用POST方式接收参数
        kwargs.setdefault("method", "POST")
        # 生成当前时间戳（毫秒），用于请求签名和API的时效性验证
        timestamp = int(datetime.now().timestamp() * 1000)
        # 默认JSON数据为空字典，确保后续操作不会出错
        kwargs.setdefault("json", dict())

        # 构建请求JSON数据，包含公共参数（parkingId、timestamp、sign）
        kwargs["json"] = {
            **{
                "parkingId": self.parking_id,  # 停车场ID，必填公共参数
                "timestamp": timestamp,  # 时间戳，用于请求的时效性验证
                "sign": self.signature({  # 生成请求签名
                    "parkingId": self.parking_id,
                    "timestamp": timestamp,
                })
            },
            **kwargs["json"],  # 合并用户提供的请求参数
        }

        # 如果没有提供客户端，则创建新客户端并使用异步上下文管理器（自动关闭）
        if not isinstance(client, httpx.AsyncClient):
            async with self.async_client() as client:
                response = await client.request(**kwargs)
        else:
            response = await client.request(**kwargs)

        # 解析响应JSON数据，如果请求失败则返回空字典
        response_json = response.json() if response.is_success else dict()

        # 返回请求结果：(验证是否通过, 响应JSON数据, 原始响应对象)
        return Draft202012Validator(validate_json_schema).is_valid(response_json), response_json, response
