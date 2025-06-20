from __future__ import annotations

from telegram import Update, constants
from telegram.ext import ContextTypes
import html


from services.ai_service import get_ai_analysis
from services.nodit_api import get_full_token_profile_from_nodit

from utils.chains import resolve_chain_alias, SUPPORTED_CHAINS
from utils.formatter import format_number, format_percent


async def analysis_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    token_data = None
    
   
    if context.args and len(context.args) >= 2:
        chain_input = context.args[0]
        address = context.args[1]
        
        chain = resolve_chain_alias(chain_input)
        if not chain:
            supported_names = ", ".join(SUPPORTED_CHAINS.keys())
            await update.message.reply_text(f"Unsupported chain: '{chain_input}'.\nSupported chains: {supported_names}")
            return
            
        message = await update.message.reply_text(f"Fetching data for {address} on {chain} before analysis...")
        
       
        token_data = await get_full_token_profile_from_nodit(chain, address)
        if not token_data:
            await message.edit_text("Failed to fetch token information. Please check the address and chain.")
            return
            
        if context.chat_data is not None:
            context.chat_data["checked_token"] = token_data


    else:
        if context.chat_data is None or "checked_token" not in context.chat_data:
            await update.message.reply_text(
                "Usage: /analysis <chain> <address>\nOr run /check on a token first."
            )
            return
        token_data = context.chat_data["checked_token"]

    if token_data:
        message = await update.message.reply_text("🤖 Conducting AI analysis, please wait...")
        try:
            analysis_text = get_ai_analysis(token_data)
            if not analysis_text or "Error:" in analysis_text:
                raise ValueError(analysis_text or "AI analysis returned an empty result.")

            name = html.escape(token_data.get('name') or 'Unknown')
            symbol = html.escape(token_data.get('symbol') or 'N/A')
            title = f"<b>🤖 AI Analysis for {name} ({symbol})</b>\n\n"

            await message.edit_text(title + analysis_text, parse_mode="HTML")

        except Exception as e:
            await message.edit_text(f"Sorry, the AI analysis failed. Error: {e}")

