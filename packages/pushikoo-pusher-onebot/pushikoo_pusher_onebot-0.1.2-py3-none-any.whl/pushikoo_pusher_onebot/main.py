from loguru import logger
from pushikoo_interface import Pusher, Struct, StructImage, StructText

from pushikoo_pusher_onebot.api import OneBotAPIClient, image_to_base64
from pushikoo_pusher_onebot.config import AdapterConfig, ImageSendMethod, InstanceConfig


class OneBot(Pusher[AdapterConfig, InstanceConfig]):
    def __init__(self) -> None:
        logger.debug(f"{self.adapter_name}.{self.identifier} initialized")

    def _create_api(self) -> OneBotAPIClient:
        """Create API client instance with current config (supports hot-reload)."""
        bot_config = self.config.bots[self.instance_config.bot]
        return OneBotAPIClient(
            url=bot_config.url,
            token=bot_config.token,
            proxies=self.ctx.get_proxies(),
        )

    def push(self, content: Struct) -> None:
        api = self._create_api()
        message_field = []

        # Count images
        images = [e for e in content.content if isinstance(e, StructImage)]
        max_count = self.instance_config.max_image_count

        for i, element in enumerate(content.content):
            if isinstance(element, StructText):
                # Mobile QQ eats one newline after an image, so add an extra newline
                if len(message_field) != 0:
                    if message_field[-1]["type"] == "image":
                        message_field.append({"type": "text", "data": {"text": "\n"}})
                message_field.append({"type": "text", "data": {"text": element.text}})

            elif isinstance(element, StructImage):
                # Check image count limit
                img_index = images.index(element)
                if img_index + 1 > max_count:
                    if img_index + 1 == max_count + 1:
                        # First image exceeding limit, replace with text hint
                        message_field.append(
                            {
                                "type": "text",
                                "data": {"text": f"({len(images)} images in total)\n"},
                            }
                        )
                    # Skip images exceeding limit
                    continue

                # Build image URL
                source = (
                    element.source
                    if isinstance(element.source, str)
                    else element.source[0]
                )
                method = self.instance_config.image_send_method
                if method == ImageSendMethod.BASE64:
                    image_url = "base64://" + image_to_base64(source)
                elif method == ImageSendMethod.URL:
                    image_url = source
                elif method == ImageSendMethod.FILE:
                    image_url = "file:///" + source
                else:
                    image_url = source

                message_field.append({"type": "image", "data": {"file": image_url}})

        # Send message
        contact = self.instance_config.contact
        target_id = int(contact.id)

        if contact.private:
            api.send_private_msg(target_id, message_field)
        else:
            api.send_group_msg(target_id, message_field)
