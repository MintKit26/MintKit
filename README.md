# MintKit 🛠️🪙

> A transparent, automated token launch toolkit for Solana developers.

MintKit gives developers the full infrastructure to deploy a community-first token correctly — with locked liquidity, automatic buybacks, burns, airdrops, and a public transparency log. All automated. All verifiable on-chain.

---

## The Problem

Most token launches fail because humans run them.

- Developers rug pull
- Teams abandon projects
- Insiders dump on communities
- Buybacks get promised but never happen
- Transparency logs never get published

MintKit solves this by automating the correct behavior from day one. The rules are set at launch and the bot follows them — no human intervention required after deployment.

---

## What MintKit Does

You bring the coin idea. MintKit handles everything else.

```
Developer provides:        MintKit handles:
─────────────────          ──────────────────────────────
Coin name                  SPL token deployment
Ticker symbol              Liquidity pool creation
Tokenomics config          LP locking (180 days default)
                           Mint authority revocation
                           Buyback engine
                           50% burn / 50% airdrop
                           Social media promotion
                           Transparency log
```

---

## Core Features

### 🔒 Transparent Tokenomics
Every token launched with MintKit uses a publicly documented split:

| Allocation | Default | Purpose |
|------------|---------|---------|
| Liquidity Pool | 50% | Locked minimum 180 days |
| Public Float | 45% | Free market trading |
| Treasury | 5% | Funds ongoing bot operations |

All allocations are configurable. All transactions are logged publicly.

### 🤖 Automated Buyback Engine
Creator rewards flow into a buyback wallet automatically:
- **50% burned** — sent to null address, permanently reducing supply
- **50% airdropped** — distributed to top 100 holders by balance

No manual intervention. No broken promises. Just code running as written.

### 📋 Transparency Log
Every action MintKit takes is logged with a timestamp and transaction hash:
- Token deployment details
- LP lock confirmation
- Every buyback executed
- Every burn transaction
- Every airdrop batch

Anyone can verify the bot did what it said it would do.

### 🔑 Mint Authority Revocation
Immediately after deployment MintKit permanently revokes the mint authority. No one — including the developer — can ever create additional tokens. Supply is fixed forever at launch.

---

## Optional Plugins

MintKit core handles deployment and automation. Optional plugins add more:

### 📡 Trend Scanner (optional)
Scans X (Twitter) and Reddit for viral meme trends. Useful for developers who want data-driven coin timing rather than manual selection.

### 💡 Concept Generator (optional)
Uses AI to generate coin names, tickers, taglines, and meme image prompts from trending content. Useful for high-volume automated launches.

---

## Getting Started

### Prerequisites
- Python 3.11+
- Phantom wallet
- Twitter/X Developer Account (for promotion bot)
- Anthropic API key (for optional AI features)

### Installation

```bash
git clone https://github.com/yourusername/mintkit.git
cd mintkit
python -m pip install -r requirements.txt
```

### Deploy a Token

**Option 1 — From a config file (recommended for developers):**

Create a `coin_config.json` file:
```json
{
  "coin_name": "Your Coin Name",
  "ticker": "TICKER",
  "tagline": "One line description",
  "total_supply": 1000000000,
  "liquidity_pct": 50,
  "float_pct": 45,
  "treasury_pct": 5,
  "lock_days": 180
}
```

Then run:
```bash
python core/deployer.py coin_config.json
```

**Option 2 — From approved database concepts:**
```bash
python plugins/scanner.py        # scan for trends
python plugins/generator.py      # generate concepts
python plugins/generator.py approve <id>   # approve a concept
python core/deployer.py          # deploy approved concepts
```

---

## Project Structure

```
mintkit/
├── core/
│   ├── deployer.py        # SPL token deployment
│   ├── promoter.py        # Social media posting
│   ├── buyback.py         # Buyback, burn, airdrop engine
│   ├── treasury.py        # Reserve fund management
│   └── transparency.py    # Public audit logging
├── plugins/
│   ├── scanner.py         # Optional trend scanning
│   └── generator.py       # Optional concept generation
├── config/
│   └── default.json       # Default configuration
├── docs/                  # Documentation
├── ARCHITECTURE.md        # Full system design
├── README.md
├── requirements.txt
└── .env.example
```

---

## Configuration

All MintKit behavior is controlled by a single config file:

```json
{
  "network": "devnet",
  "wallet_path": "./deployer_wallet.json",

  "tokenomics": {
    "total_supply": 1000000000,
    "liquidity_pct": 50,
    "float_pct": 45,
    "treasury_pct": 5,
    "lock_days": 180
  },

  "buyback": {
    "trigger_sol": 0.5,
    "burn_pct": 50,
    "airdrop_pct": 50,
    "airdrop_holders": 100
  },

  "promotion": {
    "platforms": ["twitter"],
    "disclose_bot": true,
    "disclosure": "Bot-managed project. Not financial advice. DYOR."
  }
}
```

---

## Roadmap

- [x] Trend Scanner
- [x] Concept Generator
- [x] SPL Token Deployer (devnet)
- [x] Liquidity Pool Creation (Raydium)
- [x] LP Locking
- [x] Buyback Engine
- [x] Promotion Bot
- [x] Treasury Manager
- [x] CLI Interface
- [x] Web Dashboard
- [x] Mainnet Launch
- [x] Multi-chain Support (Base, ETH L2)

---

## Ethics & Compliance

MintKit is built around honest, transparent token launches.

- All social media posts disclose bot identity
- All posts include "Not financial advice. DYOR."
- Mint authority revoked at launch — supply permanently fixed
- LP locked on-chain — verifiable by anyone
- Every bot action logged publicly with TX hashes
- No wash trading, no fake volume, no coordinated manipulation

Developers using MintKit are responsible for compliance with the laws and regulations in their jurisdiction. Consult a crypto-friendly attorney before mainnet launch.

---

## License

MIT License — open source and free to use.

---

*Built by JMHMsr on the belief that automation and transparency can make crypto fairer for everyone.*
