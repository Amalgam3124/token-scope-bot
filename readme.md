# TokenScope 🧠📊

**TokenScope** is a Telegram bot that delivers real-time, cross-chain token analytics.\
It combines on-chain data from [Nodit Web3 API](https://developer.nodit.io) with market-trend data (via Dexscreener) and optional AI summaries (via OpenRouter).

---

## ✨ Features

### 🔍 Token Analytics
- **/daily** - Get top 5 trending tokens across supported chains
- **/check <chain> <token_address>** - Detailed on-chain metrics (creation time, transactions, holders count, etc.)
- **/summary <chain> <token_address>** - AI-powered natural-language summary of token's on-chain profile and recent trends

### 💼 Wallet Management
- **/create** - Create a new secure wallet for the user
- **/import <private_key>** - Import existing wallet with private key
- **/delete** - Delete your wallet securely
- **/balance [chain] [token_address]** - Check wallet balance on specified chain

### 🌐 Cross-chain Support
Ethereum · Base · Polygon · Arbitrum · Optimism

---

## 🏦 Wallet Security & Encryption

- All wallet private keys are encrypted using **Fernet symmetric encryption** before being stored in the database
- **Encryption key management:**
  - By default, the key is generated and saved to `wallet_key.key` in the project root
  - **Recommended:** Set the encryption key as an environment variable `WALLET_ENCRYPTION_KEY` for better security
- **⚠️ Important:** If you lose the encryption key, you will not be able to decrypt any previously stored wallets!
- To generate a new key, run:
  ```bash
  python generate_key.py
  ```

---

## 🚀 Commands

| Command                            | Description                                              | Example                                    |
| ---------------------------------- | -------------------------------------------------------- | ------------------------------------------ |
| `/start`                           | Welcome message + list of available commands             | `/start`                                   |
| `/daily`                           | Show top 5 trending tokens on supported chain            | `/daily`                                   |
| `/check <chain> <token_address>`   | Fetch token metrics for `<token_address>` on `<chain>`   | `/check ethereum 0x1234...`                |
| `/summary <chain> <token_address>` | Generate an AI summary of `<token_address>` on `<chain>` | `/summary base 0x5678...`                  |
| `/create`                          | Create a new wallet                                     | `/create`                                  |
| `/import <private_key>`            | Import an existing wallet                                | `/import 0xabcd...`                        |
| `/delete`                          | Delete your wallet                                      | `/delete`                                  |
| `/balance [chain] [token_address]` | Check wallet balance                                     | `/balance ethereum` or `/balance ethereum 0x1234...` |

---

## 🛠️ Setup & Installation

### 1. Prerequisites

- **Python 3.10+**
- **Telegram Bot token** (from [@BotFather](https://t.me/botfather))
- **Nodit Web3 API key** (from [Nodit Developer Portal](https://developer.nodit.io))
- ***(Optional)* OpenRouter API key** for AI summaries (from [OpenRouter](https://openrouter.ai))

### 2. Clone & Enter

```bash
git clone https://github.com/Amalgam3124/token-scope-bot.git
cd token-scope-bot
```

### 3. Virtual Environment & Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate       # Windows
# or
source venv/bin/activate      # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 4. Environment Variables

Create a `.env` file in the project root:

```ini
# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token

# Nodit Web3 API Configuration
NODIT_API_KEY=your_nodit_api_key

# AI Summaries Configuration (Optional)
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_API_BASE=https://openrouter.ai/api/v1

# Wallet Encryption (Optional - will auto-generate if not set)
# Generate with: python generate_key.py
WALLET_ENCRYPTION_KEY=your_base64_fernet_key
```

> **🔒 Security Notes:**
> - If `WALLET_ENCRYPTION_KEY` is not set, a new key will be generated and saved to `wallet_key.key`
> - For best security, set `WALLET_ENCRYPTION_KEY` as an environment variable (do not commit it to version control)
> - Losing this key means you cannot decrypt any previously stored wallets!
> - Always keep your `.env` file secure and never commit it to version control

### 5. Generate Encryption Key (Optional)

If you haven't set the `WALLET_ENCRYPTION_KEY` environment variable:

```bash
python generate_key.py
```

This will generate a new encryption key and provide instructions on how to use it.

### 6. Run the Bot

```bash
python bot.py
```

The bot will start and display "Bot is running. Press Ctrl-C to stop."

---

## 🔗 Supported Chains

| Chain    | Identifier |
| -------- | ---------- |
| Ethereum | `ethereum` |
| Base     | `base`     |
| Optimism | `optimism` |
| Arbitrum | `arbitrum` |
| Polygon  | `polygon`  |

---

## 📊 Usage Examples

### Getting Trending Tokens
```
/daily
```
Returns the top 5 trending tokens with their basic information and market data.

### Checking Token Metrics
```
/check ethereum 0xA0b86a33E6441b8c4C8C8C8C8C8C8C8C8C8C8C8C
```
Provides detailed on-chain metrics including:
- Token creation time
- Total transactions
- Holder count
- Market cap
- Price information

### AI-Powered Token Summary
```
/summary base 0x1234567890123456789012345678901234567890
```
Generates a natural language summary of the token's performance and trends.

### Wallet Management
```
/create                    # Create new wallet
/import 0xabcd...         # Import existing wallet
/balance ethereum         # Check ETH balance
/balance base 0x1234...   # Check specific token balance
/delete                   # Delete wallet
```

---

## 🏗️ Architecture Overview

```
TokenScope/
├── bot.py                 # Main bot entry point
├── generate_key.py        # Encryption key generator
├── requirements.txt       # Python dependencies
├── .env_example          # Environment variables template
├── wallets.db            # Encrypted wallet storage
├── handlers/             # Command handlers
│   ├── daily.py          # /daily command logic
│   ├── check.py          # /check command logic
│   ├── summary.py        # /summary command logic
│   ├── analysis.py       # /analysis command logic
│   └── wallet.py         # Wallet management commands
├── services/             # External service integrations
│   ├── nodit_api.py      # Nodit Web3 API client
│   ├── ai_service.py     # OpenRouter AI service
│   ├── balance_service.py # Balance checking service
│   └── trending.py       # Dexscreener trending data
└── utils/                # Utility functions
    ├── chains.py         # Supported chains configuration
    ├── formatter.py      # Number and text formatting
    └── wallet.py         # Wallet encryption/decryption
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Yes | Telegram bot token from @BotFather |
| `NODIT_API_KEY` | Yes | Nodit Web3 API key |
| `OPENROUTER_API_KEY` | No | OpenRouter API key for AI summaries |
| `OPENROUTER_API_BASE` | No | OpenRouter API base URL (default: https://openrouter.ai/api/v1) |
| `WALLET_ENCRYPTION_KEY` | No | Fernet encryption key for wallet security |

### API Rate Limits

- **Nodit API**: Depends on your plan and quota
- **Dexscreener**: May be rate-limited occasionally
- **OpenRouter**: Depends on your plan

---

## 🚨 Troubleshooting

### Common Issues

**1. Bot not responding**
- Check if `BOT_TOKEN` is correctly set in `.env`
- Verify the bot is running with `python bot.py`
- Check bot permissions in Telegram

**2. API errors**
- Verify your API keys are correct
- Check your API quota/rate limits
- Ensure network connectivity

**3. Wallet encryption errors**
- Regenerate encryption key: `python generate_key.py`
- Update `WALLET_ENCRYPTION_KEY` in `.env`
- Restart the bot

**4. Import errors**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (requires 3.10+)
- Verify virtual environment is activated

### Logs

The bot provides detailed logging. Check the console output for error messages and debugging information.

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/token-scope-bot.git
cd token-scope-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env_example .env
# Edit .env with your API keys

# Run the bot
python bot.py
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
