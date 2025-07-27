import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

from utils.wallet import wallet_manager
from services.buy_service import buy_token, estimate_buy_amount
from utils.chains import resolve_chain_alias, SUPPORTED_CHAINS
from utils.formatter import escape_markdown_v2

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /buy command"""
    if not update.message:
        return
        
    user_id = update.effective_user.id
    
    # Check if user has a wallet
    wallet = wallet_manager.get_user_wallet(user_id)
    if not wallet:
        await update.message.reply_text(
            "❌ *Wallet Not Found!*\n\n"
            "You don't have a wallet configured for trading.\n\n"
            "🔧 *To fix this:*\n"
            "• Use `/create` to create a new wallet\n"
            "• Use `/import <private_key>` to import an existing wallet\n\n"
            "⚠️ *Note:* You need a wallet with ETH balance to buy tokens."
        )
        return
    
    # Parse command arguments
    text = update.message.text.strip()
    parts = text.split()
    
    if len(parts) < 3:
        await update.message.reply_text(
            "❌ Invalid command format!\n\n"
            "Usage: /buy <chain> <contract_address> [amount_in_eth]\n\n"
            "Examples:\n"
            "/buy ethereum 0x1234567890abcdef1234567890abcdef12345678 0.1\n"
            "/buy polygon 0x1234567890abcdef1234567890abcdef12345678\n\n"
            "Supported chains: ethereum, polygon, base, arbitrum"
        )
        return
    
    # Extract parameters
    chain_input = parts[1]
    contract_address = parts[2]
    amount_in_eth = 0.01  # Default amount if not specified
    
    # Parse optional amount
    if len(parts) >= 4:
        try:
            amount_in_eth = float(parts[3])
            if amount_in_eth <= 0:
                await update.message.reply_text("❌ Amount must be greater than 0!")
                return
        except ValueError:
            await update.message.reply_text("❌ Invalid amount! Please provide a valid number.")
            return
    
    # Resolve chain alias
    chain = resolve_chain_alias(chain_input)
    if not chain:
        await update.message.reply_text(
            f"❌ Unsupported chain: {chain_input}\n\n"
            "Supported chains: ethereum, polygon, base, arbitrum"
        )
        return
    
    # Validate contract address
    if not re.match(r'^0x[a-fA-F0-9]{40}$', contract_address):
        await update.message.reply_text(
            "❌ Invalid contract address format!\n\n"
            "Contract address should be a 40-character hexadecimal string starting with '0x'."
        )
        return
    
    # Send initial message
    status_message = await update.message.reply_text(
        f"🔄 Processing buy order...\n"
        f"Chain: {chain}\n"
        f"Token: {contract_address}\n"
        f"Amount: {amount_in_eth} ETH"
    )
    
    try:
        # First, get an estimate
        estimate = await estimate_buy_amount(chain, contract_address, amount_in_eth, wallet["address"])
        
        if not estimate:
            await status_message.edit_text(
                "❌ Failed to get token information or estimate.\n\n"
                "Please check:\n"
                "• Contract address is correct\n"
                "• Token exists on the specified chain\n"
                "• You have sufficient balance"
            )
            return
        
        # Show estimate and ask for confirmation
        token_symbol = estimate.get("token_symbol", "Unknown")
        token_name = estimate.get("token_name", "Unknown")
        estimated_tokens = estimate.get("estimated_tokens", 0)
        price_usd = estimate.get("price_usd", 0)
        wallet_balance = estimate.get("wallet_balance")
        sufficient_balance = estimate.get("sufficient_balance", True)
        
        estimate_text = (
            f"📊 *Buy Estimate*\n\n"
            f"*Token:* {escape_markdown(token_name, version=2)} \\({escape_markdown(token_symbol, version=2)}\\)\n"
            f"*Contract:* `{escape_markdown(contract_address, version=2)}`\n"
            f"*Chain:* {escape_markdown(chain, version=2)}\n"
            f"*Amount:* {escape_markdown(str(amount_in_eth), version=2)} ETH\n"
            f"*Estimated Tokens:* {escape_markdown(f'{estimated_tokens:,.0f}', version=2)}\n"
            f"*Price:* ${escape_markdown(f'{price_usd:.6f}', version=2)}"
        )
        
        # Add balance information if available
        if wallet_balance is not None:
            balance_status = "✅" if sufficient_balance else "❌"
            estimate_text += f"\n*Wallet Balance:* {escape_markdown(f'{wallet_balance:.4f}', version=2)} ETH {balance_status}"
            
            if not sufficient_balance:
                estimate_text += f"\n\n⚠️ *Insufficient Balance!*\n"
                estimate_text += f"You need {escape_markdown(str(amount_in_eth), version=2)} ETH but have {escape_markdown(f'{wallet_balance:.4f}', version=2)} ETH"
        
        estimate_text += f"\n\n⚠️ *Warning:* This will execute a REAL transaction on the blockchain\\!\n"
        estimate_text += f"💰 *Real ETH will be spent*\n"
        estimate_text += f"⏱️ *Transaction cannot be reversed*"
        
        # Create confirmation buttons
        if wallet_balance is not None and not sufficient_balance:
            # Disable confirm button if insufficient balance
            keyboard = [
                [
                    InlineKeyboardButton("❌ Insufficient Balance", callback_data="insufficient_balance"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_buy")
                ]
            ]
        else:
            keyboard = [
                [
                    InlineKeyboardButton("✅ Confirm Buy", callback_data=f"confirm_buy_{chain}_{contract_address}_{amount_in_eth}"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_buy")
                ]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await status_message.edit_text(
            estimate_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        await status_message.edit_text(
            f"❌ Error processing buy order: {str(e)}"
        )

async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle buy confirmation callbacks"""
    if not update.callback_query:
        return
        
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check if user has a wallet
    wallet = wallet_manager.get_user_wallet(user_id)
    if not wallet:
        await query.edit_message_text("❌ Wallet not found!")
        return
    
    if query.data == "cancel_buy":
        await query.edit_message_text("❌ Buy order cancelled.")
        return
    
    if query.data == "insufficient_balance":
        await query.edit_message_text(
            "❌ *Insufficient Balance*\n\n"
            "You don't have enough ETH to complete this transaction.\n\n"
            "🔧 *Solutions:*\n"
            "• Add more ETH to your wallet\n"
            "• Use `/balance` to check your current balance\n"
            "• Try a smaller amount\n"
            "• Consider gas fees in your calculations",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return
    
    if query.data.startswith("confirm_buy_"):
        # Parse callback data: confirm_buy_<chain>_<contract>_<amount>
        parts = query.data.split("_")
        if len(parts) < 5:
            await query.edit_message_text("❌ Invalid callback data!")
            return
        
        chain = parts[2]
        contract_address = parts[3]
        amount_in_eth = float(parts[4])
        
        # Update message to show processing
        await query.edit_message_text(
            f"🔄 Executing buy transaction...\n\n"
            f"Chain: {chain}\n"
            f"Token: {contract_address}\n"
            f"Amount: {amount_in_eth} ETH\n\n"
            f"Please wait..."
        )
        
        try:
            # Execute the buy transaction
            result = await buy_token(chain, contract_address, amount_in_eth, wallet["private_key"])
            
            if result["success"]:
                # Format success message
                token_info = result.get("token_info", {})
                token_symbol = token_info.get("symbol", "Unknown")
                token_name = token_info.get("name", "Unknown")
                tx_hash = result.get("transaction_hash", "0x...")
                estimated_tokens = result.get("estimated_tokens", 0)
                
                success_text = (
                    f"✅ *Buy Transaction Successful\\!*\n\n"
                    f"*Token:* {escape_markdown(token_name, version=2)} \\({escape_markdown(token_symbol, version=2)}\\)\n"
                    f"*Amount:* {escape_markdown(str(amount_in_eth), version=2)} ETH\n"
                    f"*Tokens Received:* {escape_markdown(f'{estimated_tokens:,.0f}', version=2)}\n"
                    f"*Transaction Hash:* `{escape_markdown(tx_hash, version=2)}`\n"
                    f"*Chain:* {escape_markdown(chain, version=2)}\n\n"
                    f"🎉 Your tokens have been purchased successfully\\!"
                )
                
                await query.edit_message_text(
                    success_text,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            else:
                error_msg = result.get("error", "Unknown error")
                
                # Provide specific guidance based on error type
                if "Insufficient ETH balance" in error_msg:
                    guidance = (
                        f"💰 *Balance Issue*\n\n"
                        f"*Error:* {escape_markdown(error_msg, version=2)}\n\n"
                        f"🔧 *Solutions:*\n"
                        f"• Add more ETH to your wallet\n"
                        f"• Use `/balance` to check your current balance\n"
                        f"• Reduce the buy amount\n"
                        f"• Consider gas fees when calculating total cost"
                    )
                elif "Failed to check wallet balance" in error_msg:
                    guidance = (
                        f"🔍 *Connection Issue*\n\n"
                        f"*Error:* {escape_markdown(error_msg, version=2)}\n\n"
                        f"🔧 *Solutions:*\n"
                        f"• Check your internet connection\n"
                        f"• Verify ALCHEMY_API_KEY is configured\n"
                        f"• Try again in a few minutes"
                    )
                elif "Failed to build swap transaction" in error_msg:
                    guidance = (
                        f"🔄 *Swap Issue*\n\n"
                        f"*Error:* {escape_markdown(error_msg, version=2)}\n\n"
                        f"🔧 *Solutions:*\n"
                        f"• Verify ONEINCH_API_KEY is configured\n"
                        f"• Check if the token has sufficient liquidity\n"
                        f"• Try a different amount or token"
                    )
                else:
                    guidance = (
                        f"❌ *Transaction Failed*\n\n"
                        f"*Error:* {escape_markdown(error_msg, version=2)}\n\n"
                        f"Please try again or contact support if the problem persists\\."
                    )
                
                await query.edit_message_text(
                    guidance,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                
        except Exception as e:
            await query.edit_message_text(
                f"❌ *Transaction Error*\n\n"
                f"*Error:* {escape_markdown(str(e), version=2)}\n\n"
                f"Please try again later\\.",
                parse_mode=ParseMode.MARKDOWN_V2
            ) 