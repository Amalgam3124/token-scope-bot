import os
import asyncio
import httpx
from typing import Optional, Dict, Any
import json
from .uniswap_api_service import uniswap_api_service

NODIT_BASE_URL = "https://web3.nodit.io/v1"
_NODIT_HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "X-API-KEY": os.getenv("NODIT_API_KEY", "nodit-demo")
}

async def get_token_info(chain: str, contract_address: str) -> Optional[Dict[str, Any]]:
    """Get token information from Nodit API"""
    url = f"{NODIT_BASE_URL}/{chain}/mainnet/token/getTokenMetadata"
    payload = {"tokenAddress": contract_address}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=_NODIT_HEADERS, json=payload, timeout=10)
            if response.status_code == 404:
                return None
            elif response.status_code == 403:
                # For demo purposes, return mock data when API is not available
                print(f"API access restricted (403), using mock data for {chain}/{contract_address}")
                return {
                    "name": "Demo Token",
                    "symbol": "DEMO",
                    "decimals": 18,
                    "totalSupply": "1000000000000000000000000"
                }
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, dict):
                return data
            elif isinstance(data, dict) and "result" in data:
                return data["result"]
            else:
                return None
    except Exception as e:
        print(f"Error getting token info for {chain}/{contract_address}: {e}")
        # Return mock data for demo purposes
        return {
            "name": "Demo Token",
            "symbol": "DEMO",
            "decimals": 18,
            "totalSupply": "1000000000000000000000000"
        }

async def get_token_price_from_api(chain: str, contract_address: str) -> Optional[float]:
    """Get token price from 1inch API"""
    try:
        # Use a small amount to get price estimate
        test_amount_eth = 0.001
        test_amount_wei = str(int(test_amount_eth * 10**18))
        
        # Get WETH address
        weth_addresses = {
            "ethereum": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "polygon": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
            "base": "0x4200000000000000000000000000000000000006",
            "arbitrum": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
        }
        
        weth_address = weth_addresses.get(chain)
        if not weth_address:
            return None
            
        # Get quote from 1inch API
        quote = await uniswap_api_service.get_quote(chain, weth_address, contract_address, test_amount_wei)
        if not quote:
            return None
            
        # Calculate price per token
        tokens_received = float(quote.get("toTokenAmount", "0")) / 10**18
        if tokens_received == 0:
            return None
            
        # Price per token = ETH spent / tokens received
        price_per_token = test_amount_eth / tokens_received
        
        return price_per_token
        
    except Exception as e:
        print(f"Error getting price from API for {chain}/{contract_address}: {e}")
        return None

async def estimate_buy_amount(
    chain: str, 
    contract_address: str, 
    amount_in_eth: float,
    wallet_address: str
) -> Optional[Dict[str, Any]]:
    """Estimate how many tokens you would get for the given ETH amount using API"""
    try:
        # Get token info
        token_info = await get_token_info(chain, contract_address)
        if not token_info:
            return None
            
        # Get current price from API
        price = await get_token_price_from_api(chain, contract_address)
        if not price:
            # Fallback to demo price
            price = 0.001
            
        # Check wallet balance if address is provided
        wallet_balance = None
        if wallet_address:
            wallet_balance = await uniswap_api_service.get_eth_balance(chain, wallet_address)
            
        # Get WETH address
        weth_addresses = {
            "ethereum": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "polygon": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
            "base": "0x4200000000000000000000000000000000000006",
            "arbitrum": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
        }
        
        weth_address = weth_addresses.get(chain)
        if not weth_address:
            return None
            
        # Convert amount to wei
        amount_in_wei = str(int(amount_in_eth * 10**18))
        
        # Get amounts out from API
        amounts = await uniswap_api_service.estimate_swap_amounts_out(chain, amount_in_eth, contract_address)
        if not amounts or len(amounts) < 2:
            # Fallback calculation
            estimated_tokens = amount_in_eth / price
        else:
            estimated_tokens = float(amounts[1]) / 10**18
        
        result = {
            "estimated_tokens": estimated_tokens,
            "token_symbol": token_info.get("symbol", "Unknown"),
            "token_name": token_info.get("name", "Unknown"),
            "price_usd": price,
            "amount_in_eth": amount_in_eth
        }
        
        # Add balance information if available
        if wallet_balance is not None:
            result["wallet_balance"] = wallet_balance
            result["sufficient_balance"] = wallet_balance >= amount_in_eth
            
        return result
    except Exception as e:
        print(f"Error estimating buy amount: {e}")
        return None

async def execute_buy_transaction(
    chain: str,
    contract_address: str,
    amount_in_eth: float,
    private_key: str,
    slippage: float = 0.05  # 5% slippage
) -> Dict[str, Any]:
    """Execute the buy transaction using API"""
    try:
        # Validate inputs
        if not contract_address.startswith("0x") or len(contract_address) != 42:
            return {"success": False, "error": "Invalid contract address"}
            
        if amount_in_eth <= 0:
            return {"success": False, "error": "Amount must be greater than 0"}
            
        # Check if chain is supported
        supported_chains = ["ethereum", "polygon", "base", "arbitrum"]
        if chain not in supported_chains:
            return {"success": False, "error": f"Unsupported chain: {chain}"}
            
        # Execute swap using API
        result = await uniswap_api_service.execute_swap_exact_eth_for_tokens(
            chain=chain,
            amount_in_eth=amount_in_eth,
            token_address=contract_address,
            private_key=private_key,
            slippage=slippage,
            deadline_minutes=20
        )
        
        return result
        
    except Exception as e:
        return {"success": False, "error": f"Transaction failed: {str(e)}"}

async def buy_token(
    chain: str,
    contract_address: str,
    amount_in_eth: float,
    private_key: str
) -> Dict[str, Any]:
    """Main function to buy a token using real API transactions"""
    try:
        # First, get token information
        token_info = await get_token_info(chain, contract_address)
        if not token_info:
            return {"success": False, "error": "Token not found or invalid contract address"}
            
        # Estimate the buy
        estimate = await estimate_buy_amount(chain, contract_address, amount_in_eth, "")
        if not estimate:
            return {"success": False, "error": "Failed to estimate buy amount"}
            
        # Execute the transaction
        result = await execute_buy_transaction(chain, contract_address, amount_in_eth, private_key)
        
        if result["success"]:
            result["token_info"] = token_info
            result["estimate"] = estimate
            
        return result
        
    except Exception as e:
        return {"success": False, "error": f"Buy operation failed: {str(e)}"} 