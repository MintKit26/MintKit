import sqlite3

conn = sqlite3.connect('mintkit.db')
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS meme_trends (
    id TEXT PRIMARY KEY, source TEXT, title TEXT, description TEXT,
    url TEXT, image_url TEXT, raw_score REAL, velocity_score REAL,
    novelty_score REAL, longevity_score REAL, viability_score REAL,
    discovered_at TEXT, used_for_coin INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')))""")

cur.execute("""CREATE TABLE IF NOT EXISTS scan_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at TEXT DEFAULT (datetime('now')),
    trends_found INTEGER, top_candidates TEXT, status TEXT)""")

conn.commit()
conn.close()
print("Done! Tables created successfully.")
