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


_counter: int = 0


def _db_max_ticket_id(client: Client) -> int | None:
    try:
        result = client.table("ticket_requests").select("ticket_id").order("id", desc=True).limit(1).execute()
        if result.data:
            return int(result.data[0]["ticket_id"].split("-")[1])
    except Exception:
        logging.warning("Failed to query max ticket_id")
    return None


def peek_next_ticket_id() -> str:
    client = _get_client()
    if client:
        num = _db_max_ticket_id(client)
        if num is not None:
            return f"T-{num + 1:03d}"
    return f"T-{_counter + 1:03d}"


def _next_ticket_id(client: Client | None) -> str:
    global _counter
    if client:
        num = _db_max_ticket_id(client)
        if num is not None:
            return f"T-{num + 1:03d}"
    _counter += 1
    return f"T-{_counter:03d}"


def save_ticket_request(
    channel: str | None,
    locale: str | None,
    message: str,
) -> tuple[int | None, str]:
    client = _get_client()
    tid = _next_ticket_id(client)
    if not client:
        return None, tid
    try:
        result = client.table("ticket_requests").insert({
            "ticket_id": tid,
            "channel": channel,
            "locale": locale,
            "message": message,
        }).execute()
        if result.data:
            return result.data[0]["id"], tid
    except Exception:
        logging.exception("Failed to insert ticket request")
    return None, tid


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
