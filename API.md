# MintKit API Documentation

Full reference for the MintKit REST API. Use this to build custom tools,
integrations, or your own dashboard on top of MintKit.

---

## Base URL

```
https://your-railway-url.up.railway.app
```

For local development:
```
http://localhost:8000
```

---

## Authentication

Public endpoints are open to everyone.
Action endpoints require a Bearer token obtained by logging in.

### Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "password": "your_dashboard_password"
}
```

**Response:**
```json
{
  "token": "abc123..."
}
```

Include the token in all action requests:
```http
Authorization: Bearer abc123...
```

---

## Public Endpoints

### GET /api/status

Returns the full pipeline status summary.

```http
GET /api/status
```

**Response:**
```json
{
  "checked_at": "2026-03-26T12:00:00",
  "trends_scanned": 247,
  "concepts_generated": 12,
  "concepts_approved": 3,
  "tokens_deployed": 1,
  "promotions_posted": 2,
  "buybacks_executed": 0,
  "tokens_burned": 0,
  "treasury_sol": 0.0
}
```

---

### GET /api/coins

Returns all deployed tokens.

```http
GET /api/coins
```

**Response:**
```json
{
  "coins": [
    {
      "concept_id": "FADE",
      "coin_name": "Faded Coin",
      "ticker": "FADE",
      "mint_address": "5MWGjU8x...",
      "deployer_address": "5BcJbhFv...",
      "liquidity_wallet": "6pwtsDXF...",
      "treasury_wallet": "EZBnzczH...",
      "total_supply": 1000000000,
      "network": "devnet",
      "deployed_at": "2026-03-26T12:00:00",
      "status": "deployed",
      "tx_hash": "abc123..."
    }
  ]
}
```

---

### GET /api/trends

Returns the top scored meme trends from the database.

```http
GET /api/trends
```

**Response:**
```json
{
  "trends": [
    {
      "id": "ac6c1f80",
      "source": "twitter",
      "title": "ngl I don't think Iori is enough of a gamer",
      "description": "Full tweet text...",
      "url": "https://twitter.com/i/web/status/...",
      "velocity_score": 72.0,
      "novelty_score": 100.0,
      "longevity_score": 65.0,
      "viability_score": 79.5,
      "discovered_at": "2026-03-26T12:00:00"
    }
  ]
}
```

---

### GET /api/concepts

Returns all generated coin concepts.

```http
GET /api/concepts
```

**Response:**
```json
{
  "concepts": [
    {
      "id": "ac6c1f80",
      "trend_title": "ngl I don't think Iori...",
      "coin_name": "Faded Coin",
      "ticker": "FADE",
      "tagline": "For everyone who got faded but kept building anyway.",
      "backstory": "Born from the pain of being ignored...",
      "image_prompt": "A ghostly transparent character...",
      "viability_score": 79.5,
      "created_at": "2026-03-26T12:00:00",
      "approved": 1
    }
  ]
}
```

**Approval status values:**
- `0` — pending review
- `1` — approved
- `2` — rejected

---

### GET /api/buybacks

Returns all executed buybacks.

```http
GET /api/buybacks
```

**Response:**
```json
{
  "buybacks": [
    {
      "id": 1,
      "concept_id": "FADE",
      "ticker": "FADE",
      "trigger_balance": 0.5,
      "tokens_bought": 500000,
      "tokens_burned": 250000,
      "tokens_airdropped": 250000,
      "holder_count": 100,
      "burn_tx": "BURN_FADE_...",
      "airdrop_tx": "AIRDROP_FADE_...",
      "executed_at": "2026-03-26T12:00:00",
      "status": "executed"
    }
  ]
}
```

---

### GET /api/activity

Returns the recent activity log across all modules.

```http
GET /api/activity
```

**Response:**
```json
{
  "events": [
    {
      "type": "scan",
      "ts": "2026-03-26T12:00:00",
      "message": "Scan complete — 3 trends found",
      "tag": "scanner"
    },
    {
      "type": "deploy",
      "ts": "2026-03-26T11:00:00",
      "message": "Token deployed — Faded Coin ($FADE)",
      "tag": "deployer · $FADE"
    }
  ]
}
```

---

## Action Endpoints

All action endpoints require Authorization header.

---

### POST /api/actions/scan

Triggers the trend scanner immediately.

```http
POST /api/actions/scan
Authorization: Bearer abc123...
```

**Response:**
```json
{
  "success": true,
  "message": "Scan complete — 3 trends found"
}
```

---

### POST /api/actions/generate

Runs the concept generator on unprocessed trends.

```http
POST /api/actions/generate
Authorization: Bearer abc123...
```

**Response:**
```json
{
  "success": true,
  "message": "Concepts generated successfully"
}
```

---

### POST /api/actions/approve/{concept_id}

Approves a coin concept for deployment.

```http
POST /api/actions/approve/ac6c1f8078399740
Authorization: Bearer abc123...
```

**Response:**
```json
{
  "success": true,
  "message": "Concept ac6c1f8078399740 approved"
}
```

---

### POST /api/actions/reject/{concept_id}

Rejects a coin concept.

```http
POST /api/actions/reject/ac6c1f8078399740
Authorization: Bearer abc123...
```

**Response:**
```json
{
  "success": true,
  "message": "Concept ac6c1f8078399740 rejected"
}
```

---

### POST /api/actions/deploy

Deploys all approved concepts. Optionally provide a config file path.

```http
POST /api/actions/deploy
Authorization: Bearer abc123...
Content-Type: application/json

{
  "config_path": "coin_config.example.json"
}
```

Omit the body to deploy from approved database concepts:
```http
POST /api/actions/deploy
Authorization: Bearer abc123...
```

**Response:**
```json
{
  "success": true,
  "message": "Deployment initiated"
}
```

---

### POST /api/actions/promote

Posts launch announcements for all unannounced deployments.

```http
POST /api/actions/promote
Authorization: Bearer abc123...
```

**Response:**
```json
{
  "success": true,
  "message": "Promotion complete"
}
```

---

### POST /api/actions/buyback

Runs the buyback engine across all active deployments.

```http
POST /api/actions/buyback
Authorization: Bearer abc123...
```

**Response:**
```json
{
  "success": true,
  "message": "Buyback engine complete"
}
```

---

### POST /api/actions/treasury

Generates a treasury report and saves it to the transparency logs.

```http
POST /api/actions/treasury
Authorization: Bearer abc123...
```

**Response:**
```json
{
  "success": true,
  "message": "Treasury report generated"
}
```

---

## Error Responses

All endpoints return a consistent error format:

```json
{
  "detail": "Invalid or missing token"
}
```

**HTTP status codes:**
- `200` — success
- `401` — unauthorized (missing or invalid token)
- `422` — validation error (missing required fields)
- `500` — server error

---

## Example — Full Launch Flow

Here's a complete example of launching a coin via the API:

```python
import requests

BASE = "https://your-mintkit-url.up.railway.app"

# 1. Login
res = requests.post(f"{BASE}/api/auth/login", json={"password": "your_password"})
token = res.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Run scanner
requests.post(f"{BASE}/api/actions/scan", headers=headers)

# 3. Generate concepts
requests.post(f"{BASE}/api/actions/generate", headers=headers)

# 4. Get pending concepts
concepts = requests.get(f"{BASE}/api/concepts").json()["concepts"]
pending = [c for c in concepts if c["approved"] == 0]

# 5. Approve the best one
best = pending[0]
requests.post(f"{BASE}/api/actions/approve/{best['id']}", headers=headers)

# 6. Deploy
requests.post(f"{BASE}/api/actions/deploy", headers=headers)

# 7. Promote
requests.post(f"{BASE}/api/actions/promote", headers=headers)

# 8. Check status
status = requests.get(f"{BASE}/api/status").json()
print(status)
```

---

## Rate Limits

There are currently no rate limits on the API.
For production deployments it is recommended to add rate limiting
via a reverse proxy like nginx or Cloudflare.

---

*MintKit API — by JMHMsr — Apache 2.0 License*
