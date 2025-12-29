import asyncio
import os
import time
import random
import traceback
from alibabacloud_dm20151123.client import Client as Dm20151123Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dm20151123 import models as dm_20151123_models
from alibabacloud_tea_util import models as util_models
from pixelarraylib.monitor.feishu import Feishu

feishu_alert = Feishu("devtoolkit服务报警")


class AliyunEmailSender:
    def __init__(self, access_key_id, access_key_secret):
        """
        description:
            初始化阿里云邮件发送工具类
        parameters:
            access_key_id(str): 阿里云访问密钥ID
            access_key_secret(str): 阿里云访问密钥Secret
        """
        self.client = Dm20151123Client(
            open_api_models.Config(
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                endpoint="dm.aliyuncs.com",
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

    def create_verification_email_content(
        self, username, verification_code, email_type, validity=15
    ):
        """
        description:
            创建邮件HTML内容
        parameters:
            username(str): 用户名
            validity(int): 验证码有效期
        return:
            str: 邮件HTML内容
        """
        email_type_str = "注册" if email_type == "register" else "找回密码"
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e1e8f7; border-radius: 10px; }}
                .header {{ background: linear-gradient(to right, #1a2980, #26d0ce); color: white; padding: 15px; text-align: center; border-radius: 8px; }}
                .code {{ font-size: 28px; font-weight: bold; text-align: center; margin: 25px 0; letter-spacing: 5px; color: #e74c3c; }}
                .footer {{ margin-top: 30px; text-align: center; color: #777; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>北京矩阵像素科技有限公司</h2>
                </div>
                
                <p>尊敬的 <strong>{username}</strong>：</p>
                <p>您正在进行邮箱{email_type_str}验证，您的验证码为：</p>
                <div class="code">{verification_code}</div>
                <p>该验证码 <strong>{validity}分钟</strong> 内有效，请尽快完成验证。</p>
                <p>如非本人操作，请忽略此邮件。</p>
                
                <div class="footer">    
                    <p>阿里云邮件推送服务 | 安全验证</p>
                    <p>© {time.strftime('%Y')} 企业注册系统 版权所有</p>
                </div>
            </div>
        </body>
        </html>
        """

    def get_email_subject(self, email_type):
        if email_type == "register":
            return "您的注册验证码"
        elif email_type == "forgot":
            return "您的找回密码验证码"
        else:
            return "您的验证码"

    def send_verification_email(
        self, to_address, verification_code, email_type, username="用户"
    ):
        """
        description:
            发送验证邮件
        parameters:
            to_address(str): 收件人邮箱地址
            email_type(str): 邮件类型
            username(str): 用户名
        return:
            dict: 发送结果
        """
        assert email_type in [
            "register",
            "forgot",
        ], "邮件类型错误，当前只有register和forgot两种类型"
        try:
            response = self.client.single_send_mail_with_options(
                dm_20151123_models.SingleSendMailRequest(
                    account_name="captcha_new@captcha.pixelarrayai.com",
                    address_type=1,
                    to_address=to_address,
                    subject=self.get_email_subject(email_type),
                    html_body=self.create_verification_email_content(
                        username=username,
                        verification_code=verification_code,
                        email_type=email_type,
                    ),
                    reply_to_address=False,
                    from_alias="系统验证",  # 发信人昵称
                ),
                util_models.RuntimeOptions(),
            )
            if response.status_code == 200:
                return True
            else:
                print(f"发送验证邮件失败: {response}")
                return False

        except Exception as e:
            print(traceback.format_exc())
            return False


class AliyunEmailSenderAsync:
    def __init__(self, access_key_id, access_key_secret):
        self.client = Dm20151123Client(
            open_api_models.Config(
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                endpoint="dm.aliyuncs.com",
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

    def create_verification_email_content(
        self, username, verification_code, email_type, validity=15
    ):
        """
        description:
            创建邮件HTML内容
        parameters:
            username(str): 用户名
            validity(int): 验证码有效期
        return:
            str: 邮件HTML内容
        """
        email_type_str = "注册" if email_type == "register" else "找回密码"
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e1e8f7; border-radius: 10px; }}
                .header {{ background: linear-gradient(to right, #1a2980, #26d0ce); color: white; padding: 15px; text-align: center; border-radius: 8px; }}
                .code {{ font-size: 28px; font-weight: bold; text-align: center; margin: 25px 0; letter-spacing: 5px; color: #e74c3c; }}
                .footer {{ margin-top: 30px; text-align: center; color: #777; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>北京矩阵像素科技有限公司</h2>
                </div>
                
                <p>尊敬的 <strong>{username}</strong>：</p>
                <p>您正在进行邮箱{email_type_str}验证，您的验证码为：</p>
                <div class="code">{verification_code}</div>
                <p>该验证码 <strong>{validity}分钟</strong> 内有效，请尽快完成验证。</p>
                <p>如非本人操作，请忽略此邮件。</p>
                
                <div class="footer">    
                    <p>阿里云邮件推送服务 | 安全验证</p>
                    <p>© {time.strftime('%Y')} 企业注册系统 版权所有</p>
                </div>
            </div>
        </body>
        </html>
        """

    def get_email_subject(self, email_type):
        if email_type == "register":
            return "您的注册验证码"
        elif email_type == "forgot":
            return "您的找回密码验证码"
        else:
            return "您的验证码"

    async def send_verification_email(
        self, to_address, verification_code, email_type, username="用户"
    ):
        """
        description:
            发送验证邮件
        parameters:
            to_address(str): 收件人邮箱地址
            email_type(str): 邮件类型
            username(str): 用户名
        return:
            dict: 发送结果
        """
        assert email_type in [
            "register",
            "forgot",
        ], "邮件类型错误，当前只有register和forgot两种类型"
        try:
            response = await self.client.single_send_mail_with_options_async(
                dm_20151123_models.SingleSendMailRequest(
                    account_name="captcha_new@captcha.pixelarrayai.com",
                    address_type=1,
                    to_address=to_address,
                    subject=self.get_email_subject(email_type),
                    html_body=self.create_verification_email_content(
                        username=username,
                        verification_code=verification_code,
                        email_type=email_type,
                    ),
                    reply_to_address=False,
                    from_alias="系统验证",  # 发信人昵称
                ),
                util_models.RuntimeOptions(),
            )
            if response.status_code == 200:
                return True
            else:
                print(f"发送验证邮件失败: {response}")
                return False

        except Exception as e:
            print(traceback.format_exc())
            return False
