import asyncio
import json
import logging

from fastapi import APIRouter
from openai import OpenAI
from sse_starlette.sse import EventSourceResponse

from apps.api.schemas import AgentRequest, AgentResponse, Citation
from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

client = OpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.groq_api_key,
)


@router.post("/agent/run", response_model=AgentResponse)
async def run_agent(req: AgentRequest) -> AgentResponse:
    logger.info("agent run via Groq: %s", req.query[:80])

    # ponytail: sync LLM call blocks the event loop until a real multi-agent
    # flow exists; swap to AsyncOpenAI / run_in_threadpool when concurrency matters.
    try:
        completion = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "You are a helpful research assistant."},
                {"role": "user", "content": req.query},
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        report = completion.choices[0].message.content
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        report = f"(error) Could not generate report: {e}"

    return AgentResponse(
        query=req.query,
        report=report,
        citations=[Citation(title="Groq Inference", url="https://groq.com")],
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
