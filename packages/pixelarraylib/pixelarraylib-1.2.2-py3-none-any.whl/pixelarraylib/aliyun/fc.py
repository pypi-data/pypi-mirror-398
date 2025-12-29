import json
import os
from tempfile import TemporaryDirectory
import traceback

from alibabacloud_fc20230330.client import Client as FC20230330Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_darabonba_stream.client import Client as StreamClient
from alibabacloud_fc20230330 import models as fc20230330_models
from alibabacloud_tea_util import models as util_models
from pixelarraylib.monitor.feishu import Feishu
from pixelarraylib.system.common import execute_command, file_to_base64

feishu_alert = Feishu("devtoolkit服务报警")


class FCUtils:
    def __init__(self, access_key_id, access_key_secret, account_id, region_id):
        """
        description:
            初始化函数计算（FC）工具类
        parameters:
            access_key_id(str): 阿里云访问密钥ID
            access_key_secret(str): 阿里云访问密钥Secret
            account_id(str): 阿里云账号ID
            region_id(str): 阿里云区域ID
        """
        self.client = FC20230330Client(
            open_api_models.Config(
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                endpoint=f"{account_id}.{region_id}.fc.aliyuncs.com",
            )
        )

    def invoke_function(
        self,
        function_name: str,
        params: dict,
        retry: int = 5,
        timeout: int = 6000 * 1000,
    ) -> tuple[str, bool]:
        """
        description:
            调用函数计算服务中的函数
        parameters:
            function_name(str): 函数名称
            params(dict): 函数参数
            retry(int): 重试次数，默认为5
            timeout(int): 超时时间（毫秒），默认为6000秒
        return:
            result(str): 函数执行结果
            success(bool): 是否调用成功
        """
        last_exception = None
        for i in range(retry):
            try:
                body_stream = StreamClient.read_from_string(json.dumps(params))
                invoke_function_headers = fc20230330_models.InvokeFunctionHeaders(
                    x_fc_invocation_type="Sync", x_fc_log_type="None"
                )
                invoke_function_request = fc20230330_models.InvokeFunctionRequest(
                    qualifier="LATEST", body=body_stream
                )

                runtime = util_models.RuntimeOptions()
                runtime.connect_timeout = 60
                runtime.read_timeout = timeout
                response = self.client.invoke_function_with_options(
                    function_name,
                    invoke_function_request,
                    invoke_function_headers,
                    runtime,
                )
                if not response or response.status_code != 200:
                    last_exception = f"aliyun fc invoke_function error: {i} {response}"
                    # 如果不是最后一次重试，则继续重试
                    if i < retry - 1:
                        continue
                    else:
                        return None, False
                return response.body.read().decode(), True
            except Exception as e:
                last_exception = (
                    f"aliyun fc invoke_function error: {i} {traceback.format_exc()}"
                )
                # 如果不是最后一次重试，则继续重试
                if i < retry - 1:
                    continue
                else:
                    return None, False
        # 如果所有重试都失败，返回最后一次的异常信息
        print(
            f"aliyun fc invoke_function failed after {retry} retries. Last error: {last_exception}"
        )
        return None, False

    def update_function(
        self,
        function_name: str,
        dir_path: str,
        retry: int = 5,
    ) -> tuple[str, bool]:
        """
        description:
            更新函数计算服务中的函数代码
        parameters:
            function_name(str): 函数名称
            dir_path(str): 代码目录路径
            retry(int): 重试次数，默认为5
        return:
            success(bool): 是否更新成功
        """
        last_exception = None
        for i in range(retry):
            try:
                update_function_input_vpcconfig = fc20230330_models.VPCConfig(
                    security_group_id="sg-2ze2gmwyq9wxt34xbbli",
                    v_switch_ids=["vsw-2ze0wbhhcu9c0veyf2y1m"],
                    vpc_id="vpc-2zewkxvljq1091qa8x1um",
                )
                with TemporaryDirectory() as temp_dir:
                    code_zip_path = os.path.join(temp_dir, "code.zip")
                    _, success = execute_command(["zip", "-r", code_zip_path, dir_path])
                    if not success:
                        continue
                    update_function_input_input_code_location = (
                        fc20230330_models.InputCodeLocation(
                            zip_file=file_to_base64(code_zip_path)
                        )
                    )
                update_function_input = fc20230330_models.UpdateFunctionInput(
                    handler="index.handler",
                    code=update_function_input_input_code_location,
                    timeout=6000,
                    disk_size=10240,
                    internet_access=True,
                    cpu=16,
                    runtime="python3.12",
                    instance_concurrency=1,
                    memory_size=16384,
                    vpc_config=update_function_input_vpcconfig,
                )
                update_function_request = fc20230330_models.UpdateFunctionRequest(
                    body=update_function_input
                )
                runtime = util_models.RuntimeOptions()
                headers = {}
                response = self.client.update_function_with_options(
                    function_name, update_function_request, headers, runtime
                )
                if not response or response.status_code != 200:
                    last_exception = f"aliyun fc update_function error: {i} {response}"
                    # 如果不是最后一次重试，则继续重试
                    if i < retry - 1:
                        continue
                    else:
                        return False
                return True
            except Exception as e:
                last_exception = (
                    f"aliyun fc update_function error: {i} {traceback.format_exc()}"
                )
                # 如果不是最后一次重试，则继续重试
                if i < retry - 1:
                    continue
                else:
                    return False
        # 如果所有重试都失败，返回最后一次的异常信息
        print(
            f"aliyun fc update_function failed after {retry} retries. Last error: {last_exception}"
        )
        return False
