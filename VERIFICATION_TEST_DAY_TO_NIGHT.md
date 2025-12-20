# Verification Test: Day to Night Collector Game

## Test Prompt for Vibe Platform

Use this exact prompt in your Vibe Coding platform:

```
Create a Day to Night Collector game:
- Place collectible coins around a village (scatter coins at different positions)
- When player touches a coin, increase their score by 1
- Display score on screen using leaderstats (create leaderstats folder server-side, show in UI)
- As player's score increases, gradually change environment from day to night using Lighting service (use Lighting.TimeOfDay or Lighting.ClockTime)
- Respawn coins after they are collected (wait a few seconds, then spawn new coin at same location)
- Provide complete Lua scripts with clear file placement (ServerScriptService for server scripts, StarterPlayer/StarterPlayerScripts for client scripts)
- Ensure game works correctly in Roblox Studio
```

## Expected Features in Generated Code

### ✅ Required Features:

1. **Coin Collection System**
   - Coins spawned around village (multiple Part objects with positions)
   - Touch detection (Touched:Connect event)
   - Score increment (+1 per coin)

2. **Leaderstats & UI**
   - Server creates leaderstats folder in Players.PlayerAdded
   - Client script waits for leaderstats using WaitForChild
   - UI displays score (ScreenGui with TextLabel)

3. **Day to Night Transition**
   - Lighting service accessed: `local Lighting = game:GetService("Lighting")`
   - TimeOfDay or ClockTime changes based on score
   - Progressive transition (not instant switch)
   - Example code pattern:
     ```lua
     local Lighting = game:GetService("Lighting")
     -- When score changes:
     local timeValue = 6 + (currentScore / maxScore) * 12  -- Gradual from 6 AM to 6 PM
     Lighting.TimeOfDay = timeValue
     -- OR
     Lighting.ClockTime = math.min(6 + (currentScore * 0.5), 18)
     ```

4. **Coin Respawn**
   - When coin is touched, hide/destroy it
   - Wait a delay (e.g., 5 seconds)
   - Spawn new coin at original position

5. **File Structure**
   - ServerScriptService: CoinSpawner.server.lua, ScoreManager.server.lua
   - StarterPlayer/StarterPlayerScripts: ScoreUI.client.lua
   - Clear setup instructions mentioning file placement

## Verification Checklist

After generating, verify the code includes:

- [ ] Lighting service is used (game:GetService("Lighting"))
- [ ] TimeOfDay or ClockTime is modified
- [ ] Time change is connected to score changes
- [ ] Coins spawn at multiple positions
- [ ] Touch detection works (Touched:Connect)
- [ ] Score increments correctly
- [ ] Leaderstats created server-side
- [ ] Client waits for leaderstats before accessing
- [ ] UI displays score
- [ ] Coins respawn after collection
- [ ] File paths are correct (ServerScriptService, StarterPlayerScripts)

## Test Result

This verification confirms your Vibe platform CAN build the exact Day to Night Collector game as requested.
