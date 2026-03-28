"""
MintKit — Health Check
Tests all API connections and dependencies at once.
Run this after rekeying or setting up on a new machine.
"""

import os
import sys
import json
import sqlite3
import subprocess
from datetime import datetime

# ── Results tracker ───────────────────────────────────────
results = []

def check(name, fn):
    try:
        msg = fn()
        results.append(("pass", name, msg))
        print(f"  ✅ {name}: {msg}")
    except Exception as e:
        results.append(("fail", name, str(e)))
        print(f"  ❌ {name}: {str(e)[:80]}")

# ── Individual checks ─────────────────────────────────────
def check_python():
    v = sys.version_info
    if v.major < 3 or v.minor < 11:
        raise Exception(f"Python {v.major}.{v.minor} — needs 3.11+")
    return f"Python {v.major}.{v.minor}.{v.micro}"

def check_tweepy():
    import tweepy
    return f"tweepy {tweepy.__version__}"

def check_anthropic():
    import anthropic
    return f"anthropic {anthropic.__version__}"

def check_solana():
    import solana
    return "solana installed"

def check_solders():
    import solders
    return f"solders installed"

def check_fastapi():
    import fastapi
    return f"fastapi {fastapi.__version__}"

def check_dotenv():
    from dotenv import load_dotenv
    return "python-dotenv installed"

def check_schedule():
    import schedule
    return f"schedule installed"

def check_twitter_key():
    # Check environment first
    key = os.environ.get("TWITTER_BEARER_TOKEN", "")
    if key and "paste" not in key.lower():
        return f"set in environment ({key[:12]}...)"
    # Check scanner file
    scanner_path = os.path.join("plugins", "trend_scanner.py")
    if os.path.exists(scanner_path):
        with open(scanner_path) as f:
            content = f.read()
        import re
        match = re.search(r'TWITTER_BEARER_TOKEN"\]\s*=\s*"([^"]+)"', content)
        if match and "paste" not in match.group(1).lower():
            key = match.group(1)
            os.environ["TWITTER_BEARER_TOKEN"] = key
            return f"set in scanner ({key[:12]}...)"
    raise Exception("Not set — run setup.py or add to plugins/trend_scanner.py")

def check_anthropic_key():
    # Check environment first
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key and "paste" not in key.lower():
        return f"set in environment ({key[:12]}...)"
    # Check generator file
    generator_path = os.path.join("plugins", "concept_generator.py")
    if os.path.exists(generator_path):
        with open(generator_path) as f:
            content = f.read()
        import re
        match = re.search(r'ANTHROPIC_API_KEY\s*=\s*"([^"]+)"', content)
        if match and "paste" not in match.group(1).lower():
            key = match.group(1)
            os.environ["ANTHROPIC_API_KEY"] = key
            return f"set in generator ({key[:12]}...)"
    raise Exception("Not set — run setup.py or add to plugins/concept_generator.py")

def check_twitter_connection():
    import tweepy
    key = os.environ.get("TWITTER_BEARER_TOKEN", "")
    if not key:
        raise Exception("No bearer token")
    client = tweepy.Client(bearer_token=key, wait_on_rate_limit=False)
    res = client.search_recent_tweets(query="test lang:en", max_results=10)
    return "connected"

def check_anthropic_connection():
    import anthropic
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise Exception("No API key")
    client = anthropic.Anthropic(api_key=key)
    res = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=10,
        messages=[{"role": "user", "content": "Hi"}]
    )
    return "connected"

def check_solana_connection():
    from solana.rpc.api import Client
    client = Client("https://api.devnet.solana.com")
    res = client.get_latest_blockhash()
    return "devnet reachable"

def check_solana_cli():
    result = subprocess.run(
        ["solana", "--version"],
        capture_output=True, text=True, timeout=5
    )
    if result.returncode != 0:
        raise Exception("solana CLI not found")
    return result.stdout.strip()

def check_wallet():
    wallet_path = "deployer_wallet.json"
    if not os.path.exists(wallet_path):
        raise Exception(f"{wallet_path} not found — run deployer once to create it")
    with open(wallet_path) as f:
        data = json.load(f)
    from solders.keypair import Keypair
    kp = Keypair.from_bytes(bytes(data))
    return f"{str(kp.pubkey())[:20]}..."

def check_wallet_balance():
    from solana.rpc.api import Client
    from solders.keypair import Keypair
    import json
    wallet_path = "deployer_wallet.json"
    if not os.path.exists(wallet_path):
        raise Exception("wallet not found")
    with open(wallet_path) as f:
        data = json.load(f)
    kp = Keypair.from_bytes(bytes(data))
    client = Client("https://api.devnet.solana.com")
    res = client.get_balance(kp.pubkey())
    sol = res.value / 1_000_000_000
    if sol < 0.1:
        raise Exception(f"{sol:.4f} SOL — too low, run airdrop.py")
    return f"{sol:.4f} SOL"

def check_database():
    db_path = "mintkit.db"
    if not os.path.exists(db_path):
        return "not created yet — will be created on first run"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    conn.close()
    return f"found — tables: {', '.join(tables) or 'none'}"

def check_core_files():
    required = [
        "core/deployer.py",
        "core/promoter.py",
        "core/buyback.py",
        "core/transparency.py",
        "core/treasury.py",
    ]
    missing = [f for f in required if not os.path.exists(f)]
    if missing:
        raise Exception(f"Missing: {', '.join(missing)}")
    return f"all {len(required)} files present"

def check_plugin_files():
    required = [
        "plugins/trend_scanner.py",
        "plugins/concept_generator.py",
    ]
    missing = [f for f in required if not os.path.exists(f)]
    if missing:
        raise Exception(f"Missing: {', '.join(missing)}")
    return f"all {len(required)} files present"

def check_dashboard_files():
    required = [
        "dashboard/server.py",
        "dashboard/frontend/index.html",
    ]
    missing = [f for f in required if not os.path.exists(f)]
    if missing:
        raise Exception(f"Missing: {', '.join(missing)}")
    return f"all {len(required)} files present"

# ── Main ──────────────────────────────────────────────────
def run_health_check():
    print("""
╔═══════════════════════════════════════╗
║         MintKit Health Check          ║
╚═══════════════════════════════════════╝
""")
    print(f"Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    print("── Python & Dependencies ─────────────────")
    check("Python version",   check_python)
    check("tweepy",           check_tweepy)
    check("anthropic",        check_anthropic)
    check("solana",           check_solana)
    check("solders",          check_solders)
    check("fastapi",          check_fastapi)
    check("python-dotenv",    check_dotenv)
    check("schedule",         check_schedule)

    print("\n── API Keys ──────────────────────────────")
    check("Twitter Bearer Token",  check_twitter_key)
    check("Anthropic API Key",     check_anthropic_key)

    print("\n── API Connections ───────────────────────")
    check("Twitter connection",    check_twitter_connection)
    check("Anthropic connection",  check_anthropic_connection)
    check("Solana devnet",         check_solana_connection)
    check("Solana CLI",            check_solana_cli)

    print("\n── Wallet ────────────────────────────────")
    check("Deployer wallet",       check_wallet)
    check("Wallet balance",        check_wallet_balance)

    print("\n── Database ──────────────────────────────")
    check("mintkit.db",            check_database)

    print("\n── Project Files ─────────────────────────")
    check("Core modules",          check_core_files)
    check("Plugins",               check_plugin_files)
    check("Dashboard",             check_dashboard_files)

    # Summary
    passed = sum(1 for r in results if r[0] == "pass")
    failed = sum(1 for r in results if r[0] == "fail")
    total  = len(results)

    print(f"\n{'═' * 42}")
    print(f"Results: {passed}/{total} passed", end="")
    if failed:
        print(f" — {failed} failed")
        print("\nFailed checks:")
        for r in results:
            if r[0] == "fail":
                print(f"  ❌ {r[1]}: {r[2]}")
    else:
        print(" — all good!")
        print("\nMintKit is fully connected and ready to run.")
    print(f"{'═' * 42}\n")

if __name__ == "__main__":
    run_health_check()
