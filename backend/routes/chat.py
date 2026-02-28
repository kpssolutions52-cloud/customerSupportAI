"""
Chat route: POST /chat
Uses company context (JWT or API key), RAG, and streams response.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from auth import CompanyFromAuth
from database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from models import ChatLog

from agent import chat_stream as agent_chat_stream, chat as agent_chat

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@router.post("/chat")
async def chat_stream_endpoint(
    request: ChatRequest,
    company: CompanyFromAuth,
    db: Session = Depends(get_db),
):
    """
    Chat with the company's AI agent. Streams response (SSE).
    Authenticate with Bearer token (dashboard) or X-API-Key (API).
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    async def event_generator():
        full_response = []
        try:
            async for chunk in agent_chat_stream(company.id, request.message):
                if chunk:
                    full_response.append(chunk)
                    yield {"data": chunk}
            # Log to chat_logs after stream completes
            full = "".join(full_response)
            log = ChatLog(
                company_id=company.id,
                message=request.message,
                response=full,
            )
            db.add(log)
            db.commit()
        except Exception as e:
            yield {"data": f"[Error: {str(e)}]"}

    return EventSourceResponse(event_generator())


@router.post("/chat/completion", response_model=ChatResponse)
def chat_completion_endpoint(
    request: ChatRequest,
    company: CompanyFromAuth,
    db: Session = Depends(get_db),
):
    """
    Chat without streaming. Returns full response at once.
    Also logs to chat_logs.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    try:
        response = agent_chat(company.id, request.message)
        log = ChatLog(
            company_id=company.id,
            message=request.message,
            response=response,
        )
        db.add(log)
        db.commit()
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
