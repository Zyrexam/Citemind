# CiteMind

A multi-agent AI research assistant that plans, retrieves, and writes cited reports.

**Status:** In development. API, web UI, and retrieval pipeline run locally under Docker Compose.

## What it does

Takes a research question, breaks it into focused sub-queries, searches the web, and
synthesises a structured report where every claim carries a numbered citation. Selecting a
citation opens the source and **the passage the claim rests on**, so the answer can be
checked rather than trusted.

Example input: "When does retrieval beat fine-tuning?"

## Architecture

```
UI (Next.js)  -->  FastAPI Gateway  -->  Planner  -->  Retriever  -->  Writer
                                                              |
                                                        Guardrails
```

The evaluator agent and the RAGAS harness live under `agents/evaluator/` and `evals/`. The
Qdrant vector store is wired into compose but is not yet in the live retrieval path.

## Services

| Service | Port | Description |
|---|---|---|
| API Gateway | 8123 | FastAPI REST + SSE streaming |
| Qdrant | 6333 | Vector database for hybrid RAG |
| Web UI | 3000 | Next.js reader interface |

Port 8123 rather than 8000 because Docker Desktop's own host proxy occupies 8000 on this
machine. The api container still listens on 8000 internally; only the host mapping is
`8123:8000`.

## Tech Stack

- **Agents:** planner, retriever, and writer as plain modules over an OpenAI-compatible client
- **LLM:** Groq (`openai/gpt-oss-120b`) via `LLM_BASE_URL`; any OpenAI-compatible endpoint works
- **Retrieval:** Tavily search, `search_depth="advanced"`, 6 results per query, deduped by URL
- **API:** FastAPI, Uvicorn, SSE
- **UI:** Next.js 15 App Router, React 18, TailwindCSS 3.4, react-markdown + remark-gfm
- **Evals:** RAGAS harness with local `all-MiniLM-L6-v2` embeddings
- **Infra:** Docker, Docker Compose

No CI/CD. The workflow that existed was broken YAML and has been removed.

## The interface

Styled as a researcher's manuscript rather than a chat app.

- The question is set as the display title of the report it produces.
- Claims carry superscript **figures**. Selecting one opens the source in a margin column,
  draws a leader line from the figure into it, and shows the quoted passage.
- Sources are ranked beneath the question and cross-highlight with the figures.
- **Download** produces a `.md` file containing the question, the report, and a Sources
  section with links. **Copy** does the same to the clipboard.

No provider, model name, or API endpoint is shown anywhere in the interface.

## Run with Docker Compose

```bash
docker compose up --build
```

`--build` is required. The web source is copied into the image and compiled at image build
time — there is no bind mount, so a plain `docker compose up` will keep serving the previous
image.

Accessible at:

- http://localhost:8123 (API)
- http://localhost:6333 (Qdrant)
- http://localhost:3000 (Web UI)

## Run Locally

```bash
# API
uvicorn apps.api.main:app --host 0.0.0.0 --port 8123

# Web UI (from apps/web/)
npm run dev

# Qdrant
docker run -p 6333:6333 qdrant/qdrant
```

## Test

```bash
# Health check
curl http://localhost:8123/health

# Agent query
curl -X POST "http://localhost:8123/agent/run" \
  -H "Content-Type: application/json" \
  -d '{"query":"Compare RAG evaluation approaches"}'

# Streaming query
curl "http://localhost:8123/agent/stream?query=test+query"

# Unit tests
pytest tests/ -v

# Typecheck and build the web app
cd apps/web && npx tsc --noEmit && npm run build
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | /health | Service health check |
| POST | /agent/run | Run a research query (sync) |
| GET | /agent/stream | Stream a research query (SSE) |

## Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```
GROQ_API_KEY=
TAVILY_API_KEY=
OPENAI_API_KEY=
HF_TOKEN=
QDRANT_URL=http://localhost:6333
LLM_MODEL=openai/gpt-oss-120b
LLM_BASE_URL=https://api.groq.com/openai/v1
API_PORT=8123
LOG_LEVEL=info
```

The web app reads `NEXT_PUBLIC_API_URL`, defaulting to `http://localhost:8123`. Note that
`NEXT_PUBLIC_*` values are inlined at **build** time, so changing it requires a rebuild.

## Project Structure

```
citemind/
├── apps/
│   ├── api/          # FastAPI gateway
│   │   ├── main.py     # App entrypoint
│   │   └── routes.py   # Endpoints
│   └── web/          # Next.js UI
│       ├── app/        # Pages, global styles, layout
│       └── components/ # UI primitives
├── core/
│   └── config.py     # Pydantic settings
├── agents/
│   ├── planner/      # Sub-query generation
│   ├── retriever/    # Tavily search and dedupe
│   ├── writer/       # Report generation
│   └── evaluator/    # Reserved
├── guardrails/       # Input validation, PII scrubbing, output validation
├── tests/            # Unit and integration tests
├── evals/            # RAGAS evaluation harness
├── infra/            # Container definitions
├── docker-compose.yml
├── pyproject.toml
└── .env
```

## Roadmap

- [x] Scaffolding and FastAPI gateway
- [x] Groq LLM wiring
- [x] Planner agent
- [x] Retriever agent with Tavily
- [x] Writer agent with citations
- [x] Guardrails layer
- [x] SSE streaming endpoint
- [x] Docker + compose
- [x] Next.js UI, redesigned as a cited-manuscript reader
- [x] Downloadable report with sources
- [ ] Run the eval harness and publish real scores
- [ ] Deploy api to Cloud Run and web to Vercel
- [ ] Qdrant wired into the live retrieval path for hybrid search
- [ ] Auth, rate limiting, observability

## Why This Project

Hands-on experience with:

- Multi-agent orchestration and prompt design
- RAG pipelines and retrieval strategies
- RESTful APIs with FastAPI and UI integration
- Docker-based packaging and deployment
- Typographic and interaction design for a reading tool