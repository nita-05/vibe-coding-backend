# Seasonal Collector Game - Setup Instructions

## 📁 Folder Structure

```
SeasonalCollectorGame/
├── ServerScriptService/
│   ├── EventManager.server.lua          ✅ Core event system
│   ├── CollectibleManager.server.lua    ✅ Collectible spawning
│   ├── PlayerDataManager.server.lua     ✅ Stats & upgrades
│   ├── LeaderboardManager.server.lua    ✅ Leaderboards
│   ├── NPCManager.server.lua            ✅ NPCs
│   ├── EnvironmentManager.server.lua    ✅ Environment effects
│   ├── UpgradeManager.server.lua        ✅ Upgrade purchases
│   └── GameManager.server.lua           ✅ Main manager
│
├── ReplicatedStorage/
│   └── Modules/
│       └── DataStoreManager.lua         ✅ Data persistence
│
└── StarterPlayer/
    └── StarterPlayerScripts/
        ├── MainUI.client.lua            ✅ Main game UI
        ├── ShopUI.client.lua            ✅ Shop interface
        ├── LeaderboardUI.client.lua     ✅ Leaderboard display
        ├── CollectionEffect.client.lua  ✅ Collection effects
        ├── NPCDialogUI.client.lua       ✅ NPC dialogs
        └── QuestUI.client.lua           ✅ Quest interface
```

## 🚀 Installation Steps

1. **Copy all files** to your Roblox Studio project
2. **Place scripts** in correct locations (see structure above)
3. **Ensure ReplicatedStorage/Modules folder exists**
4. **Test in Play mode**

## ✅ Systems Included

- ✅ Event System (Snow/Halloween/Festival switching)
- ✅ Collectible System (Rarity, Event-specific models)
- ✅ Player Progression (Stats, Upgrades, DataStore)
- ✅ Leaderboards (Event, Daily, All-time)
- ✅ NPCs (Guide, Shop, Quest)
- ✅ Environment Effects (Non-destructive overlays)
- ✅ UI Systems (Event status, Shop, Leaderboards)

## 🎮 How It Works

1. **EventManager** controls which event is active
2. **CollectibleManager** spawns event-specific collectibles
3. **PlayerDataManager** tracks stats and handles upgrades
4. **LeaderboardManager** maintains rankings
5. **NPCs** provide interaction points
6. **EnvironmentManager** applies visual effects

## 🔧 Configuration

All systems are configurable via CONFIG tables in each script.

## 📝 Notes

- Map is NOT modified (non-destructive)
- All effects are overlays
- Data persists via DataStore
- Server-authoritative (exploit-safe)
