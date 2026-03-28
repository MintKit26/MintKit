# MintKit — Solana Token Launch Toolkit
## Architecture Document v1.0

---

## Vision

MintKit is an open source developer toolkit that gives anyone the full
infrastructure to launch a transparent, community-first token on Solana.
Every launch is honest, verifiable, and automated — removing the human
failures that plague most meme coin projects.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        MINTKIT                              │
│                   Developer Toolkit                         │
└──────┬──────────────┬──────────────┬────────────────────────┘
       │              │              │
       ▼              ▼              ▼
┌────────────┐ ┌────────────┐ ┌────────────────┐
│    CLI     │ │ Dashboard  │ │      API       │
│  Interface │ │    (Web)   │ │   (Headless)   │
└────────────┘ └────────────┘ └────────────────┘
       │              │              │
       └──────────────┴──────────────┘
                      │
         ┌────────────▼────────────┐
         │       CORE ENGINE       │
         └────────────┬────────────┘
                      │
     ┌────────────────┼────────────────┐
     │                │                │
     ▼                ▼                ▼
┌─────────┐    ┌─────────────┐   ┌──────────────┐
│  TREND  │    │   CONCEPT   │   │    TOKEN     │
│ SCANNER │    │  GENERATOR  │   │  DEPLOYER    │
└─────────┘    └─────────────┘   └──────────────┘
     │                │                │
     ▼                ▼                ▼
┌─────────┐    ┌─────────────┐   ┌──────────────┐
│PROMOTION│    │   BUYBACK   │   │ TRANSPARENCY │
│   BOT   │    │   ENGINE    │   │     LOG      │
└─────────┘    └─────────────┘   └──────────────┘
```

---

## Three Ways to Use MintKit

### 1. CLI (Command Line Interface)
For developers who want full control via terminal commands.
```bash
mintkit scan                    # scan for trends
mintkit generate                # generate coin concepts
mintkit deploy --ticker FADE    # deploy approved concept
mintkit status                  # check all active coins
```

### 2. Dashboard (Web UI)
A clean web interface for developers who prefer visual management.
- View trending memes in real time
- Review and approve coin concepts
- Monitor deployments and buybacks
- View transparency log

### 3. API (Headless)
For developers building their own tools on top of MintKit.
```
POST /api/scan
POST /api/generate
POST /api/deploy
GET  /api/coins
GET  /api/transparency/:coinId
```

---

## Module 1 — Trend Scanner

**Purpose:** Identify trending memes worth building a coin around.

**Data Sources (configurable):**
- X (Twitter) — enabled by default
- Reddit — optional
- Instagram — optional
- Facebook — optional
- Custom RSS feeds — optional

**Configuration per project:**
```json
{
  "sources": ["twitter", "reddit"],
  "scan_interval_hours": 6,
  "min_viability_score": 65,
  "keywords": ["meme", "viral", "based"],
  "exclude_keywords": ["nsfw", "politics"]
}
```

**Output:** Ranked list of meme trends with scores

---

## Module 2 — Concept Generator

**Purpose:** Turn a meme trend into a complete coin identity.

**Generates:**
- Coin name and ticker
- Tagline and backstory
- Meme image prompt
- Social media post templates
- Disclosure language

**Developer controls:**
- Auto-approve above a score threshold
- Manual review mode (default)
- Custom prompt templates
- Brand guidelines enforcement

**Guardrails (always on):**
- No financial promises
- No impersonation of existing coins
- Disclosure language always included
- Bot identity always disclosed

---

## Module 3 — Token Deployer

**Purpose:** Deploy the token on-chain with transparent, locked tokenomics.

**Supported networks:**
- Solana (primary)
- Base (coming soon)
- Ethereum L2s (roadmap)

**Default tokenomics (fully configurable):**
```
Total Supply:     1,000,000,000
Liquidity Pool:   50% — locked minimum 180 days
Public Float:     45% — free market
Treasury:          5% — funds next deployment
```

**Deployment steps (automated):**
1. Generate new wallet keypair for this coin
2. Deploy SPL token
3. Create liquidity pool on Raydium
4. Lock LP tokens via time-lock contract
5. Publish all addresses to transparency log
6. Notify promotion bot

**Developer controls:**
- Custom supply amount
- Custom tokenomics split
- Custom lock duration
- Devnet or mainnet toggle

---

## Module 4 — Promotion Bot

**Purpose:** Announce the launch honestly across social media.

**Post content (auto-generated):**
- Meme image
- Coin name, ticker, contract address
- LP lock proof link
- Transparency log link
- Disclosure: "Bot-managed project. Not financial advice. DYOR."

**Supported platforms:**
- X (Twitter)
- Instagram
- Facebook
- Telegram
- Discord

**Developer controls:**
- Choose which platforms to post to
- Custom post templates
- Post schedule (immediate or delayed)
- Language/tone settings

---

## Module 5 — Buyback Engine

**Purpose:** Automatically reinvest creator rewards to benefit holders.

**Flow:**
```
Creator Rewards
      │
      ▼
Buyback Wallet
      │
   ┌──┴──┐
   │     │
  50%   50%
  BURN  AIRDROP
   │     │
   ▼     ▼
 Null   Top 100
Address Holders
```

**Trigger options:**
- Balance threshold (default: 0.5 SOL)
- Time-based (every X days)
- Manual trigger

**Developer controls:**
- Custom burn/airdrop split
- Custom holder count for airdrop
- Minimum holder balance to qualify

---

## Module 6 — Transparency Log

**Purpose:** Immutable public record of every action taken.

**Every entry contains:**
- Timestamp
- Action type
- Transaction hash
- Amount
- Reasoning (for AI decisions)

**Storage options:**
- Local JSON file (default)
- GitHub repository (recommended)
- Arweave (permanent, immutable)
- Public API endpoint

**Auto-generated per launch:**
- Launch report (tokenomics, addresses, lock TX)
- Buyback reports (burn TX, airdrop TXs)
- Treasury reports

---

## Module 7 — Treasury Manager

**Purpose:** Manage the bot reserve to fund future deployments.

**Income sources:**
- 5% of each token supply at launch
- Gradual sell schedule (max 1% daily volume)

**Spend triggers:**
- Next coin deployment fees
- API costs
- Infrastructure costs

**Rules (hardcoded):**
- Never sells more than 1% of daily volume
- Only sells when next deployment is ready
- All transactions logged publicly

---

## Developer Configuration File

Each MintKit project has a single config file:

```json
{
  "project_name": "My Meme Bot",
  "network": "devnet",
  "wallet_path": "./wallet.json",

  "scanner": {
    "sources": ["twitter"],
    "interval_hours": 6,
    "min_score": 65,
    "auto_approve_above": 85
  },

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
    "disclosure": "Bot-managed project. Not financial advice. DYOR.",
    "disclose_bot": true
  },

  "transparency": {
    "storage": "github",
    "repo": "yourusername/mintkit-log"
  }
}
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| CLI | Python, Click |
| Dashboard | React, TailwindCSS |
| API | FastAPI |
| Trend Scanner | Tweepy, PRAW, Anthropic Claude |
| Concept Generator | Anthropic Claude API |
| Token Deployment | Solana Web3.js, Anchor, Raydium SDK |
| Buyback Engine | Solana Web3.js |
| Database | SQLite (local) / PostgreSQL (hosted) |
| Transparency Log | JSON / GitHub / Arweave |

---

## Project Structure

```
mintkit/
├── core/
│   ├── scanner.py          # Trend scanning
│   ├── generator.py        # Concept generation
│   ├── deployer.py         # Token deployment
│   ├── promoter.py         # Social media posting
│   ├── buyback.py          # Buyback engine
│   ├── treasury.py         # Treasury management
│   └── transparency.py     # Transparency logging
├── cli/
│   └── main.py             # CLI interface
├── dashboard/
│   ├── src/                # React frontend
│   └── api/                # FastAPI backend
├── config/
│   └── default.json        # Default configuration
├── tests/
│   └── devnet/             # Devnet test suite
├── docs/                   # Documentation
├── README.md
└── requirements.txt
```

---

## Business Model

**Open Source Core:**
- Full toolkit free and open source on GitHub
- Community can contribute and extend

**Revenue:**
- Flat fee per mainnet deployment (e.g. 0.1 SOL)
- Optional hosted dashboard (SaaS tier)
- Premium features (multi-chain, advanced analytics)

---

## Development Phases

### Phase 1 — Core Engine (Current)
- ✅ Trend Scanner
- ✅ Concept Generator
- ⬜ Token Deployer (devnet)
- ⬜ Transparency Log

### Phase 2 — Automation
- ⬜ Promotion Bot
- ⬜ Buyback Engine
- ⬜ Treasury Manager

### Phase 3 — Developer Experience
- ⬜ CLI interface
- ⬜ Config file system
- ⬜ Full documentation

### Phase 4 — Platform
- ⬜ Web Dashboard
- ⬜ REST API
- ⬜ Mainnet launch
- ⬜ Multi-chain support

---

## Legal

- Register business entity before mainnet launch
- Consult crypto-friendly attorney re: token securities classification
- All promotions include disclosure language
- Bot identity always disclosed on all platforms
- Keep records of all bot decisions for compliance

---

*MintKit is built on the belief that transparency and automation
can make crypto fairer for everyone.*
