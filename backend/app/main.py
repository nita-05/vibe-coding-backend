from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.settings import settings


app = FastAPI(title="Vibe Coding Backend", version="0.1.0")

origins = settings.cors_origin_list()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"] ,
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "vibe-coding-api"}


# Minimal prototype UI
_STATIC_DIR = Path(__file__).parent / "static"
_INDEX = _STATIC_DIR / "index.html"

if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/")
def root():
    if _INDEX.exists():
        return FileResponse(str(_INDEX))
    return JSONResponse({"ok": True, "message": "UI not built"})
