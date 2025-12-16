from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-4"
    roblox_api_key: str = ""  # Optional - for future Roblox Cloud API integration
    roblox_universe_id: str = ""
    roblox_place_id: str = ""
    database_url: str = "sqlite:///./vibe_coding.db"
    cors_origins: str = "http://localhost:5173"
    port: int = 8000

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

