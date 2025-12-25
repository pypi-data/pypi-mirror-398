#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
天津博瑞皓科设备通信模块

该模块提供了与天津博瑞皓科设备通信的功能，主要用于发送通知消息，
支持同步和异步两种通信方式。基于httpx库实现，支持灵活的参数配置和响应验证。

技术依赖:
- httpx: 用于HTTP请求（支持同步和异步）
- jsonschema: 用于验证API响应的JSON结构
"""
import httpx
from jsonschema.validators import Draft202012Validator


class Speaker:
    """
    天津博瑞皓科设备通信客户端类
    
    该类用于创建和管理与天津博瑞皓科设备通信的HTTP客户端，
    支持同步和异步两种请求方式，提供统一的客户端配置接口。
    """

    def __init__(
            self,
            base_url: str = "https://speaker.17laimai.cn",
            token: str = "",
            id: str = "",
            version: str = "1"
    ):
        """
        初始化Speaker客户端
        
        Args:
            base_url (str, optional): API基础URL
                默认值为"https://speaker.17laimai.cn"
            token (str, optional): 认证令牌
                用于API访问权限验证，默认值为空字符串
            id (str, optional): 设备或用户ID
                用于标识发送者，默认值为空字符串
            version (str, optional): API版本号
                默认值为"1"
        """
        # 处理基础URL，确保不以斜杠结尾，避免后续拼接时出现双斜杠
        self.base_url = base_url[:-1] if base_url.endswith("/") else base_url
        self.token = token  # 存储认证令牌
        self.id = id  # 存储设备/用户ID
        self.version = version  # 存储API版本号

    def client(self, **kwargs):
        """
        创建并返回同步HTTP客户端
        
        Args:
            **kwargs: 传递给httpx.Client的额外参数
                可覆盖默认配置（base_url, timeout等）
        
        Returns:
            httpx.Client: 配置好的同步HTTP客户端实例
        
        默认配置:
            - base_url: 使用初始化时设置的self.base_url
            - timeout: 120秒（2分钟），处理潜在的慢响应
        """
        # 设置默认基础URL，确保请求使用正确的API地址
        kwargs.setdefault("base_url", self.base_url)
        # 设置默认超时时间为120秒，避免长时间无响应导致程序挂起
        kwargs.setdefault("timeout", 120)
        # 创建并返回配置好的同步HTTP客户端
        return httpx.Client(**kwargs)

    def async_client(self, **kwargs):
        """
        创建并返回异步HTTP客户端
        
        Args:
            **kwargs: 传递给httpx.AsyncClient的额外参数
                可覆盖默认配置（base_url, timeout等）
        
        Returns:
            httpx.AsyncClient: 配置好的异步HTTP客户端实例
        
        默认配置:
            - base_url: 使用初始化时设置的self.base_url
            - timeout: 120秒（2分钟），处理潜在的慢响应
        """
        # 设置默认基础URL，确保请求使用正确的API地址
        kwargs.setdefault("base_url", self.base_url)
        # 设置默认超时时间为120秒，避免长时间无响应导致程序挂起
        kwargs.setdefault("timeout", 120)
        # 创建并返回配置好的异步HTTP客户端
        return httpx.AsyncClient(**kwargs)

    def notify(
            self,
            client: httpx.Client = None,
            validate_json_schema: dict = {
                "type": "object",
                "properties": {
                    "errcode": {
                        "oneOf": [
                            {"type": "integer", "const": 0},
                            {"type": "string", "const": "0"},
                        ]
                    }
                },
                "required": ["errcode"]
            },
            message: str = "",
            **kwargs
    ):
        """
        同步发送通知消息
        
        该方法通过同步HTTP客户端向设备发送通知消息，
        支持自定义请求参数和响应验证。
        
        Args:
            client (httpx.Client, optional): 同步HTTP客户端实例
                如果不提供，将自动创建一个新的客户端
            validate_json_schema (dict, optional): JSON Schema验证规则
                用于验证API响应的结构是否符合预期
                默认验证响应中包含"errcode"字段且值为0
            message (str, optional): 要发送的通知消息内容
                默认值为空字符串
            **kwargs: 额外的请求参数，将直接传递给client.request方法
                可覆盖默认的method、url、params等参数
        
        Returns:
            tuple: 返回三元组 (is_valid, response_json, response)
                - is_valid: JSON Schema验证结果（布尔值）
                - response_json: API返回的JSON响应数据
                - response: httpx.Response对象
        """
        # 设置默认请求方法为POST，符合发送通知的语义（提交数据）
        kwargs.setdefault("method", "POST")
        # 设置默认请求URL，指向通知接口
        kwargs.setdefault("url", "/notify.php")
        
        # 获取或创建请求参数字典，避免None值导致的类型错误
        data = kwargs.get("data", dict())
        # 添加必要的请求参数
        data.setdefault("token", self.token)  # 添加认证令牌
        data.setdefault("id", self.id)  # 添加设备/用户ID
        data.setdefault("version", self.version)  # 添加API版本号
        data.setdefault("message", message)  # 添加通知消息内容
        # 将更新后的参数字典放回kwargs
        kwargs["data"] = data
        
        # 客户端处理：如果未提供客户端，则创建新客户端并自动关闭
        if not isinstance(client, httpx.Client):
            # 使用with上下文管理器确保客户端在使用后正确关闭
            with self.client() as client:
                response = client.request(**kwargs)
        else:
            # 如果提供了客户端，则直接使用（由调用方负责关闭）
            response = client.request(**kwargs)
        
        # 解析响应，如果请求成功则解析JSON，否则返回空字典
        response_json = response.json() if response.is_success else dict()
        
        # 返回验证结果、响应数据和原始响应对象
        return Draft202012Validator(validate_json_schema).is_valid(response_json), response_json, response

    async def async_notify(
            self,
            client: httpx.AsyncClient = None,
            multiple_return_values: bool = False,
            validate_json_schema: dict = {
                "type": "object",
                "properties": {
                    "errcode": {
                        "oneOf": [
                            {"type": "integer", "const": 0},
                            {"type": "string", "const": "0"},
                        ]
                    }
                },
                "required": ["errcode"]
            },
            message: str = "", **kwargs):
        """
        异步发送通知消息
        
        该方法通过异步HTTP客户端向设备发送通知消息，
        支持自定义请求参数和响应验证，适用于高并发场景。
        
        Args:
            client (httpx.AsyncClient, optional): 异步HTTP客户端实例
                如果不提供，将自动创建一个新的客户端
            multiple_return_values (bool, optional): 是否返回多个值
                默认值为False，保留此参数以保持API兼容性
            validate_json_schema (dict, optional): JSON Schema验证规则
                用于验证API响应的结构是否符合预期
                默认验证响应中包含"errcode"字段且值为0
            message (str, optional): 要发送的通知消息内容
                默认值为空字符串
            **kwargs: 额外的请求参数，将直接传递给client.request方法
                可覆盖默认的method、url、params等参数
        
        Returns:
            tuple: 返回三元组 (is_valid, response_json, response)
                - is_valid: JSON Schema验证结果（布尔值）
                - response_json: API返回的JSON响应数据
                - response: httpx.Response对象
        """
        # 设置默认请求方法为POST，符合发送通知的语义（提交数据）
        kwargs.setdefault("method", "POST")
        # 设置默认请求URL，指向通知接口
        kwargs.setdefault("url", "/notify.php")
        
        # 获取或创建请求参数字典，避免None值导致的类型错误
        data = kwargs.get("data", dict())
        # 添加必要的请求参数
        data.setdefault("token", self.token)  # 添加认证令牌
        data.setdefault("id", self.id)  # 添加设备/用户ID
        data.setdefault("version", self.version)  # 添加API版本号
        data.setdefault("message", message)  # 添加通知消息内容
        # 将更新后的参数字典放回kwargs
        kwargs["data"] = data
        
        # 客户端处理：如果未提供客户端，则创建新客户端并自动关闭
        if not isinstance(client, httpx.AsyncClient):
            # 使用async with上下文管理器确保异步客户端在使用后正确关闭
            async with self.async_client() as client:
                response = await client.request(**kwargs)
        else:
            # 如果提供了客户端，则直接使用（由调用方负责关闭）
            response = await client.request(**kwargs)
        
        # 解析响应，如果请求成功则解析JSON，否则返回空字典
        response_json = response.json() if response.is_success else dict()
        
        # 返回验证结果、响应数据和原始响应对象
        return Draft202012Validator(validate_json_schema).is_valid(response_json), response_json, response