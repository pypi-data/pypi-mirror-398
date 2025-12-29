import requests
import json
import asyncio
import csv
import os
from typing import Optional


class Feishu:
    channel_map = {
        "矩阵像素订阅群": "https://open.feishu.cn/open-apis/bot/v2/hook/6e368741-ab2e-46f4-a945-5c1182303f91",
        "devtoolkit服务报警": "https://open.feishu.cn/open-apis/bot/v2/hook/b9e7cfa1-c63f-4a9f-9699-286f7316784b",
        "baymax服务报警": "https://open.feishu.cn/open-apis/bot/v2/hook/5d8d4fa6-67c4-4202-9122-389d1ec2b668",
        "videodriver服务报警": "https://open.feishu.cn/open-apis/bot/v2/hook/5359b92d-02ab-47ca-a617-58b8152eaa2d",
        "arraycut服务报警": "https://open.feishu.cn/open-apis/bot/v2/hook/e610b1e8-f867-4670-8d4d-0553f64884f0",
        "knowledgebase微服务报警": "https://open.feishu.cn/open-apis/bot/v2/hook/5f007914-235a-4287-8349-6c1dd7c70024",
        "llm微服务报警": "https://open.feishu.cn/open-apis/bot/v2/hook/54942aa6-24f1-4851-8fe9-d7c87572d00a",
        "thirdparty微服务报警": "https://open.feishu.cn/open-apis/bot/v2/hook/b1e6237a-1323-4ad9-96f4-d74de5cdc00f",
        "picturebed服务报警": "https://open.feishu.cn/open-apis/bot/v2/hook/d3c2e68c-3ed3-4832-9b66-76db5bd69b42",
        "picturetransform服务报警": "https://open.feishu.cn/open-apis/bot/v2/hook/e975aa0a-acef-4e3f-bee4-6dc507b87ebd",
        "cloudstorage服务报警": "https://open.feishu.cn/open-apis/bot/v2/hook/a632d0bc-e400-40ce-a3bb-1b9b9ee634f4",
        "deployengine服务报警": "https://open.feishu.cn/open-apis/bot/v2/hook/9a347a63-58fb-4e10-9a3d-ff4918ddb3a9",
    }

    def __init__(
        self,
        channel_name,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
    ):
        """
        description:
            初始化飞书告警客户端
        parameters:
            channel_name(str): 飞书频道名称
            app_id(Optional[str]): 应用ID，可选
            app_secret(Optional[str]): 应用密钥，可选
        """
        self.webhook_url = self.channel_map[channel_name]
        self.app_id = app_id
        self.app_secret = app_secret
        self._access_token = None

    def send(self, text):
        """
        description:
            发送文本消息到飞书群
        parameters:
            text(str): 要发送的文本内容
        return:
            success(bool): 发送是否成功
        """
        print(text)
        headers = {"Content-Type": "application/json"}
        data = {"msg_type": "text", "content": {"text": text}}
        response = requests.post(
            self.webhook_url, headers=headers, data=json.dumps(data)
        )
        return bool(
            response
            and response.json().get("StatusCode") == 0
            and response.json().get("StatusMessage") == "success"
        )

    async def send_async(self, text: str):
        """
        description:
            异步发送文本消息到飞书群
        parameters:
            text(str): 要发送的文本内容
        return:
            success(bool): 发送是否成功
        """
        return await asyncio.to_thread(self.send, text)

    def send_markdown(
        self,
        markdown_content: str,
        title: str,
        template: str = "turquoise",
    ):
        """
        description:
            发送Markdown格式的消息到飞书群
        parameters:
            markdown_content(str): Markdown格式的内容
            title(str): 消息标题
            template(str): 卡片模板颜色，默认为"turquoise"
        return:
            success(bool): 发送是否成功
        """
        headers = {"Content-Type": "application/json; charset=utf-8"}
        card = {
            "config": {"wide_screen_mode": True, "enable_forward": True},
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": template,
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": markdown_content}}
            ],
        }
        payload = {"msg_type": "interactive", "card": card}
        resp = requests.post(
            self.webhook_url, headers=headers, data=json.dumps(payload)
        )
        return bool(resp.ok and resp.json().get("StatusCode") == 0)

    async def send_markdown_async(
        self,
        markdown_content: str,
        title: str,
        template: str = "turquoise",
    ):
        """
        description:
            异步发送Markdown格式的消息到飞书群
        parameters:
            markdown_content(str): Markdown格式的内容
            title(str): 消息标题
            template(str): 卡片模板颜色，默认为"turquoise"
        return:
            success(bool): 发送是否成功
        """
        return await asyncio.to_thread(
            self.send_markdown, markdown_content, title, template
        )

    def send_table(
        self,
        headers: list,
        rows: list,
        title: str,
        template: str = "turquoise",
    ):
        """
        description:
            发送表格消息到飞书群
        parameters:
            headers(list): 表头列表
            rows(list): 表格行数据列表
            title(str): 消息标题
            template(str): 卡片模板颜色，默认为"turquoise"
        return:
            success(bool): 发送是否成功
        """
        headers_req = {"Content-Type": "application/json; charset=utf-8"}
        n_cols = len(headers)
        columns = []
        for ci in range(n_cols):
            elements_in_col = []
            # 表头
            elements_in_col.append(
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"**{headers[ci]}**"},
                }
            )
            # 每一行的该列内容
            for row in rows:
                cell = row[ci] if ci < len(row) else ""
                elements_in_col.append(
                    {"tag": "div", "text": {"tag": "lark_md", "content": cell}}
                )
            columns.append(
                {
                    "tag": "column",
                    "width": "weighted",
                    "weight": 1,
                    "elements": elements_in_col,
                }
            )

        elements = [{"tag": "column_set", "columns": columns}]

        card = {
            "config": {"wide_screen_mode": True, "enable_forward": True},
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": template,
            },
            "elements": elements,
        }
        payload = {"msg_type": "interactive", "card": card}

        resp = requests.post(
            self.webhook_url, headers=headers_req, data=json.dumps(payload)
        )
        try:
            print("feishu send_table resp:", resp.status_code, resp.json())
        except Exception:
            print("feishu send_table resp:", resp.status_code, resp.text)
        return bool(resp.ok and resp.json().get("StatusCode") == 0)

    async def send_table_async(
        self,
        headers: list[str],
        rows: list[list[str]],
        title: str,
        template: str = "turquoise",
    ):
        """
        description:
            异步发送表格消息到飞书群
        parameters:
            headers(list[str]): 表头列表
            rows(list[list[str]]): 表格行数据列表
            title(str): 消息标题
            template(str): 卡片模板颜色，默认为"turquoise"
        return:
            success(bool): 发送是否成功
        """
        return await asyncio.to_thread(self.send_table, headers, rows, title, template)

    def send_file(
        self,
        file_url: Optional[str] = None,
        title: Optional[str] = None,
        template: str = "turquoise",
    ):
        """
        description:
            发送文件到飞书群
            通过文件下载链接发送包含文件下载按钮的卡片消息
        parameters:
            file_url(str): 文件下载链接（如 OSS 链接），必需参数
            title(str): 消息标题，如果为 None 则使用文件名
            template(str): 卡片模板颜色，默认 "turquoise"
        return:
            bool: 发送是否成功
        """
        if not file_url:
            print("错误：必须提供 file_url（文件下载链接）")
            return False
        headers = {"Content-Type": "application/json; charset=utf-8"}
        markdown_content = f"[点击下载文件]({file_url})"

        card = {
            "config": {"wide_screen_mode": True, "enable_forward": True},
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": template,
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": markdown_content}}
            ],
        }
        payload = {"msg_type": "interactive", "card": card}

        try:
            resp = requests.post(
                self.webhook_url, headers=headers, data=json.dumps(payload)
            )
            if resp.ok:
                result = resp.json()
                return bool(result.get("StatusCode") == 0 or result.get("code") == 0)
            else:
                print(f"发送文件消息失败: {resp.status_code}, {resp.text}")
                return False
        except Exception as e:
            print(f"发送文件消息异常: {e}")
            return False

    async def send_file_async(self, file_url: str, title: str, template: str):
        """
        description:
            异步发送文件到飞书群
        parameters:
            file_url(str): 文件下载链接
            title(str): 消息标题
            template(str): 卡片模板颜色
        return:
            success(bool): 发送是否成功
        """
        return await asyncio.to_thread(self.send_file, file_url, title, template)


class FeishuDocumentManager:
    """
    飞书文档管理器，用于管理飞书文档的创建、查询、更新和删除
    """

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
    ):
        """
        description:
            初始化飞书文档管理器
        parameters:
            app_id(Optional[str]): 飞书应用ID，如果不提供则从settings中读取
            app_secret(Optional[str]): 飞书应用密钥，如果不提供则从settings中读取
        """
        try:
            from settings import FEISHU_APP_ID, FEISHU_APP_SECRET
            self.app_id = app_id or FEISHU_APP_ID
            self.app_secret = app_secret or FEISHU_APP_SECRET
        except ImportError:
            if not app_id or not app_secret:
                raise ValueError(
                    "必须提供app_id和app_secret，或者在settings中配置FEISHU_APP_ID和FEISHU_APP_SECRET"
                )
            self.app_id = app_id
            self.app_secret = app_secret

        self.base_url = "https://open.feishu.cn/open-apis"
        self._access_token = None
        self._token_expire_time = 0

    def _get_access_token(self) -> str:
        """
        description:
            获取飞书应用的访问令牌（带缓存机制）
        return:
            str: 访问令牌
        """
        import time

        # 如果token未过期，直接返回缓存的token
        if self._access_token and time.time() < self._token_expire_time:
            return self._access_token

        url = f"{self.base_url}/auth/v3/app_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()

            if result.get("code") != 0:
                raise Exception(
                    f"获取access_token失败: {result.get('msg', 'unknown error')}"
                )

            self._access_token = result.get("app_access_token")
            # token有效期默认7200秒，提前300秒刷新
            expire = result.get("expire", 7200)
            self._token_expire_time = time.time() + expire - 300

            return self._access_token
        except requests.RequestException as e:
            raise Exception(f"请求access_token时发生错误: {str(e)}")

    def _get_headers(self) -> dict:
        """
        description:
            获取请求头，包含access_token
        return:
            dict: 请求头字典
        """
        return {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def list_documents(
        self,
        user_id: Optional[str] = None,
        folder_token: Optional[str] = None,
        page_size: int = 50,
        page_token: Optional[str] = None,
        order_by: str = "EditedTime",
        direction: str = "DESC",
    ) -> tuple[dict, bool]:
        """
        description:
            列出文档列表（支持按用户或文件夹筛选）
        parameters:
            user_id(Optional[str]): 用户ID，如果提供则只返回该用户的文档
            folder_token(Optional[str]): 文件夹token，如果提供则只返回该文件夹下的文档
            page_size(int): 每页数量，默认50
            page_token(Optional[str]): 分页token，用于获取下一页
            order_by(str): 排序字段，默认为"EditedTime"（编辑时间）
            direction(str): 排序方向，"ASC"或"DESC"，默认为"DESC"
        return:
            result(dict): API返回的结果，包含文档列表
            success(bool): 是否成功
        """
        url = f"{self.base_url}/drive/v1/files"
        headers = self._get_headers()
        params = {
            "page_size": page_size,
            "order_by": order_by,
            "direction": direction,
        }

        if user_id:
            params["user_id"] = user_id
        if folder_token:
            params["folder_token"] = folder_token
        if page_token:
            params["page_token"] = page_token

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()

            if result.get("code") != 0:
                return result, False

            return result, True
        except requests.RequestException as e:
            return {"code": -1, "msg": f"请求失败: {str(e)}"}, False

    def create_document(
        self,
        folder_token: str,
        title: str,
        doc_type: str = "doc",
    ) -> tuple[dict, bool]:
        """
        description:
            创建新文档
        parameters:
            folder_token(str): 目标文件夹token
            title(str): 文档标题
            doc_type(str): 文档类型，"doc"表示文档，"sheet"表示电子表格，"bitable"表示多维表格，默认为"doc"
        return:
            result(dict): API返回的结果，包含创建的文档信息
            success(bool): 是否成功
        """
        url = f"{self.base_url}/drive/v1/files/create"
        headers = self._get_headers()
        data = {
            "folder_token": folder_token,
            "title": title,
            "type": doc_type,
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()

            if result.get("code") != 0:
                return result, False

            return result, True
        except requests.RequestException as e:
            return {"code": -1, "msg": f"请求失败: {str(e)}"}, False

    def update_document(
        self,
        document_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
    ) -> tuple[dict, bool]:
        """
        description:
            更新文档（支持更新标题和内容）
        parameters:
            document_id(str): 文档ID（doc_token）
            title(Optional[str]): 新的文档标题，如果提供则更新标题
            content(Optional[str]): 新的文档内容（Markdown格式），如果提供则更新内容
        return:
            result(dict): API返回的结果
            success(bool): 是否成功
        """
        success_count = 0

        # 更新标题
        if title:
            url = f"{self.base_url}/drive/v1/files/{document_id}"
            headers = self._get_headers()
            data = {"name": title}

            try:
                response = requests.patch(url, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()

                if result.get("code") == 0:
                    success_count += 1
                else:
                    return result, False
            except requests.RequestException as e:
                return {"code": -1, "msg": f"更新标题失败: {str(e)}"}, False

        # 更新内容（使用docx API）
        if content:
            url = f"{self.base_url}/docx/v1/documents/{document_id}/blocks/{document_id}"
            headers = self._get_headers()
            # 构建文档块内容
            blocks = [
                {
                    "block_id": document_id,
                    "block_type": 1,  # 1表示文本块
                    "text": {
                        "elements": [
                            {
                                "text_run": {
                                    "content": content,
                                }
                            }
                        ]
                    },
                }
            ]
            data = {"document_revision_id": -1, "blocks": blocks}

            try:
                response = requests.patch(url, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()

                if result.get("code") == 0:
                    success_count += 1
                else:
                    return result, False
            except requests.RequestException as e:
                return {"code": -1, "msg": f"更新内容失败: {str(e)}"}, False

        if success_count > 0:
            return {"code": 0, "msg": "success"}, True
        else:
            return {"code": -1, "msg": "没有提供需要更新的内容"}, False

    def delete_document(self, file_token: str) -> tuple[dict, bool]:
        """
        description:
            删除文档
        parameters:
            file_token(str): 文件token（文档ID）
        return:
            result(dict): API返回的结果
            success(bool): 是否成功
        """
        url = f"{self.base_url}/drive/v1/files/{file_token}"
        headers = self._get_headers()

        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            result = response.json()

            if result.get("code") != 0:
                return result, False

            return result, True
        except requests.RequestException as e:
            return {"code": -1, "msg": f"请求失败: {str(e)}"}, False

    def get_document_info(self, document_id: str) -> tuple[dict, bool]:
        """
        description:
            获取文档详细信息
        parameters:
            document_id(str): 文档ID（file_token）
        return:
            result(dict): API返回的结果，包含文档信息
            success(bool): 是否成功
        """
        url = f"{self.base_url}/drive/v1/files/{document_id}"
        headers = self._get_headers()

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()

            if result.get("code") != 0:
                return result, False

            return result, True
        except requests.RequestException as e:
            return {"code": -1, "msg": f"请求失败: {str(e)}"}, False
