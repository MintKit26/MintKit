"""
MintKit — Update Token Metadata
Updates existing $MKIT metadata with correct image URL.
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
TOKEN_NAME          = "MintKit"
TOKEN_SYMBOL        = "MKIT"
TOKEN_URI           = "https://raw.githubusercontent.com/MintKit26/MintKit/main/metadata/mkit.json"
RPC_URL             = "https://api.mainnet-beta.solana.com"
METADATA_PROGRAM_ID = Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")

def borsh_string(s: str) -> bytes:
    b = s.encode("utf-8")
    return struct.pack("<I", len(b)) + b

def borsh_option_string(s: str) -> bytes:
    return bytes([1]) + borsh_string(s)

def get_metadata_pda(mint: Pubkey) -> Pubkey:
    seeds = [b"metadata", bytes(METADATA_PROGRAM_ID), bytes(mint)]
    pda, _ = Pubkey.find_program_address(seeds, METADATA_PROGRAM_ID)
    return pda

def build_update_ix(metadata_pda, mint, update_authority, name, symbol, uri):
    # UpdateMetadataAccountV2 discriminator = 15
    data  = bytes([15])
    # Option<DataV2> = Some(1)
    data += bytes([1])
    data += borsh_string(name)
    data += borsh_string(symbol)
    data += borsh_string(uri)
    data += struct.pack("<H", 0)  # seller_fee_basis_points
    data += bytes([0])             # creators = None
    data += bytes([0])             # collection = None
    data += bytes([0])             # uses = None
    # Option<Pubkey> new_update_authority = None
    data += bytes([0])
    # Option<bool> primary_sale_happened = None
    data += bytes([0])
    # Option<bool> is_mutable = Some(true)
    data += bytes([1, 1])

    accounts = [
        AccountMeta(pubkey=metadata_pda,    is_signer=False, is_writable=True),
        AccountMeta(pubkey=update_authority, is_signer=True,  is_writable=False),
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

    ix = build_update_ix(
        metadata_pda=metadata_pda,
        mint=mint,
        update_authority=deployer.pubkey(),
        name=TOKEN_NAME,
        symbol=TOKEN_SYMBOL,
        uri=TOKEN_URI,
    )

    blockhash = client.get_latest_blockhash().value.blockhash
    msg = Message.new_with_blockhash([ix], deployer.pubkey(), blockhash)
    tx  = Transaction([deployer], msg, blockhash)

    log.info("Updating metadata...")
    try:
        result = client.send_transaction(tx, opts=TxOpts(skip_preflight=False))
        print(f"\n✅ Metadata updated!")
        print(f"   Name:     {TOKEN_NAME}")
        print(f"   Symbol:   {TOKEN_SYMBOL}")
        print(f"   URI:      {TOKEN_URI}")
        print(f"   TX:       {result.value}")
        print(f"   Explorer: https://explorer.solana.com/tx/{result.value}")
    except Exception as e:
        log.error(f"Failed: {e}")

if __name__ == "__main__":
    main()
