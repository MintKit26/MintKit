"""
MintKit — Base Chain Support
Deploy tokens on Base (Coinbase L2) as a cheaper alternative to Solana.
Base has near-zero fees and a large meme coin community.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Networks ──────────────────────────────────────────────
NETWORKS = {
    "base_mainnet": {
        "rpc": "https://mainnet.base.org",
        "chain_id": 8453,
        "name": "Base Mainnet",
        "explorer": "https://basescan.org"
    },
    "base_testnet": {
        "rpc": "https://sepolia.base.org",
        "chain_id": 84532,
        "name": "Base Sepolia Testnet",
        "explorer": "https://sepolia.basescan.org"
    }
}

NETWORK = os.getenv("BASE_NETWORK", "base_testnet")

# ── ERC-20 Token ABI (minimal) ────────────────────────────
ERC20_ABI = [
    {
        "inputs": [
            {"name": "name", "type": "string"},
            {"name": "symbol", "type": "string"},
            {"name": "totalSupply", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# ── Simple ERC-20 Bytecode template ──────────────────────
# This is a minimal ERC-20 token contract for deployment
# In production use OpenZeppelin contracts via Foundry or Hardhat
ERC20_BYTECODE_NOTE = """
For production Base deployment use one of these approaches:

1. Foundry (recommended):
   forge create --rpc-url https://mainnet.base.org \\
     --private-key $PRIVATE_KEY \\
     src/MintKitToken.sol:MintKitToken \\
     --constructor-args "Coin Name" "TICKER" 1000000000

2. Hardhat:
   npx hardhat run scripts/deploy.js --network base

3. Remix IDE:
   - Open remix.ethereum.org
   - Paste the contract
   - Deploy to Base network via MetaMask

See docs/BASE_DEPLOY.md for full instructions.
"""

@dataclass
class BaseTokenConfig:
    coin_name: str
    ticker: str
    tagline: str
    total_supply: int      = 1_000_000_000
    liquidity_pct: float   = 50.0
    float_pct: float       = 45.0
    treasury_pct: float    = 5.0
    decimals: int          = 18    # ERC-20 standard is 18

@dataclass
class BaseDeployedToken:
    coin_name: str
    ticker: str
    contract_address: str
    deployer_address: str
    liquidity_wallet: str
    treasury_wallet: str
    total_supply: int
    network: str
    deployed_at: str
    tx_hash: str
    explorer_url: str

def get_solidity_contract(config: BaseTokenConfig) -> str:
    """Generate a Solidity ERC-20 contract for the token."""
    total_supply_wei = config.total_supply * (10 ** config.decimals)
    return f"""// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title {config.coin_name}
 * @dev {config.tagline}
 * Deployed by MintKit — transparent, automated token launch toolkit
 * by JMHMsr — github.com/JMHMsr/mintkit
 */
contract {config.ticker} is ERC20, Ownable {{

    uint256 public constant TOTAL_SUPPLY = {total_supply_wei};

    // Wallet allocations
    address public liquidityWallet;
    address public treasuryWallet;

    // Tokenomics
    uint256 public constant LIQUIDITY_PCT = {int(config.liquidity_pct)};
    uint256 public constant FLOAT_PCT     = {int(config.float_pct)};
    uint256 public constant TREASURY_PCT  = {int(config.treasury_pct)};

    // Mint authority permanently renounced after deploy
    bool public mintingComplete = false;

    event TokensDistributed(
        address indexed floatWallet,
        address indexed liquidityWallet,
        address indexed treasuryWallet,
        uint256 floatAmount,
        uint256 liquidityAmount,
        uint256 treasuryAmount
    );

    constructor(
        address _liquidityWallet,
        address _treasuryWallet
    ) ERC20("{config.coin_name}", "{config.ticker}") Ownable(msg.sender) {{
        require(_liquidityWallet != address(0), "Invalid liquidity wallet");
        require(_treasuryWallet  != address(0), "Invalid treasury wallet");

        liquidityWallet = _liquidityWallet;
        treasuryWallet  = _treasuryWallet;

        uint256 floatAmount     = TOTAL_SUPPLY * FLOAT_PCT     / 100;
        uint256 liquidityAmount = TOTAL_SUPPLY * LIQUIDITY_PCT / 100;
        uint256 treasuryAmount  = TOTAL_SUPPLY - floatAmount - liquidityAmount;

        // Mint to each wallet
        _mint(msg.sender,       floatAmount);
        _mint(_liquidityWallet, liquidityAmount);
        _mint(_treasuryWallet,  treasuryAmount);

        mintingComplete = true;

        emit TokensDistributed(
            msg.sender,
            _liquidityWallet,
            _treasuryWallet,
            floatAmount,
            liquidityAmount,
            treasuryAmount
        );
    }}

    /**
     * @dev Minting is permanently disabled after deployment.
     * Supply is fixed forever.
     */
    function _update(address from, address to, uint256 value) internal override {{
        if (from == address(0) && mintingComplete) {{
            revert("Minting permanently disabled");
        }}
        super._update(from, to, value);
    }}
}}
"""

def generate_deploy_script(config: BaseTokenConfig, network_key: str) -> str:
    """Generate a Foundry deployment script."""
    network = NETWORKS.get(network_key, NETWORKS["base_testnet"])
    return f"""#!/bin/bash
# MintKit — Base Chain Deployment Script
# Generated for: {config.coin_name} (${config.ticker})
# Network: {network['name']}

# Make sure you have Foundry installed: https://getfoundry.sh

# Set your private key (never commit this!)
export PRIVATE_KEY="your_private_key_here"

# Deploy the contract
forge create \\
  --rpc-url {network['rpc']} \\
  --private-key $PRIVATE_KEY \\
  src/{config.ticker}.sol:{config.ticker} \\
  --constructor-args \\
    "your_liquidity_wallet_address" \\
    "your_treasury_wallet_address" \\
  --verify \\
  --etherscan-api-key your_basescan_api_key

# After deployment, note the contract address and verify on:
# {network['explorer']}
"""

def save_contract_files(config: BaseTokenConfig):
    """Save the Solidity contract and deploy script to disk."""
    os.makedirs("contracts", exist_ok=True)
    os.makedirs("scripts", exist_ok=True)

    # Save contract
    contract_path = f"contracts/{config.ticker}.sol"
    with open(contract_path, "w") as f:
        f.write(get_solidity_contract(config))
    log.info(f"Contract saved: {contract_path}")

    # Save deploy script
    script_path = f"scripts/deploy_{config.ticker.lower()}.sh"
    with open(script_path, "w") as f:
        f.write(generate_deploy_script(config, NETWORK))
    os.chmod(script_path, 0o755)
    log.info(f"Deploy script saved: {script_path}")

    print(f"\n{'=' * 55}")
    print(f"Base Chain Files Generated for ${config.ticker}")
    print(f"{'=' * 55}")
    print(f"Contract:      {contract_path}")
    print(f"Deploy script: {script_path}")
    print(f"\nNext steps:")
    print(f"  1. Install Foundry: curl -L https://foundry.paradigm.xyz | bash")
    print(f"  2. Run: bash {script_path}")
    print(f"  3. Verify on: {NETWORKS[NETWORK]['explorer']}")
    print(f"{'=' * 55}\n")

def prepare_base_deployment(config: BaseTokenConfig):
    """
    Prepare everything needed for a Base chain deployment.
    Generates contract files and deployment scripts.
    Full deployment requires Foundry or Hardhat.
    """
    log.info(f"Preparing Base deployment for {config.coin_name} (${config.ticker})")
    log.info(f"Network: {NETWORKS[NETWORK]['name']}")
    log.info(f"Total supply: {config.total_supply:,}")
    log.info(f"Tokenomics: {config.liquidity_pct}% liq | {config.float_pct}% float | {config.treasury_pct}% treasury")
    save_contract_files(config)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        with open(config_path) as f:
            data = json.load(f)
        config = BaseTokenConfig(
            coin_name=data["coin_name"],
            ticker=data["ticker"],
            tagline=data.get("tagline", ""),
            total_supply=data.get("total_supply", 1_000_000_000),
            liquidity_pct=data.get("liquidity_pct", 50.0),
            float_pct=data.get("float_pct", 45.0),
            treasury_pct=data.get("treasury_pct", 5.0),
        )
        prepare_base_deployment(config)
    else:
        print("Usage: python base_deployer.py coin_config.json")
