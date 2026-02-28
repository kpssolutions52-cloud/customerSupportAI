# Customer Support AI

Production-ready **Customer Support AI Agent** SaaS: chat UI, RAG over your knowledge base (Chroma), and fallback to human support. Built with **Next.js**, **FastAPI**, **OpenAI**, and **LangChain**.

## Features

- **Chat interface** – Send messages and get AI responses in **real time** (streaming).
- **Knowledge base** – Load company documents; embeddings stored in **Chroma**; answers use **RAG**.
- **AI agent** – Answers from the knowledge base; if no relevant context, says *"I will connect you to human support."*
- **API** – `POST /chat` (streaming), `POST /chat/completion`, `GET /health`, `POST /ingest`.

## Tech stack

| Layer   | Stack        |
|--------|--------------|
| Frontend | Next.js, React, TailwindCSS |
| Backend  | Python, FastAPI             |
| AI       | OpenAI API (GPT-4o), LangChain |
| Vector DB | Chroma (local persistence)  |

## Project structure

```
customerSupportAI/
├── frontend/          # Next.js app
│   ├── app/
│   ├── lib/
│   └── ...
├── backend/
│   ├── main.py        # FastAPI app, routes
│   ├── agent.py       # RAG chain, streaming
│   ├── db.py          # Chroma + embeddings
│   ├── seed_kb.py    # Seed sample docs
│   ├── requirements.txt
│   └── .env.example
└── README.md
```

## Run locally

### 1. Backend (Python)

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...

# Seed sample knowledge base (optional but recommended)
python seed_kb.py

# Start API
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- API: **http://localhost:8000**
- Docs: **http://localhost:8000/docs**

### 2. Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

- App: **http://localhost:3000**

### 3. Use the app

1. Open http://localhost:3000.
2. Type a question (e.g. “What are your return policies?” or “When are you open?”).
3. The AI streams the answer from the knowledge base or replies with “I will connect you to human support” when there’s no relevant context.

## Environment

**Backend (backend/.env)**

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `OPENAI_CHAT_MODEL` | No | Default: `gpt-4o` |
| `OPENAI_EMBEDDING_MODEL` | No | Default: `text-embedding-3-small` |
| `CHROMA_PERSIST_DIR` | No | Default: `./chroma_db` |

**Frontend (frontend/.env.local)**

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | No | Backend URL; default: `http://localhost:8000` |

## API overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/chat` | Chat with **streaming** (SSE) |
| POST | `/chat/completion` | Chat, full response in one shot |
| POST | `/ingest` | Add documents to the knowledge base |

**POST /chat** body: `{ "message": "Your question" }`  
**POST /ingest** body: `{ "documents": ["text1", "text2"], "metadatas": null }`

## Adding your own documents

1. **Via API:** `POST http://localhost:8000/ingest` with JSON body:
   ```json
   { "documents": ["First document text...", "Second document..."] }
   ```
2. **Via script:** Add text content to a list in a Python script and call `add_documents_to_kb(texts)` from `db.py` (see `seed_kb.py`).

## Requirements

- **Backend:** Python 3.10+
- **Frontend:** Node.js 18+
- **OpenAI** API key

## License

MIT.
