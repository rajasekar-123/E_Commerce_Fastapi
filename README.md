# E-Commerce FastAPI + AI/RAG Application

> **Migrated from Spring Boot → FastAPI** with SOLID architecture, AI shopping assistant, and RAG pipeline.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        React Frontend (Vite)                        │
│   Home │ Search │ Product │ Cart │ Checkout │ Orders │ AI Chat      │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ fetch() (JWT Bearer)
┌───────────────────────────▼─────────────────────────────────────────┐
│                    FastAPI Backend                                   │
│                                                                     │
│  Presentation Layer (Routes) — thin, no business logic              │
│       │                                                             │
│  Application Layer (Services) — all business rules here             │
│       │                          │                                  │
│  Domain Layer         AI Services (AssistantService)                │
│  (Entities + Interfaces)    │         │         │                   │
│       │                   RAG      Tools       LLM                  │
│  Infrastructure Layer   ChromaDB  PostgreSQL  Gemini/Groq/Ollama    │
│  (SQLAlchemy Repos, LLM Providers, ChromaDB, Redis)                 │
│       │                                                             │
│  PostgreSQL          Redis (chat history)    ChromaDB               │
└─────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI 0.115+, Python 3.11 |
| ORM | SQLAlchemy 2.x (async) + asyncpg |
| Migrations | Alembic |
| Database | PostgreSQL 16 |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Validation | Pydantic v2 |
| Payment | Razorpay (Python SDK) |
| Email | fastapi-mail (Gmail SMTP) |
| AI/LLM | Gemini / Groq / Ollama (abstracted) |
| Embeddings | sentence-transformers (local) or Gemini |
| Vector DB | ChromaDB |
| Chat Memory | Redis |
| Frontend | React + Vite + TailwindCSS + Zustand |
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions |

## Project Structure

```
ecommerce-fastapi/
├── backend/
│   ├── app/
│   │   ├── core/           # config, security, exceptions, logging, dependencies
│   │   ├── database/       # SQLAlchemy base, session factory
│   │   ├── domain/
│   │   │   ├── entities/   # SQLAlchemy 2.x models (User, Product, Order, ...)
│   │   │   └── interfaces/ # Abstract repository + AI provider interfaces
│   │   ├── infrastructure/
│   │   │   ├── repositories/  # SQLAlchemy implementations
│   │   │   ├── llm/           # Gemini, Groq, Ollama providers
│   │   │   ├── embeddings/    # Local + Gemini embedding providers
│   │   │   └── vectorstore/   # ChromaDB implementation
│   │   ├── application/
│   │   │   ├── services/   # AuthService, ProductService, OrderService, ...
│   │   │   └── ai/         # AssistantService, RAGService, IngestionService, ToolService
│   │   ├── schemas/        # Pydantic v2 request/response schemas
│   │   ├── presentation/
│   │   │   └── routes/     # FastAPI routers (thin HTTP layer)
│   │   └── main.py
│   ├── alembic/
│   │   └── versions/001_initial_schema.py
│   ├── tests/
│   │   ├── unit/           # Service-level tests with mocked repos
│   │   └── integration/    # API-level tests (WIP)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── services/api.js    # native fetch() wrapper (replaces Axios)
│   │   ├── pages/AIChat.jsx   # AI shopping assistant UI
│   │   └── components/AIChatButton.jsx
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── .github/workflows/
    ├── ci.yml              # Lint + Test + Docker build
    └── cd.yml              # Build + Push + SSH deploy
```

## Quick Start (Docker Compose)

### 1. Clone and configure

```bash
git clone <your-repo>
cd ecommerce-fastapi/backend
cp .env.example .env
# Edit .env with your actual API keys
```

### 2. Generate a secure SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Start all services

```bash
cd ecommerce-fastapi
docker compose up -d
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- ChromaDB: http://localhost:8001

### 4. Run migrations (auto-run on container start)

```bash
docker compose exec backend alembic upgrade head
```

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # fill in values

# Start PostgreSQL, Redis, ChromaDB separately (or via docker compose)
docker compose up postgres redis chromadb -d

# Run migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
# Create .env.local:
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

## API Endpoints

### Public
| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login → JWT |
| GET | `/products` | List active products |
| GET | `/products/search` | Search/filter products |
| GET | `/products/{id}` | Product details |
| GET | `/categories` | List categories |
| GET | `/products/{id}/reviews` | Product reviews |

### Authenticated (USER role)
| Method | Path | Description |
|---|---|---|
| GET | `/auth/me` | Current user profile |
| GET | `/orders` | My orders |
| POST | `/orders` | Create order |
| GET | `/users/addresses` | My addresses |
| POST | `/users/addresses` | Add address |
| POST | `/products/{id}/reviews` | Add review |
| POST | `/ai/chat` | AI assistant chat |

### Admin
| Method | Path | Description |
|---|---|---|
| POST/PUT/DELETE | `/admin/products` | Product CRUD |
| POST/PUT/DELETE | `/admin/categories` | Category CRUD |
| GET/PUT | `/admin/orders` | Order management |
| GET | `/admin/dashboard` | Dashboard stats |
| POST | `/documents/upload` | Upload RAG document |

## AI Shopping Assistant

The assistant supports:
- **Product search** — "Find me headphones under ₹5000"
- **Order queries** — "What's the status of my latest order?"
- **Document-grounded answers** — using RAG over uploaded policy/product docs
- **Multi-turn conversation** — session history persisted in Redis

### Uploading Knowledge Base Documents (Admin)

```bash
curl -X POST http://localhost:8000/documents/upload \
  -H "Authorization: Bearer <admin_token>" \
  -F "file=@shipping-policy.pdf"
```

## Environment Variables

See [`.env.example`](backend/.env.example) for complete documentation of all variables.

Key variables:
- `DATABASE_URL` — PostgreSQL async URL
- `SECRET_KEY` — JWT signing secret (generate with `secrets.token_hex(32)`)
- `LLM_PROVIDER` — `gemini` | `groq` | `ollama`
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` — Razorpay credentials
- `GEMINI_API_KEY` — Google AI Studio API key

## Running Tests

```bash
cd backend
pytest tests/unit/ -v --cov=app --cov-report=term-missing
```

## CI/CD

### CI (GitHub Actions)
Triggers on push/PR to `main`:
- Python lint (ruff) + unit tests with coverage
- Node.js build validation
- Docker build test

### CD (GitHub Actions)
Triggers after CI passes on `main`:
- Build + push Docker images to Docker Hub
- SSH deploy to VPS with `docker compose pull && up -d`

**Required GitHub Secrets:**
```
DOCKER_USERNAME, DOCKER_PASSWORD
SSH_HOST, SSH_USER, SSH_PRIVATE_KEY
VITE_API_URL
```

## Spring Boot → FastAPI Migration Reference

| Spring Boot | FastAPI Equivalent |
|---|---|
| `@RestController` | FastAPI Router (thin, no logic) |
| `@Service` | Application Service class |
| `@Repository` / `JpaRepository` | `IXxxRepository` interface + `SQLAlchemyXxxRepository` |
| `@Entity` | SQLAlchemy `Mapped` model |
| `DTO` | Pydantic schema |
| `Spring Security` | `python-jose` + `passlib` + `get_current_user()` |
| `@Async` | `BackgroundTasks` |
| `application.yml` | `.env` + `pydantic-settings` |
| `@Valid` | Pydantic v2 validators |
| `@ExceptionHandler` | FastAPI exception handlers |
| `MySQL` | PostgreSQL |
| `Axios` (frontend) | native `fetch()` |
#   E _ C o m m e r c e _ F a s t a p i  
 