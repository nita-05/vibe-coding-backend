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

    def cors_origin_list(self) -> List[str]:
        v = (self.cors_origins or "").strip()
        if v == "" or v == "*":
            return ["*"]
        return [o.strip() for o in v.split(",") if o.strip()]


settings = Settings()
