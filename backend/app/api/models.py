from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class AIChatRequest(BaseModel):
    messages: List[ChatMessage]
    system_prompt: str = "You are a helpful assistant."
    temperature: float = 0.6
    max_tokens: int = 180
    context: Dict[str, Any] = Field(default_factory=dict)


class AIChatResponse(BaseModel):
    success: bool
    message: str
    error: Optional[str] = None


class RobloxGenerateRequest(BaseModel):
    prompt: str
    template: str = "coin_collector"
    require_ai: bool = True
    temperature: float = 0.2
    max_tokens: int = 1400


class RobloxFile(BaseModel):
    path: str
    content: str


class RobloxGenerateResponse(BaseModel):
    success: bool
    title: str
    description: str
    files: List[RobloxFile]
    setup_instructions: List[str]
    notes: List[str] = Field(default_factory=list)
    session_id: Optional[str] = None
    error: Optional[str] = None


class RobloxZipRequest(BaseModel):
    title: str = "roblox_pack"
    files: List[RobloxFile]


class RobloxRegenerateRequest(BaseModel):
    prompt: str
    change_request: str
    template: str = "coin_collector"
    session_id: Optional[str] = None
    require_ai: bool = True
    base_title: str = ""
    base_description: str = ""
    base_files: List[RobloxFile] = Field(default_factory=list)
    temperature: float = 0.2
    max_tokens: int = 1800
