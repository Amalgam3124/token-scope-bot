import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

from utils.wallet import wallet_manager
from services.balance_service import get_wallet_balances
from utils.chains import resolve_chain_alias, SUPPORTED_CHAINS
from utils.formatter import escape_markdown_v2

async def create_wallet_command(update, context):
    if not update.message:
        return
    user_id = update.effective_user.id
    existing = wallet_manager.get_user_wallet(user_id)
    if existing:
        await update.message.reply_text(
            "⚠️ You already have a wallet! Please use /delete to remove it before creating a new one."
        )
        return
    result = wallet_manager.generate_wallet(user_id)
    private_key = escape_markdown(result["private_key"], version=2)
    address = escape_markdown(result["address"], version=2)
    message = (
        "✅ *Wallet Created Successfully\!*  \n"
        f"*Address:* `{address}`  \n"
        f"*Private Key:* `{private_key}`  \n"
        "⚠️ *Important:* Save your private key securely\! It will not be shown again\."
    )
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)

async def import_wallet_command(update, context):
    if not update.message:
        return
    user_id = update.effective_user.id
    existing = wallet_manager.get_user_wallet(user_id)
    if existing:
        await update.message.reply_text(
            "⚠️ You already have a wallet! Please use /delete to remove it before importing a new one."
        )
        return
    text = update.message.text.strip()
    parts = text.split()
    if len(parts) < 2:
        await update.message.reply_text(
            "❌ Please provide your private key!\n\n"
            "Usage: /import <private_key>\n\n"
            "⚠️ Warning: Never share your private key with others!"
        )
        return
    private_key = parts[1]
    if not re.match(r'^0x[a-fA-F0-9]{64}$', private_key):
        await update.message.reply_text(
            "❌ Invalid private key format!\n\n"
            "Private key should be a 64-character hexadecimal string starting with '0x'."
        )
        return
    result = wallet_manager.import_wallet(user_id, private_key)
    if "error" in result:
        await update.message.reply_text(f"❌ Error: {result['error']}")
        return
    private_key_md = escape_markdown(private_key, version=2)
    address = escape_markdown(result["address"], version=2)
    message = (
        "✅ *Wallet Imported Successfully\!*  \n"
        f"*Address:* `{address}`  \n"
        f"*Private Key:* `{private_key_md}`  \n"
    )
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)

async def delete_wallet_command(update, context):
    if not update.message:
        return
    user_id = update.effective_user.id
    wallet = wallet_manager.get_user_wallet(user_id)
    if not wallet:
        await update.message.reply_text("❌ You don't have a wallet to delete!")
        return
    result = wallet_manager.delete_wallet(user_id, wallet["address"])
    if "error" in result:
        await update.message.reply_text(f"❌ Error: {result['error']}")
    else:
        address = escape_markdown(wallet["address"], version=2)
        await update.message.reply_text(
            f"✅ Wallet deleted successfully\!  \n*Address:* `{address}`",
            parse_mode=ParseMode.MARKDOWN_V2
        )

async def balance_command(update, context):
    if not update.message:
        return
    user_id = update.effective_user.id
    wallet = wallet_manager.get_user_wallet(user_id)
    if not wallet:
        await update.message.reply_text(
            "❌ You don't have a wallet!\n\nUse /create to create a wallet first."
        )
        return
    text = update.message.text.strip()
    parts = text.split()
    address = wallet["address"]
    chain = "ethereum"
    specific_token = None
    if len(parts) >= 2:
        chain_input = parts[1]
        resolved_chain = resolve_chain_alias(chain_input)
        if resolved_chain:
            chain = resolved_chain
        else:
            await update.message.reply_text(
                f"❌ Unsupported chain: {chain_input}\n\nSupported chains: {', '.join(SUPPORTED_CHAINS.keys())}"
            )
            return
    if len(parts) >= 3:
        specific_token = parts[2]
        if not re.match(r'^0x[a-fA-F0-9]{40}$', specific_token):
            await update.message.reply_text("❌ Invalid token address format!")
            return
    status_message = await update.message.reply_text("🔄 Fetching balance, please wait...")
    try:
        balance_data = await get_wallet_balances(chain, address, specific_token)
        if not balance_data["balances"]:
            escaped_address = escape_markdown_v2(address)
            escaped_chain = escape_markdown_v2(chain.capitalize())
            await status_message.edit_text(
                f"💼 *No balances found*  \n*Wallet:* `{escaped_address}`  \n*Chain:* {escaped_chain}",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
        escaped_address = escape_markdown_v2(address)
        escaped_chain = escape_markdown_v2(chain.capitalize())
        message = f"💼 *Wallet Balance*  \n*Wallet:* `{escaped_address}`  \n*Chain:* {escaped_chain}  \n\n"
        for balance in balance_data["balances"]:
            symbol = escape_markdown_v2(balance["symbol"])
            name = escape_markdown_v2(balance["name"])
            amount = escape_markdown_v2(balance["balance"])
            message += f"*{symbol}* \\(_{name}_\\)  \n`{amount}`  \n\n"
        buttons = []
        for supported_chain in SUPPORTED_CHAINS.keys():
            if supported_chain != chain:
                button = InlineKeyboardButton(
                    text=f"🔄 {supported_chain.capitalize()}",
                    callback_data=f"balance_{address}_{supported_chain}"
                )
                buttons.append(button)
        reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None
        await status_message.edit_text(
            message,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
    except Exception as e:
        error_msg = escape_markdown_v2(f"❌ Error fetching balance: {str(e)}")
        await status_message.edit_text(
            error_msg,
            parse_mode=ParseMode.MARKDOWN_V2
        )

async def wallet_callback(update, context):
    if not update.callback_query:
        return
    query = update.callback_query
    data = query.data
    if data.startswith("delete_wallet_"):
        address = data.replace("delete_wallet_", "")
        user_id = update.effective_user.id
        result = wallet_manager.delete_wallet(user_id, address)
        if "error" in result:
            await query.answer(f"Error: {result['error']}")
        else:
            await query.answer("Wallet deleted successfully!")
            await query.edit_message_text("✅ Wallet deleted successfully!")
    elif data.startswith("balance_"):
        parts = data.split("_")
        if len(parts) >= 3:
            address = parts[1]
            chain = parts[2]
            await query.answer("Fetching balance...")
            try:
                balance_data = await get_wallet_balances(chain, address)
                if not balance_data["balances"]:
                    escaped_address = escape_markdown_v2(address)
                    escaped_chain = escape_markdown_v2(chain.capitalize())
                    await query.edit_message_text(
                        f"💼 *No balances found*  \n*Wallet:* `{escaped_address}`  \n*Chain:* {escaped_chain}",
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                    return
                escaped_address = escape_markdown_v2(address)
                escaped_chain = escape_markdown_v2(chain.capitalize())
                message = f"💼 *Wallet Balance*  \n*Wallet:* `{escaped_address}`  \n*Chain:* {escaped_chain}  \n\n"
                for balance in balance_data["balances"]:
                    symbol = escape_markdown_v2(balance["symbol"])
                    name = escape_markdown_v2(balance["name"])
                    amount = escape_markdown_v2(balance["balance"])
                    message += f"*{symbol}* \\(_{name}_\\)  \n`{amount}`  \n\n"
                buttons = []
                for supported_chain in SUPPORTED_CHAINS.keys():
                    if supported_chain != chain:
                        button = InlineKeyboardButton(
                            text=f"🔄 {supported_chain.capitalize()}",
                            callback_data=f"balance_{address}_{supported_chain}"
                        )
                        buttons.append(button)
                reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None
                await query.edit_message_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=reply_markup
                )
            except Exception as e:
                error_msg = escape_markdown_v2(f"❌ Error fetching balance: {str(e)}")
                await query.edit_message_text(
                    error_msg,
                    parse_mode=ParseMode.MARKDOWN_V2
                ) 