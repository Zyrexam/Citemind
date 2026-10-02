import logging

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from agents.planner.agent import plan
from agents.retriever.agent import retrieve
from agents.writer.agent import write
from core.config import settings
from guardrails import scrub_pii, validate_input, validate_output

logger = logging.getLogger(__name__)
router = APIRouter()


class AgentRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)


class Citation(BaseModel):
    title: str
    url: str | None = None
    snippet: str | None = None


class Claim(BaseModel):
    claim: str
    source: int
    quote: str


class AgentResponse(BaseModel):
    query: str
    report: str
    citations: list[Citation] = []
    claims: list[Claim] = []
    status: str = "ok"


@router.post("/agent/run", response_model=AgentResponse)
async def run_agent(req: AgentRequest) -> AgentResponse:
    ok, err = validate_input(req.query)
    if not ok:
        raise HTTPException(status_code=400, detail=err)

    clean_query = scrub_pii(req.query)

    # these all block, and the writer sleeps 65s between retries
    sub_queries = await run_in_threadpool(plan, clean_query)
    logger.info("planner produced %d queries", len(sub_queries))

    sources = await run_in_threadpool(
        retrieve, sub_queries, max_results=settings.results_per_query)
    logger.info("retriever returned %d sources", len(sources))

    trace: dict = {}
    try:
        report = await run_in_threadpool(write, clean_query, sources, trace)
    except RuntimeError as e:
        logger.error("writer failed: %s", e)
        raise HTTPException(status_code=503, detail=str(e)) from e

    ok, err = validate_output(report)
    if not ok:
        logger.warning("output validation failed: %s", err)
        raise HTTPException(status_code=502, detail=err)

    citations = [
        Citation(
            title=s["title"],
            url=s["url"],
            snippet=(s.get("content") or "")[:600] or None,
        )
        for s in sources
    ]
    claims = [Claim(**c) for c in trace.get("claims", [])]

    return AgentResponse(
        query=clean_query,
        report=report,
        citations=citations,
        claims=claims,
    )
