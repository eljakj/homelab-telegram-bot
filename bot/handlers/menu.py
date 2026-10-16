"""Builds and shows the inline-keyboard menus.

Callback data uses ":" as the separator between the fixed action tokens and
the dynamic part (a VM ID or a container name), e.g. "qemu:101" or
"docker:3:vaultwarden". Using ":" instead of "_" means a container name is
free to contain underscores or hyphens without breaking the parsing in
handlers/actions.py.
"""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from ..auth import is_authorized


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = context.bot_data["settings"]
    if not is_authorized(update, settings):
        return

    kb = [
        [InlineKeyboardButton("🖥️ Proxmox-Host", callback_data="menu_host")],
        [InlineKeyboardButton("📦 VMs & Container", callback_data="menu_vms")],
        [InlineKeyboardButton("🐳 Docker-Container", callback_data="menu_docker")],
    ]
    text = "Was möchtest du steuern?"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))


async def host_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    kb = [
        [InlineKeyboardButton("🔄 Reboot", callback_data="confirm_host:reboot")],
        [InlineKeyboardButton("⏻ Shutdown", callback_data="confirm_host:shutdown")],
        [InlineKeyboardButton("◀️ Zurück", callback_data="menu_main")],
    ]
    await update.callback_query.edit_message_text("Proxmox-Host:", reply_markup=InlineKeyboardMarkup(kb))


async def vms_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    proxmox = context.bot_data["proxmox"]
    resources = proxmox.list_resources()

    kb = []
    for r in resources:
        vtype = r.get("type")
        vmid = r.get("vmid")
        icon = "🟢" if r.get("status") == "running" else "🔴"
        label = f"{icon} {vmid} {r.get('name')}"
        kb.append([InlineKeyboardButton(label, callback_data=f"{vtype}:{vmid}")])
    kb.append([InlineKeyboardButton("◀️ Zurück", callback_data="menu_main")])

    await update.callback_query.edit_message_text("VMs & Container:", reply_markup=InlineKeyboardMarkup(kb))


async def vm_detail_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, vtype: str, vmid: str) -> None:
    kb = [
        [InlineKeyboardButton("▶️ Start", callback_data=f"do_{vtype}:start:{vmid}")],
        [InlineKeyboardButton("🔄 Reboot", callback_data=f"confirm_{vtype}:reboot:{vmid}")],
        [InlineKeyboardButton("⏹️ Stop", callback_data=f"confirm_{vtype}:stop:{vmid}")],
        [InlineKeyboardButton("◀️ Zurück", callback_data="menu_vms")],
    ]
    await update.callback_query.edit_message_text(f"{vtype.upper()} {vmid}:", reply_markup=InlineKeyboardMarkup(kb))


async def docker_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    portainer = context.bot_data["portainer"]
    settings = context.bot_data["settings"]

    kb = []
    for endpoint in settings.portainer_endpoints:
        containers = portainer.list_containers(endpoint.id)
        for c in containers:
            name = c["Names"][0].lstrip("/")
            icon = "🟢" if c["State"] == "running" else "🔴"
            label = f"{icon} [{endpoint.label}] {name}"
            kb.append([InlineKeyboardButton(label, callback_data=f"docker:{endpoint.id}:{name}")])
    kb.append([InlineKeyboardButton("◀️ Zurück", callback_data="menu_main")])

    await update.callback_query.edit_message_text("Docker-Container:", reply_markup=InlineKeyboardMarkup(kb))


async def docker_detail_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE, endpoint_id: int, name: str
) -> None:
    kb = [
        [InlineKeyboardButton("▶️ Start", callback_data=f"do_docker:start:{endpoint_id}:{name}")],
        [InlineKeyboardButton("🔄 Restart", callback_data=f"confirm_docker:restart:{endpoint_id}:{name}")],
        [InlineKeyboardButton("⏹️ Stop", callback_data=f"confirm_docker:stop:{endpoint_id}:{name}")],
        [InlineKeyboardButton("◀️ Zurück", callback_data="menu_docker")],
    ]
    await update.callback_query.edit_message_text(f"Container: {name}", reply_markup=InlineKeyboardMarkup(kb))


async def ask_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, action_data: str) -> None:
    kb = [
        [InlineKeyboardButton("✅ Bestätigen", callback_data=f"do_{action_data}")],
        [InlineKeyboardButton("❌ Abbrechen", callback_data="menu_main")],
    ]
    label = action_data.replace(":", " ")
    await update.callback_query.edit_message_text(f"Sicher? {label}", reply_markup=InlineKeyboardMarkup(kb))
