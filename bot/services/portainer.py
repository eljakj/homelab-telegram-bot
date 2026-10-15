"""Portainer client — manages plain Docker containers via Portainer's API."""

from __future__ import annotations

import logging
from typing import Any

import requests

from ..config import Settings

logger = logging.getLogger(__name__)


class PortainerError(RuntimeError):
    """Raised whenever the Portainer API can't be reached or rejects a call."""


class PortainerClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = (
            f"{settings.portainer_url}/api/endpoints/{settings.portainer_endpoint_id}/docker"
        )
        self._headers = {"X-API-Key": settings.portainer_api_token}
        self._verify = settings.verify_tls

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self._base_url}{path}"
        try:
            response = requests.request(
                method, url, headers=self._headers, timeout=10, verify=self._verify, **kwargs
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("Portainer API request failed: %s %s", method, path)
            raise PortainerError(f"Portainer-API nicht erreichbar: {exc}") from exc
        if not response.content:
            return None
        return response.json()

    def list_containers(self) -> list[dict]:
        return self._request("GET", "/containers/json", params={"all": "true"}) or []

    def container_action(self, name: str, action: str) -> None:
        """action: start | stop | restart"""
        self._request("POST", f"/containers/{name}/{action}")
