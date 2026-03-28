"""
MintKit Dashboard — FastAPI Backend
Serves the dashboard API and connects to the mintkit database and modules.
"""

import os
import sys
import json
import sqlite3
import hashlib
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Add parent directory to path so we can import mintkit modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(title="MintKit Dashboard", version="1.0.0")

# ── CORS ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config ────────────────────────────────────────────────
DB_PATH       = os.getenv("DB_PATH", "mintkit.db")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "mintkit2026")
SECRET_TOKEN  = hashlib.sha256(DASHBOARD_PASSWORD.encode()).hexdigest()

# ── Auth ──────────────────────────────────────────────────
security = HTTPBearer(auto_error=False)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials or credentials.credentials != SECRET_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token"
        )
    return True

# ── Database ──────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def table_exists(cur, table_name: str) -> bool:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cur.fetchone() is not None

# ── Models ─────────────────────────────────────────────────
class LoginRequest(BaseModel):
    password: str

class DeployRequest(BaseModel):
    config_path: Optional[str] = None

# ── Auth Endpoint ─────────────────────────────────────────
@app.post("/api/auth/login")
def login(req: LoginRequest):
    if req.password == DASHBOARD_PASSWORD:
        return {"token": SECRET_TOKEN}
    raise HTTPException(status_code=401, detail="Invalid password")

# ── Status Endpoint ───────────────────────────────────────
@app.get("/api/status")
def get_status():
    conn = get_db()
    cur  = conn.cursor()
    status = {
        "checked_at": datetime.utcnow().isoformat(),
        "trends_scanned": 0,
        "concepts_generated": 0,
        "concepts_approved": 0,
        "tokens_deployed": 0,
        "promotions_posted": 0,
        "buybacks_executed": 0,
        "tokens_burned": 0,
        "treasury_sol": 0.0
    }

    try:
        if table_exists(cur, "meme_trends"):
            cur.execute("SELECT COUNT(*) as c FROM meme_trends")
            status["trends_scanned"] = cur.fetchone()["c"]

        if table_exists(cur, "coin_concepts"):
            cur.execute("SELECT COUNT(*) as c FROM coin_concepts")
            status["concepts_generated"] = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) as c FROM coin_concepts WHERE approved = 1")
            status["concepts_approved"] = cur.fetchone()["c"]

        if table_exists(cur, "deployments"):
            cur.execute("SELECT COUNT(*) as c FROM deployments WHERE status='deployed'")
            status["tokens_deployed"] = cur.fetchone()["c"]

        if table_exists(cur, "promotions"):
            cur.execute("SELECT COUNT(*) as c FROM promotions")
            status["promotions_posted"] = cur.fetchone()["c"]

        if table_exists(cur, "buybacks"):
            cur.execute("SELECT COUNT(*) as c FROM buybacks")
            status["buybacks_executed"] = cur.fetchone()["c"]
            cur.execute("SELECT SUM(tokens_burned) as t FROM buybacks")
            row = cur.fetchone()
            status["tokens_burned"] = int(row["t"] or 0)

    except Exception as e:
        log.error(f"Status error: {e}")

    conn.close()
    return status

# ── Coins Endpoint ────────────────────────────────────────
@app.get("/api/coins")
def get_coins():
    conn = get_db()
    cur  = conn.cursor()
    coins = []

    try:
        if table_exists(cur, "deployments"):
            cur.execute("SELECT * FROM deployments ORDER BY deployed_at DESC")
            coins = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        log.error(f"Coins error: {e}")

    conn.close()
    return {"coins": coins}

# ── Concepts Endpoint ─────────────────────────────────────
@app.get("/api/concepts")
def get_concepts():
    conn = get_db()
    cur  = conn.cursor()
    concepts = []

    try:
        if table_exists(cur, "coin_concepts"):
            cur.execute("SELECT * FROM coin_concepts ORDER BY created_at DESC LIMIT 20")
            concepts = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        log.error(f"Concepts error: {e}")

    conn.close()
    return {"concepts": concepts}

# ── Trends Endpoint ───────────────────────────────────────
@app.get("/api/trends")
def get_trends():
    conn = get_db()
    cur  = conn.cursor()
    trends = []

    try:
        if table_exists(cur, "meme_trends"):
            cur.execute("SELECT * FROM meme_trends ORDER BY viability_score DESC LIMIT 20")
            trends = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        log.error(f"Trends error: {e}")

    conn.close()
    return {"trends": trends}

# ── Buybacks Endpoint ─────────────────────────────────────
@app.get("/api/buybacks")
def get_buybacks():
    conn = get_db()
    cur  = conn.cursor()
    buybacks = []

    try:
        if table_exists(cur, "buybacks"):
            cur.execute("SELECT * FROM buybacks ORDER BY executed_at DESC LIMIT 20")
            buybacks = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        log.error(f"Buybacks error: {e}")

    conn.close()
    return {"buybacks": buybacks}

# ── Activity Log Endpoint ─────────────────────────────────
@app.get("/api/activity")
def get_activity():
    conn = get_db()
    cur  = conn.cursor()
    events = []

    try:
        # Pull recent events from all tables
        if table_exists(cur, "scan_runs"):
            cur.execute("SELECT 'scan' as type, run_at as ts, status, trends_found as detail FROM scan_runs ORDER BY run_at DESC LIMIT 5")
            for row in cur.fetchall():
                events.append({
                    "type": "scan",
                    "ts": row["ts"],
                    "message": f"Scan complete — {row['detail']} trends found",
                    "tag": "scanner"
                })

        if table_exists(cur, "deployments"):
            cur.execute("SELECT 'deploy' as type, deployed_at as ts, coin_name, ticker, status FROM deployments ORDER BY deployed_at DESC LIMIT 5")
            for row in cur.fetchall():
                events.append({
                    "type": "deploy",
                    "ts": row["ts"],
                    "message": f"Token deployed — {row['coin_name']} (${row['ticker']})",
                    "tag": f"deployer · ${row['ticker']}"
                })

        if table_exists(cur, "promotions"):
            cur.execute("SELECT posted_at as ts, coin_name, ticker, platform, status FROM promotions ORDER BY posted_at DESC LIMIT 5")
            for row in cur.fetchall():
                events.append({
                    "type": "promote",
                    "ts": row["ts"],
                    "message": f"Promoted ${row['ticker']} on {row['platform']}",
                    "tag": f"promoter · ${row['ticker']}"
                })

        if table_exists(cur, "buybacks"):
            cur.execute("SELECT executed_at as ts, ticker, tokens_burned, tokens_airdropped, status FROM buybacks ORDER BY executed_at DESC LIMIT 5")
            for row in cur.fetchall():
                events.append({
                    "type": "buyback",
                    "ts": row["ts"],
                    "message": f"Buyback — burned {row['tokens_burned']:,} ${row['ticker']}",
                    "tag": f"buyback · ${row['ticker']}"
                })

    except Exception as e:
        log.error(f"Activity error: {e}")

    conn.close()
    events.sort(key=lambda x: x["ts"], reverse=True)
    return {"events": events[:20]}

# ── Action Endpoints (require auth) ───────────────────────
@app.post("/api/actions/scan")
def action_scan(auth=Depends(verify_token)):
    try:
        from plugins.trend_scanner import run_scan
        results = run_scan()
        return {"success": True, "message": f"Scan complete — {len(results)} trends found"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/actions/generate")
def action_generate(auth=Depends(verify_token)):
    try:
        from plugins.concept_generator import run_concept_generator
        run_concept_generator()
        return {"success": True, "message": "Concepts generated successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/actions/approve/{concept_id}")
def action_approve(concept_id: str, auth=Depends(verify_token)):
    try:
        from plugins.concept_generator import approve_concept, init_concepts_table
        init_concepts_table()
        approve_concept(concept_id)
        return {"success": True, "message": f"Concept {concept_id} approved"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/actions/reject/{concept_id}")
def action_reject(concept_id: str, auth=Depends(verify_token)):
    try:
        from plugins.concept_generator import reject_concept, init_concepts_table
        init_concepts_table()
        reject_concept(concept_id)
        return {"success": True, "message": f"Concept {concept_id} rejected"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/actions/deploy")
def action_deploy(req: DeployRequest, auth=Depends(verify_token)):
    try:
        from core.deployer import run_deployer
        run_deployer(req.config_path)
        return {"success": True, "message": "Deployment initiated"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/actions/promote")
def action_promote(auth=Depends(verify_token)):
    try:
        from core.promoter import run_promoter
        run_promoter()
        return {"success": True, "message": "Promotion complete"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/actions/buyback")
def action_buyback(auth=Depends(verify_token)):
    try:
        from core.buyback import run_buyback_engine
        run_buyback_engine()
        return {"success": True, "message": "Buyback engine complete"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/actions/treasury")
def action_treasury(auth=Depends(verify_token)):
    try:
        from core.treasury import run_treasury_manager
        run_treasury_manager()
        return {"success": True, "message": "Treasury report generated"}
    except Exception as e:
        return {"success": False, "message": str(e)}

# ── Serve Public Launchpad ────────────────────────────────
public_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
if os.path.exists(public_path):
    app.mount("/", StaticFiles(directory=public_path, html=True), name="public")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
