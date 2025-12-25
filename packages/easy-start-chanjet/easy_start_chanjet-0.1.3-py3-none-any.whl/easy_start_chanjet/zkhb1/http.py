#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
畅捷通中科汇博HTTP请求模块

该模块提供了与畅捷通中科汇博API交互的HTTP请求功能，
主要用于获取实际支付项目列表，支持同步和异步两种请求方式。
"""
import httpx

class Http:
    def __init__(self, base_url: str = "https://mnav.cyjintaiwuye.com"):
        self.base_url = base_url


def get_actual_payment_item_list(
        client: httpx.Client = None,
        multiple_return_values: bool = False,
        url: str = "/estate/WebSerVice/jsonPostInterfaceNew.ashx",
        **kwargs
):
    """
    同步获取实际支付项目列表
    
    该函数通过同步HTTP客户端向指定的API端点发送请求，
    获取实际支付项目列表数据，支持灵活配置请求参数。

    Args:
        client (httpx.Client): 同步HTTP客户端实例
        multiple_return_values (bool, optional): 是否返回多个值
            - True: 返回元组 (payment_list, response_json, response)
            - False: 仅返回payment_list
            默认值为 False
        url (str, optional): API端点URL
            默认值为 "/estate/WebSerVice/jsonPostInterfaceNew.ashx"
        **kwargs: 额外的请求参数，将直接传递给client.request方法
            可覆盖默认的method和params等参数

    Returns:
        Union[Tuple[list, dict, httpx.Response], list]:
            - 如果multiple_return_values为True：
              返回三元组 (payment_list, response_json, response)
              - payment_list: 实际支付项目列表，如果请求失败则返回空列表
              - response_json: 响应的JSON数据，如果请求失败或无响应文本则返回空字典
              - response: httpx.Response对象
            - 如果multiple_return_values为False：
              仅返回payment_list
    """
    # 设置默认请求方法为GET
    kwargs.setdefault("method", "GET")
    # 设置默认API端点URL
    kwargs.setdefault("url", url)

    # 获取或创建请求参数字典
    params = kwargs.get("params", dict())
    # 添加API方法参数，指定获取支付项目数据
    params.setdefault("json", "Getpayment")
    kwargs["params"] = params

    # 发送同步请求
    response = client.request(**kwargs)
    # 解析响应JSON（如果有响应文本）
    response_json = response.json() if response.text else dict()

    if multiple_return_values:
        # 返回完整结果信息
        return response_json.get("Getpayment", list()), response_json, response
    else:
        # 仅返回支付项目列表
        return response_json.get("Getpayment", list())


async def async_get_actual_payment_item_list(
        client: httpx.AsyncClient = None,
        multiple_return_values: bool = False,
        url: str = "/estate/WebSerVice/jsonPostInterfaceNew.ashx",
        **kwargs
):
    """
    异步获取实际支付项目列表
    
    该函数通过异步HTTP客户端向指定的API端点发送请求，
    获取实际支付项目列表数据，支持灵活配置请求参数。

    Args:
        client (httpx.AsyncClient): 异步HTTP客户端实例
        multiple_return_values (bool, optional): 是否返回多个值
            - True: 返回元组 (payment_list, response_json, response)
            - False: 仅返回payment_list
            默认值为 False
        url (str, optional): API端点URL
            默认值为 "/estate/WebSerVice/jsonPostInterfaceNew.ashx"
        **kwargs: 额外的请求参数，将直接传递给client.request方法
            可覆盖默认的method和params等参数

    Returns:
        Union[Tuple[list, dict, httpx.Response], list]:
            - 如果multiple_return_values为True：
              返回三元组 (payment_list, response_json, response)
              - payment_list: 实际支付项目列表，如果请求失败则返回空列表
              - response_json: 响应的JSON数据，如果请求失败或无响应文本则返回空字典
              - response: httpx.Response对象
            - 如果multiple_return_values为False：
              仅返回payment_list
    """
    # 设置默认请求方法为GET
    kwargs.setdefault("method", "GET")
    # 设置默认API端点URL
    kwargs.setdefault("url", url)

    # 获取或创建请求参数字典
    params = kwargs.get("params", dict())
    # 添加API方法参数，指定获取支付项目数据
    params.setdefault("json", "Getpayment")
    kwargs["params"] = params

    # 发送异步请求
    response = await client.request(**kwargs)
    # 解析响应JSON（如果有响应文本）
    response_json = response.json() if response.text else dict()

    if multiple_return_values:
        # 返回完整结果信息
        return response_json.get("Getpayment", list()), response_json, response
    else:
        # 仅返回支付项目列表
        return response_json.get("Getpayment", list())
