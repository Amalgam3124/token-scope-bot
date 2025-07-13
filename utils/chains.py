# utils/chains.py

SUPPORTED_CHAINS = {
    "ethereum": {},
    "polygon": {},
    "base": {},
    "arbitrum": {},
}

CHAIN_ALIASES = {
    "eth": "ethereum",
    "pol": "polygon",
    "matic": "polygon",
    "arb": "arbitrum",
}


CHAIN_MAP = {
    "ethereum": "ethereum",
    "polygon": "polygon",
    "base": "base",
    "arbitrum": "arbitrum",
}

def resolve_chain_alias(chain_input: str) -> str | None:
    chain_lower = chain_input.lower()
    if chain_lower in SUPPORTED_CHAINS:
        return chain_lower
    return CHAIN_ALIASES.get(chain_lower)