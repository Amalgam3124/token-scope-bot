# services/nodit_api.py
import os
import json
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone

import requests
import httpx
from utils.formatter import format_datetime_string

NODIT_BASE_URL = "https://web3.nodit.io/v1"

_NODIT_HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "X-API-KEY": os.getenv("NODIT_API_KEY", "nodit-demo")
}


def get_price_from_dexscreener(token_address: str) -> Optional[Dict[str, Any]]:
    url = f"https://api.dexscreener.com/latest/dex/search?q={token_address}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        pairs = data.get("pairs")
        if not pairs:
            print(f"DEXSCREENER: No pairs found for {token_address}")
            return None
        return pairs[0]
    except requests.exceptions.RequestException as e:
        print(f"DEXSCREENER: Request failed for {token_address}: {e}")
        return None
    except (ValueError, json.JSONDecodeError):
        print(f"DEXSCREENER: Failed to decode JSON for {token_address}")
        return None



async def get_token_metadata_from_nodit(chain: str, token_address: str) -> Optional[Dict[str, Any]]:
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
    except json.JSONDecodeError:
        print(f"NODIT_METADATA: Failed to decode JSON for {chain}/{token_address}")
        return None


async def get_token_holders_from_nodit(chain: str, token_address: str) -> Optional[Dict[str, Any]]:
    url = f"{NODIT_BASE_URL}/{chain}/mainnet/token/getTokenHoldersByContract"
    payload = {
        "contractAddress": token_address,
        "withCount": True
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=_NODIT_HEADERS, json=payload, timeout=10)
            if response.status_code == 404:
                print(f"NODIT_HOLDERS: Holders not found for {token_address} on {chain} (404)")
                return None
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, dict) else None
    except httpx.RequestError as e:
        print(f"NODIT_HOLDERS: Request failed for {chain}/{token_address}: {e}")
        return None
    except httpx.HTTPStatusError as e:
        print(f"NODIT_HOLDERS: HTTP error for {chain}/{token_address}: {e.response.status_code} - {e.response.text}")
        return None
    except json.JSONDecodeError:
        print(f"NODIT_HOLDERS: Failed to decode JSON for {chain}/{token_address}")
        return None


async def get_token_transactions_from_nodit(chain: str, token_address: str) -> Optional[Dict[str, Any]]:
    url = f"{NODIT_BASE_URL}/{chain}/mainnet/token/getTokenTransfersByContract"
    
    to_date = datetime.now(timezone.utc)
    from_date = to_date - timedelta(days=30)
    
    payload = {
        "contractAddress": token_address,
        "fromDate": from_date.isoformat(),
        "toDate": to_date.isoformat(),
        "withCount": True,
        "withZeroValue": False
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=_NODIT_HEADERS, json=payload, timeout=20)
            if response.status_code == 404:
                print(f"NODIT_TXN: Transactions not found for {token_address} on {chain} (404)")
                return None
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, dict) else None
    except httpx.RequestError as e:
        print(f"NODIT_TXN: Request failed for {chain}/{token_address}: {e}")
        return None
    except httpx.HTTPStatusError as e:
        print(f"NODIT_TXN: HTTP error for {chain}/{token_address}: {e.response.status_code} - {e.response.text}")
        return None
    except json.JSONDecodeError:
        print(f"NODIT_TXN: Failed to decode JSON for {chain}/{token_address}")
        return None


async def get_full_token_profile_from_nodit(chain: str, token_address: str) -> Optional[Dict[str, Any]]:
    if not chain or not isinstance(chain, str):
        return None

    metadata = await get_token_metadata_from_nodit(chain, token_address)
    if not metadata:
        print(f"Failed to get metadata for {token_address}, stopping.")
        return None

    await asyncio.sleep(0.3)
    holders = await get_token_holders_from_nodit(chain, token_address)
    
    await asyncio.sleep(0.3)
    transactions = await get_token_transactions_from_nodit(chain, token_address)
    
    total_supply_raw = metadata.get("totalSupply")
    decimals = metadata.get("decimals", 0)
    total_supply_formatted = "N/A"
    if total_supply_raw and isinstance(decimals, int):
        try:
            total_supply = int(total_supply_raw) / (10 ** decimals)
            total_supply_formatted = f"{total_supply:,.2f}"
        except (ValueError, TypeError):
            pass

    profile = {
        "name": metadata.get("name"),
        "address": token_address,
        "created": format_datetime_string(metadata.get("deployedAt")),
        "type": metadata.get("type"),
        "totalSupply": total_supply_formatted,
        "holders": holders.get("count") if holders and isinstance(holders, dict) else "N/A",
        "transactions": transactions.get("count") if transactions and isinstance(transactions, dict) else "N/A",
        "source": "Nodit"
    }

    return profile