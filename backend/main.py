"""
Multi-tenant Customer Support AI — FastAPI application.
Clean architecture: routes in /routes, auth/db/agent in backend root.
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routes import auth, chat, upload, admin, webhook

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables and Chroma dir on startup."""
    init_db()
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    os.makedirs(persist_dir, exist_ok=True)
    yield


app = FastAPI(
    title="Customer Support AI API",
    description="Multi-tenant Customer Support AI with RAG, JWT, API keys",
    version="2.0.0",
    lifespan=lifespan,
)

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

# --- Routes ---
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(admin.router)
app.include_router(webhook.router)


@app.get("/health")
def health():
    """Health check for load balancers."""
    return {"status": "ok", "service": "customer-support-ai"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
