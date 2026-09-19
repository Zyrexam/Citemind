import asyncio
import json
import logging

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from apps.api.schemas import AgentRequest, AgentResponse, Citation

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/agent/run", response_model=AgentResponse)
async def run_agent(req: AgentRequest) -> AgentResponse:
    logger.info("agent run: %s", req.query[:80])
    # TODO(M3-M5): replace with real planner/retriever/writer flow
    await asyncio.sleep(0.3)
    return AgentResponse(
        query=req.query,
        report=f"(stub) Research report for: {req.query}",
        citations=[Citation(title="Example source", url="https://example.com")],
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
