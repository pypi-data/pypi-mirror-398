from alibabacloud_alidns20150109.client import Client as Alidns20150109Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_alidns20150109 import models as alidns_20150109_models
from alibabacloud_tea_util import models as util_models
from typing import Optional, Dict, Any


class DomainUtils:
    def __init__(self, access_key_id: str, access_key_secret: str, domain_name: str):
        """
        description:
            初始化域名服务工具类
        parameters:
            access_key_id(str): 阿里云访问密钥ID
            access_key_secret(str): 阿里云访问密钥Secret
            domain_name(str): 域名名称
        """
        self.domain_name = domain_name
        self.client = self._create_client(access_key_id, access_key_secret)

    def _create_client(
        self, access_key_id: str, access_key_secret: str
    ) -> Alidns20150109Client:
        """
        description:
            创建阿里云DNS客户端
        parameters:
            access_key_id(str): 阿里云访问密钥ID
            access_key_secret(str): 阿里云访问密钥Secret
        return:
            client(Alidns20150109Client): DNS客户端对象
        """
        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
        )
        config.endpoint = "alidns.cn-hangzhou.aliyuncs.com"
        return Alidns20150109Client(config)

    def list_domain_records(self) -> tuple[list, bool]:
        """
        description:
            列出域名解析记录
        return:
            records: 解析记录列表
            success: 操作是否成功
        """
        all_records = []
        page_number = 1
        page_size = 20
        runtime = util_models.RuntimeOptions()
        try:
            while True:
                describe_domain_records_request = (
                    alidns_20150109_models.DescribeDomainRecordsRequest(
                        domain_name=self.domain_name,
                        page_number=page_number,
                        page_size=page_size,
                    )
                )
                response = self.client.describe_domain_records_with_options(
                    describe_domain_records_request, runtime
                )
                records = response.body.domain_records.to_map()["Record"]
                if records:
                    all_records.extend(records)
                total_count = getattr(response.body, "total_count", None)
                if total_count is not None:
                    if page_number * page_size >= total_count:
                        break
                else:
                    # 如果没有total_count字段，判断本次返回数量是否小于page_size
                    if not records or len(records) < page_size:
                        break
                page_number += 1
            return all_records, True
        except Exception as error:
            return [], False

    async def list_domain_records_async(self) -> tuple[list, bool]:
        """
        description:
            异步列出域名解析记录
        return:
            records: 解析记录列表
            success: 操作是否成功
        """
        all_records = []
        page_number = 1
        page_size = 20
        runtime = util_models.RuntimeOptions()
        try:
            while True:
                describe_domain_records_request = (
                    alidns_20150109_models.DescribeDomainRecordsRequest(
                        domain_name=self.domain_name,
                        page_number=page_number,
                        page_size=page_size,
                    )
                )
                response = await self.client.describe_domain_records_with_options_async(
                    describe_domain_records_request, runtime
                )
                # 兼容同步接口的处理方式
                records = response.body.domain_records.to_map()["Record"]
                if records:
                    all_records.extend(records)
                total_count = getattr(response.body, "total_count", None)
                if total_count is not None:
                    if page_number * page_size >= total_count:
                        break
                else:
                    # 如果没有total_count字段，判断本次返回数量是否小于page_size
                    if not records or len(records) < page_size:
                        break
                page_number += 1
            return all_records, True
        except Exception as error:
            return [], False

    def add_domain_record(
        self,
        rr: str,
        type: str,
        value: str,
        ttl: int = 600,
        line: str = "default",
        priority: Optional[int] = None,
    ) -> tuple[bool, str]:
        """
        description:
            添加域名解析记录
        parameters:
            rr: 主机记录，如 www, @, *
            type: 记录类型，如 A, CNAME, MX, TXT 等
            value: 记录值
            ttl: TTL值，默认600秒
            line: 解析线路，默认default
            priority: 优先级，仅MX记录需要
        return:
            success: 操作是否成功
            record_id: 记录ID
        """
        runtime = util_models.RuntimeOptions()
        try:
            request = alidns_20150109_models.AddDomainRecordRequest(
                domain_name=self.domain_name,
                rr=rr,
                type=type,
                value=value,
                ttl=ttl,
                line=line,
            )

            if priority is not None:
                request.priority = priority

            response = self.client.add_domain_record_with_options(request, runtime)

            if response.body.record_id:
                return True, response.body.record_id
            else:
                return False, None

        except Exception as error:
            return False, None

    async def add_domain_record_async(
        self,
        rr: str,
        type: str,
        value: str,
        ttl: int = 600,
        line: str = "default",
        priority: Optional[int] = None,
    ) -> tuple[bool, str]:
        """
        description:
            异步添加域名解析记录
        parameters:
            rr: 主机记录，如 www, @, *
            type: 记录类型，如 A, CNAME, MX, TXT 等
            value: 记录值
            ttl: TTL值，默认600秒
            line: 解析线路，默认default
            priority: 优先级，仅MX记录需要
        return:
            success: 操作是否成功
            record_id: 记录ID
        """
        runtime = util_models.RuntimeOptions()
        try:
            request = alidns_20150109_models.AddDomainRecordRequest(
                domain_name=self.domain_name,
                rr=rr,
                type=type,
                value=value,
                ttl=ttl,
                line=line,
            )

            if priority is not None:
                request.priority = priority

            response = await self.client.add_domain_record_with_options_async(
                request, runtime
            )

            if response.body.record_id:
                return True, response.body.record_id
            else:
                return False, None

        except Exception as error:
            return False, None

    def delete_domain_record(self, record_id: str) -> bool:
        """
        description:
            删除域名解析记录
        parameters:
            record_id: 记录ID
        return:
            success: 操作是否成功
        """
        runtime = util_models.RuntimeOptions()
        try:
            request = alidns_20150109_models.DeleteDomainRecordRequest(
                record_id=record_id
            )

            response = self.client.delete_domain_record_with_options(request, runtime)

            if response.body.request_id:
                return True
            else:
                return False

        except Exception as error:
            return False

    async def delete_domain_record_async(self, record_id: str) -> bool:
        """
        description:
            异步删除域名解析记录
        parameters:
            record_id: 记录ID
        return:
            success: 操作是否成功
        """
        runtime = util_models.RuntimeOptions()
        try:
            request = alidns_20150109_models.DeleteDomainRecordRequest(
                record_id=record_id
            )

            response = await self.client.delete_domain_record_with_options_async(
                request, runtime
            )

            if response.body.request_id:
                return True
            else:
                return False

        except Exception as error:
            return False

    def update_domain_record(
        self,
        record_id: str,
        rr: str,
        type: str,
        value: str,
        ttl: int = 600,
        line: str = "default",
        priority: Optional[int] = None,
    ) -> tuple[bool, str]:
        """
        description:
            更新域名解析记录
        parameters:
            record_id: 记录ID
            rr: 主机记录，如 www, @, *
            type: 记录类型，如 A, CNAME, MX, TXT 等
            value: 记录值
            ttl: TTL值，默认600秒
            line: 解析线路，默认default
            priority: 优先级，仅MX记录需要
        return:
            success: 操作是否成功
            record_id: 记录ID
        """
        runtime = util_models.RuntimeOptions()
        try:
            request = alidns_20150109_models.UpdateDomainRecordRequest(
                record_id=record_id,
                rr=rr,
                type=type,
                value=value,
                ttl=ttl,
                line=line,
            )

            if priority is not None:
                request.priority = priority

            response = self.client.update_domain_record_with_options(request, runtime)

            if response.body.record_id:
                return True, response.body.record_id
            else:
                return False, None

        except Exception as error:
            return False, None

    async def update_domain_record_async(
        self,
        record_id: str,
        rr: str,
        type: str,
        value: str,
        ttl: int = 600,
        line: str = "default",
        priority: Optional[int] = None,
    ) -> tuple[bool, str]:
        """
        description:
            异步更新域名解析记录
        parameters:
            record_id: 记录ID
            rr: 主机记录，如 www, @, *
            type: 记录类型，如 A, CNAME, MX, TXT 等
            value: 记录值
            ttl: TTL值，默认600秒
            line: 解析线路，默认default
            priority: 优先级，仅MX记录需要
        return:
            success: 操作是否成功
            record_id: 记录ID
        """
        runtime = util_models.RuntimeOptions()
        try:
            request = alidns_20150109_models.UpdateDomainRecordRequest(
                record_id=record_id,
                rr=rr,
                type=type,
                value=value,
                ttl=ttl,
                line=line,
            )

            if priority is not None:
                request.priority = priority

            response = await self.client.update_domain_record_with_options_async(
                request, runtime
            )

            if response.body.record_id:
                return True, response.body.record_id
            else:
                return False, None

        except Exception as error:
            return False, None

    def find_record_by_rr_and_type(
        self, rr: str, type: str
    ) -> Optional[Dict[str, Any]]:
        """
        description:
            根据主机记录和记录类型查找记录
        parameters:
            rr: 主机记录
            type: 记录类型
        return:
            找到的记录字典，如果没找到返回None
        """
        records, success = self.list_domain_records()
        if not success:
            return None

        for record in records:
            if record.get("RR") == rr and record.get("Type") == type:
                return record
        return None

    async def find_record_by_rr_and_type_async(
        self, rr: str, type: str
    ) -> Optional[Dict[str, Any]]:
        """
        description:
            异步根据主机记录和记录类型查找记录
        parameters:
            rr: 主机记录
            type: 记录类型
        return:
            找到的记录字典，如果没找到返回None
        """
        records, success = await self.list_domain_records_async()
        if not success:
            return None

        for record in records:
            if record.get("RR") == rr and record.get("Type") == type:
                return record
        return None

    def delete_record_by_rr_and_type(self, rr: str, type: str) -> tuple[bool, str]:
        """
        description:
            根据主机记录和记录类型删除记录
        parameters:
            rr: 主机记录
            type: 记录类型
        return:
            success: 操作是否成功
        """
        record = self.find_record_by_rr_and_type(rr, type)
        if not record:
            return False

        record_id = record.get("RecordId")
        if not record_id:
            return False

        return self.delete_domain_record(record_id)

    async def delete_record_by_rr_and_type_async(
        self, rr: str, type: str
    ) -> tuple[bool, str]:
        """
        description:
            异步根据主机记录和记录类型删除记录
        parameters:
            rr: 主机记录
            type: 记录类型
        return:
            success: 操作是否成功
        """
        record = await self.find_record_by_rr_and_type_async(rr, type)
        if not record:
            return False

        record_id = record.get("RecordId")
        if not record_id:
            return False

        return await self.delete_domain_record_async(record_id)
