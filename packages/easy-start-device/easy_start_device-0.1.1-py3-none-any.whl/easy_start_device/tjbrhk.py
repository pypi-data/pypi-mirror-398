#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import httpx
from jsonschema.validators import Draft202012Validator


class Speaker:
    """
    天津博瑞皓科的客户端类，用于发送通知消息。
    
    该类提供了同步和异步两种方式与天津博瑞皓科进行交互，支持自定义配置和参数。
    """

    def __init__(
            self,
            base_url: str = "https://speaker.17laimai.cn",
            token: str = "",
            id: str = "",
            version: str = "1"
    ):
        """
        初始化Speaker客户端。
        
        Args:
            base_url (str, optional): API基础URL，默认为"https://speaker.17laimai.cn"。
            token (str, optional): 认证令牌，用于API访问权限验证。默认值为空字符串。
            id (str, optional): 设备或用户ID，用于标识发送者。默认值为空字符串。
            version (str, optional): API版本号，默认为"1"。
        """
        # 确保base_url不以斜杠结尾
        self.base_url = base_url[:-1] if base_url.endswith("/") else base_url
        self.token = token  # 存储认证令牌
        self.id = id  # 存储设备/用户ID
        self.version = version  # 存储API版本号

    def client(self, **kwargs):
        """
        创建并返回一个同步HTTP客户端。
        
        Args:
            **kwargs: 传递给httpx.Client的额外参数。
            
        Returns:
            httpx.Client: 配置好的同步HTTP客户端实例。
        """
        # 设置默认的base_url
        kwargs.setdefault("base_url", self.base_url)
        # 设置默认超时时间为120秒
        kwargs.setdefault("timeout", 120)
        # 创建并返回客户端
        return httpx.Client(**kwargs)

    def async_client(self, **kwargs):
        """
        创建并返回一个异步HTTP客户端。
        
        Args:
            **kwargs: 传递给httpx.AsyncClient的额外参数。
            
        Returns:
            httpx.AsyncClient: 配置好的异步HTTP客户端实例。
        """
        # 设置默认的base_url
        kwargs.setdefault("base_url", self.base_url)
        # 设置默认超时时间为120秒
        kwargs.setdefault("timeout", 120)
        # 创建并返回异步客户端
        return httpx.AsyncClient(**kwargs)

    def notify(
            self,
            client: httpx.Client = None,
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
            message: str = "",
            **kwargs
    ):
        """
        发送同步通知消息。
        
        Args:
            client (httpx.Client): HTTP客户端实例，如果为None则自动创建。
            multiple_return_values (bool, optional): 是否返回多个值。默认值为False。
            validate_json_schema (dict, optional): 用于验证JSON响应的JSON模式。默认值为{"type": "object", "properties": {"errcode": {"oneOf": [{"type": "integer", "const": 0}, {"type": "string", "const": "0"}]}}, "required": ["errcode"]}。
            message (str, optional): 要发送的通知消息内容。默认值为空字符串。
            **kwargs: 传递给client.request的额外参数。
            
        Returns:
            tuple: 返回一个元组，包含三个元素：
                - bool: 操作是否成功（根据返回的errcode判断）
                - dict: API返回的JSON响应数据
                - httpx.Response: 原始响应对象
        """

        # 设置默认请求方法为POST
        kwargs.setdefault("method", "POST")
        # 设置默认请求URL为"/notify.php"
        kwargs.setdefault("url", "/notify.php")
        # 获取数据字典
        data = kwargs.get("data", dict())
        # 设置必要的请求参数
        data.setdefault("token", self.token)
        data.setdefault("id", self.id)
        data.setdefault("version", self.version)
        data.setdefault("message", message)
        # 更新kwargs中的数据
        kwargs["data"] = data
        # 如果提供的客户端不是httpx.Client实例，则创建新客户端
        if not isinstance(client, httpx.Client):
            with self.client() as client:
                response = client.request(**kwargs)
        else:
            # 使用提供的客户端发送请求
            response = client.request(**kwargs)

        # 解析响应，如果请求成功则解析JSON，否则返回空字典
        response_json = response.json() if response.is_success else dict()
        # 返回操作结果、响应JSON和原始响应
        if multiple_return_values:
            return Draft202012Validator(validate_json_schema).is_valid(response_json), response_json, response
        return Draft202012Validator(validate_json_schema).is_valid(response_json)

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
        发送异步通知消息。

        Args:
            client (httpx.AsyncClient): 异步HTTP客户端实例，如果为None则自动创建。
            message (str, optional): 要发送的通知消息内容。默认值为空字符串。
            multiple_return_values (bool, optional): 是否返回多个值。默认值为False。
            validate_json_schema (dict, optional): 用于验证JSON响应的JSON模式。默认值为{"type": "object", "properties": {"errcode": {"oneOf": [{"type": "integer", "const": 0}, {"type": "string", "const": "0"}]}}, "required": ["errcode"]}。
            **kwargs: 传递给client.request的额外参数。

        Returns:
            tuple: 返回一个元组，包含三个元素：
                - bool: 操作是否成功（根据返回的errcode判断）
                - dict: API返回的JSON响应数据
                - httpx.Response: 原始响应对象
        """
        # 设置默认请求方法为POST
        kwargs.setdefault("method", "POST")
        # 设置默认请求URL为"/notify.php"
        kwargs.setdefault("url", "/notify.php")

        # 获取数据字典
        data = kwargs.get("data", dict())
        # 设置必要的请求参数
        data.setdefault("token", self.token)
        data.setdefault("id", self.id)
        data.setdefault("version", self.version)
        data.setdefault("message", message)
        # 更新kwargs中的数据
        kwargs["data"] = data
        # 如果提供的客户端不是httpx.AsyncClient实例，则创建新客户端
        if not isinstance(client, httpx.AsyncClient):
            async with self.async_client() as client:
                response = await client.request(**kwargs)
        else:
            # 使用提供的客户端发送请求
            response = await client.request(**kwargs)

        # 解析响应，如果请求成功则解析JSON，否则返回空字典
        response_json = response.json() if response.is_success else dict()
        # 返回操作结果、响应JSON和原始响应
        if multiple_return_values:
            return Draft202012Validator(validate_json_schema).is_valid(response_json), response_json, response
        return Draft202012Validator(validate_json_schema).is_valid(response_json)
