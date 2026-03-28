"""
MintKit — CLI Interface
Clean command line interface for the entire MintKit pipeline.

Usage:
    python mintkit.py scan              # scan for trends
    python mintkit.py generate          # generate coin concepts
    python mintkit.py approve <id>      # approve a concept
    python mintkit.py reject <id>       # reject a concept
    python mintkit.py deploy            # deploy approved concepts
    python mintkit.py deploy <config>   # deploy from config file
    python mintkit.py promote           # promote unannounced deployments
    python mintkit.py buyback           # run buyback engine
    python mintkit.py report            # show all transparency reports
    python mintkit.py report <ticker>   # show report for specific coin
    python mintkit.py status            # show full pipeline status
"""

import sys
import os
import sqlite3
import json
from datetime import datetime

# ── Helpers ───────────────────────────────────────────────
def print_banner():
    print("""
╔═══════════════════════════════════════╗
║           MintKit v1.0                ║
║   Solana Token Launch Toolkit         ║
║   by JMHMsr                           ║
╚═══════════════════════════════════════╝
""")

def print_help():
    print("""
Commands:
  scan                  Scan X/Twitter for trending memes
  generate              Generate coin concepts from trends
  approve <id>          Approve a coin concept
  reject  <id>          Reject a coin concept
  deploy                Deploy all approved concepts
  deploy  <config.json> Deploy from a config file
  deploy  --base        Deploy on Base chain instead of Solana
  promote               Post launch announcements
  buyback               Run buyback engine
  treasury              Show treasury report
  images                Generate coin logo images
  report                Show all transparency reports
  report  <TICKER>      Show report for specific coin
  status                Show full pipeline status
  health                Test all API connections
  test                  Run automated test suite
  setup                 Run first time setup wizard

Examples:
  python mintkit.py scan
  python mintkit.py deploy coin_config.example.json
  python mintkit.py approve ac6c1f8078399740
  python mintkit.py report FADE
  python mintkit.py status
""")

def success(msg): print(f"  ✅ {msg}")
def error(msg):   print(f"  ❌ {msg}")
def info(msg):    print(f"  ℹ️  {msg}")
def warn(msg):    print(f"  ⚠️  {msg}")

# ── Status ────────────────────────────────────────────────
def cmd_status():
    """Show full pipeline status."""
    print("\n📊 MINTKIT PIPELINE STATUS")
    print("=" * 50)

    db_path = "mintkit.db"
    if not os.path.exists(db_path):
        warn("No database found. Run 'scan' or 'deploy' first.")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Trends
    try:
        cur.execute("SELECT COUNT(*) as count FROM meme_trends")
        trend_count = cur.fetchone()["count"]
        print(f"\n🔍 Trends Scanned:     {trend_count}")
    except:
        print(f"\n🔍 Trends Scanned:     0")

    # Concepts
    try:
        cur.execute("SELECT COUNT(*) as count FROM coin_concepts")
        concept_count = cur.fetchone()["count"]
        cur.execute("SELECT COUNT(*) as count FROM coin_concepts WHERE approved = 1")
        approved_count = cur.fetchone()["count"]
        print(f"💡 Concepts Generated: {concept_count} ({approved_count} approved)")
    except:
        print(f"💡 Concepts Generated: 0")

    # Deployments
    try:
        cur.execute("SELECT COUNT(*) as count FROM deployments")
        deploy_count = cur.fetchone()["count"]
        cur.execute("SELECT * FROM deployments")
        deployments = [dict(row) for row in cur.fetchall()]
        print(f"🚀 Tokens Deployed:    {deploy_count}")
        for d in deployments:
            network = d.get("network", "").upper()
            print(f"   • {d['coin_name']} (${d['ticker']}) — {network}")
            print(f"     Mint: {d['mint_address']}")
    except:
        print(f"🚀 Tokens Deployed:    0")

    # Promotions
    try:
        cur.execute("SELECT COUNT(*) as count FROM promotions")
        promo_count = cur.fetchone()["count"]
        print(f"📣 Promotions Posted:  {promo_count}")
    except:
        print(f"📣 Promotions Posted:  0")

    # Buybacks
    try:
        cur.execute("SELECT COUNT(*) as count FROM buybacks")
        buyback_count = cur.fetchone()["count"]
        cur.execute("SELECT SUM(tokens_burned) as total FROM buybacks")
        total_burned = cur.fetchone()["total"] or 0
        print(f"🔥 Buybacks Executed:  {buyback_count}")
        print(f"🔥 Total Burned:       {int(total_burned):,} tokens")
    except:
        print(f"🔥 Buybacks Executed:  0")

    conn.close()
    print("\n" + "=" * 50)
    print(f"Last checked: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n")

# ── Images ────────────────────────────────────────────────
def cmd_images():
    print("\n🎨 Running Image Generator...")
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from image_generator import run_image_generator
        run_image_generator()
    except ImportError as e:
        error(f"Could not load image generator: {e}")

# ── Test ──────────────────────────────────────────────────
def cmd_test():
    print("\n🧪 Running test suite...")
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        import tests
        tests.unittest.main(module=tests, argv=[""], exit=False, verbosity=2)
    except ImportError as e:
        error(f"Could not load tests: {e}")
        info("Make sure tests.py is in the root mintkit folder.")

# ── Setup ─────────────────────────────────────────────────
def cmd_setup():
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        import setup
    except ImportError as e:
        error(f"Could not load setup wizard: {e}")
        info("Make sure setup.py is in the root mintkit folder.")

# ── Base Deploy ───────────────────────────────────────────
def cmd_deploy_base(config_path: str = None):
    print("\n🔷 Preparing Base chain deployment...")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))
        from base_deployer import prepare_base_deployment, BaseTokenConfig
        import json
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                data = json.load(f)
            config = BaseTokenConfig(
                coin_name=data["coin_name"],
                ticker=data["ticker"],
                tagline=data.get("tagline", ""),
                total_supply=data.get("total_supply", 1_000_000_000),
            )
            prepare_base_deployment(config)
        else:
            error("Please provide a config file.")
            info("Usage: python mintkit.py deploy --base coin_config.json")
    except ImportError as e:
        error(f"Could not load base deployer: {e}")

# ── Health ────────────────────────────────────────────────
def cmd_health():
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from health import run_health_check
        run_health_check()
    except ImportError as e:
        error(f"Could not load health check: {e}")
        info("Make sure health.py is in the root mintkit folder.")

# ── Scan ──────────────────────────────────────────────────
def cmd_scan():
    print("\n🔍 Starting trend scan...")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "plugins"))
        from trend_scanner import run_scan
        results = run_scan()
        if results:
            success(f"Found {len(results)} viable trends.")
        else:
            info("No new viable trends found this cycle.")
    except ImportError as e:
        error(f"Could not load scanner: {e}")
        info("Make sure plugins/trend_scanner.py exists.")

# ── Generate ──────────────────────────────────────────────
def cmd_generate():
    print("\n💡 Generating coin concepts...")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "plugins"))
        from concept_generator import run_concept_generator
        run_concept_generator()
    except ImportError as e:
        error(f"Could not load generator: {e}")
        info("Make sure plugins/concept_generator.py exists.")

# ── Approve / Reject ──────────────────────────────────────
def cmd_approve(concept_id: str):
    print(f"\n✅ Approving concept: {concept_id}")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "plugins"))
        from concept_generator import approve_concept, init_concepts_table
        init_concepts_table()
        approve_concept(concept_id)
        success(f"Concept {concept_id} approved and ready for deployment.")
    except Exception as e:
        error(f"Approval failed: {e}")

def cmd_reject(concept_id: str):
    print(f"\n❌ Rejecting concept: {concept_id}")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "plugins"))
        from concept_generator import reject_concept, init_concepts_table
        init_concepts_table()
        reject_concept(concept_id)
        success(f"Concept {concept_id} rejected.")
    except Exception as e:
        error(f"Rejection failed: {e}")

# ── Deploy ────────────────────────────────────────────────
def cmd_deploy(config_path: str = None):
    if config_path:
        print(f"\n🚀 Deploying from config: {config_path}")
    else:
        print(f"\n🚀 Deploying approved concepts...")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))
        from deployer import run_deployer
        run_deployer(config_path)
    except ImportError as e:
        error(f"Could not load deployer: {e}")
        info("Make sure core/deployer.py exists.")

# ── Promote ───────────────────────────────────────────────
def cmd_promote():
    print("\n📣 Running promotion bot...")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))
        from promoter import run_promoter
        run_promoter()
    except ImportError as e:
        error(f"Could not load promoter: {e}")
        info("Make sure core/promoter.py exists.")

# ── Treasury ──────────────────────────────────────────────
def cmd_treasury():
    print("\n💰 Running Treasury Manager...")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))
        from treasury import run_treasury_manager
        run_treasury_manager()
    except ImportError as e:
        error(f"Could not load treasury manager: {e}")
        info("Make sure core/treasury.py exists.")

# ── Buyback ───────────────────────────────────────────────
def cmd_buyback():
    print("\n🔄 Running buyback engine...")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))
        from buyback import run_buyback_engine
        run_buyback_engine()
    except ImportError as e:
        error(f"Could not load buyback engine: {e}")
        info("Make sure core/buyback.py exists.")

# ── Report ────────────────────────────────────────────────
def cmd_report(ticker: str = None):
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))
        from transparency import generate_report, generate_all_reports, sync_from_database
        sync_from_database()
        if ticker:
            generate_report(ticker.upper())
        else:
            generate_all_reports()
    except ImportError as e:
        error(f"Could not load transparency module: {e}")
        info("Make sure core/transparency.py exists.")

# ── Entry Point ───────────────────────────────────────────
def main():
    print_banner()

    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1].lower()

    if command == "health":
        cmd_health()

    elif command == "scan":
        cmd_scan()

    elif command == "generate":
        cmd_generate()

    elif command == "approve":
        if len(sys.argv) < 3:
            error("Please provide a concept ID.")
            info("Usage: python mintkit.py approve <id>")
        else:
            cmd_approve(sys.argv[2])

    elif command == "reject":
        if len(sys.argv) < 3:
            error("Please provide a concept ID.")
            info("Usage: python mintkit.py reject <id>")
        else:
            cmd_reject(sys.argv[2])

    elif command == "deploy":
        if len(sys.argv) > 2 and sys.argv[2] == "--base":
            config = sys.argv[3] if len(sys.argv) > 3 else None
            cmd_deploy_base(config)
        else:
            config = sys.argv[2] if len(sys.argv) > 2 else None
            cmd_deploy(config)

    elif command == "promote":
        cmd_promote()

    elif command == "treasury":
        cmd_treasury()

    elif command == "buyback":
        cmd_buyback()

    elif command == "report":
        ticker = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_report(ticker)

    elif command == "status":
        cmd_status()

    elif command == "images":
        cmd_images()

    elif command == "test":
        cmd_test()

    elif command == "setup":
        cmd_setup()

    elif command in ["help", "--help", "-h"]:
        print_help()

    else:
        error(f"Unknown command: {command}")
        print_help()

if __name__ == "__main__":
    main()
