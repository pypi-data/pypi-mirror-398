from enum import Enum

from pydantic import BaseModel, Field
from pushikoo_interface.adapter import PusherConfig, PusherInstanceConfig


class ImageSendMethod(str, Enum):
    """Image sending method"""

    URL = "url"
    BASE64 = "base64"
    FILE = "file"


class Bot(BaseModel):
    """OneBot bot configuration"""

    url: str = Field(description="OneBot HTTP API URL, e.g. http://127.0.0.1:3000")
    token: str | None = Field(
        default=None,
        description="OneBot Access Token, None means no authentication required",
    )


class Contact(BaseModel):
    """Push target contact configuration"""

    id: str = Field(description="QQ number or group number")
    private: bool = Field(default=False, description="Whether it's a private chat")


class AdapterConfig(PusherConfig):
    """Adapter level configuration"""

    bots: dict[str, Bot] = Field(
        default_factory=lambda: {"bot0": Bot()},
        description="Bot configuration, key is the bot identifier",
    )


class InstanceConfig(PusherInstanceConfig):
    """Instance configuration"""

    bot: str = Field(default="bot0", description="Bot identifier to use")
    contact: Contact = Field(
        default_factory=lambda: Contact(id="123456"), description="Push target"
    )
    image_send_method: ImageSendMethod = Field(
        default=ImageSendMethod.BASE64,
        description="Image sending method",
    )
    max_image_count: int = Field(
        default=15, description="Maximum number of images per message"
    )
