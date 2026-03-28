"""
MintKit — Setup Wizard
Walks new developers through first time setup step by step.
"""

import os
import sys
import json
import subprocess

def title(text):
    print(f"\n{'═' * 50}")
    print(f"  {text}")
    print(f"{'═' * 50}")

def step(n, text):
    print(f"\n── Step {n}: {text} ──────────────────────────")

def success(msg): print(f"  ✅ {msg}")
def error(msg):   print(f"  ❌ {msg}")
def info(msg):    print(f"  ℹ️  {msg}")
def ask(prompt):  return input(f"  → {prompt}: ").strip()

def check_dep(package):
    try:
        __import__(package)
        return True
    except ImportError:
        return False

print("""
╔═══════════════════════════════════════╗
║       MintKit Setup Wizard            ║
║   First time setup — let's go!        ║
╚═══════════════════════════════════════╝
""")

# ── Step 1 — Python version ───────────────────────────────
step(1, "Checking Python version")
v = sys.version_info
if v.major >= 3 and v.minor >= 11:
    success(f"Python {v.major}.{v.minor}.{v.micro} — good to go")
else:
    error(f"Python {v.major}.{v.minor} found — MintKit needs Python 3.11+")
    info("Download from python.org/downloads")
    sys.exit(1)

# ── Step 2 — Install dependencies ────────────────────────
step(2, "Installing dependencies")
packages = ["tweepy", "anthropic", "dotenv", "solana", "solders", "fastapi", "uvicorn", "schedule"]
missing = [p for p in packages if not check_dep(p.replace("-","_"))]

if missing:
    info(f"Installing: {', '.join(missing)}")
    subprocess.run([sys.executable, "-m", "pip", "install",
                   "tweepy", "anthropic", "python-dotenv",
                   "solana", "solders", "fastapi", "uvicorn",
                   "schedule", "anchorpy"], check=False)
    success("Dependencies installed")
else:
    success("All dependencies already installed")

# ── Step 3 — API Keys ─────────────────────────────────────
step(3, "API Keys setup")
print("\n  You'll need these keys:")
print("  • Anthropic API key — console.anthropic.com")
print("  • Twitter Bearer Token — developer.twitter.com")
print("  • Twitter Consumer Key, Secret, Access Token, Access Secret")
print()

anthropic_key    = ask("Paste your Anthropic API key (sk-ant-...)")
bearer_token     = ask("Paste your Twitter Bearer Token")
consumer_key     = ask("Paste your Twitter Consumer Key")
consumer_secret  = ask("Paste your Twitter Consumer Secret")
access_token     = ask("Paste your Twitter Access Token")
access_secret    = ask("Paste your Twitter Access Token Secret")
dashboard_pw     = ask("Choose a dashboard password")
network          = ask("Network — type 'devnet' for testing or 'mainnet' for real (devnet)") or "devnet"

# Write .env file
env_content = f"""ANTHROPIC_API_KEY={anthropic_key}
TWITTER_BEARER_TOKEN={bearer_token}
TWITTER_API_KEY={consumer_key}
TWITTER_API_SECRET={consumer_secret}
TWITTER_ACCESS_TOKEN={access_token}
TWITTER_ACCESS_SECRET={access_secret}
DASHBOARD_PASSWORD={dashboard_pw}
WALLET_PATH=./deployer_wallet.json
NETWORK={network}
"""

with open(".env", "w") as f:
    f.write(env_content)
success(".env file created")

# Also patch the scanner and generator directly
scanner_path   = os.path.join("plugins", "trend_scanner.py")
generator_path = os.path.join("plugins", "concept_generator.py")

if os.path.exists(scanner_path):
    with open(scanner_path, "r") as f:
        content = f.read()
    content = content.replace('os.environ["TWITTER_BEARER_TOKEN"] = "paste_your_bearer_token_here"',
                               f'os.environ["TWITTER_BEARER_TOKEN"] = "{bearer_token}"')
    content = content.replace('os.environ["ANTHROPIC_API_KEY"]    = "paste_your_anthropic_key_here"',
                               f'os.environ["ANTHROPIC_API_KEY"]    = "{anthropic_key}"')
    with open(scanner_path, "w") as f:
        f.write(content)
    success("trend_scanner.py updated with keys")

if os.path.exists(generator_path):
    with open(generator_path, "r") as f:
        content = f.read()
    content = content.replace('ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")',
                               f'ANTHROPIC_API_KEY = "{anthropic_key}"')
    with open(generator_path, "w") as f:
        f.write(content)
    success("concept_generator.py updated with keys")

# ── Step 4 — Create wallet ────────────────────────────────
step(4, "Setting up Solana wallet")
wallet_path = "deployer_wallet.json"

if os.path.exists(wallet_path):
    success(f"Wallet already exists: {wallet_path}")
else:
    try:
        from solders.keypair import Keypair
        kp = Keypair()
        with open(wallet_path, "w") as f:
            json.dump(list(bytes(kp)), f)
        success(f"Wallet created: {wallet_path}")
        info(f"Address: {kp.pubkey()}")
        if network == "devnet":
            info("Run 'python airdrop.py' to fund your wallet with free devnet SOL")
    except Exception as e:
        error(f"Could not create wallet: {e}")

# ── Step 5 — Verify project files ─────────────────────────
step(5, "Checking project files")
required = [
    "mintkit.py",
    "core/deployer.py",
    "core/promoter.py",
    "core/buyback.py",
    "core/transparency.py",
    "core/treasury.py",
    "plugins/trend_scanner.py",
    "plugins/concept_generator.py",
    "dashboard/server.py",
    "dashboard/frontend/index.html",
]
all_good = True
for f in required:
    if os.path.exists(f):
        success(f)
    else:
        error(f"{f} — missing!")
        all_good = False

# ── Step 6 — Run health check ─────────────────────────────
step(6, "Running health check")
try:
    from health import run_health_check
    run_health_check()
except Exception as e:
    info(f"Health check skipped: {e}")

# ── Done ──────────────────────────────────────────────────
title("Setup Complete!")

if all_good:
    print("""
  MintKit is ready to run!

  Quick start:
    python mintkit.py health          check everything is connected
    python mintkit.py scan            scan for trending memes
    python mintkit.py generate        generate coin concepts
    python mintkit.py status          view pipeline status

  Dashboard:
    cd dashboard && python server.py  start local dashboard
    open http://localhost:8000        view in browser
""")
else:
    print("""
  Some files are missing — make sure you extracted
  the full mintkit.zip before running setup.
""")
