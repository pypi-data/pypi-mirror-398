#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Wisharetec SCAASP 系统管理客户端模块

该模块提供了与 Wisharetec SCAASP 系统交互的 Python 客户端，支持同步和异步操作，
包括登录状态检查、登录、令牌刷新和 API 请求发送等功能。同时支持令牌缓存机制，
可使用 diskcache 或 redis 进行令牌持久化存储。
"""

import hashlib
import json

import diskcache
import httpx
import redis
from jsonschema.validators import Draft202012Validator


class Admin:
    """
    Wisharetec SCAASP 系统管理客户端类
    
    提供与 SCAASP 系统交互的核心功能，包括同步和异步 API 调用、
    登录状态管理、令牌缓存等功能。
    
    Attributes:
        base_url (str): API 基础 URL
        username (str): 用户名
        password (str): 密码
        token (dict): 当前令牌信息
        cache_config (dict): 缓存配置信息
    """

    def __init__(
            self,
            base_url: str = "https://sq.wisharetec.com/",
            username: str = "",
            password: str = "",
            cache_config: dict = None,
    ):
        """
        初始化 Admin 客户端
        
        Args:
            base_url (str): API 基础 URL，默认 https://sq.wisharetec.com/
            username (str): 用户名，默认空字符串
            password (str): 密码，默认空字符串
            cache_config (dict): 缓存配置字典，支持以下键：
                - key: 缓存键名，默认 wisharetec_scaasp_token_{username}
                - expire: 缓存过期时间（秒），默认 180 天
                - instance: 缓存实例，支持 diskcache.Cache 或 redis.Redis 对象
        """
        # 处理基础 URL，确保不包含尾部斜杠
        self.base_url = base_url[:-1] if base_url.endswith("/") else base_url
        self.username = username
        self.password = password
        self.token: dict = dict()

        # 初始化缓存配置
        self.cache_config = cache_config if isinstance(cache_config, dict) else dict()
        # 设置缓存键名，默认包含用户名以区分不同用户
        self.cache_config.setdefault("key", f"wisharetec_scaasp_token_{self.username}")
        # 设置缓存过期时间，默认 180 天
        self.cache_config.setdefault("expire", 24 * 60 * 60 * 180)
        # 设置缓存实例，默认 None
        self.cache_config.setdefault("instance", None)

    def client(self, **kwargs):
        """
        创建同步 HTTP 客户端
        
        Args:
            **kwargs: 传递给 httpx.Client 的额外参数，会覆盖默认配置
            
        Returns:
            httpx.Client: 配置好的同步 HTTP 客户端
        """
        kwargs.setdefault("base_url", self.base_url)  # 设置基础 URL
        kwargs.setdefault("timeout", 600)  # 设置超时时间（秒）
        kwargs.setdefault("verify", False)  # 禁用 SSL 验证
        return httpx.Client(**kwargs)

    def async_client(self, **kwargs):
        """
        创建异步 HTTP 客户端
        
        Args:
            **kwargs: 传递给 httpx.AsyncClient 的额外参数，会覆盖默认配置
            
        Returns:
            httpx.AsyncClient: 配置好的异步 HTTP 客户端
        """
        kwargs.setdefault("base_url", self.base_url)  # 设置基础 URL
        kwargs.setdefault("timeout", 600)  # 设置超时时间（秒）
        kwargs.setdefault("verify", False)  # 禁用 SSL 验证
        return httpx.AsyncClient(**kwargs)

    def get_login_state(
            self,
            client: httpx.Client = None,
            token: dict = dict(),
            **kwargs
    ):
        """
        检查登录状态
        
        发送请求检查当前令牌是否有效
        
        Args:
            client (httpx.Client, optional): 同步 HTTP 客户端实例
            token (dict, optional): 令牌信息，默认使用实例的 token 属性
            **kwargs: 传递给客户端请求的额外参数
            
        Returns:
            tuple: (登录状态, 响应文本, 响应对象)
                - 登录状态 (bool): True 表示已登录，False 表示未登录
                - 响应文本 (str/dict): 响应内容
                - 响应对象 (httpx.Response): 原始响应对象
        """
        # 确定使用的令牌
        token = token if isinstance(token, dict) and len(token.keys()) else self.token

        # 设置默认请求参数
        kwargs.setdefault("method", "POST")
        kwargs.setdefault("url", "/old/serverUserAction!checkSession.action")

        # 设置请求头
        headers = kwargs.get("headers", dict())
        headers.setdefault("Token", token.get("token", ""))
        headers.setdefault("Companycode", token.get("companyCode", ""))
        kwargs["headers"] = headers

        # 发送请求
        if not isinstance(client, httpx.Client):
            with self.client() as client:
                response = client.request(**kwargs)
        else:
            response = client.request(**kwargs)

        # 处理响应
        response_text = response.text if response.is_success else dict()

        return (
            response_text.strip() == "null",
            response_text,
            response
        )

    async def async_get_login_state(
            self,
            client: httpx.AsyncClient = None,
            **kwargs
    ):
        """
        异步检查登录状态
        
        异步发送请求检查当前令牌是否有效
        
        Args:
            client (httpx.AsyncClient, optional): 异步 HTTP 客户端实例
            **kwargs: 传递给客户端请求的额外参数
            
        Returns:
            tuple: (登录状态, 响应文本, 响应对象)
                - 登录状态 (bool): True 表示已登录，False 表示未登录
                - 响应文本 (str/dict): 响应内容
                - 响应对象 (httpx.Response): 原始响应对象
        """
        # 设置默认请求参数
        kwargs.setdefault("method", "POST")
        kwargs.setdefault("url", "/old/serverUserAction!checkSession.action")

        # 设置请求头
        headers = kwargs.get("headers", dict())
        headers.setdefault("Token", self.token.get("token", ""))
        headers.setdefault("Companycode", self.token.get("companyCode", ""))
        kwargs["headers"] = headers

        # 发送请求
        if not isinstance(client, httpx.AsyncClient):
            async with self.async_client() as client:
                response = await client.request(**kwargs)
        else:
            response = await client.request(**kwargs)

        # 处理响应
        response_text = response.text if response.is_success else dict()

        return (
            response_text.strip() == "null",
            response_text,
            response
        )

    def login(
            self,
            client: httpx.Client = None,
            validate_json_schema: dict = {
                "properties": {
                    "token": {"type": "string", "minLength": 1},
                    "companyCode": {"type": "string", "minLength": 1},
                },
                "required": ["token", "companyCode"],
            },
            **kwargs
    ):
        """
        同步登录
        
        发送登录请求获取令牌
        
        Args:
            client (httpx.Client, optional): 同步 HTTP 客户端实例
            validate_json_schema (dict, optional): 响应 JSON 验证模式
            **kwargs: 传递给客户端请求的额外参数
            
        Returns:
            tuple: (登录结果, 令牌信息, 响应对象)
                - 登录结果 (bool): True 表示登录成功，False 表示登录失败
                - 令牌信息 (dict): 包含 token 和 companyCode 等信息
                - 响应对象 (httpx.Response): 原始响应对象
        """
        # 设置默认请求参数
        kwargs.setdefault("method", "POST")
        kwargs.setdefault("url", "/manage/login")

        # 设置登录数据
        data = kwargs.get("data", dict())
        data.setdefault("username", self.username)
        data.setdefault("password", hashlib.md5(self.password.encode("utf-8")).hexdigest())
        data.setdefault("mode", "PASSWORD")
        kwargs["data"] = data

        # 发送请求
        if not isinstance(client, httpx.Client):
            with self.client() as client:
                response = client.request(**kwargs)
        else:
            response = client.request(**kwargs)

        # 处理响应
        response_json = response.json() if response.is_success else dict()
        self.token = response_json.get("data", dict())

        return (
            Draft202012Validator(validate_json_schema).is_valid(response_json.get("data", dict())),
            response_json.get("data", dict()),
            response
        )

    async def async_login(
            self,
            client: httpx.AsyncClient = None,
            validate_json_schema: dict = {
                "properties": {
                    "token": {"type": "string", "minLength": 1},
                    "companyCode": {"type": "string", "minLength": 1},
                },
                "required": ["token", "companyCode"],
            },
            **kwargs
    ):
        """
        异步登录
        
        异步发送登录请求获取令牌
        
        Args:
            client (httpx.AsyncClient, optional): 异步 HTTP 客户端实例
            validate_json_schema (dict, optional): 响应 JSON 验证模式
            **kwargs: 传递给客户端请求的额外参数
            
        Returns:
            tuple: (登录结果, 令牌信息, 响应对象)
                - 登录结果 (bool): True 表示登录成功，False 表示登录失败
                - 令牌信息 (dict): 包含 token 和 companyCode 等信息
                - 响应对象 (httpx.Response): 原始响应对象
        """
        # 设置默认请求参数
        kwargs.setdefault("method", "POST")
        kwargs.setdefault("url", "/manage/login")

        # 设置登录数据
        data = kwargs.get("data", dict())
        data.setdefault("username", self.username)
        data.setdefault("password", hashlib.md5(self.password.encode("utf-8")).hexdigest())
        data.setdefault("mode", "PASSWORD")
        kwargs["data"] = data

        # 发送请求
        if not isinstance(client, httpx.AsyncClient):
            async with self.async_client() as client:
                response = await client.request(**kwargs)
        else:
            response = await client.request(**kwargs)

        # 处理响应
        response_json = response.json() if response.is_success else dict()
        self.token = response_json.get("data", dict())

        return (
            Draft202012Validator(validate_json_schema).is_valid(response_json.get("data", dict())),
            response_json.get("data", dict()),
            response
        )

    def refresh_token(
            self,
            client: httpx.Client = None
    ):
        """
        刷新令牌
        
        从缓存获取令牌或重新登录获取新令牌，并验证令牌有效性
        
        Args:
            client (httpx.Client, optional): 同步 HTTP 客户端实例
            
        Returns:
            Admin: 客户端实例本身，支持链式调用
        """
        # 获取缓存配置
        cache_key = self.cache_config.get("key", f"wisharetec_scaasp_token_{self.username}")
        cache_inst = self.cache_config.get("instance", None)
        cache_expire = self.cache_config.get("expire", 24 * 60 * 60 * 180)

        # 如果没有缓存实例或缓存实例类型不支持，则直接获取新令牌
        if not isinstance(cache_inst, (diskcache.Cache, redis.Redis, redis.StrictRedis)):
            state, token, _ = self.login(client=client)
        else:
            # 从缓存获取令牌
            if isinstance(cache_inst, diskcache.Cache):
                token = cache_inst.get(cache_key, dict())
            elif isinstance(cache_inst, (redis.Redis, redis.StrictRedis)):
                token = json.loads(cache_inst.get(cache_key, b"{}"))
            else:
                token = dict()

        # 确保令牌是字典类型
        token = token if isinstance(token, dict) else dict()

        # 验证令牌是否有效
        state, _, _ = self.get_login_state(client=client, token=token)

        # 如果令牌无效，重新登录获取新令牌
        if not state:
            state, token, _ = self.login(client=client)

        # 将有效令牌存入缓存
        if state and isinstance(cache_inst, diskcache.Cache):
            cache_inst.set(cache_key, token, expire=cache_expire)
        elif state and isinstance(cache_inst, (redis.Redis, redis.StrictRedis)):
            cache_inst.set(cache_key, json.dumps(token), ex=cache_expire)

        # 更新实例令牌
        self.token = token

        return self

    async def async_refresh_token(
            self,
            client: httpx.AsyncClient = None
    ):
        """
        异步刷新令牌
        
        异步从缓存获取令牌或重新登录获取新令牌，并验证令牌有效性
        
        Args:
            client (httpx.AsyncClient, optional): 异步 HTTP 客户端实例
            
        Returns:
            Admin: 客户端实例本身，支持链式调用
        """
        # 获取缓存配置
        cache_key = self.cache_config.get("key", f"wisharetec_scaasp_token_{self.username}")
        cache_inst = self.cache_config.get("instance", None)
        cache_expire = self.cache_config.get("expire", 24 * 60 * 60 * 180)

        # 如果没有缓存实例或缓存实例类型不支持，则直接获取新令牌
        if not isinstance(cache_inst, (diskcache.Cache, redis.Redis, redis.StrictRedis)):
            state, token, _ = await self.async_login(client=client)
        else:
            # 从缓存获取令牌
            if isinstance(cache_inst, diskcache.Cache):
                token = cache_inst.get(cache_key, dict())
            elif isinstance(cache_inst, (redis.Redis, redis.StrictRedis)):
                token = json.loads(cache_inst.get(cache_key, b"{}"))
            else:
                token = dict()

        # 确保令牌是字典类型
        token = token if isinstance(token, dict) else dict()

        # 验证令牌是否有效
        state, _, _ = await self.async_get_login_state(client=client)

        # 如果令牌无效，重新登录获取新令牌
        if not state:
            state, token, _ = await self.async_login(client=client)

        # 将有效令牌存入缓存
        if state and isinstance(cache_inst, diskcache.Cache):
            cache_inst.set(cache_key, token, expire=cache_expire)
        elif state and isinstance(cache_inst, (redis.Redis, redis.StrictRedis)):
            cache_inst.set(cache_key, json.dumps(token), ex=cache_expire)

        # 更新实例令牌
        self.token = token

        return self

    def request(
            self,
            client: httpx.Client = None,
            validate_json_schema: dict = {
                "properties": {
                    "status": {
                        "oneOf": [
                            {"type": "integer", "const": 100},
                            {"type": "string", "const": "100"},
                        ]
                    }
                },
                "required": ["status"],
            },
            token: dict = None,
            **kwargs
    ):
        """
        发送同步 API 请求
        
        发送带令牌认证的同步 API 请求，并验证响应格式
        
        Args:
            client (httpx.Client, optional): 同步 HTTP 客户端实例
            validate_json_schema (dict, optional): 响应 JSON 验证模式
            token (dict, optional): 令牌信息，默认使用实例的 token 属性
            **kwargs: 传递给客户端请求的额外参数
            
        Returns:
            tuple: (验证结果, 响应数据, 响应对象)
                - 验证结果 (bool): True 表示响应格式有效，False 表示无效
                - 响应数据 (dict): 解析后的响应 JSON 数据
                - 响应对象 (httpx.Response): 原始响应对象
        """
        # 确保令牌是字典类型
        self.token = self.token if isinstance(self.token, dict) else dict()

        # 确定使用的令牌
        token = token if isinstance(token, dict) and len(token.keys()) else self.token

        # 设置请求头
        headers = kwargs.get("headers", dict())
        headers.setdefault("Token", token.get("token", ""))
        headers.setdefault("Companycode", token.get("companyCode", ""))
        kwargs["headers"] = headers

        # 设置默认请求方法
        kwargs.setdefault("method", "POST")

        # 发送请求
        if not isinstance(client, httpx.Client):
            with self.client() as client:
                response = client.request(**kwargs)
        else:
            response = client.request(**kwargs)

        # 处理响应
        response_json = response.json() if response.is_success else dict()
        return (
            Draft202012Validator(validate_json_schema).is_valid(response_json),
            response_json,
            response
        )

    async def async_request(
            self,
            client: httpx.AsyncClient = None,
            validate_json_schema: dict = {
                "properties": {
                    "status": {
                        "oneOf": [
                            {"type": "integer", "const": 100},
                            {"type": "string", "const": "100"},
                        ]
                    }
                }
            },
            token: dict = None,
            **kwargs
    ):
        """
        发送异步 API 请求
        
        异步发送带令牌认证的 API 请求，并验证响应格式
        
        Args:
            client (httpx.AsyncClient, optional): 异步 HTTP 客户端实例
            validate_json_schema (dict, optional): 响应 JSON 验证模式
            token (dict, optional): 令牌信息，默认使用实例的 token 属性
            **kwargs: 传递给客户端请求的额外参数
            
        Returns:
            tuple: (验证结果, 响应数据, 响应对象)
                - 验证结果 (bool): True 表示响应格式有效，False 表示无效
                - 响应数据 (dict): 解析后的响应 JSON 数据
                - 响应对象 (httpx.Response): 原始响应对象
        """
        # 确保令牌是字典类型
        self.token = self.token if isinstance(self.token, dict) else dict()

        # 确定使用的令牌
        token = token if isinstance(token, dict) and len(token.keys()) else self.token

        # 设置请求头
        headers = kwargs.get("headers", dict())
        headers.setdefault("Token", token.get("token", ""))
        headers.setdefault("Companycode", token.get("companyCode", ""))
        kwargs["headers"] = headers

        # 设置默认请求方法
        kwargs.setdefault("method", "POST")

        # 发送请求
        if not isinstance(client, httpx.AsyncClient):
            async with self.async_client() as client:
                response = await client.request(**kwargs)
        else:
            response = await client.request(**kwargs)

        # 处理响应
        response_json = response.json() if response.is_success else dict()

        return (
            Draft202012Validator(validate_json_schema).is_valid(response_json),
            response_json,
            response
        )
