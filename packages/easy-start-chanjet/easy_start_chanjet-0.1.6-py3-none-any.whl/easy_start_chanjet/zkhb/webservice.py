#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
畅捷通中科华博WebService模块

该模块提供了与畅捷通中科华博WebService API交互的功能，包括：
1. 生成支付项目查询SQL语句
2. 同步和异步调用WebService API获取数据集

支持SOAP XML格式请求，使用BeautifulSoup解析XML响应，
支持灵活配置请求参数，并根据需要返回不同格式的结果。

技术依赖:
- httpx: 用于HTTP请求（支持同步和异步）
- xmltodict: 用于XML与字典之间的转换
- BeautifulSoup: 用于解析XML格式的响应
"""
import httpx
import xmltodict
from bs4 import BeautifulSoup


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

    def get_query_actual_payment_item_list_sql(
            self,
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

        表结构说明:
            - chargeMasterList (cml): 收费主列表
            - EstateDetail (ed): 小区详情
            - ChargeFeeItem (cfi): 收费项目
            - RoomDetail (rd): 房间详情
            - ChargeBillItem (cbi): 收费账单项目

        默认查询列说明:
            - ChargeMListID: 收费主列表ID
            - ChargeMListNo: 收费单号
            - ChargeTime: 收费时间
            - PayerName: 付款人姓名
            - ChargePersonName: 收费人姓名
            - ActualPayMoney: 实际支付金额
            - EstateID: 小区ID
            - ItemNames: 项目名称
            - EstateName: 小区名称
            - ChargeFeeItemID: 收费项目ID
            - ActualAmount: 实际金额
            - SDate: 开始日期
            - EDate: 结束日期
            - RmId: 房间ID
            - RmNo: 房间号
            - CreateTime: 创建时间
            - LastUpdateTime: 最后更新时间
            - ItemName: 项目名称
            - IsPayFull: 是否已全额支付
        """
        # 定义默认查询列集合，包含收费相关的主要字段
        default_columns = [
            'cml.ChargeMListID',      # 收费主列表ID
            'cml.ChargeMListNo',      # 收费单号
            'cml.ChargeTime',         # 收费时间
            'cml.PayerName',          # 付款人姓名
            'cml.ChargePersonName',   # 收费人姓名
            'cml.ActualPayMoney',     # 实际支付金额
            'cml.EstateID',           # 小区ID
            'cml.ItemNames',          # 项目名称
            'ed.Caption as EstateName',  # 小区名称
            'cfi.ChargeFeeItemID',    # 收费项目ID
            'cfi.ActualAmount',       # 实际金额
            'cfi.SDate',              # 开始日期
            'cfi.EDate',              # 结束日期
            'cfi.RmId',               # 房间ID
            'rd.RmNo',                # 房间号
            'cml.CreateTime',         # 创建时间
            'cml.LastUpdateTime',     # 最后更新时间
            'cbi.ItemName',           # 项目名称
            'cbi.IsPayFull',          # 是否已全额支付
        ]

        # 定义默认表连接关系，使用left join确保即使关联表无数据也能返回结果
        table_joins = ''.join([
            ' from chargeMasterList as cml',                           # 主表：收费主列表
            ' left join EstateDetail as ed on cml.EstateID=ed.EstateID',  # 左联：小区详情
            ' left join ChargeFeeItem as cfi on cml.ChargeMListID=cfi.ChargeMListID',  # 左联：收费项目
            ' left join RoomDetail as rd on cfi.RmId=rd.RmId',         # 左联：房间详情
            ' left join ChargeBillItem as cbi on cfi.CBillItemID=cbi.CBillItemID',  # 左联：收费账单项目
        ])

        # 构建并返回完整的SQL语句，使用1=1便于添加额外条件
        return f"select {column_str} {','.join(default_columns)} {table_joins} where 1=1 {condition_str} {order_by_str};"

    def get_data_set(
            self,
            client: httpx.Client = None,
            **kwargs
    ):
        """
        同步调用WebService API获取数据集

        该函数通过同步HTTP客户端向WebService API发送SOAP请求，
        获取数据集并解析XML响应，支持灵活配置请求参数。

        Args:
            client (httpx.Client, optional): 同步HTTP客户端实例
                如果不提供，将自动创建一个新的客户端
            **kwargs: 额外的请求参数，将直接传递给client.request方法
                可覆盖默认的method、url、params、headers和data等参数

        Returns:
            tuple: 返回二元组 (results, response)
                - results: 解析后的数据列表，如果请求失败或解析失败则返回空列表
                - response: httpx.Response对象

        注意:
            - 默认请求方法为POST
            - 默认请求参数包含 {"op": "GetDataSet"}，用于指定WebService操作
            - 响应XML中数据集存储在"NewDataSet"元素内
            - 单个Table元素会被转换为列表，确保返回值始终是列表格式
        """
        # 设置默认请求方法为POST，符合WebService SOAP请求的通常做法
        kwargs.setdefault("method", "POST")
        # 设置默认WebService API端点URL，指向ForcelandEstateService服务
        kwargs.setdefault("url", "/estate/webService/ForcelandEstateService.asmx")

        # 获取或创建请求参数字典，避免None值导致的类型错误
        params = kwargs.get("params", dict())
        # 添加WebService操作参数，指定调用GetDataSet方法
        params.setdefault("op", "GetDataSet")
        # 将更新后的参数字典放回kwargs
        kwargs["params"] = params

        # 获取或创建请求头字典，设置SOAP请求所需的Content-Type
        headers = kwargs.get("headers", dict())
        # 设置SOAP请求的Content-Type为XML格式
        headers.setdefault("Content-Type", "text/xml; charset=utf-8")
        # 将更新后的请求头字典放回kwargs
        kwargs["headers"] = headers

        # 获取请求数据，将转换为SOAP XML格式
        data = kwargs.get("data", dict())
        # 将请求数据转换为SOAP XML格式，包含必要的命名空间和请求体
        data = xmltodict.unparse(
            {
                "soap:Envelope": {
                    "@xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/",  # SOAP信封命名空间
                    "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",  # XML Schema实例命名空间
                    "@xmlns:xsd": "http://www.w3.org/2001/XMLSchema",  # XML Schema命名空间
                    "soap:Body": {
                        "GetDataSet": {
                            "@xmlns": "http://zkhb.com.cn/",  # WebService操作命名空间
                            **data,  # 展开用户提供的请求数据
                        }
                    }
                }
            }
        )
        # 将生成的SOAP XML数据放回kwargs
        kwargs["data"] = data
        
        # 客户端处理：如果未提供客户端，则创建新客户端并自动关闭
        if not isinstance(client, httpx.Client):
            # 使用with上下文管理器确保客户端在使用后正确关闭
            with self.client() as client:
                response = client.request(**kwargs)
        else:
            # 如果提供了客户端，则直接使用（由调用方负责关闭）
            response = client.request(**kwargs)
        
        # 解析SOAP响应XML
        xml_doc = BeautifulSoup(response.text, features="xml") if response.is_success else None
        if xml_doc is None:
            # 如果请求失败或响应解析失败，返回空列表
            results = []
        else:
            # 提取数据集部分并转换为字典
            new_data_set = xmltodict.parse(xml_doc.find("NewDataSet").encode("utf-8"), encoding="utf-8")
            # 获取Table元素数据，默认返回空字典
            results = new_data_set.get("NewDataSet", dict()).get("Table", dict())

            # 确保结果始终是列表格式：如果只有单个Table元素，将其转换为列表
            if not isinstance(results, list):
                results = [results]

        # 返回完整结果信息：解析后的数据和响应对象
        return results, response

    async def async_get_data_set(
            self,
            client: httpx.AsyncClient = None,
            **kwargs
    ):
        """
        异步调用WebService API获取数据集

        该函数通过异步HTTP客户端向WebService API发送SOAP请求，
        获取数据集并解析XML响应，支持灵活配置请求参数。

        Args:
            client (httpx.AsyncClient, optional): 异步HTTP客户端实例
                如果不提供，将自动创建一个新的客户端
            **kwargs: 额外的请求参数，将直接传递给client.request方法
                可覆盖默认的method、url、params、headers和data等参数

        Returns:
            tuple: 返回二元组 (results, response)
                - results: 解析后的数据列表，如果请求失败或解析失败则返回空列表
                - response: httpx.Response对象

        注意:
            - 这是一个异步方法，调用时需要使用await关键字
            - 默认请求方法为POST
            - 默认请求参数包含 {"op": "GetDataSet"}，用于指定WebService操作
            - 响应XML中数据集存储在"NewDataSet"元素内
            - 单个Table元素会被转换为列表，确保返回值始终是列表格式
        """
        # 设置默认请求方法为POST，符合WebService SOAP请求的通常做法
        kwargs.setdefault("method", "POST")
        # 设置默认WebService API端点URL，指向ForcelandEstateService服务
        kwargs.setdefault("url", "/estate/webService/ForcelandEstateService.asmx")

        # 获取或创建请求参数字典，避免None值导致的类型错误
        params = kwargs.get("params", dict())
        # 添加WebService操作参数，指定调用GetDataSet方法
        params.setdefault("op", "GetDataSet")
        # 将更新后的参数字典放回kwargs
        kwargs["params"] = params

        # 获取或创建请求头字典，设置SOAP请求所需的Content-Type
        headers = kwargs.get("headers", dict())
        # 设置SOAP请求的Content-Type为XML格式
        headers.setdefault("Content-Type", "text/xml; charset=utf-8")
        # 将更新后的请求头字典放回kwargs
        kwargs["headers"] = headers

        # 获取请求数据，将转换为SOAP XML格式
        data = kwargs.get("data", dict())
        # 将请求数据转换为SOAP XML格式，包含必要的命名空间和请求体
        data = xmltodict.unparse(
            {
                "soap:Envelope": {
                    "@xmlns:soap": "http://schemas.xmlsoap.org/soap/envelope/",  # SOAP信封命名空间
                    "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",  # XML Schema实例命名空间
                    "@xmlns:xsd": "http://www.w3.org/2001/XMLSchema",  # XML Schema命名空间
                    "soap:Body": {
                        "GetDataSet": {
                            "@xmlns": "http://zkhb.com.cn/",  # WebService操作命名空间
                            **data,  # 展开用户提供的请求数据
                        }
                    }
                }
            }
        )
        # 将生成的SOAP XML数据放回kwargs
        kwargs["data"] = data
        
        # 客户端处理：如果未提供客户端，则创建新客户端并自动关闭
        if not isinstance(client, httpx.AsyncClient):
            # 使用async with上下文管理器确保异步客户端在使用后正确关闭
            async with self.async_client() as client:
                response = await client.request(**kwargs)
        else:
            # 如果提供了客户端，则直接使用（由调用方负责关闭）
            response = await client.request(**kwargs)
        
        # 解析SOAP响应XML
        xml_doc = BeautifulSoup(response.text, features="xml") if response.is_success else None
        if xml_doc is None:
            # 如果请求失败或响应解析失败，返回空列表
            results = []
        else:
            # 提取数据集部分并转换为字典
            new_data_set = xmltodict.parse(xml_doc.find("NewDataSet").encode("utf-8"), encoding="utf-8")
            # 获取Table元素数据，默认返回空字典
            results = new_data_set.get("NewDataSet", dict()).get("Table", dict())

            # 确保结果始终是列表格式：如果只有单个Table元素，将其转换为列表
            if not isinstance(results, list):
                results = [results]

        # 返回完整结果信息：解析后的数据和响应对象
        return results, response