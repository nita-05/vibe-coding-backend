from __future__ import annotations

from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    # When true, endpoints will NOT fall back to static templates.
    # They will error if AI is not configured or if AI output is invalid.
    require_ai: bool = Field(default=True, alias="REQUIRE_AI")

    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")
    database_url: str = Field(default="sqlite:///./vibe_coding.db", alias="DATABASE_URL")
    auth_session_ttl_seconds: int = Field(default=60 * 60 * 24 * 7, alias="AUTH_SESSION_TTL_SECONDS")  # 7 days
    auth_cookie_name: str = Field(default="vibe_session", alias="AUTH_COOKIE_NAME")
    auth_cookie_secure: bool = Field(default=False, alias="AUTH_COOKIE_SECURE")  # set True behind HTTPS
    auth_cookie_samesite: str = Field(default="lax", alias="AUTH_COOKIE_SAMESITE")  # "lax" | "strict" | "none"
    
    # Google OAuth
    google_client_id: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: Optional[str] = Field(default=None, alias="GOOGLE_REDIRECT_URI")
    
    # Frontend URL for OAuth redirects
    frontend_url: Optional[str] = Field(default=None, alias="FRONTEND_URL")

    def cors_origin_list(self) -> List[str]:
        v = (self.cors_origins or "").strip()
        if v == "" or v == "*":
            # Cookie-based auth requires explicit origins for dev. For prod builds served by FastAPI,
            # CORS is irrelevant (same-origin), so this mainly affects local dev on Vite.
            # In production, CORS_ORIGINS should be set to include frontend URL
            return ["http://localhost:5173", "http://127.0.0.1:5173"]
        return [o.strip() for o in v.split(",") if o.strip()]


settings = Settings()
