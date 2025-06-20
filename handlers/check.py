from __future__ import annotations

import os
from typing import Dict
import html

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from services.nodit_api import get_full_token_profile_from_nodit
from utils.chains import SUPPORTED_CHAINS, resolve_chain_alias
from utils.formatter import format_token_check_message, escape_markdown_v2



async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /check <chain> <token_address>
    Returns a token profile using Nodit's on-chain data.
    """
    if not update.message:
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: `/check <chain> <token_address>`", parse_mode=ParseMode.MARKDOWN_V2)
        return

    chain_input = context.args[0]
    address = context.args[1]

    chain = resolve_chain_alias(chain_input)

    if not chain:
        supported_names = ", ".join(SUPPORTED_CHAINS.keys())
        await update.message.reply_text(f"Unsupported chain: '{chain_input}'.\nSupported chains: {supported_names}")
        return

    chain_escaped = escape_markdown_v2(chain.capitalize())
    message = await update.message.reply_text(f"Fetching details for `{address}` on *{chain_escaped}*, please wait\\.\\.\\.", parse_mode=ParseMode.MARKDOWN_V2)

    token_data = await get_full_token_profile_from_nodit(chain, address)
    
    if not token_data:
        await message.edit_text("Failed to fetch token information from Nodit.")
        return

    if context.chat_data is not None:
        context.chat_data["checked_token"] = token_data
    
    token_data['rank'] = '🔹'
    token_data['chain_name'] = chain.capitalize()
    formatted_message = format_token_check_message(token_data)
    
    await message.edit_text(formatted_message, parse_mode=ParseMode.MARKDOWN_V2)
