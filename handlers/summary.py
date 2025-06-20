# handlers/summary.py
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from services.ai_service import get_ai_analysis
from utils.formatter import escape_markdown_v2

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    try:
        rank_to_find = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text(
            "Please provide a valid rank number from the last /daily list.\n"
            "Example: `/summary 2`",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    daily_results = context.bot_data.get('daily_results', [])
    if not daily_results:
        await update.message.reply_text("Please run the `/daily` command first to get a list of tokens.")
        return

    token_data = next((token for token in daily_results if token.get('rank') == rank_to_find), None)

    if not token_data:
        await update.message.reply_text(f"Could not find a token with rank {rank_to_find}. Please check the rank number.")
        return

    token_name = escape_markdown_v2(token_data.get('name', 'Unknown'))
    message = await update.message.reply_text(f"🤖 Generating AI analysis for *{token_name}*...")

    ai_summary = get_ai_analysis(token_data)
    
    header = f"🧠 *AI Analysis for {token_name}*\n"
    final_message = header + escape_markdown_v2(ai_summary)

    await message.edit_text(final_message, parse_mode=ParseMode.MARKDOWN_V2)

async def summary_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles button clicks for summary requests from the /daily list."""
    query = update.callback_query
    if not query or not query.data:
        return
        
    await query.answer()

    try:
        rank_to_find = int(query.data.split('_')[1])
    except (IndexError, ValueError):
        await query.edit_message_text("Error: Invalid button data.", reply_markup=None)
        return

    daily_results = context.bot_data.get('daily_results', [])
    if not daily_results:
        await query.edit_message_text(
            "The data from `/daily` has expired. Please run the command again.",
            reply_markup=None
        )
        return

    token_data = next((token for token in daily_results if token.get('rank') == rank_to_find), None)
    if not token_data:
        await query.edit_message_text(
            f"Error: Could not find rank {rank_to_find}. The list might have been updated.",
            reply_markup=None
        )
        return

    token_name = escape_markdown_v2(token_data.get('name', 'Unknown'))
    
    if query.message:
        await query.message.reply_text(
            f"🤖 Generating AI analysis for *{token_name}*\\.\\.\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )

    ai_summary = get_ai_analysis(token_data)
    
    header = f"🧠 *AI Analysis for {token_name}*\n\n"
    final_message = header + escape_markdown_v2(ai_summary)

    if query.message:
        await query.message.reply_text(final_message, parse_mode=ParseMode.MARKDOWN_V2)
    
    await query.edit_message_reply_markup(reply_markup=None) 