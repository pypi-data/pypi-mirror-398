import os
import json
import traceback
import oss2
import hmac
import base64
import aiohttp
import asyncio
import xml.etree.ElementTree as ET
import requests
from hashlib import sha1
from datetime import datetime
from urllib.parse import quote, urlencode
from datetime import datetime
from pixelarraylib.system.common import size_unit_convert, percentage
from pixelarraylib.monitor.feishu import Feishu
import aiofiles
from concurrent.futures import ThreadPoolExecutor


feishu_alert = Feishu("devtoolkit服务报警")


class OSSUtils:
    def __init__(
        self,
        access_key_id,
        access_key_secret,
        region_id,
        bucket_name,
        use_vpc=False,
    ):
        """
        description:
            初始化OSS工具类
        parameters:
            access_key_id(str): 阿里云访问密钥ID
            access_key_secret(str): 阿里云访问密钥Secret
            region_id(str): 阿里云区域ID
            bucket_name(str): OSS存储桶名称
            use_vpc(bool): 是否使用VPC内网端点，默认为False
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.bucket_name = bucket_name
        if use_vpc:
            self.endpoint = f"https://oss-{region_id}-internal.aliyuncs.com"
        else:
            self.endpoint = f"https://oss-{region_id}.aliyuncs.com"
        self.client = self.get_oss_client(
            access_key_id, access_key_secret, self.endpoint, bucket_name
        )
        # 创建oss2的Auth对象用于签名
        self.auth = oss2.Auth(access_key_id, access_key_secret)

    def get_oss_client(
        self, access_key_id, access_key_secret, endpoint, bucket_name, retry=3
    ):
        """
        description:
            获取OSS客户端
        parameters:
            access_key_id(str): 阿里云access_key_id
            access_key_secret(str): 阿里云access_key_secret
            endpoint(str): 阿里云endpoint
            bucket_name(str): 阿里云bucket_name
        return:
            bucket(oss2.Bucket): OSS客户端
        """
        for _ in range(retry):
            try:
                return oss2.Bucket(
                    oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name
                )
            except Exception as e:
                print(e)
        return None

    def _sign_request(self, method, url, headers=None, params=None):
        """
        description:
            使用oss2库生成OSS签名
        parameters:
            method(str): HTTP方法
            url(str): 请求URL
            headers(dict): 请求头
            params(dict): 请求参数
        return:
            headers(dict): 包含签名的请求头
        """
        if headers is None:
            headers = {}
        if params is None:
            params = {}

        # 创建oss2的Request对象
        req = oss2.http.Request(method, url, params=params, headers=headers)

        # 使用oss2的签名功能
        self.auth._sign_request(req, "", "")

        # 过滤掉None键和None值
        result = {}
        for k, v in req.headers.items():
            if k is not None and v is not None:
                result[str(k)] = str(v)
        return result

    def list_regions(self):
        """
        description:
            列出OSS支持的区域
        return:
            regions(list): 区域列表，每个元素为字典，包含 region_id, region_name, internal_endpoint, internet_endpoint
        """
        try:
            # 使用通用的OSS endpoint来获取区域列表
            url = "https://oss-cn-hangzhou.aliyuncs.com/?regions"
            
            # 生成签名
            headers = self._sign_request("GET", url)
            
            # 发送请求
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # 解析XML响应
            root = ET.fromstring(response.text)
            regions = []
            
            # 查找所有 RegionInfo 元素
            for region_info_elem in root.findall(".//RegionInfo"):
                region_elem = region_info_elem.find("Region")
                internal_endpoint_elem = region_info_elem.find("InternalEndpoint")
                internet_endpoint_elem = region_info_elem.find("InternetEndpoint")
                
                region_id = region_elem.text if region_elem is not None else ""
                # 从 region_id 中提取区域名称（去掉 oss- 前缀）
                region_name = region_id.replace("oss-", "") if region_id else None
                internal_endpoint = internal_endpoint_elem.text if internal_endpoint_elem is not None else None
                internet_endpoint = internet_endpoint_elem.text if internet_endpoint_elem is not None else None
                
                if region_id:
                    regions.append({
                        "region_id": region_id,
                        "region_name": region_name,
                        "internal_endpoint": internal_endpoint,
                        "internet_endpoint": internet_endpoint
                    })
            self.regions = regions
            return regions
        except Exception as e:
            print(f"list_regions error: {traceback.format_exc()}, {e}")
            self.regions = []
            return []

    def list_region_ids(self):
        """
        description:
            列出OSS支持的区域ID
        return:
            region_ids(list): 区域ID列表
        """
        regions = self.list_regions()
        return [region["region_id"] for region in regions]

    def list_objects(self, prefix, batch_size=100):
        """
        description:
            列出OSS中的对象，返回生成器
        parameters:
            prefix(str): 前缀
            batch_size(int): 每批返回的对象数量
        return:
            generator: 对象列表生成器
        """
        next_marker = ""
        while True:
            object_list = self.client.list_objects(
                prefix=prefix, marker=next_marker, max_keys=batch_size
            )
            for obj in object_list.object_list:
                if obj.size > 0:
                    yield obj
            if not object_list.is_truncated:
                break
            next_marker = object_list.next_marker

    def is_object(self, key):
        """
        description:
            判断某个对象是否在OSS中存在
        parameters:
            key(str): 对象的key
        return:
            flag(bool): 是否存在
        """
        try:
            return self.client.object_exists(key)
        except Exception as e:
            print(e)
            return False

    def get_size(self, prefix, unit="B"):
        """
        description:
            获取OSS中对象或前缀下所有对象的大小
        parameters:
            prefix(str): 前缀
            unit(str): 单位，默认B
        return:
            size(int): 对象或前缀下所有对象的大小
            count(int): 对象或前缀下所有对象的个数
        """
        object_list = self.list_objects(prefix)
        total_size = 0
        object_count = 0
        for obj in object_list:
            total_size += self.client.get_object_meta(obj.key).content_length
            object_count += 1

        return (
            size_unit_convert(total_size, input_unit="B", output_unit=unit),
            object_count,
        )

    def delete(self, prefix):
        """
        description:
            删除OSS中的对象或前缀
        parameters:
            prefix(str): 对象或前缀的key
        return:
            flag(bool): 是否删除成功
        """
        try:
            for obj in self.list_objects(prefix):
                self.client.delete_object(obj.key)
            return True
        except Exception as e:
            print(traceback.format_exc())
            return False

    def ls(self, prefix):
        """
        description:
            列出当前目录下的所有文件夹和文件的key
        parameters:
            prefix(str): 前缀
        return:
            key_list(list): 文件夹和文件的key列表
        """
        if not prefix.endswith("/"):
            prefix += "/"

        key_list = []
        next_marker = ""

        while True:
            result = self.client.list_objects(
                prefix=prefix, marker=next_marker, max_keys=1000, delimiter="/"
            )

            key_list.extend(
                [{"type": "directory", "key": p} for p in result.prefix_list]
            )
            key_list.extend(
                [{"type": "file", "key": obj.key} for obj in result.object_list]
            )

            if not result.is_truncated:
                break
            next_marker = result.next_marker

        return [key for key in key_list if key["key"] != prefix]

    def get_last_modified(self, prefix):
        """
        description:
            获取OSS中对象或前缀下所有对象的最后修改时间
        parameters:
            prefix(str): 前缀
        return:
            last_modified(str): 最后修改时间
        """
        if self.is_object(prefix):
            obj_key = prefix
        else:
            obj_key = max(
                self.list_objects(prefix),
                key=lambda x: self.client.get_object_meta(x.key).last_modified,
            ).key

        return datetime.fromtimestamp(
            self.client.get_object_meta(obj_key).last_modified
        ).strftime("%Y-%m-%d %H:%M:%S")

    def path_exists(self, prefix):
        """
        description:
            检查OSS中对象或前缀是否存在
        parameters:
            prefix(str): 前缀
        return:
            flag(bool): 是否存在
        """
        try:
            for obj in self.list_objects(prefix):
                return True
            return False
        except Exception as e:
            print(traceback.format_exc())
            return False

    def download_object(self, prefix, dir_path):
        """
        description:
            下载OSS中的对象
        parameters:
            prefix(str): 前缀
            local_path(str): 本地文件路径
        return:
            flag(bool): 是否下载成功
        """
        if not dir_path:
            dir_path = "."
        if not self.is_object(prefix):
            return False
        file_name = os.path.basename(prefix)
        os.makedirs(dir_path, exist_ok=True)
        download_path = os.path.join(dir_path, file_name)
        print("download_path", download_path)
        try:
            self.client.get_object_to_file(prefix, download_path)
            return True
        except Exception as e:
            print(f"oss download_object error: {traceback.format_exc()}")
            return False

    def upload_object(self, prefix, local_path):
        """
        description:
            上传对象到OSS
        parameters:
            prefix(str): 前缀
            local_path(str): 本地文件路径
        return:
            flag(bool): 是否上传成功
        """
        if not os.path.exists(local_path):
            print(f"文件 {local_path} 不存在，请检查！")
            return False

        file_name = os.path.basename(local_path)
        try:
            self.client.put_object_from_file(
                os.path.join(prefix, file_name), local_path
            )
            return True
        except Exception as e:
            print(traceback.format_exc())
            return False

    def copy_object(self, prefix, target_prefix):
        """
        description:
            复制对象
        parameters:
            prefix(str): 前缀
            target_prefix(str): 目标前缀
        """
        try:
            self.client.copy_object(
                source_bucket_name=self.bucket_name,
                source_key=prefix,
                target_key=target_prefix,
            )
            return True
        except Exception as e:
            print(traceback.format_exc())
            return False

    def generate_presigned_url(self, prefix, expires_in=60 * 60 * 24):
        """
        description:
            使用OSS生成预签名URL
        parameters:
            prefix(str): 前缀
            expires_in(int): 过期时间，默认24小时
        return:
            url(str): 预签名URL
        """
        return self.client.sign_url("GET", prefix, expires_in)


class OSSObject:
    """OSS 对象表示类"""

    def __init__(self, key, size, last_modified, etag=None):
        self.key = key
        self.size = size
        self.last_modified = last_modified
        self.etag = etag


class OSSRegion:
    """OSS 区域表示类"""

    def __init__(self, region_id, region_name=None, internal_endpoint=None, internet_endpoint=None):
        self.region_id = region_id
        self.region_name = region_name
        self.internal_endpoint = internal_endpoint
        self.internet_endpoint = internet_endpoint

    def __repr__(self):
        return f"OSSRegion(region_id='{self.region_id}', region_name='{self.region_name}', internet_endpoint='{self.internet_endpoint}')"


class OSSUtilsAsync:
    def __init__(
        self, access_key_id, access_key_secret, region_id, bucket_name, use_vpc=False
    ):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.bucket_name = bucket_name
        if use_vpc:
            self.endpoint = (
                f"https://{self.bucket_name}.oss-{region_id}-internal.aliyuncs.com"
            )
        else:
            self.endpoint = f"https://{self.bucket_name}.oss-{region_id}.aliyuncs.com"
        self.base_url = self.endpoint
        self.session = None
        self.thread_pool = ThreadPoolExecutor(max_workers=4)

        # 创建oss2的Auth对象用于签名
        self.auth = oss2.Auth(access_key_id, access_key_secret)

        # 创建oss2的Bucket对象用于同步操作
        correct_endpoint = self.endpoint.replace(f"{self.bucket_name}.", "")
        self.oss_bucket = oss2.Bucket(self.auth, correct_endpoint, self.bucket_name)

    async def _ensure_session(self):
        """确保 aiohttp 会话已创建"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """关闭 aiohttp 会话和线程池"""
        if self.session is not None:
            await self.session.close()
            self.session = None
        if self.thread_pool is not None:
            self.thread_pool.shutdown(wait=True)
            self.thread_pool = None

    async def _run_in_thread(self, func, *args, **kwargs):
        """在线程池中运行同步函数"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, func, *args, **kwargs)

    def _sign_request(self, method, url, headers=None, params=None):
        """使用oss2库生成OSS签名"""
        if headers is None:
            headers = {}
        if params is None:
            params = {}

        # 创建oss2的Request对象
        req = oss2.http.Request(method, url, params=params, headers=headers)

        # 使用oss2的签名功能
        self.auth._sign_request(req, self.bucket_name, "")

        # 过滤掉None键和None值
        result = {}
        for k, v in req.headers.items():
            if k is not None and v is not None:
                result[str(k)] = str(v)
        return result

    def _parse_list_objects_xml(self, xml_text):
        """解析 OSS ListObjects 响应的 XML"""
        try:
            root = ET.fromstring(xml_text)
            objects = []

            # 查找所有 Contents 元素（不使用命名空间）
            for contents in root.findall(".//Contents"):
                key_elem = contents.find("Key")
                size_elem = contents.find("Size")
                last_modified_elem = contents.find("LastModified")
                etag_elem = contents.find("ETag")

                if key_elem is not None and size_elem is not None:
                    # URL解码key
                    from urllib.parse import unquote

                    key = unquote(key_elem.text) if key_elem.text else ""
                    size = int(size_elem.text) if size_elem.text else 0
                    last_modified = (
                        last_modified_elem.text
                        if last_modified_elem is not None
                        else None
                    )
                    etag = etag_elem.text if etag_elem is not None else None

                    # 只返回大小大于0的对象（排除目录）
                    if size > 0:
                        objects.append(OSSObject(key, size, last_modified, etag))

            return objects
        except ET.ParseError as e:
            print(f"XML 解析错误: {e}")
            return []

    def _parse_ls_xml(self, xml_text, prefix):
        """解析 OSS ListObjects 响应的 XML (用于 ls 方法)"""
        try:
            root = ET.fromstring(xml_text)
            key_list = []

            # 查找所有 CommonPrefixes 元素 (目录) - 不使用命名空间
            for prefix_elem in root.findall(".//CommonPrefixes"):
                prefix_text = prefix_elem.find("Prefix")
                if prefix_text is not None and prefix_text.text != prefix:
                    # URL解码key，与同步版本保持一致
                    from urllib.parse import unquote

                    decoded_key = unquote(prefix_text.text)
                    key_list.append({"type": "directory", "key": decoded_key})

            # 查找所有 Contents 元素 (文件) - 不使用命名空间
            for contents in root.findall(".//Contents"):
                key_elem = contents.find("Key")
                if key_elem is not None and key_elem.text != prefix:
                    # URL解码key，与同步版本保持一致
                    from urllib.parse import unquote

                    decoded_key = unquote(key_elem.text)
                    key_list.append({"type": "file", "key": decoded_key})

            return key_list
        except ET.ParseError as e:
            print(f"XML 解析错误: {e}")
            return []

    async def list_regions(self):
        """
        description:
            列出OSS支持的区域
        return:
            regions(list): 区域列表，每个元素为字典，包含 region_id, region_name, internal_endpoint, internet_endpoint
        """
        try:
            # 使用通用的OSS endpoint来获取区域列表
            url = "https://oss-cn-hangzhou.aliyuncs.com/?regions"
            
            # 生成签名（对于 list_regions API，不需要 bucket_name）
            # 直接使用空字符串作为 bucket_name，因为 list_regions 不需要 bucket
            headers = {}
            params = {}
            req = oss2.http.Request("GET", url, params=params, headers=headers)
            # 使用空字符串作为 bucket_name，因为 list_regions 不需要 bucket
            self.auth._sign_request(req, "", "")
            signed_headers = {}
            for k, v in req.headers.items():
                if k is not None and v is not None:
                    signed_headers[str(k)] = str(v)
            
            # 发送请求
            session = await self._ensure_session()
            async with session.get(url, headers=signed_headers) as resp:
                if resp.status != 200:
                    resp.raise_for_status()
                
                # 解析XML响应
                text = await resp.text()
                root = ET.fromstring(text)
                regions = []
                
                # 查找所有 RegionInfo 元素
                for region_info_elem in root.findall(".//RegionInfo"):
                    region_elem = region_info_elem.find("Region")
                    internal_endpoint_elem = region_info_elem.find("InternalEndpoint")
                    internet_endpoint_elem = region_info_elem.find("InternetEndpoint")
                    
                    region_id = region_elem.text if region_elem is not None else ""
                    # 从 region_id 中提取区域名称（去掉 oss- 前缀）
                    region_name = region_id.replace("oss-", "") if region_id else None
                    internal_endpoint = internal_endpoint_elem.text if internal_endpoint_elem is not None else None
                    internet_endpoint = internet_endpoint_elem.text if internet_endpoint_elem is not None else None
                    
                    if region_id:
                        regions.append({
                            "region_id": region_id,
                            "region_name": region_name,
                            "internal_endpoint": internal_endpoint,
                            "internet_endpoint": internet_endpoint
                        })
                
                self.regions = regions
                return regions
        except Exception as e:
            print(f"list_regions error: {traceback.format_exc()}, {e}")
            self.regions = []
            return []

    async def list_region_ids(self):
        """
        description:
            列出OSS支持的区域ID
        return:
            region_ids(list): 区域ID列表
        """
        regions = await self.list_regions()
        return [region["region_id"] for region in regions]

    async def list_objects(self, prefix="", max_keys=100):
        """列出对象，返回所有匹配的对象"""
        session = await self._ensure_session()
        all_objects = []
        next_marker = ""

        while True:
            params = {
                "prefix": prefix,
                "max-keys": str(max_keys),
                "delimiter": "",
                "marker": next_marker,
                "encoding-type": "url",
            }

            # 构建URL参数
            param_str = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{self.base_url}/?{param_str}"
            headers = self._sign_request("GET", url, params=params)
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    break

                text = await resp.text()
                objects = self._parse_list_objects_xml(text)
                all_objects.extend(objects)

                # 检查是否还有更多对象
                root = ET.fromstring(text)
                is_truncated = root.find(".//IsTruncated")
                if is_truncated is None or is_truncated.text.lower() != "true":
                    break

                # 获取下一页的marker
                next_marker_elem = root.find(".//NextMarker")
                if next_marker_elem is None:
                    break
                next_marker = next_marker_elem.text

        return all_objects

    async def is_object(self, key):
        """判断对象是否存在"""
        try:
            # 使用list_objects来检查对象是否存在，避免签名问题
            object_list = await self.list_objects(key)
            # 检查是否有完全匹配的对象
            for obj in object_list:
                if obj.key == key:
                    return True
            return False
        except Exception as e:
            print(f"is_object error: {e}")
            return False

    async def upload_object(self, prefix, local_path):
        """上传对象"""
        if not os.path.exists(local_path):
            return False

        file_name = os.path.basename(local_path)
        key = f"{prefix}/{file_name}" if prefix else file_name

        # 使用线程池运行oss2的同步操作
        try:
            await self._run_in_thread(
                self.oss_bucket.put_object_from_file, key, local_path
            )
            return True
        except Exception as e:
            return False

    async def download_object(self, key, dir_path="."):
        """下载对象"""
        if dir_path and dir_path != "":
            os.makedirs(dir_path, exist_ok=True)
        file_name = os.path.basename(key)
        local_path = os.path.join(dir_path, file_name)

        # 使用线程池运行oss2的同步操作
        try:
            await self._run_in_thread(
                self.oss_bucket.get_object_to_file, key, local_path
            )
            return True
        except Exception as e:
            return False

    async def delete(self, prefix):
        """删除OSS中的对象或前缀"""
        try:
            object_list = await self.list_objects(prefix)

            # 使用线程池批量删除对象
            delete_tasks = []
            for obj in object_list:
                task = self._run_in_thread(self.oss_bucket.delete_object, obj.key)
                delete_tasks.append(task)

            # 等待所有删除操作完成
            results = await asyncio.gather(*delete_tasks, return_exceptions=True)

            # 检查是否有任何删除失败
            for result in results:
                if isinstance(result, Exception):
                    return False

            return True
        except Exception as e:
            print(f"删除对象时出错: {e}")
            return False

    async def get_size(self, prefix, unit="B"):
        """获取OSS中对象或前缀下所有对象的大小"""
        object_list = await self.list_objects(prefix)
        total_size = 0
        object_count = 0

        # 使用线程池获取每个对象的准确大小
        size_tasks = []
        for obj in object_list:
            task = self._run_in_thread(self.oss_bucket.get_object_meta, obj.key)
            size_tasks.append(task)

        # 等待所有获取元数据操作完成
        results = await asyncio.gather(*size_tasks, return_exceptions=True)

        for result in results:
            if not isinstance(result, Exception):
                total_size += result.content_length
                object_count += 1

        return (
            size_unit_convert(total_size, input_unit="B", output_unit=unit),
            object_count,
        )

    async def ls(self, prefix):
        """列出当前目录下的所有文件夹和文件的key"""
        if not prefix.endswith("/"):
            prefix += "/"

        session = await self._ensure_session()
        key_list = []
        next_marker = ""

        while True:
            params = {
                "prefix": prefix,
                "delimiter": "/",
                "max-keys": "1000",
                "marker": next_marker,
                "encoding-type": "url",
            }

            url = f"{self.base_url}"
            headers = self._sign_request("GET", "", params=params)

            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status != 200:
                    break

                text = await resp.text()
                batch_key_list = self._parse_ls_xml(text, prefix)
                key_list.extend(batch_key_list)

                # 检查是否还有更多结果
                root = ET.fromstring(text)
                is_truncated = root.find(".//IsTruncated")
                if is_truncated is None or is_truncated.text.lower() != "true":
                    break

                # 获取下一页的marker
                next_marker_elem = root.find(".//NextMarker")
                if next_marker_elem is None:
                    break
                next_marker = next_marker_elem.text

        return key_list

    async def get_last_modified(self, prefix):
        """获取OSS中对象或前缀下所有对象的最后修改时间，格式化为%Y-%m-%d %H:%M:%S"""
        from datetime import datetime

        def format_time(timestamp):
            if not timestamp:
                return ""
            try:
                # 将时间戳转换为datetime对象
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return ""

        if await self.is_object(prefix):
            # 如果是单个对象，直接获取其最后修改时间
            try:
                meta = await self._run_in_thread(
                    self.oss_bucket.get_object_meta, prefix
                )
                return format_time(meta.last_modified)
            except Exception:
                return ""
        else:
            # 如果是前缀，找到最后修改的对象 - 与同步版本保持一致
            object_list = await self.list_objects(prefix)
            if object_list:
                # 使用线程池获取每个对象的最后修改时间
                meta_tasks = []
                for obj in object_list:
                    task = self._run_in_thread(self.oss_bucket.get_object_meta, obj.key)
                    meta_tasks.append(task)

                # 等待所有获取元数据操作完成
                results = await asyncio.gather(*meta_tasks, return_exceptions=True)

                # 找到最后修改的对象
                latest_time = 0
                latest_meta = None
                for result in results:
                    if (
                        not isinstance(result, Exception)
                        and result.last_modified > latest_time
                    ):
                        latest_time = result.last_modified
                        latest_meta = result

                if latest_meta:
                    return format_time(latest_meta.last_modified)

        return ""

    async def path_exists(self, prefix):
        """检查OSS中对象或前缀是否存在"""
        try:
            object_list = await self.list_objects(prefix)
            return len(object_list) > 0
        except Exception as e:
            print(f"检查路径存在性时出错: {e}")
            return False

    async def copy_object(self, prefix, target_prefix):
        """复制对象"""
        try:
            await self._run_in_thread(
                self.oss_bucket.copy_object,
                source_bucket_name=self.bucket_name,
                source_key=prefix,
                target_key=target_prefix,
            )
            return True
        except Exception as e:
            return False

    async def generate_presigned_url(self, key, expires_in=3600):
        """生成预签名URL"""
        # 使用线程池运行oss2的同步操作
        return await self._run_in_thread(
            self.oss_bucket.sign_url, "GET", key, expires_in
        )
