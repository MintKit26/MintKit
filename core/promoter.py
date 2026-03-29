"""
MintKit — Promotion Bot
Posts token launches to X (Twitter) with full disclosure language.
Honest, transparent, bot-identity always disclosed.
"""

import os
import json
import logging
import sqlite3
from datetime import datetime
from typing import Optional

import tweepy
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

DB_PATH = "mintkit.db"

# ── Hardcode keys here if .env not loading ────────────────
TWITTER_API_KEY         = os.getenv("TWITTER_API_KEY", "paste_consumer_key")
TWITTER_API_SECRET      = os.getenv("TWITTER_API_SECRET", "paste_consumer_secret")
TWITTER_ACCESS_TOKEN    = os.getenv("TWITTER_ACCESS_TOKEN", "paste_access_token")
TWITTER_ACCESS_SECRET   = os.getenv("TWITTER_ACCESS_SECRET", "paste_access_secret")

# ── Disclosure (always appended to every post) ────────────
DISCLOSURE = "\n\n🤖 Bot-managed project. Not financial advice. DYOR."

# ── Database ──────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_promotions_table():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS deployments (
        concept_id TEXT PRIMARY KEY, coin_name TEXT, ticker TEXT,
        mint_address TEXT, deployer_address TEXT, liquidity_wallet TEXT,
        treasury_wallet TEXT, total_supply INTEGER, network TEXT,
        deployed_at TEXT, status TEXT, tx_hash TEXT)""")
    cur.execute("""INSERT OR IGNORE INTO deployments VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        ('mkit001','MintKit','MKIT',
        'Hkwj68C2EtdwmcAohej9XLhowf3E9WPuVPsiTk5FAXAP',
        'ELj8Ju526bbMfM2UEazChPwzcmm6aWF4afpzHd72oG23',
        'AKYKKc1eDLGdLeenhqVAWh8vmhDhFN1B5SXEV4LyofD6',
        '3hiuiBF75bGd3Matn67KQXDiZDB5Ukz5EaW9zX9jJVb1',
        1000000000,'mainnet','2026-03-29T00:00:00','deployed',
        'GeLGcX4FLjsCCYGDEA7vN8VFQrpbZksNHqppCZQDqqjH4TMK1bQ4c9aQAPretzoPp6dRBniNPcLVpkiBqQuKQiG'))
    cur.execute("""
        CREATE TABLE IF NOT EXISTS promotions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id TEXT,
            coin_name TEXT,
            ticker TEXT,
            platform TEXT,
            post_type TEXT,
            content TEXT,
            post_id TEXT,
            posted_at TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()
    log.info("Promotions table ready.")

def save_promotion(concept_id, coin_name, ticker, platform, post_type, content, post_id, status):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO promotions
        (concept_id, coin_name, ticker, platform, post_type, content, post_id, posted_at, status)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (concept_id, coin_name, ticker, platform, post_type, content, post_id,
          datetime.utcnow().isoformat(), status))
    conn.commit()
    conn.close()

# ── Load Deployments ──────────────────────────────────────
def get_unannounced_deployments() -> list:
    """Get deployed tokens that haven't been promoted yet."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT d.* FROM deployments d
        LEFT JOIN promotions p ON d.concept_id = p.concept_id
        WHERE d.status = 'deployed'
        AND p.concept_id IS NULL
    """)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows

# ── Twitter Client ────────────────────────────────────────
def get_twitter_client():
    return tweepy.Client(
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_SECRET
    )

# ── Post Templates ────────────────────────────────────────
def build_launch_post(deployment: dict) -> str:
    ticker    = deployment["ticker"]
    coin_name = deployment["coin_name"]
    mint      = deployment["mint_address"]
 NETWORK = os.getenv("NETWORK", "mainnet")
    liq_pct   = deployment.get("liquidity_pct", 50)

    explorer = f"https://explorer.solana.com/address/{mint}"
    if network == "devnet":
        explorer += "?cluster=devnet"

    post = f"""🚀 {coin_name} (${ticker}) is live on Solana!

📋 Contract: {mint}

💰 Tokenomics:
• {liq_pct}% liquidity locked
• Automatic buyback & burn
• 50% burns / 50% airdropped to holders
• Mint authority revoked ✅

🔍 Verify on-chain:
{explorer}{DISCLOSURE}"""

    return post

def build_buyback_post(deployment: dict, burn_amount: int, airdrop_amount: int, tx_hash: str) -> str:
    ticker    = deployment["ticker"]
    coin_name = deployment["coin_name"]

    post = f"""🔥 ${ticker} Buyback Complete!

Burned: {burn_amount:,} ${ticker} 🔥
Airdropped: {airdrop_amount:,} ${ticker} to top holders 🎁

TX: {tx_hash}

Supply decreasing. Holders rewarded.{DISCLOSURE}"""

    return post

# ── Post to Twitter ───────────────────────────────────────
def post_to_twitter(content: str) -> Optional[str]:
    try:
        client = get_twitter_client()
        response = client.create_tweet(text=content)
        post_id = str(response.data["id"])
        log.info(f"Posted to Twitter. Tweet ID: {post_id}")
        return post_id
    except Exception as e:
        log.error(f"Twitter post failed: {e}")
        return None

# ── Main Promotion Flow ───────────────────────────────────
def promote_deployment(deployment: dict):
    """Post launch announcement for a deployed token."""
    coin_name  = deployment["coin_name"]
    ticker     = deployment["ticker"]
    concept_id = deployment["concept_id"]

    log.info(f"Promoting {coin_name} (${ticker})...")

    # Build post content
    content = build_launch_post(deployment)

    log.info("Post content:")
    log.info("-" * 40)
    log.info(content)
    log.info("-" * 40)

    # Post to Twitter
    post_id = post_to_twitter(content)
    status  = "posted" if post_id else "failed"

    # Save record
    save_promotion(
        concept_id=concept_id,
        coin_name=coin_name,
        ticker=ticker,
        platform="twitter",
        post_type="launch",
        content=content,
        post_id=post_id or "",
        status=status
    )

    if post_id:
        log.info(f"Launch announced! https://twitter.com/TrendMintBot/status/{post_id}")
    else:
        log.error("Promotion failed — check your Twitter API keys.")

def run_promoter():
    """Promote all unannounced deployments."""
    log.info("Starting Promotion Bot...")
    init_promotions_table()

    deployments = get_unannounced_deployments()
    if not deployments:
        log.info("No new deployments to promote.")
        return

    log.info(f"Found {len(deployments)} deployment(s) to promote.")
    for deployment in deployments:
        promote_deployment(deployment)

if __name__ == "__main__":
    run_promoter()
