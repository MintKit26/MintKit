"""
TrendMintBot — Trend Scanner
Bearer Token only. SQLite database. No Redis required.
"""

import os
import json
import time
import hashlib
import logging
import sqlite3
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional

import tweepy
from dotenv import load_dotenv
import anthropic
import schedule

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Settings ──────────────────────────────────────────────
SCAN_INTERVAL_HOURS = 6
MIN_VIABILITY_SCORE = 20
TOP_N_CANDIDATES    = 3
TWITTER_MEME_TERMS  = ["meme", "viral", "lol", "based", "ngl", "iykyk"]
DB_PATH             = "mintkit.db"

# ── Data Structure ────────────────────────────────────────
@dataclass
class MemeTrend:
    id: str
    source: str
    title: str
    description: str
    url: str
    raw_score: float
    velocity_score: float
    novelty_score: float
    longevity_score: float
    viability_score: float
    discovered_at: str
    image_url: Optional[str] = None

# ── Database ──────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meme_trends (
            id TEXT PRIMARY KEY,
            source TEXT,
            title TEXT,
            description TEXT,
            url TEXT,
            image_url TEXT,
            raw_score REAL,
            velocity_score REAL,
            novelty_score REAL,
            longevity_score REAL,
            viability_score REAL,
            discovered_at TEXT,
            used_for_coin INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scan_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at TEXT,
            trends_found INTEGER,
            top_candidates TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()
    log.info("Database ready.")

# ── Clients ───────────────────────────────────────────────
def get_twitter_client():
    bearer = os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer:
        raise ValueError("TWITTER_BEARER_TOKEN not found")
    return tweepy.Client(bearer_token=bearer, wait_on_rate_limit=True)

def get_claude_client():
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY not found")
    return anthropic.Anthropic(api_key=key)

# ── Deduplication ─────────────────────────────────────────
def make_id(text: str) -> str:
    return hashlib.sha256(text.lower().strip().encode()).hexdigest()[:16]

def is_duplicate(trend_id: str) -> bool:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM meme_trends WHERE id = ?", (trend_id,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

# ── Scoring ───────────────────────────────────────────────
def score_velocity(engagement: float, age_hours: float) -> float:
    if age_hours <= 0:
        age_hours = 0.1
    rate = engagement / age_hours
    thresholds = [100, 500, 1000, 5000, 10000, 50000]
    for i, t in enumerate(thresholds):
        if rate < t:
            return (i / len(thresholds)) * 100
    return 100.0

def score_longevity(title: str, claude: anthropic.Anthropic) -> float:
    try:
        response = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": f"""Rate this meme trend's longevity 0-100.
0-20=one day, 21-50=few days, 51-75=multi-week, 76-100=long-term.
Title: {title}
Reply ONLY with JSON: {{"score": 72}}"""
            }]
        )
        text = response.content[0].text.strip().replace("```json","").replace("```","")
        return float(json.loads(text).get("score", 50))
    except Exception as e:
        log.warning(f"Longevity scoring failed: {e}")
        return 50.0

def compute_viability(velocity: float, longevity: float) -> float:
    return (velocity * 0.60) + (longevity * 0.40)

# ── Twitter Scanner ───────────────────────────────────────
def scan_twitter(client: tweepy.Client, claude: anthropic.Anthropic) -> list:
    log.info("Scanning Twitter/X...")
    trends = []

    try:
        query = "(" + " OR ".join(TWITTER_MEME_TERMS) + ") lang:en -is:retweet has:images"
        response = client.search_recent_tweets(
            query=query,
            max_results=50,
            sort_order="relevancy",
            tweet_fields=["created_at", "public_metrics"],
        )

        if not response.data:
            log.info("No tweets returned.")
            return trends

        for tweet in response.data:
            metrics = tweet.public_metrics
            engagement = (
                metrics.get("like_count", 0) +
                metrics.get("retweet_count", 0) * 2 +
                metrics.get("reply_count", 0)
            )

            if engagement < 100:
                continue

            trend_id = make_id(tweet.text)
            if is_duplicate(trend_id):
                continue

            created = tweet.created_at
            age_hours = max((datetime.utcnow() - created.replace(tzinfo=None)).total_seconds() / 3600, 0.1)

            velocity  = score_velocity(engagement, age_hours)
            longevity = score_longevity(tweet.text[:120], claude)
            viability = compute_viability(velocity, longevity)

            trends.append(MemeTrend(
                id=trend_id,
                source="twitter",
                title=tweet.text[:120],
                description=tweet.text,
                url=f"https://twitter.com/i/web/status/{tweet.id}",
                raw_score=float(engagement),
                velocity_score=velocity,
                novelty_score=0,
                longevity_score=longevity,
                viability_score=viability,
                discovered_at=datetime.utcnow().isoformat(),
                image_url=None
            ))

    except Exception as e:
        log.error(f"Twitter scan error: {e}")

    log.info(f"Twitter: {len(trends)} new trends found.")
    return trends

# ── Save ──────────────────────────────────────────────────
def save_trends(trends: list):
    if not trends:
        return
    conn = get_db()
    cur = conn.cursor()
    for t in trends:
        cur.execute("""
            INSERT OR IGNORE INTO meme_trends
            (id, source, title, description, url, image_url,
            raw_score, velocity_score, novelty_score, longevity_score,
            viability_score, discovered_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            t.id, t.source, t.title, t.description, t.url, t.image_url,
            t.raw_score, t.velocity_score, t.novelty_score, t.longevity_score,
            t.viability_score, t.discovered_at
        ))
    conn.commit()
    conn.close()

def log_scan_run(count: int, top: list, status: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO scan_runs (run_at, trends_found, top_candidates, status) VALUES (?,?,?,?)",
        (datetime.utcnow().isoformat(), count, json.dumps([asdict(t) for t in top]), status)
    )
    conn.commit()
    conn.close()

# ── Main Scan Cycle ───────────────────────────────────────
def run_scan():
    log.info("=" * 50)
    log.info("Starting scan cycle...")
    init_db()

    try:
        twitter = get_twitter_client()
        claude  = get_claude_client()
    except ValueError as e:
        log.error(f"Setup error: {e}")
        return []

    all_trends = scan_twitter(twitter, claude)

    viable = [t for t in all_trends if t.viability_score >= MIN_VIABILITY_SCORE]
    viable.sort(key=lambda t: t.viability_score, reverse=True)

    save_trends(all_trends)

    top = viable[:TOP_N_CANDIDATES]

    log.info(f"Done: {len(all_trends)} found, {len(viable)} viable, {len(top)} selected.")
    for i, t in enumerate(top, 1):
        log.info(f"  {i}. {t.title[:70]} | score={t.viability_score:.1f}")

    log_scan_run(len(all_trends), top, "success")
    return top

# ── Scheduler ─────────────────────────────────────────────
def start_scheduler():
    log.info(f"TrendMintBot started. Scanning every {SCAN_INTERVAL_HOURS} hours.")
    init_db()
    run_scan()
    schedule.every(SCAN_INTERVAL_HOURS).hours.do(run_scan)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    start_scheduler()
