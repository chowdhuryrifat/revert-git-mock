import asyncio
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .schemas import TicketRequest
from .classifier import classify
from .database import save_ticket_request, save_ticket_response, peek_next_ticket_id

load_dotenv()
logging.basicConfig(level=logging.INFO)
app = FastAPI(title="QueueStorm Ticket Classifier")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "queuestorm-classifier"}


@app.get("/next-ticket-id")
async def next_ticket_id():
    tid = await asyncio.to_thread(peek_next_ticket_id)
    return {"ticket_id": tid}


@app.post("/sort-ticket")
async def sort_ticket(request: TicketRequest):
    result = classify(request.ticket_id, request.message)

    request_id, tid = await asyncio.to_thread(
        save_ticket_request,
        channel=request.channel.value if request.channel else None,
        locale=request.locale.value if request.locale else None,
        message=request.message,
    )

    result["ticket_id"] = tid

    if request_id is not None:
        await asyncio.to_thread(
            save_ticket_response,
            ticket_request_id=request_id,
            ticket_id=tid,
            case_type=result["case_type"],
            severity=result["severity"],
            department=result["department"],
            agent_summary=result["agent_summary"],
            human_review_required=result["human_review_required"],
            confidence=result["confidence"],
        )

    return result
