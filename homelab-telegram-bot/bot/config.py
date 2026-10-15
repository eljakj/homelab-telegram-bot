"""Central configuration, loaded from environment variables.

Secrets never live in source code. Locally, a `.env` file (git-ignored) is
picked up via python-dotenv; in the container, the compose `env_file`
directive injects the same variables.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    bot_token: str
    allowed_chat_id: int

    proxmox_url: str
    proxmox_node: str
    proxmox_token_id: str
    proxmox_token_secret: str

    portainer_url: str
    portainer_api_token: str
    portainer_endpoint_id: int

    verify_tls: bool


def load_settings() -> Settings:
    return Settings(
        bot_token=_require("BOT_TOKEN"),
        allowed_chat_id=int(_require("ALLOWED_CHAT_ID")),
        proxmox_url=_require("PROXMOX_URL").rstrip("/"),
        proxmox_node=_require("PROXMOX_NODE"),
        proxmox_token_id=_require("PROXMOX_TOKEN_ID"),
        proxmox_token_secret=_require("PROXMOX_TOKEN_SECRET"),
        portainer_url=_require("PORTAINER_URL").rstrip("/"),
        portainer_api_token=_require("PORTAINER_API_TOKEN"),
        portainer_endpoint_id=int(_require("PORTAINER_ENDPOINT_ID")),
        verify_tls=os.environ.get("VERIFY_TLS", "false").lower() == "true",
    )
