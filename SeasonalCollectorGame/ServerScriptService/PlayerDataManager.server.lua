-- PlayerDataManager.server.lua
-- Manages player stats, progression, and upgrades
-- Place in ServerScriptService

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- ============================================
-- MODULES
-- ============================================
-- Ensure Modules folder exists
local modulesFolder = ReplicatedStorage:FindFirstChild("Modules")
if not modulesFolder then
	modulesFolder = Instance.new("Folder")
	modulesFolder.Name = "Modules"
	modulesFolder.Parent = ReplicatedStorage
end

-- Wait for DataStoreManager module
local dataStoreModule = modulesFolder:FindFirstChild("DataStoreManager") or modulesFolder:FindFirstChild("DataStoreManager.lua")
if not dataStoreModule then
	warn("⚠️ DataStoreManager module not found!")
	warn("   Please ensure DataStoreManager.lua is a ModuleScript in ReplicatedStorage/Modules")
	warn("   Using in-memory storage (data will not persist)")
	-- Use in-memory fallback instead of creating module (permission issue)
	dataStoreModule = nil
end

-- Use DataStoreManager if available, otherwise use in-memory fallback
local DataStoreManager
if dataStoreModule then
	DataStoreManager = require(dataStoreModule)
else
	-- In-memory fallback (no persistence)
	DataStoreManager = {
		SavePlayerData = function(player, data) 
			return true 
		end,
		LoadPlayerData = function(player) 
			return nil 
		end,
		SaveLeaderboard = function(type, data) 
			return true 
		end,
		LoadLeaderboard = function(type) 
			return nil 
		end,
	}
end

-- ============================================
-- REMOTE EVENTS
-- ============================================
local Events = ReplicatedStorage:FindFirstChild("RemoteEvents")
if not Events then
	Events = Instance.new("Folder")
	Events.Name = "RemoteEvents"
	Events.Parent = ReplicatedStorage
end

local function getOrCreateEvent(name)
	local event = Events:FindFirstChild(name)
	if not event then
		event = Instance.new("RemoteEvent")
		event.Name = name
		event.Parent = Events
	end
	return event
end

local UpdateStats = getOrCreateEvent("UpdateStats")
local UpgradePurchased = getOrCreateEvent("UpgradePurchased")
local LifeMessage = getOrCreateEvent("LifeMessage")

-- ============================================
-- WALLET CAPACITY
-- ============================================
local DEFAULT_WALLET_CAPACITY = 100
local FORCE_DEFAULT_WALLET_CAPACITY = true -- always set everyone to default (prevents old 1000 values)
local WALLET_FULL_MESSAGE_COOLDOWN_SECONDS = 2.0
local lastWalletFullMessageAt = {}

-- ============================================
-- DEFAULT PLAYER DATA
-- ============================================
local function deepCopy(tbl)
	local copy = {}
	for k, v in pairs(tbl) do
		if type(v) == "table" then
			copy[k] = deepCopy(v)
		else
			copy[k] = v
		end
	end
	return copy
end

local DEFAULT_DATA = {
	-- Stats
	eventPoints = 0,
	totalCollected = 0,
	collectionSpeed = 1.0, -- Multiplier
	magnetRadius = 0, -- Studs

	-- Leveling (NEW)
	level = 1,
	xp = 0,
	
	-- Coins & Vehicles (NEW)
	coins = 0,
	walletCapacity = DEFAULT_WALLET_CAPACITY, -- Max coins you can carry before depositing
	bankBalance = 0, -- Coins stored in bank
	ownedVehicles = {}, -- Table of vehicle names
	equippedVehicle = "", -- Currently equipped vehicle name (empty string, not nil)
	hasTwoWheeler = false, -- Track if player owns at least one two-wheeler
	inventory = {}, -- Purchased shop items
	
	-- Upgrades
	upgrades = {
		collectionSpeed = 0, -- Level
		magnetRadius = 0,
		eventMultiplier = 0,
	},
	
	-- Event stats (reset per event)
	currentEventPoints = 0,
	currentEventCollected = 0,
	
	-- All-time stats
	allTimePoints = 0,
	allTimeCollected = 0,
}

-- ============================================
-- UPGRADE CONFIGURATION
-- ============================================
local UPGRADE_CONFIG = {
	collectionSpeed = {
		cost = {100, 250, 500, 1000, 2000},
		effect = {1.2, 1.5, 2.0, 2.5, 3.0}, -- Multipliers
		maxLevel = 5,
	},
	
	magnetRadius = {
		cost = {150, 300, 600, 1200, 2500},
		effect = {5, 10, 15, 20, 30}, -- Studs
		maxLevel = 5,
	},
	
	eventMultiplier = {
		cost = {200, 500, 1000, 2000, 5000},
		effect = {1.1, 1.25, 1.5, 2.0, 3.0}, -- Multipliers
		maxLevel = 5,
	},
}

-- ============================================
-- PLAYER DATA STORAGE
-- ============================================
local playerData = {}

-- ============================================
-- LEVELING CONFIG
-- ============================================
local function xpRequiredForLevel(level: number)
	level = math.max(1, math.floor(tonumber(level) or 1))
	-- Smooth growth: L1->2 is easy, later levels take longer
	return 100 + ((level - 1) * 50) + math.floor(((level - 1) ^ 2) * 10)
end

local function ensureLevelingFields(data)
	if not data then return end
	data.level = math.max(1, math.floor(tonumber(data.level) or 1))
	data.xp = math.max(0, math.floor(tonumber(data.xp) or 0))
end

local function applyLevelUpRewards(player, data, levelsGained)
	-- Keep rewards safe and non-breaking: deposit small bonus straight into bank.
	-- This doesn't affect wallet capacity / upgrades, and reinforces banking.
	if not player or not player.Parent or not data then return end
	levelsGained = math.max(0, math.floor(tonumber(levelsGained) or 0))
	if levelsGained <= 0 then return end

	local bonusPerLevel = 10
	data.bankBalance = math.max(0, math.floor(tonumber(data.bankBalance) or 0)) + (bonusPerLevel * levelsGained)
	LifeMessage:FireClient(player, "⭐ Level Up! You're now Level " .. tostring(data.level) .. " (+" .. tostring(bonusPerLevel * levelsGained) .. " bank coins)")
end

local function addXP(player, amount)
	if not player or not player.Parent then return end

	local data = playerData[player]
	if not data then
		initializePlayer(player)
		data = playerData[player]
	end
	if not data then return end

	ensureLevelingFields(data)

	amount = math.floor(tonumber(amount) or 0)
	if amount <= 0 then
		return
	end

	data.xp += amount

	local levelsGained = 0
	while data.xp >= xpRequiredForLevel(data.level) do
		data.xp -= xpRequiredForLevel(data.level)
		data.level += 1
		levelsGained += 1
	end

	if levelsGained > 0 then
		applyLevelUpRewards(player, data, levelsGained)
	end

	-- Save + update client (UpdateStats already powers the HUD)
	DataStoreManager.SavePlayerData(player, data)
	UpdateStats:FireClient(player, data)
end

-- ============================================
-- INITIALIZE PLAYER
-- ============================================
local function initializePlayer(player)
	-- Try to load from DataStore
	local savedData = DataStoreManager.LoadPlayerData(player)
	
	if savedData then
		playerData[player] = savedData
		-- Reset event-specific stats
		playerData[player].currentEventPoints = 0
		playerData[player].currentEventCollected = 0
	else
		-- New player - use defaults
		playerData[player] = {}
		for key, value in pairs(DEFAULT_DATA) do
			playerData[player][key] = value
		end
	end

	-- Ensure new fields exist for older saves
	ensureLevelingFields(playerData[player])
	
	-- Ensure wallet capacity exists for older saves, and upgrade to new default if lower
	if FORCE_DEFAULT_WALLET_CAPACITY then
		playerData[player].walletCapacity = DEFAULT_WALLET_CAPACITY
	else
		if playerData[player].walletCapacity == nil or (tonumber(playerData[player].walletCapacity) or 0) < DEFAULT_WALLET_CAPACITY then
			playerData[player].walletCapacity = DEFAULT_WALLET_CAPACITY
		end
	end
	
	-- Calculate current stats from upgrades
	local data = playerData[player]
	local speedLevel = data.upgrades.collectionSpeed
	local magnetLevel = data.upgrades.magnetRadius
	local multiplierLevel = data.upgrades.eventMultiplier
	
	data.collectionSpeed = UPGRADE_CONFIG.collectionSpeed.effect[speedLevel + 1] or 1.0
	data.magnetRadius = UPGRADE_CONFIG.magnetRadius.effect[magnetLevel + 1] or 0
	
	-- Send initial data to client
	UpdateStats:FireClient(player, data)
	
	print("✅ Initialized player data for " .. player.Name)
end

-- ============================================
-- ADD POINTS
-- ============================================
local function addPoints(player, points, rarity)
	local data = playerData[player]
	if not data then
		initializePlayer(player)
		data = playerData[player]
	end
	
	-- Apply event multiplier
	local multiplierLevel = data.upgrades.eventMultiplier
	local multiplier = UPGRADE_CONFIG.eventMultiplier.effect[multiplierLevel + 1] or 1.0
	points = math.floor(points * multiplier)
	
	-- Apply gamepass multiplier (Double Points)
	if _G.GamepassManager and _G.GamepassManager.PlayerOwnsGamepass(player, "DoublePoints") then
		points = points * 2
	end
	
	-- Add points
	data.eventPoints = data.eventPoints + points
	data.currentEventPoints = data.currentEventPoints + points
	data.allTimePoints = data.allTimePoints + points
	data.totalCollected = data.totalCollected + 1
	data.currentEventCollected = data.currentEventCollected + 1
	data.allTimeCollected = data.allTimeCollected + 1
	
	-- Update client
	UpdateStats:FireClient(player, data)
	
	-- Update leaderboards
	if _G.LeaderboardManager then
		_G.LeaderboardManager.UpdatePlayerScore(player, data.currentEventPoints, "Event")
		_G.LeaderboardManager.UpdatePlayerScore(player, points, "Daily")
		_G.LeaderboardManager.UpdatePlayerScore(player, points, "AllTime")
	end
	
	return points
end

-- ============================================
-- PURCHASE UPGRADE
-- ============================================
local function purchaseUpgrade(player, upgradeType)
	local data = playerData[player]
	if not data then
		initializePlayer(player)
		data = playerData[player]
	end
	
	local config = UPGRADE_CONFIG[upgradeType]
	if not config then
		return false, "Invalid upgrade type"
	end
	
	local currentLevel = data.upgrades[upgradeType] or 0
	if currentLevel >= config.maxLevel then
		return false, "Upgrade already at max level"
	end
	
	local cost = config.cost[currentLevel + 1]
	if data.eventPoints < cost then
		return false, "Not enough points"
	end
	
	-- Purchase
	data.eventPoints = data.eventPoints - cost
	data.upgrades[upgradeType] = currentLevel + 1
	
	-- Update stats
	if upgradeType == "collectionSpeed" then
		data.collectionSpeed = config.effect[currentLevel + 1]
	elseif upgradeType == "magnetRadius" then
		data.magnetRadius = config.effect[currentLevel + 1]
	end
	
	-- Save data
	DataStoreManager.SavePlayerData(player, data)
	
	-- Notify client
	UpdateStats:FireClient(player, data)
	UpgradePurchased:FireClient(player, upgradeType, currentLevel + 1)
	
	print("✅ " .. player.Name .. " purchased " .. upgradeType .. " level " .. (currentLevel + 1))
	
	return true, "Upgrade purchased!"
end

-- ============================================
-- COIN FUNCTIONS (NEW)
-- ============================================
local function addCoins(player, amount)
	if not player or not player.Parent then return 0 end
	
	local data = playerData[player]
	if not data then
		initializePlayer(player)
		data = playerData[player]
	end
	
	-- Apply gamepass multiplier if applicable
	if _G.GamepassManager then
		local multiplier = _G.GamepassManager.GetCoinMultiplier and _G.GamepassManager.GetCoinMultiplier(player) or 1.0
		amount = math.floor(amount * multiplier)
	end
	
	-- Apply event multiplier
	if _G.EventManager then
		local eventMultiplier = _G.EventManager.GetCoinMultiplier and _G.EventManager.GetCoinMultiplier() or 1.0
		amount = math.floor(amount * eventMultiplier)
	end

	amount = math.floor(tonumber(amount) or 0)
	if amount <= 0 then
		return 0
	end

	-- Wallet capacity (allow overflow to bank instead of blocking pickup)
	local capacity = math.floor(tonumber(data.walletCapacity) or DEFAULT_WALLET_CAPACITY)
	if capacity <= 0 then
		capacity = DEFAULT_WALLET_CAPACITY
		data.walletCapacity = capacity
	end

	local current = math.floor(tonumber(data.coins) or 0)
	local space = math.max(0, capacity - current)
	local toWallet = math.min(space, amount)
	local overflow = amount - toWallet

	if toWallet > 0 then
		data.coins = current + toWallet
	else
		data.coins = current
	end

	if overflow > 0 then
		data.bankBalance = math.floor(tonumber(data.bankBalance) or 0) + overflow

		-- Optional: tell the player overflow went to bank (throttled)
		local now = os.clock()
		local last = lastWalletFullMessageAt[player]
		if not last or (now - last) >= WALLET_FULL_MESSAGE_COOLDOWN_SECONDS then
			lastWalletFullMessageAt[player] = now
			LifeMessage:FireClient(player, "Wallet full — +" .. tostring(overflow) .. " sent to bank.")
		end
	end

	-- XP for coins collected (wallet + bank overflow)
	addXP(player, amount)
	
	-- Update leaderboards
	if _G.LeaderboardManager then
		_G.LeaderboardManager.UpdatePlayerScore(player, data.coins, "Coins")
	end
	
	-- Save data
	DataStoreManager.SavePlayerData(player, data)
	
	-- Notify client
	UpdateStats:FireClient(player, data)
	
	return amount
end

local function resetPlayerDataToDefaults(player: Player)
	if not player or not player.Parent then return false end

	playerData[player] = deepCopy(DEFAULT_DATA)
	ensureLevelingFields(playerData[player])

	-- Enforce default wallet capacity so restarts are predictable
	playerData[player].walletCapacity = DEFAULT_WALLET_CAPACITY

	-- Clear wallet-full message throttling for this run
	lastWalletFullMessageAt[player] = nil

	DataStoreManager.SavePlayerData(player, playerData[player])
	UpdateStats:FireClient(player, playerData[player])

	return true
end

local function spendCoins(player, amount)
	if not player or not player.Parent then return false end
	
	local data = playerData[player]
	if not data then return false end
	
	if (data.coins or 0) < amount then
		return false
	end
	
	data.coins = data.coins - amount
	
	-- Update map if MapManager exists
	if _G.MapManager and _G.MapManager.UpdatePlayerCoins then
		_G.MapManager.UpdatePlayerCoins(player, data.coins)
	end
	
	-- Save data
	DataStoreManager.SavePlayerData(player, data)
	
	-- Notify client
	UpdateStats:FireClient(player, data)
	
	return true
end

-- ============================================
-- VEHICLE FUNCTIONS (NEW)
-- ============================================
local function purchaseVehicle(player, vehicleName)
	if not player or not player.Parent then return false, "Player not found" end
	
	-- Get vehicle config
	local VehicleConfig = require(ReplicatedStorage:WaitForChild("Modules"):WaitForChild("VehicleConfig"))
	local vehicleData = VehicleConfig.GetVehicle(vehicleName)
	
	if not vehicleData then
		return false, "Vehicle not found"
	end
	
	-- Get player data
	local data = playerData[player]
	if not data then
		initializePlayer(player)
		data = playerData[player]
	end
	
	-- Check if already owned
	if data.ownedVehicles and table.find(data.ownedVehicles, vehicleName) then
		return false, "Vehicle already owned"
	end
	
	-- Check unlock requirements for cars
	if vehicleData.type == "Car" then
		if not data.hasTwoWheeler then
			return false, "You must own a two-wheeler before buying cars!"
		end
	end
	
	-- Check event availability
	local currentEvent = _G.EventManager and _G.EventManager.GetCurrentEvent() or "Snow"
	if vehicleData.eventExclusive and vehicleData.eventExclusive ~= currentEvent then
		return false, "This vehicle is only available during " .. vehicleData.eventExclusive .. " events"
	end
	
	-- Check price
	local price = vehicleData.price
	if (data.coins or 0) < price then
		return false, "Not enough coins! Need " .. price .. " coins"
	end
	
	-- Purchase
	if not spendCoins(player, price) then
		return false, "Failed to purchase vehicle"
	end
	
	-- Add to owned vehicles
	if not data.ownedVehicles then
		data.ownedVehicles = {}
	end
	table.insert(data.ownedVehicles, vehicleName)
	
	-- Update hasTwoWheeler flag
	if vehicleData.type == "TwoWheeler" then
		data.hasTwoWheeler = true
	end
	
	-- Save data
	DataStoreManager.SavePlayerData(player, data)
	UpdateStats:FireClient(player, data)
	
	print("✅ " .. player.Name .. " purchased vehicle: " .. vehicleName)
	
	return true, "Vehicle purchased!"
end

local function equipVehicle(player, vehicleName)
	if not player or not player.Parent then return false, "Player not found" end
	
	local data = playerData[player]
	if not data then
		initializePlayer(player)
		data = playerData[player]
	end
	
	-- Check if vehicle is owned
	if not data.ownedVehicles or not table.find(data.ownedVehicles, vehicleName) then
		return false, "Vehicle not owned"
	end
	
	-- Equip vehicle
	data.equippedVehicle = vehicleName
	
	-- Save data
	DataStoreManager.SavePlayerData(player, data)
	UpdateStats:FireClient(player, data)
	
	-- Notify VehicleService to spawn vehicle
	if _G.VehicleService then
		_G.VehicleService.SpawnPlayerVehicle(player)
	end
	
	print("✅ " .. player.Name .. " equipped vehicle: " .. vehicleName)
	
	return true, "Vehicle equipped!"
end

-- ============================================
-- RESET EVENT STATS
-- ============================================
local function resetEventStats(player)
	local data = playerData[player]
	if data then
		data.currentEventPoints = 0
		data.currentEventCollected = 0
		UpdateStats:FireClient(player, data)
	end
end

-- ============================================
-- SAVE DATA ON PLAYER LEAVE
-- ============================================
Players.PlayerRemoving:Connect(function(player)
	local data = playerData[player]
	if data then
		DataStoreManager.SavePlayerData(player, data)
		playerData[player] = nil
	end
end)

-- Auto-save every 30 seconds
spawn(function()
	while true do
		wait(30)
		for player, data in pairs(playerData) do
			if player and player.Parent then
				DataStoreManager.SavePlayerData(player, data)
			end
		end
	end
end)

-- ============================================
-- INITIALIZATION
-- ============================================
Players.PlayerAdded:Connect(function(player)
	initializePlayer(player)
end)

-- ============================================
-- EXPORT API
-- ============================================
_G.PlayerDataManager = {
	InitializePlayer = initializePlayer,
	AddPoints = addPoints,
	PurchaseUpgrade = purchaseUpgrade,
	AddCoins = addCoins,
	SpendCoins = spendCoins,
	ResetPlayerDataToDefaults = resetPlayerDataToDefaults,
	PurchaseVehicle = purchaseVehicle,
	EquipVehicle = equipVehicle,
	AddXP = addXP,
	GetXPForNextLevel = function(player)
		local data = playerData[player]
		if not data then return 0 end
		ensureLevelingFields(data)
		return xpRequiredForLevel(data.level)
	end,
	GetPlayerData = function(player)
		return playerData[player]
	end,
	ResetEventStats = resetEventStats,
	GetUpgradeConfig = function()
		return UPGRADE_CONFIG
	end,
}

print("✅ Player Data Manager initialized")
if dataStoreModule then
	print("   - DataStore persistence enabled")
else
	warn("   ⚠️ Using in-memory storage (data won't persist)")
	warn("   ⚠️ Set DataStoreManager.lua as ModuleScript for persistence")
end
print("   - Upgrades: Collection Speed, Magnet Radius, Event Multiplier")
print("   - Coins & Vehicles system ready")
