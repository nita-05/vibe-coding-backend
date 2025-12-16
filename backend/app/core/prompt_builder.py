from typing import Dict, Any, List
import json
import os


class PromptBuilder:
    """Handles Roblox-specific prompt engineering and safety validation."""
    
    def __init__(self):
        self.examples_dir = os.path.join(os.path.dirname(__file__), "../prompts/examples")
        
    def enhance_prompt(
        self,
        user_prompt: str,
        blueprint_id: str = None,
        settings: Dict[str, Any] = None
    ) -> str:
        """
        Enhance user prompt with blueprint context and settings.
        Supports natural language queries with or without blueprints.
        """
        enhanced = user_prompt
        
        # If blueprint is selected, add blueprint-specific context
        if blueprint_id:
            blueprint_context = self._get_blueprint_context(blueprint_id)
            if blueprint_context:
                enhanced = f"{blueprint_context}\n\nUser request: {user_prompt}"
        else:
            # No blueprint selected - enhance with natural language understanding
            # The AI will interpret the natural language prompt directly
            enhanced = f"User request: {user_prompt}\n\nInterpret this natural language request and create a complete, working game. Extract the game type and all mentioned features, then implement everything."
        
        return enhanced
    
    def _get_blueprint_context(self, blueprint_id: str) -> str:
        """Get blueprint-specific context for prompt enhancement."""
        blueprints = {
            "obby-basic": (
                "Create a COMPLETE, FUNCTIONAL obstacle course (obby) game. MUST create: "
                "Starting platform at Vector3.new(0,20,0) (FLOATING HIGH in air, NOT on ground/baseplate, "
                "size Vector3.new(20,3,20) to Vector3.new(30,3,30) - SMALLER, MORE ATTRACTIVE, not extremely large), "
                "CRITICAL SPAWN FIX: Create SpawnLocation ON TOP of starting platform at Vector3.new(0,24,0) (Y = platform Y + 4, same X/Z) "
                "so players spawn STANDING ON the platform, NOT UNDER THE GROUND! If SpawnLocation Y is same as platform Y or lower, player will spawn UNDERGROUND - WRONG! "
                "SpawnLocation MUST be at Y = platform Y + 4 (if platform at Y=20, SpawnLocation MUST be at Y=24, NOT Y=20 or Y=0!). "
                "NEVER place SpawnLocation at Y=0, Y=1, or same Y as platform - player will spawn UNDERGROUND! "
                "SpawnLocation properties: Anchored = true, Size = Vector3.new(4,4,4), Transparency = 1, CanCollide = false, Enabled = true, Neutral = true, "
                "Position MUST be Vector3.new(0,24,0) for platform at (0,20,0) - Y=24 is ON TOP, Y=20 is INSIDE platform, Y=0 is UNDERGROUND! "
                "ALSO add Players.PlayerAdded event to explicitly set player spawn position: player.CharacterAdded:Connect(function(character) local humanoidRootPart = character:WaitForChild('HumanoidRootPart', 5); if humanoidRootPart then humanoidRootPart.CFrame = CFrame.new(0, 24, 0) end end) - this ensures player spawns ON TOP, NOT UNDERGROUND!"
                "CRITICAL: Create START sign/indicator ON TOP of starting platform: Create Part (size Vector3.new(8,3,12), "
                "position on starting platform top at Vector3.new(0,22,0), BrickColor = Bright green, Anchored = true) "
                "with SurfaceGui (Face = Enum.NormalId.Top) + TextLabel (Text = 'START', TextSize = 24, "
                "Font = Enum.Font.ArialBold, TextColor3 = Color3.new(1,1,1), TextScaled = true, BackgroundTransparency = 1) "
                "so players can SEE START text clearly ON TOP of platform, "
                "create EXACTLY 10-12 SEPARATE SMALLER floating platforms/islands at different heights and positions - YOU MUST CREATE ALL PLATFORMS, NOT JUST 3 OR 4! "
                "If you only create 3-4 platforms, you have FAILED COMPLETELY AND THE GAME WILL NOT WORK! The script MUST include platform1, platform2, platform3, platform4, platform5, platform6, platform7, platform8, platform9, platform10, and optionally platform11 and platform12. "
                "DO NOT STOP AT 3 PLATFORMS! DO NOT STOP AT 4 PLATFORMS! DO NOT STOP AT 5 PLATFORMS! YOU MUST CREATE AT MINIMUM 10 PLATFORMS (platform1 through platform10)! "
                "MANDATORY: You MUST write code that creates platform1, platform2, platform3, platform4, platform5, platform6, platform7, platform8, platform9, platform10 - ALL TEN PLATFORMS! "
                "Each platform MUST be created individually with explicit code - platform1 = Instance.new, platform2 = Instance.new, platform3 = Instance.new, platform4 = Instance.new, platform5 = Instance.new, platform6 = Instance.new, platform7 = Instance.new, platform8 = Instance.new, platform9 = Instance.new, platform10 = Instance.new. "
                "Count your platforms as you create them: 1 (platform1), 2 (platform2), 3 (platform3), 4 (platform4), 5 (platform5), 6 (platform6), 7 (platform7), 8 (platform8), 9 (platform9), 10 (platform10) - if you stop before reaching platform10, you have FAILED! "
                "CRITICAL CHECKLIST: Before finishing your script, verify you have created: [ ] platform1, [ ] platform2, [ ] platform3, [ ] platform4, [ ] platform5, [ ] platform6, [ ] platform7, [ ] platform8, [ ] platform9, [ ] platform10 - ALL MUST BE CHECKED! "
                "(ALL platforms MUST float at Y > 18, NOT on ground/baseplate, vary Y between 18-28 for visual depth, "
                "size Vector3.new(20,3,20) to Vector3.new(30,3,30) - smaller and more attractive, "
                "platforms can form a winding path like in classic obby games, with GAPS of 30-50 studs between platforms - players must make jumps), "
                "NO platforms should be at Y < 5 (ground level) - ALL platforms must float high in air, "
                "RED platform MUST be FAR AWAY (position at least 300+ studs from start, maximum distance like Vector3.new(350,27,50)), "
                "finish platform MUST be at MAXIMUM distance (600-750 studs from start like Vector3.new(740,28,60)), "
                "platform positions can vary in X AND Z directions to create a path (example positions for 10-12 platforms: (0,20,0), (60,22,40), (120,24,-30), "
                "(180,20,50), (250,25,-40), (320,22,60), (390,27,-50), (460,24,40), (530,22,-30), (600,26,50), (670,24,-40), (740,28,60) for finish), "
                "each platform should be its own Part with Material = Neon or GlowMaterial, "
                "BrickColor = Bright blue/green/yellow/red for variety, Anchored = true, "
                "Create FINISH/STOP sign on finish platform: Create Part (size Vector3.new(8,3,12), position on finish platform top, "
                "BrickColor = Bright green, Anchored = true) with SurfaceGui (Face = Enum.NormalId.Top) + TextLabel "
                "(Text = 'FINISH', TextSize = 24, Font = Enum.Font.ArialBold, TextColor3 = Color3.new(1,1,1), "
                "TextScaled = true, BackgroundTransparency = 1) so players know where the game ends, "
                "checkpoints (3-4 glowing parts on platforms players can touch with Touch detection that saves spawn point), "
                "respawn system (CharacterAdded event that teleports to last checkpoint when Humanoid dies), "
                "touch events for checkpoints that WORK (Touched:Connect with complete logic), GUI messages guiding players. "
                "If user mentions 'moving obstacles', MUST create Parts that move WITH PROPER CODE: "
                "for spinning obstacles ON platforms (size Vector3.new(4-6,4-6,4-6)), add BodyAngularVelocity with "
                "MaxTorque = Vector3.new(math.huge, math.huge, math.huge) and AngularVelocity = Vector3.new(0, 10, 0) "
                "for fast visible rotation - code: local bav = Instance.new('BodyAngularVelocity', obstacle); "
                "bav.MaxTorque = Vector3.new(math.huge, math.huge, math.huge); bav.AngularVelocity = Vector3.new(0, 10, 0), "
                "for moving obstacles BETWEEN platforms, use TweenService.Create() with TweenInfo.new(2-3, Enum.EasingStyle.Linear, "
                "Enum.EasingDirection.InOut, math.huge, true) for continuous back-and-forth movement, "
                "place 3-5 moving obstacles total (2-3 ON platforms as spinning cubes, 1-2 BETWEEN platforms as moving barriers), "
                "obstacles MUST be visibly moving when game runs - include movement code in script, NOT static. "
                "Character movement MUST work (Players.PlayerAdded with CharacterAdded to ensure Humanoid exists). "
                "Jumping MUST work (Humanoid.JumpPower = 50). Use Instance.new('Part') for ALL elements. "
                "Platforms must be SMALLER, ATTRACTIVE ISLANDS (20-30 studs wide) FLOATING HIGH in air (Y > 18) "
                "with GAPS (30-50 studs) in a path-like arrangement - floating high, NOT on ground. NO placeholders. "
                "Complete FUNCTIONAL obby in ONE script."
            ),
            "tycoon-basic": (
                "Create a COMPLETE, PRODUCTION-READY tycoon game that works fully in Roblox Studio. CRITICAL REQUIREMENTS - MUST CREATE ALL OF THESE: "
                "1. PLAYER BASE SYSTEM: Create starter base platform at Vector3.new(0,1,0) (size Vector3.new(40,1,40), BrickColor = Bright blue, Material = SmoothPlastic, Anchored = true). "
                "Each player gets their own base section. Create base expansion system where players start with base1, and can unlock base2, base3, base4 (each 40 studs wide, positioned at Vector3.new(0,1,0), Vector3.new(50,1,0), Vector3.new(100,1,0), Vector3.new(150,1,0) respectively). "
                "2. MONEY SYSTEM: Create leaderstats folder for each player (game.Players.PlayerAdded → Create Folder 'leaderstats' → Create IntValue 'Cash' with initial value 100). "
                "Money MUST persist and update in real-time. Display money in GUI (see GUI section). "
                "3. MONEY GENERATOR: Create glowing part at Vector3.new(0,2,0) on starter base (size Vector3.new(6,6,6), Material = Neon, BrickColor = Bright yellow, Name = 'MoneyGenerator', Anchored = true). "
                "Add ClickDetector to generator. When clicked, add money to player's Cash (increment by 10 + upgrade multiplier). "
                "Add visual feedback: spawn floating money text above generator, play sound effect (optional), create particle effect (optional). "
                "CRITICAL: Click detection MUST work: local clickDetector = Instance.new('ClickDetector', generator); clickDetector.MaxActivationDistance = 50; generator.ClickDetector.MouseClick:Connect(function(player) -- add money code here end). "
                "4. PASSIVE INCOME: Create automatic money generation that runs every second (game:GetService('RunService').Heartbeat:Connect or while wait(1) do loop). "
                "Each player earns passive income based on owned generators (e.g., 5 cash per generator per second). "
                "5. UPGRADE SYSTEM: Create upgrade station (Part at Vector3.new(15,2,0), size Vector3.new(8,8,8), Material = Neon, BrickColor = Bright green, Name = 'UpgradeStation', Anchored = true) with ClickDetector. "
                "Create multiple upgrades: Click Power (increases money per click, costs 50, 100, 200, etc.), Generator Speed (reduces click cooldown, costs 100, 200, 400, etc.), Auto Generator (unlocks passive income, costs 500), Base Expansion (unlocks new base sections, costs 1000, 2000, etc.). "
                "Upgrade data stored in player's Folder (create 'Upgrades' folder in player with IntValues for each upgrade level). "
                "When upgrade purchased, check if player has enough Cash, deduct cost, update upgrade level, apply upgrade effect. "
                "6. BUILDING SYSTEM: Create at least 5-8 building spots on each base (Parts at different positions like Vector3.new(-15,2,0), Vector3.new(15,2,0), Vector3.new(0,2,-15), Vector3.new(0,2,15), etc., size Vector3.new(10,10,10), Material = SmoothPlastic, BrickColor = Medium stone grey, Name = 'BuildingSpot', Anchored = true, CanCollide = false, Transparency = 0.5). "
                "When player reaches certain upgrade level or has enough money, buildings appear on spots (create Parts that look like buildings - different sizes, colors, materials - representing different structures like shops, factories, towers). "
                "Each building spot can have multiple building levels (level 1 building appears, then level 2 replaces it, etc.). "
                "7. GUI SYSTEM - MONEY DISPLAY: Create ScreenGui in StarterGui (game.StarterGui:SetCore or create ScreenGui in ReplicatedStorage/StarterGui). "
                "Create Frame (size UDim2.new(0, 200, 0, 50), position UDim2.new(0, 10, 0, 10), BackgroundColor3 = Color3.new(0,0,0), BackgroundTransparency = 0.3, BorderSizePixel = 2, BorderColor3 = Color3.new(0,1,1)). "
                "Add TextLabel inside Frame (Text = 'Cash: $0', TextSize = 24, Font = Enum.Font.ArialBold, TextColor3 = Color3.new(1,1,0), BackgroundTransparency = 1, Size = UDim2.new(1,0,1,0)). "
                "Update text every second: while wait(1) do local leaderstats = player:FindFirstChild('leaderstats'); if leaderstats then local cash = leaderstats:FindFirstChild('Cash'); if cash then gui.TextLabel.Text = 'Cash: $' .. cash.Value end end end. "
                "8. GUI SYSTEM - UPGRADE MENU: Create ScreenGui with Frame (visible when upgrade station clicked, size UDim2.new(0, 300, 0, 400), position UDim2.new(0.5, -150, 0.5, -200), BackgroundColor3 = Color3.new(0.1,0.1,0.2), BorderSizePixel = 2, BorderColor3 = Color3.new(0,1,1)). "
                "Add TextLabel at top (Text = 'UPGRADES', TextSize = 28, Font = Enum.Font.ArialBold, TextColor3 = Color3.new(1,1,1)). "
                "Add upgrade buttons for each upgrade type (TextButton, size UDim2.new(0.9,0,0,60), position varies, BackgroundColor3 = Color3.new(0.2,0.2,0.3), TextColor3 = Color3.new(1,1,1), Text = 'Upgrade Click Power - $50', Font = Enum.Font.ArialBold). "
                "Each button has MouseButton1Click event that purchases upgrade. "
                "Show current level and next cost on each button. "
                "9. VISUAL FEEDBACK: When money earned, spawn floating text above generator (create Part with BillboardGui + TextLabel, tween upward, then destroy). "
                "When building unlocked, tween building part in (TweenService, scale from 0 to full size, position from above to final). "
                "When upgrade purchased, show chat message or GUI notification. "
                "10. SPAWN SYSTEM: Create SpawnLocation at Vector3.new(0,5,0) (Y = base Y + 4) so players spawn ON BASE, NOT UNDERGROUND. SpawnLocation.Enabled = true, SpawnLocation.Neutral = true. "
                "Also add Players.PlayerAdded → CharacterAdded → teleport player to spawn position. "
                "11. BASE EXPANSION VISUALS: When base expands, create new base platform, add new building spots, new generators, new upgrade stations. "
                "Each base expansion should be visually distinct (different colors, decorations). "
                "12. MULTI-PLAYER SUPPORT: Each player has separate money, upgrades, buildings. Use player-specific Folders in Workspace or ReplicatedStorage. "
                "Create player base manager that handles per-player state. "
                "13. GAME LOOP: Run automatic income generation, GUI updates, building unlocks continuously. "
                "Use RunService.Heartbeat or while wait(1) do for game loop. "
                "14. ERROR HANDLING: Check if leaderstats exists before accessing, check if parts exist before touching, handle nil values. "
                "15. CHAT GUIDANCE: Use StarterGui:SetCore('ChatMakeSystemMessage', {Text = 'Welcome! Click the yellow generator to earn money!'}) to guide players. "
                "CRITICAL: ALL CODE MUST BE IN ONE SCRIPT. NO placeholders, NO 'TODO', NO incomplete features. "
                "The script MUST create EVERYTHING when pasted into ServerScriptService and Play is clicked. "
                "Everything must be created with Instance.new() - base, generators, buildings, GUI, leaderstats, upgrades. "
                "The game MUST be fully playable in Roblox Studio immediately after pasting. "
                "Test that: money system works, clicking generator adds money, GUI updates, upgrades can be purchased, buildings appear, base expands. "
                "Complete production-ready tycoon game in ONE script (300+ lines minimum to include all features)."
            ),
            "narrative-basic": "Create a COMPLETE story game. MUST create: NPC character (Part with humanoid or visible model), dialogue triggers (3-4 parts players touch to start conversations), quest items (collectible parts), dialogue GUI (ScreenGui with TextLabel showing story text), quest tracker GUI, touch events for all interactive elements, story progression system, chat messages guiding narrative. Use Instance.new() for ALL elements. Position NPCs and triggers in clear locations. NO placeholders. Complete story experience in ONE script.",
            "simulator-basic": "Create a COMPLETE simulator game. MUST create: Currency system (leaderstats with coins value), upgrade buttons (3-5 clickable parts for different upgrades), currency display GUI (ScreenGui showing coins, clicks per second), auto-generator (part that spawns currency automatically), rebirth button (clickable part to reset with bonus), upgrade effects (creates new parts or modifies existing ones), click detection system, progression tracking. Use Instance.new() for ALL elements. NO placeholders. Complete simulator with working mechanics in ONE script.",
            "racing-basic": "Create a COMPLETE racing game. MUST create: Starting line (large part at Vector3.new(0,1,0)), race track (multiple parts forming a path), checkpoints (3-5 glowing parts along track players must pass through), finish line (glowing part at end of track), lap counter system, leaderboard (leaderstats with LapCount), checkpoint detection (touch events), lap completion detection, reset system for new races, chat messages for lap progress. Use Instance.new('Part') to build entire track. Position checkpoints clearly. NO placeholders. Complete racing game in ONE script.",
            "fps-basic": (
                "Create a COMPLETE, PRODUCTION-READY First Person Shooter game that AUTOMATICALLY WORKS in Roblox Studio with ZERO manual setup. Just paste into ServerScriptService and click Play - it works immediately! CRITICAL REQUIREMENTS - MUST CREATE ALL OF THESE: "
                "1. TEAM SYSTEM: Create Red Team and Blue Team (game.Teams:CreateTeam). Red Team (TeamColor = BrickColor.new('Bright red'), Name = 'Red Team'). Blue Team (TeamColor = BrickColor.new('Bright blue'), Name = 'Blue Team'). Auto-assign players to teams on join (game.Players.PlayerAdded → assign to team). "
                "2. SPAWN SYSTEM: Create Red SpawnLocation at Vector3.new(-50,5,0) (Size Vector3.new(20,10,20), TeamColor = Bright red, Enabled = true, Neutral = false). Create Blue SpawnLocation at Vector3.new(50,5,0) (Size Vector3.new(20,10,20), TeamColor = Bright blue, Enabled = true, Neutral = false). Also create neutral spawns at Vector3.new(0,5,-30) and Vector3.new(0,5,30) for FFA mode. Add Players.PlayerAdded → CharacterAdded → teleport to team spawn on death/respawn. "
                "3. WEAPON SYSTEM - MULTIPLE WEAPONS (VISUAL + FUNCTIONAL): Create at least 3 weapon types that BOTH LOOK GOOD and WORK PROPERLY: "
                "   - Rifle: Part at Vector3.new(0,3,0), size Vector3.new(4,2,8), Material = Neon OR SmoothPlastic, BrickColor = Dark stone grey OR Really black, Name = 'Rifle', Damage = 25, FireRate = 600 RPM, MaxAmmo = 30, Range = 500 studs. "
                "      VISUAL: Make it look like a real rifle - use MeshPart OR combine multiple Parts to create rifle shape (barrel Part, stock Part, handle Part). Add SpecialMesh OR use Part with proper proportions. Add decal or Texture for detail. "
                "      Add BillboardGui with TextLabel above weapon showing 'RIFLE - Click to Pickup' (BackgroundColor3 = Color3.new(0,0,0), BackgroundTransparency = 0.3, TextColor3 = Color3.new(1,1,1), TextSize = 16, Font = Enum.Font.ArialBold). "
                "      FUNCTIONAL: ClickDetector (MaxActivationDistance = 50). When player clicks weapon, equip it (create Tool in player's Backpack), give player IntValue 'CurrentAmmo' with value 30, IntValue 'MaxAmmo' with value 30, Tool handle shooting. "
                "      Shooting: Use Tool.Activated event OR RemoteEvent, RaycastParams for hit detection, deal damage to hit players, create muzzle flash effect, reduce ammo. "
                "   - Pistol: Part at Vector3.new(-20,3,0), size Vector3.new(2,1,5), Material = Metal OR SmoothPlastic, BrickColor = Dark stone grey OR Really black, Name = 'Pistol', Damage = 15, FireRate = 300 RPM, MaxAmmo = 15, Range = 200 studs. "
                "      VISUAL: Make it look like a real pistol - use smaller Parts, add handle detail, use SpecialMesh OR multiple Parts. Add BillboardGui showing 'PISTOL - Click to Pickup' (same style as Rifle). "
                "      FUNCTIONAL: ClickDetector, equips as Tool, shooting works, ammo tracking works, visual muzzle flash when firing. "
                "   - Shotgun: Part at Vector3.new(20,3,0), size Vector3.new(5,3,10), Material = Neon OR SmoothPlastic, BrickColor = Dark stone grey OR Really black, Name = 'Shotgun', Damage = 40, FireRate = 60 RPM, MaxAmmo = 8, Range = 100 studs. "
                "      VISUAL: Make it look like a real shotgun - wider barrel, pump handle detail, use SpecialMesh OR multiple Parts. Add BillboardGui showing 'SHOTGUN - Click to Pickup'. "
                "      FUNCTIONAL: ClickDetector, equips as Tool, shooting works with spread pattern (multiple rays for shotgun), ammo tracking works. "
                "   CRITICAL: Weapons MUST BOTH look visually appealing AND work functionally. "
                "   Visual quality: Use proper materials (Metal for realistic look, SmoothPlastic for clean look, Neon for glowing weapons), proper colors (Dark stone grey, Really black, or custom colors), proper sizes (rifle longer, pistol smaller, shotgun wider), add details (use MeshPart OR SpecialMesh OR combine multiple Parts to create weapon shape - barrel, stock, handle, scope). Add decals or textures for visual appeal. "
                "   Functional quality: ClickDetector works (player can click to pick up), pickup works (weapon disappears from map, appears in player's hand), Tool equips properly (Tool in Backpack, appears in player's hand, can be activated), shooting works (left-click fires weapon, raycast hits players), damage works (hit players take damage, health decreases), ammo works (ammo decreases on shot, reloads when empty or R pressed), reload works (wait time, ammo refills, UI updates). "
                "   EVERYTHING MUST WORK: Weapons must actually shoot, damage must actually be applied, health must actually decrease, ammo must actually track, reload must actually refill ammo. "
                "   EVERYTHING MUST LOOK GOOD: Weapons must look like real weapons (not just blocks), health packs must glow and pulse, armor must be visible, all items must have labels showing what they are. "
                "   Weapon shooting logic: Create Tool in player's Backpack when picked up, Tool.Activated event fires weapon, use RaycastParams for hit detection, calculate damage based on distance and weapon type, apply damage to hit players, create visual muzzle flash, create hit sparks/effects. "
                "   Ammo system: Track current ammo (IntValue in player or Tool), decrease on shot, show ammo in UI, reload when R key pressed (UserInputService.KeyDown) or ammo = 0, reload takes time (wait(2) for reload). "
                "4. HEALTH SYSTEM: Each player starts with 100 HP. Create IntValue 'Health' in player's Character or use Humanoid.Health. "
                "   Damage application: When player hit by weapon, reduce Health by weapon damage, check if Health <= 0 (death), trigger respawn. "
                "   Death detection: Humanoid.Died event → respawn player after 3 seconds, increment Deaths counter, reset Health to 100. "
                "5. SCORING SYSTEM - ADVANCED: Create leaderstats folder for each player (game.Players.PlayerAdded → Create Folder 'leaderstats'). "
                "   Create IntValue 'Kills' (initial = 0) - increment when player kills enemy. "
                "   Create IntValue 'Deaths' (initial = 0) - increment when player dies. "
                "   Create IntValue 'Score' (initial = 0) - update Score = Kills * 10 - Deaths * 5. "
                "   Create IntValue 'Assists' (initial = 0) - track assists (optional). "
                "   Calculate K/D ratio: Kills / Deaths (display in UI). "
                "   Leaderboard: Display top 5 players by Score in UI (update every second). "
                "6. UI SYSTEM - COMPLETE GUI: Create ScreenGui in StarterGui (game.StarterGui:SetCore or create in ReplicatedStorage/StarterGui). "
                "   A. HEALTH BAR: Create Frame at position UDim2.new(0, 10, 0, 10), size UDim2.new(0, 200, 0, 30), BackgroundColor3 = Color3.new(0.2,0,0), BorderSizePixel = 2, BorderColor3 = Color3.new(1,0,0). "
                "      Add TextLabel inside (Text = 'HP: 100', TextSize = 20, Font = Enum.Font.ArialBold, TextColor3 = Color3.new(1,1,1), Size = UDim2.new(1,0,1,0)). "
                "      Update every frame: while wait(0.1) do local character = player.Character; if character then local humanoid = character:FindFirstChild('Humanoid'); if humanoid then gui.HealthLabel.Text = 'HP: ' .. math.floor(humanoid.Health) end end end. "
                "   B. AMMO COUNTER: Create Frame at position UDim2.new(1, -150, 1, -60), size UDim2.new(0, 140, 0, 40), BackgroundColor3 = Color3.new(0,0,0.2), BorderSizePixel = 2, BorderColor3 = Color3.new(0,0,1). "
                "      Add TextLabel (Text = 'AMMO: 30/30', TextSize = 24, Font = Enum.Font.ArialBold, TextColor3 = Color3.new(1,1,0), Size = UDim2.new(1,0,1,0)). "
                "      Update when ammo changes: display current/max ammo, show 'RELOAD' when low. "
                "   C. SCORE DISPLAY: Create Frame at position UDim2.new(0, 10, 0, 50), size UDim2.new(0, 200, 0, 120), BackgroundColor3 = Color3.new(0,0,0), BackgroundTransparency = 0.3, BorderSizePixel = 2, BorderColor3 = Color3.new(0,1,1). "
                "      Add TextLabels for: 'Kills: 0', 'Deaths: 0', 'K/D: 0.00', 'Score: 0' (TextSize = 18, Font = ArialBold, TextColor3 = White, positioned vertically). "
                "      Update every second from leaderstats. "
                "   D. KILL FEED: Create Frame at position UDim2.new(1, -300, 0, 10), size UDim2.new(0, 290, 0, 200), BackgroundColor3 = Color3.new(0,0,0), BackgroundTransparency = 0.5, BorderSizePixel = 0. "
                "      Add ScrollingFrame inside with TextLabels showing recent kills (e.g., 'Player1 killed Player2 with Rifle'). "
                "      Add kill events to feed (max 5 messages, auto-remove old ones). "
                "   E. CROSSHAIR: Create Frame at position UDim2.new(0.5, -10, 0.5, -10), size UDim2.new(0, 20, 0, 20), BackgroundTransparency = 1. "
                "      Add ImageLabel with crosshair image (or use 4 Parts as crosshair lines). "
                "   F. GAME TIMER: Create Frame at position UDim2.new(0.5, -100, 0, 10), size UDim2.new(0, 200, 0, 40), BackgroundColor3 = Color3.new(0,0,0), BackgroundTransparency = 0.7, BorderSizePixel = 2, BorderColor3 = Color3.new(1,1,1). "
                "      Add TextLabel (Text = 'TIME: 10:00', TextSize = 28, Font = Enum.Font.ArialBold, TextColor3 = Color3.new(1,1,0), Size = UDim2.new(1,0,1,0)). "
                "      Countdown timer: start at 10:00, decrement every second, end game when 0:00. "
                "7. MAP/ARENA - COMPLETE ENVIRONMENT: Create engaging map with: "
                "   - Base platform at Vector3.new(0,1,0), size Vector3.new(200,2,200), Material = SmoothPlastic, BrickColor = Medium stone grey, Anchored = true. "
                "   - Cover elements: Create 10-15 Parts as cover (size Vector3.new(10,8,10), positions scattered around map at Vector3.new(-40,4,20), Vector3.new(40,4,-20), etc., Material = Concrete, BrickColor = Medium stone grey, Anchored = true). "
                "   - Obstacles: Create barriers, walls, pillars at various positions to create chokepoints and strategic areas. "
                "   - Spawn protection zones: Create invisible Parts at spawns (Transparency = 1, CanCollide = false) with Script that gives players invincibility for 5 seconds after spawn. "
                "8. HEALTH PACKS (VISUAL + FUNCTIONAL): Create 4-6 health packs scattered on map that BOTH LOOK GOOD and WORK PROPERLY: "
                "   VISUAL: Parts at Vector3.new(-30,3,30), Vector3.new(30,3,-30), etc., size Vector3.new(4,4,4), Material = Neon (for glowing effect), BrickColor = Bright green, Name = 'HealthPack', Anchored = true. "
                "   Add visual detail: Use SpecialMesh (MeshType = Enum.MeshType.Sphere OR use Heart mesh if available), or create cross symbol using multiple Parts. "
                "   Add pulsing glow effect: Use TweenService to animate Transparency from 0.3 to 0.7 and back, or animate Size slightly, or use PointLight (Brightness = 2, Color = Bright green, Range = 10). "
                "   Add BillboardGui with TextLabel showing 'HEALTH PACK - Touch to Heal' (BackgroundColor3 = Color3.new(0,0.5,0), TextColor3 = Color3.new(1,1,1), TextSize = 14). "
                "   FUNCTIONAL: Add ClickDetector to each (MaxActivationDistance = 20) OR use Touched event. "
                "   Touch/Click logic: When player touches/clicks health pack, restore Humanoid.Health to 100 (or max health), hide pack (Transparency = 1, CanCollide = false), show floating text '+100 HP' above player, respawn pack after 15 seconds (reset Transparency and CanCollide, use wait(15) then reset), play sound effect if possible (Sound with SoundId). "
                "   CRITICAL: Health packs MUST both look visually appealing (glowing, pulsing, visible label) AND work functionally (actually heal player when touched). "
                "9. ARMOR PICKUPS (OPTIONAL, VISUAL + FUNCTIONAL): Create 2-3 armor pickups that BOTH LOOK GOOD and WORK PROPERLY: "
                "   VISUAL: Parts at scattered positions, size Vector3.new(4,4,4), Material = Neon, BrickColor = Bright blue, Name = 'ArmorPack'. "
                "   Add visual detail: Use SpecialMesh (MeshType = Enum.MeshType.Brick OR Cylinder), add PointLight (Brightness = 2, Color = Bright blue, Range = 10), add pulsing glow effect with TweenService. "
                "   Add BillboardGui with TextLabel showing 'ARMOR PACK - Touch to Equip' (BackgroundColor3 = Color3.new(0,0,0.5), TextColor3 = Color3.new(1,1,1)). "
                "   FUNCTIONAL: Add ClickDetector OR Touched event. "
                "   Armor system: Add IntValue 'Armor' in player's Character or leaderstats (max 100), reduce damage when hit (check Armor first, then Health), armor depletes first, then health, show armor value in UI. "
                "   CRITICAL: Armor pickups MUST both look visually appealing AND work functionally (actually provide armor when picked up). "
                "10. VISUAL EFFECTS - POLISH: "
                "    - Muzzle flash: When weapon fires, create Part at weapon muzzle (Material = Neon, BrickColor = Bright yellow, size Vector3.new(0.5,0.5,2), Transparency = 0.5) for 0.1 seconds. "
                "    - Hit effects: When player hit, create Part at hit position (Material = Neon, BrickColor = Bright red, size Vector3.new(0.5,0.5,0.5)) for 0.2 seconds, or use ParticleEmitter. "
                "    - Death effect: When player dies, create explosion effect (multiple Parts with Neon material, tween scale and transparency). "
                "    - Hit indicators: When player hits enemy, show '+' damage number floating above enemy (BillboardGui + TextLabel, tween upward, destroy after 1 second). "
                "11. GAME MODES: Support multiple modes (implement in single script with game mode selection): "
                "    - Team Deathmatch: First team to 50 kills wins. "
                "    - Free-for-All: First player to 30 kills wins. "
                "    - Capture the Flag (if requested): Add flags, bases, capture logic. "
                "12. RESPAWN SYSTEM: When player dies, wait 3 seconds, respawn at team spawn (or neutral spawn for FFA), reset Health to 100, reset ammo, give spawn protection (5 seconds invincibility). "
                "13. CHAT MESSAGES: Use StarterGui:SetCore('ChatMakeSystemMessage', {Text = 'Welcome to FPS Arena! Kill enemies to score points!'}) on join. "
                "    Announce kills: 'Player1 killed Player2 with Rifle!'. "
                "    Announce game end: 'Red Team wins! Final Score: 50-45'. "
                "14. MULTI-PLAYER SUPPORT: Each player has separate health, ammo, score. Use player-specific Folders in Workspace or ReplicatedStorage. "
                "15. GAME LOOP - AUTOMATIC START: Script MUST run immediately when pasted and Play clicked. Use RunService.Heartbeat:Connect() or spawn(function() while true do wait() end end) at the END of script to create game loop. "
                "   CRITICAL: Script initialization code MUST run IMMEDIATELY when script loads - create teams, spawn locations, weapons, UI, everything when script first runs, NOT waiting for players! "
                "   Start initialization immediately: spawn(function() -- create teams, spawns, weapons, map immediately end). "
                "   The game MUST start automatically - when Play is clicked, everything appears and works immediately! "
                "16. ERROR HANDLING: Check if player exists, character exists, parts exist before accessing. Handle nil values gracefully. "
                "17. SCRIPT EXECUTION - CRITICAL: The script MUST execute ALL initialization code immediately when Play is clicked. "
                "   Put all setup code at the TOP of script (before any events) so it runs first: Create teams → Create spawns → Create weapons → Create map → Create UI → Then add event listeners. "
                "   Use spawn() or coroutine to run initialization in parallel. The script should NOT wait for anything - it should create everything immediately when Roblox Studio loads it!"
                "CRITICAL: ALL CODE MUST BE IN ONE SCRIPT. NO placeholders, NO 'TODO', NO incomplete features. "
                "The script MUST AUTOMATICALLY CREATE EVERYTHING when pasted into ServerScriptService and Play is clicked - ZERO manual setup required! "
                "Everything must be created with Instance.new() - weapons, health packs, UI, leaderstats, teams, spawns, ALL game elements. "
                "SCRIPT EXECUTION ORDER IS CRITICAL - Script must execute initialization code IMMEDIATELY when Play is clicked: "
                "   FIRST (Lines 1-100): Create teams (game.Teams:CreateTeam) - runs immediately when script loads "
                "   SECOND (Lines 101-200): Create spawn locations - runs immediately "
                "   THIRD (Lines 201-300): Create map elements (arena, cover, obstacles) - runs immediately "
                "   FOURTH (Lines 301-400): Create weapons on map - runs immediately "
                "   FIFTH (Lines 401-450): Create UI (ScreenGui in StarterGui) - runs immediately "
                "   LAST (Lines 451+): Add event listeners (Players.PlayerAdded, etc.) - handles players as they join "
                "The initialization code MUST run FIRST, BEFORE any event listeners! Use direct code execution at script top level, NOT inside functions that wait for events. "
                "The game MUST START AUTOMATICALLY - when player clicks Play in Roblox Studio, teams exist, spawns exist, map exists, weapons visible, UI appears, THEN players spawn and join - everything works immediately! "
                "NO manual configuration needed - NO editing required - NO additional setup - just paste and play! "
                "The script MUST run automatically on start - initialization code executes immediately at script load, then event listeners handle players. "
                "Test that: When Play clicked, teams appear in Teams menu, spawns visible in game, weapons visible on map, UI appears, THEN player spawns - everything works immediately. "
                "Complete production-ready FPS game in ONE script that AUTOMATICALLY WORKS (400+ lines minimum to include all features)."
            ),
            "fps-advanced": (
                "Create a SUPER ADVANCED, PRODUCTION-READY modular First Person Shooter (FPS) game system for Roblox Studio. "
                "Generate COMPLETE, WORKING scripts for ALL modules with proper folder structure and setup instructions. "
                "CRITICAL: Generate ALL scripts in the correct format with clear file names and folder locations. "
                "OUTPUT FORMAT: Provide scripts as separate code blocks labeled with their file paths (e.g., '=== StarterPlayer/StarterPlayerScripts/PlayerController.lua ==='). "
                "Then provide setup instructions. "
                ""
                "REQUIRED FOLDER STRUCTURE & SCRIPTS: "
                ""
                "1. StarterPlayer/StarterPlayerScripts/: "
                "   - PlayerController.lua: Smooth first-person camera, mobile + PC support, stamina + sprinting, jump/crouch/prone, camera bobbing, damage feedback, screen shake. "
                "   - CameraSystem.lua: Advanced camera controls, FOV adjustments, ADS (aim-down-sights) camera zoom, smooth transitions. "
                "   - GunClient.lua: Client-side gun handling, weapon switching, fire modes (single/burst/auto), ADS toggle, reload animation, heat system UI. "
                "   - RecoilSystem.lua: Dynamic recoil patterns per weapon, weapon sway, recoil recovery, pattern configs. "
                "   - InputSystem.lua: UserInputService handling, mobile touch controls, keyboard/mouse inputs, input validation. "
                "   - UIController.lua: Animated crosshair, hit marker effect, kill popup, health bar, ammo + reload UI, weapon inventory UI, mini-map, damage direction indicator. "
                ""
                "2. ReplicatedStorage/Modules/: "
                "   - GunConfig.lua: Module with all weapon stats (damage, fire rate, recoil pattern, ammo, range, penetration, drop). At least 3 weapons: Rifle, Pistol, Shotgun. "
                "   - DamageService.lua: Server-validated damage calculation, anti-cheat basics, damage falloff, penetration logic. "
                "   - AnimationService.lua: Weapon animations, reload animations, muzzle flash VFX, shell casing ejection, hit effects. "
                "   - RecoilConfig.lua: Recoil patterns for each weapon (upward curve, side spray, recovery time). "
                "   - Networking.lua: RemoteEvent/RemoteFunction setup, client-server communication, data validation. "
                ""
                "3. ReplicatedStorage/Assets/: "
                "   - Instructions to create GunModels folder (MeshParts for weapons), MuzzleFlash (ParticleEmitter), BulletImpact (ParticleEmitter), Sounds (Sound objects). "
                "   Provide code to create these assets programmatically if possible. "
                ""
                "4. ServerScriptService/: "
                "   - EnemyAI.lua: Smart enemy AI using PathfindingService, enemies attack/retreat/flank, enemy types (normal, tank, fast), state machine (Idle, Chase, Attack, Retreat). "
                "   - EnemySpawner.lua: Wave-based enemy spawning, spawn points, enemy type selection, wave progression, difficulty scaling. "
                "   - HitDetection.lua: Server-side raycast validation, hit detection for client shots, server-authoritative damage, anti-cheat validation. "
                "   - PlayerData.lua: Player data management, leaderstats (Kills, Deaths, Score), player stats tracking, data persistence. "
                ""
                "5. StarterGui/: "
                "   - Instructions to create GUI elements: Crosshair (ScreenGui + ImageLabel), HealthBar (Frame + progress bar), AmmoCounter (TextLabel), HitMarker (ImageLabel with animation), KillFeed (ScrollingFrame + TextLabels). "
                "   Provide code to create these GUIs programmatically. "
                ""
                "6. Workspace/: "
                "   - EnemyFolder: Create folder for enemies, provide code to spawn enemies into this folder. "
                ""
                "GAME FEATURES - MUST IMPLEMENT ALL: "
                ""
                "GUN SYSTEM: "
                "- Raycast-based instant hit bullets (use RaycastParams) "
                "- Bullet penetration + drop options (multiple raycasts for penetration, gravity calculation for drop) "
                "- Dynamic recoil pattern (different patterns per weapon, stored in RecoilConfig) "
                "- Weapon sway (camera movement based on movement/breathing) "
                "- Muzzle flash VFX (ParticleEmitter or Part with Neon material at muzzle position) "
                "- Shell casing ejection (spawn Part with BodyVelocity, animate rotation) "
                "- Weapon switching (Tool system, switch between weapons) "
                "- ADS (Aim-down-sights) - camera zoom, crosshair change, reduced sway "
                "- Fire modes: single (one shot per click), burst (3 shots per click), auto (continuous fire) "
                "- Reload animation + sound (use AnimationService or TweenService, play Sound) "
                "- Heat system (gun overheats after X shots, must cool down, show heat bar in UI) "
                ""
                "ENEMY SYSTEM: "
                "- Smart enemy AI using PathfindingService (PathfindingService:CreatePath, ComputeAsync) "
                "- Enemies attack (move toward player, shoot), retreat (move away when low health), flank (move to side) "
                "- Enemy types: normal (standard stats), tank (high health, slow), fast (low health, fast movement) "
                "- Enemy wave generator (spawn enemies in waves, increase difficulty) "
                "- Enemy death animation + ragdoll effect (set Humanoid.Health to 0, use BodyVelocity for ragdoll) "
                ""
                "MULTIPLAYER SYSTEM: "
                "- Remote events + remote functions (RemoteEvent for fire shots, RemoteFunction for data requests) "
                "- Server-validated damage (all damage calculated server-side, client only sends input) "
                "- Anti-cheat basics (validate shot position, check fire rate limits, validate damage) "
                "- Kill feed synced for all players (RemoteEvent broadcasts kills to all players) "
                "- Death/respawn system (on death, wait 3 seconds, respawn at spawn location) "
                ""
                "PLAYER SYSTEM: "
                "- Smooth first-person camera (Camera.CFrame manipulation, smooth interpolation) "
                "- Mobile + PC support (UserInputService.TouchEnabled check, different controls) "
                "- Stamina + sprinting (stamina bar, decrease on sprint, regenerate when not sprinting) "
                "- Jump, crouch, prone (Humanoid.Jump, Humanoid.HipHeight for crouch/prone) "
                "- Camera bobbing (camera sway when walking/running) "
                "- Damage feedback (screen red flash, camera shake on hit) "
                "- Screen shake (camera shake on explosions, hits, etc.) "
                ""
                "UI & UX: "
                "- Animated crosshair (expand on shot, contract over time, TweenService) "
                "- Hit marker effect (ImageLabel appears briefly on hit, fade out) "
                "- Kill popup (TextLabel shows 'KILL!' when enemy killed, animate) "
                "- Health bar (Frame with BackgroundColor3, Size changes with health) "
                "- Ammo + reload UI (TextLabel shows '30/120' current/max ammo, reload progress bar) "
                "- Weapon inventory UI (Frame showing equipped weapons, allow switching) "
                "- Menu + settings UI (Frame with buttons for pause, settings, quit) "
                "- Mini-map (Frame with dots showing player/enemy positions) "
                "- Damage direction indicator (arrow pointing to direction of damage) "
                ""
                "OUTPUT REQUIREMENTS: "
                "- Generate ALL scripts with complete, working code - NO placeholders, NO TODOs "
                "- Each script must be in its own code block with clear file path label "
                "- Provide setup instructions after all scripts "
                "- Explain how each module connects (which scripts call which modules) "
                "- List required Roblox objects that must be created manually (if any) "
                "- Provide assembly instructions (step-by-step how to set up in Roblox Studio) "
                "- Code must be optimized, readable, commented "
                "- All scripts must work together - test integration points "
                ""
                "SCRIPT FORMAT EXAMPLE: "
                "=== StarterPlayer/StarterPlayerScripts/PlayerController.lua === "
                "[Full working Lua code here] "
                ""
                "=== ReplicatedStorage/Modules/GunConfig.lua === "
                "[Full working Lua code here] "
                ""
                "SETUP INSTRUCTIONS: "
                "[Detailed step-by-step instructions] "
                ""
                "CRITICAL: Generate COMPLETE, RUNNABLE code for ALL files. If any dependency is missing, automatically create it. Do not leave TODOs. "
                "The final system must be production-ready and fully functional when properly assembled in Roblox Studio. "
            ),
        }
        return blueprints.get(blueprint_id, "")
    
    def validate_script_safety(self, lua_script: str) -> Dict[str, Any]:
        """
        Validate Lua script for safety and Roblox compliance.
        Returns validation result with warnings and errors.
        """
        warnings = []
        errors = []
        
        # Check for dangerous patterns
        dangerous_patterns = [
            ("http", "HTTP requests are not allowed in Roblox"),
            ("file", "File system access is not allowed"),
            ("io.open", "File I/O is not allowed"),
            ("os.execute", "OS execution is not allowed"),
            ("require", "Careful with require - ensure modules exist"),
        ]
        
        script_lower = lua_script.lower()
        
        for pattern, message in dangerous_patterns:
            if pattern in script_lower:
                if pattern == "http" or pattern == "file" or pattern == "os.execute":
                    errors.append(message)
                else:
                    warnings.append(message)
        
        # Check for basic Roblox API usage
        roblox_apis = ["workspace", "players", "replicatedstorage", "replicatedfirst"]
        has_roblox_api = any(api in script_lower for api in roblox_apis)
        
        if not has_roblox_api:
            warnings.append("Script may not use Roblox APIs - verify compatibility")
        
        # Check for obby game completeness (if it's an obby-style game)
        if "obby" in script_lower or ("platform" in script_lower and "floating" in script_lower):
            # Check for essential obby elements
            has_spawn = "spawnlocation" in script_lower
            has_platforms = "platform" in script_lower and "instance.new" in script_lower
            has_anchored = "anchored" in script_lower and "true" in script_lower
            
            # Count platforms (check for platform1 through platform10+)
            platform_count = 0
            for i in range(1, 13):
                if f"platform{i}" in script_lower or f"platform {i}" in script_lower:
                    platform_count = max(platform_count, i)
            
            # Check script length (complete obby should be 200+ lines)
            line_count = len(lua_script.split('\n'))
            
            if not has_spawn:
                warnings.append("Obby game may be missing SpawnLocation - player might spawn on ground")
            if not has_platforms:
                warnings.append("Obby game may be missing platform creation code")
            if not has_anchored:
                warnings.append("Platforms may not be anchored - they might fall")
            if platform_count < 10:
                warnings.append(f"Only {platform_count} platform(s) detected. Expected 10-12 platforms for complete obby game.")
            if line_count < 150:
                warnings.append(f"Script is only {line_count} lines. A complete obby game should be 200+ lines to include all platforms, spawn, signs, and game mechanics.")
        
        # Check for tycoon game completeness (if it's a tycoon-style game)
        if "tycoon" in script_lower or ("money" in script_lower and "generator" in script_lower and "upgrade" in script_lower):
            # Check for essential tycoon elements
            has_leaderstats = "leaderstats" in script_lower
            has_money = ("cash" in script_lower or "money" in script_lower) and ("intvalue" in script_lower or "numbervalue" in script_lower)
            has_generator = "generator" in script_lower and "clickdetector" in script_lower
            has_upgrade = "upgrade" in script_lower and ("clickdetector" in script_lower or "textbutton" in script_lower)
            has_gui = "screengui" in script_lower or "startergui" in script_lower
            has_building = "building" in script_lower or "structure" in script_lower
            
            # Check script length (complete tycoon should be 300+ lines)
            line_count = len(lua_script.split('\n'))
            
            if not has_leaderstats:
                warnings.append("Tycoon game may be missing leaderstats - money won't persist or display properly")
            if not has_money:
                warnings.append("Tycoon game may be missing money/cash value system")
            if not has_generator:
                warnings.append("Tycoon game may be missing clickable money generator with ClickDetector")
            if not has_upgrade:
                warnings.append("Tycoon game may be missing upgrade system with ClickDetector or GUI buttons")
            if not has_gui:
                warnings.append("Tycoon game may be missing GUI for displaying money and upgrades")
            if not has_building:
                warnings.append("Tycoon game may be missing building/expansion system")
            if line_count < 200:
                warnings.append(f"Script is only {line_count} lines. A complete tycoon game should be 300+ lines to include money system, GUI, upgrades, buildings, and all game mechanics.")
        
        # Check for FPS game completeness (if it's an FPS-style game)
        if "fps" in script_lower or ("shooter" in script_lower and ("weapon" in script_lower or "shoot" in script_lower)):
            # Check for essential FPS elements
            has_leaderstats = "leaderstats" in script_lower
            has_kills = "kills" in script_lower and ("intvalue" in script_lower or "numbervalue" in script_lower)
            has_weapon = "weapon" in script_lower and ("clickdetector" in script_lower or "raycast" in script_lower or "fire" in script_lower)
            has_health = "health" in script_lower or "humanoid" in script_lower
            has_damage = "damage" in script_lower or "hit" in script_lower
            has_gui = "screengui" in script_lower or "startergui" in script_lower
            has_spawn = "spawnlocation" in script_lower or "spawn" in script_lower
            has_team = "team" in script_lower or ("red" in script_lower and "blue" in script_lower)
            has_ammo = "ammo" in script_lower or "bullet" in script_lower
            
            # Check script length (complete FPS should be 400+ lines)
            line_count = len(lua_script.split('\n'))
            
            if not has_leaderstats:
                warnings.append("FPS game may be missing leaderstats - kills/deaths/score won't persist or display properly")
            if not has_kills:
                warnings.append("FPS game may be missing kills/deaths tracking system")
            if not has_weapon:
                warnings.append("FPS game may be missing weapon system with shooting mechanics")
            if not has_health:
                warnings.append("FPS game may be missing health system")
            if not has_damage:
                warnings.append("FPS game may be missing damage system")
            if not has_gui:
                warnings.append("FPS game may be missing GUI for displaying health, ammo, score, kill feed")
            if not has_spawn:
                warnings.append("FPS game may be missing spawn system")
            if not has_team:
                warnings.append("FPS game may be missing team system (recommended for FPS games)")
            if not has_ammo:
                warnings.append("FPS game may be missing ammo system")
            if line_count < 300:
                warnings.append(f"Script is only {line_count} lines. A complete FPS game should be 400+ lines to include weapons, health, scoring, UI, teams, spawns, and all game mechanics.")
        
        return {
            "is_safe": len(errors) == 0,
            "warnings": warnings,
            "errors": errors,
            "risk_score": len(errors) * 10 + len(warnings) * 2
        }

