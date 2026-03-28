"""
MintKit — Transparency Log
Generates and maintains a public, human-readable audit trail
of every action the bot takes. Every deployment, buyback,
burn, and airdrop is logged with timestamps and TX hashes.
"""

import os
import json
import logging
import sqlite3
from datetime import datetime
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

DB_PATH  = "mintkit.db"
LOG_DIR  = "transparency_logs"

# ── Setup ─────────────────────────────────────────────────
def init_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        log.info(f"Created transparency log directory: {LOG_DIR}")

# ── Database ──────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ── Log Entry Builders ────────────────────────────────────
def log_deployment(deployment: dict):
    entry = {
        "event": "token_deployed",
        "timestamp": deployment.get("deployed_at", datetime.utcnow().isoformat()),
        "network": deployment.get("network", "devnet"),
        "coin_name": deployment["coin_name"],
        "ticker": deployment["ticker"],
        "mint_address": deployment["mint_address"],
        "tx_hash": deployment.get("tx_hash", ""),
        "tokenomics": {
            "total_supply": deployment["total_supply"],
            "mint_authority": "revoked"
        },
        "wallets": {
            "deployer": deployment["deployer_address"],
            "liquidity": deployment["liquidity_wallet"],
            "treasury": deployment["treasury_wallet"]
        },
        "explorer": f"https://explorer.solana.com/address/{deployment['mint_address']}" +
                   ("?cluster=devnet" if deployment.get("network") == "devnet" else "")
    }
    append_log(deployment["ticker"], entry)
    log.info(f"Logged deployment for {deployment['ticker']}")

def log_promotion(promotion: dict):
    entry = {
        "event": "promotion_posted",
        "timestamp": promotion.get("posted_at", datetime.utcnow().isoformat()),
        "platform": promotion["platform"],
        "post_type": promotion["post_type"],
        "post_id": promotion.get("post_id", ""),
        "status": promotion["status"]
    }
    append_log(promotion["ticker"], entry)
    log.info(f"Logged promotion for {promotion['ticker']}")

def log_buyback(buyback: dict):
    entry = {
        "event": "buyback_executed",
        "timestamp": buyback.get("executed_at", datetime.utcnow().isoformat()),
        "trigger_balance_sol": buyback["trigger_balance"],
        "tokens_bought": buyback["tokens_bought"],
        "burn": {
            "amount": buyback["tokens_burned"],
            "tx": buyback.get("burn_tx", "")
        },
        "airdrop": {
            "amount": buyback["tokens_airdropped"],
            "holder_count": buyback["holder_count"],
            "tx": buyback.get("airdrop_tx", "")
        },
        "status": buyback["status"]
    }
    append_log(buyback["ticker"], entry)
    log.info(f"Logged buyback for {buyback['ticker']}")

# ── File Operations ───────────────────────────────────────
def append_log(ticker: str, entry: dict):
    """Append an entry to the coin's transparency log file."""
    init_log_dir()
    log_path = os.path.join(LOG_DIR, f"{ticker.lower()}_log.json")

    existing = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as f:
                data = json.load(f)
                existing = data if isinstance(data, list) else [data]
        except Exception:
            existing = []

    existing.append(entry)
    with open(log_path, "w") as f:
        json.dump(existing, f, indent=2)

def get_log(ticker: str) -> list:
    """Read the full transparency log for a coin."""
    log_path = os.path.join(LOG_DIR, f"{ticker.lower()}_log.json")
    if not os.path.exists(log_path):
        return []
    with open(log_path, "r") as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]

# ── Report Generation ─────────────────────────────────────
def generate_report(ticker: str):
    """Print a human-readable transparency report for a coin."""
    entries = get_log(ticker)
    if not entries:
        log.info(f"No transparency log found for {ticker}.")
        return

    print("\n" + "=" * 60)
    print(f"TRANSPARENCY REPORT — ${ticker}")
    print(f"Generated: {datetime.utcnow().isoformat()}")
    print("=" * 60)

    for entry in entries:
        event = entry.get("event", "unknown")
        ts    = entry.get("timestamp", "")

        if event == "token_deployed":
            print(f"\n📦 DEPLOYMENT — {ts}")
            print(f"   Network:    {entry.get('network', '').upper()}")
            print(f"   Mint:       {entry.get('mint_address', '')}")
            print(f"   TX:         {entry.get('tx_hash', '')}")
            print(f"   Authority:  {entry.get('tokenomics', {}).get('mint_authority', '')}")
            print(f"   Explorer:   {entry.get('explorer', '')}")

        elif event == "promotion_posted":
            print(f"\n📣 PROMOTION — {ts}")
            print(f"   Platform:   {entry.get('platform', '')}")
            print(f"   Type:       {entry.get('post_type', '')}")
            print(f"   Post ID:    {entry.get('post_id', '')}")
            print(f"   Status:     {entry.get('status', '')}")

        elif event == "buyback_executed":
            print(f"\n🔄 BUYBACK — {ts}")
            print(f"   Triggered:  {entry.get('trigger_balance_sol', 0):.4f} SOL")
            print(f"   Bought:     {entry.get('tokens_bought', 0):,} tokens")
            burn    = entry.get("burn", {})
            airdrop = entry.get("airdrop", {})
            print(f"   Burned:     {burn.get('amount', 0):,} tokens → TX: {burn.get('tx', '')}")
            print(f"   Airdropped: {airdrop.get('amount', 0):,} tokens to {airdrop.get('holder_count', 0)} holders")
            print(f"   Status:     {entry.get('status', '')}")

    print("\n" + "=" * 60)
    print(f"Total events: {len(entries)}")
    print("=" * 60 + "\n")

def generate_all_reports():
    """Generate reports for all coins in the transparency log directory."""
    init_log_dir()
    files = [f for f in os.listdir(LOG_DIR) if f.endswith("_log.json")]
    if not files:
        log.info("No transparency logs found.")
        return
    for f in files:
        ticker = f.replace("_log.json", "").upper()
        generate_report(ticker)

def sync_from_database():
    """
    Sync all database records to transparency log files.
    Useful for rebuilding logs or catching up after a restart.
    """
    log.info("Syncing database to transparency logs...")
    conn = get_db()
    cur  = conn.cursor()

    # Sync deployments
    try:
        cur.execute("SELECT * FROM deployments")
        for row in cur.fetchall():
            log_deployment(dict(row))
    except Exception as e:
        log.warning(f"Could not sync deployments: {e}")

    # Sync promotions
    try:
        cur.execute("SELECT * FROM promotions")
        for row in cur.fetchall():
            log_promotion(dict(row))
    except Exception as e:
        log.warning(f"Could not sync promotions: {e}")

    # Sync buybacks
    try:
        cur.execute("SELECT * FROM buybacks")
        for row in cur.fetchall():
            log_buyback(dict(row))
    except Exception as e:
        log.warning(f"Could not sync buybacks: {e}")

    conn.close()
    log.info("Sync complete.")

# ── Main ──────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        ticker = sys.argv[1].upper()
        generate_report(ticker)
    elif len(sys.argv) == 1:
        sync_from_database()
        generate_all_reports()
    else:
        print("Usage:")
        print("  python core/transparency.py          # sync and show all reports")
        print("  python core/transparency.py FADE     # show report for $FADE")
