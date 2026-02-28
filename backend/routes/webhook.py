"""
WhatsApp webhook: POST /webhook/whatsapp
Receives incoming WhatsApp messages and responds using the company's AI agent.
Company is identified by a query param or header (e.g. company_id or api_key).
"""

import os
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Company
from auth import get_company_by_api_key
from agent import chat as agent_chat

router = APIRouter(prefix="/webhook", tags=["webhook"])

# WhatsApp Cloud API sends JSON with structure: { "messages": [...] }
# For a minimal webhook we accept: X-API-Key to identify company, body with "message" or "messages"


class WhatsAppIncoming(BaseModel):
    """Minimal shape: one message text."""
    message: str | None = None
    messages: list[dict] | None = None  # raw from Meta
    company_id: str | None = None


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(None),
):
    """
    Webhook for WhatsApp integration.
    - Identify company via header X-API-Key (or body company_id if you use custom routing).
    - Body can be { "message": "user text" } or Meta's webhook payload.
    - Responds with AI reply using company's knowledge base.
    """
    if not x_api_key:
        raise HTTPException(401, detail="X-API-Key required")
    company = get_company_by_api_key(db, x_api_key.strip())
    if not company:
        raise HTTPException(401, detail="Invalid API key")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail="Invalid JSON")
    # Extract user message text
    message_text = body.get("message")
    if not message_text and body.get("messages"):
        msgs = body["messages"]
        if msgs and isinstance(msgs[0], dict):
            message_text = msgs[0].get("text", {}).get("body") if isinstance(msgs[0].get("text"), dict) else str(msgs[0].get("text", ""))
    if not message_text or not str(message_text).strip():
        return {"ok": True, "reply": None}
    # Get AI response for this company
    reply = agent_chat(company.id, str(message_text).strip())
    # Return reply so your WhatsApp sender can send it back to the user
    return {"ok": True, "reply": reply}
