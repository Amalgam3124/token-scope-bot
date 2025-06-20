# utils/formatter.py
from typing import Any, Dict
from datetime import datetime

def escape_markdown_v2(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

def format_number(value: Any) -> str:
    if value is None:
        return "N/A"
    try:
        num = float(value)
        if abs(num) >= 1_000_000_000:
            result = f"{num/1_000_000_000:.2f}B"
        elif abs(num) >= 1_000_000:
            result = f"{num/1_000_000:.2f}M"
        elif abs(num) >= 1_000:
            result = f"{num/1_000:.2f}K"
        elif abs(num) < 0.0001 and num != 0:
            result = f"{num:.8f}".rstrip('0')
        else:
            result = f"{num:,.2f}"
        return escape_markdown_v2(result)
    except (ValueError, TypeError):
        return "N/A"

def format_percent(value: Any) -> str:
    if value is None:
        return "N/A"
    try:
        val = float(value)
        sign = '+' if val > 0 else ''
        result = f"{sign}{val:.2f}%"
        return escape_markdown_v2(result)
    except (ValueError, TypeError):
        return "N/A"

def format_datetime_string(dt_string: str | None) -> str:
    if not dt_string:
        return "N/A"
    try:
        dt_object = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return dt_object.strftime('%Y-%m-%d %H:%M')
    except (ValueError, TypeError):
        return dt_string

def format_token_check_message(data: Dict[str, Any]) -> str:
    name = escape_markdown_v2(data.get('name', 'N/A'))
    chain_name = escape_markdown_v2(data.get('chain_name', ''))
    header_text = f"{name} on {chain_name}"
    if 'rank' in data:
        rank = escape_markdown_v2(f"{data['rank']}.")
        header_text = f"*{rank} {header_text}*"
    else:
        header_text = f"*{header_text}*"

    lines = [
        header_text,
        f"*Contract Address*: `{data.get('address', 'N/A')}`",
        f"*Created*: {escape_markdown_v2(data.get('created', 'N/A'))}",
        f"*Type*: {escape_markdown_v2(data.get('type', 'N/A'))}",
        f"*Total Supply*: {escape_markdown_v2(data.get('totalSupply', 'N/A'))}",
        f"*Total Holders*: {escape_markdown_v2(str(data.get('holders', 'N/A')))}",
        f"*Total Transactions \\(30d\\)*: {escape_markdown_v2(str(data.get('transactions', 'N/A')))}",
    ]
    
    return "\n".join(lines)