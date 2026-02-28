# Customer Support AI — Multi-tenant SaaS

Production-ready **multi-tenant Customer Support AI Agent** SaaS: companies sign up, upload knowledge bases, get their own AI agent and API key. JWT auth, PostgreSQL, Chroma (RAG), Stripe-ready, WhatsApp webhook.

## Features

- **Multi-tenant:** Each company has its own knowledge base, API key, and chat logs.
- **Auth:** Signup, login, JWT. Passwords hashed with bcrypt.
- **Knowledge base:** Upload documents (dashboard or API); stored in Chroma per company.
- **AI agent:** RAG with GPT-4o; fallback: *"I will connect you to human support."*
- **API key:** Per company for server-to-server and WhatsApp webhook.
- **Admin:** View companies and usage (header `X-Admin-Secret`).
- **Deployment:** Docker and docker-compose (PostgreSQL + backend + frontend).

## Tech stack

| Layer     | Stack |
|----------|--------|
| Frontend | Next.js 14, React, TailwindCSS, ShadCN UI |
| Backend  | Python, FastAPI |
| AI       | OpenAI GPT-4o, LangChain, Chroma |
| Database | PostgreSQL (users, companies, documents, chat_logs) |
| Auth     | JWT (python-jose), passlib (bcrypt) |
| Payments | Stripe integration ready (env + dependency) |

## Project structure

```
/backend
  main.py           # FastAPI app, lifespan, CORS
  models.py         # SQLAlchemy: Company, User, Document, ChatLog
  database.py       # PostgreSQL engine, session, init_db
  auth.py           # JWT, password hash, get_current_user, get_company_for_request
  agent.py          # RAG per company (Chroma + GPT-4o)
  db.py             # Chroma vector store per company
  routes/
    auth.py         # POST /auth/signup, /auth/login, GET /auth/me
    chat.py         # POST /chat (streaming), POST /chat/completion
    upload.py       # POST /upload, POST /upload/text
    admin.py        # GET /admin/companies, GET /admin/usage
    webhook.py      # POST /webhook/whatsapp
/frontend
  app/              # Next.js App Router
    page.tsx        # Landing
    login/          # Login page
    signup/         # Signup page
    dashboard/      # Dashboard layout, Chat, Upload
  components/ui/    # ShadCN-style: Button, Input, Card, Label
  lib/              # api.ts, utils.ts
```

## Database tables

- **users** — id, email, password (hashed), company_id
- **companies** — id, name, api_key
- **documents** — id, company_id, content
- **chat_logs** — id, company_id, message, response

## API endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /health | — | Health check |
| POST | /auth/signup | — | Create company + user |
| POST | /auth/login | — | Get JWT |
| GET | /auth/me | Bearer | Current user + company + API key |
| POST | /chat | Bearer or X-API-Key | Streaming chat |
| POST | /chat/completion | Bearer or X-API-Key | Non-streaming chat |
| POST | /upload | Bearer | Upload file (.txt, .md, .csv) |
| POST | /upload/text | Bearer | Add text to KB (JSON body) |
| GET | /admin/companies | X-Admin-Secret | List companies + usage |
| GET | /admin/usage | X-Admin-Secret | Totals |
| POST | /webhook/whatsapp | X-API-Key | WhatsApp webhook |

## Environment (.env)

```env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/customer_support_ai
JWT_SECRET=your-long-random-secret
STRIPE_SECRET=sk_test_...          # optional
ADMIN_SECRET=your-admin-secret     # optional, for /admin/*
```

## Run locally

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env     # set OPENAI_API_KEY, DATABASE_URL, JWT_SECRET
# Start PostgreSQL (e.g. Docker: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16-alpine)
# Create DB: createdb customer_support_ai  (or use Docker postgres default)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- App: http://localhost:3000  
- API docs: http://localhost:8000/docs  

### Docker

```bash
cp backend/.env.example backend/.env   # set OPENAI_API_KEY, JWT_SECRET
docker-compose up -d
```

- Frontend: http://localhost:3000  
- Backend: http://localhost:8000  
- PostgreSQL: localhost:5432  

## Security

- Passwords hashed with bcrypt (passlib).
- Endpoints protected by JWT or API key; admin by `X-Admin-Secret`.
- API keys are generated securely per company (signup).

## Deployment (AWS EC2 / Docker)

- **Backend:** Use `backend/Dockerfile`; set env (e.g. `DATABASE_URL` to RDS).
- **Frontend:** Use `frontend/Dockerfile`; set `NEXT_PUBLIC_API_URL` to your backend URL.
- **PostgreSQL:** Run separately (RDS or container); ensure `DATABASE_URL` is correct.
- **Stripe:** Set `STRIPE_SECRET` (and webhook secret when you add billing).

## WhatsApp

- `POST /webhook/whatsapp` expects header `X-API-Key` (company API key).
- Body: `{ "message": "user text" }` or Meta webhook payload; response includes `reply` for your bot to send back.

---

**License:** MIT.
