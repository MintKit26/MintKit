"""
MintKit — Auto Airdrop
Keeps trying the devnet airdrop every 30 seconds until it succeeds.
"""

import subprocess
import time
import sys

WALLET = "5BcJbhFvbSd3Ucxw7B4iqriAaN2Qfrw5hk4veEBJU4S8"
AMOUNT = "1"
INTERVAL = 30  # seconds between attempts

print(f"Auto airdrop started for {WALLET}")
print(f"Trying every {INTERVAL} seconds... (Ctrl+C to stop)\n")

attempt = 1
while True:
    print(f"Attempt {attempt}...", end=" ", flush=True)
    try:
        result = subprocess.run(
            ["solana", "airdrop", AMOUNT, WALLET, "--url", "devnet"],
            capture_output=True,
            text=True,
            timeout=15
        )
        output = result.stdout + result.stderr

        if "SOL" in output and "Error" not in output:
            print(f"SUCCESS! {output.strip()}")
            print("\nWallet funded! Run the deployer:")
            print("  python mintkit.py deploy coin_config.example.json")
            sys.exit(0)
        else:
            print(f"Failed — {output.strip()[:60]}")

    except subprocess.TimeoutExpired:
        print("Timed out")
    except FileNotFoundError:
        print("solana.exe not found — make sure solana.exe is in your mintkit folder")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")

    attempt += 1
    time.sleep(INTERVAL)
