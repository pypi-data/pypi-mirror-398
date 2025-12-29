import json
from operator import contains
import traceback
from typing import Optional, Dict, Any, List
from alibabacloud_eci20180808.client import Client as EciClient
from alibabacloud_eci20180808.models import (
    CreateContainerGroupRequest,
    DescribeAvailableResourceRequestDestinationResource,
    DescribeContainerGroupsRequest,
    CreateContainerGroupRequestContainer,
    CreateContainerGroupRequestImageRegistryCredential,
    CreateContainerGroupRequestTag,
    DescribeRegionsRequest,
    DescribeAvailableResourceRequest,
    DeleteContainerGroupRequest,
)
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from pixelarraylib.monitor.feishu import Feishu
from pixelarraylib.aliyun.eip import EIPUtils

feishu_alert = Feishu("devtoolkit服务报警")


class ECIUtils:
    def __init__(self, region_id: str, access_key_id: str, access_key_secret: str):
        """
        description:
            初始化ECI工具类
        parameters:
            region_id(str): 地域ID
            access_key_id(str): 访问密钥ID
            access_key_secret(str): 访问密钥Secret
        """
        self.region_id = region_id
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.client = self._create_client()
        self.eip_utils = EIPUtils(
            region_id=region_id,
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
        )

    def _create_client(self) -> EciClient:
        """
        description:
            创建ECI客户端
        return:
            EciClient: ECI客户端实例
        """
        config = open_api_models.Config(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
            region_id=self.region_id,
            endpoint=f"eci.{self.region_id}.aliyuncs.com",
        )
        return EciClient(config)

    def describe_available_resource(self, cpu: float, memory: float) -> Dict[str, Any]:
        """
        description:
            查询可用资源
        parameters:
            cpu(float): CPU
            memory(float): 内存
        return:
            dict: 查询结果
        """
        try:
            describe_zones_request = DescribeAvailableResourceRequest(
                region_id=self.region_id,
                destination_resource=DescribeAvailableResourceRequestDestinationResource(
                    category="InstanceType",
                    cores=cpu,
                    memory=memory,
                ),
            )
            runtime = util_models.RuntimeOptions()
            response = self.client.describe_available_resource_with_options(
                describe_zones_request, runtime
            )
            return response.body.to_map(), True
        except Exception as error:
            print(f"查询可用资源失败: {error}")
            return {}

    def create_container_group(
        self,
        container_group_name: str,
        acr_credentials: Dict,
        images: List[Dict[str, Any]],
        cpu: float,
        memory: float,
        restart_policy: str = "Always",
        allocate_public_ip: bool = True,
    ):
        """
        description:
            创建容器组
        parameters:
            container_group_name(str): 容器组名称
            acr_credentials(Dict): ACR凭证
            images(List[Dict[str, Any]]): 镜像列表
            cpu(float): CPU
            memory(float): 内存
            restart_policy(str): 重启策略
            allocate_public_ip(bool): 是否分配公网IP
        return:
            dict: 创建结果
            success(bool): 是否成功
        """
        containers = []
        for image in images:
            container_0 = CreateContainerGroupRequestContainer(
                name=image["repository_name"],
                image=f"pixelarrayai-registry.{self.region_id}.cr.aliyuncs.com/{image['namespace_name']}/{image['repository_name']}:latest",
            )
            containers.append(container_0)

        image_registry_credentials = [
            CreateContainerGroupRequestImageRegistryCredential(
                password=acr_credentials["password"],
                server=f"pixelarrayai-registry.{self.region_id}.cr.aliyuncs.com",
                user_name=acr_credentials["username"],
            )
        ]

        tag_0 = CreateContainerGroupRequestTag(key="team", value="pixelarrayai")

        if allocate_public_ip:
            response, success = self.eip_utils.allocate_eip()
            if not success:
                print(f"创建容器组失败: 分配公网IP失败")
                return {}, False
            eip_instance_id = response["AllocationId"]
        else:
            eip_instance_id = None

        create_container_group_request = CreateContainerGroupRequest(
            region_id=self.region_id,
            container_group_name=container_group_name,
            restart_policy=restart_policy,
            cpu=cpu,
            memory=memory,
            dns_policy="Default",
            active_deadline_seconds=600,
            spot_strategy="SpotAsPriceGo",
            tag=[tag_0],
            image_registry_credential=image_registry_credentials,
            termination_grace_period_seconds=60,
            container=containers,
            auto_match_image_cache=False,
            share_process_namespace=True,
            schedule_strategy="VSwitchOrdered",
            eip_instance_id=eip_instance_id,
        )
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
            response = self.client.create_container_group_with_options(
                create_container_group_request, runtime
            )
            return response.body.to_map(), True
        except Exception as error:
            print(f"创建容器组失败: {error}")
            return {}, False

    def describe_container_group(self, container_group_id: str):
        """
        description:
            查询容器组
        parameters:
            container_group_id(str): 容器组ID
        return:
            dict: 查询结果
        """
        try:
            describe_container_groups_request = DescribeContainerGroupsRequest(
                container_group_ids=[container_group_id],
                region_id=self.region_id,
            )
            runtime = util_models.RuntimeOptions()
            response = self.client.describe_container_groups_with_options(
                describe_container_groups_request, runtime
            )
            return response.body.to_map()
        except Exception as error:
            print(f"查询容器组失败: {error}")
            return {}

    def list_container_groups(self):
        """
        description:
            查询容器组列表
        parameters:
            None
        return:
            dict: 查询结果
        """
        try:
            describe_container_groups_request = DescribeContainerGroupsRequest(
                region_id=self.region_id
            )
            runtime = util_models.RuntimeOptions()
            response = self.client.describe_container_groups_with_options(
                describe_container_groups_request, runtime
            )
            return response.body.to_map()
        except Exception as error:
            print(f"查询容器组列表失败: {error}")
            return {}

    def delete_container_group(self, container_group_id: str):
        """
        description:
            删除容器组
        parameters:
            container_group_id(str): 容器组ID
        return:
            dict: 删除结果
            success(bool): 是否成功
        """
        try:
            delete_container_group_request = DeleteContainerGroupRequest(
                container_group_id=container_group_id,
                region_id=self.region_id,
            )
            runtime = util_models.RuntimeOptions()
            response = self.client.delete_container_group_with_options(
                delete_container_group_request, runtime
            )
            return response.body.to_map(), True
        except Exception as error:
            print(f"删除容器组失败: {error}")
            return {}, False
