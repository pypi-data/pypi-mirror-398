#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Wisharetec 善数系统管理客户端模块

该模块提供了与善数系统（Saas）交互的Python客户端，支持同步和异步操作，
包括登录、令牌管理、组织树获取等功能。同时支持令牌缓存机制，
可使用diskcache或redis进行令牌持久化存储。
"""

import hashlib
from typing import Union

import diskcache
import httpx
import redis
from jsonschema.validators import Draft202012Validator


class Admin:
    """
    Wisharetec 善数系统管理客户端类
    
    提供与善数系统交互的核心功能，包括同步和异步API调用、
    登录状态管理、令牌缓存等功能。
    
    Attributes:
        base_url (str): API基础URL
        account (str): 账号
        password (str): 密码
        token (str): 当前认证令牌
        cache_config (dict): 缓存配置信息
    """

    def __init__(
            self,
            base_url: str = "https://saas.wisharetec.com/",
            account: str = "",
            password: str = "",
            cache_config: dict = None,
    ):
        """
        初始化善数系统管理客户端
        
        Args:
            base_url (str): API基础URL，默认https://saas.wisharetec.com/
            account (str): 账号，默认空字符串
            password (str): 密码，默认空字符串
            cache_config (dict): 缓存配置字典，支持以下键：
                - key: 缓存键名，默认wisharetec_shanshu_admin_token_{account}
                - expire: 缓存过期时间（秒），默认180天
                - instance: 缓存实例，支持diskcache.Cache或redis.Redis对象
        """
        # 处理基础URL，确保不包含尾部斜杠
        self.base_url = base_url[:-1] if isinstance(base_url, str) and base_url.endswith("/") else base_url
        self.account = account
        self.password = password
        self.token: str = ""

        # 初始化缓存配置
        self.cache_config = cache_config if isinstance(cache_config, dict) else dict()
        # 设置缓存键名，默认包含账号以区分不同用户
        self.cache_config.setdefault("key", f"wisharetec_shanshu_admin_token_{self.account}")
        # 设置缓存过期时间，默认180天
        self.cache_config.setdefault("expire", 24 * 60 * 60 * 180)
        # 设置缓存实例，默认None
        self.cache_config.setdefault("instance", None)

    def client(self, **kwargs):
        """
        创建同步HTTP客户端
        
        Args:
            **kwargs: 传递给httpx.Client的额外参数，会覆盖默认配置
            
        Returns:
            httpx.Client: 配置好的同步HTTP客户端
        """
        kwargs.setdefault("base_url", self.base_url)  # 设置基础URL
        kwargs.setdefault("timeout", 600)  # 设置超时时间（秒）
        kwargs.setdefault("verify", False)  # 禁用SSL验证
        return httpx.Client(**kwargs)

    def async_client(self, **kwargs):
        """
        创建异步HTTP客户端
        
        Args:
            **kwargs: 传递给httpx.AsyncClient的额外参数，会覆盖默认配置
            
        Returns:
            httpx.AsyncClient: 配置好的异步HTTP客户端
        """
        kwargs.setdefault("base_url", self.base_url)  # 设置基础URL
        kwargs.setdefault("timeout", 600)  # 设置超时时间（秒）
        kwargs.setdefault("verify", False)  # 禁用SSL验证
        return httpx.AsyncClient(**kwargs)

    def manage_tree(
            self,
            client: httpx.Client = None,
            validate_json_schema: dict = {
                "type": "array",
                "minItems": 1,
            },
            token: str = "",
            **kwargs
    ):
        """
        获取组织管理树
        
        Args:
            client (httpx.Client, optional): 同步HTTP客户端实例
            validate_json_schema (dict, optional): 响应JSON验证模式
            token (str, optional): 认证令牌，默认使用实例的token属性
            **kwargs: 传递给客户端请求的额外参数
            
        Returns:
            tuple: (验证结果, 响应数据, 响应对象)
                - 验证结果 (bool): True表示响应格式有效，False表示无效
                - 响应数据 (dict): 解析后的响应JSON数据
                - 响应对象 (httpx.Response): 原始响应对象
        """
        # 确保实例令牌有效性
        self.token = self.token if isinstance(self.token, str) and len(self.token) else ""
        # 确定使用的令牌
        token = token if isinstance(token, str) and len(token) else self.token

        # 设置默认请求参数
        kwargs.setdefault("method", "GET")
        kwargs.setdefault("url", "/api/space/space/manageTree")

        # 设置请求头
        headers = kwargs.get("headers", dict())
        headers.setdefault("client", "co-pc")  # 客户端类型标识
        headers.setdefault("authorization", token)  # 认证令牌
        kwargs["headers"] = headers

        # 设置默认JSON数据
        kwargs.setdefault("json", dict())

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

    async def async_manage_tree(
            self,
            client: httpx.AsyncClient = None,
            validate_json_schema: dict = {
                "type": "array",
                "minItems": 1,
            },
            token: str = "",
            **kwargs
    ):
        """
        异步获取组织管理树
        
        Args:
            client (httpx.AsyncClient, optional): 异步HTTP客户端实例
            validate_json_schema (dict, optional): 响应JSON验证模式
            token (str, optional): 认证令牌，默认使用实例的token属性
            **kwargs: 传递给客户端请求的额外参数
            
        Returns:
            tuple: (验证结果, 响应数据, 响应对象)
                - 验证结果 (bool): True表示响应格式有效，False表示无效
                - 响应数据 (dict): 解析后的响应JSON数据
                - 响应对象 (httpx.Response): 原始响应对象
        """
        # 确保实例令牌有效性
        self.token = self.token if isinstance(self.token, str) and len(self.token) else ""
        # 确定使用的令牌
        token = token if isinstance(token, str) and len(token) else self.token

        # 设置默认请求参数
        kwargs.setdefault("method", "GET")
        kwargs.setdefault("url", "/api/space/space/manageTree")

        # 设置请求头
        headers = kwargs.get("headers", dict())
        headers.setdefault("client", "co-pc")  # 客户端类型标识
        headers.setdefault("authorization", token)  # 认证令牌
        kwargs["headers"] = headers

        # 设置默认JSON数据
        kwargs.setdefault("json", dict())

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

    def login(
            self,
            client: httpx.Client = None,
            validate_json_schema: dict = {
                "properties": {
                    # "tenantSimpleInfoVList": {"type": "array", "minItems": 1},
                    "userLoginV": {
                        "type": "object",
                        "properties": {
                            "userInfoV": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string", "minLength": 1}
                                },
                                "required": ["id"]
                            },
                        },
                        "required": ["userInfoV"]
                    }
                },
                "required": ["userLoginV"],
            },
            **kwargs
    ):
        """
        同步登录
        
        发送登录请求获取认证令牌，令牌会从响应头的authorization字段中提取
        
        Args:
            client (httpx.Client, optional): 同步HTTP客户端实例
            validate_json_schema (dict, optional): 响应JSON验证模式
            **kwargs: 传递给客户端请求的额外参数
            
        Returns:
            tuple: (登录结果, 令牌信息, 响应对象)
                - 登录结果 (bool): True表示登录成功，False表示登录失败
                - 令牌信息 (str): 认证令牌
                - 响应对象 (httpx.Response): 原始响应对象
        """
        # 设置默认请求参数
        kwargs.setdefault("method", "POST")
        kwargs.setdefault("url", "/api/user/loginInteractive")

        # 设置登录数据
        json_data = kwargs.get("json", dict())
        json_data.setdefault("account", self.account)
        json_data.setdefault("password", hashlib.md5(self.password.encode("utf-8")).hexdigest())
        kwargs["json"] = json_data

        # 设置请求头
        headers = kwargs.get("headers", dict())
        headers.setdefault("client", "co-pc")  # 客户端类型标识
        kwargs["headers"] = headers

        # 发送请求
        if not isinstance(client, httpx.Client):
            with self.client() as client:
                response = client.request(**kwargs)
        else:
            response = client.request(**kwargs)

        # 处理响应
        response_json = response.json() if response.is_success else dict()

        # 从响应头获取令牌
        self.token = response.headers.get("authorization", "")
        return (
            Draft202012Validator(validate_json_schema).is_valid(response_json),
            self.token,
            response
        )

    async def async_login(
            self,
            client: httpx.AsyncClient = None,
            validate_json_schema: dict = {
                "properties": {
                    # "tenantSimpleInfoVList": {"type": "array", "minItems": 1},
                    "userLoginV": {
                        "type": "object",
                        "properties": {
                            "userInfoV": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string", "minLength": 1}
                                },
                                "required": ["id"]
                            },
                        },
                        "required": ["userInfoV"]
                    }
                },
                "required": ["userLoginV"],
            },
            **kwargs
    ):
        """
        异步登录
        
        异步发送登录请求获取认证令牌，令牌会从响应头的authorization字段中提取
        
        Args:
            client (httpx.AsyncClient, optional): 异步HTTP客户端实例
            validate_json_schema (dict, optional): 响应JSON验证模式
            **kwargs: 传递给客户端请求的额外参数
            
        Returns:
            tuple: (登录结果, 令牌信息, 响应对象)
                - 登录结果 (bool): True表示登录成功，False表示登录失败
                - 令牌信息 (str): 认证令牌
                - 响应对象 (httpx.Response): 原始响应对象
        """
        # 设置默认请求参数
        kwargs.setdefault("method", "POST")
        kwargs.setdefault("url", "/api/user/loginInteractive")

        # 设置登录数据
        json_data = kwargs.get("json", dict())
        json_data.setdefault("account", self.account)
        json_data.setdefault("password", hashlib.md5(self.password.encode("utf-8")).hexdigest())
        kwargs["json"] = json_data

        # 设置请求头
        headers = kwargs.get("headers", dict())
        headers.setdefault("client", "co-pc")  # 客户端类型标识
        kwargs["headers"] = headers

        # 发送请求
        if not isinstance(client, httpx.AsyncClient):
            async with self.async_client() as client:
                response = await client.request(**kwargs)
        else:
            response = await client.request(**kwargs)

        # 处理响应
        response_json = response.json() if response.is_success else dict()

        # 从响应头获取令牌
        self.token = response.headers.get("authorization", "")

        return (
            Draft202012Validator(validate_json_schema).is_valid(response_json),
            self.token,
            response
        )

    def refresh_token(self, client: httpx.Client = None):
        """
        刷新令牌
        
        从缓存获取令牌或重新登录获取新令牌，并验证令牌有效性
        
        Args:
            client (httpx.Client, optional): 同步HTTP客户端实例
            
        Returns:
            Admin: 客户端实例本身，支持链式调用
        """
        # 获取缓存配置
        cache_key = self.cache_config.get("key", f"wisharetec_shanshu_admin_token_{self.account}")
        cache_inst = self.cache_config.get("instance", None)
        cache_expire = self.cache_config.get("expire", 7100)

        # 如果没有缓存实例或缓存实例类型不支持，则直接获取新令牌
        if not isinstance(cache_inst, (diskcache.Cache, redis.Redis, redis.StrictRedis)):
            state, token, _ = self.login(client=client)
        else:
            # 从缓存获取访问令牌
            token = cache_inst.get(cache_key, "")

        # 验证访问令牌是否有效（通过调用manage_tree接口）
        state, _, _ = self.manage_tree(client=client, token=token)
        if not state:
            # 访问令牌无效，重新获取
            state, token, _ = self.login(client=client)

        # 将访问令牌存入缓存
        if state and isinstance(cache_inst, diskcache.Cache):
            cache_inst.set(cache_key, token, expire=cache_expire)
        if state and isinstance(cache_inst, (redis.Redis, redis.StrictRedis)):
            cache_inst.set(cache_key, token, ex=cache_expire)

        # 更新客户端存储的令牌
        self.token = token
        return self

    async def async_refresh_token(self, client: httpx.AsyncClient = None):
        """
        异步刷新令牌
        
        异步从缓存获取令牌或重新登录获取新令牌，并验证令牌有效性
        
        Args:
            client (httpx.AsyncClient, optional): 异步HTTP客户端实例
            
        Returns:
            Admin: 客户端实例本身，支持链式调用
        """
        # 获取缓存配置
        cache_key = self.cache_config.get("key", f"wisharetec_shanshu_admin_token_{self.account}")
        cache_inst = self.cache_config.get("instance", None)
        cache_expire = self.cache_config.get("expire", 7100)

        # 如果没有缓存实例或缓存实例类型不支持，则直接获取新令牌
        if not isinstance(cache_inst, (diskcache.Cache, redis.Redis, redis.StrictRedis)):
            state, token, _ = await self.async_login(client=client)
        else:
            # 从缓存获取访问令牌
            token = cache_inst.get(cache_key, "")

        # 验证访问令牌是否有效（通过调用async_manage_tree接口）
        state, _, _ = await self.async_manage_tree(client=client, token=token)
        if not state:
            # 访问令牌无效，重新获取
            state, token, _ = await self.async_login(client=client)

        # 将访问令牌存入缓存
        if state and isinstance(cache_inst, diskcache.Cache):
            cache_inst.set(cache_key, token, expire=cache_expire)
        if state and isinstance(cache_inst, (redis.Redis, redis.StrictRedis)):
            cache_inst.set(cache_key, token, ex=cache_expire)

        # 更新客户端存储的令牌
        self.token = token
        return self

    def request(
            self,
            client: httpx.Client = None,
            validate_json_schema: dict = dict(),
            token: str = "",
            **kwargs
    ):
        """
        发送同步API请求
        
        发送带认证令牌的同步API请求，并验证响应格式
        
        Args:
            client (httpx.Client, optional): 同步HTTP客户端实例
            validate_json_schema (dict, optional): 响应JSON验证模式
            token (str, optional): 认证令牌，默认使用实例的token属性
            **kwargs: 传递给客户端请求的额外参数
            
        Returns:
            tuple: (验证结果, 响应数据, 响应对象)
                - 验证结果 (bool): True表示响应格式有效，False表示无效
                - 响应数据 (dict): 解析后的响应JSON数据
                - 响应对象 (httpx.Response): 原始响应对象
        """
        # 确保实例令牌有效性
        self.token = self.token if isinstance(self.token, str) and len(self.token) else ""
        # 确定使用的令牌
        token = token if isinstance(token, str) and len(token) else self.token

        # 设置默认请求参数
        kwargs.setdefault("method", "GET")

        # 设置请求头
        headers = kwargs.get("headers", dict())
        headers.setdefault("client", "co-pc")  # 客户端类型标识
        headers.setdefault("authorization", token)  # 认证令牌
        kwargs["headers"] = headers

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
            validate_json_schema: dict = dict(),
            token: str = "",
            **kwargs
    ):
        """
        发送异步API请求
        
        异步发送带认证令牌的API请求，并验证响应格式
        
        Args:
            client (httpx.AsyncClient, optional): 异步HTTP客户端实例
            validate_json_schema (dict, optional): 响应JSON验证模式
            token (str, optional): 认证令牌，默认使用实例的token属性
            **kwargs: 传递给客户端请求的额外参数
            
        Returns:
            tuple: (验证结果, 响应数据, 响应对象)
                - 验证结果 (bool): True表示响应格式有效，False表示无效
                - 响应数据 (dict): 解析后的响应JSON数据
                - 响应对象 (httpx.Response): 原始响应对象
        """
        # 确保实例令牌有效性
        self.token = self.token if isinstance(self.token, str) and len(self.token) else ""
        # 确定使用的令牌
        token = token if isinstance(token, str) and len(token) else self.token

        # 设置默认请求参数
        kwargs.setdefault("method", "GET")

        # 设置请求头
        headers = kwargs.get("headers", dict())
        headers.setdefault("client", "co-pc")  # 客户端类型标识
        headers.setdefault("authorization", token)  # 认证令牌
        kwargs["headers"] = headers

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
