import os
import asyncio
import httpx
import json
from typing import Optional, Dict, Any
from eth_account import Account
from .uniswap_api_service import uniswap_api_service

# Token contract addresses for different chains
TOKEN_ADDRESSES = {
    "ethereum": {
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "USDC": "0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C8C8"
    },
    "polygon": {
        "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    },
    "base": {
        "USDT": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    },
    "arbitrum": {
        "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
        "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
    }
}

# ERC20 ABI for transfer function
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

async def get_token_balance(chain: str, token_symbol: str, wallet_address: str) -> Optional[float]:
    """Get token balance for a wallet"""
    try:
        if token_symbol == "ETH":
            # For ETH, use the existing balance check
            balance = await uniswap_api_service.get_eth_balance(chain, wallet_address)
            return balance
        else:
            # For ERC20 tokens, we need to call the contract
            token_address = TOKEN_ADDRESSES.get(chain, {}).get(token_symbol)
            if not token_address:
                return None
            
            # This would require web3.py for full implementation
            # For now, return a mock balance
            return 1000.0  # Mock balance
            
    except Exception as e:
        print(f"Error getting {token_symbol} balance: {e}")
        return None

async def estimate_send_fee(
    chain: str,
    recipient_address: str,
    amount: float,
    token_symbol: str,
    wallet_address: str
) -> Optional[Dict[str, Any]]:
    """Estimate the fee for sending tokens"""
    try:
        # Get current wallet balance
        current_balance = await get_token_balance(chain, token_symbol, wallet_address)
        
        # Estimate gas fee (this would be more accurate with web3.py)
        if token_symbol == "ETH":
            estimated_fee = 0.001  # Mock gas estimate for ETH transfer
        else:
            estimated_fee = 0.005  # Mock gas estimate for ERC20 transfer
        
        # Calculate total cost
        if token_symbol == "ETH":
            total_cost = amount + estimated_fee
        else:
            # For ERC20 tokens, we need ETH for gas fees
            total_cost = estimated_fee
        
        # Check if balance is sufficient
        balance_sufficient = current_balance is not None and current_balance >= total_cost
        
        return {
            "estimated_fee": estimated_fee,
            "total_cost": total_cost,
            "current_balance": current_balance,
            "balance_sufficient": balance_sufficient,
            "token_symbol": token_symbol,
            "amount": amount
        }
        
    except Exception as e:
        print(f"Error estimating send fee: {e}")
        return None

async def send_eth_transaction(
    chain: str,
    recipient_address: str,
    amount: float,
    private_key: str
) -> Dict[str, Any]:
    """Send ETH transaction"""
    try:
        # Get account from private key
        account = Account.from_key(private_key)
        from_address = account.address
        
        # Check balance
        balance = await uniswap_api_service.get_eth_balance(chain, from_address)
        if balance is None:
            return {"success": False, "error": "Failed to check wallet balance"}
        
        if balance < amount:
            return {
                "success": False, 
                "error": f"Insufficient ETH balance. You have {balance:.4f} ETH, need {amount} ETH"
            }
        
        # For demo purposes, return mock transaction data
        # In production, you would build and send the actual transaction
        return {
            "success": True,
            "tx_hash": f"0x{'a' * 64}",  # Mock transaction hash
            "gas_used": 21000,  # Standard ETH transfer gas
            "fee_paid": 0.001,  # Mock fee
            "message": "Transaction data generated. In production, this would be signed and sent to the blockchain."
        }
        
    except Exception as e:
        return {"success": False, "error": f"ETH transaction failed: {str(e)}"}

async def send_erc20_transaction(
    chain: str,
    recipient_address: str,
    amount: float,
    token_symbol: str,
    private_key: str
) -> Dict[str, Any]:
    """Send ERC20 token transaction"""
    try:
        # Get token address
        token_address = TOKEN_ADDRESSES.get(chain, {}).get(token_symbol)
        if not token_address:
            return {"success": False, "error": f"Token {token_symbol} not supported on {chain}"}
        
        # Get account from private key
        account = Account.from_key(private_key)
        from_address = account.address
        
        # Check ETH balance for gas fees
        eth_balance = await uniswap_api_service.get_eth_balance(chain, from_address)
        if eth_balance is None:
            return {"success": False, "error": "Failed to check ETH balance for gas fees"}
        
        estimated_gas_fee = 0.005  # Mock gas estimate
        if eth_balance < estimated_gas_fee:
            return {
                "success": False, 
                "error": f"Insufficient ETH for gas fees. You have {eth_balance:.4f} ETH, need {estimated_gas_fee} ETH"
            }
        
        # For demo purposes, return mock transaction data
        # In production, you would build and send the actual ERC20 transfer
        return {
            "success": True,
            "tx_hash": f"0x{'b' * 64}",  # Mock transaction hash
            "gas_used": 65000,  # Mock gas for ERC20 transfer
            "fee_paid": estimated_gas_fee,
            "message": "Transaction data generated. In production, this would be signed and sent to the blockchain."
        }
        
    except Exception as e:
        return {"success": False, "error": f"ERC20 transaction failed: {str(e)}"}

async def send_token(
    chain: str,
    recipient_address: str,
    amount: float,
    token_symbol: str,
    private_key: str
) -> Dict[str, Any]:
    """Main function to send tokens"""
    try:
        # Validate inputs
        if not recipient_address.startswith("0x") or len(recipient_address) != 42:
            return {"success": False, "error": "Invalid recipient address"}
            
        if amount <= 0:
            return {"success": False, "error": "Amount must be greater than 0"}
            
        supported_chains = ["ethereum", "polygon", "base", "arbitrum"]
        if chain not in supported_chains:
            return {"success": False, "error": f"Unsupported chain: {chain}"}
            
        supported_tokens = ["ETH", "USDT", "USDC"]
        if token_symbol not in supported_tokens:
            return {"success": False, "error": f"Unsupported token: {token_symbol}"}
        
        # Send based on token type
        if token_symbol == "ETH":
            result = await send_eth_transaction(chain, recipient_address, amount, private_key)
        else:
            result = await send_erc20_transaction(chain, recipient_address, amount, token_symbol, private_key)
        
        return result
        
    except Exception as e:
        return {"success": False, "error": f"Send operation failed: {str(e)}"} 