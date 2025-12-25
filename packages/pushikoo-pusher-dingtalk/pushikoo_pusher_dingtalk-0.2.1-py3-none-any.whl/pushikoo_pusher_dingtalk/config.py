from pydantic import BaseModel, Field

from pushikoo_interface import PusherConfig, PusherInstanceConfig


class OSSConfig(BaseModel):
    """Configuration for S3-compatible OSS storage."""

    endpoint: str = Field(
        default="",
        description="S3-compatible endpoint URL, e.g. 'https://s3.us-east-1.amazonaws.com'",
    )
    bucket: str = Field(default="", description="Bucket name, e.g. 'my-images'")
    access_key: str = Field(
        default="", description="Access key, e.g. 'AKIAIOSFODNN7EXAMPLE'"
    )
    secret_key: str = Field(
        default="",
        description="Secret key, e.g. 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'",
    )


class AdapterConfig(PusherConfig):
    """DingTalk pusher adapter configuration."""

    oss: OSSConfig = Field(
        default=OSSConfig(),
        description="OSS configuration for image upload",
    )


class InstanceConfig(PusherInstanceConfig):
    """DingTalk pusher instance configuration."""

    webhook_url: str = Field(default="", description="DingTalk custom bot webhook URL")
    secret: str = Field(default="", description="Signing secret (starts with 'SEC')")
