#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
群接龙开放平台 API 客户端模块

本模块提供了与群接龙开放平台 API 进行交互的客户端实现，支持以下功能：
- 访问令牌的获取与刷新
- 支持同步和异步 HTTP 请求
- 响应数据的 JSON Schema 验证
- 访问令牌的缓存管理（支持 diskcache 和 Redis）
- 灵活的 API 请求接口

依赖库：
- httpx: 用于发送 HTTP 请求
- jsonschema: 用于验证 API 响应格式
- diskcache: 用于本地缓存访问令牌
- redis: 用于分布式缓存访问令牌
"""
import diskcache
import httpx
import redis
from jsonschema.validators import Draft202012Validator


class Api:
    """
    群接龙开放平台 API 客户端类

    提供与群接龙开放平台 API 交互的核心功能，包括令牌管理、请求发送和响应验证。

    示例用法：
    ```python
    from easy_start_qunjielong.open import Api

    # 初始化 API 客户端
    api = Api(secret="your_secret_key")

    # 刷新访问令牌
    api.refresh_token()

    # 发送 API 请求
    success, data, response = api.request(method="GET", url="/open/api/some_endpoint")
    ```
    """

    def __init__(
            self,
            base_url: str = "https://openapi.qunjielong.com",
            secret: str = "",
            cache_config: dict = None
    ):
        """
        初始化 API 客户端

        Args:
            base_url (str, optional): API 基础 URL，默认为 "https://openapi.qunjielong.com"
            secret (str, optional): 应用密钥，用于获取访问令牌
            cache_config (dict, optional): 缓存配置字典，包含以下键：
                - key (str): 缓存键名，默认为 "qunjielong_open_access_token_{secret}"
                - expire (int): 缓存过期时间（秒），默认为 7100
                - instance: 缓存实例（diskcache.Cache 或 redis.Redis/StrictRedis）
        """
        # 确保 base_url 不以斜杠结尾
        self.base_url = base_url[:-1] if base_url.endswith("/") else base_url
        self.secret = secret  # 应用密钥
        self.access_token = ""  # 访问令牌
        # 初始化缓存配置
        self.cache_config = cache_config if isinstance(cache_config, dict) else dict()
        # 设置缓存键名，默认包含 secret 以区分不同应用
        self.cache_config.setdefault("key", f"qunjielong_open_access_token_{self.secret}")
        # 设置缓存过期时间，默认 7100 秒（接近 2 小时，小于令牌有效期 2 小时）
        self.cache_config.setdefault("expire", 7100)
        # 设置缓存实例，默认 None
        self.cache_config.setdefault("instance", None)

    def client(self, **kwargs):
        """
        创建同步 HTTP 客户端

        Args:
            **kwargs: 传递给 httpx.Client 的额外参数

        Returns:
            httpx.Client: 配置好的同步 HTTP 客户端
        """
        kwargs.setdefault("base_url", self.base_url)  # 设置基础 URL
        kwargs.setdefault("timeout", 120)  # 设置超时时间（秒）
        kwargs.setdefault("verify", False)  # 禁用 SSL 验证
        return httpx.Client(**kwargs)

    def async_client(self, **kwargs):
        """
        创建异步 HTTP 客户端

        Args:
            **kwargs: 传递给 httpx.AsyncClient 的额外参数

        Returns:
            httpx.AsyncClient: 配置好的异步 HTTP 客户端
        """
        kwargs.setdefault("base_url", self.base_url)  # 设置基础 URL
        kwargs.setdefault("timeout", 120)  # 设置超时时间（秒）
        kwargs.setdefault("verify", False)  # 禁用 SSL 验证
        return httpx.AsyncClient(**kwargs)

    def token(
            self,
            client: httpx.Client = None,
            validate_json_schema: dict = {
                "properties": {
                    "code": {
                        "oneOf": [
                            {"type": "integer", "const": 200},
                            {"type": "string", "const": "200"},
                        ],
                    }
                },
                "required": ["code"],
            },
            **kwargs
    ):
        """
        获取访问令牌

        Args:
            client (httpx.Client, optional): 已配置的同步 HTTP 客户端
            validate_json_schema (dict, optional): 响应数据的 JSON Schema 验证规则
            **kwargs: 传递给 client.request 的额外参数

        Returns:
            tuple: (验证状态, 访问令牌, 原始响应)
                - 验证状态 (bool): API 响应是否符合 JSON Schema
                - 访问令牌 (str): 获取到的访问令牌，如果失败则为 None
                - 原始响应 (httpx.Response): API 请求的原始响应对象
        """
        kwargs.setdefault("method", "GET")  # 默认使用 GET 方法
        kwargs.setdefault("url", "/open/auth/token")  # 设置令牌获取接口路径
        # 获取或创建参数字典
        params = kwargs.get("params", dict())
        params.setdefault("secret", self.secret)  # 设置应用密钥参数
        kwargs["params"] = params
        
        # 如果没有提供客户端，则创建临时客户端
        if not isinstance(client, httpx.Client):
            with self.client() as client:
                response = client.request(**kwargs)
        else:
            response = client.request(**kwargs)
        
        # 解析响应数据
        response_json = response.json() if response.is_success else dict()
        # 更新访问令牌
        self.access_token = response_json.get("data", None)
        
        # 验证响应并返回结果
        return (
            Draft202012Validator(validate_json_schema).is_valid(response_json),
            response_json.get("data", None),
            response
        )

    async def async_token(
            self,
            client: httpx.AsyncClient = None,
            validate_json_schema: dict = {
                "properties": {
                    "code": {
                        "oneOf": [
                            {"type": "integer", "const": 200},
                            {"type": "string", "const": "200"},
                        ],
                    }
                },
                "required": ["code"],
            },
            **kwargs
    ):
        """
        异步获取访问令牌

        Args:
            client (httpx.AsyncClient, optional): 已配置的异步 HTTP 客户端
            validate_json_schema (dict, optional): 响应数据的 JSON Schema 验证规则
            **kwargs: 传递给 client.request 的额外参数

        Returns:
            tuple: (验证状态, 访问令牌, 原始响应)
                - 验证状态 (bool): API 响应是否符合 JSON Schema
                - 访问令牌 (str): 获取到的访问令牌，如果失败则为 None
                - 原始响应 (httpx.Response): API 请求的原始响应对象
        """
        kwargs.setdefault("method", "GET")  # 默认使用 GET 方法
        kwargs.setdefault("url", "/open/auth/token")  # 设置令牌获取接口路径
        # 获取或创建参数字典
        params = kwargs.get("params", dict())
        params.setdefault("secret", self.secret)  # 设置应用密钥参数
        kwargs["params"] = params
        
        # 如果没有提供客户端，则创建临时客户端
        if not isinstance(client, httpx.AsyncClient):
            async with self.async_client() as client:
                response = await client.request(**kwargs)
        else:
            response = await client.request(**kwargs)
        
        # 解析响应数据
        response_json = response.json() if response.is_success else dict()
        # 更新访问令牌
        self.access_token = response_json.get("data", None)
        
        # 验证响应并返回结果
        return (
            Draft202012Validator(validate_json_schema).is_valid(response_json),
            response_json.get("data", None),
            response
        )

    def ghome_getGhomeInfo(
            self,
            client: httpx.Client = None,
            validate_json_schema: dict = {
                "properties": {
                    "code": {
                        "oneOf": [
                            {"type": "integer", "const": 200},
                            {"type": "string", "const": "200"},
                        ],
                    },
                    "data": {
                        "properties": {
                            "ghId": {"type": "integer", "minimum": 1},
                        },
                        "required": ["ghId"]
                    }
                },
                "required": ["code"],
            },
            access_token: str = None,
            **kwargs
    ):
        """
        获取管家信息（用于验证访问令牌有效性）

        Args:
            client (httpx.Client, optional): 已配置的同步 HTTP 客户端
            validate_json_schema (dict, optional): 响应数据的 JSON Schema 验证规则
            access_token (str, optional): 访问令牌，默认使用客户端存储的令牌
            **kwargs: 传递给 client.request 的额外参数

        Returns:
            tuple: (验证状态, 管家信息, 原始响应)
                - 验证状态 (bool): API 响应是否符合 JSON Schema
                - 管家信息 (dict): 包含 ghId 等管家信息的字典
                - 原始响应 (httpx.Response): API 请求的原始响应对象
        """
        # 使用提供的令牌或客户端存储的令牌
        access_token = access_token if isinstance(access_token, str) and len(access_token) else self.access_token
        kwargs.setdefault("method", "GET")  # 默认使用 GET 方法
        kwargs.setdefault("url", "/open/api/ghome/getGhomeInfo")  # 设置接口路径
        # 获取或创建参数字典
        params = kwargs.get("params", dict())
        params.setdefault("accessToken", access_token)  # 设置访问令牌参数
        kwargs["params"] = params
        
        # 如果没有提供客户端，则创建临时客户端
        if not isinstance(client, httpx.Client):
            with self.client() as client:
                response = client.request(**kwargs)
        else:
            response = client.request(**kwargs)
        
        # 解析响应数据
        response_json = response.json() if response.is_success else dict()
        
        # 验证响应并返回结果
        return (
            Draft202012Validator(validate_json_schema).is_valid(response_json),
            response_json.get("data", None),
            response
        )

    async def async_ghome_getGhomeInfo(
            self,
            client: httpx.AsyncClient = None,
            validate_json_schema: dict = {
                "properties": {
                    "code": {
                        "oneOf": [
                            {"type": "integer", "const": 200},
                            {"type": "string", "const": "200"},
                        ],
                    },
                    "data": {
                        "properties": {
                            "ghId": {"type": "integer", "minimum": 1},
                        },
                        "required": ["ghId"]
                    }
                },
                "required": ["code"],
            },
            access_token: str = None,
            **kwargs
    ):
        """
        异步获取管家信息（用于验证访问令牌有效性）

        Args:
            client (httpx.AsyncClient, optional): 已配置的异步 HTTP 客户端
            validate_json_schema (dict, optional): 响应数据的 JSON Schema 验证规则
            access_token (str, optional): 访问令牌，默认使用客户端存储的令牌
            **kwargs: 传递给 client.request 的额外参数

        Returns:
            tuple: (验证状态, 管家信息, 原始响应)
                - 验证状态 (bool): API 响应是否符合 JSON Schema
                - 管家信息 (dict): 包含 ghId 等管家信息的字典
                - 原始响应 (httpx.Response): API 请求的原始响应对象
        """
        # 使用提供的令牌或客户端存储的令牌
        access_token = access_token if isinstance(access_token, str) and len(access_token) else self.access_token
        kwargs.setdefault("method", "GET")  # 默认使用 GET 方法
        kwargs.setdefault("url", "/open/api/ghome/getGhomeInfo")  # 设置接口路径
        # 获取或创建参数字典
        params = kwargs.get("params", dict())
        params.setdefault("accessToken", access_token)  # 设置访问令牌参数
        kwargs["params"] = params
        
        # 如果没有提供客户端，则创建临时客户端
        if not isinstance(client, httpx.AsyncClient):
            async with self.async_client() as client:
                response = await client.request(**kwargs)
        else:
            response = await client.request(**kwargs)
        
        # 解析响应数据
        response_json = response.json() if response.is_success else dict()
        
        # 验证响应并返回结果
        return (
            Draft202012Validator(validate_json_schema).is_valid(response_json),
            response_json.get("data", None),
            response
        )

    def refresh_token(self, client: httpx.Client = None):
        """
        刷新访问令牌（同步）

        该方法会：
        1. 从缓存获取访问令牌（如果有缓存配置）
        2. 验证令牌有效性
        3. 如果令牌无效或不存在，则重新获取
        4. 将新令牌存入缓存（如果有缓存配置）

        Args:
            client (httpx.Client, optional): 已配置的同步 HTTP 客户端

        Returns:
            self: 返回客户端实例，支持链式调用
        """
        cache_key = self.cache_config.get("key", f"qunjielong_open_access_token_{self.secret}")
        cache_inst = self.cache_config.get("instance", None)
        cache_expire = self.cache_config.get("expire", 7100)

        # 如果没有缓存实例或缓存实例类型不支持，则直接获取新令牌
        if not isinstance(cache_inst, (diskcache.Cache, redis.Redis, redis.StrictRedis)):
            state, access_token, _ = self.token(client=client)
        else:
            # 从缓存获取访问令牌
            access_token = cache_inst.get(cache_key, None)

        # 验证访问令牌是否有效
        state, _, _ = self.ghome_getGhomeInfo(client=client, access_token=access_token)
        if not state:
            # 访问令牌无效，重新获取
            state, access_token, _ = self.token(client=client)

        # 将访问令牌存入缓存
        if state and isinstance(cache_inst, diskcache.Cache):
            cache_inst.set(cache_key, access_token, expire=cache_expire)
        if state and isinstance(cache_inst, (redis.Redis, redis.StrictRedis)):
            cache_inst.set(cache_key, access_token, ex=cache_expire)
        
        # 更新客户端存储的令牌
        self.access_token = access_token
        return self

    async def async_refresh_token(self, client: httpx.AsyncClient = None):
        """
        异步刷新访问令牌

        该方法会：
        1. 从缓存获取访问令牌（如果有缓存配置）
        2. 验证令牌有效性
        3. 如果令牌无效或不存在，则重新获取
        4. 将新令牌存入缓存（如果有缓存配置）

        Args:
            client (httpx.AsyncClient, optional): 已配置的异步 HTTP 客户端

        Returns:
            self: 返回客户端实例，支持链式调用
        """
        cache_key = self.cache_config.get("key", f"qunjielong_open_access_token_{self.secret}")
        cache_inst = self.cache_config.get("instance", None)
        cache_expire = self.cache_config.get("expire", 7100)
        
        # 如果没有缓存实例或缓存实例类型不支持，则直接获取新令牌
        if not isinstance(cache_inst, (diskcache.Cache, redis.Redis, redis.StrictRedis)):
            state, access_token, _ = await self.async_token(client=client)
        else:
            # 从缓存获取访问令牌
            access_token = cache_inst.get(cache_key, None)

        # 验证访问令牌是否有效
        state, _, _ = await self.async_ghome_getGhomeInfo(client=client, access_token=access_token)
        if not state:
            # 访问令牌无效，重新获取
            state, access_token, _ = await self.async_token(client=client)

        # 将访问令牌存入缓存
        if state and isinstance(cache_inst, diskcache.Cache):
            cache_inst.set(cache_key, access_token, expire=cache_expire)
        if state and isinstance(cache_inst, (redis.Redis, redis.StrictRedis)):
            cache_inst.set(cache_key, access_token, ex=cache_expire)
        
        # 更新客户端存储的令牌
        self.access_token = access_token
        return self

    def request(
            self,
            client: httpx.Client = None,
            validate_json_schema: dict = {
                "properties": {
                    "code": {
                        "oneOf": [
                            {"type": "integer", "const": 200},
                            {"type": "string", "const": "200"},
                        ],
                    },
                }
            },
            access_token: str = None,
            **kwargs
    ):
        """
        发送同步 API 请求

        Args:
            client (httpx.Client, optional): 已配置的同步 HTTP 客户端
            validate_json_schema (dict, optional): 响应数据的 JSON Schema 验证规则
            access_token (str, optional): 访问令牌，默认使用客户端存储的令牌
            **kwargs: 传递给 client.request 的额外参数，包括：
                - method (str): 请求方法（GET/POST/PUT/DELETE 等）
                - url (str): 请求路径
                - params (dict): URL 查询参数
                - json (dict): 请求体 JSON 数据
                - data (dict/str): 请求体表单数据
                - files (dict): 文件上传数据

        Returns:
            tuple: (验证状态, 响应数据, 原始响应)
                - 验证状态 (bool): API 响应是否符合 JSON Schema
                - 响应数据 (dict): API 响应的 data 字段内容
                - 原始响应 (httpx.Response): API 请求的原始响应对象
        """
        # 使用提供的令牌或客户端存储的令牌
        access_token = access_token if isinstance(access_token, str) and len(access_token) else self.access_token
        kwargs.setdefault("method", "GET")  # 默认使用 GET 方法
        
        # 获取或创建参数字典
        params = kwargs.get("params", dict())
        params.setdefault("accessToken", access_token)  # 设置访问令牌参数
        kwargs["params"] = params
        
        # 如果没有提供客户端，则创建临时客户端
        if not isinstance(client, httpx.Client):
            with self.client() as client:
                response = client.request(**kwargs)
        else:
            response = client.request(**kwargs)
        
        # 解析响应数据
        response_json = response.json() if response.is_success else dict()
        
        # 验证响应并返回结果
        return (
            Draft202012Validator(validate_json_schema).is_valid(response_json),
            response_json.get("data", None),
            response
        )

    async def async_request(
            self,
            client: httpx.AsyncClient = None,
            validate_json_schema: dict = {
                "properties": {
                    "code": {
                        "oneOf": [
                            {"type": "integer", "const": 200},
                            {"type": "string", "const": "200"},
                        ],
                    },
                }
            },
            access_token: str = None,
            **kwargs
    ):
        """
        发送异步 API 请求

        Args:
            client (httpx.AsyncClient, optional): 已配置的异步 HTTP 客户端
            validate_json_schema (dict, optional): 响应数据的 JSON Schema 验证规则
            access_token (str, optional): 访问令牌，默认使用客户端存储的令牌
            **kwargs: 传递给 client.request 的额外参数，包括：
                - method (str): 请求方法（GET/POST/PUT/DELETE 等）
                - url (str): 请求路径
                - params (dict): URL 查询参数
                - json (dict): 请求体 JSON 数据
                - data (dict/str): 请求体表单数据
                - files (dict): 文件上传数据

        Returns:
            tuple: (验证状态, 响应数据, 原始响应)
                - 验证状态 (bool): API 响应是否符合 JSON Schema
                - 响应数据 (dict): API 响应的 data 字段内容
                - 原始响应 (httpx.Response): API 请求的原始响应对象
        """
        # 使用提供的令牌或客户端存储的令牌
        access_token = access_token if isinstance(access_token, str) and len(access_token) else self.access_token
        kwargs.setdefault("method", "GET")  # 默认使用 GET 方法
        
        # 获取或创建参数字典
        params = kwargs.get("params", dict())
        params.setdefault("accessToken", access_token)  # 设置访问令牌参数
        kwargs["params"] = params
        
        # 如果没有提供客户端，则创建临时客户端
        if not isinstance(client, httpx.AsyncClient):
            async with self.async_client() as client:
                response = await client.request(**kwargs)
        else:
            response = await client.request(**kwargs)
        
        # 解析响应数据
        response_json = response.json() if response.is_success else dict()
        
        # 验证响应并返回结果
        return (
            Draft202012Validator(validate_json_schema).is_valid(response_json),
            response_json.get("data", None),
            response
        )