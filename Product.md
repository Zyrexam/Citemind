# PROJECT.md — ResearchMind

**Internal planning document**
Status: 🚧 Planning · Owner: [Your Name] · Last updated: [Date]

---

## 1. Objective

Build a production-grade multi-agent AI research assistant that demonstrates hands-on skills in:
- AI agent frameworks (Google ADK, CrewAI)
- RAG pipelines, vector DBs, prompt engineering
- FastAPI REST APIs + streaming
- Docker deployments and GitHub workflows
- Microservices and cloud deployment basics

**Success criteria:** A working end-to-end demo deployed publicly, with a clean repo, README, and a short technical write-up.

---

## 2. Scope

### In Scope
- Multi-agent orchestration (Planner, Retriever, Writer, Evaluator)
- Hybrid RAG (BM25 + dense) with re-ranking
- FastAPI gateway with REST + SSE
- Guardrails layer
- Docker + docker-compose
- Minimal React UI
- Eval harness (RAGAS)
- Public GitHub repo with CI

### Out of Scope (v1)
- Multi-tenant auth
- Billing / user accounts
- Fine-tuning custom models
- Mobile app

---

## 3. Milestones

| # | Milestone | Deliverable | Target |
|---|---|---|---|
| M1 | Repo scaffolding | Folder structure, README, CI skeleton | Week 1 |
| M2 | FastAPI gateway | `/agent/run`, `/health`, SSE stub | Week 1 |
| M3 | Planner agent | Google ADK planner with tool stubs | Week 2 |
| M4 | Retriever agent | Qdrant + hybrid search + re-rank | Week 2 |
| M5 | Writer + Evaluator | Structured output + citations | Week 3 |
| M6 | Guardrails | Input/output validation, PII scrub | Week 3 |
| M7 | Docker + compose | One-command full stack | Week 4 |
| M8 | React UI | Query box + streaming output | Week 4 |
| M9 | Eval harness | RAGAS metrics, benchmark report | Week 5 |
| M10 | Deploy + write-up | Public URL + blog post | Week 5 |

---

## 4. Task Breakdown

### M1 — Repo Scaffolding
- [ ] Create GitHub repo `researchmind`
- [ ] Add folder structure (apps, agents, core, rag, guardrails, infra, tests, evals)
- [ ] Add `.gitignore`, `.env.example`, `LICENSE` (MIT)
- [ ] Add `README.md` (public) and `PROJECT.md` (this file)
- [ ] Add GitHub Actions: lint + test on PR

### M2 — FastAPI Gateway
- [ ] `apps/api/main.py` with `/health`
- [ ] `POST /agent/run` — synchronous first
- [ ] `GET /agent/stream` — SSE
- [ ] Pydantic request/response schemas
- [ ] Unit tests with `pytest`

### M3 — Planner Agent
- [ ] Google ADK setup
- [ ] System prompt + tool declarations
- [ ] Decompose query → subtasks
- [ ] Unit test with mocked LLM

### M4 — Retriever Agent
- [ ] Qdrant local via Docker
- [ ] Ingestion script (PDFs / web)
- [ ] Chunking strategies (fixed, semantic)
- [ ] Embeddings (sentence-transformers + OpenAI)
- [ ] Hybrid search + cross-encoder re-rank

### M5 — Writer + Evaluator
- [ ] Writer prompt with citation format
- [ ] Structured output (JSON schema)
- [ ] Evaluator agent for factuality + coverage
- [ ] Retry loop on low score

### M6 — Guardrails
- [ ] Input validation (length, injection patterns)
- [ ] PII scrubbing (`presidio` or regex)
- [ ] Output schema enforcement
- [ ] Logging + rejection reasons

### M7 — Docker + Compose
- [ ] Multi-stage Dockerfile for API
- [ ] Dockerfile for UI
- [ ] `docker-compose.yml` (api, ui, qdrant, postgres)
- [ ] `.env` wiring
- [ ] One-command startup verified

### M8 — React UI
- [ ] Next.js app with Tailwind
- [ ] Query input + submit
- [ ] SSE consumption + live rendering
- [ ] Citations panel

### M9 — Eval Harness
- [ ] Golden Q&A set (20–30 examples)
- [ ] RAGAS: faithfulness, answer relevancy, context precision
- [ ] Benchmark report in `evals/results/`

### M10 — Deploy + Write-up
- [ ] Deploy API to Cloud Run / ECS
- [ ] Deploy UI to Vercel
- [ ] Record 60-sec demo GIF
- [ ] Publish blog post / LinkedIn write-up

---

## 5. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Agent framework churn (ADK is new) | Keep orchestration abstract behind an interface |
| LLM cost during dev | Use Ollama + small models locally |
| Scope creep | Freeze v1 scope; park extras in "Future" |
| Time (side project) | Timebox to 5 weeks; ship MVP first |

---

## 6. Dependencies

- API keys: OpenAI, Tavily (or SerpAPI)
- Local: Docker, Python 3.11+, Node 20+
- Accounts: GitHub, GCP or AWS, Vercel

---

## 7. Future (Post-v1)

- Auth + rate limiting
- Observability: Langfuse, OpenTelemetry
- Multi-user workspaces
- Agent framework plug-in interface
- Fine-tuned evaluator model

---

## 8. Definition of Done (v1)

- [ ] Public repo with clean README
- [ ] `docker-compose up` runs full stack locally
- [ ] Live deployed demo URL
- [ ] Eval report published
- [ ] Demo GIF + blog post published
- [ ] Resume bullet + interview story ready

---

Want me to also generate:
1. A **GitHub Issues template** mapped to these tasks?
2. A **`CONTRIBUTING.md`**?
3. A **resume bullet + interview story** based on this project?