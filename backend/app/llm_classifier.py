import json
import os
import logging
from openai import OpenAI

SYSTEM_PROMPT = """You are a ticket classifier for a digital finance company (bKash).
Classify the customer message and return ONLY valid JSON with these fields:
{
  "case_type": "wrong_transfer" | "payment_failed" | "refund_request" | "phishing_or_social_engineering" | "other",
  "severity": "low" | "medium" | "high" | "critical",
  "department": "customer_support" | "dispute_resolution" | "payments_ops" | "fraud_risk",
  "agent_summary": "One neutral sentence describing the issue.",
  "human_review_required": true | false,
  "confidence": 0.0 to 1.0
}

Rules:
- wrong_transfer: money sent to wrong recipient → severity high, department dispute_resolution
- payment_failed: transaction failed but balance deducted → severity high, department payments_ops
- refund_request: customer asks for refund → severity low, department customer_support
- phishing_or_social_engineering: suspicious calls, OTP/PIN requests → severity critical, department fraud_risk
- other: anything not covered → severity low, department customer_support
- human_review_required = true for critical severity OR phishing cases
- agent_summary must NEVER ask the customer to share PIN, OTP, password, or card numbers
- confidence should reflect how clearly the message matches a category (0.0-1.0)
- amount mentioned in Bangla (e.g., ৫০০০ টাকা) should be normalized (e.g., 5000 BDT) in the summary."""


def _parse_response(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start != -1 and brace_end != -1:
            try:
                return json.loads(text[brace_start : brace_end + 1])
            except json.JSONDecodeError:
                pass
    return None


def classify_with_llm(ticket_id: str, message: str) -> dict | None:
    api_key = os.environ.get("AIML_API_KEY") or os.environ.get("AIMLAPI_API_KEY")
    base_url = os.environ.get("AIML_API_BASE_URL", "https://api.aimlapi.com/v1")
    model = os.environ.get("AIML_MODEL", "gpt-4o")

    if not api_key:
        logging.warning("AIML_API_KEY not set. Skipping LLM classifier.")
        return None

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Classify this ticket:\nticket_id: {ticket_id}\nmessage: {message}",
                },
            ],
            temperature=0.1,
            max_tokens=300,
        )
        content = response.choices[0].message.content
        if not content:
            logging.warning("LLM returned empty response")
            return None

        parsed = _parse_response(content)
        if not parsed:
            logging.warning(f"LLM response could not be parsed as JSON: {content}")
            return None

        parsed["ticket_id"] = ticket_id
        return parsed

    except Exception:
        logging.exception("LLM classifier failed")
        return None
