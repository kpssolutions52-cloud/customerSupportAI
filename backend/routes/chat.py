"""
Chat route: POST /chat
Multi-tenant: each tenant is isolated by tenant_id + API key / JWT.

Input (body):
- tenant_id
- message

Security:
- Tenant API key via X-API-Key header (or JWT for dashboard users).
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session

from auth import TenantFromAuth
from database import get_db
from models import ChatLog
from agent import chat_stream as agent_chat_stream, chat as agent_chat

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    tenant_id: str
    message: str


class ChatResponse(BaseModel):
    response: str


@router.post("/chat")
async def chat_stream_endpoint(
    request: ChatRequest,
    tenant: TenantFromAuth,
    db: Session = Depends(get_db),
):
    """
    Chat with the tenant's AI agent. Streams response (SSE).
    We verify tenant_id in the body matches the authenticated tenant.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if str(tenant.id) != request.tenant_id:
        raise HTTPException(status_code=403, detail="tenant_id does not match credentials")

    async def event_generator():
        full_response: list[str] = []
        try:
            async for chunk in agent_chat_stream(request.tenant_id, request.message, db=db):
                if chunk:
                    full_response.append(chunk)
                    yield {"data": chunk}
            full = "".join(full_response)
            log = ChatLog(
                tenant_id=request.tenant_id,
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
    tenant: TenantFromAuth,
    db: Session = Depends(get_db),
):
    """
    Chat without streaming. Returns full response at once.
    Also logs to chat_logs.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if str(tenant.id) != request.tenant_id:
        raise HTTPException(status_code=403, detail="tenant_id does not match credentials")
    try:
        response = agent_chat(request.tenant_id, request.message, db=db)
        log = ChatLog(
            tenant_id=request.tenant_id,
            message=request.message,
            response=response,
        )
        db.add(log)
        db.commit()
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
