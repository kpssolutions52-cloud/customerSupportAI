"""
Customer Support AI - FastAPI backend.
Exposes POST /chat (streaming + non-streaming), GET /health, and knowledge base ingestion.
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from agent import chat, chat_stream
from db import add_documents_to_kb

# Load environment variables from .env
load_dotenv()


# Optional: run logic on startup (e.g. ensure vector store exists)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure Chroma persist directory exists
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    os.makedirs(persist_dir, exist_ok=True)
    yield
    # Shutdown: nothing to clean up for now
    pass


app = FastAPI(
    title="Customer Support AI API",
    description="Production-ready Customer Support AI Agent with RAG",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow frontend (Next.js) to call the API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response models ---

class ChatRequest(BaseModel):
    """Body for POST /chat."""
    message: str


class ChatResponse(BaseModel):
    """Non-streaming response for POST /chat when stream=false."""
    response: str


class IngestRequest(BaseModel):
    """Body for POST /ingest: add documents to the knowledge base."""
    documents: list[str]
    metadatas: list[dict] | None = None


# --- Health check ---

@app.get("/health")
def health():
    """
    Health check endpoint for load balancers and monitoring.
    """
    return {"status": "ok", "service": "customer-support-ai"}


# --- Chat: streaming (default) and non-streaming ---

@app.post("/chat")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Chat with the AI agent. Streams the response in real time using Server-Sent Events (SSE).
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    async def event_generator():
        try:
            async for chunk in chat_stream(request.message):
                if chunk:
                    # SSE format: data line + blank line
                    yield {"data": chunk}
        except Exception as e:
            yield {"data": f"[Error: {str(e)}]"}

    return EventSourceResponse(event_generator())


@app.post("/chat/completion", response_model=ChatResponse)
def chat_completion_endpoint(request: ChatRequest):
    """
    Chat with the AI agent. Returns the full response at once (no streaming).
    Use this when you don't need real-time token streaming.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    try:
        response = chat(request.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Knowledge base ingestion ---

@app.post("/ingest")
def ingest_documents(request: IngestRequest):
    """
    Add documents to the knowledge base. Text is split into chunks, embedded, and stored in Chroma.
    """
    if not request.documents:
        raise HTTPException(status_code=400, detail="documents list cannot be empty")
    try:
        count = add_documents_to_kb(request.documents, request.metadatas)
        return {"status": "ok", "chunks_added": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000 ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
