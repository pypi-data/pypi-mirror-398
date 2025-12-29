import os
import sys

from typing import List

from alibabacloud_vpc20160428.client import Client as Vpc20160428Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_vpc20160428 import models as vpc_20160428_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient
from pixelarraylib.monitor.feishu import Feishu

feishu_alert = Feishu("devtoolkit服务报警")


class EIPUtils:
    def __init__(self, region_id: str, access_key_id: str, access_key_secret: str):
        """
        description:
            初始化EIP工具类
        parameters:
            region_id(str): 地域ID
            access_key_id(str): 访问密钥ID
            access_key_secret(str): 访问密钥Secret
        """
        self.region_id = region_id
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.client = self._create_client()

    def _create_client(self) -> Vpc20160428Client:
        """
        description:
            创建EIP客户端
        return:
            Vpc20160428Client: EIP客户端实例
        """
        config = open_api_models.Config(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
            region_id=self.region_id,
            endpoint=f"vpc.{self.region_id}.aliyuncs.com",
        )
        return Vpc20160428Client(config)

    def allocate_eip(self):
        """
        description:
            分配EIP
        return:
            dict: 分配结果
            success(bool): 是否成功
        """
        allocate_eip_address_request = vpc_20160428_models.AllocateEipAddressRequest(
            region_id=self.region_id
        )
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
            response = self.client.allocate_eip_address_with_options(
                allocate_eip_address_request, runtime
            )
            return response.body.to_map(), True
        except Exception as error:
            print(f"分配EIP失败: {error}")
            return {}, False

    def release_eip(self, allocation_id: str):
        """
        description:
            释放EIP
        parameters:
            allocation_id(str): 分配ID
        return:
            dict: 释放结果
            success(bool): 是否成功
        """
        release_eip_address_request = vpc_20160428_models.ReleaseEipAddressRequest(
            region_id=self.region_id, allocation_id=allocation_id
        )
        runtime = util_models.RuntimeOptions()
        try:
            response = self.client.release_eip_address_with_options(
                release_eip_address_request, runtime
            )
            return response.body.to_map(), True
        except Exception as error:
            print(f"释放EIP失败: {error}")
            return {}, False

    def list_eips(self):
        """
        description:
            查询EIP列表
        return:
            dict: 查询结果
            success(bool): 是否成功
        """
        list_eip_addresses_request = vpc_20160428_models.DescribeEipAddressesRequest(
            region_id=self.region_id
        )
        runtime = util_models.RuntimeOptions()
        try:
            response = self.client.describe_eip_addresses_with_options(
                list_eip_addresses_request, runtime
            )
            return response.body.to_map(), True
        except Exception as error:
            print(f"查询EIP列表失败: {error}")
            return {}, False
