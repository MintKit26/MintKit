"""
TrendMintBot — Concept Generator
Takes trending memes from the scanner and generates a full coin identity.
"""

import os
import json
import logging
import sqlite3
import sys
from datetime import datetime
from dataclasses import dataclass

from dotenv import load_dotenv
import anthropic

load_dotenv()

# ── API Keys ─────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

DB_PATH = "trendmintbot.db"

# ── Data Structure ────────────────────────────────────────
@dataclass
class CoinConcept:
    id: str
    trend_title: str
    coin_name: str
    ticker: str
    tagline: str
    backstory: str
    image_prompt: str
    viability_score: float
    created_at: str
    approved: int = 0

# ── Database ──────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_concepts_table():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS coin_concepts (
            id TEXT PRIMARY KEY,
            trend_title TEXT,
            coin_name TEXT,
            ticker TEXT,
            tagline TEXT,
            backstory TEXT,
            image_prompt TEXT,
            viability_score REAL,
            created_at TEXT,
            approved INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()
    log.info("Coin concepts table ready.")

# ── Fetch Unprocessed Trends ──────────────────────────────
def get_unprocessed_trends():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.* FROM meme_trends t
        LEFT JOIN coin_concepts c ON t.id = c.id
        WHERE c.id IS NULL
        ORDER BY t.viability_score DESC
        LIMIT 5
    """)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows

# ── Generate Concept ──────────────────────────────────────
def generate_coin_concept(trend: dict, claude: anthropic.Anthropic):
    prompt = f"""You are a creative director for meme coins. Create a fun, original coin identity based on this trending meme.

TRENDING MEME:
Title: {trend['title']}
Description: {trend['description']}

Rules:
- Fun and culturally relevant
- No financial promises, no "moon", "pump", "guaranteed"
- Do not copy existing coins
- Ticker must be 3-6 capital letters only

Respond ONLY with JSON, no markdown:
{{
    "coin_name": "Example Coin",
    "ticker": "EXMPL",
    "tagline": "One fun sentence about the coin",
    "backstory": "2-3 sentences about the coin community vibe.",
    "image_prompt": "Detailed image generation prompt for the coin logo."
}}"""

    try:
        response = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(text)

        ticker = "".join(c for c in data["ticker"].upper() if c.isalpha())[:6]

        concept = CoinConcept(
            id=trend["id"],
            trend_title=trend["title"][:120],
            coin_name=data["coin_name"],
            ticker=ticker,
            tagline=data["tagline"],
            backstory=data["backstory"],
            image_prompt=data["image_prompt"],
            viability_score=trend["viability_score"],
            created_at=datetime.utcnow().isoformat(),
            approved=0
        )
        log.info(f"Generated: {concept.coin_name} (${concept.ticker})")
        return concept

    except Exception as e:
        log.error(f"Generation failed: {e}")
        return None

# ── Save ──────────────────────────────────────────────────
def save_concept(concept: CoinConcept):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO coin_concepts
        (id, trend_title, coin_name, ticker, tagline, backstory,
         image_prompt, viability_score, created_at, approved)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        concept.id, concept.trend_title, concept.coin_name, concept.ticker,
        concept.tagline, concept.backstory, concept.image_prompt,
        concept.viability_score, concept.created_at, concept.approved
    ))
    conn.commit()
    conn.close()

# ── Review ────────────────────────────────────────────────
def review_pending_concepts():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM coin_concepts WHERE approved = 0")
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()

    if not rows:
        log.info("No pending concepts.")
        return

    print("\n" + "=" * 60)
    print("PENDING COIN CONCEPTS")
    print("=" * 60)
    for i, row in enumerate(rows, 1):
        print(f"\n[{i}] {row['coin_name']} (${row['ticker']})")
        print(f"    Trend:     {row['trend_title'][:70]}")
        print(f"    Tagline:   {row['tagline']}")
        print(f"    Backstory: {row['backstory']}")
        print(f"    Image:     {row['image_prompt'][:80]}...")
        print(f"    ID:        {row['id']}")
    print("\n" + "=" * 60)
    print("Approve: python concept_generator.py approve <ID>")
    print("Reject:  python concept_generator.py reject <ID>")
    print("=" * 60 + "\n")

def approve_concept(concept_id: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE coin_concepts SET approved = 1 WHERE id = ?", (concept_id,))
    conn.commit()
    conn.close()
    print(f"Approved: {concept_id}")

def reject_concept(concept_id: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE coin_concepts SET approved = 2 WHERE id = ?", (concept_id,))
    conn.commit()
    conn.close()
    print(f"Rejected: {concept_id}")

# ── Main ──────────────────────────────────────────────────
def run_concept_generator():
    log.info("Starting Concept Generator...")
    init_concepts_table()

    if not ANTHROPIC_API_KEY:
        log.error("ANTHROPIC_API_KEY not found.")
        log.error("Add it to your .env file: ANTHROPIC_API_KEY=sk-ant-yourkey")
        return

    claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    trends = get_unprocessed_trends()
    if not trends:
        log.info("No new trends to process.")
        review_pending_concepts()
        return

    log.info(f"Processing {len(trends)} trends...")
    for trend in trends:
        concept = generate_coin_concept(trend, claude)
        if concept:
            save_concept(concept)

    review_pending_concepts()

if __name__ == "__main__":
    if len(sys.argv) == 3:
        action = sys.argv[1]
        concept_id = sys.argv[2]
        init_concepts_table()
        if action == "approve":
            approve_concept(concept_id)
        elif action == "reject":
            reject_concept(concept_id)
        else:
            print("Use: approve or reject")
    else:
        run_concept_generator()
