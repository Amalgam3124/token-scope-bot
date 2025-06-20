# bot.py
import os
import logging
from dotenv import load_dotenv

from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue, CallbackQueryHandler
from telegram.constants import ParseMode

from handlers.daily import daily_hot_list
from handlers.summary import summary_command, summary_callback
from handlers.check import check_command
from handlers.analysis import analysis_command


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
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
        "Welcome to the Nodit TokenScope Bot\\!\n\n"
        "*Available commands:*\n"
        "`/daily` \\- Get the top trending tokens\\.\n"
        "`/summary <rank>` \\- Get an AI analysis for a token from the daily list\\.\n"
        "`/check <chain> <address>` \\- Get a quick overview of a token\\.\n"
        "`/analysis <chain> <address>` \\- Get a detailed AI analysis of a token\\.\n\n"
        "Just type a command to get started\\!"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN_V2)

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
        ]
        await application.bot.set_my_commands(commands)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)


def main() -> None:
    print("Starting bot...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("daily", daily_hot_list))
    application.add_handler(CommandHandler("summary", summary_command))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("analysis", analysis_command))

    application.add_handler(CallbackQueryHandler(summary_callback, pattern="^summary_"))

    application.add_error_handler(error_handler)
    
    if application.job_queue:
        application.job_queue.run_once(set_bot_commands, 0, data=application)

    print("Bot is running. Press Ctrl-C to stop.")
    application.run_polling()


if __name__ == "__main__":
    main()