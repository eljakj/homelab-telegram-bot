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
class PortainerEndpoint:
    """One Docker environment managed by Portainer (e.g. one VM)."""

    id: int
    label: str


def _parse_endpoints(raw: str) -> tuple[PortainerEndpoint, ...]:
    """Parses "3:VM101,4:VM103" into PortainerEndpoint(3, "VM101"), ...

    The label is just what shows up in the bot's menu — it has no meaning
    to Portainer itself. If omitted (just "3,4"), the numeric ID is reused
    as the label.
    """
    endpoints = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        id_str, _, label = item.partition(":")
        endpoints.append(PortainerEndpoint(id=int(id_str), label=label or id_str))
    if not endpoints:
        sys.exit("PORTAINER_ENDPOINTS must list at least one endpoint, e.g. '3:VM101'")
    return tuple(endpoints)


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
    portainer_endpoints: tuple[PortainerEndpoint, ...]

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
        portainer_endpoints=_parse_endpoints(_require("PORTAINER_ENDPOINTS")),
        verify_tls=os.environ.get("VERIFY_TLS", "false").lower() == "true",
    )