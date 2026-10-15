"""Builds and shows the inline-keyboard menus."""

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
        [InlineKeyboardButton("🔄 Reboot", callback_data="confirm_host_reboot")],
        [InlineKeyboardButton("⏻ Shutdown", callback_data="confirm_host_shutdown")],
        [InlineKeyboardButton("◀️ Zurück", callback_data="menu_main")],
    ]
    await update.callback_query.edit_message_text("Proxmox-Host:", reply_markup=InlineKeyboardMarkup(kb))


async def vms_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    proxmox = context.bot_data["proxmox"]
    resources = proxmox.list_resources()

    kb = []
    for r in resources:
        icon = "🟢" if r.get("status") == "running" else "🔴"
        label = f"{icon} {r.get('vmid')} {r.get('name')}"
        kb.append([InlineKeyboardButton(label, callback_data=f"vm_{r.get('type')}_{r.get('vmid')}")])
    kb.append([InlineKeyboardButton("◀️ Zurück", callback_data="menu_main")])

    await update.callback_query.edit_message_text("VMs & Container:", reply_markup=InlineKeyboardMarkup(kb))


async def vm_detail_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, vtype: str, vmid: str) -> None:
    kb = [
        [InlineKeyboardButton("▶️ Start", callback_data=f"do_{vtype}_start_{vmid}")],
        [InlineKeyboardButton("🔄 Reboot", callback_data=f"confirm_{vtype}_reboot_{vmid}")],
        [InlineKeyboardButton("⏹️ Stop", callback_data=f"confirm_{vtype}_stop_{vmid}")],
        [InlineKeyboardButton("◀️ Zurück", callback_data="menu_vms")],
    ]
    await update.callback_query.edit_message_text(f"{vtype.upper()} {vmid}:", reply_markup=InlineKeyboardMarkup(kb))


async def docker_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    portainer = context.bot_data["portainer"]
    containers = portainer.list_containers()

    kb = []
    for c in containers:
        name = c["Names"][0].lstrip("/")
        icon = "🟢" if c["State"] == "running" else "🔴"
        kb.append([InlineKeyboardButton(f"{icon} {name}", callback_data=f"docker_{name}")])
    kb.append([InlineKeyboardButton("◀️ Zurück", callback_data="menu_main")])

    await update.callback_query.edit_message_text("Docker-Container:", reply_markup=InlineKeyboardMarkup(kb))


async def docker_detail_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str) -> None:
    kb = [
        [InlineKeyboardButton("▶️ Start", callback_data=f"do_docker_start_{name}")],
        [InlineKeyboardButton("🔄 Restart", callback_data=f"confirm_docker_restart_{name}")],
        [InlineKeyboardButton("⏹️ Stop", callback_data=f"confirm_docker_stop_{name}")],
        [InlineKeyboardButton("◀️ Zurück", callback_data="menu_docker")],
    ]
    await update.callback_query.edit_message_text(f"Container: {name}", reply_markup=InlineKeyboardMarkup(kb))


async def ask_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, action_data: str) -> None:
    kb = [
        [InlineKeyboardButton("✅ Bestätigen", callback_data=f"do_{action_data}")],
        [InlineKeyboardButton("❌ Abbrechen", callback_data="menu_main")],
    ]
    label = action_data.replace("_", " ")
    await update.callback_query.edit_message_text(f"Sicher? {label}", reply_markup=InlineKeyboardMarkup(kb))
