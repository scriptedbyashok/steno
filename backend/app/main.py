from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import admin, attempts, auth, dictations, rankings, users

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

app = FastAPI(title="Steno Practice API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the deployed frontend origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(dictations.router)
app.include_router(rankings.router)
app.include_router(attempts.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# Mounted last so /api/* and /health above still match first.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
