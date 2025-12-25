#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
畅捷通中科华博HTTP请求模块

该模块提供了与畅捷通中科华博API交互的HTTP请求功能，
主要用于获取实际支付项目列表，支持同步和异步两种请求方式。
基于httpx库实现，支持灵活的参数配置和响应验证。

技术依赖:
- httpx: 用于HTTP请求（支持同步和异步）
- jsonschema: 用于验证API响应的JSON结构
"""
import httpx
from jsonschema.validators import Draft202012Validator


class Api:
    """
    畅捷通中科华博API客户端类

    该类用于创建和管理与畅捷通中科华博API交互的HTTP客户端，
    支持同步和异步两种请求方式，提供统一的客户端配置接口。
    """

    def __init__(self, base_url: str = ""):
        """
        初始化API客户端

        Args:
            base_url (str, optional): API基础URL
                如果URL以"/"结尾，会自动移除末尾的斜杠
                默认值为空字符串

        示例:
            api = Api("https://example.com/api/")
            # self.base_url 将被处理为 "https://example.com/api"
        """
        # 处理基础URL，确保不以斜杠结尾，避免后续拼接时出现双斜杠
        self.base_url = base_url[:-1] if base_url.endswith("/") else base_url

    def client(self, **kwargs):
        """
        创建并返回同步HTTP客户端

        Args:
            **kwargs: 传递给httpx.Client的额外参数
                可覆盖默认配置（base_url, timeout, verify等）

        Returns:
            httpx.Client: 配置好的同步HTTP客户端实例

        默认配置:
            - base_url: 使用初始化时设置的self.base_url
            - timeout: 120秒（2分钟），处理潜在的慢响应
            - verify: False（禁用SSL证书验证，适用于开发环境或自签名证书）
        """
        # 设置默认基础URL，确保请求使用正确的API地址
        kwargs.setdefault("base_url", self.base_url)
        # 设置默认超时时间为120秒，避免长时间无响应导致程序挂起
        kwargs.setdefault("timeout", 120)
        # 禁用SSL证书验证，允许与使用自签名证书的服务器通信
        kwargs.setdefault("verify", False)
        # 创建并返回配置好的同步HTTP客户端
        return httpx.Client(**kwargs)

    def async_client(self, **kwargs):
        """
        创建并返回异步HTTP客户端

        Args:
            **kwargs: 传递给httpx.AsyncClient的额外参数
                可覆盖默认配置（base_url, timeout, verify等）

        Returns:
            httpx.AsyncClient: 配置好的异步HTTP客户端实例

        默认配置:
            - base_url: 使用初始化时设置的self.base_url
            - timeout: 120秒（2分钟），处理潜在的慢响应
            - verify: False（禁用SSL证书验证，适用于开发环境或自签名证书）
        """
        # 设置默认基础URL，确保请求使用正确的API地址
        kwargs.setdefault("base_url", self.base_url)
        # 设置默认超时时间为120秒，避免长时间无响应导致程序挂起
        kwargs.setdefault("timeout", 120)
        # 禁用SSL证书验证，允许与使用自签名证书的服务器通信
        kwargs.setdefault("verify", False)
        # 创建并返回配置好的异步HTTP客户端
        return httpx.AsyncClient(**kwargs)

    def get_actual_payment_item_list(
            self,
            client: httpx.Client = None,
            validate_json_schema: dict = {
                "properties": {
                    "result": {
                        "oneOf": [
                            {"type": "boolean", "const": True},
                            {"type": "string", "const": "True"},
                            {"type": "string", "const": "true"},
                        ]
                    }
                }
            },
            **kwargs
    ):
        """
        同步获取实际支付项目列表

        该函数通过同步HTTP客户端向指定的API端点发送请求，
        获取实际支付项目列表数据，支持灵活配置请求参数。

        Args:
            client (httpx.Client, optional): 同步HTTP客户端实例
                如果不提供，将自动创建一个新的客户端
            validate_json_schema (dict, optional): JSON Schema验证规则
                用于验证API响应的结构是否符合预期
                默认验证响应中包含"result"字段且值为True
            **kwargs: 额外的请求参数，将直接传递给client.request方法
                可覆盖默认的method、url、params等参数

        Returns:
            tuple: 返回三元组 (is_valid, payment_list, response)
                - is_valid: JSON Schema验证结果（布尔值）
                - payment_list: 实际支付项目列表，如果请求失败则返回空列表
                - response: httpx.Response对象

        注意:
            - 默认请求方法为GET
            - 默认请求参数包含 {"json": "Getpayment"}，用于指定API方法
            - 响应JSON中实际支付项目列表存储在"Getpayment"字段中
        """
        # 设置默认请求方法为GET，符合HTTP GET方法的语义（获取资源）
        kwargs.setdefault("method", "GET")
        # 设置默认API端点URL，指向获取支付项目列表的接口
        kwargs.setdefault("url", "/estate/WebSerVice/jsonPostInterfaceNew.ashx")
        # 获取或创建请求参数字典，避免None值导致的类型错误
        params = kwargs.get("params", dict())
        # 添加API方法参数，指定调用Getpayment接口获取支付项目数据
        params.setdefault("json", "Getpayment")
        # 将更新后的参数字典放回kwargs
        kwargs["params"] = params

        # 客户端处理：如果未提供客户端，则创建新客户端并自动关闭
        if not isinstance(client, httpx.Client):
            # 使用with上下文管理器确保客户端在使用后正确关闭
            with self.client() as client:
                response = client.request(**kwargs)
        else:
            # 如果提供了客户端，则直接使用（由调用方负责关闭）
            response = client.request(**kwargs)

        # 响应处理：解析响应JSON（如果请求成功且有响应文本）
        response_json = response.json() if response.is_success else dict()

        # 验证响应JSON结构并返回结果
        return (
            Draft202012Validator(validate_json_schema).is_valid(response_json),
            response_json.get("Getpayment", list()),
            response
        )

    async def async_get_actual_payment_item_list(
            self,
            client: httpx.AsyncClient = None,
            validate_json_schema: dict = {
                "properties": {
                    "result": {
                        "oneOf": [
                            {"type": "boolean", "const": True},
                            {"type": "string", "const": "True"},
                            {"type": "string", "const": "true"},
                        ]
                    }
                }
            },
            **kwargs
    ):
        """
        异步获取实际支付项目列表

        该函数通过异步HTTP客户端向指定的API端点发送请求，
        获取实际支付项目列表数据，支持灵活配置请求参数。
        适用于需要并发处理多个请求的场景。

        Args:
            client (httpx.AsyncClient, optional): 异步HTTP客户端实例
                如果不提供，将自动创建一个新的客户端
            validate_json_schema (dict, optional): JSON Schema验证规则
                用于验证API响应的结构是否符合预期
                默认验证响应中包含"result"字段且值为True
            **kwargs: 额外的请求参数，将直接传递给client.request方法
                可覆盖默认的method、url、params等参数

        Returns:
            tuple: 返回三元组 (is_valid, payment_list, response)
                - is_valid: JSON Schema验证结果（布尔值）
                - payment_list: 实际支付项目列表，如果请求失败则返回空列表
                - response: httpx.Response对象

        注意:
            - 这是一个异步方法，调用时需要使用await关键字
            - 默认请求方法为GET
            - 默认请求参数包含 {"json": "Getpayment"}，用于指定API方法
            - 响应JSON中实际支付项目列表存储在"Getpayment"字段中
        """
        # 设置默认请求方法为GET，符合HTTP GET方法的语义（获取资源）
        kwargs.setdefault("method", "GET")
        # 设置默认API端点URL，指向获取支付项目列表的接口
        kwargs.setdefault("url", "/estate/WebSerVice/jsonPostInterfaceNew.ashx")
        # 获取或创建请求参数字典，避免None值导致的类型错误
        params = kwargs.get("params", dict())
        # 添加API方法参数，指定调用Getpayment接口获取支付项目数据
        params.setdefault("json", "Getpayment")
        # 将更新后的参数字典放回kwargs
        kwargs["params"] = params

        # 客户端处理：如果未提供客户端，则创建新客户端并自动关闭
        if not isinstance(client, httpx.AsyncClient):
            # 使用async with上下文管理器确保异步客户端在使用后正确关闭
            async with self.async_client() as client:
                response = await client.request(**kwargs)
        else:
            # 如果提供了客户端，则直接使用（由调用方负责关闭）
            response = await client.request(**kwargs)

        # 响应处理：解析响应JSON（如果请求成功且有响应文本）
        response_json = response.json() if response.is_success else dict()

        # 验证响应JSON结构并返回结果
        return (
            Draft202012Validator(validate_json_schema).is_valid(response_json),
            response_json.get("Getpayment", list()),
            response
        )