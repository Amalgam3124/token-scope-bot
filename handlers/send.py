import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

from utils.wallet import wallet_manager
from services.send_service import send_token, estimate_send_fee
from utils.chains import resolve_chain_alias, SUPPORTED_CHAINS
from utils.formatter import escape_markdown_v2

async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /send command"""
    if not update.message:
        return
        
    user_id = update.effective_user.id
    
    # Check if user has a wallet
    wallet = wallet_manager.get_user_wallet(user_id)
    if not wallet:
        await update.message.reply_text(
            "❌ *Wallet Not Found\\!*\n\n"
            "You don't have a wallet configured for sending\\.\n\n"
            "🔧 *To fix this:*\n"
            "• Use `/create` to create a new wallet\n"
            "• Use `/import <private_key>` to import an existing wallet\n\n"
            "⚠️ *Note:* You need a wallet with sufficient balance to send tokens\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return
    
    # Parse command arguments
    text = update.message.text.strip()
    parts = text.split()
    
    if len(parts) < 4:
        await update.message.reply_text(
            "❌ *Invalid command format\\!*\n\n"
            "Usage: `/send <chain> <address> <amount> <token>`\n\n"
            "Examples:\n"
            "• `/send ethereum 0x1234\\.\\.\\. 0\\.1 eth`\n"
            "• `/send polygon 0x1234\\.\\.\\. 100 usdt`\n"
            "• `/send base 0x1234\\.\\.\\. 50 usdc`\n\n"
            "Supported chains: ethereum, polygon, base, arbitrum\n"
            "Supported tokens: ETH, USDT, USDC",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return
    
    # Extract parameters
    chain_input = parts[1]
    recipient_address = parts[2]
    amount_str = parts[3]
    token_symbol = parts[4].upper() if len(parts) > 4 else "ETH"
    
    # Parse amount
    try:
        amount = float(amount_str)
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be greater than 0\\!")
            return
    except ValueError:
        await update.message.reply_text("❌ Invalid amount\\! Please provide a valid number\\.")
        return
    
    # Resolve chain alias
    chain = resolve_chain_alias(chain_input)
    if not chain:
        await update.message.reply_text(
            f"❌ Unsupported chain: {chain_input}\n\n"
            "Supported chains: ethereum, polygon, base, arbitrum"
        )
        return
    
    # Validate recipient address
    if not re.match(r'^0x[a-fA-F0-9]{40}$', recipient_address):
        await update.message.reply_text(
            "❌ Invalid recipient address format\\!\n\n"
            "Address should be a 40\\-character hexadecimal string starting with '0x'\\."
        )
        return
    
    # Validate token
    supported_tokens = ["ETH", "USDT", "USDC"]
    if token_symbol not in supported_tokens:
        await update.message.reply_text(
            f"❌ Unsupported token: {token_symbol}\n\n"
            "Supported tokens: ETH, USDT, USDC"
        )
        return
    
    # Send initial message
    status_message = await update.message.reply_text(
        f"🔄 Processing send transaction...\n"
        f"Chain: {chain}\n"
        f"To: {recipient_address[:10]}...{recipient_address[-8:]}\n"
        f"Amount: {amount} {token_symbol}"
    )
    
    try:
        # Get fee estimate
        fee_estimate = await estimate_send_fee(
            chain=chain,
            recipient_address=recipient_address,
            amount=amount,
            token_symbol=token_symbol,
            wallet_address=wallet["address"]
        )
        
        if not fee_estimate:
            await status_message.edit_text(
                "❌ Failed to estimate transaction fee.\n\n"
                "Please check:\n"
                "• Recipient address is correct\n"
                "• You have sufficient balance\n"
                "• Network connection is stable"
            )
            return
        
        # Show estimate and ask for confirmation
        estimated_fee = fee_estimate.get("estimated_fee", 0)
        total_cost = fee_estimate.get("total_cost", 0)
        balance_sufficient = fee_estimate.get("balance_sufficient", True)
        current_balance = fee_estimate.get("current_balance", 0)
        
        estimate_text = (
            f"📤 *Send Transaction Estimate*\n\n"
            f"*To:* `{escape_markdown(recipient_address, version=2)}`\n"
            f"*Chain:* {escape_markdown(chain, version=2)}\n"
            f"*Amount:* {escape_markdown(str(amount), version=2)} {escape_markdown(token_symbol, version=2)}\n"
            f"*Estimated Fee:* {escape_markdown(f'{estimated_fee:.6f}', version=2)} ETH\n"
            f"*Total Cost:* {escape_markdown(f'{total_cost:.6f}', version=2)} ETH"
        )
        
        # Add balance information
        if current_balance is not None:
            balance_status = "✅" if balance_sufficient else "❌"
            estimate_text += f"\n*Wallet Balance:* {escape_markdown(f'{current_balance:.4f}', version=2)} ETH {balance_status}"
            
            if not balance_sufficient:
                estimate_text += f"\n\n⚠️ *Insufficient Balance!*\n"
                estimate_text += f"You need {escape_markdown(f'{total_cost:.4f}', version=2)} ETH but have {escape_markdown(f'{current_balance:.4f}', version=2)} ETH"
        
        estimate_text += f"\n\n⚠️ *Warning:* This will execute a REAL transaction on the blockchain\\!\n"
        estimate_text += f"💰 *Real tokens will be sent*\n"
        estimate_text += f"⏱️ *Transaction cannot be reversed*"
        
        # Create confirmation buttons
        if current_balance is not None and not balance_sufficient:
            # Disable confirm button if insufficient balance
            keyboard = [
                [
                    InlineKeyboardButton("❌ Insufficient Balance", callback_data="insufficient_balance_send"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_send")
                ]
            ]
        else:
            keyboard = [
                [
                    InlineKeyboardButton("✅ Confirm Send", callback_data=f"confirm_send_{chain}_{recipient_address}_{amount}_{token_symbol}"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_send")
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
            f"❌ Error processing send request: {str(e)}\n\n"
            "Please try again or contact support if the problem persists."
        )

async def send_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle send confirmation callbacks"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    if query.data == "cancel_send":
        await query.edit_message_text("❌ Send transaction cancelled.")
        return
    
    if query.data == "insufficient_balance_send":
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
    
    if query.data.startswith("confirm_send_"):
        # Parse callback data: confirm_send_<chain>_<address>_<amount>_<token>
        parts = query.data.split("_")
        if len(parts) < 6:
            await query.edit_message_text("❌ Invalid callback data.")
            return
        
        chain = parts[2]
        recipient_address = parts[3]
        amount = float(parts[4])
        token_symbol = parts[5]
        
        # Get user wallet
        user_id = query.from_user.id
        wallet = wallet_manager.get_user_wallet(user_id)
        if not wallet:
            await query.edit_message_text("❌ Wallet not found. Please create or import a wallet first.")
            return
        
        # Update message to show processing
        await query.edit_message_text(
            f"🔄 *Processing Send Transaction...*\n\n"
            f"*To:* `{escape_markdown(recipient_address, version=2)}`\n"
            f"*Amount:* {escape_markdown(str(amount), version=2)} {escape_markdown(token_symbol, version=2)}\n"
            f"*Chain:* {escape_markdown(chain, version=2)}\n\n"
            f"Please wait while we process your transaction...",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        try:
            # Execute the send transaction
            result = await send_token(
                chain=chain,
                recipient_address=recipient_address,
                amount=amount,
                token_symbol=token_symbol,
                private_key=wallet["private_key"]
            )
            
            if result["success"]:
                tx_hash = result.get("tx_hash", "Unknown")
                gas_used = result.get("gas_used", 0)
                fee_paid = result.get("fee_paid", 0)
                
                success_text = (
                    f"✅ *Send Transaction Successful!*\n\n"
                    f"*To:* `{escape_markdown(recipient_address, version=2)}`\n"
                    f"*Amount:* {escape_markdown(str(amount), version=2)} {escape_markdown(token_symbol, version=2)}\n"
                    f"*Chain:* {escape_markdown(chain, version=2)}\n"
                    f"*Transaction Hash:* `{escape_markdown(tx_hash, version=2)}`\n"
                    f"*Gas Used:* {escape_markdown(str(gas_used), version=2)}\n"
                    f"*Fee Paid:* {escape_markdown(f'{fee_paid:.6f}', version=2)} ETH\n\n"
                    f"🎉 Your transaction has been sent successfully!"
                )
                
                await query.edit_message_text(
                    success_text,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            else:
                error_msg = result.get("error", "Unknown error")
                
                # Provide specific guidance based on error type
                if "Insufficient balance" in error_msg:
                    guidance = (
                        f"💰 *Balance Issue*\n\n"
                        f"*Error:* {escape_markdown(error_msg, version=2)}\n\n"
                        f"🔧 *Solutions:*\n"
                        f"• Add more ETH to your wallet\n"
                        f"• Use `/balance` to check your current balance\n"
                        f"• Reduce the send amount\n"
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
                elif "Failed to build transaction" in error_msg:
                    guidance = (
                        f"🔄 *Transaction Issue*\n\n"
                        f"*Error:* {escape_markdown(error_msg, version=2)}\n\n"
                        f"🔧 *Solutions:*\n"
                        f"• Verify the recipient address is correct\n"
                        f"• Check if the token contract is valid\n"
                        f"• Try a different amount"
                    )
                else:
                    guidance = (
                        f"❌ *Send Transaction Failed*\n\n"
                        f"*Error:* {escape_markdown(error_msg, version=2)}\n\n"
                        f"Please try again or contact support if the problem persists\\."
                    )
                
                await query.edit_message_text(
                    guidance,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                
        except Exception as e:
            await query.edit_message_text(
                f"❌ *Unexpected Error*\n\n"
                f"*Error:* {escape_markdown(str(e), version=2)}\n\n"
                f"Please try again or contact support if the problem persists\\.",
                parse_mode=ParseMode.MARKDOWN_V2
            ) 