from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import api_router
from app.core.config import settings
from app.websocket.handler import websocket_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Secure Messenger", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

app.websocket("/ws")(websocket_endpoint)

# Serve frontend: when running in Docker, frontend may be at /app/frontend; otherwise ../frontend from backend/
_frontend_candidates = [
    Path(__file__).resolve().parent.parent / "frontend",
    Path(__file__).resolve().parent.parent.parent / "frontend",
]
frontend_path = next((p for p in _frontend_candidates if p.exists()), None)
if frontend_path is not None:
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
