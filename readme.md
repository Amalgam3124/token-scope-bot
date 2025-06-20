# TokenScope 🧠📊

**TokenScope** is a Telegram bot that delivers real-time, cross-chain token analytics.\
It combines on-chain data from [Nodit Web3 API](https://developer.nodit.io) with market-trend data (via Dexscreener) and optional AI summaries (via OpenRouter).

---

## ✨ Features

- **/daily**\
  • Top 5 trending tokens on supported chain
- **/check **``** **``\
  Detailed on-chain metrics: created time, txns, holders count and etc.
- **/summary **``** **``\
  AI-powered natural-language summary of a token’s on-chain profile and recent trends
- **Cross-chain support**\
  Ethereum · Base · Polygon

---

## 🚀 Commands

| Command                            | Description                                              |
| ---------------------------------- | -------------------------------------------------------- |
| `/start`                           | Welcome message + list of available commands             |
| `/daily`                           | Show top 5 trending tokens on supported chain            |
| `/check <chain> <token_address>`   | Fetch token metrics for `<token_address>` on `<chain>`   |
| `/summary <chain> <token_address>` | Generate an AI summary of `<token_address>` on `<chain>` |

---

## 🛠️ Setup & Installation

### 1. Prerequisites

- Python 3.10+
- A Telegram Bot token (from BotFather)
- Nodit Web3 API key
- *(Optional)* OpenRouter API key for AI summaries

### 2. Clone & Enter

```bash
git clone https://github.com/Amalgam3124/token-scope-bot.git
cd token-scope-bot
```

### 3. Virtual Environment & Dependencies

```bash
python -m venv venv
.\venv\Scripts\activate       # Windows
# or
source venv/bin/activate      # macOS/Linux

pip install -r requirements.txt
```

### 4. Environment Variables

Create a `.env` in project root:

```ini
# Telegram
BOT_TOKEN=your_telegram_bot_token

# Nodit Web3 API
NODIT_API_KEY=your_nodit_api_key

# AI Summaries
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_API_BASE=https://openrouter.ai/api/v1

```

### 5. Run the Bot

```bash
python bot.py
```

---

## 🔗 Supported Chains

| Chain    | Identifier |
| -------- | ---------- |
| Ethereum | `ethereum` |
| Base     | `base`     |
| Optimism | `optimism` |

---

## 🏗️ Architecture Overview

```
bot.py
handlers/
  ├─ daily.py        # /daily logic
  ├─ check.py        # /check logic
  ├─ analysis.py     # /analysis logic
  └─ summary.py      # /summary logic
services/
  ├─ nodit_api.py    # Nodit on-chain API
  ├─ ai_service.py   # AI summary
  └─ trending.py     # Get trend data
utils/
  ├─ chains.py       # SUPPORTED_CHAINS list
  └─ formatter.py    # number & percent formatting
.env.example
requirements.txt
README.md
```

---

## ⚠️ Notes

- Dexscreener trending may occasionally be rate-limited 
- AI summaries require a valid OpenRouter key; otherwise summary commands will be skipped
- On-chain data depends on your Nodit API quota
- Always keep `.env` out of version control (`.gitignore` includes it)

---

## 📜 License

MIT
