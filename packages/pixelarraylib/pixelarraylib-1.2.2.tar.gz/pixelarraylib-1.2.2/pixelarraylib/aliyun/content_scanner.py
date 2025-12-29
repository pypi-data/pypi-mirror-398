import json
import traceback
from typing import Union
from alibabacloud_green20220302.client import Client
from alibabacloud_green20220302.models import (
    TextModerationRequest,
    TextModerationPlusRequest,
    ImageModerationRequest,
    VideoModerationRequest,
    VideoModerationResultRequest,
    VoiceModerationRequest,
    VoiceModerationResultRequest,
)
from alibabacloud_tea_openapi.models import Config
from alibabacloud_tea_util import models as util_models
from pixelarraylib.monitor.feishu import Feishu
feishu_alert = Feishu("devtoolkit服务报警")

class ContentScanner:
    def __init__(self, access_key_id, access_key_secret, region_id):
        """
        description:
            初始化内容安全扫描工具类
        parameters:
            access_key_id(str): 阿里云访问密钥ID
            access_key_secret(str): 阿里云访问密钥Secret
            region_id(str): 阿里云区域ID
        """
        self.client = Client(
            Config(
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                region_id=region_id,
                connect_timeout=30000,
                read_timeout=60000,
                endpoint=f"green-cip.{region_id}.aliyuncs.com",
            )
        )

    def scan_text(
        self, content: str, service: str = "ugc_moderation_byllm", use_plus: bool = True
    ) -> Union[dict, bool]:
        """
        description:
            文本内容检测
        parameters:
            content(str): 要检测的文本内容，不同的service有不同的上限，具体可以查看官网
            service(str): 服务类型，可选值 comment_detection（普通版）, llm_query_moderation（Plus版）, ugc_moderation_byllm（Plus版）
            use_plus(bool): 是否使用Plus版API
        return:
            result(dict): 检测结果
            status(bool): 是否成功
        """

        if not content.strip():
            return {}, False

        try:
            if use_plus:
                response = self.client.text_moderation_plus(
                    TextModerationPlusRequest(
                        service=service,
                        service_parameters=json.dumps({"content": content}),
                    )
                )
            else:
                response = self.client.text_moderation_with_options(
                    TextModerationRequest(
                        service=service,
                        service_parameters=json.dumps({"content": content}),
                    ),
                    util_models.RuntimeOptions(
                        read_timeout=10000, connect_timeout=10000
                    ),
                )
            return (
                (response.body.to_map(), True)
                if response.status_code == 200
                else ({}, False)
            )
        except Exception as e:
            print(traceback.format_exc())
            return {}, False

    def scan_image(
        self, oss_region_id: str, oss_bucket_name: str, oss_object_key: str, service: str = "baselineCheck"
    ) -> Union[dict, bool]:
        """
        description:
            图片内容检测（同步方式）
        parameters:
            oss_region_id(str): 图片OSS地域ID
            oss_bucket_name(str): 图片OSS桶名
            oss_object_key(str): 图片OSS对象key
            service(str): 服务类型，可选值：enhance（增强版）, baselineCheck（基础版）
        return:
            result(dict): 检测结果
            status(bool): 是否成功
        """

        try:
            response = self.client.image_moderation_with_options(
                ImageModerationRequest(
                    service=service,
                    service_parameters=json.dumps(
                        {
                            "ossRegionId": oss_region_id,
                            "ossBucketName": oss_bucket_name,
                            "ossObjectName": oss_object_key,
                        }
                    ),
                ),
                util_models.RuntimeOptions(read_timeout=10000, connect_timeout=10000),
            )
            return (
                (response.body.to_map(), True)
                if response.status_code == 200
                else ({}, False)
            )
        except Exception as e:
            print(traceback.format_exc())
            return {}, False

    def scan_video(
        self, oss_region_id: str, oss_bucket_name: str, oss_object_key: str, service: str = "videoDetection"
    ) -> Union[dict, bool]:
        """
        description:
            视频内容异步检测
        parameters:
            oss_region_id(str): 视频OSS地域ID
            oss_bucket_name(str): 视频OSS桶名
            oss_object_key(str): 视频OSS对象key
            service(str): 服务类型，默认为"videoDetection"
        return:
            task_id(str): 任务ID
            status(bool): 是否成功
        """
        try:
            response = self.client.video_moderation_with_options(
                VideoModerationRequest(
                    service=service,
                    service_parameters=json.dumps(
                        {
                            "ossRegionId": oss_region_id,
                            "ossBucketName": oss_bucket_name,
                            "ossObjectName": oss_object_key,
                            "audioScenes": ["antispam"],
                            "scenes": ["porn", "terrorism"],
                            "bizType": "default",
                        }
                    ),
                ),
                util_models.RuntimeOptions(read_timeout=10000, connect_timeout=10000),
            )
            return (
                (response.body.to_map()["Data"]["TaskId"], True)
                if response.status_code == 200
                else ("", False)
            )
        except Exception as e:
            print(traceback.format_exc())
            return "", False

    def get_video_result(
        self, task_id: str, service: str = "videoDetection"
    ) -> Union[dict, bool]:
        """
        描述:
            获取视频内容检测结果
        参数:
            task_id(str): 任务ID
            service(str): 服务类型，默认为"videoDetection"
        返回:
            result(dict): 检测结果
            status(bool): 是否成功
        """
        try:
            response = self.client.video_moderation_result_with_options(
                VideoModerationResultRequest(
                    service=service,
                    service_parameters=json.dumps({"taskId": task_id}),
                ),
                util_models.RuntimeOptions(read_timeout=10000, connect_timeout=10000),
            )
            return (
                (response.body.to_map(), True)
                if response.status_code == 200
                else ({}, False)
            )
        except Exception as e:
            print(traceback.format_exc())
            return {}, False

    def scan_voice(
        self, oss_region_id: str, oss_bucket_name: str, oss_object_key: str, service: str = "audio_media_detection"
    ) -> Union[str, bool]:
        """
        描述:
            语音内容检测
        参数:
            oss_region_id(str): 语音OSS地域ID
            oss_bucket_name(str): 语音OSS桶名
            oss_object_key(str): 语音OSS对象key
            service(str): 服务类型，默认为"audio_media_detection"
        返回:
            task_id(str): 任务ID
            status(bool): 是否成功
        """
        try:
            response = self.client.voice_moderation_with_options(
                VoiceModerationRequest(
                    service=service,
                    service_parameters=json.dumps(
                        {
                            "ossRegionId": oss_region_id,
                            "ossBucketName": oss_bucket_name,
                            "ossObjectName": oss_object_key,
                        }
                    ),
                ),
                util_models.RuntimeOptions(read_timeout=10000, connect_timeout=10000),
            )
            return (
                (response.body.to_map()["Data"]["TaskId"], True)
                if response.status_code == 200
                else ("", False)
            )
        except Exception as e:
            print(traceback.format_exc())
            return "", False

    def get_voice_result(
        self, task_id: str, service: str = "audio_media_detection"
    ) -> Union[dict, bool]:
        """
        描述:
            获取语音内容检测结果
        参数:
            task_id(str): 任务ID
            service(str): 服务类型，默认为"audio_media_detection"
        返回:
            result(dict): 检测结果
            status(bool): 是否成功
        """
        try:
            response = self.client.voice_moderation_result_with_options(
                VoiceModerationResultRequest(
                    service=service,
                    service_parameters=json.dumps({"taskId": task_id}),
                ),
                util_models.RuntimeOptions(read_timeout=10000, connect_timeout=10000),
            )
            return (
                (response.body.to_map(), True)
                if response.status_code == 200
                else ({}, False)
            )
        except Exception as e:
            print(traceback.format_exc())
            return {}, False
