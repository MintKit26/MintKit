"""
MintKit — Test Suite
Automated tests for all core modules.
Run on devnet only — never on mainnet.
"""

import os
import sys
import json
import sqlite3
import unittest
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Base test setup ───────────────────────────────────────
class MintKitTestCase(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path  = os.path.join(self.test_dir, "test.db")
        os.environ["DB_PATH"] = self.db_path

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

# ── Database Tests ────────────────────────────────────────
class TestDatabase(MintKitTestCase):

    def test_deployer_creates_table(self):
        sys.path.insert(0, "core")
        from deployer import init_deployments_table
        with patch("deployer.DB_PATH", self.db_path):
            init_deployments_table()
        conn = self.get_db()
        cur  = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deployments'")
        self.assertIsNotNone(cur.fetchone())
        conn.close()

    def test_save_and_retrieve_deployment(self):
        sys.path.insert(0, "core")
        from deployer import init_deployments_table, save_deployment, DeployedToken
        with patch("deployer.DB_PATH", self.db_path):
            init_deployments_table()
            token = DeployedToken(
                concept_id="TEST",
                coin_name="Test Coin",
                ticker="TEST",
                mint_address="mint123",
                deployer_address="deployer123",
                liquidity_wallet="liq123",
                treasury_wallet="treas123",
                total_supply=1_000_000_000,
                network="devnet",
                deployed_at=datetime.utcnow().isoformat(),
                status="deployed",
                tx_hash="tx123"
            )
            save_deployment(token)

        conn = self.get_db()
        cur  = conn.cursor()
        cur.execute("SELECT * FROM deployments WHERE concept_id = 'TEST'")
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["coin_name"], "Test Coin")
        self.assertEqual(row["ticker"], "TEST")
        conn.close()

# ── Config Tests ──────────────────────────────────────────
class TestConfig(MintKitTestCase):

    def test_load_valid_config(self):
        sys.path.insert(0, "core")
        from deployer import load_from_config
        config_path = os.path.join(self.test_dir, "test_config.json")
        config_data = {
            "coin_name": "Test Coin",
            "ticker": "TEST",
            "tagline": "A test coin",
            "total_supply": 1000000000,
            "liquidity_pct": 50,
            "float_pct": 45,
            "treasury_pct": 5,
            "lock_days": 180
        }
        with open(config_path, "w") as f:
            json.dump(config_data, f)

        config = load_from_config(config_path)
        self.assertIsNotNone(config)
        self.assertEqual(config.coin_name, "Test Coin")
        self.assertEqual(config.ticker, "TEST")
        self.assertEqual(config.total_supply, 1000000000)

    def test_load_missing_config(self):
        sys.path.insert(0, "core")
        from deployer import load_from_config
        config = load_from_config("nonexistent.json")
        self.assertIsNone(config)

    def test_load_incomplete_config(self):
        sys.path.insert(0, "core")
        from deployer import load_from_config
        config_path = os.path.join(self.test_dir, "bad_config.json")
        with open(config_path, "w") as f:
            json.dump({"coin_name": "Only Name"}, f)
        config = load_from_config(config_path)
        self.assertIsNone(config)

# ── Transparency Tests ────────────────────────────────────
class TestTransparency(MintKitTestCase):

    def test_log_deployment(self):
        sys.path.insert(0, "core")
        import transparency
        transparency.LOG_DIR = os.path.join(self.test_dir, "logs")
        transparency.DB_PATH = self.db_path

        deployment = {
            "coin_name": "Test Coin",
            "ticker": "TEST",
            "mint_address": "mint123",
            "tx_hash": "tx123",
            "network": "devnet",
            "total_supply": 1000000000,
            "deployed_at": datetime.utcnow().isoformat(),
            "deployer_address": "dep123",
            "liquidity_wallet": "liq123",
            "treasury_wallet": "treas123"
        }
        transparency.log_deployment(deployment)

        log_path = os.path.join(self.test_dir, "logs", "test_log.json")
        self.assertTrue(os.path.exists(log_path))
        with open(log_path) as f:
            data = json.load(f)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["event"], "token_deployed")

    def test_append_multiple_entries(self):
        sys.path.insert(0, "core")
        import transparency
        transparency.LOG_DIR = os.path.join(self.test_dir, "logs")
        transparency.DB_PATH = self.db_path

        transparency.append_log("TEST", {"event": "first"})
        transparency.append_log("TEST", {"event": "second"})

        log = transparency.get_log("TEST")
        self.assertEqual(len(log), 2)
        self.assertEqual(log[0]["event"], "first")
        self.assertEqual(log[1]["event"], "second")

# ── Tokenomics Tests ──────────────────────────────────────
class TestTokenomics(MintKitTestCase):

    def test_supply_splits_correctly(self):
        total      = 1_000_000_000
        liq_pct    = 50
        float_pct  = 45
        treas_pct  = 5

        liq_amount   = int(total * (liq_pct / 100))
        float_amount = int(total * (float_pct / 100))
        treas_amount = int(total * (treas_pct / 100))

        self.assertEqual(liq_amount,   500_000_000)
        self.assertEqual(float_amount, 450_000_000)
        self.assertEqual(treas_amount,  50_000_000)
        self.assertEqual(liq_amount + float_amount + treas_amount, total)

    def test_buyback_split(self):
        total_bought    = 1_000_000
        burn_pct        = 50
        airdrop_pct     = 50

        to_burn         = int(total_bought * (burn_pct / 100))
        to_airdrop      = total_bought - to_burn

        self.assertEqual(to_burn,    500_000)
        self.assertEqual(to_airdrop, 500_000)
        self.assertEqual(to_burn + to_airdrop, total_bought)

    def test_ticker_validation(self):
        raw_ticker = "  fade! "
        clean = "".join(c for c in raw_ticker.upper() if c.isalpha())[:6]
        self.assertEqual(clean, "FADE")

    def test_ticker_max_length(self):
        raw_ticker = "TOOLONGTICKER"
        clean = "".join(c for c in raw_ticker.upper() if c.isalpha())[:6]
        self.assertEqual(len(clean), 6)

# ── Buyback Tests ─────────────────────────────────────────
class TestBuyback(MintKitTestCase):

    def test_buyback_table_creation(self):
        sys.path.insert(0, "core")
        import buyback
        buyback.DB_PATH = self.db_path
        buyback.init_buyback_table()

        conn = self.get_db()
        cur  = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='buybacks'")
        self.assertIsNotNone(cur.fetchone())
        conn.close()

    def test_save_buyback_record(self):
        sys.path.insert(0, "core")
        import buyback
        buyback.DB_PATH = self.db_path
        buyback.init_buyback_table()
        buyback.save_buyback(
            concept_id="TEST",
            ticker="TEST",
            trigger_balance=0.5,
            tokens_bought=1000000,
            tokens_burned=500000,
            tokens_airdropped=500000,
            holder_count=100,
            burn_tx="burn_tx_123",
            airdrop_tx="airdrop_tx_123",
            status="executed"
        )

        conn = self.get_db()
        cur  = conn.cursor()
        cur.execute("SELECT * FROM buybacks WHERE ticker = 'TEST'")
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["tokens_burned"], 500000)
        self.assertEqual(row["status"], "executed")
        conn.close()

# ── CLI Tests ─────────────────────────────────────────────
class TestCLI(unittest.TestCase):

    def test_help_command(self):
        import mintkit
        try:
            sys.argv = ["mintkit.py", "help"]
            mintkit.print_help()
        except SystemExit:
            pass

    def test_unknown_command(self):
        import mintkit
        sys.argv = ["mintkit.py", "unknowncommand"]
        try:
            mintkit.main()
        except SystemExit:
            pass

# ── Run tests ─────────────────────────────────────────────
if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════╗
║         MintKit Test Suite            ║
╚═══════════════════════════════════════╝
""")
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestTransparency))
    suite.addTests(loader.loadTestsFromTestCase(TestTokenomics))
    suite.addTests(loader.loadTestsFromTestCase(TestBuyback))
    suite.addTests(loader.loadTestsFromTestCase(TestCLI))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {len(result.failures)} failed, {len(result.errors)} errors")
        sys.exit(1)
