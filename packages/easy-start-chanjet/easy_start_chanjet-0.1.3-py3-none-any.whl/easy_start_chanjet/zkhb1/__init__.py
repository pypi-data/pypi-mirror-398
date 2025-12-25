#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
畅捷通中科华博(zkhb)模块

该模块提供了与畅捷通中科汇博相关的功能，包括：
1. 支付日期范围验证
2. API客户端创建与管理

支持同步和异步HTTP请求，提供灵活的参数配置。
"""

from typing import Union

import arrow
# 导入HTTP客户端库，用于发送同步和异步HTTP请求
import httpx


def validate_payment_date_range(
        daily_fee: Union[int, float] = 0,
        total_amount: Union[int, float] = 0,
        start_date: str = "",
        end_date: str = ""
):
    """
    验证支付日期范围内的金额是否足够
    
    该函数用于验证在指定的日期范围内，总支付金额是否不小于
    日费用乘以天数的乘积，确保支付金额足够覆盖整个周期的费用。

    Args:
        daily_fee (Union[int, float], optional): 每日费用
            默认值为 0
        total_amount (Union[int, float], optional): 总支付金额
            默认值为 0
        start_date (str, optional): 开始日期，格式需支持arrow解析
            默认值为空字符串
        end_date (str, optional): 结束日期，格式需支持arrow解析
            默认值为空字符串

    Returns:
        bool: 如果总金额大于等于日费用乘以天数的乘积，则返回True，否则返回False
    """
    # 将费用转换为浮点数进行计算
    daily_fee = float(daily_fee)
    total_amount = float(total_amount)

    # 将日期字符串解析为arrow对象
    start_date_arrow: arrow.Arrow = arrow.get(start_date)
    end_date_arrow: arrow.Arrow = arrow.get(end_date)

    # 计算日期范围内的总天数
    # 使用interval方法生成日期序列，然后计算序列长度
    total_days = sum(1 for i in start_date_arrow.interval(frame="days", start=start_date, end=end_date_arrow))

    # 验证总金额是否足够覆盖整个周期的费用
    return total_amount >= (daily_fee * total_days)


class Api:
    """
    畅捷通中科汇博API客户端类
    
    该类用于创建和管理与畅捷通中科汇博API交互的HTTP客户端，
    支持同步和异步两种请求方式，提供统一的客户端配置接口。
    """

    def __init__(self, base_url: str = ""):
        """
        初始化API客户端
        
        Args:
            base_url (str, optional): API基础URL
                如果URL以"/"结尾，会自动移除末尾的斜杠
                默认值为空字符串
        """
        # 处理基础URL，确保不以斜杠结尾
        self.base_url = base_url[:-1] if base_url.endswith("/") else base_url

    def client(self, **kwargs):
        """
        创建并返回同步HTTP客户端
        
        Args:
            **kwargs: 传递给httpx.Client的额外参数
                可覆盖默认配置（base_url, timeout, verify等）
        
        Returns:
            httpx.Client: 配置好的同步HTTP客户端实例
        """
        # 设置默认基础URL
        kwargs.setdefault("base_url", self.base_url)
        # 设置默认超时时间为120秒
        kwargs.setdefault("timeout", 120)
        # 禁用SSL证书验证
        kwargs.setdefault("verify", False)
        return httpx.Client(**kwargs)

    def async_client(self, **kwargs):
        """
        创建并返回异步HTTP客户端
        
        Args:
            **kwargs: 传递给httpx.AsyncClient的额外参数
                可覆盖默认配置（base_url, timeout, verify等）
        
        Returns:
            httpx.AsyncClient: 配置好的异步HTTP客户端实例
        """
        # 设置默认基础URL
        kwargs.setdefault("base_url", self.base_url)
        # 设置默认超时时间为120秒
        kwargs.setdefault("timeout", 120)
        # 禁用SSL证书验证
        kwargs.setdefault("verify", False)
        return httpx.AsyncClient(**kwargs)
