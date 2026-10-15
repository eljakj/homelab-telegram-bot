"""Single source of truth for 'is this chat allowed to use the bot?'."""

from __future__ import annotations

from telegram import Update

from .config import Settings


def is_authorized(update: Update, settings: Settings) -> bool:
    chat = update.effective_chat
    return chat is not None and chat.id == settings.allowed_chat_id
