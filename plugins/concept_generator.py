"""
MintKit — Add Token Metadata (Fixed)
Uses correct Borsh encoding for Metaplex CreateMetadataAccountV3.
"""

import json
import struct
import logging
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.message import Message
from solders.instruction import Instruction, AccountMeta
from solders.system_program import ID as SYSTEM_PROGRAM_ID
from solana.rpc.api import Client
from solana.rpc.types import TxOpts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

MINT_ADDRESS        = "Hkwj68C2EtdwmcAohej9XLhowf3E9WPuVPsiTk5FAXAP"
TOKEN_NAME          = "MintKit"
TOKEN_SYMBOL        = "MKIT"
TOKEN_URI           = "https://raw.githubusercontent.com/MintKit26/MintKit/main/metadata/mkit.json"
RPC_URL             = "https://api.mainnet-beta.solana.com"
METADATA_PROGRAM_ID = Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")
SYSVAR_RENT         = Pubkey.from_string("SysvarRent111111111111111111111111111111111")

def borsh_string(s: str) -> bytes:
    b = s.encode("utf-8")
    return struct.pack("<I", len(b)) + b

def get_metadata_pda(mint: Pubkey) -> Pubkey:
    seeds = [b"metadata", bytes(METADATA_PROGRAM_ID), bytes(mint)]
    pda, _ = Pubkey.find_program_address(seeds, METADATA_PROGRAM_ID)
    return pda

def build_ix(metadata_pda, mint, mint_authority, payer, update_authority, name, symbol, uri):
    data  = bytes([33])
    data += borsh_string(name)
    data += borsh_string(symbol)
    data += borsh_string(uri)
    data += struct.pack("<H", 0)
    data += bytes([0])
    data += bytes([0])
    data += bytes([0])
    data += bytes([1])
    data += bytes([0])

    accounts = [
        AccountMeta(pubkey=metadata_pda,     is_signer=False, is_writable=True),
        AccountMeta(pubkey=mint,              is_signer=False, is_writable=False),
        AccountMeta(pubkey=mint_authority,    is_signer=True,  is_writable=False),
        AccountMeta(pubkey=payer,             is_signer=True,  is_writable=True),
        AccountMeta(pubkey=update_authority,  is_signer=False, is_writable=False),
        AccountMeta(pubkey=SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=SYSVAR_RENT,       is_signer=False, is_writable=False),
    ]
    return Instruction(program_id=METADATA_PROGRAM_ID, accounts=accounts, data=data)

def main():
    client = Client(RPC_URL)

    with open("deployer_wallet.json") as f:
        deployer = Keypair.from_bytes(bytes(json.load(f)))

    log.info(f"Deployer: {deployer.pubkey()}")
    log.info(f"Balance:  {client.get_balance(deployer.pubkey()).value / 1e9:.4f} SOL")

    mint         = Pubkey.from_string(MINT_ADDRESS)
    metadata_pda = get_metadata_pda(mint)
    log.info(f"Metadata PDA: {metadata_pda}")

    info = client.get_account_info(metadata_pda)
    if info.value is not None:
        log.info("Metadata already exists!")
        return

    ix = build_ix(
        metadata_pda=metadata_pda,
        mint=mint,
        mint_authority=deployer.pubkey(),
        payer=deployer.pubkey(),
        update_authority=deployer.pubkey(),
        name=TOKEN_NAME,
        symbol=TOKEN_SYMBOL,
        uri=TOKEN_URI,
    )

    blockhash = client.get_latest_blockhash().value.blockhash
    msg = Message.new_with_blockhash([ix], deployer.pubkey(), blockhash)
    tx  = Transaction([deployer], msg, blockhash)

    log.info("Sending transaction...")
    try:
        result = client.send_transaction(tx, opts=TxOpts(skip_preflight=False))
        print(f"\n✅ Metadata added successfully!")
        print(f"   Name:     {TOKEN_NAME}")
        print(f"   Symbol:   {TOKEN_SYMBOL}")
        print(f"   TX:       {result.value}")
        print(f"   Explorer: https://explorer.solana.com/tx/{result.value}")
    except Exception as e:
        log.error(f"Failed: {e}")

if __name__ == "__main__":
    main()
