# QueueStorm — Warmup Mock Preliminary

A ticket classification web service built for the SUST CSE Carnival 2026 Codex Community Hackathon.

## What It Does

Accepts a customer support message via `POST /sort-ticket` and returns a structured classification:
- **case_type** — wrong_transfer, payment_failed, refund_request, phishing_or_social_engineering, other
- **severity** — low, medium, high, critical
- **department** — customer_support, dispute_resolution, payments_ops, fraud_risk
- **agent_summary** — neutral one-sentence description
- **human_review_required** — flagged for critical / phishing cases
- **confidence** — 0.0 to 1.0

## Tech Stack

- **Runtime:** Python 3.12+ / FastAPI
- **Classification:** Rule-based keyword matching (no LLM dependency)
- **Database:** Supabase (PostgreSQL)
- **Deployment:** Vercel (serverless)

## Project Structure

```
├── api/
│   └── index.py          # Vercel ASGI entry point
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app & endpoints
│   ├── schemas.py        # Pydantic request/response models
│   ├── classifier.py     # Rule-based classification engine
│   └── database.py       # Supabase persistence layer
├── db/
│   └── 00001_create_ticket_tables.sql  # DB migration
├── .env                  # Supabase credentials (not committed)
├── .gitignore
├── requirements.txt
├── vercel.json
└── README.md
```

## Local Development

### Prerequisites

- Python 3.12+
- A Supabase project with the migration from `db/00001_create_ticket_tables.sql` applied

### Setup

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Environment Variables

Copy `.env` and fill in your Supabase credentials:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
```

### Run

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Endpoints

### `GET /health`

Returns service health status.

### `POST /sort-ticket`

**Request:**

```json
{
  "ticket_id": "T-001",
  "channel": "app",
  "locale": "en",
  "message": "I sent 5000 taka to a wrong number this morning, please help me get it back"
}
```

**Response:**

```json
{
  "ticket_id": "T-001",
  "case_type": "wrong_transfer",
  "severity": "high",
  "department": "dispute_resolution",
  "agent_summary": "Customer reports sending 5000 TAKA to a wrong number and requests recovery.",
  "human_review_required": true,
  "confidence": 0.85
}
```

## Deployment

### Vercel

1. Push the repository to GitHub.
2. Import the project in Vercel.
3. Set environment variables (`SUPABASE_URL`, `SUPABASE_KEY`) in Vercel dashboard.
4. Deploy — Vercel detects `vercel.json` and builds the Python serverless function.

### Alternative Platforms

The service runs as a standard FastAPI app and can be deployed on Render, Railway, Fly.io, or any platform supporting ASGI/WSGI.
