"""
MintKit — Treasury Manager
Manages the bot's SOL reserve fund.
Tracks income from token allocations, controls spending
on future deployments, and logs every transaction publicly.
"""

import os
import json
import logging
import sqlite3
from datetime import datetime
from typing import Optional

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────
DEVNET_URL          = "https://api.devnet.solana.com"
MAINNET_URL         = "https://api.mainnet-beta.solana.com"
NETWORK             = os.getenv("NETWORK", "devnet")
RPC_URL             = DEVNET_URL if NETWORK == "devnet" else MAINNET_URL

MAX_DAILY_SELL_PCT  = 1.0    # never sell more than 1% of daily volume
MIN_RESERVE_SOL     = 0.5    # always keep this much SOL in reserve
TREASURY_PCT        = 5.0    # % of each token supply retained

DB_PATH = "mintkit.db"

# ── Database ──────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_treasury_table():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS treasury (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            ticker TEXT,
            amount_sol REAL,
            amount_tokens INTEGER,
            description TEXT,
            tx_hash TEXT,
            logged_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS treasury_balance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sol_balance REAL,
            checked_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    log.info("Treasury tables ready.")

def log_treasury_event(event_type, ticker, amount_sol, amount_tokens, description, tx_hash=""):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO treasury
        (event_type, ticker, amount_sol, amount_tokens, description, tx_hash, logged_at)
        VALUES (?,?,?,?,?,?,?)
    """, (event_type, ticker, amount_sol, amount_tokens, description, tx_hash,
          datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

# ── Wallet ────────────────────────────────────────────────
def load_wallet(wallet_path: str) -> Optional[Keypair]:
    if not os.path.exists(wallet_path):
        log.error(f"Wallet not found: {wallet_path}")
        return None
    with open(wallet_path, "r") as f:
        data = json.load(f)
    return Keypair.from_bytes(bytes(data))

def get_sol_balance(client: Client, pubkey: Pubkey) -> float:
    response = client.get_balance(pubkey)
    return response.value / 1_000_000_000

# ── Treasury Status ───────────────────────────────────────
def get_treasury_status(client: Client) -> dict:
    """Get full treasury status across all coin wallets."""
    status = {
        "checked_at": datetime.utcnow().isoformat(),
        "network": NETWORK,
        "wallets": [],
        "total_sol": 0.0,
        "total_events": 0
    }

    conn = get_db()
    cur = conn.cursor()

    # Get all deployments
    try:
        cur.execute("SELECT * FROM deployments WHERE status = 'deployed'")
        deployments = [dict(row) for row in cur.fetchall()]
    except:
        deployments = []

    for d in deployments:
        ticker = d["ticker"]
        wallet_path = f"wallet_{ticker.lower()}_treasury.json"
        wallet = load_wallet(wallet_path)

        if wallet:
            balance = get_sol_balance(client, wallet.pubkey())
            status["wallets"].append({
                "ticker": ticker,
                "address": str(wallet.pubkey()),
                "sol_balance": balance,
                "wallet_path": wallet_path
            })
            status["total_sol"] += balance
        else:
            status["wallets"].append({
                "ticker": ticker,
                "address": d.get("treasury_wallet", "unknown"),
                "sol_balance": 0.0,
                "wallet_path": wallet_path,
                "note": "wallet file not found"
            })

    # Get event count
    try:
        cur.execute("SELECT COUNT(*) as count FROM treasury")
        status["total_events"] = cur.fetchone()["count"]
    except:
        status["total_events"] = 0

    conn.close()
    return status

# ── Sell Schedule ─────────────────────────────────────────
def calculate_safe_sell_amount(ticker: str, current_balance: int, daily_volume: int) -> int:
    """
    Calculate how many tokens can be safely sold today.
    Never exceeds MAX_DAILY_SELL_PCT of daily volume.
    """
    max_sell = int(daily_volume * (MAX_DAILY_SELL_PCT / 100))
    safe_amount = min(current_balance, max_sell)
    log.info(f"[{ticker}] Safe sell amount: {safe_amount:,} tokens "
             f"(max {MAX_DAILY_SELL_PCT}% of {daily_volume:,} daily volume)")
    return safe_amount

def check_deployment_funding(client: Client) -> list:
    """
    Check if any upcoming deployments need funding.
    Returns list of deployments that need SOL.
    """
    needs_funding = []
    conn = get_db()
    cur = conn.cursor()

    # Check for approved but undeployed concepts
    try:
        cur.execute("""
            SELECT c.* FROM coin_concepts c
            LEFT JOIN deployments d ON c.id = d.concept_id
            WHERE c.approved = 1 AND d.concept_id IS NULL
        """)
        pending = [dict(row) for row in cur.fetchall()]
        if pending:
            log.info(f"Found {len(pending)} concept(s) approved but not yet deployed.")
            for p in pending:
                needs_funding.append({
                    "ticker": p["ticker"],
                    "coin_name": p["coin_name"],
                    "estimated_sol_needed": 0.85  # minimum for mainnet deployment
                })
    except Exception as e:
        log.warning(f"Could not check pending deployments: {e}")

    conn.close()
    return needs_funding

# ── Report ────────────────────────────────────────────────
def print_treasury_report(client: Client):
    """Print a full treasury report."""
    status = get_treasury_status(client)

    print("\n" + "=" * 55)
    print("💰 MINTKIT TREASURY REPORT")
    print("=" * 55)
    print(f"Network:      {status['network'].upper()}")
    print(f"Checked at:   {status['checked_at']}")
    print(f"Total SOL:    {status['total_sol']:.4f} SOL")
    print(f"Total Events: {status['total_events']}")

    if status["wallets"]:
        print(f"\nTreasury Wallets:")
        for w in status["wallets"]:
            print(f"\n  ${w['ticker']}")
            print(f"    Address: {w['address']}")
            print(f"    Balance: {w['sol_balance']:.4f} SOL")
            if "note" in w:
                print(f"    Note:    {w['note']}")

    # Check pending deployments
    needs = check_deployment_funding(client)
    if needs:
        print(f"\n⚠️  Pending Deployments Needing Funding:")
        for n in needs:
            print(f"  • {n['coin_name']} (${n['ticker']}) — needs ~{n['estimated_sol_needed']} SOL")

    # Transaction history
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM treasury ORDER BY logged_at DESC LIMIT 10")
        events = [dict(row) for row in cur.fetchall()]
        if events:
            print(f"\nRecent Treasury Events:")
            for e in events:
                print(f"  [{e['logged_at'][:10]}] {e['event_type']} — "
                      f"${e['ticker']} — {e['amount_sol']:.4f} SOL — {e['description']}")
    except:
        pass
    conn.close()

    print("\n" + "=" * 55)

    # Save to transparency log
    log_path = "transparency_logs/treasury_report.json"
    os.makedirs("transparency_logs", exist_ok=True)
    with open(log_path, "w") as f:
        json.dump(status, f, indent=2)
    log.info(f"Treasury report saved to {log_path}")

# ── Fund Next Deployment ──────────────────────────────────
def fund_next_deployment(ticker: str, amount_sol: float, tx_hash: str = ""):
    """Log a treasury spend for a deployment."""
    log_treasury_event(
        event_type="deployment_funded",
        ticker=ticker,
        amount_sol=amount_sol,
        amount_tokens=0,
        description=f"Funded deployment for ${ticker}",
        tx_hash=tx_hash
    )
    log.info(f"Treasury: logged {amount_sol:.4f} SOL spend for ${ticker} deployment")

def record_token_allocation(ticker: str, amount_tokens: int):
    """Log when treasury tokens are allocated at launch."""
    log_treasury_event(
        event_type="tokens_allocated",
        ticker=ticker,
        amount_sol=0.0,
        amount_tokens=amount_tokens,
        description=f"{TREASURY_PCT}% treasury allocation at launch"
    )
    log.info(f"Treasury: recorded {amount_tokens:,} ${ticker} tokens allocated")

# ── Main ──────────────────────────────────────────────────
def run_treasury_manager():
    """Run full treasury check and report."""
    log.info("Starting Treasury Manager...")
    init_treasury_table()

    client = Client(RPC_URL)
    log.info(f"Connected to Solana {NETWORK}")

    print_treasury_report(client)

if __name__ == "__main__":
    run_treasury_manager()
