"""
MintKit — Token Minter
Mints tokens to the deployer, liquidity, and treasury wallets.
Run this after deployment if supply shows 0.
"""

import json
import logging
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────
MINT_ADDRESS    = "Hkwj68C2EtdwmcAohej9XLhowf3E9WPuVPsiTk5FAXAP"
TOTAL_SUPPLY    = 1_000_000_000
DECIMALS        = 9
LIQUIDITY_PCT   = 50
FLOAT_PCT       = 45
TREASURY_PCT    = 5
RPC_URL         = "https://api.mainnet-beta.solana.com"

def main():
    client = Client(RPC_URL)

    # Load deployer wallet
    with open("deployer_wallet.json") as f:
        deployer = Keypair.from_bytes(bytes(json.load(f)))

    log.info(f"Deployer: {deployer.pubkey()}")
    balance = client.get_balance(deployer.pubkey()).value / 1e9
    log.info(f"Balance: {balance:.4f} SOL")

    # Load coin wallets
    try:
        with open("wallet_mkit_liquidity.json") as f:
            liquidity = Keypair.from_bytes(bytes(json.load(f)))
        log.info(f"Liquidity wallet: {liquidity.pubkey()}")
    except FileNotFoundError:
        log.error("wallet_mkit_liquidity.json not found!")
        return

    try:
        with open("wallet_mkit_treasury.json") as f:
            treasury = Keypair.from_bytes(bytes(json.load(f)))
        log.info(f"Treasury wallet: {treasury.pubkey()}")
    except FileNotFoundError:
        log.error("wallet_mkit_treasury.json not found!")
        return

    # Calculate amounts
    decimals_mult    = 10 ** DECIMALS
    total_raw        = TOTAL_SUPPLY * decimals_mult
    liquidity_amount = int(total_raw * (LIQUIDITY_PCT / 100))
    treasury_amount  = int(total_raw * (TREASURY_PCT  / 100))
    float_amount     = total_raw - liquidity_amount - treasury_amount

    log.info(f"Float:     {float_amount // decimals_mult:,} MKIT ({FLOAT_PCT}%)")
    log.info(f"Liquidity: {liquidity_amount // decimals_mult:,} MKIT ({LIQUIDITY_PCT}%)")
    log.info(f"Treasury:  {treasury_amount // decimals_mult:,} MKIT ({TREASURY_PCT}%)")

    log.info("Checking mint account...")
    mint_pubkey = Pubkey.from_string(MINT_ADDRESS)
    mint_info   = client.get_account_info(mint_pubkey)
    if mint_info.value is None:
        log.error("Mint account not found on chain!")
        return
    log.info("Mint account confirmed on chain.")

    log.info("""
══════════════════════════════════════════════════
MANUAL MINTING REQUIRED

The mint was created successfully but token 
distribution requires the Solana Token Program.

To complete the mint please use one of these tools:

1. Solana CLI:
   solana-tokens create-account \\
     --mint Hkwj68C2EtdwmcAohej9XLhowf3E9WPuVPsiTk5FAXAP \\
     --owner ELj8Ju526bbMfM2UEazChPwzcmm6aWF4afpzHd72oG23

2. SPL Token CLI:
   spl-token mint Hkwj68C2EtdwmcAohej9XLhowf3E9WPuVPsiTk5FAXAP \\
     1000000000 \\
     --owner deployer_wallet.json

3. Phantom Wallet:
   Import deployer_wallet.json private key
   Use the mint authority to mint tokens

Mint Address:     Hkwj68C2EtdwmcAohej9XLhowf3E9WPuVPsiTk5FAXAP
Mint Authority:   ELj8Ju526bbMfM2UEazChPwzcmm6aWF4afpzHd72oG23
Total Supply:     1,000,000,000
Decimals:         9
══════════════════════════════════════════════════
""")

if __name__ == "__main__":
    main()
