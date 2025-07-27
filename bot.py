# bot.py
import os
import logging
from dotenv import load_dotenv
import asyncio

from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue, CallbackQueryHandler
from telegram.constants import ParseMode

from handlers.daily import daily_hot_list
from handlers.summary import summary_command, summary_callback
from handlers.check import check_command
from handlers.analysis import analysis_command
from handlers.wallet import (
    create_wallet_command,
    import_wallet_command,
    delete_wallet_command,
    balance_command,
    wallet_callback
)
from handlers.buy import buy_command, buy_callback
from handlers.send import send_command, send_callback


load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN") or ""
if not BOT_TOKEN:
    raise ValueError("Error: BOT_TOKEN is not configured in .env file.")


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    welcome_text = (
        "Welcome to the Nodit TokenScope Bot!\n\n"
        "Available commands:\n"
        "/daily - Get the top trending tokens\n"
        "/summary <rank> - Get an AI analysis for a token from the daily list\n"
        "/check <chain> <address> - Get a quick overview of a token\n"
        "/analysis <chain> <address> - Get a detailed AI analysis of a token\n\n"
        "Wallet Commands:\n"
        "/create - Create a new wallet\n"
        "/import <private_key> - Import existing wallet\n"
        "/wallets - List your wallet\n"
        "/delete - Delete your wallet\n"
        "/balance [chain] [token_address] - Check wallet balance\n"
        "/buy <chain> <contract_address> [amount] - Buy tokens\n"
        "/send <chain> <address> <amount> <token> - Send tokens\n\n"
        "Just type or tap a command to get started!"
    )
    await update.message.reply_text(welcome_text)

async def set_bot_commands(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets the bot's commands in the Telegram UI for user convenience."""
    if context.job and isinstance(context.job.data, Application):
        application = context.job.data
        commands = [
            BotCommand("start", "Show welcome message"),
            BotCommand("daily", "Top trending tokens"),
            BotCommand("summary", "AI summary for a daily token"),
            BotCommand("check", "Quick token overview"),
            BotCommand("analysis", "Detailed AI analysis"),
            BotCommand("create", "Create new wallet"),
            BotCommand("import", "Import existing wallet"),
            BotCommand("delete", "Delete your wallet"),
            BotCommand("balance", "Check wallet balance"),
            BotCommand("buy", "Buy tokens"),
            BotCommand("send", "Send tokens"),
        ]
        await application.bot.set_my_commands(commands)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)


def main() -> None:
    print("Starting bot...")

    application = Application.builder().token(BOT_TOKEN).build()

    # Register commands on startup using job_queue (safe for event loop)
    if application.job_queue:
        application.job_queue.run_once(set_bot_commands, 0, data=application)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("daily", daily_hot_list))
    application.add_handler(CommandHandler("summary", summary_command))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("analysis", analysis_command))
    application.add_handler(CommandHandler("create", create_wallet_command))
    application.add_handler(CommandHandler("import", import_wallet_command))
    application.add_handler(CommandHandler("delete", delete_wallet_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("send", send_command))
    application.add_handler(CallbackQueryHandler(summary_callback, pattern="^summary_"))
    application.add_handler(CallbackQueryHandler(wallet_callback, pattern="^(delete_wallet_|balance_)"))
    application.add_handler(CallbackQueryHandler(buy_callback, pattern="^(confirm_buy_|cancel_buy|insufficient_balance)"))
    application.add_handler(CallbackQueryHandler(send_callback, pattern="^(confirm_send_|cancel_send|insufficient_balance_send)"))
    application.add_error_handler(error_handler)
    print("Bot is running. Press Ctrl-C to stop.")
    application.run_polling()


if __name__ == "__main__":
    main()