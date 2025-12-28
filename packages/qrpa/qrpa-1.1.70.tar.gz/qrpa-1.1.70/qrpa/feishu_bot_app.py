# pip install lark-oapi -U
import json
import os
import uuid
from typing import Optional

import lark_oapi as lark
from lark_oapi.api.im.v1 import *


class FeishuBot:
    """飞书机器人类，封装所有机器人相关功能"""
    
    def __init__(self, config):
        """
        初始化飞书机器人
        
        Args:
            config: 配置对象，包含应用ID、应用密钥和群组信息
        """
        self.config = config
        self._client = None
    
    @property
    def client(self):
        """获取飞书客户端，使用懒加载模式"""
        if self._client is None:
            self._client = lark.Client.builder() \
                .app_id(self.config.feishu_bot.app_id) \
                .app_secret(self.config.feishu_bot.app_secret) \
                .log_level(lark.LogLevel.INFO) \
                .build()
        return self._client
    
    def _get_chat_id(self, bot_name: str) -> Optional[str]:
        """
        根据群组别名获取群组ID
        
        Args:
            bot_name: 群组别名
            
        Returns:
            群组ID，如果别名不存在则返回None
        """
        return self.config.dict_feishu_group.get(bot_name)
    
    def _handle_response_error(self, response, operation_name: str):
        """
        处理API响应错误
        
        Args:
            response: API响应对象
            operation_name: 操作名称，用于错误日志
        """
        if not response.success():
            lark.logger.error(
                f"{operation_name} failed, code: {response.code}, "
                f"msg: {response.msg}, log_id: {response.get_log_id()}, "
                f"resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
            )
            return True
        return False
    
    def send_text(self, content: str, bot_name: str = 'test') -> bool:
        """
        发送文本消息
        
        Args:
            content: 文本内容
            bot_name: 群组别名，默认为'test'
            
        Returns:
            发送是否成功
        """
        chat_id = self._get_chat_id(bot_name)
        if not chat_id:
            lark.logger.error(f"未找到群组别名 '{bot_name}' 对应的群组ID")
            return False
        
        message_content = {"text": content}
        
        # 构造请求对象
        request: CreateMessageRequest = CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(CreateMessageRequestBody.builder()
                          .receive_id(chat_id)
                          .msg_type("text")
                          .content(json.dumps(message_content))
                          .uuid(str(uuid.uuid4()))
                          .build()) \
            .build()
        
        # 发起请求
        response: CreateMessageResponse = self.client.im.v1.message.create(request)
        
        # 处理失败返回
        if self._handle_response_error(response, "send_text"):
            return False
        
        # 处理业务结果
        lark.logger.info(lark.JSON.marshal(response.data, indent=4))
        return True
    
    def send_image(self, file_path: str, bot_name: str = 'test') -> bool:
        """
        发送图片消息
        
        Args:
            file_path: 图片文件路径
            bot_name: 群组别名，默认为'test'
            
        Returns:
            发送是否成功
        """
        # 先上传图片获取image_key
        image_key = self.upload_image(file_path)
        if not image_key:
            return False
        
        chat_id = self._get_chat_id(bot_name)
        if not chat_id:
            lark.logger.error(f"未找到群组别名 '{bot_name}' 对应的群组ID")
            return False
        
        message_content = {"image_key": image_key}
        
        # 构造请求对象
        request: CreateMessageRequest = CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(CreateMessageRequestBody.builder()
                          .receive_id(chat_id)
                          .msg_type("image")
                          .content(json.dumps(message_content))
                          .uuid(str(uuid.uuid4()))
                          .build()) \
            .build()
        
        # 发起请求
        response: CreateMessageResponse = self.client.im.v1.message.create(request)
        
        # 处理失败返回
        if self._handle_response_error(response, "send_image"):
            return False
        
        # 处理业务结果
        lark.logger.info(lark.JSON.marshal(response.data, indent=4))
        return True
    
    def send_excel(self, file_path: str, bot_name: str = 'test') -> bool:
        """
        发送Excel文件
        
        Args:
            file_path: Excel文件路径
            bot_name: 群组别名，默认为'test'
            
        Returns:
            发送是否成功
        """
        # 先上传文件获取file_key
        file_key = self.upload_excel(file_path)
        if not file_key:
            return False
        
        chat_id = self._get_chat_id(bot_name)
        if not chat_id:
            lark.logger.error(f"未找到群组别名 '{bot_name}' 对应的群组ID")
            return False
        
        message_content = {"file_key": file_key}
        
        # 构造请求对象
        request: CreateMessageRequest = CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(CreateMessageRequestBody.builder()
                          .receive_id(chat_id)
                          .msg_type("file")
                          .content(json.dumps(message_content))
                          .uuid(str(uuid.uuid4()))
                          .build()) \
            .build()
        
        # 发起请求
        response: CreateMessageResponse = self.client.im.v1.message.create(request)
        
        # 处理失败返回
        if self._handle_response_error(response, "send_excel"):
            return False
        
        # 处理业务结果
        lark.logger.info(lark.JSON.marshal(response.data, indent=4))
        return True
    
    def upload_excel(self, file_path: str) -> Optional[str]:
        """
        上传Excel文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件key，上传失败返回None
        """
        if not os.path.exists(file_path):
            lark.logger.error(f"文件不存在: {file_path}")
            return None
        
        try:
            with open(file_path, "rb") as file:
                file_name = os.path.basename(file_path)
                request: CreateFileRequest = CreateFileRequest.builder() \
                    .request_body(CreateFileRequestBody.builder()
                                  .file_type("xls")
                                  .file_name(file_name)
                                  .file(file)
                                  .build()) \
                    .build()
                
                # 发起请求
                response: CreateFileResponse = self.client.im.v1.file.create(request)
                
                # 处理失败返回
                if self._handle_response_error(response, "upload_excel"):
                    return None
                
                # 处理业务结果
                lark.logger.info(lark.JSON.marshal(response.data, indent=4))
                return response.data.file_key
        except Exception as e:
            lark.logger.error(f"上传Excel文件时发生错误: {e}")
            return None
    
    def upload_image(self, file_path: str) -> Optional[str]:
        """
        上传图片文件
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            图片key，上传失败返回None
        """
        if not os.path.exists(file_path):
            lark.logger.error(f"文件不存在: {file_path}")
            return None
        
        try:
            with open(file_path, "rb") as file:
                request: CreateImageRequest = CreateImageRequest.builder() \
                    .request_body(CreateImageRequestBody.builder()
                                  .image_type("message")
                                  .image(file)
                                  .build()) \
                    .build()
                
                # 发起请求
                response: CreateImageResponse = self.client.im.v1.image.create(request)
                
                # 处理失败返回
                if self._handle_response_error(response, "upload_image"):
                    return None
                
                # 处理业务结果
                lark.logger.info(lark.JSON.marshal(response.data, indent=4))
                return response.data.image_key
        except Exception as e:
            lark.logger.error(f"上传图片文件时发生错误: {e}")
            return None

    def upload_image_from_url(self, image_url: str) -> Optional[str]:
        """
        从URL下载图片并上传到飞书

        Args:
            image_url: 图片URL地址

        Returns:
            图片key，上传失败返回None
        """
        import tempfile
        import requests
        import re

        try:
            # 下载图片
            response = requests.get(image_url, timeout=30)
            if response.status_code != 200:
                lark.logger.error(f"下载图片失败, HTTP状态码: {response.status_code}, URL: {image_url}")
                return None

            # 从URL或Content-Type推断文件扩展名
            content_type = response.headers.get('Content-Type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            elif 'gif' in content_type:
                ext = '.gif'
            else:
                # 从URL中提取扩展名
                url_path = image_url.split('?')[0]
                if url_path.endswith('.png'):
                    ext = '.png'
                elif url_path.endswith('.gif'):
                    ext = '.gif'
                else:
                    ext = '.jpg'

            # 保存到临时文件
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name

            # 上传图片
            image_key = self.upload_image(tmp_path)

            # 删除临时文件
            try:
                os.remove(tmp_path)
            except:
                pass

            return image_key

        except Exception as e:
            lark.logger.error(f"从URL上传图片时发生错误: {e}, URL: {image_url}")
            return None

    @staticmethod
    def extract_image_url_from_html(html_content: str) -> Optional[str]:
        """
        从HTML内容中提取第一个img标签的src属性

        Args:
            html_content: HTML字符串

        Returns:
            图片URL，未找到返回None
        """
        import re

        if not html_content:
            return None

        # 使用正则匹配 img 标签的 src 属性
        pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
        match = re.search(pattern, html_content)

        if match:
            return match.group(1)

        return None

    def send_card(self, card_content: dict, bot_name: str = 'test', msg_uuid: str = None) -> bool:
        """
        发送卡片消息（交互式消息）

        Args:
            card_content: 卡片内容，包含 config、elements、header 等字段的字典
            bot_name: 群组别名，默认为'test'
            msg_uuid: 消息唯一标识，用于幂等性，默认自动生成

        Returns:
            发送是否成功
        """
        chat_id = self._get_chat_id(bot_name)
        if not chat_id:
            lark.logger.error(f"未找到群组别名 '{bot_name}' 对应的群组ID")
            return False

        if msg_uuid is None:
            msg_uuid = str(uuid.uuid4())

        # 构造请求对象
        request: CreateMessageRequest = CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(CreateMessageRequestBody.builder()
                          .receive_id(chat_id)
                          .msg_type("interactive")
                          .content(json.dumps(card_content, ensure_ascii=False))
                          .uuid(msg_uuid)
                          .build()) \
            .build()

        # 发起请求
        response: CreateMessageResponse = self.client.im.v1.message.create(request)

        # 处理失败返回
        if self._handle_response_error(response, "send_card"):
            return False

        # 处理业务结果
        lark.logger.info(lark.JSON.marshal(response.data, indent=4))
        return True

    def build_shein_announcement_card(self, announcements: list, title: str = None) -> dict:
        """
        构建希音公告卡片内容

        Args:
            announcements: 公告列表，每条包含 detail（公告详情）、img_key 等字段
            title: 卡片标题，默认根据当前时间生成

        Returns:
            卡片内容字典
        """
        from datetime import datetime, timedelta

        if title is None:
            yesterday = datetime.now() - timedelta(days=1)
            title = f"希音公告【{yesterday.strftime('%Y年%m月%d日')}17时至发布时】"

        elements = []

        for item in announcements:
            # 添加分隔线
            elements.append({"tag": "hr"})

            # 从 detail 中获取数据
            detail = item.get('detail', {})
            announcement_title = detail.get('title', '') or item.get('title', '')
            start_time = detail.get('startTime', '') or item.get('startTime', '')
            img_key = item.get('img_key', '')

            # 获取 importantType、typeDesc、tagDesc
            important_type = detail.get('importantType', '')
            type_desc = detail.get('typeDesc', '')
            tag_desc = detail.get('tagDesc', '')

            # 构建类型信息行
            type_info_parts = []
            # importantType 为 1 时展示红色 (重要)
            if str(important_type) == '1':
                type_info_parts.append("<font color='red'>(重要)</font>")
            if type_desc:
                type_info_parts.append(type_desc)
            if tag_desc:
                type_info_parts.append(tag_desc)
            type_info = ' | '.join(type_info_parts) if type_info_parts else ''

            # 构建内容：标题（蓝色）+ 类型信息（灰色）+ 时间（灰色，单独一行）
            content_parts = []
            content_parts.append(f"<font color='blue'>**{announcement_title}**</font>")
            
            if type_info:
                content_parts.append(f"<font color='grey'>{type_info}</font>")
            if start_time:
                content_parts.append(f"<font color='grey'>{start_time}</font>")
            
            content_text = "\n".join(content_parts)

            element = {
                "tag": "div",
                "text": {
                    "content": content_text,
                    "tag": "lark_md"
                }
            }

            # 如果有图片，添加 extra
            if img_key:
                element["extra"] = {
                    "alt": {
                        "content": "",
                        "tag": "plain_text"
                    },
                    "img_key": img_key,
                    "tag": "img"
                }

            elements.append(element)

        return {
            "config": {
                "wide_screen_mode": True
            },
            "elements": elements,
            "header": {
                "template": "purple",
                "title": {
                    "content": title,
                    "tag": "plain_text"
                }
            }
        }

    def build_shein_violation_card(self, penalty_data: dict, appeal_data: dict, title: str = None) -> dict:
        """
        构建希音违规处罚与申诉卡片内容

        Args:
            penalty_data: 违规处罚数据，按店铺分组 {store_username: {'store_username': x, 'store_name': x, 'store_manager': x, 'data': [...], 'total': x}}
            appeal_data: 违规申诉数据，按店铺分组 {store_username: {'store_username': x, 'store_name': x, 'store_manager': x, 'data': [...], 'total': x}}
            title: 卡片标题，默认根据当前时间生成

        Returns:
            卡片内容字典
        """
        from datetime import datetime, timedelta

        if title is None:
            yesterday = datetime.now() - timedelta(days=1)
            title = f"希音违规处罚与申诉【{yesterday.strftime('%Y年%m月%d日')}17时至发布时】"

        elements = []

        # 处理违规处罚
        if penalty_data:
            elements.append({"tag": "hr"})

            for store_username, store_info in penalty_data.items():
                store_name = store_info.get('store_name', '')
                store_manager = store_info.get('store_manager', '')
                total = store_info.get('total', 0)
                data_list = store_info.get('data', [])

                # 店铺头部信息（一行展示，蓝色）
                store_header = f"<font color='blue'>{store_username} {store_name}【{store_manager}】</font>"
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": store_header
                    }
                })

                # 列出每条违规的详情（灰色小字）
                for item in data_list:
                    violation_title = item.get('title', '')
                    description = item.get('description', '')
                    add_time = item.get('addTime', '')

                    item_content = f"<font color='grey'>**{violation_title}** {description} [{add_time}]</font>"
                    elements.append({
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": item_content
                        }
                    })

        # 处理违规申诉
        if appeal_data:
            elements.append({"tag": "hr"})
            elements.append({
                "tag": "div",
                "text": {
                    "content": "**📝 违规申诉通知**",
                    "tag": "lark_md"
                }
            })

            for store_username, store_info in appeal_data.items():
                store_name = store_info.get('store_name', '')
                store_manager = store_info.get('store_manager', '')
                total = store_info.get('total', 0)
                data_list = store_info.get('data', [])

                # 店铺头部信息（一行展示，蓝色）
                store_header = f"<font color='blue'>{store_username} {store_name}【{store_manager}】</font>"
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": store_header
                    }
                })

                # 列出每条申诉的详情（灰色小字）
                for item in data_list:
                    appeal_title = item.get('title', '')
                    description = item.get('description', '')
                    add_time = item.get('addTime', '')

                    item_content = f"<font color='grey'>**{appeal_title}** {description} [{add_time}]</font>"
                    elements.append({
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": item_content
                        }
                    })

        # 如果没有数据
        if not elements:
            elements.append({"tag": "hr"})
            elements.append({
                "tag": "div",
                "text": {
                    "content": "暂无违规处罚与申诉通知",
                    "tag": "lark_md"
                }
            })

        return {
            "config": {
                "wide_screen_mode": True
            },
            "elements": elements,
            "header": {
                "template": "red",
                "title": {
                    "content": title,
                    "tag": "plain_text"
                }
            }
        }