# QueueStorm — Warmup Mock Preliminary

A ticket classification web service built for the **SUST CSE Carnival 2026 Codex Community Hackathon — Mock Preliminary Round**.

Accepts a customer support message via `POST /sort-ticket` and returns a structured classification with case type, severity, department, agent summary, and confidence score.

## Live URL

> [https://revert-git-mock-omega.vercel.app/](https://revert-git-mock-omega.vercel.app/)

## Features

- **Auto-generated Ticket ID** — customers cannot modify the ticket number; it is assigned from the database
- **LLM-Powered Classification** — uses AI/ML API (aimlapi.com) with OpenAI-compatible GPT-4o for accurate classification
- **Rule-Based Fallback** — keyword-matching engine activates when the LLM API is unavailable
- **Safety Filter** — agent summaries never ask customers to share PIN, OTP, password, or card numbers
- **Supabase Persistence** — all ticket requests and responses are stored in PostgreSQL (Supabase)
- **Web Frontend** — single-page HTML/JS interface served directly by the FastAPI backend

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Runtime** | Python 3.12+ / FastAPI |
| **Classification** | LLM (AI/ML API — GPT-4o) + rule-based fallback |
| **Database** | Supabase (PostgreSQL) |
| **Frontend** | Vanilla HTML + CSS + JS (served by FastAPI) |
| **Deployment** | Vercel (serverless) |

## Project Structure

```
├── api/
│   └── index.py              # Vercel ASGI entry point
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI app, endpoints & static file serving
│   ├── schemas.py             # Pydantic request/response models
│   ├── classifier.py          # Entry point: tries LLM first, falls back to rules
│   ├── llm_classifier.py      # LLM-based classification via AI/ML API
│   └── database.py            # Supabase persistence + auto ticket_id generation
├── static/
│   └── index.html             # Frontend single-page app
├── db/
│   └── 00001_create_ticket_tables.sql  # PostgreSQL migration
├── .env                       # Credentials (not committed)
├── .gitignore
├── requirements.txt
├── vercel.json
└── README.md
```

## API Endpoints

### `GET /health`

Returns service health status.

**Response:**
```json
{
  "status": "ok",
  "service": "queuestorm-classifier"
}
```

### `GET /next-ticket-id`

Returns the next auto-generated ticket ID from the database (read-only, does not advance the counter).

**Response:**
```json
{
  "ticket_id": "T-005"
}
```

### `POST /sort-ticket`

Accepts a customer support ticket and returns a structured classification.

**Request:**
```json
{
  "ticket_id": "T-001",
  "channel": "app",
  "locale": "en",
  "message": "I sent 5000 taka to a wrong number this morning, please help me get it back"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `ticket_id` | string | Yes | Echoed back; backend assigns the actual ID from DB |
| `channel` | string | No | `app`, `sms`, `call_center`, `merchant_portal` |
| `locale` | string | No | `bn`, `en`, `mixed` |
| `message` | string | Yes | Free-text customer complaint |

**Response:**
```json
{
  "ticket_id": "T-001",
  "case_type": "wrong_transfer",
  "severity": "high",
  "department": "dispute_resolution",
  "agent_summary": "The customer sent 5000 BDT to the wrong number.",
  "human_review_required": false,
  "confidence": 1.0
}
```

| Field | Type | Notes |
|-------|------|-------|
| `ticket_id` | string | Matches request value |
| `case_type` | enum | `wrong_transfer`, `payment_failed`, `refund_request`, `phishing_or_social_engineering`, `other` |
| `severity` | enum | `low`, `medium`, `high`, `critical` |
| `department` | enum | `customer_support`, `dispute_resolution`, `payments_ops`, `fraud_risk` |
| `agent_summary` | string | Neutral one-sentence description (never asks for PIN/OTP) |
| `human_review_required` | boolean | `true` for critical severity or phishing cases |
| `confidence` | number | 0.0 – 1.0 |

## Classification Logic

1. **LLM (primary):** Sends the message to AI/ML API (`gpt-4o`) with a structured system prompt. Returns JSON directly.
2. **Rule-based (fallback):** Keyword-pattern matching across 5 case types with confidence scoring.
3. **Safety filter:** Scans the generated summary for PIN/OTP/password leakage; replaces if detected.

## LLM Usage

- **Used:** Yes
- **Provider:** AI/ML API (aimlapi.com) — OpenAI-compatible endpoint
- **Model:** `gpt-4o`
- **Fallback:** Rule-based keyword matching activates when the API key is missing or the request fails

## Local Development

### Prerequisites

- Python 3.12+
- A Supabase project with the migration from `db/00001_create_ticket_tables.sql` applied
- (Optional) An AI/ML API key from [aimlapi.com](https://aimlapi.com)

### Setup

```bash
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r backend\requirements.txt
```

### Environment Variables

Create a `.env` file in the `backend/` directory:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
AIML_API_KEY=your-aimlapi-key     # optional — falls back to rules
```

### Run

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API and frontend are both available at `http://localhost:8000`.

## Deployment (Vercel — Runbook)

### Prerequisites

- GitHub repository with the code pushed
- Vercel account connected to GitHub

### Steps

1. **Import the repository** in the Vercel dashboard.
2. **Set Root Directory** to `backend/`.
3. **Environment Variables** — add these in Vercel project settings:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-service-role-key
   AIML_API_KEY=your-aimlapi-key
   ```
4. **Deploy** — Vercel auto-detects Python, builds the serverless function, and serves both the API and the frontend.

### Redeploy

- Push a new commit to GitHub (auto-deploy), or
- In Vercel dashboard → **Deployments** → select the latest → **Redeploy**

### Verify

```
curl https://your-app.vercel.app/health
# {"status":"ok","service":"queuestorm-classifier"}
```

Open the app URL in a browser to see the frontend.

## Known Issues / Blocker

- **Supabase required for persistence:** Without Supabase credentials, tickets are still classified but not persisted (graceful fallback with in-memory counter for ticket IDs).
- **LLM API latency:** First request may take 2–5 seconds due to cold start + LLM inference. Rule-based fallback is instantaneous.
- **Local counter is not persistent:** Without Supabase, the in-memory ticket ID counter resets on server restart.
- **Bangla numeric amounts:** The LLM handles Bangla numerals (e.g., ৫০০০); the rule-based extractor handles only Arabic numerals.
