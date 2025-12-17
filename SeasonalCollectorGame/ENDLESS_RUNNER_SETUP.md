# 🏃 Endless Runner Game - Complete Setup

## ✅ All Systems Created

Your game has been completely transformed into a **Temple Run-style endless runner**!

### 🎮 Core Features

1. **✅ Start with Car**
   - Player spawns in a vehicle immediately
   - Vehicle stays in place, road scrolls backward

2. **✅ Lane-Based Movement**
   - **A/Left Arrow**: Move left
   - **D/Right Arrow**: Move right
   - **W/Up Arrow/Space**: Jump (to avoid gaps and low obstacles)
   - **S/Down Arrow**: Slide (to avoid high obstacles)

3. **✅ Obstacle System**
   - **Barriers**: Static red obstacles (must avoid)
   - **Moving**: Orange obstacles that move side-to-side
   - **Gaps**: Yellow markers (must jump over)

4. **✅ Health & Warnings**
   - **5 hits = Death**
   - **Warning at 3 hits**: "⚠️ WARNING! You're taking damage!"
   - **Warning at 4 hits**: Same warning
   - **5th hit**: Game Over

5. **✅ Level Progression**
   - Level up every 1000 points
   - Speed increases with level
   - More obstacles spawn at higher levels
   - Max level: 10

6. **✅ Coin Collection**
   - Coins spawn on the road
   - Collect by driving into them
   - Each coin = 10 points
   - Points per second while playing

7. **✅ Death & Restart**
   - Death screen shows final score and level
   - "RESTART" button to play again
   - Score and level tracking

## 📁 Files Created

### Server Scripts:
- `ServerScriptService/EndlessRunnerManager.server.lua` - Main game manager
- `ServerScriptService/RoadGenerator.server.lua` - Endless scrolling road
- `ServerScriptService/ObstacleSpawner.server.lua` - Obstacle spawning system
- `ServerScriptService/RoadCoinSpawner.server.lua` - Coin spawning on road

### Client Scripts:
- `StarterPlayer/StarterPlayerScripts/RunnerController.client.lua` - Player controls
- `StarterPlayer/StarterPlayerScripts/GameUI.client.lua` - In-game HUD
- `StarterPlayer/StarterPlayerScripts/DeathUI.client.lua` - Death screen

## 🎮 How to Play

1. **Game starts automatically** when you spawn
2. **Controls:**
   - **A/Left**: Move left lane
   - **D/Right**: Move right lane
   - **W/Space**: Jump
   - **S**: Slide
3. **Collect coins** for points
4. **Avoid obstacles** - 5 hits = death
5. **Level up** every 1000 points
6. **Restart** after death to play again

## ⚙️ Configuration

All settings are in `EndlessRunnerManager.server.lua`:
- `MaxHealth = 5` (hits before death)
- `WarningAt = {3, 4}` (show warnings at these hits)
- `BaseSpeed = 20` (starting speed)
- `SpeedIncreasePerLevel = 5` (speed boost per level)
- `PointsPerCoin = 10`
- `PointsPerSecond = 1`

## 🚀 Game Flow

1. Player spawns → Vehicle created automatically
2. Road starts scrolling
3. Obstacles spawn ahead
4. Coins spawn on road
5. Player collects coins → Score increases
6. Player hits obstacle → Health decreases
7. At 3-4 hits → Warning appears
8. At 5 hits → Death screen
9. Click "RESTART" → Game restarts

## 🎯 Level System

- **Level 1**: Base speed, 1 obstacle at a time
- **Level 2-3**: Slightly faster, more obstacles
- **Level 4+**: Faster speed, 1-2 obstacles per spawn
- **Level 10**: Maximum difficulty

## 💡 Tips

- Jump over gaps and low obstacles
- Slide under high obstacles
- Switch lanes to avoid obstacles
- Collect coins for points and level ups
- Higher levels = faster speed = more challenging!

---

**Your game is now a complete Temple Run-style endless runner!** 🎮🏃‍♂️
