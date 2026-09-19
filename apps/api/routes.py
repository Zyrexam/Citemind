import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from agents.planner.agent import plan
from agents.retriever.agent import retrieve
from agents.writer.agent import write
from apps.api.schemas import AgentRequest, AgentResponse, Citation
from guardrails.input import validate_input
from guardrails.output import validate_output
from guardrails.pii import scrub_pii

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/agent/run", response_model=AgentResponse)
async def run_agent(req: AgentRequest) -> AgentResponse:
    ok, err = validate_input(req.query)
    if not ok:
        raise HTTPException(status_code=400, detail=err)

    clean_query = scrub_pii(req.query)

    sub_queries = plan(clean_query)
    logger.info("planner produced %d queries", len(sub_queries))

    sources = retrieve(sub_queries, max_results=3)
    logger.info("retriever returned %d sources", len(sources))

    report = write(clean_query, sources)

    ok, err = validate_output(report)
    if not ok:
        logger.warning("output validation failed: %s", err)
        report = "(Report generation failed validation.)"

    citations = [Citation(title=s["title"], url=s["url"]) for s in sources]

    return AgentResponse(
        query=clean_query,
        report=report,
        citations=citations,
    )


@router.get("/agent/stream")
async def stream_agent(query: str):
    async def event_gen():
        tokens = f"(stub) Streaming answer for: {query}".split()
        for tok in tokens:
            yield {"event": "token", "data": json.dumps({"token": tok + " "})}
            await asyncio.sleep(0.05)
        yield {"event": "done", "data": json.dumps({"status": "ok"})}

    return EventSourceResponse(event_gen())
