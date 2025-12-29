from datetime import datetime, timedelta
import json
from alibabacloud_cms20190101.client import Client as Cms20190101Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_cms20190101 import models as cms_20190101_models
from alibabacloud_tea_util import models as util_models


class ECSUtils:
    def __init__(self, access_key_id: str, access_key_secret: str, region_id: str):
        """
        description:
            初始化ECS（弹性计算服务）工具类
        parameters:
            access_key_id(str): 阿里云访问密钥ID
            access_key_secret(str): 阿里云访问密钥Secret
            region_id(str): 阿里云区域ID
        """
        self.cms_client = Cms20190101Client(
            open_api_models.Config(
                type="access_key",
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                endpoint=f"metrics.{region_id}.aliyuncs.com",
            )
        )

    def get_memory_utilization(self, instance_id: str, delta_minutes: int = 1) -> float:
        """
        description:
            获取实例的内存使用率
        parameters:
            instance_id(str): 实例ID
            delta_minutes(int): 时间差 默认1分钟
        return:
            memory_utilization(float): 内存使用率 取值范围0-1
        """
        describe_metric_list_request = cms_20190101_models.DescribeMetricListRequest(
            namespace="acs_ecs_dashboard",
            metric_name="memory_usedutilization",
            dimensions=f'{{"instanceId": "{instance_id}"}}',
            start_time=datetime.now() - timedelta(minutes=delta_minutes),
            end_time=datetime.now(),
        )
        runtime = util_models.RuntimeOptions()
        response = self.cms_client.describe_metric_list_with_options(
            describe_metric_list_request, runtime
        )
        monitor_list = json.loads(response.body.datapoints)
        max_value = max(monitor_list, key=lambda x: x["timestamp"])
        return max_value["Average"] * 0.01

    def get_cpu_utilization(self, instance_id: str, delta_minutes: int = 1) -> float:
        """
        description:
            获取实例的CPU使用率
        parameters:
            instance_id(str): 实例ID
            delta_minutes(int): 时间差 默认1分钟
        return:
            cpu_utilization(float): 内存使用率 取值范围0-1
        """
        describe_metric_list_request = cms_20190101_models.DescribeMetricListRequest(
            namespace="acs_ecs_dashboard",
            metric_name="CPUUtilization",
            dimensions=f'{{"instanceId": "{instance_id}"}}',
            start_time=datetime.now() - timedelta(minutes=delta_minutes),
            end_time=datetime.now(),
        )
        runtime = util_models.RuntimeOptions()
        response = self.cms_client.describe_metric_list_with_options(
            describe_metric_list_request, runtime
        )
        monitor_list = json.loads(response.body.datapoints)
        max_value = max(monitor_list, key=lambda x: x["timestamp"])
        return max_value["Average"] * 0.01
