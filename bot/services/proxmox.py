"""Proxmox VE client.

Talks to the official REST API with a scoped API token, instead of shelling
out to `qm` / `pct` / `pvesh` as root. This is what lets the bot run as an
unprivileged container anywhere on the network, rather than living on the
hypervisor itself.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from ..config import Settings

logger = logging.getLogger(__name__)

# Maps the bot's internal action name to the Proxmox API's status command.
# "stop" intentionally maps to a graceful ACPI shutdown, not a hard "stop".
_VM_ACTIONS = {"start": "start", "stop": "shutdown", "reboot": "reboot"}


class ProxmoxError(RuntimeError):
    """Raised whenever the Proxmox API can't be reached or rejects a call."""


class ProxmoxClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = f"{settings.proxmox_url}/api2/json"
        self._node = settings.proxmox_node
        self._verify = settings.verify_tls
        self._headers = {
            "Authorization": (
                f"PVEAPIToken={settings.proxmox_token_id}={settings.proxmox_token_secret}"
            )
        }

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self._base_url}{path}"
        try:
            response = requests.request(
                method, url, headers=self._headers, timeout=10, verify=self._verify, **kwargs
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("Proxmox API request failed: %s %s", method, path)
            raise ProxmoxError(f"Proxmox-API nicht erreichbar: {exc}") from exc
        if not response.content:
            return None
        return response.json().get("data")

    def list_resources(self) -> list[dict]:
        """All VMs and LXCs across the cluster, with their live status."""
        return self._request("GET", "/cluster/resources", params={"type": "vm"}) or []

    def vm_action(self, vtype: str, vmid: str, action: str) -> None:
        """Start/stop/reboot a single VM (qemu) or container (lxc)."""
        if action not in _VM_ACTIONS:
            raise ValueError(f"Unknown VM action: {action}")
        kind = "qemu" if vtype == "qemu" else "lxc"
        proxmox_action = _VM_ACTIONS[action]
        self._request("POST", f"/nodes/{self._node}/{kind}/{vmid}/status/{proxmox_action}")

    def node_power(self, command: str) -> None:
        """Reboot or shut down the Proxmox host itself."""
        if command not in ("reboot", "shutdown"):
            raise ValueError(f"Unknown node power command: {command}")
        self._request("POST", f"/nodes/{self._node}/status", data={"command": command})
