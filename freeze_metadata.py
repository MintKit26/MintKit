"""
MintKit — Freeze Token Metadata
Sets is_mutable to false so Phantom doesn't flag the token.
"""

import json
import struct
import logging
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.message import Message
from solders.instruction import Instruction, AccountMeta
from solana.rpc.api import Client
from solana.rpc.types import TxOpts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

MINT_ADDRESS        = "Hkwj68C2EtdwmcAohej9XLhowf3E9WPuVPsiTk5FAXAP"
RPC_URL             = "https://api.mainnet-beta.solana.com"
METADATA_PROGRAM_ID = Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")

def borsh_string(s):
    b = s.encode("utf-8")
    return struct.pack("<I", len(b)) + b

def get_metadata_pda(mint):
    seeds = [b"metadata", bytes(METADATA_PROGRAM_ID), bytes(mint)]
    pda, _ = Pubkey.find_program_address(seeds, METADATA_PROGRAM_ID)
    return pda

def main():
    client = Client(RPC_URL)
    with open("deployer_wallet.json") as f:
        deployer = Keypair.from_bytes(bytes(json.load(f)))

    log.info(f"Deployer: {deployer.pubkey()}")
    log.info(f"Balance:  {client.get_balance(deployer.pubkey()).value / 1e9:.4f} SOL")

    mint         = Pubkey.from_string(MINT_ADDRESS)
    metadata_pda = get_metadata_pda(mint)
    log.info(f"Metadata PDA: {metadata_pda}")

    # UpdateMetadataAccountV2 — discriminator 15
    # Set is_mutable = false
    data  = bytes([15])
    data += bytes([1])                           # Option<DataV2> = Some
    data += borsh_string("MintKit")              # name
    data += borsh_string("MKIT")                 # symbol
    data += borsh_string("https://raw.githubusercontent.com/MintKit26/MintKit/main/metadata/mkit.json")
    data += struct.pack("<H", 0)                 # seller_fee_basis_points
    data += bytes([0])                           # creators = None
    data += bytes([0])                           # collection = None
    data += bytes([0])                           # uses = None
    data += bytes([0])                           # new_update_authority = None
    data += bytes([0])                           # primary_sale_happened = None
    data += bytes([1, 0])                        # is_mutable = Some(false) ← KEY CHANGE

    accounts = [
        AccountMeta(pubkey=metadata_pda,    is_signer=False, is_writable=True),
        AccountMeta(pubkey=deployer.pubkey(), is_signer=True, is_writable=False),
    ]

    ix = Instruction(program_id=METADATA_PROGRAM_ID, accounts=accounts, data=data)
    blockhash = client.get_latest_blockhash().value.blockhash
    msg = Message.new_with_blockhash([ix], deployer.pubkey(), blockhash)
    tx  = Transaction([deployer], msg, blockhash)

    log.info("Freezing metadata...")
    try:
        result = client.send_transaction(tx, opts=TxOpts(skip_preflight=False))
        print(f"\n✅ Metadata frozen! is_mutable = false")
        print(f"   TX: {result.value}")
        print(f"   Phantom warning should be gone now!")
    except Exception as e:
        log.error(f"Failed: {e}")

if __name__ == "__main__":
    main()
