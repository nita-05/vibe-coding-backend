from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class GenerationRequest(BaseModel):
    prompt: str
    blueprint_id: Optional[str] = None
    settings: Optional[Dict[str, Any]] = {
        "creativity": 0.7,
        "world_scale": "medium",
        "device": "desktop"
    }


class ModuleInfo(BaseModel):
    name: str
    description: str
    entry_point: str


class GenerationResponse(BaseModel):
    title: str
    narrative: str
    lua_script: str
    modules: List[ModuleInfo]
    testing_steps: List[str]
    assets_needed: List[str] = []
    optimization_tips: List[str] = []
    validation: Optional[Dict[str, Any]] = None


class DraftCreate(BaseModel):
    prompt: str
    blueprint_id: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    result: GenerationResponse


class DraftResponse(BaseModel):
    id: int
    prompt: str
    blueprint_id: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    result: GenerationResponse
    created_at: str


class BlueprintInfo(BaseModel):
    id: str
    name: str
    description: str
    category: str
    example_prompt: str


class RobloxPublishRequest(BaseModel):
    place_name: str
    script_content: str
    description: str = ""


# AI Chat Models for Roblox Integration
class AIChatMessage(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str


class AIChatRequest(BaseModel):
    messages: List[AIChatMessage]
    system_prompt: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 150
    context: Optional[Dict[str, Any]] = None  # Game context (player name, game state, etc.)


class AIChatResponse(BaseModel):
    message: str
    success: bool
    error: Optional[str] = None
