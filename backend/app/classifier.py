import re
from .schemas import CaseType, Severity, Department


KEYWORD_PATTERNS = {
    CaseType.wrong_transfer: [
        r"wrong\s+number",
        r"wrong\s+person",
        r"wrong\s+recipient",
        r"sent\s+to\s+wrong",
        r"send\s+to\s+wrong",
        r"sent\s+\w+\s+to\s+wrong",
        r"send\s+\w+\s+to\s+wrong",
        r"mistakenly\s+sent",
        r"transferred\s+to\s+wrong",
        r"transferred\s+\w+\s+to\s+wrong",
        r"wrong\s+account",
        r"incorrect\s+number",
        r"wrong\s+bkash\s+number",
        r"wrong\s+bKash\s+number",
        r"went\s+to\s+wrong",
    ],
    CaseType.payment_failed: [
        r"payment\s+failed",
        r"transaction\s+failed",
        r"failed\s+transaction",
        r"deducted\s+but",
        r"money\s+deducted",
        r"amount\s+deducted",
        r"failed\s+but",
        r"payment\s+didn't\s+go\s+through",
        r"payment\s+did\s+not\s+go\s+through",
        r"payment\s+unsuccessful",
        r"money\s+taken\s+but",
        r"charged\s+but",
        r"amount\s+deducted\s+but\s+not",
    ],
    CaseType.refund_request: [
        r"\brefund\b",
        r"give\s+me\s+back",
        r"get\s+my\s+money\s+back",
        r"\breverse\b",
        r"cancel\s+transaction",
        r"changed\s+my\s+mind",
        r"money\s+back",
        r"return\s+my\s+money",
    ],
    CaseType.phishing_or_social_engineering: [
        r"\botp\b",
        r"\bpin\b",
        r"asking\s+for\s+(?:my\s+)?password",
        r"share\s+(?:your\s+)?password",
        r"\bscam\b",
        r"\bphishing\b",
        r"called\s+me",
        r"asking\s+for\s+my",
        r"fake\s+call",
        r"suspicious\s+call",
        r"bank\s+calling",
        r"asking\s+for\s+otp",
    ],
}


CASE_TYPE_SEVERITY = {
    CaseType.wrong_transfer: Severity.high,
    CaseType.payment_failed: Severity.high,
    CaseType.refund_request: Severity.low,
    CaseType.phishing_or_social_engineering: Severity.critical,
    CaseType.other: Severity.low,
}


CASE_TYPE_DEPARTMENT = {
    CaseType.wrong_transfer: Department.dispute_resolution,
    CaseType.payment_failed: Department.payments_ops,
    CaseType.refund_request: Department.customer_support,
    CaseType.phishing_or_social_engineering: Department.fraud_risk,
    CaseType.other: Department.customer_support,
}


AMOUNT_PATTERN = r"(\d+[\d,.]*)\s*(taka|bdt|tk|\u09f3)?\b"
SAFETY_PATTERNS = [
    r"(?:share|send|provide|give|enter|type)\s+(?:me\s+)?(?:your\s+)?(?:pin|otp|password)",
    r"(?:ask|asking)\s+(?:for\s+)?(?:your\s+)?(?:pin|otp|password)",
    r"(?:full\s+)?card\s+number",
    r"credit\s+card",
]


def _count_matches(text: str, patterns: list[str]) -> int:
    return sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))


def _extract_amount(message: str) -> str | None:
    match = re.search(AMOUNT_PATTERN, message, re.IGNORECASE)
    if match:
        amount = match.group(1)
        currency = match.group(2)
        return f"{amount} {currency.upper() if currency else 'BDT'}"
    match = re.search(r"(?:sent|transferred|paid|send|pay|transfer)\s+(\d+[\d,.]*)", message, re.IGNORECASE)
    if match:
        return f"{match.group(1)} BDT"
    return None


def _generate_summary(case_type: CaseType, message: str) -> str:
    if case_type is CaseType.wrong_transfer:
        amount = _extract_amount(message)
        if amount:
            return f"Customer reports sending {amount} to a wrong number and requests recovery."
        return "Customer reports sending money to a wrong recipient and requests recovery."

    if case_type is CaseType.payment_failed:
        return "Customer reports a payment failure where the balance was deducted but the transaction did not complete."

    if case_type is CaseType.refund_request:
        return "Customer requests a refund for a recent transaction."

    if case_type is CaseType.phishing_or_social_engineering:
        return "Customer reports a suspicious communication requesting sensitive information."

    text = message if len(message) <= 100 else message[:97] + "..."
    return f"Customer reports: {text}"


def _safety_filter(summary: str) -> str:
    for pattern in SAFETY_PATTERNS:
        if re.search(pattern, summary, re.IGNORECASE):
            return "Customer requires assistance. An agent will review the ticket."
    return summary


def classify(ticket_id: str, message: str) -> dict:
    text = message.lower()

    best_case = CaseType.other
    best_score = 0

    for case_type, patterns in KEYWORD_PATTERNS.items():
        score = _count_matches(text, patterns)
        if score > best_score:
            best_score = score
            best_case = case_type

    if best_score == 0:
        best_case = CaseType.other

    severity = CASE_TYPE_SEVERITY[best_case]
    department = CASE_TYPE_DEPARTMENT[best_case]
    human_review_required = severity is Severity.critical or best_case is CaseType.phishing_or_social_engineering

    if best_case is CaseType.other:
        confidence = 0.50
    else:
        total = len(KEYWORD_PATTERNS[best_case])
        ratio = best_score / total if total > 0 else 0
        confidence = round(0.50 + ratio * 0.45, 3)

    summary = _generate_summary(best_case, message)
    summary = _safety_filter(summary)

    return {
        "ticket_id": ticket_id,
        "case_type": best_case.value,
        "severity": severity.value,
        "department": department.value,
        "agent_summary": summary,
        "human_review_required": human_review_required,
        "confidence": confidence,
    }
