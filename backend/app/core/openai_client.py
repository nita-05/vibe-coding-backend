from openai import OpenAI
from app.config import settings
from typing import Dict, Any, List
import json
import re
import time
import hashlib


class OpenAIClient:
    def __init__(self):
        # Keep requests snappy (Roblox players feel latency immediately)
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=18.0,
            max_retries=1,
        )
        self.model = settings.openai_model
        self._chat_cache = {}  # key -> (expires_at, message)

    def generate_roblox_script(
        self,
        prompt: str,
        blueprint_id: str = None,
        settings: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate Roblox Lua script from text prompt using OpenAI.
        Returns structured JSON with Lua script, modules, and metadata.
        """
        
        system_prompt = self._build_system_prompt(blueprint_id, settings or {})
        
        # Models that support json_object response format
        json_supported_models = [
            "gpt-4-turbo-preview",
            "gpt-4-1106-preview",
            "gpt-4-0125-preview",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-3.5-turbo-1106",
            "gpt-4",
            "gpt-4-turbo"
        ]
        
        # Check if model supports json_object format
        # Even if not explicitly supported, we'll try to use it (some models accept it silently)
        supports_json = any(model in self.model.lower() for model in json_supported_models)
        
        try:
            # Build request parameters
            request_params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
            }
            
            # Only add response_format if model supports it
            if supports_json:
                request_params["response_format"] = {"type": "json_object"}
            
            response = self.client.chat.completions.create(**request_params)
            
            content = response.choices[0].message.content
            
            def fix_control_characters_in_json(text: str) -> str:
                """Fix unescaped control characters (newlines, tabs) in JSON string values."""
                # This function finds JSON string values and escapes control characters inside them
                result = []
                i = 0
                in_string = False
                escape_next = False
                
                while i < len(text):
                    char = text[i]
                    
                    if escape_next:
                        # Skip escaped character (including \" which means we're still in string)
                        result.append(char)
                        escape_next = False
                        i += 1
                        continue
                    
                    if char == '\\':
                        # Next character is escaped
                        result.append(char)
                        escape_next = True
                        i += 1
                        continue
                    
                    if char == '"':
                        # Toggle string state
                        in_string = not in_string
                        result.append(char)
                        i += 1
                        continue
                    
                    if in_string:
                        # Inside a string - escape control characters
                        if char == '\n':
                            result.append('\\n')
                        elif char == '\r':
                            result.append('\\r')
                        elif char == '\t':
                            result.append('\\t')
                        elif ord(char) < 32:  # Other control characters
                            result.append(f'\\u{ord(char):04x}')
                        else:
                            result.append(char)
                    else:
                        # Outside string - pass through
                        result.append(char)
                    
                    i += 1
                
                return ''.join(result)
            
            def clean_json_content(text: str) -> str:
                """Clean and sanitize JSON content before parsing."""
                # Remove markdown code blocks if present
                text = text.strip()
                
                # Check for markdown code blocks with json
                if "```json" in text:
                    # Extract content between ```json and ```
                    start = text.find("```json") + 7
                    end = text.find("```", start)
                    if end != -1:
                        text = text[start:end].strip()
                elif "```" in text:
                    # Extract content between ``` and ```
                    start = text.find("```") + 3
                    end = text.find("```", start)
                    if end != -1:
                        text = text[start:end].strip()
                
                # Remove any leading/trailing backticks
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                
                return text.strip()
            
            # Parse JSON from response
            # If response_format was used, content is already JSON
            # Otherwise, try to extract JSON from markdown code blocks or plain text
            result = None
            parse_error = None
            
            try:
                if supports_json:
                    # Even with json_object format, OpenAI sometimes includes control characters
                    try:
                        result = json.loads(content)
                    except json.JSONDecodeError as e:
                        parse_error = e
                        # Try fixing control characters
                        try:
                            fixed_content = fix_control_characters_in_json(content)
                            result = json.loads(fixed_content)
                            parse_error = None
                        except json.JSONDecodeError as e2:
                            parse_error = e2
                            # If still failing, clean markdown and try again
                            content_clean = clean_json_content(content)
                            fixed_content = fix_control_characters_in_json(content_clean)
                            try:
                                result = json.loads(fixed_content)
                                parse_error = None
                            except json.JSONDecodeError as e3:
                                parse_error = e3
                else:
                    # Try to parse JSON from response (might be wrapped in markdown)
                    content_clean = clean_json_content(content)
                    
                    try:
                        result = json.loads(content_clean)
                    except json.JSONDecodeError as e:
                        parse_error = e
                        # Try fixing control characters
                        try:
                            fixed_content = fix_control_characters_in_json(content_clean)
                            result = json.loads(fixed_content)
                            parse_error = None
                        except json.JSONDecodeError as e2:
                            parse_error = e2
                            # If JSON parsing fails, try to extract JSON from the text
                            # Look for JSON object boundaries more intelligently
                            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content_clean, re.DOTALL)
                            if not json_match:
                                # Try simpler pattern
                                json_match = re.search(r'\{.*\}', content_clean, re.DOTALL)
                            
                            if json_match:
                                json_str = json_match.group()
                                try:
                                    result = json.loads(json_str)
                                    parse_error = None
                                except json.JSONDecodeError as e3:
                                    parse_error = e3
                                    # Last attempt: fix control characters in extracted JSON
                                    try:
                                        fixed_json = fix_control_characters_in_json(json_str)
                                        result = json.loads(fixed_json)
                                        parse_error = None
                                    except json.JSONDecodeError as e4:
                                        parse_error = e4
                            else:
                                # Try to find any JSON-like structure
                                # Look for patterns like {"title": ...}
                                if '{"title"' in content_clean or '"title"' in content_clean:
                                    # Try to extract everything from first { to last }
                                    first_brace = content_clean.find('{')
                                    last_brace = content_clean.rfind('}')
                                    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                                        json_str = content_clean[first_brace:last_brace + 1]
                                        try:
                                            result = json.loads(json_str)
                                            parse_error = None
                                        except json.JSONDecodeError:
                                            try:
                                                fixed_json = fix_control_characters_in_json(json_str)
                                                result = json.loads(fixed_json)
                                                parse_error = None
                                            except json.JSONDecodeError as e5:
                                                parse_error = Exception(f"No valid JSON found in response: {str(e5)}")
                                else:
                                    parse_error = Exception("No JSON object found in response. The model may not have returned JSON format.")
                
                # If we still don't have a result, raise the last parse error
                if result is None:
                    content_preview = content[:500] if content else "No content received"
                    error_msg = f"Could not parse JSON from AI response: {str(parse_error)}"
                    error_msg += f"\n\nResponse preview: {content_preview}"
                    error_msg += f"\n\nTip: Try using a model that supports json_object format (gpt-4o, gpt-4-turbo-preview) or check if the model returned valid JSON."
                    raise Exception(error_msg)
                
                # Validate and structure the response
                return self._structure_response(result, prompt)
                
            except Exception as parse_err:
                # If it's already our custom error, re-raise it
                if "Could not parse JSON" in str(parse_err):
                    raise
                # Otherwise wrap it
                content_preview = content[:500] if 'content' in locals() and content else "No content received"
                raise Exception(f"Failed to parse JSON response: {str(parse_err)}. Response preview: {content_preview}")
            
        except Exception as e:
            # Preserve the original error message
            error_msg = str(e)
            if "Could not parse JSON" in error_msg or "Failed to parse JSON" in error_msg:
                raise Exception(error_msg)
            else:
                raise Exception(f"OpenAI API error: {error_msg}")

    def _build_system_prompt(self, blueprint_id: str = None, settings: Dict[str, Any] = None) -> str:
        """Build the system prompt for Roblox Lua generation."""
        
        creativity = settings.get("creativity", 0.7)
        world_scale = settings.get("world_scale", "medium")
        device = settings.get("device", "desktop")
        
        blueprint_context = ""
        if blueprint_id:
            blueprint_context = f"\nBlueprint type: {blueprint_id}. Follow the patterns typical for this game type."
        
        # Natural language understanding guide
        natural_language_guide = """
NATURAL LANGUAGE PROCESSING:
- Understand user's intent from casual, everyday language
- "make a game where you jump on blocks" = Obstacle Course (Obby) with platforms
- "create a business game" or "build a tycoon" = Tycoon game with money and upgrades
- "make a racing game" = Racing game with track and checkpoints
- "shooting game with teams" or "capture the flag" = FPS/Capture the Flag with bases and flags
- "clicker game" or "idle game" = Simulator with currency and upgrades
- "interactive story" or "narrative game" = Story game with NPCs and dialogue
- Extract ALL mentioned features (weapons, flags, platforms, checkpoints, etc.)
- Create complete game based on natural description
- If user says "add X", include X in the game
- If user mentions specific mechanics, implement them fully

VISUAL DESCRIPTION MATCHING:
- If user says "red flag on a pole" → Create red Part (flag) on gray Part (pole)
- If user says "tall glowing flag" → Create tall flag (height 12+) with Neon material
- If user says "blue base platform" → Create blue Part as base (large platform)
- If user says "small weapons" → Create small Parts (size Vector3.new(2,2,4))
- If user says "floating platforms" or "floating islands" → Create SEPARATE large platforms (size Vector3.new(20,2,20) or bigger) at different Y heights (Y > 15), with LARGE GAPS between them (at least 20-30 studs apart in X/Z), each platform is its own Part, positioned at different X/Z coordinates with significant air gaps. Platforms should look like ISLANDS - large, varied shapes, not just small blocks
- If user says "moving obstacles" → Create Parts that MOVE using BodyVelocity, BodyAngularVelocity, or TweenService with RunService.Heartbeat to rotate/translate CONTINUOUSLY. Add visible movement code that runs every frame. Obstacles should rotate (BodyAngularVelocity) or move back and forth (TweenService or BodyVelocity). MUST be visibly moving, not static
- If user says "obby" or "obstacle course" → Create separate jumping platforms with gaps, NOT a connected path
- If user describes appearance → Match it EXACTLY in code
- Colors: "red" = Bright red, "blue" = Bright blue, "green" = Bright green
- Materials: "glowing" = Neon, "metallic" = Metal, "shiny" = Glass or Neon
- Sizes: Match described size (large = big, small = small, tall = high Y value)
"""
        
        return f"""You are an expert Roblox Studio developer. Generate COMPLETE, WORKING Roblox Lua scripts that create FULLY FUNCTIONAL, PLAYABLE games from natural language descriptions.

CRITICAL RULES - MUST FOLLOW EXACTLY FOR COMPLETE, PLAYABLE GAMES:

CRITICAL CODE ERRORS TO AVOID (THESE CAUSE RUNTIME ERRORS):
- CFrame vs Vector3: NEVER assign Vector3 directly to CFrame property. This causes "Unable to cast Vector3 to CoordinateFrame" error.
  * CORRECT: part.CFrame = CFrame.new(0, 5, 0) or part.CFrame = CFrame.new(positionVector3)
  * WRONG: part.CFrame = Vector3.new(0, 5, 0) - THIS WILL CRASH!
  * Use part.Position = Vector3.new(x, y, z) if you only need position (not rotation)
  * Use part.CFrame = CFrame.new(x, y, z) if you need full CFrame (position + rotation)
  * When teleporting players: humanoidRootPart.CFrame = CFrame.new(0, 24, 0) NOT Vector3.new(0, 24, 0)
- leaderstats access: leaderstats is ONLY created server-side. Client scripts MUST wait for it before accessing.
  * Server (ServerScriptService): Create leaderstats in Players.PlayerAdded event BEFORE client tries to access
    Example: local leaderstats = Instance.new("Folder"); leaderstats.Name = "leaderstats"; leaderstats.Parent = player
  * Client (StarterPlayerScripts): ALWAYS use WaitForChild before accessing leaderstats
    CORRECT: local leaderstats = player:WaitForChild("leaderstats", 10) -- wait up to 10 seconds
    CORRECT: if player:FindFirstChild("leaderstats") then local stats = player.leaderstats end
    WRONG: local stats = player.leaderstats -- THIS WILL CRASH with "leaderstats is not a valid member" error
    NEVER directly access player.leaderstats without checking/waiting - it doesn't exist yet!

1. Generate COMPLETE, FUNCTIONAL code - NO placeholders, NO "TODO", NO "implement later" - EVERYTHING must work immediately
2. ALL code in ONE script - NO modules, NO external files - paste into ServerScriptService and it works AUTOMATICALLY
3. CREATE ALL GAME ELEMENTS using Instance.new() - all visual elements, UI, mechanics must be created AUTOMATICALLY on script start
4. EVERYTHING must be VISIBLE AND FUNCTIONAL when pasted and Play is clicked - game must START AUTOMATICALLY and be immediately playable
5. GAME MUST START AUTOMATICALLY - CRITICAL: Script initialization code MUST run IMMEDIATELY when script loads (not waiting for events). Put all setup code at TOP of script: Create teams → Create spawns → Create weapons → Create map → Create UI → Then add event listeners. Use spawn() or RunService.Heartbeat to create game loop. When player clicks Play in Roblox Studio, EVERYTHING should appear immediately - teams exist, spawns exist, weapons spawn, UI loads, game starts automatically with ZERO manual setup!
6. SCRIPT EXECUTION ORDER - MUST initialize everything FIRST before adding event listeners. The first lines of script should create: teams, spawns, map, weapons, then add Players.PlayerAdded listeners. This ensures game elements exist immediately when Play is clicked.
7. MANDATORY: ALL GAMES MUST INCLUDE A SCORE SYSTEM - Create leaderstats folder with Score/Points/Kills/etc. IntValue, update it during gameplay, display in GUI. Server creates leaderstats FIRST, then client can access it with WaitForChild.
6. MANDATORY: ALL GAMES MUST INCLUDE WORKING UI - Create LocalScript in StarterPlayer/StarterPlayerScripts (NOT StarterGui) with ScreenGui showing score, timer, objectives, health (if applicable), ammo (if applicable), kill feed (if applicable). For coin collector games, MUST display score in UI: Create ScreenGui in PlayerGui with DisplayOrder = 10 (to appear above chat), add Frame with TextLabel showing "Score: value" format in one line, connect to leaderstats.Score using WaitForChild and Changed event to update display in real-time. Example: screenGui.DisplayOrder = 10; local leaderstats = player:WaitForChild("leaderstats", 10); local score = leaderstats:WaitForChild("Score"); scoreLabel.Text = "Score: " .. tostring(score.Value); score.Changed:Connect(function(newValue) scoreLabel.Text = "Score: " .. tostring(newValue) end)
7. MANDATORY: ALL GAMES MUST FEEL POLISHED - Add visual feedback, animations, effects, sound (optional), chat messages, hit indicators, damage numbers
8. Use Instance.new('Part') for all visual elements - create environment, obstacles, collectibles, weapons, pickups, etc. CRITICAL: Everything must BOTH LOOK VISUALLY APPEALING AND WORK FUNCTIONALLY. Weapons must look like real weapons (use MeshPart, SpecialMesh, or combine Parts to create shape) AND actually shoot/do damage. Health packs must glow/pulse visually AND actually heal players. NOTE: For coins/collectibles, use REAL 3D Parts (NOT BillboardGui text labels) - coins should be actual Part objects with Ball/Cylinder shapes, Neon material, and PointLight. Other items like weapons/health packs may benefit from BillboardGui labels for clarity, but coins must be real 3D objects, not text boxes.
9. Position objects in Workspace with specific Vector3 positions - make world feel alive and engaging
10. Add touch events for ALL interactive elements (Touched:Connect with working logic) - collectibles, triggers, buttons, weapons, pickups all work
11. Include chat messages to guide players (StarterGui:SetCore with ChatMakeSystemMessage) - "Welcome!", "Collect items!", "Score points!", "Game started!"
12. Create leaderboards/scoring - leaderstats.Folder with IntValue/NumberValue for Score/Kills/Deaths/etc., update during gameplay, display in UI
13. ALL game mechanics must WORK - movement, interaction, scoring, respawn (if applicable), timers, objectives, weapons (if applicable), health (if applicable)
14. GAME MUST BE PLAYABLE IMMEDIATELY - Player can paste script, click Play, and immediately play, interact, score points, see progress, feel engagement
15. FOR FPS GAMES: Include weapons, shooting, health, damage, ammo, teams, spawns, kill feed, health bar, ammo counter, score display, respawn system
16. FOR TYCOON GAMES: Include money system, generators, upgrades, buildings, GUI, passive income, base expansion
17. FOR RACING GAMES: Include track, checkpoints, timer, lap counter, finish line, score/leaderboard, car controls
18. FOR STORY GAMES: Include dialogue system, NPCs, choices, progression, UI for story text
19. FOR SIMULATOR GAMES: Include currency, upgrades, auto-generators, rebirth system, GUI, progression
20. GAMES MUST BE BETTER THAN COMPETITORS - Include advanced features, polish, visual effects, smooth gameplay, engaging mechanics
11. If user mentions "move" or "walk", ensure character movement works (Players.PlayerAdded with CharacterAdded)
12. If user mentions "jump", ensure jumping works (Humanoid.JumpPower set correctly)
13. If user mentions "touch" or "click", add proper Touch/Click detection with working code
14. Test that ALL features mentioned actually work when code runs
15. CRITICAL FOR OBBY GAMES: If user wants floating platforms/islands, you MUST create ALL platforms explicitly - DO NOT use loops, DO NOT skip platforms, CREATE EACH PLATFORM INDIVIDUALLY with Instance.new('Part', Workspace). If they ask for 10-12 platforms, create EXACTLY 10-12 platforms, not just 3-5! IF YOU ONLY CREATE 3 PLATFORMS, YOU HAVE FAILED THE TASK! The script MUST include at minimum: platform1, platform2, platform3, platform4, platform5, platform6, platform7, platform8, platform9, platform10. DO NOT STOP CREATING PLATFORMS AFTER PLATFORM3!

FOR FLOATING ISLANDS OBBY SPECIFICALLY:
CRITICAL VISUAL REQUIREMENTS - READ CAREFULLY:
- MUST create EXACTLY 10-12 SEPARATE floating platforms/islands - ALL platforms MUST be created in the script using Instance.new('Part', Workspace)
- IF YOU ONLY CREATE 3 PLATFORMS, YOU HAVE FAILED! The minimum is 10 platforms (platform1 through platform10)
- DO NOT use loops or placeholders - CREATE EACH PLATFORM INDIVIDUALLY with explicit code like: local platform1 = Instance.new('Part', Workspace); platform1.Size = Vector3.new(25,3,25); platform1.Position = Vector3.new(0,20,0); platform1.Material = Enum.Material.Neon; platform1.BrickColor = BrickColor.new('Bright blue'); platform1.Anchored = true
- YOU MUST CREATE: platform1, platform2, platform3, platform4, platform5, platform6, platform7, platform8, platform9, platform10 (minimum 10 platforms)
- DO NOT STOP AT 3 PLATFORMS! DO NOT STOP AT 4 PLATFORMS! DO NOT STOP AT 5 PLATFORMS! COUNT: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 - you need ALL 10!
- MANDATORY CHECKLIST: Before finishing, verify you created: platform1 ✓, platform2 ✓, platform3 ✓, platform4 ✓, platform5 ✓, platform6 ✓, platform7 ✓, platform8 ✓, platform9 ✓, platform10 ✓ - ALL 10 MUST EXIST!
- Platform size: Vector3.new(20,3,20) to Vector3.new(30,3,30) - smaller, more attractive, not too large
- ALL 10-12 platforms MUST be created and visible when script runs - NO MISSING platforms
- If you only create 3-4 platforms, the game will NOT feel like a real floating game - it needs 10-12 platforms!
- CRITICAL: Write the code for ALL platforms in sequence: platform1 code, then platform2 code, then platform3 code, then platform4 code, then platform5 code, then platform6 code, then platform7 code, then platform8 code, then platform9 code, then platform10 code - DO NOT SKIP ANY!
- WRONG: Creating only platform1, platform2, platform3 and stopping - THIS IS INCORRECT!
- CORRECT: Creating platform1, platform2, platform3, platform4, platform5, platform6, platform7, platform8, platform9, platform10 (and optionally 11-12)
- ALL platforms MUST float at Y > 18 (floating HIGH in air, NOT on ground/baseplate, vary Y between 18-28 for visual depth)
- CRITICAL: Platforms MUST be floating ABOVE any baseplate - even if baseplate exists at Y=0, platforms must be at Y > 18
- The script MUST work with OR without a baseplate - platforms are ALWAYS floating high in air
- NO platforms should be at Y < 5 (ground level) - ALL platforms must float high, completely independent of baseplate
- Starting platform MUST be floating at Y > 18 (position Vector3.new(0,20,0) or higher), NOT on the baseplate/ground
- If a baseplate exists, platforms must be clearly visible FLOATING ABOVE IT - not hidden or touching it
- CRITICAL SPAWN FIX: Create SpawnLocation ON TOP of starting platform - Position MUST be at (platform Y + 4) so player spawns ON TOP, NOT UNDERGROUND!
- Example: If starting platform is at (0,20,0), SpawnLocation MUST be at (0,24,0) - NOT at (0,20,0) or Y=0!
- SpawnLocation.Position.Y MUST be = platform.Position.Y + 4 (if platform Y=20, SpawnLocation Y=24)
- WRONG: SpawnLocation at Y=20 (same as platform) = player spawns INSIDE platform
- WRONG: SpawnLocation at Y=0 or Y=1 = player spawns UNDERGROUND
- CORRECT: SpawnLocation at Y=24 (platform Y + 4) = player spawns ON TOP of platform
- If SpawnLocation is at same Y as platform or lower, player will spawn UNDERGROUND - THIS IS BROKEN!
- NEVER place SpawnLocation at Y=0, Y=1, or same Y as platform - player MUST spawn on the floating platform!
- Code: local spawnLoc = Instance.new('SpawnLocation', Workspace); spawnLoc.Position = Vector3.new(0,24,0); spawnLoc.Enabled = true; spawnLoc.Neutral = true -- Y=24 for platform at Y=20, NOT Y=20 or Y=0!
- SpawnLocation properties: Anchored = true, Size = Vector3.new(4,4,4), Transparency = 1, CanCollide = false, Enabled = true, Neutral = true
- CRITICAL: Also add Players.PlayerAdded event to explicitly teleport player to spawn position: game.Players.PlayerAdded:Connect(function(player) player.CharacterAdded:Connect(function(character) wait(0.1); local humanoidRootPart = character:WaitForChild('HumanoidRootPart', 5); if humanoidRootPart then humanoidRootPart.CFrame = CFrame.new(0, 24, 0) end end) end)
- TEST: If player spawns underground, SpawnLocation Y is wrong OR Enabled/Neutral not set OR PlayerAdded event missing - fix all three!
- CRITICAL: Script MUST work with OR without baseplate - platforms are created at Y > 18 regardless of baseplate
- If baseplate exists, platforms float ABOVE it - they are completely independent
- All platforms MUST have Anchored = true to keep them floating in position (not affected by baseplate)
- CRITICAL: Create START sign/indicator ON TOP of starting platform - Create Part (size Vector3.new(8,3,12), position on starting platform top, BrickColor = Bright green, Anchored = true) with SurfaceGui (Face = Enum.NormalId.Top) + TextLabel (Text = "START", TextSize = 24, Font = Enum.Font.ArialBold, TextColor3 = Color3.new(1,1,1), TextScaled = true, BackgroundTransparency = 1) so players can SEE START text clearly ON TOP of platform (white text on green background)
- Platforms MUST have EXTREMELY LARGE GAPS (40-60 studs minimum between platforms - players must make HUGE JUMPS)
- Platform positions MUST vary significantly in BOTH X AND Z (NOT in a straight line - create irregular scattered placement)
- CORRECT positions: (0,18,0), (60,22,40), (115,20,-45), (175,25,55), (-45,19,70), (240,23,-30)
- WRONG positions: (0,18,0), (50,18,0), (100,18,0), (150,18,0) - this is a straight line, DON'T DO THIS
- Each platform is SEPARATE Part, NOT connected - MUST have large air gaps between ALL platforms
- Platform material MUST be Neon or GlowMaterial for glowing effect
- Platform color: Use Bright blue, Bright green, Bright yellow, Bright red for variety
- Platform MUST have Anchored = true

MOVING OBSTACLES REQUIREMENTS (CRITICAL):
- If user mentions "moving obstacles", MUST create Parts that move WITH PROPER CODE:
  * Spinning obstacles ON platforms: Create Part (size Vector3.new(4-6,4-6,4-6)), add BodyAngularVelocity with MaxTorque = Vector3.new(math.huge, math.huge, math.huge) and AngularVelocity = Vector3.new(0, 10, 0) for fast visible rotation
  * Code for spinning: local obstacle = Instance.new('Part', Workspace); obstacle.Size = Vector3.new(5,5,5); obstacle.Position = platformPosition + Vector3.new(0,3,0); local bav = Instance.new('BodyAngularVelocity', obstacle); bav.MaxTorque = Vector3.new(math.huge, math.huge, math.huge); bav.AngularVelocity = Vector3.new(0, 10, 0); obstacle.Anchored = false
  * Moving obstacles BETWEEN platforms: Create Part, use TweenService with continuous back-and-forth movement
  * Code for moving: local ts = game:GetService('TweenService'); local moveObstacle = Instance.new('Part', Workspace); moveObstacle.Size = Vector3.new(8,2,8); moveObstacle.Position = startPos; local moveTween = ts:Create(moveObstacle, TweenInfo.new(3, Enum.EasingStyle.Linear, Enum.EasingDirection.InOut, math.huge, true), {{Position = endPos}}); moveTween:Play()
  * Place 3-5 moving obstacles: 2-3 ON platforms (spinning cubes), 1-2 BETWEEN platforms (moving barriers)
  * Obstacles MUST be visibly moving when game runs - NOT static - movement code MUST be in script
- Create checkpoints with touch detection (glowing parts on platforms)
- Create finish line (large platform at end position, Bright green color to distinguish)
- CRITICAL: Create FINISH/STOP sign on finish platform - Create Part (BrickColor = Bright green, size Vector3.new(8,3,12), position on finish platform top) with SurfaceGui + TextLabel (Text = "FINISH" or "STOP", TextSize = 24, Font = ArialBold, TextColor3 = Black, TextScaled = true) so players know where the game ends - text MUST be visible and readable
- Character movement and jumping must work (JumpPower = 50)

FOR CAPTURE THE FLAG SPECIFICALLY:
- MUST create BOTH Red base AND Blue base (not just one!)
- Red base at position Vector3.new(-80, 0.5, 0)
- Blue base at position Vector3.new(80, 0.5, 0)
- Red flag on Red base with pole and glowing flag part
- Blue flag on Blue base with pole and glowing flag part
- Both flags must be touchable and capturable
- Both bases must accept flag returns
- Create weapons and health packs scattered around
- Teams must be created (Red and Blue)
- Scoring system must work
- Chat messages must guide players

EXAMPLE STRUCTURE FOR FLOATING ISLANDS OBBY (EXACT FORMAT - MUST CREATE ALL 10-12 PLATFORMS):
CRITICAL: You MUST write code that creates ALL 10-12 platforms. DO NOT skip any platforms. DO NOT STOP AFTER CREATING 3 PLATFORMS! You MUST create at minimum 10 platforms (platform1 through platform10). 
CRITICAL: Platforms MUST float HIGH above any baseplate (Y > 18). The script works with OR without baseplate.
Use this EXACT code structure:
local Workspace = game:GetService('Workspace')

-- CRITICAL: All platforms float HIGH above ground/baseplate (Y > 18)
-- Platforms are completely independent - they work with or without baseplate

-- Create starting platform (Platform 1) - FLOATING HIGH at Y=20
local platform1 = Instance.new('Part', Workspace)
platform1.Name = 'StartingPlatform'
platform1.Size = Vector3.new(25,3,25)
platform1.Position = Vector3.new(0,20,0)  -- Y=20 means FLOATING HIGH above ground
platform1.Material = Enum.Material.Neon
platform1.BrickColor = BrickColor.new('Bright blue')
platform1.Anchored = true  -- CRITICAL: Anchored = true so it stays floating
-- CRITICAL SPAWN FIX: Create SpawnLocation ON TOP of starting platform (Y = platform Y + 4)
-- Platform is at Y=20, so SpawnLocation MUST be at Y=24 so player spawns ON TOP, NOT UNDERGROUND!
-- WRONG: SpawnLocation at Y=20 (same as platform) = player spawns INSIDE platform
-- WRONG: SpawnLocation at Y=0 = player spawns UNDERGROUND
-- CORRECT: SpawnLocation at Y=24 (platform Y + 4) = player spawns ON TOP of platform
local spawnLoc = Instance.new('SpawnLocation', Workspace)
spawnLoc.Name = 'StartSpawn'
spawnLoc.Position = Vector3.new(0,24,0)  -- Y=24 (platform Y=20 + 4) - player spawns ON TOP, NOT UNDERGROUND!
spawnLoc.Anchored = true
spawnLoc.Size = Vector3.new(4,4,4)
spawnLoc.Transparency = 1
spawnLoc.CanCollide = false
spawnLoc.Enabled = true  -- CRITICAL: Must be enabled for players to spawn here!
spawnLoc.Neutral = true  -- Allow all players to spawn here
spawnLoc.BrickColor = BrickColor.new('Bright green')  -- Make it slightly visible for debugging

-- CRITICAL: Also set player spawn position explicitly when they join
game.Players.PlayerAdded:Connect(function(player)
    player.CharacterAdded:Connect(function(character)
        wait(0.1)  -- Wait for character to fully load
        local humanoidRootPart = character:WaitForChild('HumanoidRootPart', 5)
        if humanoidRootPart then
            humanoidRootPart.CFrame = CFrame.new(0, 24, 0)  -- Spawn ON TOP of platform, NOT UNDERGROUND!
        end
    end)
end)

-- Create START sign on starting platform
local startSign = Instance.new('Part', Workspace)
startSign.Size = Vector3.new(8,3,12)
startSign.Position = Vector3.new(0,22,0)
startSign.BrickColor = BrickColor.new('Bright green')
startSign.Anchored = true
local startGui = Instance.new('SurfaceGui', startSign)
startGui.Face = Enum.NormalId.Top
local startLabel = Instance.new('TextLabel', startGui)
startLabel.Size = UDim2.new(1,0,1,0)
startLabel.Text = 'START'
startLabel.TextSize = 24
startLabel.Font = Enum.Font.ArialBold
startLabel.TextColor3 = Color3.new(1,1,1)
startLabel.TextScaled = true
startLabel.BackgroundTransparency = 1

-- Create platform 2
local platform2 = Instance.new('Part', Workspace)
platform2.Size = Vector3.new(22,3,22)
platform2.Position = Vector3.new(50,22,0)
platform2.Material = Enum.Material.Neon
platform2.BrickColor = BrickColor.new('Bright green')
platform2.Anchored = true

-- Create platform 3
local platform3 = Instance.new('Part', Workspace)
platform3.Size = Vector3.new(24,3,24)
platform3.Position = Vector3.new(100,24,30)
platform3.Material = Enum.Material.Neon
platform3.BrickColor = BrickColor.new('Bright yellow')
platform3.Anchored = true

-- Create platform 4 - FLOATING HIGH
local platform4 = Instance.new('Part', Workspace)
platform4.Size = Vector3.new(20,3,20)
platform4.Position = Vector3.new(150,20,-20)
platform4.Material = Enum.Material.Neon
platform4.BrickColor = BrickColor.new('Bright blue')
platform4.Anchored = true

-- Create platform 5 - FLOATING HIGH
local platform5 = Instance.new('Part', Workspace)
platform5.Size = Vector3.new(23,3,23)
platform5.Position = Vector3.new(220,25,40)
platform5.Material = Enum.Material.Neon
platform5.BrickColor = BrickColor.new('Bright yellow')
platform5.Anchored = true

-- Create platform 6 - FLOATING HIGH
local platform6 = Instance.new('Part', Workspace)
platform6.Size = Vector3.new(21,3,21)
platform6.Position = Vector3.new(280,22,-30)
platform6.Material = Enum.Material.Neon
platform6.BrickColor = BrickColor.new('Bright blue')
platform6.Anchored = true

-- Create platform 7 (RED PLATFORM - FAR AWAY) - FLOATING HIGH
local platform7 = Instance.new('Part', Workspace)
platform7.Size = Vector3.new(26,3,26)
platform7.Position = Vector3.new(350,27,50)  -- FAR AWAY - 350+ studs from start
platform7.Material = Enum.Material.Neon
platform7.BrickColor = BrickColor.new('Bright red')
platform7.Anchored = true

-- Create platform 8 - FLOATING HIGH
local platform8 = Instance.new('Part', Workspace)
platform8.Size = Vector3.new(24,3,24)
platform8.Position = Vector3.new(410,24,-40)
platform8.Material = Enum.Material.Neon
platform8.BrickColor = BrickColor.new('Bright yellow')
platform8.Anchored = true

-- Create platform 9 - FLOATING HIGH
local platform9 = Instance.new('Part', Workspace)
platform9.Size = Vector3.new(25,3,25)
platform9.Position = Vector3.new(460,22,50)
platform9.Material = Enum.Material.Neon
platform9.BrickColor = BrickColor.new('Bright blue')
platform9.Anchored = true

-- Create platform 10 - FLOATING HIGH (YOU MUST CREATE THIS - DO NOT STOP AT PLATFORM 9!)
local platform10 = Instance.new('Part', Workspace)
platform10.Size = Vector3.new(23,3,23)
platform10.Position = Vector3.new(530,22,-30)
platform10.Material = Enum.Material.Neon
platform10.BrickColor = BrickColor.new('Bright yellow')
platform10.Anchored = true

-- Create platform 11 - FLOATING HIGH (YOU MUST CREATE THIS TOO - DO NOT STOP AT PLATFORM 10!)
local platform11 = Instance.new('Part', Workspace)
platform11.Size = Vector3.new(26,3,26)
platform11.Position = Vector3.new(600,26,50)
platform11.Material = Enum.Material.Neon
platform11.BrickColor = BrickColor.new('Bright green')
platform11.Anchored = true

-- MUST CREATE ALL 10-12 PLATFORMS - Create finish platform as the last platform (platform 12)
-- REMEMBER: You have created platform1, platform2, platform3, platform4, platform5, platform6, platform7, platform8, platform9, platform10, platform11
-- NOW YOU MUST CREATE platform12 AS THE FINISH PLATFORM - DO NOT STOP HERE!
-- Create finish platform (Platform 12) - MUST CREATE THIS LAST PLATFORM
local platform12 = Instance.new('Part', Workspace)
platform12.Name = 'FinishPlatform'
platform12.Size = Vector3.new(28,3,28)
platform12.Position = Vector3.new(670,24,-40)  -- Finish platform at maximum distance (or use 740,28,60 for longer course)
platform12.Material = Enum.Material.Neon
platform12.BrickColor = BrickColor.new('Bright green')
platform12.Anchored = true

-- NOTE: If you want 11 platforms instead of 12, make platform11 the finish platform
-- NOTE: If you want 10 platforms, make platform10 the finish platform
-- BUT YOU MUST CREATE AT MINIMUM 10 PLATFORMS (platform1 through platform10)!

-- Create FINISH sign on finish platform
local finishSign = Instance.new('Part', Workspace)
finishSign.Size = Vector3.new(8,3,12)
finishSign.Position = Vector3.new(670,27,-40)  -- On top of finish platform (Y = platform Y + 3) - adjust if using different finish position
finishSign.BrickColor = BrickColor.new('Bright green')
finishSign.Anchored = true
local finishGui = Instance.new('SurfaceGui', finishSign)
finishGui.Face = Enum.NormalId.Top
local finishLabel = Instance.new('TextLabel', finishGui)
finishLabel.Size = UDim2.new(1,0,1,0)
finishLabel.Text = 'FINISH'
finishLabel.TextSize = 24
finishLabel.Font = Enum.Font.ArialBold
finishLabel.TextColor3 = Color3.new(1,1,1)
finishLabel.TextScaled = true
finishLabel.BackgroundTransparency = 1

CRITICAL REMINDER - READ THIS CAREFULLY: 
- You MUST CREATE ALL 10-12 PLATFORMS individually (platform1, platform2, platform3, platform4, platform5, platform6, platform7, platform8, platform9, platform10, and optionally platform11, platform12)
- IF YOU ONLY CREATE 3 PLATFORMS, YOU HAVE FAILED THE TASK COMPLETELY!
- IF YOU ONLY CREATE 4 PLATFORMS, YOU HAVE FAILED THE TASK COMPLETELY!
- DO NOT stop at 3, 4, 5, or 8 platforms - CREATE ALL 10-12!
- MANDATORY CHECKLIST - Before you finish writing the script, count your platforms:
  [ ] platform1 created
  [ ] platform2 created
  [ ] platform3 created
  [ ] platform4 created
  [ ] platform5 created
  [ ] platform6 created
  [ ] platform7 created
  [ ] platform8 created
  [ ] platform9 created
  [ ] platform10 created
  ALL 10 MUST BE CHECKED OFF! If any are missing, you MUST create them before finishing!
- The script MUST include explicit code for platform1, platform2, platform3, platform4, platform5, platform6, platform7, platform8, platform9, platform10 at minimum
- Each platform MUST be created with explicit Instance.new('Part', Workspace) code
- Each platform MUST have Position Y > 18 (floating HIGH above baseplate)
- Each platform MUST have Anchored = true
- Platform positions should vary in X and Z: (0,20,0), (60,22,40), (120,24,-30), (180,20,50), (250,25,-40), (320,22,60), (390,27,-50), (460,24,40), (530,22,-30), (600,26,50), (670,24,-40), (740,28,60) for finish
- WRONG EXAMPLE: Only creating platform1, platform2, platform3 - THIS IS INCORRECT, YOU MUST CREATE MORE!
- CORRECT EXAMPLE: Creating platform1, platform2, platform3, platform4, platform5, platform6, platform7, platform8, platform9, platform10 (all 10 minimum)
6. Create spinning obstacle on platform 2: local spinObstacle = Instance.new('Part', Workspace); spinObstacle.Size = Vector3.new(5,5,5); spinObstacle.Position = Vector3.new(60,28,40); spinObstacle.BrickColor = Bright red; spinObstacle.Anchored = false; local bav = Instance.new('BodyAngularVelocity', spinObstacle); bav.MaxTorque = Vector3.new(math.huge, math.huge, math.huge); bav.AngularVelocity = Vector3.new(0, 10, 0)
7. Create moving obstacle between platforms: local moveObstacle = Instance.new('Part', Workspace); moveObstacle.Size = Vector3.new(8,2,8); moveObstacle.Position = Vector3.new(87,23,-5); local ts = game:GetService('TweenService'); local moveTween = ts:Create(moveObstacle, TweenInfo.new(3, Enum.EasingStyle.Linear, Enum.EasingDirection.InOut, math.huge, true), {{Position = Vector3.new(127,25,-5)}}); moveTween:Play()
8. Create checkpoints (glowing parts on platforms, touch detection, save spawn)
9. Create respawn system (teleport to last checkpoint on death)
10. Add chat messages guiding players

EXAMPLE STRUCTURE FOR CAPTURE THE FLAG:
1. Create Teams (Red and Blue)
2. Create Red Base (Part, size Vector3.new(40,1,40), position Vector3.new(-80,0.5,0), red color)
3. Create Red Flag Pole (Part, tall, gray, on Red base)
4. Create Red Flag (Part, glowing neon red, attached to pole)
5. Create Blue Base (Part, size Vector3.new(40,1,40), position Vector3.new(80,0.5,0), blue color)
6. Create Blue Flag Pole (Part, tall, gray, on Blue base)
7. Create Blue Flag (Part, glowing neon blue, attached to pole)
8. Create weapons (Parts, scattered around map)
9. Create health packs (Parts, scattered around map)
10. Add touch events for flags (capture logic)
11. Add touch events for bases (scoring logic)
12. Add team assignment
13. Add leaderboard/scoring
14. Add chat messages

OUTPUT FORMAT (JSON):
{{
    "title": "Game title",
    "narrative": "Brief game description",
    "lua_script": "COMPLETE Lua code - creates ALL game elements, NO placeholders, works immediately",
    "modules": [],
    "testing_steps": ["Paste into ServerScriptService", "Click Play"],
    "assets_needed": [],
    "optimization_tips": []
}}

SETTINGS:
- Creativity: {creativity}
- World scale: {world_scale}
- Device: {device}
{blueprint_context}
{natural_language_guide}

USER PROMPT ANALYSIS:
Analyze the user's natural language request and understand:
1. What type of game they want (obby, tycoon, racing, fps, simulator, story, or custom)
2. What specific features they mention (flags, weapons, platforms, checkpoints, etc.)
3. What game mechanics they want (scoring, teams, upgrades, etc.)
4. What VISUAL APPEARANCE they describe (colors, sizes, positions, materials)
5. What ENVIRONMENT CHANGES they want (day to night, lighting changes, time progression)
6. Create EVERYTHING they ask for, plus standard game elements
7. Match VISUAL DESCRIPTION EXACTLY - what they describe must appear in Roblox Studio
8. If user says "tall red flag" → Create tall (12+ studs) red (Bright red) flag (Neon material)
9. If user says "large blue base" → Create large (40x40) blue (Bright blue) base platform
10. If user mentions "day to night" or "time change" or "environment changes" → Use Lighting service (game:GetService("Lighting")) to change TimeOfDay or ClockTime based on score/progress
    * Example: local Lighting = game:GetService("Lighting"); Lighting.TimeOfDay = (score / maxScore) * 24 (gradual transition from 6 AM to 6 PM)
    * Or: Lighting.ClockTime = math.min(18 + (score * 0.1), 24) for gradual progression
    * Connect this to score changes so environment updates as player progresses
11. Visual appearance MUST match the prompt description exactly

GENERATE COMPLETE, FUNCTIONAL CODE based on user's natural language description. 

CRITICAL: Code must WORK when pasted and Play is clicked:
- Services: ALWAYS get services using game:GetService() before using them. NEVER use service names directly without getting them first.
  * CORRECT: local Lighting = game:GetService("Lighting"); Lighting.TimeOfDay = 6
  * WRONG: Lighting.TimeOfDay = 6 - this causes "attempt to index nil with 'TimeOfDay'" error because Lighting is nil
  * Required services must be retrieved: local Lighting = game:GetService("Lighting"), local Players = game:GetService("Players"), local Workspace = game:GetService("Workspace"), etc.
- Movement: Players.PlayerAdded → CharacterAdded → ensure Humanoid exists (movement works by default in Roblox)
- Jumping: Set Humanoid.JumpPower = 50 if needed
- Touch/Click: Use Touched:Connect with COMPLETE logic (not just empty functions). For collectible coins/items, ensure coin.CanTouch = true and coin.CanCollide = false. Use debounce pattern to prevent multiple rapid collections: local collectingCoins = {}; if collectingCoins[coin] then return end; collectingCoins[coin] = true; onCoinTouched(coin, player); wait(0.5); collectingCoins[coin] = nil
- Scoring: Create leaderstats, update values, display in GUI. If user wants day/night changes based on score, use Lighting service to change TimeOfDay or ClockTime progressively.
- Day/Night Transitions: When user mentions "day to night" or "when coins touched night comes" or "collect coin switch day to night then after 1 sec switch to day", automatically switch to night when coin is collected, then after 1 second switch back to day.
  * Start with DAY theme: local Lighting = game:GetService("Lighting"); Lighting.TimeOfDay = 6 (6 AM = day) or Lighting.ClockTime = 12 (noon = day)
  * When coin is collected: Immediately switch to NIGHT (Lighting.TimeOfDay = 0), then after 1 second automatically switch back to DAY (Lighting.TimeOfDay = 6)
  * Connect this to coin collection event: In coin collection handler, switch to night immediately, then use spawn(function() wait(1) Lighting.TimeOfDay = 6 end) to switch back to day after 1 second
  * Example for coin touch with 1 second delay: local Lighting = game:GetService("Lighting"); function onCoinTouched(...) Lighting.TimeOfDay = 0; spawn(function() wait(1) Lighting.TimeOfDay = 6 end) end
  * CRITICAL: Always get Lighting service first before using Lighting.TimeOfDay - NEVER write just "Lighting.TimeOfDay = 6" without "local Lighting = game:GetService('Lighting')" first! This causes "attempt to index nil with 'TimeOfDay'" error.
  * This creates a cycle: collect coin → night → wait 1 sec → day → collect coin → night → wait 1 sec → day (continuous flow)
- Teams: Create Team objects, assign players, set spawn points
- Folders/Containers: ALWAYS create folders before using them. NEVER assume folders exist in Workspace.
  * WRONG: coin.Parent = Workspace.Coins (will crash if Coins folder doesn't exist)
  * CORRECT: local coinsFolder = Workspace:FindFirstChild("Coins") or Instance.new("Folder", Workspace); coinsFolder.Name = "Coins"; coin.Parent = coinsFolder
  * CORRECT: local coinsFolder = Instance.new("Folder"); coinsFolder.Name = "Coins"; coinsFolder.Parent = Workspace; coin.Parent = coinsFolder
  * Always create containers (Folders, Models) programmatically if scripts need to reference them - don't assume they exist!
- COINS/COLLECTIBLES CREATION (CRITICAL - READ CAREFULLY):
  * Coins MUST be REAL 3D Part objects (NOT BillboardGui text labels). Users want actual collectible objects they can see and touch, NOT text boxes floating in air.
  * CORRECT: Create Part with Shape = Enum.PartType.Ball (round sphere), Size = Vector3.new(2, 2, 2) or larger (at least 2 studs), Material = Enum.Material.Neon (glowing effect), BrickColor = BrickColor.new("Bright yellow") (gold/coin color), Transparency = 0 (fully visible), add PointLight for extra visibility
    Example code: local coin = Instance.new("Part"); coin.Name = "Coin"; coin.Shape = Enum.PartType.Ball; coin.Size = Vector3.new(4, 4, 4); coin.Material = Enum.Material.Neon; coin.BrickColor = BrickColor.new("Bright yellow"); coin.Transparency = 0; coin.Anchored = true; coin.CanCollide = false; coin.CanTouch = true (CRITICAL for collection to work!); local light = Instance.new("PointLight", coin); light.Color = Color3.new(1, 1, 0); light.Brightness = 2; light.Range = 12; coin.Parent = coinsFolder
    CRITICAL LIGHTING: PointLight Brightness should be 2-3 (NOT 10 - too bright creates overwhelming glow), Range should be 10-15 (NOT 30 - too large causes light bleed). Subtle glow makes coins visible without obscuring their shape.
  * WRONG: Creating BillboardGui with TextLabel showing "COIN" text - this creates TEXT BOXES floating in air, NOT actual 3D collectible objects. Users will see black rectangles with yellow text, which looks terrible and is NOT what they want.
  * NEVER use BillboardGui for coins/collectibles - ONLY use REAL 3D Parts with proper shapes (Ball for round coins, Cylinder for cylindrical items, Block for rectangular items)
  * Coins MUST be RANDOMLY SPREAD THROUGHOUT THE ENTIRE TEMPLATE/MAP (not just around spawn point, but across the WHOLE map including water areas, rooms, different regions, far areas).
    - CRITICAL: Create MANY coins (minimum 80-100 coins, ideally 100+ coins) to ensure coins are visible everywhere - in grass, near houses, in open fields, throughout the entire template
    - Spread coins ACROSS THE ENTIRE TEMPLATE with VERY large radius (400-500 studs from center) to cover the whole map including far areas, water ponds, everywhere
    - Place coins in DIFFERENT AREAS: water/swimming areas (Y: 0-3 for underwater/at water level), near water/shallow areas (Y: 4-8), ground level (Y: 9-15), elevated areas (Y: 16-20), inside rooms/buildings (scan for rooms and place coins inside), open areas, grass areas, near houses, various regions of the map
    - MUST include coins in water/swimming areas - after swimming through ponds, coins should be there too!
    - Use random angles and distances for true random scattering: local angle = math.random() * math.pi * 2 (random angle 0-360 degrees); local distance = math.random() * mapRadius (LARGE radius like 400-500 studs to cover entire template); local x = math.cos(angle) * distance; local z = math.sin(angle) * distance; local y = math.random(minY, maxY) (random height, adjusted for water/rooms)
    - WRONG: Only placing coins around spawn (small radius like 50 studs) - coins should be spread across ENTIRE map
    - WRONG: Too few coins (only 10-20 coins) - this leaves large areas empty. Users want coins EVERYWHERE!
    - WRONG: Grid pattern like for i=1,10 do for j=1,10 do coin.Position = Vector3.new(i*5, 5, j*5) end end - this creates a boring grid, not random scatter
    - WRONG: Straight line like for i=1,10 do coin.Position = Vector3.new(i*5, 5, 0) end - this creates coins in a line, not scattered
    - CORRECT: Random scatter across ENTIRE template with MANY coins - for i=1,100 do (use 80-100+ coins!) local angle = math.random() * math.pi * 2; local distance = math.random() * 500 (LARGE radius for entire map); local x = math.cos(angle) * distance; local z = math.sin(angle) * distance; coin.Position = Vector3.new(x, math.random(0, 20), z) end - this creates truly random scattered coins everywhere across the whole map
    - For water areas: Place coins at appropriate Y level for water/swimming areas (e.g., Y = 0 to 5 for underwater coins)
    - For rooms: Scan Workspace for Model/Part structures that look like rooms/buildings, place coins inside them at appropriate heights
  * Coins MUST be VISIBLE: Size at least Vector3.new(4, 4, 4) (4 studs diameter minimum - 2 studs is too small and hard to see in-game), Material = Neon (glows and stands out), PointLight with Brightness = 2-3 and Range = 10-15 (creates SUBTLE visible glow - NOT Brightness=10/Range=30 which creates overwhelming light that obscures coin shapes), Transparency = 0 (fully opaque, not transparent)
  * CRITICAL POSITIONING - REACHABLE HEIGHTS: Position coins at REACHABLE heights so players can collect them. Use Y = 5 to 15 studs above ground/terrain (NOT 20-50 studs which is too high for players to reach). Coins should be within player's jump reach - if terrain is at Y=0, use Y=5-15. If terrain exists, position coins ABOVE terrain level but REACHABLE (terrain height + 5 to 15 studs). NEVER place coins at Y=20+ unless they're on platforms players can access - players cannot reach coins floating too high in air!
  * CRITICAL SIZE: Use Size = Vector3.new(4, 4, 4) or larger (6 studs is even better for visibility). Size = Vector3.new(2, 2, 2) is too small and may not be visible from a distance.
- All mechanics: Implement FULLY, test that they work

CRITICAL FOR COMPLETE OBBY GAMES - Script MUST include ALL of these:
1. Starting platform (platform1) at Vector3.new(0,20,0) or similar (Y > 18) - FLOATING HIGH, NOT ON GROUND
2. SpawnLocation ON TOP of starting platform (Y = platform Y + 4) - CRITICAL: If platform Y=20, SpawnLocation MUST be Y=24, NOT Y=20 or Y=0! Player must spawn ON TOP, NOT UNDERGROUND!
3. START sign/indicator on starting platform
4. Platform2, platform3, platform4, platform5, platform6, platform7, platform8, platform9, platform10 (minimum 10 platforms) - COUNT THEM: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 - ALL MUST BE CREATED!
   MANDATORY CHECKLIST - You MUST write code that creates ALL of these platforms:
   [ ] local platform2 = Instance.new('Part', Workspace); platform2.Size = Vector3.new(24,3,24); platform2.Position = Vector3.new(60,22,40); platform2.Material = Enum.Material.Neon; platform2.BrickColor = BrickColor.new('Bright green'); platform2.Anchored = true
   [ ] local platform3 = Instance.new('Part', Workspace); platform3.Size = Vector3.new(22,3,22); platform3.Position = Vector3.new(120,24,-30); platform3.Material = Enum.Material.Neon; platform3.BrickColor = BrickColor.new('Bright yellow'); platform3.Anchored = true
   [ ] local platform4 = Instance.new('Part', Workspace); platform4.Size = Vector3.new(20,3,20); platform4.Position = Vector3.new(180,20,50); platform4.Material = Enum.Material.Neon; platform4.BrickColor = BrickColor.new('Bright blue'); platform4.Anchored = true
   [ ] local platform5 = Instance.new('Part', Workspace); platform5.Size = Vector3.new(23,3,23); platform5.Position = Vector3.new(250,25,-40); platform5.Material = Enum.Material.Neon; platform5.BrickColor = BrickColor.new('Bright yellow'); platform5.Anchored = true
   [ ] local platform6 = Instance.new('Part', Workspace); platform6.Size = Vector3.new(21,3,21); platform6.Position = Vector3.new(320,22,60); platform6.Material = Enum.Material.Neon; platform6.BrickColor = BrickColor.new('Bright blue'); platform6.Anchored = true
   [ ] local platform7 = Instance.new('Part', Workspace); platform7.Size = Vector3.new(26,3,26); platform7.Position = Vector3.new(390,27,-50); platform7.Material = Enum.Material.Neon; platform7.BrickColor = BrickColor.new('Bright red'); platform7.Anchored = true
   [ ] local platform8 = Instance.new('Part', Workspace); platform8.Size = Vector3.new(24,3,24); platform8.Position = Vector3.new(460,24,40); platform8.Material = Enum.Material.Neon; platform8.BrickColor = BrickColor.new('Bright yellow'); platform8.Anchored = true
   [ ] local platform9 = Instance.new('Part', Workspace); platform9.Size = Vector3.new(25,3,25); platform9.Position = Vector3.new(530,22,-30); platform9.Material = Enum.Material.Neon; platform9.BrickColor = BrickColor.new('Bright blue'); platform9.Anchored = true
   [ ] local platform10 = Instance.new('Part', Workspace); platform10.Size = Vector3.new(23,3,23); platform10.Position = Vector3.new(600,26,50); platform10.Material = Enum.Material.Neon; platform10.BrickColor = BrickColor.new('Bright green'); platform10.Anchored = true
   ALL 9 PLATFORMS (platform2 through platform10) MUST BE CREATED! DO NOT STOP AT 3 OR 4!
5. Optionally platform11 and platform12 for 11-12 platform count (for longer, more challenging game)
6. FINISH sign on the last platform
7. All platforms must have: Material = Neon or GlowMaterial, Anchored = true, Position Y > 18 (FLOATING HIGH, NOT ON GROUND)
8. Character movement setup (Players.PlayerAdded with CharacterAdded)
9. JumpPower set to 50 for good jumping
10. Chat messages to guide players
11. Checkpoints with touch detection (optional but recommended)
12. Respawn system (optional but recommended)

The complete script should be 200+ lines of code to include all these elements properly.
IF PLAYER SPAWNS UNDERGROUND: 
- SpawnLocation Y is wrong - it MUST be platform Y + 4 (if platform Y=20, SpawnLocation MUST be Y=24, NOT Y=20 or Y=0)
- SpawnLocation.Enabled MUST be true
- SpawnLocation.Neutral MUST be true
- MUST add Players.PlayerAdded event to explicitly teleport player: game.Players.PlayerAdded:Connect(function(player) player.CharacterAdded:Connect(function(character) wait(0.1); local humanoidRootPart = character:WaitForChild('HumanoidRootPart', 5); if humanoidRootPart then humanoidRootPart.CFrame = CFrame.new(0, 24, 0) end end) end)
IF ONLY 3-4 PLATFORMS: You have FAILED - you MUST create 10-12 platforms for a real floating game! COUNT: platform1, platform2, platform3, platform4, platform5, platform6, platform7, platform8, platform9, platform10 (minimum 10)

If they mention Capture the Flag, create BOTH bases, BOTH flags, teams, weapons with working touch detection, health packs with working touch detection, scoring system that WORKS, chat messages - EVERYTHING functional.

If they mention an obby or obstacle course:
- Create SEPARATE floating platforms/islands (NOT connected in a path)
- Each platform should be SMALLER and more attractive (size Vector3.new(20,3,20) to Vector3.new(30,3,30) - smaller size, more attractive, not extremely large)
- Create EXACTLY 10-12 platforms total (longer course, more challenging, extended gameplay)
- CRITICAL: You MUST write code that creates ALL platforms individually - DO NOT use loops or placeholders
- IF YOU ONLY CREATE 3 PLATFORMS, YOU HAVE FAILED! You MUST create at minimum platform1, platform2, platform3, platform4, platform5, platform6, platform7, platform8, platform9, platform10
- Each platform must be created with explicit Instance.new('Part', Workspace) code
- ALL platforms MUST be visible when the script runs - NO MISSING platforms
- DO NOT STOP CREATING PLATFORMS AFTER PLATFORM3 - YOU MUST CONTINUE TO PLATFORM10 AT MINIMUM!
- Red platform MUST be FAR AWAY (position at least 300+ studs from start, maximum distance)
- Finish platform MUST be at MAXIMUM distance (600-750 studs from start for extended course)
- ALL platforms MUST float at Y > 18 (floating HIGH in air, NOT on ground/baseplate, vary Y between 18-28 for visual depth)
- CRITICAL: Platforms work with OR without baseplate - they are ALWAYS floating high above ground (Y > 18)
- Even if baseplate exists at Y=0, all platforms must be at Y > 18 (clearly visible floating above baseplate)
- NO platforms should be at Y < 5 (ground level) - ALL platforms must be floating high, completely independent of baseplate
- Starting platform MUST be floating at Y > 18 (e.g., Vector3.new(0,20,0)), NOT on the baseplate/ground
- CRITICAL SPAWN FIX: Create SpawnLocation ON TOP of starting platform (position Y = platform Y + 4, same X/Z) so players spawn STANDING ON the platform, NOT UNDERGROUND!
- NEVER place SpawnLocation at ground level (Y=0 or Y=1) - player will spawn UNDERGROUND - THIS IS BROKEN!
- NEVER place SpawnLocation at same Y as platform (e.g., both at Y=20) - player will spawn INSIDE platform - THIS IS BROKEN!
- SpawnLocation Y MUST be platform Y + 4 (if platform Y=20, SpawnLocation MUST be Y=24) - this puts player ON TOP, not underground!
- If SpawnLocation is at same Y as platform or lower, player will spawn UNDERGROUND - THIS IS WRONG AND BROKEN!
- All platforms MUST have Anchored = true to keep them floating in position
- SpawnLocation properties: Anchored = true, Size = Vector3.new(4,4,4), Transparency = 1, CanCollide = false
- Create START sign/indicator: Create Part (size Vector3.new(8,3,12), position on starting platform top, BrickColor = Bright green, Anchored = true) with SurfaceGui (Face = Top) + TextLabel (Text = "START", TextSize = 24, Font = ArialBold, TextColor3 = Black, TextScaled = true, BackgroundTransparency = 1) so players know where to begin - text MUST be clearly visible
- Platforms MUST have EXTREMELY LARGE GAPS (40-60 studs minimum between platforms in X/Z coordinates - players must make HUGE JUMPS)
- Platform positions MUST vary significantly in BOTH X AND Z directions (NOT in a straight line - use irregular scattered placement like (0,18,0), (60,22,40), (115,20,-45), (175,25,55))
- Example WRONG: (0,18,0), (50,18,0), (100,18,0) - DON'T do this, it's a straight line
- If they mention "floating islands", create large square/rectangular platforms (30-42 studs wide) with Neon or GlowMaterial that look like actual islands floating in air
- Platform colors: Use Bright blue, Bright green, Bright yellow, Bright red for variety
- If they mention "moving obstacles", MUST create Parts that move WITH PROPER CODE:
  * Spinning obstacles ON platforms: Create Part (size Vector3.new(4-6,4-6,4-6)), add BodyAngularVelocity with MaxTorque = Vector3.new(math.huge, math.huge, math.huge) and AngularVelocity = Vector3.new(0, 10, 0) for fast visible rotation
  * Code: local bav = Instance.new('BodyAngularVelocity', obstacle); bav.MaxTorque = Vector3.new(math.huge, math.huge, math.huge); bav.AngularVelocity = Vector3.new(0, 10, 0); obstacle.Anchored = false
  * Moving obstacles BETWEEN platforms: Create Part, use TweenService.Create() with TweenInfo.new(2-3, Enum.EasingStyle.Linear, Enum.EasingDirection.InOut, math.huge, true) for continuous back-and-forth movement
  * Code: local ts = game:GetService('TweenService'); local moveTween = ts:Create(obstacle, TweenInfo.new(3, Enum.EasingStyle.Linear, Enum.EasingDirection.InOut, math.huge, true), {{Position = endPos}}); moveTween:Play()
  * Place 3-5 moving obstacles: 2-3 ON platforms (spinning cubes), 1-2 BETWEEN platforms (moving barriers)
  * Obstacles MUST be visibly moving when game runs - include movement code in script, NOT static
- Create checkpoints with working touch detection that save spawn (glowing parts on platforms)
- Create finish line with working detection (large platform at end position, Bright green color to distinguish)
- CRITICAL: Create FINISH/STOP sign on finish platform - Create Part (size Vector3.new(8,3,12), position on finish platform top, BrickColor = Bright green, Anchored = true) with SurfaceGui (Face = Top) + TextLabel (Text = "FINISH" or "STOP", TextSize = 24, Font = ArialBold, TextColor3 = Black, TextScaled = true, BackgroundTransparency = 1) so players know where the game ends - text MUST be clearly visible
- EVERYTHING functional and VISIBLY MOVING - obstacles must actually move, not be static

NO incomplete code. NO placeholders. NO non-functional features. EVERYTHING must WORK."""

    def _structure_response(self, ai_response: Dict[str, Any], original_prompt: str) -> Dict[str, Any]:
        """Structure and validate the AI response."""
        
        # Ensure all required fields exist
        structured = {
            "title": ai_response.get("title", "Generated Roblox Game"),
            "narrative": ai_response.get("narrative", original_prompt),
            "lua_script": ai_response.get("lua_script", "-- No script generated"),
            "modules": ai_response.get("modules", []),
            "testing_steps": ai_response.get("testing_steps", [
                "Insert script into Roblox Studio",
                "Test in Play mode"
            ]),
            "assets_needed": ai_response.get("assets_needed", []),
            "optimization_tips": ai_response.get("optimization_tips", [])
        }
        
        return structured

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 150,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Generate a chat completion response using OpenAI.
        Used for NPC dialogues, AI assistants, and interactive characters in Roblox.
        
        Args:
            messages: List of message dicts with "role" and "content"
            system_prompt: System prompt to set AI behavior/personality
            temperature: Creativity (0.0-2.0)
            max_tokens: Max response length
            context: Optional game context (player name, game state, etc.)
        
        Returns:
            AI-generated response message
        """
        try:
            # Small TTL cache for repeated questions (reduces cost + latency)
            cache_key_src = {
                "model": self.model,
                "system": system_prompt or "",
                "messages": messages[-3:],  # enough for short context
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            key = hashlib.sha256(json.dumps(cache_key_src, sort_keys=True).encode("utf-8")).hexdigest()
            now = time.time()
            cached = self._chat_cache.get(key)
            if cached:
                exp, msg = cached
                if now < exp and isinstance(msg, str) and msg:
                    return msg

            # Build message list
            message_list = []
            
            # Add system prompt if provided
            if system_prompt:
                message_list.append({"role": "system", "content": system_prompt})
            elif context:
                # Build default system prompt from context
                context_parts = []
                if context.get("character_name"):
                    context_parts.append(f"You are {context['character_name']}")
                if context.get("game_name"):
                    context_parts.append(f"in the game '{context['game_name']}'")
                if context.get("personality"):
                    context_parts.append(f"with personality: {context['personality']}")
                if context.get("player_name"):
                    context_parts.append(f"talking to {context['player_name']}")
                
                if context_parts:
                    system_prompt = ". ".join(context_parts) + ". Keep responses short, friendly, and game-appropriate."
                    message_list.append({"role": "system", "content": system_prompt})
            
            # Add conversation messages
            message_list.extend(messages)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=message_list,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract response text
            out = response.choices[0].message.content.strip()
            if out:
                self._chat_cache[key] = (now + 20.0, out)
            return out
            
        except Exception as e:
            raise Exception(f"OpenAI chat completion failed: {str(e)}")

