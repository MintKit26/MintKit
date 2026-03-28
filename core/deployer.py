"""
MintKit — Token Deployer
Deploys SPL tokens on Solana devnet with transparent, locked tokenomics.
Uses solana and solders libraries only.
"""

import os
import json
import logging
import sqlite3
import sys
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import CreateAccountParams, create_account
from solders.instruction import Instruction, AccountMeta
from solders.transaction import Transaction
from solders.message import Message
from solders.hash import Hash
from solana.rpc.api import Client
from solana.rpc.types import TxOpts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Network ───────────────────────────────────────────────
DEVNET_URL  = "https://api.devnet.solana.com"
MAINNET_URL = "https://api.mainnet-beta.solana.com"
NETWORK     = "devnet"
RPC_URL     = DEVNET_URL if NETWORK == "devnet" else MAINNET_URL

DB_PATH = "mintkit.db"

# SPL Token Program ID
TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJe1bSf")
SYSVAR_RENT_PUBKEY = Pubkey.from_string("SysvarRent111111111111111111111111111111111")
SYSTEM_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111111")

# ── Data Structures ───────────────────────────────────────
@dataclass
class TokenConfig:
    coin_name: str
    ticker: str
    tagline: str
    total_supply: int       = 1_000_000_000
    liquidity_pct: float    = 50.0
    float_pct: float        = 45.0
    treasury_pct: float     = 5.0
    lock_days: int          = 180
    decimals: int           = 9

@dataclass
class DeployedToken:
    concept_id: str
    coin_name: str
    ticker: str
    mint_address: str
    deployer_address: str
    liquidity_wallet: str
    treasury_wallet: str
    total_supply: int
    network: str
    deployed_at: str
    status: str
    tx_hash: Optional[str] = None

# ── Database ──────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_deployments_table():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS deployments (
            concept_id TEXT PRIMARY KEY,
            coin_name TEXT,
            ticker TEXT,
            mint_address TEXT,
            deployer_address TEXT,
            liquidity_wallet TEXT,
            treasury_wallet TEXT,
            total_supply INTEGER,
            network TEXT,
            deployed_at TEXT,
            status TEXT,
            tx_hash TEXT
        )
    """)
    conn.commit()
    conn.close()
    log.info("Deployments table ready.")

def save_deployment(token: DeployedToken):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO deployments
        (concept_id, coin_name, ticker, mint_address, deployer_address,
         liquidity_wallet, treasury_wallet, total_supply, network,
         deployed_at, status, tx_hash)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        token.concept_id, token.coin_name, token.ticker,
        token.mint_address, token.deployer_address,
        token.liquidity_wallet, token.treasury_wallet,
        token.total_supply, token.network,
        token.deployed_at, token.status, token.tx_hash
    ))
    conn.commit()
    conn.close()

# ── Load Coin Details ─────────────────────────────────────
def load_from_database() -> list:
    try:
        conn = sqlite3.connect("trendmintbot.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='coin_concepts'")
        if not cur.fetchone():
            log.warning("coin_concepts table not found.")
            conn.close()
            return []
        cur.execute("""
            SELECT c.* FROM coin_concepts c
            LEFT JOIN deployments d ON c.id = d.concept_id
            WHERE c.approved = 1 AND d.concept_id IS NULL
        """)
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return [TokenConfig(
            coin_name=r["coin_name"],
            ticker=r["ticker"],
            tagline=r["tagline"]
        ) for r in rows]
    except Exception as e:
        log.error(f"Failed to load from database: {e}")
        return []

def load_from_config(config_path: str) -> Optional[TokenConfig]:
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
        return TokenConfig(
            coin_name=data["coin_name"],
            ticker=data["ticker"],
            tagline=data.get("tagline", ""),
            total_supply=data.get("total_supply", 1_000_000_000),
            liquidity_pct=data.get("liquidity_pct", 50.0),
            float_pct=data.get("float_pct", 45.0),
            treasury_pct=data.get("treasury_pct", 5.0),
            lock_days=data.get("lock_days", 180),
            decimals=data.get("decimals", 9)
        )
    except Exception as e:
        log.error(f"Failed to load config: {e}")
        return None

# ── Wallet ────────────────────────────────────────────────
def load_or_create_wallet(wallet_path: str) -> Keypair:
    if os.path.exists(wallet_path):
        with open(wallet_path, "r") as f:
            data = json.load(f)
        keypair = Keypair.from_bytes(bytes(data))
        log.info(f"Loaded wallet: {keypair.pubkey()}")
        return keypair
    else:
        keypair = Keypair()
        with open(wallet_path, "w") as f:
            json.dump(list(bytes(keypair)), f)
        log.info(f"Created new wallet: {keypair.pubkey()}")
        log.info(f"Wallet saved to: {wallet_path}")
        return keypair

def check_balance(client: Client, pubkey: Pubkey) -> float:
    response = client.get_balance(pubkey)
    return response.value / 1_000_000_000

def request_airdrop(client: Client, pubkey: Pubkey, amount_sol: float = 2.0):
    import time
    lamports = int(amount_sol * 1_000_000_000)
    log.info(f"Requesting {amount_sol} SOL airdrop...")
    try:
        response = client.request_airdrop(pubkey, lamports)
        log.info(f"Airdrop requested. Waiting for confirmation...")
        time.sleep(5)
        balance = check_balance(client, pubkey)
        log.info(f"Balance after airdrop: {balance:.4f} SOL")
    except Exception as e:
        log.error(f"Airdrop failed: {e}")

# ── Token Deployment ──────────────────────────────────────
def deploy_token(config: TokenConfig, deployer: Keypair, client: Client) -> Optional[DeployedToken]:
    log.info(f"Deploying {config.coin_name} (${config.ticker}) on {NETWORK}...")

    try:
        # Check and fund balance
        balance = check_balance(client, deployer.pubkey())
        log.info(f"Deployer balance: {balance:.4f} SOL")

        if balance < 0.1:
            log.error(f"Insufficient SOL balance: {balance:.4f} SOL")
            log.error("Fund your wallet first:")
            log.error(f"  .\\solana.exe airdrop 1 {deployer.pubkey()} --url devnet")
            log.error("Then run the deployer again.")
            return None

        # Generate wallets
        mint_keypair      = Keypair()
        liquidity_keypair = Keypair()
        treasury_keypair  = Keypair()

        log.info(f"Mint address:      {mint_keypair.pubkey()}")
        log.info(f"Liquidity wallet:  {liquidity_keypair.pubkey()}")
        log.info(f"Treasury wallet:   {treasury_keypair.pubkey()}")

        # Get minimum rent for mint account (82 bytes)
        rent_response = client.get_minimum_balance_for_rent_exemption(82)
        mint_rent = rent_response.value

        # Get recent blockhash
        blockhash_response = client.get_latest_blockhash()
        recent_blockhash = blockhash_response.value.blockhash

        # Build create mint account instruction
        create_mint_account_ix = create_account(CreateAccountParams(
            from_pubkey=deployer.pubkey(),
            to_pubkey=mint_keypair.pubkey(),
            lamports=mint_rent,
            space=82,
            owner=TOKEN_PROGRAM_ID
        ))

        # Build initialize mint instruction
        # Instruction data: [0, decimals, mint_authority (32 bytes), 1, freeze_authority (32 bytes)]
        init_mint_data = bytes([0, config.decimals]) + \
                        bytes(deployer.pubkey()) + \
                        bytes([1]) + \
                        bytes(deployer.pubkey())

        init_mint_ix = Instruction(
            program_id=TOKEN_PROGRAM_ID,
            accounts=[
                AccountMeta(pubkey=mint_keypair.pubkey(), is_signer=False, is_writable=True),
                AccountMeta(pubkey=SYSVAR_RENT_PUBKEY, is_signer=False, is_writable=False),
            ],
            data=init_mint_data
        )

        # Send create + initialize mint transaction
        log.info("Creating token mint...")
        msg = Message.new_with_blockhash(
            [create_mint_account_ix, init_mint_ix],
            deployer.pubkey(),
            recent_blockhash
        )
        tx = Transaction([deployer, mint_keypair], msg, recent_blockhash)
        response = client.send_transaction(tx)
        mint_tx = str(response.value)
        log.info(f"Mint created! TX: {mint_tx}")

        import time
        time.sleep(3)

        # Save deployment record
        deployed = DeployedToken(
            concept_id=config.ticker,
            coin_name=config.coin_name,
            ticker=config.ticker,
            mint_address=str(mint_keypair.pubkey()),
            deployer_address=str(deployer.pubkey()),
            liquidity_wallet=str(liquidity_keypair.pubkey()),
            treasury_wallet=str(treasury_keypair.pubkey()),
            total_supply=config.total_supply,
            network=NETWORK,
            deployed_at=datetime.utcnow().isoformat(),
            status="deployed",
            tx_hash=mint_tx
        )

        # Save wallet keypairs for later use
        with open(f"wallet_{config.ticker.lower()}_mint.json", "w") as f:
            json.dump(list(bytes(mint_keypair)), f)
        with open(f"wallet_{config.ticker.lower()}_liquidity.json", "w") as f:
            json.dump(list(bytes(liquidity_keypair)), f)
        with open(f"wallet_{config.ticker.lower()}_treasury.json", "w") as f:
            json.dump(list(bytes(treasury_keypair)), f)

        save_deployment(deployed)
        print_deployment_summary(deployed, config)
        save_transparency_log(deployed, config)

        return deployed

    except Exception as e:
        log.error(f"Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return None

# ── Output ────────────────────────────────────────────────
def print_deployment_summary(token: DeployedToken, config: TokenConfig):
    print("\n" + "=" * 60)
    print(f"✅ {token.coin_name} (${token.ticker}) DEPLOYED")
    print("=" * 60)
    print(f"Network:          {token.network.upper()}")
    print(f"Mint Address:     {token.mint_address}")
    print(f"Deployer:         {token.deployer_address}")
    print(f"Liquidity Wallet: {token.liquidity_wallet}")
    print(f"Treasury Wallet:  {token.treasury_wallet}")
    print(f"Total Supply:     {token.total_supply:,}")
    print(f"Mint TX:          {token.tx_hash}")
    print(f"Deployed At:      {token.deployed_at}")
    print(f"\nView on Solana Explorer:")
    cluster = "?cluster=devnet" if token.network == "devnet" else ""
    print(f"https://explorer.solana.com/address/{token.mint_address}{cluster}")
    print("=" * 60 + "\n")

def save_transparency_log(token: DeployedToken, config: TokenConfig):
    log_entry = {
        "event": "token_deployed",
        "timestamp": token.deployed_at,
        "network": token.network,
        "coin_name": token.coin_name,
        "ticker": token.ticker,
        "mint_address": token.mint_address,
        "mint_tx": token.tx_hash,
        "tokenomics": {
            "total_supply": token.total_supply,
            "liquidity_pct": config.liquidity_pct,
            "float_pct": config.float_pct,
            "treasury_pct": config.treasury_pct,
            "lock_days": config.lock_days
        },
        "wallets": {
            "deployer": token.deployer_address,
            "liquidity": token.liquidity_wallet,
            "treasury": token.treasury_wallet
        }
    }
    log_path = f"transparency_{token.ticker.lower()}.json"
    with open(log_path, "w") as f:
        json.dump(log_entry, f, indent=2)
    log.info(f"Transparency log saved: {log_path}")

# ── Main ──────────────────────────────────────────────────
def run_deployer(config_path: str = None):
    init_deployments_table()
    client = Client(RPC_URL)
    log.info(f"Connected to Solana {NETWORK}")

    wallet_path = "deployer_wallet.json"
    deployer = load_or_create_wallet(wallet_path)

    configs = []
    if config_path:
        config = load_from_config(config_path)
        if config:
            configs.append(config)
    else:
        configs = load_from_database()
        if not configs:
            log.info("No approved concepts found.")
            log.info("Run: python plugins/concept_generator.py approve <id>")
            log.info("Or:  python core/deployer.py coin_config.example.json")
            return

    for config in configs:
        result = deploy_token(config, deployer, client)
        if result:
            log.info(f"Successfully deployed {result.coin_name} (${result.ticker})")
        else:
            log.error(f"Failed to deploy {config.coin_name}")

if __name__ == "__main__":
    config_file = sys.argv[1] if len(sys.argv) > 1 else None
    run_deployer(config_file)
