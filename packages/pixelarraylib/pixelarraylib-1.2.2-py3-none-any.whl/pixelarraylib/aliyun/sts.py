import traceback
import json
import oss2
from alibabacloud_sts20150401.client import Client as StsClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_sts20150401 import models as sts_20150401_models
from alibabacloud_tea_util import models as util_models
from pixelarraylib.monitor.feishu import Feishu
from pixelarraylib.db_utils.redis import RedisUtils

feishu_alert = Feishu("devtoolkit服务报警")


class STSUtils:
    def __init__(
        self, access_key_id, access_key_secret, role_arn, region_id, bucket_name, redis_utils
    ):
        """
        description:
            初始化STS（安全令牌服务）工具类
        parameters:
            access_key_id(str): 阿里云访问密钥ID
            access_key_secret(str): 阿里云访问密钥Secret
            role_arn(str): 角色ARN
            region_id(str): 阿里云区域ID
            bucket_name(str): OSS存储桶名称
            redis_utils(RedisUtils): Redis工具类实例，用于缓存STS令牌
        """
        assert isinstance(redis_utils, RedisUtils), "redis_utils must be a RedisUtils instance"
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.role_arn = role_arn
        # 使用新版本的STS客户端
        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            region_id=region_id,
        )
        self.client = StsClient(config)
        self.redis_utils = redis_utils
        self.bucket_name = bucket_name
        self.oss_endpoint = f"https://oss-{region_id}.aliyuncs.com"
        self.region_id = region_id

    def get_sts_token(self, role_session_name, duration_seconds=3600):
        """
        description:
            获取STS临时访问凭证
        parameters:
            role_session_name(str): 角色会话名称
            duration_seconds(int): 临时凭证有效期，单位为秒
        return:
            credentials(dict): 临时访问凭证
            flag(bool): 是否成功
        """
        assert role_session_name in ["oss-session"]
        try:
            credentials = self.redis_utils.get(f"sts_auth_token_{role_session_name}")
            if credentials:
                return json.loads(credentials), True

            assume_role_request = sts_20150401_models.AssumeRoleRequest(
                role_arn=self.role_arn,
                role_session_name=role_session_name,
                duration_seconds=duration_seconds,
            )

            response = self.client.assume_role_with_options(
                assume_role_request, util_models.RuntimeOptions()
            )

            credentials = response.to_map()["body"]["Credentials"]

            access_key_id = credentials["AccessKeyId"]
            access_key_secret = credentials["AccessKeySecret"]
            security_token = credentials["SecurityToken"]

            credentials = {
                "access_key_id": access_key_id,
                "access_key_secret": access_key_secret,
                "security_token": security_token,
            }
            self.redis_utils.set(
                f"sts_auth_token_{role_session_name}",
                json.dumps(credentials),
                expire_seconds=duration_seconds,
            )
            return credentials, True
        except Exception as e:
            print(traceback.format_exc())
            return {}, False

    def get_oss_sts_client(self, endpoint, bucket_name):
        """
        description:
            获取基于STS的OSS客户端
        return:
            bucket(oss2.Bucket): OSS客户端
            flag(bool): 是否成功
        """
        try:
            credentials, flag = self.get_sts_token("oss-session")
            if not credentials or not flag:
                return None, False

            auth = oss2.StsAuth(
                credentials["access_key_id"],
                credentials["access_key_secret"],
                credentials["security_token"],
            )
            return oss2.Bucket(auth, endpoint, bucket_name), True
        except Exception as e:
            print(traceback.format_exc())
            return None, False

    def generate_presigned_url(self, prefix, expires_in=60 * 60 * 24):
        """
        description:
            使用STS生成预签名URL
        parameters:
            prefix(str): 前缀
            expires_in(int): 过期时间，默认24小时
        return:
            url(str): 预签名URL
        """
        try:
            sts_oss_client, sts_flag = self.get_oss_sts_client(
                self.oss_endpoint, self.bucket_name
            )
            if not sts_oss_client or not sts_flag:
                return ""
            return sts_oss_client.sign_url("GET", prefix, expires_in)
        except Exception as e:
            print(traceback.format_exc())
            return ""
