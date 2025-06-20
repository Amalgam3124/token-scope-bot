# services/trending.py

import requests
from typing import List, Dict, Optional

_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
TOP_BOOSTS_URL = "https://api.dexscreener.com/token-boosts/top/v1"

def fetch_top_boosted_tokens() -> Optional[List[Dict]]:
    """
    Fetches a flat list of top boosted tokens from DexScreener's public API.
    """
    try:
        response = requests.get(TOP_BOOSTS_URL, headers=_DEFAULT_HEADERS, timeout=15)
        response.raise_for_status()
        
        # The API can return a list directly or a dict containing the list
        json_data = response.json()
        if isinstance(json_data, dict):
            return json_data.get("boostedTokens", [])
        elif isinstance(json_data, list):
            return json_data
        else:
            print(f"DEXSCREENER: Unexpected response format from token-boosts: got {type(json_data)}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"DEXSCREENER: Request to token-boosts failed: {e}")
        return None
    except ValueError: # JSONDecodeError
        print("DEXSCREENER: Failed to decode JSON from token-boosts response.")
        return None

def get_token_details_from_dexscreener(token_address: str, chain_id: str) -> Optional[Dict]:
    """
    Fetches detailed token information from DexScreener using the search endpoint.
    """
    try:
        # Use the search endpoint to get detailed token information
        url = f"https://api.dexscreener.com/latest/dex/search?q={token_address}"
        response = requests.get(url, headers=_DEFAULT_HEADERS, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        pairs = data.get("pairs", [])
        
        if not pairs:
            return None
            
        # Find the pair that matches our chain
        for pair in pairs:
            if pair.get("chainId") == chain_id:
                # Add the tokenAddress field to the pair data
                pair["tokenAddress"] = pair.get("baseToken", {}).get("address")
                return pair
                
        # If no exact match, return the first pair with tokenAddress added
        if pairs:
            pairs[0]["tokenAddress"] = pairs[0].get("baseToken", {}).get("address")
            return pairs[0]
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"DEXSCREENER: Request failed for {token_address}: {e}")
        return None
    except (ValueError, KeyError):
        print(f"DEXSCREENER: Failed to parse response for {token_address}")
        return None 