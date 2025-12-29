import random
import traceback
from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_tea_util import models as util_models
from pixelarraylib.monitor.feishu import Feishu
import asyncio

feishu_alert = Feishu("devtoolkit服务报警")


class SMSUtils:
    def __init__(self, access_key_id, access_key_secret):
        """
        description:
            初始化短信服务工具类
        parameters:
            access_key_id(str): 阿里云访问密钥ID
            access_key_secret(str): 阿里云访问密钥Secret
        """
        self.sms_cilent = Dysmsapi20170525Client(
            open_api_models.Config(
                type="access_key",
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                endpoint="dysmsapi.aliyuncs.com",
            )
        )

    def generate_verification_code(self, length=6):
        """
        description:
            生成数字验证码
        parameters:
            length(int): 验证码长度
        return:
            str: 验证码
        """
        return "".join(str(random.randint(0, 9)) for _ in range(length))

    def send_verification_code(self, phone_numbers, verification_code):
        """
        description:
            发送验证码给指定手机号
        parameters:
            phone_numbers(str): 手机号
            verification_code(str): 验证码（6位数字）
        return:
            flag(bool): 是否发送成功
        """
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            sign_name="北京矩阵像素科技有限公司",
            template_code="SMS_318235798",
            phone_numbers=phone_numbers,
            template_param=f'{{"code":"{verification_code}"}}',
        )
        runtime = util_models.RuntimeOptions()
        try:
            response = self.sms_cilent.send_sms_with_options(send_sms_request, runtime)
            flag = bool(
                response and response.status_code == 200 and response.body.code == "OK"
            )
            if not flag:
                print(f"短信发送失败: {response}")
            return flag
        except Exception as e:
            print("短信发送失败: " + traceback.format_exc())
            return False


class SMSUtilsAsync:
    def __init__(self, access_key_id, access_key_secret):
        """
        description:
            初始化异步短信服务工具类
        parameters:
            access_key_id(str): 阿里云访问密钥ID
            access_key_secret(str): 阿里云访问密钥Secret
        """
        self.sms_cilent = Dysmsapi20170525Client(
            open_api_models.Config(
                type="access_key",
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                endpoint="dysmsapi.aliyuncs.com",
            )
        )

    async def generate_verification_code(self, length=6):
        """
        description:
            生成数字验证码
        parameters:
            length(int): 验证码长度
        return:
            str: 验证码
        """
        return await asyncio.to_thread(
            lambda: "".join(str(random.randint(0, 9)) for _ in range(length))
        )

    async def send_verification_code(self, phone_numbers, verification_code):
        """
        description:
            发送验证码给指定手机号
        param:
            phone_numbers: 手机号
            verification_code: 验证码（6位数字）
        return:
            flag(bool): 是否发送成功
        """
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            sign_name="北京矩阵像素科技有限公司",
            template_code="SMS_318235798",
            phone_numbers=phone_numbers,
            template_param=f'{{"code":"{verification_code}"}}',
        )
        runtime = util_models.RuntimeOptions()
        try:
            response = await self.sms_cilent.send_sms_with_options_async(
                send_sms_request, runtime
            )
            flag = bool(
                response and response.status_code == 200 and response.body.code == "OK"
            )
            if not flag:
                print(f"短信发送失败: {response}")
            return flag
        except Exception as e:
            print("短信发送失败: " + traceback.format_exc())
            return False
