"""Routes button presses to the right menu or the right side-effecting action."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from ..auth import is_authorized
from ..services.portainer import PortainerError
from ..services.proxmox import ProxmoxError
from . import menu

logger = logging.getLogger(__name__)


async def execute_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action_data: str) -> None:
    proxmox = context.bot_data["proxmox"]
    portainer = context.bot_data["portainer"]
    parts = action_data.split("_")
    target = parts[0]

    try:
        if target == "host":
            command = "reboot" if parts[1] == "reboot" else "shutdown"
            proxmox.node_power(command)
            msg = "🔄 Host wird neu gestartet..." if command == "reboot" else "⏻ Host wird heruntergefahren..."
        elif target in ("qemu", "lxc"):
            action, vmid = parts[1], parts[2]
            proxmox.vm_action(target, vmid, action)
            msg = f"✅ {target.upper()} {vmid}: {action} ausgeführt."
        elif target == "docker":
            action, name = parts[1], parts[2]
            portainer.container_action(name, action)
            msg = f"✅ Docker-Container {name}: {action} ausgeführt."
        else:
            msg = "Unbekannte Aktion."
    except (ProxmoxError, PortainerError) as exc:
        logger.error("Action '%s' failed: %s", action_data, exc)
        msg = f"❌ Aktion fehlgeschlagen: {exc}"

    await update.callback_query.edit_message_text(msg)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = context.bot_data["settings"]
    if not is_authorized(update, settings):
        return

    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_main":
        await menu.main_menu(update, context)
    elif data == "menu_host":
        await menu.host_menu(update, context)
    elif data == "menu_vms":
        await menu.vms_menu(update, context)
    elif data == "menu_docker":
        await menu.docker_menu(update, context)
    elif data.startswith("vm_"):
        _, vtype, vmid = data.split("_")
        await menu.vm_detail_menu(update, context, vtype, vmid)
    elif data.startswith("docker_"):
        name = data.split("_", 1)[1]
        await menu.docker_detail_menu(update, context, name)
    elif data.startswith("confirm_"):
        await menu.ask_confirm(update, context, data[len("confirm_"):])
    elif data.startswith("do_"):
        await execute_action(update, context, data[len("do_"):])
