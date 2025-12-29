import re
import traceback
import pandas as pd
from alibabacloud_bssopenapi20171214.client import Client as BssOpenApi20171214Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_bssopenapi20171214 import models as bss_open_api_20171214_models
from alibabacloud_tea_util import models as util_models
from pixelarraylib.monitor.feishu import Feishu

feishu_alert = Feishu("devtoolkit服务报警")


class BillingUtils:
    def __init__(
        self, access_key_id, access_key_secret, use_proxy=False, proxy_url=None
    ):
        """
        description:
            初始化阿里云计费工具类
        parameters:
            access_key_id(str): 阿里云访问密钥ID
            access_key_secret(str): 阿里云访问密钥Secret
            use_proxy(bool): 是否使用代理，默认False
            proxy_url(str): 代理URL，格式如 http://127.0.0.1:7897
        """
        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            endpoint="business.aliyuncs.com",
        )

        self.client = BssOpenApi20171214Client(config)

    def _format_bill_response(self, response, with_comments=False):
        """
        description:
            格式化账单查询响应为JSON格式

        parameters:
            response(dict): API响应对象
            with_comments(bool): 是否添加注释，默认False
        return:
            dict: 格式化后的响应数据
        """
        # 字段注释映射
        field_comments = {
            "Message": "错误信息",
            "RequestId": "请求ID",
            "BillingCycle": "账期",
            "TotalCount": "总记录数",
            "AccountID": "账号ID",
            "AccountName": "账号名称",
            "MaxResults": "本次请求所返回的最大记录数",
            "NextToken": "用来表示当前调用返回读取到的位置，空代表数据已经读取完毕",
            "Code": "状态码",
            "Success": "是否成功",
            "ProductName": "产品名称",
            "SubOrderId": "该条账单对应的订单明细ID",
            "BillAccountID": "账单所属账号ID",
            "DeductedByCashCoupons": "代金券折扣",
            "PaymentTime": "订单支付时间",
            "PaymentAmount": "现金支付（包含信用额度退款抵扣）",
            "DeductedByPrepaidCard": "储值卡抵扣",
            "InvoiceDiscount": "优惠金额",
            "UsageEndTime": "账单结束时间",
            "Item": "账单类型",
            "SubscriptionType": "订阅类型",
            "PretaxGrossAmount": "原始金额",
            "Currency": "货币类型",
            "CommodityCode": "商品Code，与费用中心产品明细Code一致",
            "UsageStartTime": "账单开始时间",
            "AdjustAmount": "信用额度退款抵扣",
            "Status": "支付状态",
            "DeductedByCoupons": "优惠券抵扣",
            "RoundDownDiscount": "抹零优惠",
            "ProductDetail": "产品明细",
            "ProductCode": "产品代码",
            "ProductType": "产品类型",
            "OutstandingAmount": "未结清金额",
            "BizType": "业务类型",
            "PipCode": "产品Code，与费用中心账单产品Code一致",
            "PretaxAmount": "应付金额",
            "OwnerID": "自帐号AccountID（多账号代付场景）",
            "BillAccountName": "账单所属账号名称",
            "RecordID": "订单号、账单号",
            "CashAmount": "现金支付（不包含信用额度退款抵扣）",
        }

        def add_comment(value, field_name):
            """
            description:
                为字段值添加注释
            parameters:
                value(Any): 字段值
                field_name(str): 字段名称
            return:
                value_with_comment(str): 带注释的字段值
            """
            if with_comments and field_name in field_comments:
                return f"{value} # {field_comments[field_name]}"
            return value

        try:
            # 构建基础响应结构
            formatted_response = {
                "Message": add_comment(
                    "Successful!" if response.body.success else "Failed", "Message"
                ),
                "RequestId": add_comment(response.body.request_id, "RequestId"),
                "Data": {
                    "BillingCycle": add_comment(
                        response.body.data.billing_cycle, "BillingCycle"
                    ),
                    "TotalCount": add_comment(
                        response.body.data.total_count, "TotalCount"
                    ),
                    "AccountID": add_comment(
                        getattr(response.body.data, "account_id", ""), "AccountID"
                    ),
                    "AccountName": add_comment(
                        getattr(response.body.data, "account_name", ""), "AccountName"
                    ),
                    "MaxResults": add_comment(
                        getattr(response.body.data, "max_results", 0), "MaxResults"
                    ),
                    "Items": {"Item": []},
                },
                "Code": add_comment(
                    "Success" if response.body.success else "Failed", "Code"
                ),
                "Success": add_comment(response.body.success, "Success"),
            }

            # 添加NextToken（如果存在）
            if (
                hasattr(response.body.data, "next_token")
                and response.body.data.next_token
            ):
                formatted_response["Data"]["NextToken"] = add_comment(
                    response.body.data.next_token, "NextToken"
                )

            # 处理账单项
            if hasattr(response.body.data, "items") and response.body.data.items:
                items = response.body.data.items
                if hasattr(items, "item") and items.item:
                    bill_items = items.item
                    if not isinstance(bill_items, list):
                        bill_items = [bill_items]

                    for item in bill_items:
                        item_data = {
                            "ProductName": add_comment(
                                getattr(item, "product_name", ""), "ProductName"
                            ),
                            "SubOrderId": add_comment(
                                getattr(item, "sub_order_id", ""), "SubOrderId"
                            ),
                            "BillAccountID": add_comment(
                                getattr(item, "bill_account_id", ""), "BillAccountID"
                            ),
                            "DeductedByCashCoupons": add_comment(
                                getattr(item, "deducted_by_cash_coupons", 0),
                                "DeductedByCashCoupons",
                            ),
                            "PaymentTime": add_comment(
                                getattr(item, "payment_time", ""), "PaymentTime"
                            ),
                            "PaymentAmount": add_comment(
                                getattr(item, "payment_amount", 0), "PaymentAmount"
                            ),
                            "DeductedByPrepaidCard": add_comment(
                                getattr(item, "deducted_by_prepaid_card", 0),
                                "DeductedByPrepaidCard",
                            ),
                            "InvoiceDiscount": add_comment(
                                getattr(item, "invoice_discount", 0), "InvoiceDiscount"
                            ),
                            "UsageEndTime": add_comment(
                                getattr(item, "usage_end_time", ""), "UsageEndTime"
                            ),
                            "Item": add_comment(getattr(item, "item", ""), "Item"),
                            "SubscriptionType": add_comment(
                                getattr(item, "subscription_type", ""),
                                "SubscriptionType",
                            ),
                            "PretaxGrossAmount": add_comment(
                                getattr(item, "pretax_gross_amount", 0),
                                "PretaxGrossAmount",
                            ),
                            "Currency": add_comment(
                                getattr(item, "currency", "CNY"), "Currency"
                            ),
                            "CommodityCode": add_comment(
                                getattr(item, "commodity_code", ""), "CommodityCode"
                            ),
                            "UsageStartTime": add_comment(
                                getattr(item, "usage_start_time", ""), "UsageStartTime"
                            ),
                            "AdjustAmount": add_comment(
                                getattr(item, "adjust_amount", 0), "AdjustAmount"
                            ),
                            "Status": add_comment(
                                getattr(item, "status", ""), "Status"
                            ),
                            "DeductedByCoupons": add_comment(
                                getattr(item, "deducted_by_coupons", 0),
                                "DeductedByCoupons",
                            ),
                            "RoundDownDiscount": add_comment(
                                getattr(item, "round_down_discount", 0),
                                "RoundDownDiscount",
                            ),
                            "ProductDetail": add_comment(
                                getattr(item, "product_detail", ""), "ProductDetail"
                            ),
                            "ProductCode": add_comment(
                                getattr(item, "product_code", ""), "ProductCode"
                            ),
                            "ProductType": add_comment(
                                getattr(item, "product_type", ""), "ProductType"
                            ),
                            "OutstandingAmount": add_comment(
                                getattr(item, "outstanding_amount", 0),
                                "OutstandingAmount",
                            ),
                            "BizType": add_comment(
                                getattr(item, "biz_type", ""), "BizType"
                            ),
                            "PipCode": add_comment(
                                getattr(item, "pip_code", ""), "PipCode"
                            ),
                            "PretaxAmount": add_comment(
                                getattr(item, "pretax_amount", 0), "PretaxAmount"
                            ),
                            "OwnerID": add_comment(
                                getattr(item, "owner_id", ""), "OwnerID"
                            ),
                            "BillAccountName": add_comment(
                                getattr(item, "bill_account_name", ""),
                                "BillAccountName",
                            ),
                            "RecordID": add_comment(
                                getattr(item, "record_id", ""), "RecordID"
                            ),
                            "CashAmount": add_comment(
                                getattr(item, "cash_amount", 0), "CashAmount"
                            ),
                        }
                        formatted_response["Data"]["Items"]["Item"].append(item_data)

            return formatted_response

        except Exception as e:
            print(traceback.format_exc())
            error_response = {
                "Message": add_comment(f"Format error: {str(e)}", "Message"),
                "RequestId": add_comment(
                    getattr(response.body, "request_id", ""), "RequestId"
                ),
                "Data": {},
                "Code": add_comment("Error", "Code"),
                "Success": add_comment(False, "Success"),
            }
            return error_response

    def _query_bill_once(
        self,
        billing_cycle: str,
        max_results: int = 20,
        next_token: str = None,
        product_code: str = None,
        subscription_type: str = None,
        product_type: str = None,
        is_hide_zero_charge: bool = False,
    ) -> dict:
        """
        description:
            查询阿里云账单信息
        parameters:
            billing_cycle: 账单周期，格式：YYYY-MM，默认：2025-08
            max_results: 最大返回记录数，默认：20
            next_token: 下一页的token，用于分页查询
            product_code: 产品代码，可选
            subscription_type: 订阅类型，可选值：Subscription（预付费）、PayAsYouGo（后付费）
            product_type: 产品类型，可选
            is_hide_zero_charge: 是否隐藏零费用记录，默认：False
        return:
            dict: 格式化后的响应数据
            返回格式化的JSON响应，包含以下字段：
            - Message: 错误信息
            - RequestId: 请求ID
            - Data: 返回数据
            - BillingCycle: 账期
            - TotalCount: 总记录数
            - AccountID: 账号ID
            - AccountName: 账号名称
            - MaxResults: 本次请求所返回的最大记录数
            - NextToken: 用来表示当前调用返回读取到的位置，空代表数据已经读取完毕
            - Items: 账单详情列表
                - Item: 账单详情数组，包含产品名称、费用信息、支付状态等详细字段
        """
        # 构建请求参数
        request_params = {
            "billing_cycle": billing_cycle,
            "max_results": max_results,
            "is_hide_zero_charge": is_hide_zero_charge,
        }

        # 添加可选参数
        if next_token:
            request_params["next_token"] = next_token
        if product_code:
            request_params["product_code"] = product_code
        if subscription_type:
            request_params["subscription_type"] = subscription_type
        if product_type:
            request_params["product_type"] = product_type

        query_settle_bill_request = bss_open_api_20171214_models.QuerySettleBillRequest(
            **request_params
        )
        runtime = util_models.RuntimeOptions()
        try:
            # 调用 API 并获取返回结果
            response = self.client.query_settle_bill_with_options(
                query_settle_bill_request, runtime
            )

            # 格式化响应并返回带注释的JSON格式
            formatted_response = self._format_bill_response(
                response, with_comments=True
            )
            return formatted_response

        except Exception as error:
            print(traceback.format_exc())
            error_msg = getattr(error, "message", str(error))
            # 诊断地址
            diagnose_url = ""
            if hasattr(error, "data") and error.data:
                diagnose_url = error.data.get("Recommend", "")

            # 返回错误响应
            error_response = {
                "Message": f"错误信息: {error_msg}",
                "RequestId": "",
                "Data": {},
                "Code": "Error",
                "Success": False,
                "DiagnoseUrl": diagnose_url,
            }
            return error_response

    def query_bill(self, billing_cycle: str, batch_size: int = 300):
        """
        description:
            按月份查询阿里云账单信息，会自动分页查询
        parameters:
            billing_cycle: 账单周期，格式：YYYY-MM，默认：2025-08
            batch_size: 每页返回的记录数，默认：300
        return:
            dict: 格式化后的响应数据
        """
        response = self._query_bill_once(billing_cycle=billing_cycle)
        bill_data = response.get("Data", {}).get("Items", {}).get("Item", [])
        next_token = response.get("Data", {}).get("NextToken")
        while next_token:
            response = self._query_bill_once(
                billing_cycle=billing_cycle,
                next_token=next_token,
                max_results=batch_size,
            )
            bill_data.extend(response.get("Data", {}).get("Items", {}).get("Item", []))
            next_token = response.get("Data", {}).get("NextToken")
        return bill_data

    def save_bill(
        self,
        bill_data: dict,
        output_path: str,
        file_format: str = "csv",
        translate_headers: bool = False,
    ) -> str:
        """
        description:
            将query_bill的输出结果保存为表格文件
        parameters:
            bill_data: query_bill方法返回的账单数据
            output_path: 输出文件路径
            file_format: 文件格式，支持 'excel', 'csv', 'json'，默认 'excel'
            translate_headers: 是否将表头翻译为中文，默认 False
        return:
            str: 保存的文件路径
        """
        try:
            # 内部工具：清洗字符串
            # 1) 去除注释（例如 "value # 注释" -> "value"）
            # 2) 去除首尾空白，并将内部连续空白压缩为一个空格
            # 3) 去除常见的不可见空白字符（如不间断空格、零宽空格）
            def _clean_string(value):
                """
                description:
                    清洗字符串，去除注释、不可见字符并规范化空白
                parameters:
                    value(Any): 需要清洗的值
                return:
                    cleaned_value(Any): 清洗后的值
                """
                if not isinstance(value, str):
                    return value
                # 去注释
                if " # " in value:
                    value = value.split(" # ", 1)[0]
                # 替换不可见空白
                value = (
                    value.replace("\u00a0", " ")
                    .replace("\u200b", "")
                    .replace("\u200c", "")
                    .replace("\u200d", "")
                )
                # 规范化空白：先strip，再将内部所有空白替换为下划线
                value = value.strip()
                if value:
                    # 将任意连续空白缩为一个空格
                    # 1) 将任意连续空白（空格、制表符等）替换为单个下划线
                    value = re.sub(r"\s+", "_", value)
                return value

            # 创建DataFrame
            df = pd.DataFrame(bill_data)
            # 清洗字符串
            df = df.applymap(_clean_string)
            # 将NaN替换为空字符串，确保表格为空显示空，不是NaN
            df = df.fillna("")

            # 可选：根据注释映射翻译表头为中文
            if translate_headers:
                header_map = {
                    # 公共字段
                    "BillingCycle": "账期",
                    "AccountID": "账号ID",
                    "AccountName": "账号名称",
                    # 账单项字段（与 _format_bill_response 中注释一致）
                    "ProductName": "产品名称",
                    "SubOrderId": "订单明细ID",
                    "BillAccountID": "账单所属账号ID",
                    "DeductedByCashCoupons": "代金券折扣",
                    "PaymentTime": "订单支付时间",
                    "PaymentAmount": "现金支付（含信用额度退款抵扣）",
                    "DeductedByPrepaidCard": "储值卡抵扣",
                    "InvoiceDiscount": "优惠金额",
                    "UsageEndTime": "账单结束时间",
                    "Item": "账单类型",
                    "SubscriptionType": "订阅类型",
                    "PretaxGrossAmount": "原始金额",
                    "Currency": "货币类型",
                    "CommodityCode": "商品Code",
                    "UsageStartTime": "账单开始时间",
                    "AdjustAmount": "信用额度退款抵扣",
                    "Status": "支付状态",
                    "DeductedByCoupons": "优惠券抵扣",
                    "RoundDownDiscount": "抹零优惠",
                    "ProductDetail": "产品明细",
                    "ProductCode": "产品代码",
                    "ProductType": "产品类型",
                    "OutstandingAmount": "未结清金额",
                    "BizType": "业务类型",
                    "PipCode": "产品Code",
                    "PretaxAmount": "应付金额",
                    "OwnerID": "自帐号AccountID",
                    "BillAccountName": "账单所属账号名称",
                    "RecordID": "订单号/账单号",
                    "CashAmount": "现金支付（不含信用额度退款抵扣）",
                }
                # 仅重命名存在的列
                df = df.rename(
                    columns={k: v for k, v in header_map.items() if k in df.columns}
                )

            # 保存文件
            if file_format == "excel":
                df.to_excel(output_path, index=False, engine="openpyxl")
            elif file_format == "csv":
                df.to_csv(output_path, index=False, encoding="utf-8-sig")
            elif file_format == "json":
                df.to_json(output_path, orient="records", force_ascii=False, indent=2)

            return output_path

        except Exception as e:
            print(traceback.format_exc())
            raise Exception(f"保存账单数据失败: {str(e)}")
