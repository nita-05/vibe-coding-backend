# 🎮 Seasonal Collector Game

Complete Seasonal/Event-Based Collector Game for Roblox Studio.

## ✨ Features

- **Event System**: Switch between Snow, Halloween, and Festival events
- **Collectible System**: Rarity-based collectibles (Common, Rare, Epic, Legendary)
- **Player Progression**: Stats, upgrades, persistent data
- **Leaderboards**: Event, Daily, and All-time rankings
- **NPCs**: Event Guide, Shop Keeper, Quest Master
- **Environment Effects**: Non-destructive overlays per event
- **UI Systems**: Complete mobile-friendly interface
- **Monetization**: Fair gamepass system (no pay-to-win)

## 📋 Quick Start

1. Copy all files to your Roblox Studio project
2. Place scripts in correct locations (see SETUP_INSTRUCTIONS.md)
3. Test in Play mode
4. Configure gamepass IDs in GamepassManager.server.lua

## 🎯 Core Systems

### EventManager
- Controls event switching
- Manages lighting, skybox, effects
- Auto-switches events on timer

### CollectibleManager
- Spawns event-specific collectibles
- Rarity system with different points
- Auto-respawn system

### PlayerDataManager
- Tracks stats (points, collected, upgrades)
- Handles upgrade purchases
- DataStore persistence

### LeaderboardManager
- Event leaderboard (resets per event)
- Daily leaderboard (resets daily)
- All-time leaderboard (persistent)

## 🛠️ Configuration

All systems use CONFIG tables for easy customization.

## 📝 Notes

- **Non-destructive**: Map is never modified
- **Server-authoritative**: Exploit-safe
- **Modular**: Easy to extend
- **Production-ready**: Clean, commented code

## 🎨 Events

1. **Snow Event** (Default)
   - Snow particles
   - Cool lighting
   - Snow bubble collectibles

2. **Halloween Event**
   - Dark sky
   - Orange lighting
   - Spooky fog
   - Pumpkin collectibles

3. **Festival Event**
   - Colorful lights
   - Fireworks
   - Bright atmosphere
   - Festival orb collectibles

## 🚀 Ready to Deploy!

All systems are complete and ready for production use.
