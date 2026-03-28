"""
MintKit — Token Image Generator
Generates meme coin logos using the fal.ai image API.
Produces square logo images ready for token metadata.
"""

import os
import json
import logging
import sqlite3
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

DB_PATH    = "mintkit.db"
IMAGE_DIR  = "images"
FAL_API_KEY = os.getenv("FAL_API_KEY", "")

# ── Image style template ──────────────────────────────────
STYLE_PREFIX = """Meme coin logo, cartoon style, vibrant colors,
clean white background, centered composition, 
suitable for cryptocurrency token, fun and memorable,
high quality digital art, 512x512"""

# ── Database ──────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_images_table():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS token_images (
            id TEXT PRIMARY KEY,
            ticker TEXT,
            coin_name TEXT,
            image_path TEXT,
            prompt_used TEXT,
            generated_at TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_image_record(concept_id, ticker, coin_name, image_path, prompt, status):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO token_images
        (id, ticker, coin_name, image_path, prompt_used, generated_at, status)
        VALUES (?,?,?,?,?,?,?)
    """, (concept_id, ticker, coin_name, image_path, prompt,
          datetime.utcnow().isoformat(), status))
    conn.commit()
    conn.close()

# ── Get concepts needing images ───────────────────────────
def get_concepts_needing_images() -> list:
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("""
            SELECT c.* FROM coin_concepts c
            LEFT JOIN token_images i ON c.id = i.id
            WHERE c.approved = 1
            AND i.id IS NULL
        """)
        rows = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        log.error(f"Could not fetch concepts: {e}")
        rows = []
    conn.close()
    return rows

# ── Generate image via fal.ai ─────────────────────────────
def generate_image_fal(prompt: str, ticker: str) -> Optional[str]:
    """
    Generate image using fal.ai fast-sdxl API.
    Get your API key at fal.ai
    """
    if not FAL_API_KEY:
        log.error("FAL_API_KEY not set — get one at fal.ai")
        return None

    try:
        import urllib.request
        import json

        full_prompt = f"{STYLE_PREFIX}, {prompt}"

        payload = json.dumps({
            "prompt": full_prompt,
            "image_size": "square_hd",
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
            "num_images": 1,
            "enable_safety_checker": True
        }).encode()

        req = urllib.request.Request(
            "https://fal.run/fal-ai/fast-sdxl",
            data=payload,
            headers={
                "Authorization": f"Key {FAL_API_KEY}",
                "Content-Type": "application/json"
            }
        )

        with urllib.request.urlopen(req, timeout=60) as res:
            data = json.loads(res.read())
            image_url = data["images"][0]["url"]

        # Download the image
        os.makedirs(IMAGE_DIR, exist_ok=True)
        image_path = os.path.join(IMAGE_DIR, f"{ticker.lower()}_logo.png")

        urllib.request.urlretrieve(image_url, image_path)
        log.info(f"Image saved: {image_path}")
        return image_path

    except Exception as e:
        log.error(f"Image generation failed: {e}")
        return None

# ── Fallback: generate placeholder ───────────────────────
def generate_placeholder(ticker: str, coin_name: str) -> str:
    """
    Generate a simple SVG placeholder logo when no image API is available.
    """
    os.makedirs(IMAGE_DIR, exist_ok=True)
    svg_path = os.path.join(IMAGE_DIR, f"{ticker.lower()}_logo.svg")

    # Pick a color based on ticker
    colors = ["#4F46E5", "#059669", "#DC2626", "#D97706", "#7C3AED", "#0284C7"]
    color  = colors[sum(ord(c) for c in ticker) % len(colors)]
    letter = ticker[0] if ticker else "M"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <circle cx="256" cy="256" r="256" fill="{color}"/>
  <circle cx="256" cy="256" r="220" fill="white" opacity="0.15"/>
  <text x="256" y="300" font-family="Arial Black, sans-serif" font-size="220"
        font-weight="900" fill="white" text-anchor="middle">{letter}</text>
  <text x="256" y="420" font-family="Arial, sans-serif" font-size="72"
        font-weight="bold" fill="white" text-anchor="middle" opacity="0.9">${ticker}</text>
</svg>"""

    with open(svg_path, "w") as f:
        f.write(svg)

    log.info(f"Placeholder logo saved: {svg_path}")
    return svg_path

# ── Main ──────────────────────────────────────────────────
def run_image_generator():
    """Generate images for all approved concepts that don't have one yet."""
    log.info("Starting Image Generator...")
    init_images_table()

    concepts = get_concepts_needing_images()
    if not concepts:
        log.info("No concepts need images.")
        return

    log.info(f"Generating images for {len(concepts)} concept(s)...")
    for concept in concepts:
        ticker    = concept["ticker"]
        coin_name = concept["coin_name"]
        prompt    = concept.get("image_prompt", f"cute cartoon mascot for {coin_name} cryptocurrency")

        log.info(f"Generating image for {coin_name} (${ticker})...")

        if FAL_API_KEY:
            image_path = generate_image_fal(prompt, ticker)
        else:
            log.warning("No FAL_API_KEY — generating SVG placeholder")
            image_path = generate_placeholder(ticker, coin_name)

        if image_path:
            save_image_record(
                concept_id=concept["id"],
                ticker=ticker,
                coin_name=coin_name,
                image_path=image_path,
                prompt=prompt,
                status="generated"
            )
            print(f"  ✅ {coin_name} (${ticker}) → {image_path}")
        else:
            save_image_record(
                concept_id=concept["id"],
                ticker=ticker,
                coin_name=coin_name,
                image_path="",
                prompt=prompt,
                status="failed"
            )
            print(f"  ❌ {coin_name} (${ticker}) — failed")

if __name__ == "__main__":
    run_image_generator()
