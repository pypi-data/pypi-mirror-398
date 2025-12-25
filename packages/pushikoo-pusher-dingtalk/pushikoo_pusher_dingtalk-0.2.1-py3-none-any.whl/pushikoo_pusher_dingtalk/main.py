import hashlib
from datetime import datetime
from urllib.parse import urlparse

import boto3
from botocore.config import Config
from loguru import logger
from pushikoo_interface import Pusher, Struct, StructImage

from pushikoo_pusher_dingtalk.api import DingtalkChatbot
from pushikoo_pusher_dingtalk.config import AdapterConfig, InstanceConfig

# Expiration timestamp: 2099-12-31 23:59:59 UTC
EXPIRATION_TIMESTAMP = int(datetime(2099, 12, 31, 23, 59, 59).timestamp())


class DingTalkPusher(Pusher[AdapterConfig, InstanceConfig]):
    """钉钉群自定义机器人推送器。"""

    def __init__(self) -> None:
        logger.debug(f"{self.adapter_name}.{self.identifier} initialized")

    def _create_api(self) -> DingtalkChatbot:
        """Create API client instance with current config (supports hot-reload)."""
        return DingtalkChatbot(
            webhook=self.instance_config.webhook_url,
            secret=self.instance_config.secret or None,
        )

    def _create_s3_client(self):
        """Create S3 client instance with current config (supports hot-reload)."""
        # Note: Disable request checksum calculation to avoid chunked encoding issues
        # with some S3-compatible services that don't properly handle AWS SDK checksums
        return boto3.client(
            "s3",
            endpoint_url=self.config.oss.endpoint,
            aws_access_key_id=self.config.oss.access_key,
            aws_secret_access_key=self.config.oss.secret_key,
            config=Config(
                signature_version="s3v4",
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )

    def push(self, content: Struct) -> None:
        """推送消息到钉钉群。"""
        api = self._create_api()
        md = self._to_markdown(content)
        title = md[:10] if len(md) > 10 else md
        api.send_markdown(title, md)

    def _to_markdown(self, struct: Struct) -> str:
        """将 Struct 转换为 Markdown 格式。"""
        result = ""
        for element in struct.content:
            if isinstance(element, StructImage):
                # Get public URL for image
                public_url = self._get_public_url(element.source)
                result += element.asmarkdown(source=public_url)
            else:
                result += element.asmarkdown() + "  \n"
        return result

    def _get_public_url(self, source: str) -> str:
        """
        获取图片的公开访问 URL。

        如果是 http/https URL，直接返回。
        如果是 file:// 本地文件，上传到 OSS 并返回预签名 URL。
        """
        parsed = urlparse(source)

        if parsed.scheme in ("http", "https"):
            return source

        if parsed.scheme == "file":
            # 本地文件，上传到 OSS
            local_path = parsed.path
            # Windows 路径处理: file:///C:/path -> /C:/path -> C:/path
            if (
                local_path.startswith("/")
                and len(local_path) > 2
                and local_path[2] == ":"
            ):
                local_path = local_path[1:]

            return self._upload_to_oss(local_path)

        # 其他情况，假设是 URL
        return source

    def _upload_to_oss(self, local_path: str) -> str:
        """
        上传本地文件到 OSS 并返回预签名 URL（有效期至 2099-12-31）。

        文件以 SHA256 哈希值命名以便去重。
        """
        # 读取文件并计算 SHA256
        with open(local_path, "rb") as f:
            file_content = f.read()

        sha256_hash = hashlib.sha256(file_content).hexdigest()
        # 获取文件扩展名
        ext = ""
        if "." in local_path:
            ext = "." + local_path.rsplit(".", 1)[-1].lower()

        key = f"{sha256_hash}{ext}"

        # 创建 S3 客户端并上传到 OSS
        s3_client = self._create_s3_client()
        s3_client.put_object(
            Bucket=self.config.oss.bucket,
            Key=key,
            Body=file_content,
        )

        logger.debug(f"Uploaded {local_path} to OSS as {key}")

        # 生成预签名 URL，有效期至 2099-12-31
        expires_in = EXPIRATION_TIMESTAMP - int(datetime.now().timestamp())
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.config.oss.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

        # 生成短链接
        return self._shorten_url(presigned_url)

    def _shorten_url(self, url: str) -> str:
        """调用短链服务生成短链接。"""
        import requests

        service_base = "https://shorturl.evative7.host"
        response = requests.post(
            f"{service_base}/shorten",
            json={"url": url},
        )
        response.raise_for_status()
        data = response.json()
        short_code = data["short_url"]
        return f"{service_base}/{short_code}"
