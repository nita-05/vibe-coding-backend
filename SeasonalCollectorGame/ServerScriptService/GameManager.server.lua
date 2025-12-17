-- GameManager.server.lua
-- Main game manager - initializes all systems
-- Place in ServerScriptService

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

-- ============================================
-- INITIALIZATION
-- ============================================
print("🎮 Seasonal Collector Game - Initializing...")

-- Wait for SetupManager to create folders
wait(0.5)

-- Wait for all systems to load
wait(3) -- Give more time for systems to initialize (VehicleService needs VehicleConfig)

-- Check systems
local systems = {
	"EventManager",
	"CollectibleManager", -- Original collectible system (can coexist)
	"CoinService", -- NEW: Coin system
	"VehicleService", -- NEW: Vehicle showroom system (replaces CarService)
	"PlayerDataManager",
	"LeaderboardManager",
	"NPCManager",
	"EnvironmentManager",
	"WelcomeGuide", -- NEW: Welcome message system
	"MapManager", -- NEW: Map system for vehicle locations
}

for _, systemName in ipairs(systems) do
	-- Wait a bit and check again
	wait(0.1)
	if _G[systemName] then
		print("   ✅ " .. systemName .. " loaded")
	else
		warn("   ⚠️ " .. systemName .. " not found (may still be initializing)")
	end
end

-- ============================================
-- PLAYER JOIN
-- ============================================
Players.PlayerAdded:Connect(function(player)
	print("👤 Player joined: " .. player.Name)
	
	player.CharacterAdded:Connect(function(character)
		wait(1)
		print("   ✅ Character loaded for " .. player.Name)
	end)
end)

print("✅ Game Manager initialized")
print("   - All systems ready")
print("   - Game is ready to play!")
