#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
畅捷通中科华博WebService模块

该模块提供了与畅捷通中科华博WebService API交互的功能，包括：
1. 生成支付项目查询SQL语句
2. 同步和异步调用WebService API获取数据集

支持SOAP XML格式请求，使用BeautifulSoup解析XML响应，
支持灵活配置请求参数，并根据需要返回不同格式的结果。
"""
import httpx
# 导入XML与字典转换库，用于构建SOAP请求和解析响应
import xmltodict
# 导入BeautifulSoup库，用于解析XML格式的WebService响应
from bs4 import BeautifulSoup


def get_query_actual_payment_item_list_sql(
        column_str: str = "",
        condition_str: str = "",
        order_by_str: str = "order by cfi.ChargeFeeItemID"
):
    """
    生成查询实际支付项目列表的SQL语句
    
    该函数用于构建查询实际支付项目的SQL语句，支持自定义列名、条件和排序方式，
    主要用于在WebService API中执行复杂的数据库查询。

    Args:
        column_str (str, optional): 自定义查询列，为空则使用默认列集合
            默认值为空字符串
        condition_str (str, optional): 自定义查询条件，将添加到WHERE子句中
            默认值为空字符串
        order_by_str (str, optional): 自定义排序方式
            默认值为 "order by cfi.ChargeFeeItemID"

    Returns:
        str: 完整的SQL查询语句
    """
    # 定义默认查询列集合
    default_columns = [
        'cml.ChargeMListID',
        'cml.ChargeMListNo',
        'cml.ChargeTime',
        'cml.PayerName',
        'cml.ChargePersonName',
        'cml.ActualPayMoney',
        'cml.EstateID',
        'cml.ItemNames',
        'ed.Caption as EstateName',
        'cfi.ChargeFeeItemID',
        'cfi.ActualAmount',
        'cfi.SDate',
        'cfi.EDate',
        'cfi.RmId',
        'rd.RmNo',
        'cml.CreateTime',
        'cml.LastUpdateTime',
        'cbi.ItemName',
        'cbi.IsPayFull',
    ]

    # 定义默认表连接关系
    table_joins = ''.join([
        ' from chargeMasterList as cml',
        ' left join EstateDetail as ed on cml.EstateID=ed.EstateID',
        ' left join ChargeFeeItem as cfi on cml.ChargeMListID=cfi.ChargeMListID',
        ' left join RoomDetail as rd on cfi.RmId=rd.RmId',
        ' left join ChargeBillItem as cbi on cfi.CBillItemID=cbi.CBillItemID',
    ])

    # 构建并返回完整的SQL语句
    return f"select {column_str} {','.join(default_columns)} {table_joins} where 1=1 {condition_str} {order_by_str};"


def get_data_set(
        client: httpx.Client = None,
        multiple_return_values: bool = False,
        url: str = "/estate/webService/ForcelandEstateService.asmx",
        **kwargs
):
    """
    同步调用WebService API获取数据集
    
    该函数通过同步HTTP客户端向WebService API发送SOAP请求，
    获取数据集并解析XML响应，支持灵活配置请求参数。

    Args:
        client (httpx.Client): 同步HTTP客户端实例
        multiple_return_values (bool, optional): 是否返回多个值
            - True: 返回元组 (results, response)
            - False: 仅返回results
            默认值为 False
        url (str, optional): WebService API端点URL
            默认值为 "/estate/webService/ForcelandEstateService.asmx"
        **kwargs: 额外的请求参数，将直接传递给client.request方法
            可覆盖默认的method、url、params、headers和data等参数

    Returns:
        Union[Tuple[list, httpx.Response], list]:
            - 如果multiple_return_values为True：
              返回元组 (results, response)
              - results: 解析后的数据列表，如果请求失败或解析失败则返回空列表
              - response: httpx.Response对象
            - 如果multiple_return_values为False：
              仅返回results
    """
    # 设置默认请求方法为POST
    kwargs.setdefault("method", "POST")
    # 设置默认WebService API端点URL
    kwargs.setdefault("url", url)

    # 获取或创建请求参数字典
    params = kwargs.get("params", dict())
    # 添加WebService操作参数，指定获取数据集
    params.setdefault("op", "GetDataSet")
    kwargs["params"] = params

    # 获取或创建请求头字典
    headers = kwargs.get("headers", dict())
    # 设置SOAP请求的Content-Type
    headers.setdefault("Content-Type", "text/xml; charset=utf-8")
    kwargs["headers"] = headers

    # 获取请求数据
    data = kwargs.get("data", dict())

    # 将请求数据转换为SOAP XML格式
    data = xmltodict.unparse(
        {
            "soap:Envelope": {
                "@xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/",
                "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "@xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
                "soap:Body": {
                    "GetDataSet": {
                        "@xmlns": "http://zkhb.com.cn/",
                        **data,
                    }
                }
            }
        }
    )
    kwargs["data"] = data

    # 发送同步请求
    response = client.request(**kwargs)

    # 解析SOAP响应XML
    xml_doc = BeautifulSoup(response.text, features="xml") if response.is_success else None
    if xml_doc is None:
        results = []
    else:
        # 提取数据集部分并转换为字典
        new_data_set = xmltodict.parse(xml_doc.find("NewDataSet").encode("utf-8"), encoding="utf-8")
        results = new_data_set.get("NewDataSet", dict()).get("Table", dict())

        # 确保结果始终是列表格式
        if not isinstance(results, list):
            results = [results]

    if multiple_return_values:
        # 返回完整结果信息
        return results, response
    else:
        # 仅返回解析后的数据列表
        return results


async def async_get_data_set(
        client: httpx.AsyncClient = None,
        multiple_return_values: bool = False,
        url: str = "/estate/webService/ForcelandEstateService.asmx",
        **kwargs
):
    """
    异步调用WebService API获取数据集
    
    该函数通过异步HTTP客户端向WebService API发送SOAP请求，
    获取数据集并解析XML响应，支持灵活配置请求参数。

    Args:
        client (httpx.AsyncClient): 异步HTTP客户端实例
        multiple_return_values (bool, optional): 是否返回多个值
            - True: 返回元组 (results, response)
            - False: 仅返回results
            默认值为 False
        url (str, optional): WebService API端点URL
            默认值为 "/estate/webService/ForcelandEstateService.asmx"
        **kwargs: 额外的请求参数，将直接传递给client.request方法
            可覆盖默认的method、url、params、headers和data等参数

    Returns:
        Union[Tuple[list, httpx.Response], list]:
            - 如果multiple_return_values为True：
              返回元组 (results, response)
              - results: 解析后的数据列表，如果请求失败或解析失败则返回空列表
              - response: httpx.Response对象
            - 如果multiple_return_values为False：
              仅返回results
    
    Note:
        代码中第119行存在逻辑错误：`if isinstance(results, list): results = [results]`
        这会将一个列表再包装一层列表，应该修改为：`if not isinstance(results, list): results = [results]`
    """
    # 设置默认请求方法为POST
    kwargs.setdefault("method", "POST")
    # 设置默认WebService API端点URL
    kwargs.setdefault("url", url)

    # 获取或创建请求参数字典
    params = kwargs.get("params", dict())
    # 添加WebService操作参数，指定获取数据集
    params.setdefault("op", "GetDataSet")
    kwargs["params"] = params

    # 获取或创建请求头字典
    headers = kwargs.get("headers", dict())
    # 设置SOAP请求的Content-Type
    headers.setdefault("Content-Type", "text/xml; charset=utf-8")
    kwargs["headers"] = headers

    # 获取请求数据
    data = kwargs.get("data", dict())

    # 将请求数据转换为SOAP XML格式
    data = xmltodict.unparse(
        {
            "soap:Envelope": {
                "@xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/",
                "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "@xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
                "soap:Body": {
                    "GetDataSet": {
                        "@xmlns": "http://zkhb.com.cn/",
                        **data,
                    }
                }
            }
        }
    )
    kwargs["data"] = data

    # 发送异步请求
    response = await client.request(**kwargs)

    # 解析SOAP响应XML
    xml_doc = BeautifulSoup(response.text, features="xml")

    # 提取数据集部分并转换为字典
    new_data_set = xmltodict.parse(xml_doc.find("NewDataSet").encode("utf-8"), encoding="utf-8")
    results = new_data_set.get("NewDataSet", dict()).get("Table")

    # 确保结果始终是列表格式
    # 注意：此处存在逻辑错误，应该是 if not isinstance(results, list): results = [results]
    if not isinstance(results, list):
        results = [results]  # 错误：将列表再包装一层列表

    if multiple_return_values:
        # 返回完整结果信息
        return results, response
    else:
        # 仅返回解析后的数据列表
        return results
