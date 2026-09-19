# ResearchMind

**A multi-agent AI research assistant that plans, retrieves, reasons, and writes cited reports.**

> 🚧 **Status: In Development** — This is a planned project. Build log and progress updates coming soon.

---

## 🎯 Goal

Build a production-grade AI agent system that takes a research question, autonomously plans subtasks, retrieves information from the web and a private knowledge base, reasons over findings, and returns a structured, cited report — streamed live to a UI.

**Example:**
```
Input:  "Compare the latest approaches to RAG evaluation for enterprise use."
Output: A cited report with a clear recommendation.
```

---

## 🧩 Planned Features

- 🧠 **Multi-agent orchestration** — Planner, Retriever, Writer, Evaluator
- 📚 **Hybrid RAG** — BM25 + dense retrieval with re-ranking
- 🛡️ **Guardrails** — Input validation, output schema enforcement, PII scrubbing
- ⚡ **FastAPI gateway** — REST + SSE streaming
- 🐳 **Dockerized** — One command to run the full stack
- 🔌 **Model-agnostic** — OpenAI, Hugging Face, or local Llama via Ollama

---

## 🏗️ Planned Architecture

```
UI ──► FastAPI ──► Planner ──► Retriever ──► Writer ──► Evaluator
                       │            │            │
                   Guardrails   Vector DB    Prompt Engine
```

---

## 🛠️ Planned Tech Stack

| Layer | Tools |
|---|---|
| Agents | Google ADK, CrewAI |
| LLM | OpenAI, Hugging Face, Ollama |
| RAG | LangChain, Qdrant, sentence-transformers |
| API | FastAPI, Uvicorn, SSE |
| UI | Next.js, Tailwind |
| Infra | Docker, GitHub Actions |

---

## 📁 Planned Structure

```
researchmind/
├── apps/api/          # FastAPI gateway
├── apps/web/          # Next.js UI
├── agents/            # planner, retriever, writer, evaluator
├── core/              # shared Python library
├── rag/               # chunking, embeddings, vector store
├── guardrails/        # validation & safety
├── infra/             # docker-compose, k8s
├── tests/  evals/
└── README.md
```

---

## 🗺️ Roadmap

- [ ] Project setup + repo scaffolding
- [ ] FastAPI gateway with `/agent/run`
- [ ] Planner agent (Google ADK)
- [ ] Retriever agent + Qdrant integration
- [ ] Writer agent with prompt templates
- [ ] Guardrails layer
- [ ] Streaming (SSE) support
- [ ] Docker + docker-compose
- [ ] React UI
- [ ] Eval harness (RAGAS)
- [ ] Auth, rate limiting, observability

---

## 📌 Why This Project

This project is being built to demonstrate hands-on, end-to-end experience with:
- AI agent frameworks (Google ADK, CrewAI)
- RAG pipelines, vector DBs, and prompt engineering
- RESTful APIs with FastAPI and UI integration
- Docker-based deployment and GitHub workflows
- Microservices design and production-grade AI systems

