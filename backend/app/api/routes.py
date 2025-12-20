from __future__ import annotations

import io
import re
import zipfile
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.api.models import (
    AIChatRequest,
    AIChatResponse,
    RobloxGenerateRequest,
    RobloxGenerateResponse,
    RobloxRegenerateRequest,
    RobloxZipRequest,
)
from app.services.fallback_templates import (
    coin_collector_pack,
    obby_pack,
    runner_pack,
    seasonal_collector_pack_ai,
    tycoon_pack,
)
from app.services.openai_service import chat as ai_chat
from app.services.openai_service import generate_json
from app.services.repo_templates import seasonal_collector_pack
from app.services.session_store import session_store
from app.services.studio_plugin import generate_import_plugin_rbxmx
from app.settings import settings

router = APIRouter()

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


_ROBLOX_SYSTEM_PROMPT = """You generate Roblox Studio game scripts from a text prompt.

Return ONLY a JSON object with this shape:
{
  "title": string,
  "description": string,
  "files": [{"path": string, "content": string}],
  "setup_instructions": [string],
  "notes": [string]
}

CRITICAL: The "files" array MUST contain ALL required files for the game to work. For coin collector/day-to-night collector games, you MUST include ALL 3 files (see template expectations below). DO NOT omit any files - the game will not function if files are missing!

Rules:
- Output runnable Roblox Lua scripts.
- Use clear, copy/paste-friendly code.
- Do NOT reference external assets unless necessary.
- Include at least one server script and one client UI script.
- Cars must NOT be used as obstacles.
- Keep it simple (prototype quality), but playable.
- CRITICAL: For coin collector games (user mentions "coin collector", "day to night collector", or similar), you MUST generate ALL required files in the "files" array. The game will NOT work if any file is missing. See template expectations below for complete file list.

CRITICAL ROBLOX CODE RULES (MUST FOLLOW):
- Services: ALWAYS get services using game:GetService() before using them. NEVER use service names directly without getting them first.
  * CORRECT: local Lighting = game:GetService("Lighting"); Lighting.TimeOfDay = 6
  * WRONG: Lighting.TimeOfDay = 6 - this causes "attempt to index nil with 'TimeOfDay'" error because Lighting is nil
  * Required services must be retrieved: local Lighting = game:GetService("Lighting"), local Players = game:GetService("Players"), local Workspace = game:GetService("Workspace"), etc.
- CFrame vs Vector3: NEVER assign Vector3 directly to CFrame. ALWAYS use CFrame.new() to create CFrame.
  * CORRECT: part.CFrame = CFrame.new(0, 5, 0) or part.CFrame = CFrame.new(positionVector3)
  * WRONG: part.CFrame = Vector3.new(0, 5, 0) - this causes "Unable to cast Vector3 to CoordinateFrame" error
  * Use part.Position = Vector3.new(x, y, z) if you only need position (not rotation)
  * Use part.CFrame = CFrame.new(x, y, z) if you need full CFrame (position + rotation)
- leaderstats access: leaderstats is ONLY created server-side. Client scripts MUST wait for it.
  * Server (ServerScriptService): Create leaderstats folder in Players.PlayerAdded event
    Example: local leaderstats = Instance.new("Folder"); leaderstats.Name = "leaderstats"; leaderstats.Parent = player
  * Client (StarterPlayerScripts): ALWAYS use WaitForChild before accessing leaderstats
    Example: local leaderstats = player:WaitForChild("leaderstats", 10)
    NEVER directly access player.leaderstats without checking/waiting - causes "leaderstats is not a valid member" error
  * Check if leaderstats exists: if player:FindFirstChild("leaderstats") then ... end
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
- Score UI MUST appear above chat: Set screenGui.DisplayOrder = 10; Score format: "Score: value" in one line
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
- Score UI MUST have screenGui.DisplayOrder = 10 to appear above chat, format "Score: value" in one line
- DO NOT import or reference any existing repo files. Generate from scratch based on the prompt.

Roblox placement rules (IMPORTANT):
- All UI logic must be a LocalScript under StarterPlayer/StarterPlayerScripts/*.client.lua (NOT StarterGui/*.lua).
- CRITICAL: UI ScreenGui MUST have DisplayOrder = 10 (or higher) to appear above Roblox chat window: screenGui.DisplayOrder = 10
- Score UI must display "Score: value" format in one line: scoreLabel.Text = "Score: " .. tostring(score.Value)
- Any leaderstats or server data must be created server-side (ServerScriptService) BEFORE clients try to access it.
- Client scripts accessing leaderstats MUST use WaitForChild or check existence first.
- Prefer RemoteEvents for server->client updates.
- COIN COLLECTION: For collectible coins, MUST set coin.CanTouch = true and coin.CanCollide = false. Use debounce pattern in Touched event: local collectingCoins = {}; coin.Touched:Connect(function(hit) if collectingCoins[coin] then return end; collectingCoins[coin] = true; onCoinTouched(coin, player); wait(0.5); collectingCoins[coin] = nil end)

If template=seasonal_collector OR user prompt mentions "day to night collector" or "coin collector", you MUST generate ALL of these files (complete game pack):
1. ServerScriptService/AutoBuildSeasonalCollector.server.lua - Creates and spawns coins (MUST create MANY coins - minimum 80-100 coins, ideally 100+ coins to ensure coins are visible everywhere throughout the entire map). MUST include coin.CanTouch = true, coin.CanCollide = false, spread coins across entire map with large radius 400-500 studs, random Y positions including Y:0-3 for water areas, Y:5-15 for ground, Y:16-20 for elevated areas. Coins MUST be in grass areas, near houses, in open fields, everywhere across the template. MUST set DAY theme at the very top (FIRST LINE after services): local Lighting = game:GetService("Lighting"); Lighting.TimeOfDay = 6 (CRITICAL: Get service first using game:GetService("Lighting"), then set TimeOfDay. NEVER write just "Lighting.TimeOfDay = 6" without getting the service first - this causes "attempt to index nil" error).
2. ServerScriptService/CoinService.server.lua - Handles coin collection (Touched event with debounce), creates leaderstats.Score, increments score on collection, switches to NIGHT (Lighting.TimeOfDay = 0) immediately when coin collected, then after 1 second switches back to DAY (Lighting.TimeOfDay = 6) using spawn(function() wait(1) Lighting.TimeOfDay = 6 end), respawns coins at random positions. MUST get Lighting service first: local Lighting = game:GetService("Lighting") at the top of the script.
3. StarterPlayer/StarterPlayerScripts/ScoreUI.client.lua (or SeasonalUI.client.lua) - Displays score in UI (MUST have screenGui.DisplayOrder = 10 to appear above chat, format "Score: value" in one line, connects to leaderstats.Score with WaitForChild and Changed event).

CRITICAL: Generate ALL 3 files above. The game will NOT work if any file is missing. Each file has specific responsibilities - coin creation, coin collection/day-night logic, and UI display.
MANDATORY: Your JSON response MUST include all 3 files in the "files" array. DO NOT skip any file. Example structure:
{
  "files": [
    {"path": "ServerScriptService/AutoBuildSeasonalCollector.server.lua", "content": "..."},
    {"path": "ServerScriptService/CoinService.server.lua", "content": "..."},
    {"path": "StarterPlayer/StarterPlayerScripts/ScoreUI.client.lua", "content": "..."}
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
- UI DISPLAY: Score UI ScreenGui MUST have DisplayOrder = 10 to appear above chat: screenGui.DisplayOrder = 10; Score format must be "Score: value" in one line: scoreLabel.Text = "Score: " .. tostring(score.Value)
"""


def _pick_template_pack(template: str, prompt: str) -> Dict[str, Any]:
    template = (template or "").strip().lower()
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

CRITICAL FIXES (MUST APPLY):
- CFrame vs Vector3: Find ALL instances where Vector3 is assigned to CFrame and fix them.
  * WRONG: part.CFrame = Vector3.new(0, 5, 0) - causes "Unable to cast Vector3 to CoordinateFrame" error
  * FIX TO: part.CFrame = CFrame.new(0, 5, 0) or part.Position = Vector3.new(0, 5, 0)
  * Search for patterns: ".CFrame = Vector3" or ".CFrame = position" (where position is Vector3)
  * Use CFrame.new() when assigning to CFrame property
- leaderstats access: Fix client scripts that directly access leaderstats without waiting.
  * WRONG: local stats = player.leaderstats - causes "leaderstats is not a valid member" error
  * FIX TO: local leaderstats = player:WaitForChild("leaderstats", 10)
  * Ensure server creates leaderstats FIRST in Players.PlayerAdded event
  * Client scripts MUST use WaitForChild or FindFirstChild before accessing
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
def roblox_generate(req: RobloxGenerateRequest) -> RobloxGenerateResponse:
    prompt = (req.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    require_ai = bool(req.require_ai) or bool(settings.require_ai)

    # Offline fallback: always available.
    fallback = _pick_template_pack(req.template, prompt)

    # If no AI key, return fallback.
    if not settings.openai_api_key:
        if require_ai:
            raise HTTPException(status_code=503, detail="AI is required but OPENAI_API_KEY is not configured.")
        fallback["notes"] = list(fallback.get("notes") or []) + ["AI: OFF (no OPENAI_API_KEY configured)"]
        sid = session_store.create(fallback)
        return RobloxGenerateResponse(success=True, session_id=sid, **fallback)

    try:
        data = generate_json(
            prompt=prompt,
            system_prompt=_ROBLOX_SYSTEM_PROMPT,
            temperature=float(req.temperature),
            max_tokens=int(req.max_tokens),
            extra_context={"template": req.template},
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

        # Normalize
        norm_files = []
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

        # If AI produced an obviously broken pack, return a known-good fallback.
        if _looks_like_broken_studio_pack(norm_files):
            # Try one repair pass (AI-only mode).
            repaired = _repair_pack_once(
                prompt=prompt,
                template=req.template,
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
                    if require_ai:
                        # One more retry for seasonal_collector: regenerate as MVP from scratch (not repair).
                        if str(req.template).strip().lower() == "seasonal_collector":
                            retry = generate_json(
                                prompt=_seasonal_mvp_prompt(prompt),
                                system_prompt=_ROBLOX_SYSTEM_PROMPT,
                                temperature=0.15,
                                max_tokens=max(1400, int(req.max_tokens)),
                                extra_context={"template": req.template, "retry": "mvp_regen_from_scratch"},
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
                                    raise HTTPException(status_code=502, detail="AI generated a broken pack (even after repair and retry).")
                            else:
                                raise HTTPException(status_code=502, detail="AI generated a broken pack (even after repair and retry).")
                        else:
                            raise HTTPException(status_code=502, detail="AI generated a broken pack (even after repair).")
                    sid = session_store.create(fallback)
                    fallback["notes"] = list(fallback.get("notes") or []) + ["AI: FAILED → fallback used"]
                    return RobloxGenerateResponse(success=True, session_id=sid, **fallback)
            else:
                if require_ai:
                    if str(req.template).strip().lower() == "seasonal_collector":
                        retry = generate_json(
                            prompt=_seasonal_mvp_prompt(prompt),
                            system_prompt=_ROBLOX_SYSTEM_PROMPT,
                            temperature=0.15,
                            max_tokens=max(1400, int(req.max_tokens)),
                            extra_context={"template": req.template, "retry": "mvp_regen_from_scratch"},
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
                                raise HTTPException(status_code=502, detail="AI generated a broken pack (repair failed, retry failed).")
                        else:
                            raise HTTPException(status_code=502, detail="AI generated a broken pack (repair failed, retry failed).")
                    else:
                        raise HTTPException(status_code=502, detail="AI generated a broken pack (repair failed).")
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
        error_msg = f"AI generation error: {str(e)}"
        print(f"ERROR in roblox_generate: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        if require_ai:
            raise HTTPException(status_code=502, detail=error_msg)
        sid = session_store.create(fallback)
        fallback["notes"] = list(fallback.get("notes") or []) + [f"AI: ERROR → fallback used"]
        return RobloxGenerateResponse(success=True, session_id=sid, **fallback)


@router.post("/api/roblox/regenerate", response_model=RobloxGenerateResponse)
def roblox_regenerate(req: RobloxRegenerateRequest) -> RobloxGenerateResponse:
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
def roblox_zip(req: RobloxZipRequest):
    files = [f.model_dump() for f in req.files]
    filename, data = _zip_bytes(req.title, files)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/api/roblox/generate_zip")
def roblox_generate_zip(req: RobloxGenerateRequest):
    pack = roblox_generate(req)
    filename, data = _zip_bytes(pack.title, [f.model_dump() for f in pack.files])
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/roblox/sessions/{session_id}")
def roblox_session_get(session_id: str):
    pack = session_store.get(session_id)
    if not pack:
        raise HTTPException(status_code=404, detail="session not found")
    return pack


@router.get("/api/roblox/sessions/{session_id}/plugin.rbxmx")
def roblox_session_plugin(session_id: str, request: Request):
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
