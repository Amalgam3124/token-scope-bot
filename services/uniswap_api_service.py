import os
import asyncio
import httpx
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

# 1inch API for real swaps
ONEINCH_API_BASE = "https://api.1inch.dev/swap/v6.0"

# Uniswap V2 Router addresses
UNISWAP_ROUTERS = {
    "ethereum": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "polygon": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
    "base": "0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24",  # BaseSwap
    "arbitrum": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",  # SushiSwap
}

# WETH addresses for different chains
WETH_ADDRESSES = {
    "ethereum": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "polygon": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
    "base": "0x4200000000000000000000000000000000000006",
    "arbitrum": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
}

# Chain IDs for 1inch API
CHAIN_IDS = {
    "ethereum": 1,
    "polygon": 137,
    "base": 8453,
    "arbitrum": 42161
}

# RPC endpoints for balance checking
RPC_ENDPOINTS = {
    "ethereum": "https://eth-mainnet.g.alchemy.com/v2/" + os.getenv("ALCHEMY_API_KEY", ""),
    "polygon": "https://polygon-mainnet.g.alchemy.com/v2/" + os.getenv("ALCHEMY_API_KEY", ""),
    "base": "https://base-mainnet.g.alchemy.com/v2/" + os.getenv("ALCHEMY_API_KEY", ""),
    "arbitrum": "https://arb-mainnet.g.alchemy.com/v2/" + os.getenv("ALCHEMY_API_KEY", ""),
}

class UniswapAPIService:
    def __init__(self):
        self.api_key = os.getenv("ONEINCH_API_KEY", "")
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    async def get_eth_balance(self, chain: str, address: str) -> Optional[float]:
        """Get ETH balance for an address using RPC"""
        rpc_url = RPC_ENDPOINTS.get(chain)
        if not rpc_url:
            return None
            
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [address, "latest"],
            "id": 1
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(rpc_url, json=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if "result" in data:
                        # Convert hex balance to ETH
                        balance_wei = int(data["result"], 16)
                        balance_eth = balance_wei / 10**18
                        return balance_eth
                return None
        except Exception as e:
            print(f"Error getting balance for {address} on {chain}: {e}")
            return None
        
    async def get_quote(
        self, 
        chain: str, 
        from_token: str, 
        to_token: str, 
        amount: str
    ) -> Optional[Dict[str, Any]]:
        """Get swap quote from 1inch API"""
        if not self.api_key:
            return None
            
        chain_id = CHAIN_IDS.get(chain)
        if not chain_id:
            return None
            
        url = f"{ONEINCH_API_BASE}/{chain_id}/quote"
        params = {
            "src": from_token,
            "dst": to_token,
            "amount": amount,
            "includeTokensInfo": "true",
            "includeProtocols": "true",
            "includeGas": "true"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params, timeout=10)
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"1inch API error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"Error getting quote from 1inch: {e}")
            return None
    
    async def build_swap_tx(
        self,
        chain: str,
        from_token: str,
        to_token: str,
        amount: str,
        from_address: str,
        slippage: float = 0.05
    ) -> Optional[Dict[str, Any]]:
        """Build swap transaction using 1inch API"""
        if not self.api_key:
            return None
            
        chain_id = CHAIN_IDS.get(chain)
        if not chain_id:
            return None
            
        url = f"{ONEINCH_API_BASE}/{chain_id}/swap"
        params = {
            "src": from_token,
            "dst": to_token,
            "amount": amount,
            "from": from_address,
            "slippage": int(slippage * 100),  # Convert to percentage
            "includeTokensInfo": "true",
            "includeProtocols": "true",
            "includeGas": "true"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=params, timeout=10)
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"1inch API error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"Error building swap tx from 1inch: {e}")
            return None
    
    async def estimate_swap_amounts_out(
        self, 
        chain: str, 
        amount_in_eth: float,
        token_address: str
    ) -> Optional[List[str]]:
        """Estimate output amounts for ETH to token swap"""
        try:
            # Convert ETH amount to wei (18 decimals)
            amount_in_wei = str(int(amount_in_eth * 10**18))
            
            # Get WETH address
            weth_address = WETH_ADDRESSES.get(chain)
            if not weth_address:
                return None
                
            # Get quote
            quote = await self.get_quote(chain, weth_address, token_address, amount_in_wei)
            if not quote:
                return None
                
            # Return amounts: [input_amount, output_amount]
            return [amount_in_wei, quote.get("toTokenAmount", "0")]
            
        except Exception as e:
            print(f"Error estimating swap amounts: {e}")
            return None
    
    async def execute_swap_exact_eth_for_tokens(
        self,
        chain: str,
        amount_in_eth: float,
        token_address: str,
        private_key: str,
        slippage: float = 0.05,
        deadline_minutes: int = 20
    ) -> Dict[str, Any]:
        """Execute swap from ETH to tokens using 1inch API"""
        try:
            # Convert ETH amount to wei
            amount_in_wei = str(int(amount_in_eth * 10**18))
            
            # Get WETH address
            weth_address = WETH_ADDRESSES.get(chain)
            if not weth_address:
                return {"success": False, "error": f"WETH address not found for {chain}"}
            
            # Get account from private key
            from eth_account import Account
            account = Account.from_key(private_key)
            from_address = account.address
            
            # Check ETH balance
            balance = await self.get_eth_balance(chain, from_address)
            if balance is None:
                return {"success": False, "error": "Failed to check wallet balance"}
            
            if balance < amount_in_eth:
                return {
                    "success": False, 
                    "error": f"Insufficient ETH balance. You have {balance:.4f} ETH, need {amount_in_eth} ETH"
                }
            
            # Build swap transaction
            swap_data = await self.build_swap_tx(
                chain=chain,
                from_token=weth_address,
                to_token=token_address,
                amount=amount_in_wei,
                from_address=from_address,
                slippage=slippage
            )
            
            if not swap_data:
                return {"success": False, "error": "Failed to build swap transaction"}
            
            # For demo purposes, return the transaction data
            # In production, you would sign and send the transaction
            return {
                "success": True,
                "transaction_data": swap_data.get("tx", {}),
                "amount_in_eth": amount_in_eth,
                "estimated_tokens": float(swap_data.get("toTokenAmount", "0")) / 10**18,
                "gas_estimate": swap_data.get("tx", {}).get("gas", 0),
                "protocols": swap_data.get("protocols", []),
                "message": "Transaction data generated. In production, this would be signed and sent to the blockchain."
            }
            
        except Exception as e:
            return {"success": False, "error": f"Swap failed: {str(e)}"}

# Global instance
uniswap_api_service = UniswapAPIService() 