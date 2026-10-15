"""Entry point: wires up config, clients and handlers, then starts polling."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from .config import load_settings
from .handlers import actions, menu
from .logging_config import setup_logging
from .services.portainer import PortainerClient
from .services.proxmox import ProxmoxClient

logger = logging.getLogger(__name__)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled exception while processing an update", exc_info=context.error)
    if isinstance(update, Update) and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Da ist etwas schiefgelaufen. Details stehen im Log.",
            )
        except Exception:  # noqa: BLE001 - best-effort notification only
            logger.exception("Failed to notify chat about the error above")


def main() -> None:
    setup_logging()
    settings = load_settings()

    application = Application.builder().token(settings.bot_token).build()
    application.bot_data["settings"] = settings
    application.bot_data["proxmox"] = ProxmoxClient(settings)
    application.bot_data["portainer"] = PortainerClient(settings)

    application.add_handler(CommandHandler("start", menu.main_menu))
    application.add_handler(CommandHandler("menu", menu.main_menu))
    application.add_handler(CallbackQueryHandler(actions.button_handler))
    application.add_error_handler(on_error)

    logger.info("Telegram control bot starting (long polling)")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
