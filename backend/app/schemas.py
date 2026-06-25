from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Channel(str, Enum):
    app = "app"
    sms = "sms"
    call_center = "call_center"
    merchant_portal = "merchant_portal"


class Locale(str, Enum):
    bn = "bn"
    en = "en"
    mixed = "mixed"


class TicketRequest(BaseModel):
    ticket_id: str
    channel: Optional[Channel] = None
    locale: Optional[Locale] = None
    message: str


class CaseType(str, Enum):
    wrong_transfer = "wrong_transfer"
    payment_failed = "payment_failed"
    refund_request = "refund_request"
    phishing_or_social_engineering = "phishing_or_social_engineering"
    other = "other"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Department(str, Enum):
    customer_support = "customer_support"
    dispute_resolution = "dispute_resolution"
    payments_ops = "payments_ops"
    fraud_risk = "fraud_risk"


class TicketResponse(BaseModel):
    ticket_id: str
    case_type: CaseType
    severity: Severity
    department: Department
    agent_summary: str
    human_review_required: bool
    confidence: float = Field(ge=0.0, le=1.0)
