# services/ai_service.py

import os
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
from utils.formatter import format_number

load_dotenv()

# Switch to OpenRouter credentials and configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

def get_ai_analysis(token_data: Dict[str, Any]) -> str:
    if not OPENROUTER_API_KEY:
        return "Error: OPENROUTER_API_KEY is not configured. Please set it in your environment."

    client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=OPENROUTER_API_KEY,
    )

    prompt_lines = [
        "You are a professional crypto trader providing a quick analysis of a token.",
        "Based on the on-chain data below, provide a short, actionable analysis. Focus on:",
        "- Potential buy/sell signals.",
        "- Bullish or bearish indicators (e.g., holder count, transaction volume).",
        "- Any potential red flags (e.g., recent creation date, low holder count).",
        "- A brief outlook on the token's potential short-term momentum.",
        "Your analysis must be concise (under 150 words) and directly related to the provided data.",
        "\n--- On-Chain Data ---",
        f"Token Name: {token_data.get('name', 'N/A')}",
        f"Contract Address: {token_data.get('address', 'N/A')}",
        f"Creation Date: {token_data.get('created', 'N/A')}",
        f"Token Standard: {token_data.get('type', 'N/A')}",
        f"Total Supply: {token_data.get('totalSupply', 'N/A')}",
        f"Total Holders: {token_data.get('holders', 'N/A')}",
        f"Total Transactions (in last 30d): {token_data.get('transactions', 'N/A')}",
        "------------------\n",
        "Trader's Take:",
    ]
    prompt = "\n".join(prompt_lines)

    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3-0324:free",
            messages=[
                {"role": "system", "content": "You are a crypto trading analyst bot."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=250,
        )
        analysis = response.choices[0].message.content
        return analysis.strip() if analysis else "AI analysis failed to generate content."
    except Exception as e:
        print(f"OpenRouter API Error: {e}")
        return f"An error occurred with the AI analysis service: {e}" 