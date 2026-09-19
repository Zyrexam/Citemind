from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routes import router
from core.config import settings
from core.logging import setup_logging

setup_logging()

app = FastAPI(title="ResearchMind API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "port": settings.api_port}


app.include_router(router)
