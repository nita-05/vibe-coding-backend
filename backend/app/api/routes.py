from __future__ import annotations

import io
import re
import zipfile
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse

from app.api.models import (
    AIChatRequest,
    AIChatResponse,
    AuthLoginRequest,
    AuthMeResponse,
    AuthRegisterRequest,
    ProjectFile,
    ProjectInfo,
    ProjectListResponse,
    ProjectSaveRequest,
    ProjectUpdateRequest,
    RobloxGenerateRequest,
    RobloxGenerateResponse,
    RobloxRegenerateRequest,
    RobloxZipRequest,
    UserPublic,
)
from app.database.database import (
    authenticate_user,
    create_or_get_google_user,
    create_session,
    create_user,
    delete_session,
    get_db,
    get_project,
    get_session,
    list_projects,
    update_project,
    delete_project,
    replace_project,
    save_project,
    get_user_by_email,
    get_user_by_id,
)
from app.services.fallback_templates import (
    coin_collector_pack,
    obby_pack,
    runner_pack,
    seasonal_collector_pack_ai,
    tycoon_pack,
)
from app.services.openai_service import chat as ai_chat
from app.services.openai_service import chat_stream as ai_chat_stream
from app.services.openai_service import generate_json
from app.services.repo_templates import seasonal_collector_pack
from app.services.session_store import session_store
from app.services.studio_plugin import generate_import_plugin_rbxmx
from app.settings import settings

router = APIRouter()


def _set_session_cookie(response: Response, sid: str) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=sid,
        httponly=True,
        secure=bool(settings.auth_cookie_secure),
        samesite=str(settings.auth_cookie_samesite).lower(),
        max_age=int(settings.auth_session_ttl_seconds),
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.auth_cookie_name, path="/")


def get_current_user(request: Request, db=Depends(get_db)) -> Dict[str, Any]:
    sid = request.cookies.get(settings.auth_cookie_name) or ""
    sess = get_session(db=db, sid=sid)
    if not sess:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = get_user_by_id(db=db, user_id=str(sess.get("user_id")))
    if not user:
        delete_session(db=db, sid=sid)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


@router.post("/api/auth/register", response_model=AuthMeResponse)
def auth_register(req: AuthRegisterRequest, response: Response, db=Depends(get_db)) -> AuthMeResponse:
    email = (req.email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")
    existing = get_user_by_email(db=db, email=email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = create_user(db=db, email=email, password=req.password, name=req.name)
    sess = create_session(db=db, user_id=str(user["id"]), ttl_seconds=settings.auth_session_ttl_seconds)
    _set_session_cookie(response, sess["id"])
    return AuthMeResponse(
        authenticated=True,
        user=UserPublic(
            id=str(user["id"]),
            email=str(user["email"]),
            name=user.get("name"),
            avatar_url=user.get("avatar_url"),
        ),
    )


@router.post("/api/auth/login", response_model=AuthMeResponse)
def auth_login(req: AuthLoginRequest, response: Response, db=Depends(get_db)) -> AuthMeResponse:
    user = authenticate_user(db=db, email=req.email, password=req.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    sess = create_session(db=db, user_id=str(user["id"]), ttl_seconds=settings.auth_session_ttl_seconds)
    _set_session_cookie(response, sess["id"])
    return AuthMeResponse(
        authenticated=True,
        user=UserPublic(
            id=str(user["id"]),
            email=str(user["email"]),
            name=user.get("name"),
            avatar_url=user.get("avatar_url"),
        ),
    )


@router.post("/api/auth/logout")
def auth_logout(request: Request, response: Response, db=Depends(get_db)):
    sid = request.cookies.get(settings.auth_cookie_name) or ""
    delete_session(db=db, sid=sid)
    _clear_session_cookie(response)
    return {"ok": True}


@router.get("/api/auth/me", response_model=AuthMeResponse)
def auth_me(request: Request, db=Depends(get_db)) -> AuthMeResponse:
    sid = request.cookies.get(settings.auth_cookie_name) or ""
    sess = get_session(db=db, sid=sid)
    if not sess:
        return AuthMeResponse(authenticated=False, user=None)
    user = get_user_by_id(db=db, user_id=str(sess.get("user_id")))
    if not user:
        delete_session(db=db, sid=sid)
        return AuthMeResponse(authenticated=False, user=None)
    return AuthMeResponse(
        authenticated=True,
        user=UserPublic(
            id=str(user["id"]),
            email=str(user["email"]),
            name=user.get("name"),
            avatar_url=user.get("avatar_url"),
        ),
    )


@router.get("/api/auth/google")
def auth_google_initiate(request: Request):
    """Initiate Google OAuth flow - redirects to Google login."""
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")
    
    from urllib.parse import urlencode
    
    redirect_uri = settings.google_redirect_uri or f"{request.base_url}api/auth/google/callback"
    scope = "openid email profile"
    
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "access_type": "online",
        "prompt": "select_account",
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return {"auth_url": auth_url}


@router.get("/api/auth/google/callback")
def auth_google_callback(
    request: Request,
    response: Response,
    code: Optional[str] = None,
    error: Optional[str] = None,
    db=Depends(get_db),
):
    """Handle Google OAuth callback."""
    if error:
        # Redirect to frontend with error
        frontend_url = settings.frontend_url
        if not frontend_url:
            # Fallback: try to infer from request or use localhost for dev
            frontend_url = str(request.base_url).replace(":8000", ":5173") if ":8000" in str(request.base_url) else "http://localhost:5173"
        frontend_url = frontend_url.rstrip("/")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"{frontend_url}/?auth_error={error}", status_code=302)
    
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")
    
    try:
        import httpx
        
        redirect_uri = settings.google_redirect_uri or f"{request.base_url}api/auth/google/callback"
        
        # Exchange code for token
        token_response = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10.0,
        )
        token_response.raise_for_status()
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        # id_token is a JWT (identity token), not usable for the userinfo endpoint.
        # Keep it available for future verification if needed.
        _id_token = token_data.get("id_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="No access_token received from Google")
        
        # Get user info from Google
        userinfo_response = httpx.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10.0,
        )
        userinfo_response.raise_for_status()
        google_user = userinfo_response.json()
        
        google_id = google_user.get("id")
        email = google_user.get("email", "").lower().strip()
        name = google_user.get("name")
        avatar_url = google_user.get("picture")
        
        if not google_id or not email:
            raise HTTPException(status_code=400, detail="Invalid user data from Google")
        
        # Create or get user
        user = create_or_get_google_user(
            db=db,
            google_id=google_id,
            email=email,
            name=name,
            avatar_url=avatar_url,
        )
        
        # Create session
        sess = create_session(db=db, user_id=str(user["id"]), ttl_seconds=settings.auth_session_ttl_seconds)
        # Redirect to frontend (cookie must be set on the *returned* response)
        frontend_url = settings.frontend_url
        if not frontend_url:
            # Fallback: try to infer from request or use localhost for dev
            frontend_url = str(request.base_url).replace(":8000", ":5173") if ":8000" in str(request.base_url) else "http://localhost:5173"
        frontend_url = frontend_url.rstrip("/")
        from fastapi.responses import RedirectResponse
        redirect = RedirectResponse(url=f"{frontend_url}/?auth_success=true", status_code=302)
        _set_session_cookie(redirect, sess["id"])
        return redirect
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback error: {str(e)}")


@router.post("/api/projects", response_model=ProjectInfo)
def save_project_endpoint(
    req: ProjectSaveRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db),
) -> ProjectInfo:
    """Save a project (all files) for the current user."""
    files_data = [{"path": f.path, "content": f.content} for f in req.files]
    project_id = save_project(
        db=db,
        user_id=str(user["id"]),
        name=req.name,
        files=files_data,
        description=req.description,
    )
    proj = get_project(db=db, project_id=project_id, user_id=str(user["id"]))
    if not proj:
        raise HTTPException(status_code=500, detail="Failed to retrieve saved project")
    return ProjectInfo(
        id=proj["id"],
        name=proj["name"],
        description=proj.get("description"),
        files=[ProjectFile(path=f["path"], content=f["content"]) for f in proj.get("files", [])],
        created_at=proj["created_at"],
        updated_at=proj["updated_at"],
    )


@router.get("/api/projects", response_model=ProjectListResponse)
def list_projects_endpoint(
    user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db),
) -> ProjectListResponse:
    """List all projects for the current user."""
    projects = list_projects(db=db, user_id=str(user["id"]), limit=100)
    return ProjectListResponse(
        projects=[
            ProjectInfo(
                id=p["id"],
                name=p["name"],
                description=p.get("description"),
                files=[ProjectFile(path=f["path"], content=f["content"]) for f in p.get("files", [])],
                created_at=p["created_at"],
                updated_at=p["updated_at"],
            )
            for p in projects
        ]
    )


@router.get("/api/projects/{project_id}", response_model=ProjectInfo)
def get_project_endpoint(
    project_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db),
) -> ProjectInfo:
    """Get a project by ID (must belong to current user)."""
    proj = get_project(db=db, project_id=project_id, user_id=str(user["id"]))
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectInfo(
        id=proj["id"],
        name=proj["name"],
        description=proj.get("description"),
        files=[ProjectFile(path=f["path"], content=f["content"]) for f in proj.get("files", [])],
        created_at=proj["created_at"],
        updated_at=proj["updated_at"],
    )


@router.patch("/api/projects/{project_id}", response_model=ProjectInfo)
def update_project_endpoint(
    project_id: str,
    req: ProjectUpdateRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db),
) -> ProjectInfo:
    """Rename/update project metadata (must belong to current user)."""
    if req.name is None and req.description is None:
        raise HTTPException(status_code=400, detail="No fields to update")
    proj = update_project(
        db=db,
        project_id=project_id,
        user_id=str(user["id"]),
        name=req.name,
        description=req.description,
    )
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectInfo(
        id=proj["id"],
        name=proj["name"],
        description=proj.get("description"),
        files=[ProjectFile(path=f["path"], content=f["content"]) for f in proj.get("files", [])],
        created_at=proj["created_at"],
        updated_at=proj["updated_at"],
    )


@router.put("/api/projects/{project_id}", response_model=ProjectInfo)
def replace_project_endpoint(
    project_id: str,
    req: ProjectSaveRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db),
) -> ProjectInfo:
    """Replace project files + metadata (must belong to current user)."""
    files_data = [{"path": f.path, "content": f.content} for f in req.files]
    proj = replace_project(
        db=db,
        project_id=project_id,
        user_id=str(user["id"]),
        name=req.name,
        description=req.description,
        files=files_data,
    )
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectInfo(
        id=proj["id"],
        name=proj["name"],
        description=proj.get("description"),
        files=[ProjectFile(path=f["path"], content=f["content"]) for f in proj.get("files", [])],
        created_at=proj["created_at"],
        updated_at=proj["updated_at"],
    )


@router.delete("/api/projects/{project_id}")
def delete_project_endpoint(
    project_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db),
):
    """Delete a project (must belong to current user)."""
    ok = delete_project(db=db, project_id=project_id, user_id=str(user["id"]))
    if not ok:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"ok": True}


@router.get("/api/ai/status")
def ai_status():
    return {
        "ai_enabled": bool(settings.openai_api_key),
        "require_ai": bool(settings.require_ai),
        "model": settings.openai_model,
    }


@router.post("/api/ai/chat", response_model=AIChatResponse)
def ai_chat_endpoint(req: AIChatRequest) -> AIChatResponse:
    try:
        msg = ai_chat(
            messages=[m.model_dump() for m in req.messages if m.role != "system"],
            system_prompt=req.system_prompt,
            temperature=float(req.temperature),
            max_tokens=int(req.max_tokens),
        )
        if not msg:
            return AIChatResponse(success=False, message="", error="Empty AI response")
        return AIChatResponse(success=True, message=msg)
    except HTTPException as e:
        return AIChatResponse(success=False, message="", error=str(e.detail))


@router.post("/api/ai/chat/stream")
def ai_chat_stream_endpoint(req: AIChatRequest):
    """Stream AI response tokens (SSE)."""
    import json as _json

    def gen():
        try:
            for token in ai_chat_stream(
                messages=[m.model_dump() for m in req.messages if m.role != "system"],
                system_prompt=req.system_prompt,
                temperature=float(req.temperature),
                max_tokens=int(req.max_tokens),
            ):
                yield f"data: {_json.dumps({'token': token})}\n\n"
            yield "data: [DONE]\n\n"
        except HTTPException as e:
            yield f"event: error\ndata: {_json.dumps({'error': str(e.detail)})}\n\n"
        except Exception as e:  # pragma: no cover
            yield f"event: error\ndata: {_json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/api/ai/chat/stream")
def ai_chat_stream_endpoint(req: AIChatRequest):
    """Stream AI response tokens (SSE)."""
    import json as _json

    def gen():
        try:
            for token in ai_chat_stream(
                messages=[m.model_dump() for m in req.messages if m.role != "system"],
                system_prompt=req.system_prompt,
                temperature=float(req.temperature),
                max_tokens=int(req.max_tokens),
            ):
                yield f"data: {_json.dumps({'token': token})}\n\n"
            yield "data: [DONE]\n\n"
        except HTTPException as e:
            yield f"event: error\ndata: {_json.dumps({'error': str(e.detail)})}\n\n"
        except Exception as e:  # pragma: no cover
            yield f"event: error\ndata: {_json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


_ROBLOX_SYSTEM_PROMPT = """You generate Roblox Studio game scripts from a text prompt.

Return ONLY a JSON object with this shape:
{
  "title": string,
  "description": string,
  "files": [{"path": string, "content": string}],
  "setup_instructions": [string],
  "notes": [string]
}

CRITICAL - USER REQUEST MATCHING (READ THIS FIRST):
- MATCH THE USER'S REQUEST EXACTLY - Create ONLY what they ask for, nothing extra
- If user says "simple coin collector" → Create ONLY coins that can be collected, NO UI, NO score system unless they mention it
- If user says "simple racing game" → Create ONLY racing mechanics, NO extra UI unless they mention it
- If user mentions "score", "points", "leaderboard", "track score" → THEN add score system
- If user mentions "UI", "display", "show score", "interface" → THEN add UI
- If user says "simple" → Keep it minimal, no extra features
- DO NOT add "helpful" features the user didn't ask for - match their request exactly
- CRITICAL: For initial generation, create exactly what the prompt asks for - no assumptions, no extras

CRITICAL: The "files" array MUST contain ALL required files for the game to work. For coin collector/day-to-night collector games, you MUST include ALL 3 files (see template expectations below). DO NOT omit any files - the game will not function if files are missing!

MANDATORY OUTPUT REQUIREMENTS:
- The "files" array MUST contain at least 1 file (minimum requirement)
- Each file MUST have both "path" (string, non-empty) AND "content" (string, non-empty with actual Lua code)
- Files with empty content will be rejected - every file MUST have complete, working code
- Example of CORRECT file: {"path": "ServerScriptService/Game.lua", "content": "-- Game script\nlocal Players = game:GetService('Players')\nprint('Game started')"}
- Example of WRONG file: {"path": "ServerScriptService/Game.lua", "content": ""} - THIS WILL BE REJECTED
- If you cannot generate complete code for a file, DO NOT include it in the response - only include files with complete, working code

NATURAL LANGUAGE UNDERSTANDING - PRIMARY DIRECTIVE:
- ANALYZE the user's natural language prompt to understand what type of game they want
- Extract game type from ANY description, even if not explicitly stated:
  * "make a game where you collect items" → Collector game
  * "build a game with jumping platforms" → Platformer/Obby game
  * "create a game where players race" → Racing game
  * "make a business simulation" → Tycoon game
  * "build a shooter with teams" → FPS game
  * "create an idle clicker" → Simulator game
  * "make a story-driven adventure" → Story/Narrative game
- If template is provided, use it as a hint, but STILL analyze the prompt for specifics
- Extract ALL mentioned features, mechanics, and requirements from the prompt
- Create the EXACT game the user described, not just a generic template
- Support ANY game type - RPG, puzzle, survival, horror, adventure, etc. - not just listed templates

QUALITY REQUIREMENTS - PERFECTION IS REQUIRED:
- Output PERFECT, ERROR-FREE Roblox Lua scripts that work immediately
- DOUBLE-CHECK your code before submitting - search for common errors:
  * Search for ".CFrame = Vector3" - if found, FIX IT to use CFrame.new()
  * Search for "player.leaderstats" without WaitForChild - if found, FIX IT
  * Search for service names without game:GetService() - if found, FIX IT
- Use clear, copy/paste-friendly code
- Do NOT reference external assets unless necessary
- Include at least one server script (required for all games)
- Include client UI script ONLY if user mentions UI, score display, or interface
- Cars must NOT be used as obstacles

USER REQUEST MATCHING - CRITICAL (ENFORCE STRICTLY):
- If user says "simple coin collector" → Create ONLY coins that can be collected, NO score UI, NO leaderstats unless explicitly mentioned
- If user says "coin collector with score UI" → Create coins AND score UI
- If user says "create a simple racing game" → Create ONLY track and racing mechanics, NO extra UI, NO score system unless mentioned
- If user mentions "score", "points", "leaderboard", "track score" → THEN add score system
- If user mentions "UI", "display", "show score", "interface" → THEN add UI
- Only add what the user explicitly requests - don't add "helpful" features they didn't ask for
- CRITICAL: If the prompt does NOT mention UI or score, DO NOT create them - keep it simple
- CRITICAL: For coin collector games (user mentions "coin collector", "day to night collector", or similar), you MUST generate ALL required files in the "files" array. The game will NOT work if any file is missing. See template expectations below for complete file list.

CODE REVIEW CHECKLIST - VERIFY BEFORE SUBMITTING:
□ All CFrame assignments use CFrame.new(), NOT Vector3.new()
□ All leaderstats access uses WaitForChild or FindFirstChild
□ All services are retrieved with game:GetService() first
□ Server creates leaderstats before client tries to access
□ No direct player.leaderstats access without waiting
□ All code is complete and functional (no TODOs)
□ I only included features the user asked for (if user said "simple", I didn't add extra UI/score)
□ I matched the user's request exactly - they asked for X, I created X

CRITICAL ROBLOX CODE RULES (MUST FOLLOW - THESE ERRORS WILL CAUSE YOUR CODE TO FAIL):

1. SERVICES - ALWAYS GET SERVICES FIRST:
   * CORRECT: local Lighting = game:GetService("Lighting"); Lighting.TimeOfDay = 6
   * WRONG: Lighting.TimeOfDay = 6 - THIS WILL CRASH with "attempt to index nil" error
   * ALWAYS get services: local Players = game:GetService("Players"), local Workspace = game:GetService("Workspace"), local ReplicatedStorage = game:GetService("ReplicatedStorage"), etc.
   * NEVER use service names directly without game:GetService() first!

2. CFrame vs Vector3 - CRITICAL ERROR TO AVOID:
   * WRONG: part.CFrame = Vector3.new(0, 5, 0) - THIS WILL CRASH with "Unable to cast Vector3 to CoordinateFrame" error
   * CORRECT: part.CFrame = CFrame.new(0, 5, 0) - Use CFrame.new() for CFrame assignments
   * CORRECT: part.Position = Vector3.new(0, 5, 0) - Use Position property if you only need position
   * CORRECT: humanoidRootPart.CFrame = CFrame.new(0, 24, 0) - For teleporting players
   * WRONG: humanoidRootPart.CFrame = Vector3.new(0, 24, 0) - THIS WILL CRASH!
   * DOUBLE-CHECK: Before assigning to .CFrame, make sure you're using CFrame.new(), NOT Vector3.new()

3. leaderstats ACCESS - CRITICAL ERROR TO AVOID:
   * Server (ServerScriptService): MUST create leaderstats FIRST in Players.PlayerAdded event
     Example: local leaderstats = Instance.new("Folder"); leaderstats.Name = "leaderstats"; leaderstats.Parent = player
   * Client (StarterPlayerScripts): ALWAYS use WaitForChild before accessing leaderstats
     CORRECT: local leaderstats = player:WaitForChild("leaderstats", 10)
     CORRECT: if player:FindFirstChild("leaderstats") then local stats = player.leaderstats end
     WRONG: local stats = player.leaderstats - THIS WILL CRASH with "leaderstats is not a valid member" error
   * NEVER directly access player.leaderstats without WaitForChild or FindFirstChild first!
- Folders/Containers: ALWAYS create folders/containers before using them in Workspace or other services.
  * WRONG: part.Parent = Workspace.Coins (crashes if Coins folder doesn't exist)
  * CORRECT: local folder = Workspace:FindFirstChild("Coins") or Instance.new("Folder", Workspace); folder.Name = "Coins"; part.Parent = folder
  * NEVER assume folders exist - create them programmatically if scripts need to reference them!
- COINS/COLLECTIBLES CREATION (CRITICAL):
  * Coins MUST be REAL 3D Part objects (NOT BillboardGui text labels). Users want actual collectible objects, not text boxes.
  * CORRECT: Create Part with Shape = Enum.PartType.Ball, Size = Vector3.new(2, 2, 2) or larger, Material = Enum.Material.Neon, BrickColor = BrickColor.new("Bright yellow"), Transparency = 0, add PointLight for glow
    Example: local coin = Instance.new("Part"); coin.Shape = Enum.PartType.Ball; coin.Size = Vector3.new(2, 2, 2); coin.Material = Enum.Material.Neon; coin.BrickColor = BrickColor.new("Bright yellow"); coin.Transparency = 0; coin.Anchored = true; coin.CanCollide = false; coin.CanTouch = true (CRITICAL - coins must be touchable to be collected!); local light = Instance.new("PointLight", coin); light.Color = Color3.new(1, 1, 0); light.Brightness = 3; light.Range = 15
  * WRONG: Creating BillboardGui with TextLabel showing "COIN" text - this is NOT a real coin, users will see text boxes floating in air instead of actual collectible objects
  * NEVER use BillboardGui for coins - only use REAL 3D Parts with proper shapes (Ball, Cylinder, etc.)
  * Coins MUST be RANDOMLY SPREAD across the map (not in a grid or line).
    - Use random angles and distances: local angle = math.random() * math.pi * 2; local distance = math.random() * spawnRadius; local x = math.cos(angle) * distance; local z = math.sin(angle) * distance; local y = math.random(minY, maxY)
    - WRONG: Grid pattern like for i=1,10 do for j=1,10 do coin.Position = Vector3.new(i*5, 5, j*5) end end
    - CORRECT: Random scatter: for i=1,coinCount do local angle = math.random() * math.pi * 2; local distance = math.random() * 50; local x = math.cos(angle) * distance; local z = math.sin(angle) * distance; coin.Position = Vector3.new(x, math.random(3, 8), z) end
  * Coins MUST be VISIBLE: Size at least Vector3.new(4, 4, 4) (4 studs minimum - 2 studs is too small), Neon material for glow, PointLight with Brightness = 2-3 and Range = 10-15, Transparency = 0
  * CRITICAL POSITIONING - REACHABLE HEIGHTS: Position coins at REACHABLE heights (Y = 5 to 15 studs above ground) so players can collect them. NOT too high (Y=20-50) which players cannot reach. Coins must be within player's jump reach - ensure they're collectible!

Template expectations for template=coin_collector:
- Coins spawn in Workspace/Coins and award points on touch.
- CRITICAL: Coins MUST be REAL 3D Part objects (NOT BillboardGui text labels).
  * CORRECT: Create Part with Shape = Enum.PartType.Ball, Size = Vector3.new(2, 2, 2), Material = Enum.Material.Neon, BrickColor = Bright yellow, add PointLight for visibility
  * CRITICAL: Set coin.CanTouch = true and coin.CanCollide = false so coins can be collected
  * WRONG: Creating BillboardGui with text "COIN" - this is NOT a real coin, just text floating in air
  * Coins should be SPHERES/BALLS (Shape = Ball) or cylinders, NOT flat text boxes
  * Use: coin.Shape = Enum.PartType.Ball; coin.Material = Enum.Material.Neon; coin.BrickColor = BrickColor.new("Bright yellow"); coin.Size = Vector3.new(2, 2, 2); coin.CanTouch = true; coin.CanCollide = false
- Coins MUST be RANDOMLY SPREAD THROUGHOUT THE ENTIRE TEMPLATE/MAP (not just around spawn, but across the WHOLE map including water, rooms, different areas).
  * Use math.random() for positions with LARGE radius (200-500 studs) to cover entire template: local angle = math.random() * math.pi * 2; local distance = math.random() * 300 (large radius); local x = math.cos(angle) * distance; local z = math.sin(angle) * distance
  * Place coins in different areas: water/swimming areas (adjust Y for water level), inside rooms/buildings, open areas, throughout the map
  * WRONG: Only placing coins around spawn (small radius like 50 studs) - coins should spread across ENTIRE map
  * CORRECT: Each coin gets random angle and LARGE distance, creating scattered placement across the whole template
- Coins MUST be VISIBLE (size 2+ studs, Neon material, PointLight glow).
- Coins MUST be COLLECTIBLE: Set coin.CanTouch = true in coin creation code
- Score UI ONLY if user mentions UI/score - Set screenGui.DisplayOrder = 10; Score format: "Score: value" in one line
- Obstacles in Workspace/Obstacles kill player on touch.
- Provide an AutoBuildEnvironment script that creates a minimal playable map.

Template expectations for template=obby:
- Create a simple obby with checkpoints and a finish.
- Provide an AutoBuildObby server script.

Template expectations for template=endless_runner:
- Create an endless runner lane and spawn obstacles over time.
- Provide a server spawner and a client distance UI.

Template expectations for template=tycoon:
- Create a minimal tycoon with money, a dropper, and an upgrade button.
- Provide an AutoBuildTycoon server script and a client UI.

Template expectations for template=racing:
- Create a simple racing loop with checkpoints, lap counter, and a finish condition.
- If you include vehicles, they must not be used as obstacles.
- Provide a clean UI and a server-side race state manager.

Template expectations for template=fps:
- Create a simple blaster/shooter game with safe hit detection, health, respawn, and score UI.
- Use Roblox best practices (no client-authoritative damage).
- Provide server validation for hits.

Template expectations for template=seasonal_collector OR any coin collector game:
- Create a COMPLETE game that includes ALL necessary files (see file list below).
- MANDATORY: You MUST generate ALL required files (see file list below). The game will NOT work if files are missing!
- CRITICAL: If user mentions "day to night" or "when coins touched night comes" or "collect coin switch to night then after 1 sec switch to day", implement automatic day-to-night transition when coins are collected, then switch back to day after 1 second.
  * Start with DAY theme: MUST get service first - local Lighting = game:GetService("Lighting"); Lighting.TimeOfDay = 6 (6 AM). NEVER write just "Lighting.TimeOfDay = 6" without getting the service first - this causes "attempt to index nil" error!
  * When coin is collected: Immediately switch to NIGHT (Lighting.TimeOfDay = 0), then after 1 second automatically switch back to DAY (Lighting.TimeOfDay = 6) using spawn(function() wait(1) Lighting.TimeOfDay = 6 end). CRITICAL: Always get service first - local Lighting = game:GetService("Lighting") before using Lighting.TimeOfDay
  * Connect to coin collection: In coin touch handler, switch to night immediately, then spawn a function that waits 1 second and switches back to day
  * This creates continuous flow: collect coin → night → wait 1 sec → day → collect coin → night → wait 1 sec → day (repeating cycle)
- Coins must be spread THROUGHOUT THE ENTIRE TEMPLATE/MAP (not just around spawn) - in water areas, rooms, open areas, grass areas, near houses, everywhere across the whole map with large radius (400-500 studs). MUST create MANY coins (minimum 80-100 coins, ideally 100+ coins) to ensure coins are visible everywhere.
- CRITICAL: Coins MUST have coin.CanTouch = true for collection to work
- Score UI ONLY if user mentions UI/score/display - Set screenGui.DisplayOrder = 10 to appear above chat, format "Score: value" in one line
- DO NOT import or reference any existing repo files. Generate from scratch based on the prompt.

Roblox placement rules (IMPORTANT):
- All UI logic must be a LocalScript under StarterPlayer/StarterPlayerScripts/*.client.lua (NOT StarterGui/*.lua).
- ONLY create UI if user mentions UI/score/display - CRITICAL: UI ScreenGui MUST have DisplayOrder = 10 (or higher) to appear above Roblox chat window: screenGui.DisplayOrder = 10
- Score UI must display "Score: value" format in one line: scoreLabel.Text = "Score: " .. tostring(score.Value)
- Any leaderstats or server data must be created server-side (ServerScriptService) BEFORE clients try to access it.
- Client scripts accessing leaderstats MUST use WaitForChild or check existence first.
- Prefer RemoteEvents for server->client updates.
- COIN COLLECTION: For collectible coins, MUST set coin.CanTouch = true and coin.CanCollide = false. Use debounce pattern in Touched event: local collectingCoins = {}; coin.Touched:Connect(function(hit) if collectingCoins[coin] then return end; collectingCoins[coin] = true; onCoinTouched(coin, player); wait(0.5); collectingCoins[coin] = nil end)

If template=seasonal_collector OR user prompt mentions "day to night collector" or "coin collector", you MUST generate these files:
1. ServerScriptService/AutoBuildSeasonalCollector.server.lua - Creates and spawns coins (MUST create MANY coins - minimum 80-100 coins, ideally 100+ coins to ensure coins are visible everywhere throughout the entire map). MUST include coin.CanTouch = true, coin.CanCollide = false, spread coins across entire map with large radius 400-500 studs, random Y positions including Y:0-3 for water areas, Y:5-15 for ground, Y:16-20 for elevated areas. Coins MUST be in grass areas, near houses, in open fields, everywhere across the template. MUST set DAY theme at the very top (FIRST LINE after services): local Lighting = game:GetService("Lighting"); Lighting.TimeOfDay = 6 (CRITICAL: Get service first using game:GetService("Lighting"), then set TimeOfDay. NEVER write just "Lighting.TimeOfDay = 6" without getting the service first - this causes "attempt to index nil" error).
2. ServerScriptService/CoinService.server.lua - Handles coin collection (Touched event with debounce). ONLY create leaderstats.Score if user mentions score/points/leaderboard. For "day to night" collectors, increment counter for day-night switching. Respawns coins at random positions. MUST get Lighting service first: local Lighting = game:GetService("Lighting") at the top of the script. For "day to night" collectors: switches to NIGHT (Lighting.TimeOfDay = 0) immediately when coin collected, then after 1 second switches back to DAY (Lighting.TimeOfDay = 6) using spawn(function() wait(1) Lighting.TimeOfDay = 6 end).
3. StarterPlayer/StarterPlayerScripts/ScoreUI.client.lua (or SeasonalUI.client.lua) - ONLY generate this file if user mentions UI/score/display. Displays score in UI (MUST have screenGui.DisplayOrder = 10 to appear above chat, format "Score: value" in one line, connects to leaderstats.Score with WaitForChild and Changed event).

CRITICAL: Generate the required files above. You MUST generate at least files 1 and 2 (coin creation and coin collection). File 3 (UI) is ONLY needed if user mentions UI/score/display. Each file has specific responsibilities - coin creation, coin collection/day-night logic, and UI display (if requested).
MANDATORY: Your JSON response MUST include at least files 1 and 2. Include file 3 ONLY if user mentions UI/score/display. Example structure (if UI is requested):
{
  "files": [
    {"path": "ServerScriptService/AutoBuildSeasonalCollector.server.lua", "content": "..."},
    {"path": "ServerScriptService/CoinService.server.lua", "content": "..."},
    {"path": "StarterPlayer/StarterPlayerScripts/ScoreUI.client.lua", "content": "..."}
  ]
}
Example structure (if UI is NOT requested - simple coin collector):
{
  "files": [
    {"path": "ServerScriptService/AutoBuildSeasonalCollector.server.lua", "content": "..."},
    {"path": "ServerScriptService/CoinService.server.lua", "content": "..."}
  ]
}
"""

_REGENERATE_SYSTEM_PROMPT = """You update an existing Roblox Studio script pack based on a change request.

Return ONLY a JSON object with this shape:
{
  "title": string,
  "description": string,
  "files": [{"path": string, "content": string}],
  "setup_instructions": [string],
  "notes": [string]
}

Rules:
- Only output runnable Roblox Lua scripts.
- Preserve file paths unless the change explicitly requires adding a new file.
- If you add a file, choose a correct Roblox path (ServerScriptService, ReplicatedStorage, StarterPlayerScripts, etc.).
- Cars must NOT be used as obstacles.
- Keep changes minimal and consistent with the existing pack.

CRITICAL ROBLOX CODE RULES (MUST FOLLOW):
- CFrame vs Vector3: NEVER assign Vector3 directly to CFrame. ALWAYS use CFrame.new() to create CFrame.
  * CORRECT: part.CFrame = CFrame.new(0, 5, 0) or part.CFrame = CFrame.new(positionVector3)
  * WRONG: part.CFrame = Vector3.new(0, 5, 0) - this causes "Unable to cast Vector3 to CoordinateFrame" error
- leaderstats access: Client scripts MUST wait for leaderstats before accessing.
  * Use: local leaderstats = player:WaitForChild("leaderstats", 10)
  * NEVER directly access player.leaderstats without checking/waiting first.
- COINS/COLLECTIBLES: MUST be REAL 3D Parts (NOT BillboardGui text labels), randomly spread, and visible.
  * Create Part with Shape = Ball, Size = Vector3.new(2, 2, 2)+, Neon material, PointLight for glow
  * CRITICAL: Set coin.CanTouch = true and coin.CanCollide = false for coins to be collectible
  * Use random positions (math.random() with angles/distances), NOT grid patterns
  * NO BillboardGui text labels on coins - users want real collectible objects, not text boxes
  * Use debounce pattern for touch detection: local collectingCoins = {}; if collectingCoins[coin] then return end; collectingCoins[coin] = true; onCoinTouched(coin, player); wait(0.5); collectingCoins[coin] = nil
- UI DISPLAY: Only create/modify UI if user mentions UI/score/display in the change request. Score UI ScreenGui MUST have DisplayOrder = 10 to appear above chat: screenGui.DisplayOrder = 10; Score format must be "Score: value" in one line: scoreLabel.Text = "Score: " .. tostring(score.Value)
"""


def _pick_template_pack(template: str, prompt: str) -> Dict[str, Any]:
    template = (template or "").strip().lower()
    prompt_lower = (prompt or "").strip().lower()
    
    # If no template specified, try to infer from prompt
    if not template:
        if "racing" in prompt_lower or "race" in prompt_lower or "lap" in prompt_lower or "checkpoint" in prompt_lower:
            template = "racing"
        elif "obby" in prompt_lower or "obstacle course" in prompt_lower:
            template = "obby"
        elif "tycoon" in prompt_lower:
            template = "tycoon"
        elif "runner" in prompt_lower or "endless" in prompt_lower:
            template = "endless_runner"
        elif "coin collector" in prompt_lower or "day to night" in prompt_lower or "seasonal" in prompt_lower:
            template = "seasonal_collector"
    
    # IMPORTANT:
    # - seasonal_collector => AI-generated Seasonal Collector game (do NOT import repo files)
    # - seasonal_collector_import => export existing repo scripts (advanced/internal)
    if template in {"seasonal_collector_import", "seasonal_collectorgame", "seasonal_collector_game"}:
        return seasonal_collector_pack()
    if template in {"seasonal_collector"}:
        return seasonal_collector_pack_ai(prompt)
    if template in {"obby"}:
        return obby_pack(prompt)
    if template in {"endless_runner", "runner"}:
        return runner_pack(prompt)
    if template in {"tycoon"}:
        return tycoon_pack(prompt)
    if template in {"racing", "race"}:
        # Racing games should be AI-generated, not use fallback templates
        # The AI will generate based on the prompt which includes racing instructions
        # For now, we'll let AI handle it but could add a racing_pack function later
        return coin_collector_pack(prompt)  # This is just a fallback - AI should generate racing game
    # default
    return coin_collector_pack(prompt)


def _safe_zip_filename(title: str) -> str:
    title = (title or "roblox_pack").strip()
    title = re.sub(r"[^a-zA-Z0-9._-]+", "_", title)
    title = title.strip("._-") or "roblox_pack"
    return f"{title}.zip"


def _normalize_zip_path(path: str) -> str:
    p = (path or "").replace("\\\\", "/").lstrip("/")
    # prevent traversal
    if ".." in p.split("/"):
        raise HTTPException(status_code=400, detail="Invalid file path in pack")
    return p


def _zip_bytes(title: str, files: List[Dict[str, str]]) -> Tuple[str, bytes]:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            path = _normalize_zip_path(str(f.get("path") or ""))
            content = str(f.get("content") or "")
            if not path:
                continue
            zf.writestr(path, content)
    return _safe_zip_filename(title), buf.getvalue()


def _compact_base_files(files: List[Dict[str, str]], change_request: str) -> List[Dict[str, str]]:
    """Reduce context sent to the model so regen works on big packs."""
    if not files:
        return []
    cr = (change_request or "").lower()
    # prioritize likely-relevant files
    priority_keys = [
        ("coin", ["coin", "collect", "wallet", "bank"]),
        ("hazard", ["hazard", "obstacle", "death", "damage"]),
        ("ui", ["ui", "screen", "hud", "leaderstats", "label"]),
        ("data", ["save", "datastore", "data", "level"]),
    ]
    picked: List[Dict[str, str]] = []
    for f in files:
        p = str(f.get("path") or "").lower()
        if any(k in p for k in ["coins", "coin", "hazard", "obstacle", "ui", "datastore", "playerdata"]):
            picked.append(f)

    # if change request hints, filter further
    hinted: List[Dict[str, str]] = []
    for group, kws in priority_keys:
        if any(kw in cr for kw in kws):
            hinted.extend([f for f in picked if group in str(f.get("path") or "").lower()])
    chosen = hinted if hinted else picked

    # cap size
    out: List[Dict[str, str]] = []
    for f in chosen[:10]:
        content = str(f.get("content") or "")
        if len(content) > 8000:
            content = content[:8000] + "\n-- (truncated for AI context)\n"
        out.append({"path": str(f.get("path") or ""), "content": content})
    if not out:
        # fallback to first few
        for f in files[:6]:
            content = str(f.get("content") or "")
            if len(content) > 8000:
                content = content[:8000] + "\n-- (truncated for AI context)\n"
            out.append({"path": str(f.get("path") or ""), "content": content})
    return out


def _looks_like_broken_studio_pack(files: List[Dict[str, str]]) -> bool:
    """Heuristics to detect common Roblox client/server placement mistakes.

    We prefer returning a working fallback pack over a broken AI pack.
    """

    # Detect if server-side leaderstats creation exists somewhere.
    has_server_leaderstats = False
    for f in files or []:
        p = str(f.get("path") or "").replace("\\", "/").lower()
        c = str(f.get("content") or "").lower()
        if p.startswith("serverscriptservice/") and "leaderstats" in c and ("players.playeradded" in c or ":connect(function(player" in c):
            has_server_leaderstats = True
            break

    for f in files or []:
        path = str(f.get("path") or "")
        content = str(f.get("content") or "")
        p = path.replace("\\", "/").lower()
        c = content.lower()

        # CRITICAL: Detect Vector3 to CFrame casting errors
        # Pattern: .CFrame = Vector3.new(...) - this causes "Unable to cast Vector3 to CoordinateFrame" error
        # Simple pattern matching for the most common error case
        if ".cframe" in c and "vector3.new" in c:
            # Check if there's a direct assignment pattern like ".cframe = vector3.new"
            # Pattern: .cframe = (optional whitespace) vector3.new
            broken_pattern = re.search(r'\.cframe\s*=\s*vector3\.new', c)
            if broken_pattern:
                # Found broken pattern, but check if CFrame.new wraps it on same line
                # This is a simple heuristic - if the line has CFrame.new, it's probably fine
                lines = content.split('\n')
                for line in lines:
                    if broken_pattern.group() in line.lower():
                        if "cframe.new" not in line.lower():
                            return True
                        break

        # CRITICAL: Detect direct leaderstats access without WaitForChild (causes "not a valid member" error)
        # Pattern: player.leaderstats or LocalPlayer.leaderstats (without WaitForChild)
        if ("starterplayerscripts" in p or "playerscripts" in p or "startergui" in p):
            # Check for direct access patterns
            if (".leaderstats" in c or "localplayer.leaderstats" in c or "player.leaderstats" in c):
                # But allow if WaitForChild is used
                if "waitforchild(\"leaderstats\")" not in c and "waitforchild('leaderstats')" not in c:
                    # Direct access without waiting - this will crash
                    return True

        # Client scripts should not be responsible for creating leaderstats (server-owned pattern).
        if "starterplayerscripts" in p or "playerscripts" in p or "startergui" in p:
            if "players.playeradded" in c or "playeradded:connect" in c or "playeradded.connect" in c:
                return True
            if "instance.new(\"folder\")" in c and "leaderstats" in c:
                return True
            if "waitforchild(\"leaderstats\")" in c and ("player." in c or "localplayer" in c) and not has_server_leaderstats:
                # Not always wrong, but frequently indicates the pack forgot to create leaderstats server-side.
                # Treat as suspicious enough to fallback.
                return True

        # Files placed in StarterGui should almost never be plain .lua scripts in beginner packs.
        # Prefer StarterPlayerScripts LocalScripts for UI.
        if p.startswith("startergui/") and p.endswith(".lua"):
            return True

    return False


def _seasonal_mvp_prompt(user_prompt: str) -> str:
    # Keep this short to reduce chances of broken packs.
    return (
        "Build a minimal but complete Seasonal Collector game that works when copy/pasted into a NEW Roblox place.\n"
        "Use the required file paths listed in the system rules.\n"
        "Implement: (1) AutoBuild map/trail, (2) coin collection, (3) obstacles/hazards, (4) season cycle, (5) UI.\n"
        "Focus on correctness and Roblox placement rules first, then features.\n\n"
        f"User requirements:\n{user_prompt}"
    )


_REPAIR_SYSTEM_PROMPT = """You repair a Roblox Studio script pack that was generated incorrectly.

Return ONLY a JSON object with this shape:
{
  "title": string,
  "description": string,
  "files": [{"path": string, "content": string}],
  "setup_instructions": [string],
  "notes": [string]
}

Rules:
- Preserve the intent of the original prompt and template.
- Fix Roblox placement mistakes (ServerScriptService vs StarterPlayerScripts).
- Ensure leaderstats are created server-side if used.
- Remove any infinite yield risks (e.g., waiting for leaderstats without creating them).
- Cars must NOT be used as obstacles.

CRITICAL FIXES (MUST APPLY - SEARCH AND FIX ALL OCCURRENCES):

1. CFrame vs Vector3 - FIND AND FIX ALL:
   * Search entire codebase for: ".CFrame = Vector3" or ".cframe = vector3"
   * WRONG: part.CFrame = Vector3.new(0, 5, 0) - causes "Unable to cast Vector3 to CoordinateFrame" error
   * FIX TO: part.CFrame = CFrame.new(0, 5, 0) - ALWAYS use CFrame.new() for CFrame assignments
   * ALTERNATIVE: part.Position = Vector3.new(0, 5, 0) - Use Position property if you only need position
   * Check EVERY file - this error appears in multiple places
   * Common locations: teleporting players, positioning parts, spawning objects

2. leaderstats access - FIND AND FIX ALL:
   * Search entire codebase for: "player.leaderstats" or "LocalPlayer.leaderstats" without WaitForChild
   * WRONG: local stats = player.leaderstats - causes "leaderstats is not a valid member" error
   * FIX TO: local leaderstats = player:WaitForChild("leaderstats", 10) - ALWAYS wait first
   * ALTERNATIVE: if player:FindFirstChild("leaderstats") then local stats = player.leaderstats end
   * Ensure server creates leaderstats FIRST in Players.PlayerAdded event
   * Check ALL client scripts (StarterPlayerScripts, StarterGui) - this error is common there

3. Services - FIND AND FIX ALL:
   * Search for: "Lighting.", "Players.", "Workspace." used directly without game:GetService()
   * WRONG: Lighting.TimeOfDay = 6 - causes "attempt to index nil" error
   * FIX TO: local Lighting = game:GetService("Lighting"); Lighting.TimeOfDay = 6
   * Check EVERY file that uses services
"""


def _repair_pack_once(*, prompt: str, template: str, reason: str, candidate: Dict[str, Any]) -> Dict[str, Any]:
    # Ask the model to repair its own output.
    return generate_json(
        prompt="Repair the provided pack JSON to be runnable in Roblox Studio.",
        system_prompt=_REPAIR_SYSTEM_PROMPT,
        temperature=0.1,
        max_tokens=1600,
        extra_context={
            "template": template,
            "original_prompt": prompt,
            "reason": reason,
            "candidate_pack": candidate,
        },
    )


@router.post("/api/roblox/generate", response_model=RobloxGenerateResponse)
def roblox_generate(req: RobloxGenerateRequest, user: Dict[str, Any] = Depends(get_current_user)) -> RobloxGenerateResponse:
    prompt = (req.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    require_ai = bool(req.require_ai) or bool(settings.require_ai)

    # Template handling:
    # - If explicitly provided by user → Use it (user wants specific template behavior)
    # - If not provided → Let AI analyze prompt naturally without template restrictions
    # Template is only used for fallback templates when AI is unavailable/fails
    # AI generation should always analyze the natural language prompt, template is just a hint
    template = req.template or ""
    
    # Offline fallback: always available (only used when AI fails or unavailable)
    # Fallback uses simple keyword detection, but AI generation analyzes prompt naturally
    fallback = _pick_template_pack(template, prompt)

    # If no AI key, return fallback.
    if not settings.openai_api_key:
        if require_ai:
            raise HTTPException(status_code=503, detail="AI is required but OPENAI_API_KEY is not configured.")
        fallback["notes"] = list(fallback.get("notes") or []) + ["AI: OFF (no OPENAI_API_KEY configured)"]
        sid = session_store.create(fallback)
        return RobloxGenerateResponse(success=True, session_id=sid, **fallback)

    try:
        # AI Generation: Let AI analyze the prompt naturally
        # If template is provided, it's used as a hint in system prompt, but AI still analyzes the actual prompt
        # If template is empty, AI analyzes the prompt completely on its own
        ai_template = template if template.strip() else None
        data = generate_json(
            prompt=prompt,
            system_prompt=_ROBLOX_SYSTEM_PROMPT,
            temperature=float(req.temperature),
            max_tokens=int(req.max_tokens),
            extra_context={"template": ai_template},  # None/empty = let AI analyze naturally
        )

        # Minimal validation + merge safety notes
        title = str(data.get("title") or fallback["title"])
        description = str(data.get("description") or fallback["description"])
        files = data.get("files")
        setup_instructions = data.get("setup_instructions")
        notes = data.get("notes") or []

        if not isinstance(files, list) or not files:
            if require_ai:
                raise HTTPException(status_code=502, detail="AI returned an invalid pack (missing files).")
            return RobloxGenerateResponse(success=True, **fallback)

        # Normalize and validate files
        norm_files = []
        skipped_files = []
        for f in files:
            if not isinstance(f, dict):
                skipped_files.append("Invalid file format (not a dict)")
                continue
            path = str(f.get("path") or "").strip()
            content = str(f.get("content") or "").strip()
            if not path:
                skipped_files.append(f"File missing path: {f}")
                continue
            if not content:
                skipped_files.append(f"File '{path}' has empty content")
                continue
            # Check if content is too short (likely placeholder or error)
            if len(content) < 50:
                skipped_files.append(f"File '{path}' content too short ({len(content)} chars) - likely incomplete")
                continue
            norm_files.append({"path": path, "content": content})

        if not norm_files:
            # Provide helpful error message
            skip_reason = f"All {len(files)} files were invalid. Reasons: {', '.join(skipped_files[:3])}" if skipped_files else "No valid files found in response"
            if require_ai:
                raise HTTPException(
                    status_code=502, 
                    detail=f"AI returned an invalid pack (empty files). {skip_reason}. Please try again or simplify your prompt."
                )
            # Log the issue for debugging
            print(f"AI generation failed - no valid files. Skipped: {skipped_files}")
            return RobloxGenerateResponse(success=True, **fallback)

        # If AI produced an obviously broken pack, return a known-good fallback.
        if _looks_like_broken_studio_pack(norm_files):
            # Try one repair pass (AI-only mode).
            repaired = _repair_pack_once(
                prompt=prompt,
                template=template,
                reason="Broken pack heuristics matched (client/server placement).",
                candidate=data,
            )
            files2 = repaired.get("files")
            if isinstance(files2, list):
                norm2 = []
                for f in files2:
                    if isinstance(f, dict):
                        p = str(f.get("path") or "").strip()
                        c = str(f.get("content") or "")
                        if p and c:
                            norm2.append({"path": p, "content": c})
                if norm2 and not _looks_like_broken_studio_pack(norm2):
                    data = repaired
                    norm_files = norm2
                else:
                    # Try one more retry for seasonal_collector: regenerate as MVP from scratch (not repair).
                    if str(template).strip().lower() == "seasonal_collector":
                        retry = generate_json(
                            prompt=_seasonal_mvp_prompt(prompt),
                            system_prompt=_ROBLOX_SYSTEM_PROMPT,
                            temperature=0.15,
                            max_tokens=max(1400, int(req.max_tokens)),
                            extra_context={"template": template, "retry": "mvp_regen_from_scratch"},
                        )
                        files3 = retry.get("files")
                        if isinstance(files3, list):
                            norm3 = []
                            for f3 in files3:
                                if isinstance(f3, dict):
                                    p3 = str(f3.get("path") or "").strip()
                                    c3 = str(f3.get("content") or "")
                                    if p3 and c3:
                                        norm3.append({"path": p3, "content": c3})
                            if norm3 and not _looks_like_broken_studio_pack(norm3):
                                data = retry
                                norm_files = norm3
                            else:
                                # Even retry failed - use fallback instead of erroring
                                if require_ai:
                                    raise HTTPException(status_code=502, detail="AI generated a broken pack (even after repair and retry). Please try a different prompt or simplify your request.")
                                sid = session_store.create(fallback)
                                fallback["notes"] = list(fallback.get("notes") or []) + ["AI: FAILED → fallback used"]
                                return RobloxGenerateResponse(success=True, session_id=sid, **fallback)
                        else:
                            # Retry returned invalid - use fallback
                            if require_ai:
                                raise HTTPException(status_code=502, detail="AI generated a broken pack (even after repair and retry). Please try a different prompt.")
                            sid = session_store.create(fallback)
                            fallback["notes"] = list(fallback.get("notes") or []) + ["AI: FAILED → fallback used"]
                            return RobloxGenerateResponse(success=True, session_id=sid, **fallback)
                    else:
                        # For other templates, use fallback instead of erroring (better UX)
                        if require_ai:
                            raise HTTPException(status_code=502, detail="AI generated a broken pack (even after repair). Please try a simpler prompt or different game type.")
                        sid = session_store.create(fallback)
                        fallback["notes"] = list(fallback.get("notes") or []) + ["AI: FAILED → fallback used"]
                        return RobloxGenerateResponse(success=True, session_id=sid, **fallback)
            else:
                if require_ai:
                    if str(template).strip().lower() == "seasonal_collector":
                        retry = generate_json(
                            prompt=_seasonal_mvp_prompt(prompt),
                            system_prompt=_ROBLOX_SYSTEM_PROMPT,
                            temperature=0.15,
                            max_tokens=max(1400, int(req.max_tokens)),
                            extra_context={"template": template, "retry": "mvp_regen_from_scratch"},
                        )
                        files3 = retry.get("files")
                        if isinstance(files3, list):
                            norm3 = []
                            for f3 in files3:
                                if isinstance(f3, dict):
                                    p3 = str(f3.get("path") or "").strip()
                                    c3 = str(f3.get("content") or "")
                                    if p3 and c3:
                                        norm3.append({"path": p3, "content": c3})
                            if norm3 and not _looks_like_broken_studio_pack(norm3):
                                data = retry
                                norm_files = norm3
                            else:
                                # Even retry failed - use fallback instead of erroring
                                if require_ai:
                                    raise HTTPException(status_code=502, detail="AI generated a broken pack (repair failed, retry failed). Please try a simpler prompt.")
                                sid = session_store.create(fallback)
                                fallback["notes"] = list(fallback.get("notes") or []) + ["AI: FAILED → fallback used"]
                                return RobloxGenerateResponse(success=True, session_id=sid, **fallback)
                        else:
                            # Retry returned invalid - use fallback
                            if require_ai:
                                raise HTTPException(status_code=502, detail="AI generated a broken pack (repair failed, retry failed). Please try a different prompt.")
                            sid = session_store.create(fallback)
                            fallback["notes"] = list(fallback.get("notes") or []) + ["AI: FAILED → fallback used"]
                            return RobloxGenerateResponse(success=True, session_id=sid, **fallback)
                    else:
                        # For other templates, use fallback instead of erroring
                        if require_ai:
                            raise HTTPException(status_code=502, detail="AI generated a broken pack (repair failed). Please try a simpler prompt.")
                        sid = session_store.create(fallback)
                        fallback["notes"] = list(fallback.get("notes") or []) + ["AI: FAILED → fallback used"]
                        return RobloxGenerateResponse(success=True, session_id=sid, **fallback)
                sid = session_store.create(fallback)
                fallback["notes"] = list(fallback.get("notes") or []) + ["AI: FAILED → fallback used"]
                return RobloxGenerateResponse(success=True, session_id=sid, **fallback)

        if not isinstance(setup_instructions, list) or not setup_instructions:
            setup_instructions = fallback["setup_instructions"]

        if not isinstance(notes, list):
            notes = fallback["notes"]
        else:
            notes = [str(x) for x in notes]

        pack = RobloxGenerateResponse(
            success=True,
            title=title,
            description=description,
            files=norm_files,
            setup_instructions=[str(x) for x in setup_instructions],
            notes=notes,
        )
        sid = session_store.create(pack.model_dump())
        pack.session_id = sid
        return pack
    except HTTPException as e:
        # Re-raise HTTP exceptions (they're intentional errors with proper status codes)
        if require_ai:
            raise
        sid = session_store.create(fallback)
        fallback["notes"] = list(fallback.get("notes") or []) + [f"AI: FAILED ({str(e.detail)[:100]}) → fallback used"]
        return RobloxGenerateResponse(success=True, session_id=sid, **fallback)
    except Exception as e:
        # Catch any other exceptions (API errors, timeouts, parsing errors, etc.)
        import traceback
        error_msg = str(e)
        error_type = type(e).__name__
        
        # Log full error for debugging (especially important in deployment)
        print(f"ERROR in roblox_generate [{error_type}]: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        print(f"Prompt length: {len(prompt)}, Template: {template or 'none'}")
        
        # Provide helpful error messages based on error type
        if "timeout" in error_msg.lower() or "timed out" in error_msg.lower() or "timeout" in error_type.lower():
            error_detail = "AI request timed out. Custom prompts can take longer. Please try: 1) Simplifying your prompt, 2) Breaking it into smaller requests, or 3) Try again (sometimes it works on retry)."
        elif "rate limit" in error_msg.lower() or "429" in error_msg.lower():
            error_detail = "AI rate limit exceeded. Please wait a moment and try again."
        elif "api key" in error_msg.lower() or "authentication" in error_msg.lower() or "401" in error_msg.lower() or "403" in error_msg.lower():
            error_detail = "AI API key issue. Please check your OpenAI API key configuration in deployment settings."
        elif "json" in error_msg.lower() or "JSONDecodeError" in error_type:
            error_detail = "AI returned invalid response format. Please try again or simplify your prompt."
        elif "502" in error_msg.lower() or "Bad Gateway" in error_msg:
            error_detail = "Deployment timeout or upstream service issue. The request took too long. Please try a simpler prompt or contact support."
        else:
            error_detail = f"AI generation error: {error_msg[:200]}"
        
        if require_ai:
            raise HTTPException(status_code=502, detail=error_detail)
        sid = session_store.create(fallback)
        fallback["notes"] = list(fallback.get("notes") or []) + [f"AI: ERROR ({error_detail[:50]}) → fallback used"]
        return RobloxGenerateResponse(success=True, session_id=sid, **fallback)


@router.post("/api/roblox/regenerate", response_model=RobloxGenerateResponse)
def roblox_regenerate(req: RobloxRegenerateRequest, user: Dict[str, Any] = Depends(get_current_user)) -> RobloxGenerateResponse:
    prompt = (req.prompt or "").strip()
    change = (req.change_request or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")
    if not change:
        raise HTTPException(status_code=400, detail="change_request is required")

    require_ai = bool(req.require_ai) or bool(settings.require_ai)

    # Prefer session-based regen to avoid sending huge file packs over the network.
    base_pack_from_session = None
    if req.session_id:
        base_pack_from_session = session_store.get(req.session_id)

    if base_pack_from_session and isinstance(base_pack_from_session, dict):
        base_files = list(base_pack_from_session.get("files") or [])
        base_title = str(base_pack_from_session.get("title") or req.base_title or "")
        base_description = str(base_pack_from_session.get("description") or req.base_description or "")
        base_setup = list(base_pack_from_session.get("setup_instructions") or [])
        base_notes = list(base_pack_from_session.get("notes") or [])
    else:
        base_files = [f.model_dump() for f in (req.base_files or [])]
        base_title = req.base_title or ""
        base_description = req.base_description or ""
        base_setup = []
        base_notes = []

    base_pack = {
        "title": base_title,
        "description": base_description,
        "files": base_files,
        "setup_instructions": base_setup,
        "notes": base_notes,
    }

    # If no AI key, return base pack (or fallback) with note.
    if not settings.openai_api_key:
        if require_ai:
            raise HTTPException(status_code=503, detail="AI is required but OPENAI_API_KEY is not configured.")
        if base_files:
            base_pack["title"] = base_pack["title"] or "Roblox Pack (Offline)"
            base_pack["description"] = base_pack["description"] or "Offline mode: regeneration not available."
            base_pack["notes"] = ["Offline mode: set OPENAI_API_KEY to enable regeneration."]  # type: ignore[assignment]
            sid = session_store.create(base_pack)
            return RobloxGenerateResponse(success=True, session_id=sid, **base_pack)
        fb = _pick_template_pack(req.template, prompt)
        fb["notes"] = list(fb.get("notes") or []) + ["Offline mode: set OPENAI_API_KEY to enable regeneration."]
        sid = session_store.create(fb)
        return RobloxGenerateResponse(success=True, session_id=sid, **fb)

    # Build AI context
    compact_files = _compact_base_files(base_files, change)
    context = {
        "prompt": prompt,
        "change_request": change,
        "template": req.template,
        "base_title": base_title,
        "base_description": base_description,
        "base_files_compact": compact_files,
        "all_paths": [str(f.get("path") or "") for f in base_files],
    }

    fallback = _pick_template_pack(req.template, prompt)

    try:
        data = generate_json(
            prompt="Apply the change_request to the existing pack. Return the updated pack JSON.",
            system_prompt=_REGENERATE_SYSTEM_PROMPT,
            temperature=float(req.temperature),
            max_tokens=int(req.max_tokens),
            extra_context=context,
        )

        title = str(data.get("title") or base_title or fallback["title"])
        description = str(data.get("description") or base_description or fallback["description"])
        files = data.get("files")
        setup_instructions = data.get("setup_instructions") or fallback["setup_instructions"]
        notes = data.get("notes") or []

        if not isinstance(files, list) or not files:
            if require_ai:
                raise HTTPException(status_code=502, detail="AI returned an invalid pack (missing files).")
            return RobloxGenerateResponse(success=True, **fallback)

        norm_files: List[Dict[str, str]] = []
        for f in files:
            if not isinstance(f, dict):
                continue
            path = str(f.get("path") or "").strip()
            content = str(f.get("content") or "")
            if not path or not content:
                continue
            norm_files.append({"path": path, "content": content})
        if not norm_files:
            if require_ai:
                raise HTTPException(status_code=502, detail="AI returned an invalid pack (empty files).")
            return RobloxGenerateResponse(success=True, **fallback)

        if _looks_like_broken_studio_pack(norm_files):
            repaired = _repair_pack_once(
                prompt=prompt,
                template=req.template,
                reason="Broken pack heuristics matched during regenerate.",
                candidate=data,
            )
            files2 = repaired.get("files")
            if isinstance(files2, list):
                norm2 = []
                for f in files2:
                    if isinstance(f, dict):
                        p = str(f.get("path") or "").strip()
                        c = str(f.get("content") or "")
                        if p and c:
                            norm2.append({"path": p, "content": c})
                if norm2 and not _looks_like_broken_studio_pack(norm2):
                    data = repaired
                    norm_files = norm2
                else:
                    if require_ai:
                        raise HTTPException(status_code=502, detail="AI regeneration produced a broken pack (even after repair).")
                    sid = session_store.create(fallback)
                    fallback["notes"] = list(fallback.get("notes") or []) + ["AI: FAILED → fallback used"]
                    return RobloxGenerateResponse(success=True, session_id=sid, **fallback)
            else:
                if require_ai:
                    raise HTTPException(status_code=502, detail="AI regeneration produced a broken pack (repair failed).")
                sid = session_store.create(fallback)
                fallback["notes"] = list(fallback.get("notes") or []) + ["AI: FAILED → fallback used"]
                return RobloxGenerateResponse(success=True, session_id=sid, **fallback)

        if not isinstance(setup_instructions, list) or not setup_instructions:
            setup_instructions = fallback["setup_instructions"]

        if not isinstance(notes, list):
            notes = fallback.get("notes") or []
        else:
            notes = [str(x) for x in notes]

        pack = RobloxGenerateResponse(
            success=True,
            title=title,
            description=description,
            files=norm_files,
            setup_instructions=[str(x) for x in setup_instructions],
            notes=notes,
        )
        sid = session_store.create(pack.model_dump())
        pack.session_id = sid
        return pack
    except HTTPException:
        if require_ai:
            raise
        sid = session_store.create(fallback)
        fallback["notes"] = list(fallback.get("notes") or []) + ["AI: FAILED → fallback used"]
        return RobloxGenerateResponse(success=True, session_id=sid, **fallback)


@router.post("/api/roblox/zip")
def roblox_zip(req: RobloxZipRequest, user: Dict[str, Any] = Depends(get_current_user)):
    files = [f.model_dump() for f in req.files]
    filename, data = _zip_bytes(req.title, files)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/api/roblox/generate_zip")
def roblox_generate_zip(req: RobloxGenerateRequest, user: Dict[str, Any] = Depends(get_current_user)):
    pack = roblox_generate(req)
    filename, data = _zip_bytes(pack.title, [f.model_dump() for f in pack.files])
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/roblox/sessions/{session_id}")
def roblox_session_get(session_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    pack = session_store.get(session_id)
    if not pack:
        raise HTTPException(status_code=404, detail="session not found")
    return pack


@router.get("/api/roblox/sessions/{session_id}/plugin.rbxmx")
def roblox_session_plugin(session_id: str, request: Request, user: Dict[str, Any] = Depends(get_current_user)):
    pack = session_store.get(session_id)
    if not pack:
        raise HTTPException(status_code=404, detail="session not found")

    base_url = str(request.base_url).rstrip("/")
    xml = generate_import_plugin_rbxmx(base_url=base_url, session_id=session_id)
    filename = f"VibeCodingImporter_{session_id[:8]}.rbxmx"
    return StreamingResponse(
        io.BytesIO(xml.encode("utf-8")),
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'},
    )
