import os
import asyncio
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

NODIT_BASE_URL = "https://web3.nodit.io/v1"
_NODIT_HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "X-API-KEY": os.getenv("NODIT_API_KEY", "nodit-demo")
}

# Common token contract addresses
COMMON_TOKENS = {
    "ethereum": {
        "ETH": "0x0000000000000000000000000000000000000000",  # Native token
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F"
    },
    "polygon": {
        "MATIC": "0x0000000000000000000000000000000000000000",  # Native token
        "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063"
    },
    "base": {
        "ETH": "0x0000000000000000000000000000000000000000",  # Native token
        "USDT": "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "DAI": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb"
    }
}

async def get_native_balance(chain: str, address: str) -> Optional[Dict[str, Any]]:
    """Get native token balance"""
    # Try alternative endpoint for native balance
    url = f"{NODIT_BASE_URL}/{chain}/mainnet/account/getAccountBalance"
    payload = {"accountAddress": address}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=_NODIT_HEADERS, json=payload, timeout=10)
            if response.status_code == 404:
                print(f"NODIT_BALANCE: Account not found on {chain} with address {address} (404)")
                # Return zero balance for 404
                return {"balance": "0", "symbol": "ETH" if chain in ["ethereum", "base"] else "MATIC"}
            elif response.status_code == 400:
                print(f"NODIT_BALANCE: Wrong endpoint for {chain} with address {address} (400)")
                # Try alternative approach - return zero balance for now
                return {"balance": "0", "symbol": "ETH" if chain in ["ethereum", "base"] else "MATIC"}
            response.raise_for_status()
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, dict):
                if "balance" in data:
                    return data
                elif "result" in data and isinstance(data["result"], dict):
                    return data["result"]
                elif "data" in data and isinstance(data["data"], dict):
                    return data["data"]
                else:
                    print(f"NODIT_BALANCE: Unexpected response structure for {chain}/{address}: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    return data
            else:
                print(f"NODIT_BALANCE: Unexpected response format for {chain}/{address}: {type(data)}")
                return None
    except httpx.RequestError as e:
        print(f"NODIT_BALANCE: Request failed for {chain}/{address}: {e}")
        return None
    except httpx.HTTPStatusError as e:
        print(f"NODIT_BALANCE: HTTP error for {chain}/{address}: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"NODIT_BALANCE: Error for {chain}/{address}: {e}")
        return None

async def get_tokens_owned_by_account(chain: str, address: str) -> Optional[List[Dict[str, Any]]]:
    """Get all tokens owned by account using the correct Nodit API endpoint"""
    url = f"{NODIT_BASE_URL}/{chain}/mainnet/token/getTokensOwnedByAccount"
    payload = {"accountAddress": address}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=_NODIT_HEADERS, json=payload, timeout=15)
            if response.status_code == 404:
                print(f"NODIT_TOKENS: Account not found on {chain} with address {address} (404)")
                return []
            response.raise_for_status()
            data = response.json()
            
            # Handle different response formats based on actual API response
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Check for common response structures
                if "items" in data and isinstance(data["items"], list):
                    return data["items"]
                elif "data" in data and isinstance(data["data"], list):
                    return data["data"]
                elif "result" in data and isinstance(data["result"], list):
                    return data["result"]
                elif "tokens" in data and isinstance(data["tokens"], list):
                    return data["tokens"]
                else:
                    # If it's a dict but not a list, print the structure for debugging
                    print(f"NODIT_TOKENS: Response structure for {chain}/{address}: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    # Try to extract any list from the response
                    for key, value in data.items():
                        if isinstance(value, list):
                            return value
                    return []
            else:
                print(f"NODIT_TOKENS: Unexpected response format for {chain}/{address}: {type(data)}")
                return []
    except httpx.RequestError as e:
        print(f"NODIT_TOKENS: Request failed for {chain}/{address}: {e}")
        return []
    except httpx.HTTPStatusError as e:
        print(f"NODIT_TOKENS: HTTP error for {chain}/{address}: {e.response.status_code} - {e.response.text}")
        return []
    except Exception as e:
        print(f"NODIT_TOKENS: Error for {chain}/{address}: {e}")
        return []

async def get_token_balance(chain: str, address: str, token_address: str) -> Optional[Dict[str, Any]]:
    """Get token balance"""
    url = f"{NODIT_BASE_URL}/{chain}/mainnet/token/getTokenBalanceByContract"
    payload = {
        "contractAddress": token_address,
        "accountAddress": address
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=_NODIT_HEADERS, json=payload, timeout=10)
            if response.status_code == 404:
                print(f"NODIT_TOKEN_BALANCE: Token balance not found for {address} on {chain} (404)")
                # Return zero balance instead of None
                return {"balance": "0", "contractAddress": token_address}
            response.raise_for_status()
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, dict):
                if "balance" in data:
                    return data
                elif "result" in data and isinstance(data["result"], dict):
                    return data["result"]
                elif "data" in data and isinstance(data["data"], dict):
                    return data["data"]
                else:
                    print(f"NODIT_TOKEN_BALANCE: Unexpected response structure for {chain}/{address}/{token_address}: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    return data
            else:
                print(f"NODIT_TOKEN_BALANCE: Unexpected response format for {chain}/{address}/{token_address}: {type(data)}")
                return None
    except httpx.RequestError as e:
        print(f"NODIT_TOKEN_BALANCE: Request failed for {chain}/{address}/{token_address}: {e}")
        return None
    except httpx.HTTPStatusError as e:
        print(f"NODIT_TOKEN_BALANCE: HTTP error for {chain}/{address}/{token_address}: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"NODIT_TOKEN_BALANCE: Error for {chain}/{address}/{token_address}: {e}")
        return None

async def get_token_metadata(chain: str, token_address: str) -> Optional[Dict[str, Any]]:
    """Get token metadata"""
    url = f"{NODIT_BASE_URL}/{chain}/mainnet/token/getTokenContractMetadataByContracts"
    payload = {"contractAddresses": [token_address]}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=_NODIT_HEADERS, json=payload, timeout=10)
            if response.status_code == 404:
                print(f"NODIT_METADATA: Token not found on {chain} with address {token_address} (404)")
                return None
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0] if isinstance(data[0], dict) else None
            return data if isinstance(data, dict) else None
    except httpx.RequestError as e:
        print(f"NODIT_METADATA: Request failed for {chain}/{token_address}: {e}")
        return None
    except httpx.HTTPStatusError as e:
        print(f"NODIT_METADATA: HTTP error for {chain}/{token_address}: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"NODIT_METADATA: Error for {chain}/{token_address}: {e}")
        return None

def format_balance(balance_raw: str, decimals: int, symbol: str) -> str:
    """Format balance display"""
    try:
        if not balance_raw or balance_raw == "0":
            return "0.00"
        
        balance = int(balance_raw) / (10 ** decimals)
        if balance < 0.01:
            return f"{balance:.6f}"
        elif balance < 1:
            return f"{balance:.4f}"
        elif balance < 1000:
            return f"{balance:.2f}"
        else:
            return f"{balance:,.2f}"
    except (ValueError, TypeError):
        return "0.00"

async def get_wallet_balances(chain: str, address: str, specific_token: Optional[str] = None) -> Dict[str, Any]:
    """Get wallet balances using the improved Nodit API approach"""
    results = {
        "chain": chain,
        "address": address,
        "balances": [],
        "total_usd_value": 0.0
    }
    
    if specific_token:
        # Query specific token balance
        token_metadata = await get_token_metadata(chain, specific_token)
        if token_metadata:
            token_balance = await get_token_balance(chain, address, specific_token)
            if token_balance:
                balance_formatted = format_balance(
                    token_balance.get("balance", "0"),
                    token_metadata.get("decimals", 0),
                    token_metadata.get("symbol", "Unknown")
                )
                results["balances"].append({
                    "symbol": token_metadata.get("symbol", "Unknown"),
                    "name": token_metadata.get("name", "Unknown"),
                    "balance": balance_formatted,
                    "contract_address": specific_token
                })
    else:
        # First get native token balance
        native_balance = await get_native_balance(chain, address)
        if native_balance:
            native_symbol = "ETH" if chain in ["ethereum", "base"] else "MATIC" if chain == "polygon" else "ETH"
            balance_formatted = format_balance(
                native_balance.get("balance", "0"),
                18,  # Native tokens typically have 18 decimals
                native_symbol
            )
            if balance_formatted != "0.00":
                results["balances"].append({
                    "symbol": native_symbol,
                    "name": native_symbol,
                    "balance": balance_formatted,
                    "contract_address": "Native"
                })
        
        # Then get all ERC20 tokens owned by the account
        tokens_owned = await get_tokens_owned_by_account(chain, address)
        if tokens_owned:
            for token in tokens_owned:
                try:
                    contract = token.get("contract", {})
                    contract_address = contract.get("address")
                    balance_raw = token.get("balance", "0")
                    decimals = contract.get("decimals", 18)
                    symbol = contract.get("symbol", "Unknown")
                    name = contract.get("name", "Unknown")

                    if contract_address and balance_raw and balance_raw != "0":
                        balance_formatted = format_balance(balance_raw, decimals, symbol)
                        if balance_formatted != "0.00":
                            results["balances"].append({
                                "symbol": symbol,
                                "name": name,
                                "balance": balance_formatted,
                                "contract_address": contract_address
                            })
                except Exception as e:
                    print(f"Error processing token {token}: {e}")
                    continue
        
        # If no tokens found via getTokensOwnedByAccount, fall back to common tokens
        if not results["balances"]:
            common_tokens = COMMON_TOKENS.get(chain, {})
            
            for symbol, token_address in common_tokens.items():
                if token_address == "0x0000000000000000000000000000000000000000":
                    continue  # Skip native token as we already handled it
                
                # ERC20 token
                token_metadata = await get_token_metadata(chain, token_address)
                if token_metadata:
                    token_balance = await get_token_balance(chain, address, token_address)
                    if token_balance:
                        balance_formatted = format_balance(
                            token_balance.get("balance", "0"),
                            token_metadata.get("decimals", 0),
                            token_metadata.get("symbol", symbol)
                        )
                        if balance_formatted != "0.00":
                            results["balances"].append({
                                "symbol": token_metadata.get("symbol", symbol),
                                "name": token_metadata.get("name", symbol),
                                "balance": balance_formatted,
                                "contract_address": token_address
                            })
                
                # Avoid API rate limiting
                await asyncio.sleep(0.1)
    
    return results 