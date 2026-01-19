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
    # Serve static files from frontend build
    app.mount("/static", StaticFiles(directory=str(_FRONTEND_BUILD_DIR)), name="static")
    
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        # Don't serve API routes as static files
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        
        # Serve index.html for all non-API routes (SPA routing)
        index_file = _FRONTEND_BUILD_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
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
