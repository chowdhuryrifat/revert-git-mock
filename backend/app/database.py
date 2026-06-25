import os
import logging
from supabase import create_client, Client

_client: Client | None = None


def _get_client() -> Client | None:
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            logging.warning("SUPABASE_URL or SUPABASE_KEY not set. DB persistence disabled.")
            return None
        try:
            _client = create_client(url, key)
        except Exception:
            logging.exception("Failed to create Supabase client")
            return None
    return _client


def save_ticket_request(
    ticket_id: str,
    channel: str | None,
    locale: str | None,
    message: str,
) -> int | None:
    client = _get_client()
    if not client:
        return None
    try:
        result = client.table("ticket_requests").insert({
            "ticket_id": ticket_id,
            "channel": channel,
            "locale": locale,
            "message": message,
        }).execute()
        if result.data:
            return result.data[0]["id"]
    except Exception:
        logging.exception("Failed to insert ticket request")
    return None


def save_ticket_response(
    ticket_request_id: int,
    ticket_id: str,
    case_type: str,
    severity: str,
    department: str,
    agent_summary: str,
    human_review_required: bool,
    confidence: float,
) -> None:
    client = _get_client()
    if not client:
        return
    try:
        client.table("ticket_responses").insert({
            "ticket_request_id": ticket_request_id,
            "ticket_id": ticket_id,
            "case_type": case_type,
            "severity": severity,
            "department": department,
            "agent_summary": agent_summary,
            "human_review_required": human_review_required,
            "confidence": round(confidence, 3),
        }).execute()
    except Exception:
        logging.exception("Failed to insert ticket response")
