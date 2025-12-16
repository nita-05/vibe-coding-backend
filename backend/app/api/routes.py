from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.api.models import (
    GenerationRequest,
    GenerationResponse,
    DraftCreate,
    DraftResponse,
    BlueprintInfo,
    RobloxPublishRequest,
    AIChatRequest,
    AIChatResponse
)
from app.core.openai_client import OpenAIClient
from app.core.prompt_builder import PromptBuilder
from app.core.roblox_client import RobloxClient
from app.database.database import get_db, save_draft, get_draft, get_all_drafts
from datetime import datetime
from typing import List, Optional
import uuid

router = APIRouter(prefix="/api", tags=["api"])

# Initialize clients
openai_client = OpenAIClient()
prompt_builder = PromptBuilder()
roblox_client = RobloxClient()


@router.post("/generate", response_model=GenerationResponse)
async def generate_script(request: GenerationRequest):
    """
    Generate Roblox Lua script from text prompt using AI.
    """
    try:
        # Enhance prompt with blueprint context
        enhanced_prompt = prompt_builder.enhance_prompt(
            request.prompt,
            request.blueprint_id,
            request.settings
        )
        
        # Generate script using OpenAI
        result = openai_client.generate_roblox_script(
            enhanced_prompt,
            request.blueprint_id,
            request.settings
        )
        
        # Validate script safety
        validation = prompt_builder.validate_script_safety(result["lua_script"])
        result["validation"] = validation
        
        # Convert to response model
        response = GenerationResponse(**result)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/draft", response_model=DraftResponse)
async def create_draft(draft: DraftCreate, db=Depends(get_db)):
    """
    Save a generated script as a draft for later use.
    """
    try:
        draft_data = {
            "prompt": draft.prompt,
            "blueprint_id": draft.blueprint_id,
            "settings": draft.settings or {},
            "result": draft.result.dict(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        draft_id = save_draft(db, draft_data)
        
        response = DraftResponse(
            id=draft_id,
            prompt=draft.prompt,
            blueprint_id=draft.blueprint_id,
            settings=draft.settings,
            result=draft.result,
            created_at=draft_data["created_at"]
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save draft: {str(e)}")


@router.get("/draft/{draft_id}", response_model=DraftResponse)
async def get_draft_by_id(draft_id: int, db=Depends(get_db)):
    """
    Retrieve a saved draft by ID.
    """
    try:
        draft = get_draft(db, draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        return DraftResponse(**draft)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve draft: {str(e)}")


@router.get("/drafts", response_model=List[DraftResponse])
async def list_drafts(db=Depends(get_db), limit: int = 20):
    """
    List all saved drafts.
    """
    try:
        drafts = get_all_drafts(db, limit)
        return [DraftResponse(**draft) for draft in drafts]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve drafts: {str(e)}")


@router.post("/roblox/publish")
async def publish_to_roblox(payload: RobloxPublishRequest):
    """
    Publish a generated script to Roblox (requires Roblox API key).
    """
    if not roblox_client.is_configured():
        raise HTTPException(
            status_code=400,
            detail="Roblox Open Cloud credentials are not configured. Add ROBLOX_API_KEY, ROBLOX_UNIVERSE_ID, ROBLOX_PLACE_ID to .env file."
        )
    
    try:
        result = await roblox_client.publish_place(
            place_name=payload.place_name,
            script_content=payload.script_content,
            description=payload.description
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roblox/status")
async def roblox_status():
    """
    Check if Roblox API is configured and available.
    """
    configured = roblox_client.is_configured()
    return {
        "configured": configured,
        "place_id": roblox_client.place_id if configured else None,
        "message": "Roblox API is configured" if configured 
                  else "Roblox Open Cloud credentials not found. Add ROBLOX_API_KEY, ROBLOX_UNIVERSE_ID, ROBLOX_PLACE_ID to .env"
    }


@router.get("/blueprints", response_model=List[BlueprintInfo])
async def get_blueprints():
    """
    Get available game blueprint templates.
    """
    blueprints = [
        BlueprintInfo(
            id="obby-basic",
            name="Obstacle Course (Obby)",
            description="Create challenging obstacle courses with platforms, jumps, and checkpoints",
            category="Platformer",
            example_prompt="Create a floating island obby with neon platforms and moving obstacles"
        ),
        BlueprintInfo(
            id="tycoon-basic",
            name="Tycoon Game",
            description="Build money-generating tycoons with upgrades and automation",
            category="Simulation",
            example_prompt="Create a pizza tycoon where players build restaurants and earn money"
        ),
        BlueprintInfo(
            id="narrative-basic",
            name="Story Game",
            description="Create interactive narratives with dialogue and quests",
            category="Adventure",
            example_prompt="Create a detective story where players solve mysteries"
        ),
        BlueprintInfo(
            id="simulator-basic",
            name="Simulator",
            description="Build simulators with currency, upgrades, and rebirth mechanics",
            category="Simulation",
            example_prompt="Create a pet simulator where players collect and evolve pets"
        ),
        BlueprintInfo(
            id="racing-basic",
            name="Racing Game",
            description="Create racing experiences with vehicles and tracks",
            category="Racing",
            example_prompt="Create a futuristic racing game with power-ups and multiple tracks"
        ),
        BlueprintInfo(
            id="fps-basic",
            name="First-Person Shooter",
            description="Build FPS games with weapons, teams, and combat mechanics",
            category="Shooter",
            example_prompt="Create a team-based FPS with capture the flag mode"
        ),
        BlueprintInfo(
            id="fps-advanced",
            name="Advanced FPS System",
            description="Super advanced modular FPS with AI enemies, advanced gun mechanics, and complete multiplayer system",
            category="Shooter",
            example_prompt="Create an advanced FPS with enemy AI, weapon customization, and multiplayer support"
        )
    ]
    
    return blueprints


# ============================================
# AI Chat Endpoint for Roblox Integration
# ============================================

@router.post("/ai/chat", response_model=AIChatResponse)
async def ai_chat(request: AIChatRequest):
    """
    AI chat endpoint for Roblox game interactions.
    Allows NPCs, assistants, or game characters to respond to player messages using OpenAI.
    """
    try:
        # Get AI response from OpenAI client
        response_message = openai_client.chat_completion(
            messages=[msg.dict() for msg in request.messages],
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            context=request.context
        )
        
        return AIChatResponse(
            message=response_message,
            success=True
        )
        
    except Exception as e:
        return AIChatResponse(
            message="Sorry, I'm having trouble responding right now.",
            success=False,
            error=str(e)
        )

