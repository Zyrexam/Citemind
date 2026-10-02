# CiteMind

A multi-agent AI research assistant that plans, retrieves, and writes cited reports.

**Status:** In development. API, web UI, and retrieval pipeline run locally under Docker Compose.

## What it does

Takes a research question, breaks it into focused sub-queries, searches the web, and
synthesises a structured report where every claim carries a numbered citation. Selecting a
citation opens the source and the opening of its text, so the answer can be checked rather
than trusted.

Example input: "When does retrieval beat fine-tuning?"

## Architecture

```
UI (Next.js)  -->  FastAPI Gateway  -->  Planner  -->  Retriever  -->  Writer
                        |
                  Guardrails wraps the whole run:
                  the query is screened in, the report inspected out
```

The RAGAS harness and the deterministic report verifiers live under `evals/`. `rag/` and
`agents/evaluator/` are empty placeholders. Qdrant is wired into compose but nothing in the
running API reads it -- retrieval is Tavily only.

## Services

| Service | Port | Description |
|---|---|---|
| API Gateway | 8123 | FastAPI REST + SSE streaming |
| Qdrant | 6333 | Vector database; not yet in the retrieval path |
| Web UI | 3000 | Next.js reader interface |

Port 8123 rather than 8000 because Docker Desktop's own host proxy occupies 8000 on this
machine. The api container still listens on 8000 internally; only the host mapping is
`8123:8000`.

## Tech Stack

- **Agents:** planner, retriever, and writer as plain modules over an OpenAI-compatible client
- **LLM:** Groq (`openai/gpt-oss-120b`) via `LLM_BASE_URL`; any OpenAI-compatible endpoint works
- **Retrieval:** Tavily search, `search_depth="advanced"`, 3 results per query, deduped by URL
- **API:** FastAPI, Uvicorn, SSE
- **UI:** Next.js 15 App Router, React 18, TailwindCSS 3.4, react-markdown + remark-gfm
- **Evals:** RAGAS harness with local `all-MiniLM-L6-v2` embeddings
- **Infra:** Docker, Docker Compose

## Testing

The suite is deliberately small. It covers the API contract, the report
verifiers, and the four pieces that have each been a real bug -- claims that
never parsed, arXiv ids that would not collapse, a cache that could hand a run
a different evidence pool, and a name check that missed the commonest case.
Run it with `pytest tests/ -v`.

No CI/CD. The workflow that existed was broken YAML and has been removed.

## The interface

Styled as a researcher's manuscript rather than a chat app.

- The question is set as the display title of the report it produces.
- Claims carry superscript **figures**. Selecting one opens the source in a margin column,
  draws a leader line from the figure into it, and shows the opening of the source text.
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
```

Qdrant is not needed to run the app. It is in `docker-compose.yml` for the hybrid-search
work that has not landed yet, and no code reads it.

## Test

```bash
# Health check
curl http://localhost:8123/health

# Agent query
curl -X POST "http://localhost:8123/agent/run" \
  -H "Content-Type: application/json" \
  -d '{"query":"Compare RAG evaluation approaches"}'

# Unit tests
pytest tests/ -v

# Typecheck and build the web app
cd apps/web && npx tsc --noEmit && npm run build
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | /health | Service health check |
| POST | /agent/run | Run a research query (sync), with claims and citations |

## Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```
GROQ_API_KEY=
TAVILY_API_KEY=
LLM_MODEL=openai/gpt-oss-120b
LLM_BASE_URL=https://api.groq.com/openai/v1
API_PORT=8000
LOG_LEVEL=info
```

Retrieval depth, all optional -- the defaults in `core/config.py` are what the numbers in
this README were measured at:

```
SUB_QUERIES=8
RESULTS_PER_QUERY=3
WRITER_INPUT_CHARS=12000
WRITER_CONTEXT_CHARS=2500
WRITER_MAX_TOKENS=3500
```

One variable is read straight from the environment rather than from settings:
`CITEMIND_CACHE=0` turns off the on-disk search cache. It is on by default, with no expiry,
so a long-lived cache will keep answering from whatever Tavily returned when each query was
first run.

The web app reads `NEXT_PUBLIC_API_URL`, defaulting to `http://localhost:8123`. Note that
`NEXT_PUBLIC_*` values are inlined at **build** time, so changing it requires a rebuild.

## Project Structure

```
citemind/
├── apps/
│   ├── api/          # FastAPI gateway
│   │   ├── main.py     # App entrypoint
│   │   ├── routes.py   # Endpoints
│   │   └── Dockerfile
│   └── web/          # Next.js UI
│       ├── app/        # Pages, global styles, layout
│       ├── components/ # UI primitives
│       ├── lib/        # cn() helper
│       └── Dockerfile
├── core/
│   ├── config.py       # Pydantic settings
│   ├── search_cache.py # On-disk search cache, keyed by query
│   └── urls.py         # URL canonicalisation, shared by retriever and verifier
├── agents/
│   ├── planner/      # Sub-query generation
│   ├── retriever/    # Tavily search and dedupe
│   └── writer/       # Report generation
├── guardrails/       # Input validation, PII scrubbing, output validation
├── evals/            # RAGAS harness + deterministic report verifiers
├── tests/            # Unit and integration tests
├── docker-compose.yml
├── pyproject.toml
└── .env
```

## Why This Project

Hands-on experience with:

- Multi-agent orchestration and prompt design
- RAG pipelines and retrieval strategies
- RESTful APIs with FastAPI and UI integration
- Docker-based packaging and deployment
- Typographic and interaction design for a reading tool