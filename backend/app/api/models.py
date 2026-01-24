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
    require_ai: Optional[bool] = None  # None = use REQUIRE_AI env var; frontend doesn't send this
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
    require_ai: Optional[bool] = None  # None = use REQUIRE_AI env var
    base_title: str = ""
    base_description: str = ""
    base_files: List[RobloxFile] = Field(default_factory=list)
    temperature: float = 0.2
    max_tokens: int = 1800


class AuthRegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    name: Optional[str] = None


class AuthLoginRequest(BaseModel):
    email: str
    password: str


class UserPublic(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class AuthMeResponse(BaseModel):
    authenticated: bool
    user: Optional[UserPublic] = None


class ProjectFile(BaseModel):
    path: str
    content: str


class ProjectSaveRequest(BaseModel):
    name: str
    files: List[ProjectFile]
    description: Optional[str] = None


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    files: List[ProjectFile]
    created_at: str
    updated_at: str


class ProjectListResponse(BaseModel):
    projects: List[ProjectInfo]
