from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import router
from app.database.database import init_db
import uvicorn

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="Vibe Coding Platform API",
    description="AI-powered Roblox game creation platform",
    version="1.0.0"
)

# CORS middleware - handle OPTIONS preflight requests automatically
# Allow all origins in development, or specific origins from settings
# For Roblox HttpService, we need to allow all origins
cors_origins = settings.cors_origins_list if settings.cors_origins_list and len(settings.cors_origins_list) > 0 else ["*"]

# If cors_origins contains "*", use allow_origin_regex instead for better compatibility
if "*" in cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=".*",  # Allow all origins (needed for Roblox HttpService)
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods including OPTIONS
        allow_headers=["*"],  # Allow all headers
        expose_headers=["*"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods including OPTIONS
        allow_headers=["*"],  # Allow all headers
        expose_headers=["*"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    return {
        "message": "Vibe Coding Platform API",
        "version": "1.0.0",
        "endpoints": {
            "generate": "/api/generate",
            "drafts": "/api/drafts",
            "blueprints": "/api/blueprints"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "vibe-coding-api"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True
    )

