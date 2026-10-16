"""Portainer client — manages plain Docker containers via Portainer's API.

Portainer can manage several Docker environments (one per host) through a
single API; each call below takes an explicit endpoint_id so the bot can
talk to all of them, not just one hardcoded host.
"""

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
        self._base_url = f"{settings.portainer_url}/api/endpoints"
        self._headers = {"X-API-Key": settings.portainer_api_token}
        self._verify = settings.verify_tls

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self._base_url}{path}"
        try:
            response = requests.request(
                method, url, headers=self._headers, timeout=30, verify=self._verify, **kwargs
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            logger.exception("Portainer API request failed: %s %s", method, path)
            detail = response.text.strip() or str(exc)
            raise PortainerError(f"Portainer-API-Fehler ({response.status_code}): {detail}") from exc
        except requests.RequestException as exc:
            logger.exception("Portainer API request failed: %s %s", method, path)
            raise PortainerError(f"Portainer-API nicht erreichbar: {exc}") from exc
        if not response.content:
            return None
        return response.json()

    def list_containers(self, endpoint_id: int) -> list[dict]:
        return (
            self._request(
                "GET", f"/{endpoint_id}/docker/containers/json", params={"all": "true"}
            )
            or []
        )

    def container_action(self, endpoint_id: int, name: str, action: str) -> None:
        """action: start | stop | restart"""
        self._request("POST", f"/{endpoint_id}/docker/containers/{name}/{action}")