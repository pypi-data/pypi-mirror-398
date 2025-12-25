import base64
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests


def image_to_base64(source: str) -> str:
    """Convert image URL or local path to base64 string"""
    if source.startswith(("http://", "https://")):
        response = requests.get(source)
        response.raise_for_status()
        return base64.b64encode(response.content).decode()
    elif source.startswith("file://"):
        parsed = urlparse(source)
        path = Path(unquote(parsed.path.lstrip("/")))
        return base64.b64encode(path.read_bytes()).decode()


class OneBotAPIClient:
    def __init__(self, url: str, token: str | None = None, proxies: dict | None = None):
        self.url = url.rstrip("/")
        self.token = token
        self.proxies = proxies

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def send_private_msg(self, user_id: int, message: list[dict]) -> dict:
        response = requests.post(
            f"{self.url}/send_private_msg",
            json={"user_id": user_id, "message": message},
            headers=self._headers(),
            proxies=self.proxies,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "failed":
            raise Exception(data.get("message", data))
        return data

    def send_group_msg(self, group_id: int, message: list[dict]) -> dict:
        response = requests.post(
            f"{self.url}/send_group_msg",
            json={"group_id": group_id, "message": message},
            headers=self._headers(),
            proxies=self.proxies,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "failed":
            raise Exception(data.get("message", data))
        return data
