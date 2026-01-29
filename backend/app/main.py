from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.database.database import init_db
from app.settings import settings


app = FastAPI(title="Vibe Studio Backend", version="0.1.0")

origins = settings.cors_origin_list()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/health")
def health():
    return {"status": "healthy", "service": "vibe-coding-api"}


# Serve frontend build (if exists) or fallback to API
_FRONTEND_BUILD_DIR = Path(__file__).parent.parent.parent / "frontend" / "dist"

if _FRONTEND_BUILD_DIR.exists():
    _INDEX_FILE = _FRONTEND_BUILD_DIR / "index.html"

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        # Serve real files from dist (e.g. /assets/index-xxx.js) so the app loads
        safe_path = Path(full_path).resolve()
        file_path = (_FRONTEND_BUILD_DIR / full_path).resolve()
        if full_path and file_path.is_file() and str(file_path).startswith(str(_FRONTEND_BUILD_DIR)):
            return FileResponse(str(file_path))
        if _INDEX_FILE.exists():
            return FileResponse(str(_INDEX_FILE))
        return JSONResponse({"ok": False, "message": "Frontend not built"})
else:
    # Fallback: API only
    @app.get("/")
    def root():
        return JSONResponse({
            "ok": True,
            "message": "Vibe Studio API",
            "note": "Frontend not built. Run 'cd frontend && npm run build' to build the IDE."
        })
