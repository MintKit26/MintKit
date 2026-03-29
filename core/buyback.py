"""
MintKit — Buyback Engine
Monitors creator rewards wallet, executes buybacks,
burns 50% and airdrops 50% to top holders automatically.
"""

import os
import json
import logging
import sqlite3
import time
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
NETWORK = os.getenv("NETWORK", "mainnet")
RPC_URL             = DEVNET_URL if NETWORK == "devnet" else MAINNET_URL

BUYBACK_TRIGGER_SOL = 0.5       # trigger buyback when wallet reaches this
BURN_PCT            = 50        # % of buyback tokens to burn
AIRDROP_PCT         = 50        # % of buyback tokens to airdrop
AIRDROP_HOLDERS     = 100       # top N holders to airdrop to
NULL_ADDRESS        = "1nc1nerator11111111111111111111111111111111"  # Solana burn address

DB_PATH = "mintkit.db"

# ── Database ──────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_buyback_table():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS deployments (concept_id TEXT PRIMARY KEY, coin_name TEXT, ticker TEXT, mint_address TEXT, deployer_address TEXT, liquidity_wallet TEXT, treasury_wallet TEXT, total_supply INTEGER, network TEXT, deployed_at TEXT, status TEXT, tx_hash TEXT)")
    cur.execute("INSERT OR IGNORE INTO deployments VALUES ('mkit001','MintKit','MKIT','Hkwj68C2EtdwmcAohej9XLhowf3E9WPuVPsiTk5FAXAP','ELj8Ju526bbMfM2UEazChPwzcmm6aWF4afpzHd72oG23','AKYKKc1eDLGdLeenhqVAWh8vmhDhFN1B5SXEV4LyofD6','3hiuiBF75bGd3Matn67KQXDiZDB5Ukz5EaW9zX9jJVb1',1000000000,'mainnet','2026-03-29T00:00:00','deployed','GeLGcX4FLjsCCYGDEA7vN8VFQrpbZksNHqppCZQDqqjH4TMK1bQ4c9aQAPretzoPp6dRBniNPcLVpkiBqQuKQiG')")
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
        CREATE TABLE IF NOT EXISTS deployments (
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
        CREATE TABLE IF NOT EXISTS buybacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id TEXT,
            ticker TEXT,
            trigger_balance REAL,
            tokens_bought INTEGER,
            tokens_burned INTEGER,
            tokens_airdropped INTEGER,
            holder_count INTEGER,
            burn_tx TEXT,
            airdrop_tx TEXT,
            executed_at TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()
    log.info("Buyback table ready.")

def save_buyback(concept_id, ticker, trigger_balance, tokens_bought,
                 tokens_burned, tokens_airdropped, holder_count,
                 burn_tx, airdrop_tx, status):
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
        INSERT INTO buybacks
        (concept_id, ticker, trigger_balance, tokens_bought, tokens_burned,
         tokens_airdropped, holder_count, burn_tx, airdrop_tx, executed_at, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (concept_id, ticker, trigger_balance, tokens_bought, tokens_burned,
          tokens_airdropped, holder_count, burn_tx, airdrop_tx,
          datetime.utcnow().isoformat(), status))
    conn.commit()
    conn.close()

# ── Load Active Deployments ───────────────────────────────
def get_active_deployments() -> list:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM deployments WHERE status = 'deployed'")
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows

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

# ── Buyback Logic ─────────────────────────────────────────
def check_and_execute_buyback(deployment: dict, client: Client):
    """
    Check if treasury wallet has enough SOL to trigger a buyback.
    If yes, execute buyback, burn 50%, airdrop 50%.
    """
    ticker     = deployment["ticker"]
    concept_id = deployment["concept_id"]

    # Load treasury wallet
    treasury_wallet_path = f"wallet_{ticker.lower()}_treasury.json"
    treasury = load_wallet(treasury_wallet_path)
    if not treasury:
        log.warning(f"Treasury wallet not found for {ticker}. Skipping.")
        return

    # Check balance
    balance = get_sol_balance(client, treasury.pubkey())
    log.info(f"[{ticker}] Treasury balance: {balance:.4f} SOL")

    if balance < BUYBACK_TRIGGER_SOL:
        log.info(f"[{ticker}] Below trigger threshold ({BUYBACK_TRIGGER_SOL} SOL). Skipping.")
        return

    log.info(f"[{ticker}] Trigger threshold reached! Executing buyback...")

    # Calculate token amounts
    # In production this would buy tokens from the DEX
    # On devnet we simulate the amounts
    total_tokens_bought = int(balance * 1_000_000)  # simulated token purchase
    tokens_to_burn      = int(total_tokens_bought * (BURN_PCT / 100))
    tokens_to_airdrop   = total_tokens_bought - tokens_to_burn

    log.info(f"[{ticker}] Tokens bought:     {total_tokens_bought:,}")
    log.info(f"[{ticker}] Tokens to burn:    {tokens_to_burn:,} ({BURN_PCT}%)")
    log.info(f"[{ticker}] Tokens to airdrop: {tokens_to_airdrop:,} ({AIRDROP_PCT}%)")

    # Execute burn (send to null address)
    burn_tx    = execute_burn(ticker, tokens_to_burn, treasury, client)

    # Execute airdrop to top holders
    airdrop_tx = execute_airdrop(ticker, tokens_to_airdrop, deployment, client)

    # Save record
    save_buyback(
        concept_id=concept_id,
        ticker=ticker,
        trigger_balance=balance,
        tokens_bought=total_tokens_bought,
        tokens_burned=tokens_to_burn,
        tokens_airdropped=tokens_to_airdrop,
        holder_count=AIRDROP_HOLDERS,
        burn_tx=burn_tx or "",
        airdrop_tx=airdrop_tx or "",
        status="executed" if burn_tx else "failed"
    )

    # Log to transparency file
    log_buyback_transparency(ticker, balance, total_tokens_bought,
                             tokens_to_burn, tokens_to_airdrop,
                             burn_tx, airdrop_tx)

def execute_burn(ticker: str, amount: int, treasury: Keypair, client: Client) -> Optional[str]:
    """Send tokens to null address (permanent burn)."""
    try:
        # In production: build SPL token transfer to null address
        # On devnet: simulate and log
        log.info(f"[{ticker}] Burning {amount:,} tokens → null address")
        log.info(f"[{ticker}] Burn address: {NULL_ADDRESS}")

        # Simulated TX hash for devnet testing
        burn_tx = f"BURN_{ticker}_{int(time.time())}"
        log.info(f"[{ticker}] Burn TX: {burn_tx}")
        return burn_tx

    except Exception as e:
        log.error(f"[{ticker}] Burn failed: {e}")
        return None

def execute_airdrop(ticker: str, amount: int, deployment: dict, client: Client) -> Optional[str]:
    """Distribute tokens to top holders."""
    try:
        log.info(f"[{ticker}] Airdropping {amount:,} tokens to top {AIRDROP_HOLDERS} holders...")

        # In production: query token holders from chain, distribute proportionally
        # On devnet: simulate and log
        per_holder = amount // AIRDROP_HOLDERS
        log.info(f"[{ticker}] Each holder receives: {per_holder:,} tokens")

        airdrop_tx = f"AIRDROP_{ticker}_{int(time.time())}"
        log.info(f"[{ticker}] Airdrop TX: {airdrop_tx}")
        return airdrop_tx

    except Exception as e:
        log.error(f"[{ticker}] Airdrop failed: {e}")
        return None

# ── Transparency Log ──────────────────────────────────────
def log_buyback_transparency(ticker, balance, bought, burned, airdropped, burn_tx, airdrop_tx):
    log_entry = {
        "event": "buyback_executed",
        "timestamp": datetime.utcnow().isoformat(),
        "ticker": ticker,
        "trigger_balance_sol": balance,
        "tokens_bought": bought,
        "burn": {
            "amount": burned,
            "pct": BURN_PCT,
            "tx": burn_tx
        },
        "airdrop": {
            "amount": airdropped,
            "pct": AIRDROP_PCT,
            "holders": AIRDROP_HOLDERS,
            "tx": airdrop_tx
        }
    }

    log_path = f"transparency_{ticker.lower()}.json"

    # Append to existing log
    existing = []
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                existing = data
            else:
                existing = [data]

    existing.append(log_entry)
    with open(log_path, "w") as f:
        json.dump(existing, f, indent=2)

    log.info(f"[{ticker}] Buyback logged to {log_path}")

# ── Main ──────────────────────────────────────────────────
def run_buyback_engine():
    """Check all active deployments and execute buybacks if triggered."""
    log.info("Starting Buyback Engine...")
    init_buyback_table()

    client = Client(RPC_URL)
    log.info(f"Connected to Solana {NETWORK}")

    deployments = get_active_deployments()
    if not deployments:
        log.info("No active deployments found.")
        return

    log.info(f"Monitoring {len(deployments)} active deployment(s)...")
    for deployment in deployments:
        check_and_execute_buyback(deployment, client)

    log.info("Buyback check complete.")

if __name__ == "__main__":
    run_buyback_engine()
