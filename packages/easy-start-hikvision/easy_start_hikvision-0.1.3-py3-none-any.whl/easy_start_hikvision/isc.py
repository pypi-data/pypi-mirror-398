#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
海康威视 ISecureCenter API 客户端模块
该模块提供了与海康威视 ISecureCenter 平台交互的功能，支持同步和异步请求方式
主要功能包括：
- 生成请求签名（HMAC-SHA256 算法）
- 构建符合 API 规范的请求头
- 创建配置好的同步/异步 HTTP 客户端
- 发送 API 请求并验证响应格式

依赖库：
- httpx: 用于发送 HTTP 请求，支持同步和异步
- hashlib/hmac: 用于生成请求签名
- uuid: 用于生成随机的请求标识
- datetime: 用于生成时间戳
- jsonschema: 用于验证 API 响应的 JSON 格式
"""

import base64
import hashlib
import hmac
import uuid
from datetime import datetime

import httpx
from jsonschema.validators import Draft202012Validator


class ISecureCenter:
    """
    海康威视 ISecureCenter API 客户端类
    用于与海康威视 ISecureCenter 平台进行交互，提供签名生成和请求发送功能
    支持同步和异步两种请求模式，可复用 HTTP 客户端以提高性能
    """

    def __init__(
            self,
            host: str = "",
            ak: str = "",
            sk: str = ""
    ):
        """
        初始化 ISecureCenter API 客户端
        
        参数:
            host (str): API 服务器地址，例如 "https://example.com:443"
            ak (str): 访问密钥 Access Key，用于标识请求发起者
            sk (str): 密钥 Secret Key，用于生成请求签名，确保请求的安全性
            
        示例:
            >>> isc_client = ISecureCenter(
            ...     host="https://example.com:443",
            ...     ak="your_access_key",
            ...     sk="your_secret_key"
            ... )
        """
        # 处理主机地址末尾的斜杠，确保格式统一，避免后续请求拼接时出现问题
        self.host = host[:-1] if host.endswith("/") else host
        self.ak = ak  # 访问密钥 Access Key
        self.sk = sk  # 密钥 Secret Key

    def timestamp(self):
        """
        生成当前时间戳（毫秒）
        
        返回:
            int: 当前时间戳（毫秒），用于请求的时效性验证
            
        示例:
            >>> ts = isc_client.timestamp()
            >>> print(ts)  # 输出示例: 1630000000000
        """
        return int((datetime.now().timestamp() * 1000))

    def nonce(self):
        """
        生成随机的 UUID 字符串
        
        返回:
            str: 随机的 UUID 字符串（无连字符），用于防止请求重放攻击
            
        示例:
            >>> random_nonce = isc_client.nonce()
            >>> print(random_nonce)  # 输出示例: "a1b2c3d4e5f6g7h8i9j0..."
        """
        return uuid.uuid4().hex

    def signature(self, string: str = ""):
        """
        生成请求签名
        
        参数:
            string (str): 需要签名的字符串，由请求方法、路径、请求头等信息组成
            
        返回:
            str: 生成的签名（Base64 编码的 HMAC-SHA256 哈希值），用于验证请求的完整性和真实性
            
        签名算法说明:
            1. 使用 Secret Key 作为 HMAC 密钥
            2. 对输入字符串进行 HMAC-SHA256 哈希计算
            3. 对哈希结果进行 Base64 编码并转为字符串

        """
        return base64.b64encode(
            hmac.new(
                self.sk.encode(),  # 使用密钥 Secret Key
                string.encode(),  # 待签名字符串
                digestmod=hashlib.sha256  # 使用 SHA256 哈希算法
            ).digest()
        ).decode()

    def headers(
            self,
            method: str = "POST",
            path: str = "",
            headers: dict = {}
    ):
        """
        生成符合 ISecureCenter API 规范的请求头
        
        参数:
            method (str): HTTP 请求方法，默认 POST
            path (str): 请求路径，例如 "/api/parking/info"
            headers (dict): 额外的请求头，会与默认请求头合并
            
        返回:
            dict: 完整的请求头字典，包含所有必要的认证信息
            
        请求头说明:
            - x-ca-key: 访问密钥 Access Key
            - x-ca-nonce: 随机 UUID，防止请求重放
            - x-ca-timestamp: 时间戳，用于请求的时效性验证
            - x-ca-signature: 请求签名，验证请求的完整性
            - x-ca-signature-headers: 参与签名的请求头列表
            
        示例:
            >>> headers = isc_client.headers(method="POST", path="/api/parking/info")
            >>> print(headers)
            # 输出包含认证信息的完整请求头
        """
        # 参数类型验证和默认值设置
        method = method if isinstance(method, str) else "POST"
        path = path if isinstance(path, str) else ""
        headers = headers if isinstance(headers, dict) else dict()

        # 构建基础请求头，包含 API 认证所需的公共参数
        headers = {
            "accept": "*/*",  # 接受所有响应类型
            "content-type": "application/json",  # 内容类型为 JSON
            "x-ca-signature-headers": "x-ca-key,x-ca-nonce,x-ca-timestamp",  # 参与签名的请求头
            "x-ca-key": self.ak,  # 访问密钥 Access Key
            "x-ca-nonce": self.nonce(),  # 随机 UUID，防止请求重放
            "x-ca-timestamp": str(self.timestamp()),  # 当前时间戳，用于时效性验证
            **headers  # 合并额外的请求头
        }

        # 构建待签名字符串，按照 API 规范的格式组织
        string = "\n".join([
            method,  # HTTP 请求方法
            headers["accept"],  # Accept 头
            headers["content-type"],  # Content-Type 头
            f"x-ca-key:{headers['x-ca-key']}",  # x-ca-key 头
            f"x-ca-nonce:{headers['x-ca-nonce']}",  # x-ca-nonce 头
            f"x-ca-timestamp:{headers['x-ca-timestamp']}",  # x-ca-timestamp 头
            path,  # 请求路径
        ])

        # 添加签名到请求头
        headers["x-ca-signature"] = self.signature(string=string)
        return headers

    def client(self, **kwargs):
        """
        创建配置好的同步 HTTP 客户端
        
        参数:
            **kwargs: 传递给 httpx.Client 的额外参数，可覆盖默认配置
            
        返回:
            httpx.Client: 配置好的同步 HTTP 客户端，包含默认的基础 URL、超时时间等
            
        默认配置:
            - base_url: API 服务器地址
            - timeout: 120 秒
            - verify: False (不验证 SSL 证书，仅用于测试环境)
            
        示例:
            >>> client = isc_client.client(timeout=60)  # 自定义超时时间为 60 秒
        """
        kwargs = kwargs if isinstance(kwargs, dict) else dict()
        kwargs.setdefault("base_url", self.host)  # 设置基础 URL
        kwargs.setdefault("timeout", 120)  # 设置超时时间为 120 秒
        kwargs.setdefault("verify", False)  # 不验证 SSL 证书（仅适用于测试环境）
        return httpx.Client(**kwargs)

    def async_client(self, **kwargs):
        """
        创建配置好的异步 HTTP 客户端
        
        参数:
            **kwargs: 传递给 httpx.AsyncClient 的额外参数，可覆盖默认配置
            
        返回:
            httpx.AsyncClient: 配置好的异步 HTTP 客户端，包含默认的基础 URL、超时时间等
            
        默认配置:
            - base_url: API 服务器地址
            - timeout: 120 秒
            - verify: False (不验证 SSL 证书，仅用于测试环境)
            
        示例:
            >>> async_client = isc_client.async_client(max_connections=50)  # 自定义最大连接数
        """
        kwargs = kwargs if isinstance(kwargs, dict) else dict()
        kwargs.setdefault("base_url", self.host)  # 设置基础 URL
        kwargs.setdefault("timeout", 120)  # 设置超时时间为 120 秒
        kwargs.setdefault("verify", False)  # 不验证 SSL 证书（仅适用于测试环境）
        return httpx.AsyncClient(**kwargs)

    def request(
            self,
            client: httpx.Client = None,
            validate_json_schema: dict = {
                "properties": {
                    "code": {
                        "oneOf": [
                            {"type": "string", "const": "0"},
                            {"type": "integer", "const": 0},
                        ]
                    },
                },
                "required": ["code"]
            },
            **kwargs
    ):
        """
        发送同步 API 请求，并验证响应格式
        
        参数:
            client (httpx.Client): 可选的 HTTP 客户端，如果不提供则创建新客户端
            validate_json_schema (dict): 可选的 JSON schema 验证规则，用于验证响应格式
            **kwargs: 传递给 client.request 的额外参数，如 url、headers、json 等
            
        返回:
            tuple: (请求是否成功, 响应 JSON 数据, 原始响应对象)
                - 请求是否成功: bool 类型，根据响应的 code 字段判断
                - 响应 JSON 数据: dict 类型，API 返回的 JSON 数据
                - 原始响应对象: httpx.Response 类型，包含完整的响应信息
                
        响应验证说明:
            默认验证响应中必须包含 code 字段，且值为 "0" 或 0 表示请求成功
            
        示例:
            >>> success, data, response = isc_client.request(
            ...     url="/api/parking/info",
            ...     json={"parkingId": "123"}
            ... )
            >>> if success:
            ...     print("请求成功:", data)
            ... else:
            ...     print("请求失败:", data)
        """
        # 设置默认请求参数
        kwargs.setdefault("method", "POST")  # 默认使用 POST 方法
        kwargs.setdefault("url", "")  # 默认 URL 为空
        kwargs.setdefault("headers", dict())  # 默认请求头为空字典

        # 生成请求头
        headers = self.headers(
            method=kwargs.get("method", "POST"),
            path=kwargs.get("url", ""),
            headers=kwargs.get("headers", dict())
        )
        kwargs["headers"] = headers

        # 如果没有提供客户端，则创建新客户端并使用上下文管理器
        if not isinstance(client, httpx.Client):
            with self.client() as client:
                response = client.request(**kwargs)
        else:
            response = client.request(**kwargs)

        # 解析响应 JSON 数据，如果请求失败则返回空字典
        response_json = response.json() if response.is_success else dict()

        # 返回请求结果：(验证是否通过, 响应 JSON 数据, 原始响应对象)
        return Draft202012Validator(validate_json_schema).is_valid(response_json), response_json, response

    async def async_request(
            self,
            client: httpx.AsyncClient = None,
            validate_json_schema: dict = {
                "properties": {
                    "code": {
                        "oneOf": [
                            {"type": "string", "const": "0"},
                            {"type": "integer", "const": 0},
                        ]
                    },
                },
                "required": ["code"]
            },
            **kwargs
    ):
        """
        发送异步 API 请求，并验证响应格式
        
        参数:
            client (httpx.AsyncClient): 可选的异步 HTTP 客户端，如果不提供则创建新客户端
            validate_json_schema (dict): 可选的 JSON schema 验证规则，用于验证响应格式
            **kwargs: 传递给 client.request 的额外参数，如 url、headers、json 等
            
        返回:
            tuple: (请求是否成功, 响应 JSON 数据, 原始响应对象)
                - 请求是否成功: bool 类型，根据响应的 code 字段判断
                - 响应 JSON 数据: dict 类型，API 返回的 JSON 数据
                - 原始响应对象: httpx.Response 类型，包含完整的响应信息
                
        响应验证说明:
            默认验证响应中必须包含 code 字段，且值为 "0" 或 0 表示请求成功
            
        示例:
            >>> import asyncio
            >>> 
            >>> async def get_parking_info():
            ...     success, data, response = await isc_client.async_request(
            ...         url="/api/parking/info",
            ...         json={"parkingId": "123"}
            ...     )
            ...     return data
            >>> 
            >>> result = asyncio.run(get_parking_info())
        """
        # 设置默认请求参数
        kwargs = kwargs if isinstance(kwargs, dict) else dict()
        kwargs.setdefault("method", "POST")  # 默认使用 POST 方法
        kwargs.setdefault("url", "")  # 默认 URL 为空
        kwargs.setdefault("headers", dict())  # 默认请求头为空字典

        # 生成请求头
        headers = self.headers(
            method=kwargs.get("method", "POST"),
            path=kwargs.get("url", ""),
            headers=kwargs.get("headers", dict())
        )
        kwargs["headers"] = headers

        # 如果没有提供客户端，则创建新客户端并使用异步上下文管理器
        if not isinstance(client, httpx.AsyncClient):
            async with self.async_client() as client:
                response = await client.request(**kwargs)
        else:
            response = await client.request(**kwargs)

        # 解析响应 JSON 数据，如果请求失败则返回空字典
        response_json = response.json() if response.is_success else dict()
        # 返回请求结果：(验证是否通过, 响应 JSON 数据, 原始响应对象)
        return Draft202012Validator(validate_json_schema).is_valid(response_json), response_json, response
