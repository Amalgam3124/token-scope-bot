# handlers/daily.py

import asyncio
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from services import trending
from services.nodit_api import get_full_token_profile_from_nodit
from utils.formatter import format_token_check_message, escape_markdown_v2
from utils.chains import CHAIN_MAP

ALLOWED_CHAINS = {"ethereum", "polygon", "base"}
TOP_N_LIMIT = 5

async def daily_hot_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    message = await update.message.reply_text("🔄 Fetching the latest global hot list, please wait...")

    basic_tokens = trending.fetch_top_boosted_tokens()

    if not basic_tokens:
        await message.edit_text("❌ Could not fetch the hot list from Dexscreener. Please try again later.")
        return

    await message.edit_text(f"✅ Found {len(basic_tokens)} tokens. Fetching detailed information...")

    detailed_tokens = []
    for i, basic_token in enumerate(basic_tokens):
        chain_id = basic_token.get("chainId")
        token_address = basic_token.get("tokenAddress")
        
        if not chain_id or not token_address:
            continue
        if chain_id not in ALLOWED_CHAINS:
            continue
        detailed_token = trending.get_token_details_from_dexscreener(token_address, chain_id)
        if detailed_token:
            detailed_tokens.append(detailed_token)
        if len(detailed_tokens) >= TOP_N_LIMIT:
            break
        if i % 5 == 0:
            await message.edit_text(f"🔍 Fetching details for token {len(detailed_tokens)}/{TOP_N_LIMIT}...")

    if not detailed_tokens:
        await message.edit_text("❌ Could not fetch detailed token information. Please try again later.")
        return

    await message.edit_text(f"✅ Found {len(detailed_tokens)} tokens on allowed chains. Now fetching on-chain data...")

    full_profiles_for_summary = []
    results_text = []
    for i, token_ds in enumerate(detailed_tokens, 1):
        chain_id = token_ds.get("chainId")
        address = token_ds.get("tokenAddress")
        
        chain_name = CHAIN_MAP.get(chain_id)
        if not chain_name or not address:
            continue
        await message.edit_text(f"🔍 Fetching details for token {i}/{len(detailed_tokens)} on {chain_name.capitalize()}...")
        full_profile = await get_full_token_profile_from_nodit(chain_name, address)
        if full_profile:
            full_profile['chain_name'] = chain_name.capitalize()
            full_profile['rank'] = i
            full_profiles_for_summary.append(full_profile)
            formatted_string = format_token_check_message(full_profile)
            results_text.append(formatted_string)
        else:
            fallback_name = escape_markdown_v2(token_ds.get('baseToken', {}).get('name', 'Unknown'))
            chain_disp = escape_markdown_v2(chain_name.capitalize())
            fail_msg = escape_markdown_v2("Could not retrieve on-chain data.")
            rank_escaped = escape_markdown_v2(f"{i}.")
            results_text.append(f"*{rank_escaped} {fallback_name}* on {chain_disp}\n\\- {fail_msg}")
        await asyncio.sleep(0.5)

    context.bot_data['daily_results'] = full_profiles_for_summary

    buttons = []
    button_row = []
    for profile in full_profiles_for_summary:
        rank = profile['rank']
        button = InlineKeyboardButton(
            text=f"🧠 Summary #{rank}",
            callback_data=f"summary_{rank}"
        )
        button_row.append(button)
        if len(button_row) == 3:
            buttons.append(button_row)
            button_row = []
    if button_row:
        buttons.append(button_row)
    
    reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

    now = datetime.now(timezone.utc)
    datetime_str = escape_markdown_v2(now.strftime('%Y-%m-%d %H:%M UTC'))
    final_header = (
        f"🔥 *Top {len(results_text)} Trending Tokens \\(ETH, POL, BASE\\)*\n"
        f"On\\-chain data from Nodit \\| _{datetime_str}_\n"
    )
    final_message = final_header + "\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\n\n" + "\n\n".join(results_text)
    
    await message.edit_text(
        final_message, 
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup
    ) 