from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    stream: bool = False


class Citation(BaseModel):
    title: str
    url: str | None = None


class AgentResponse(BaseModel):
    query: str
    report: str
    citations: list[Citation] = []
    status: str = "ok"
