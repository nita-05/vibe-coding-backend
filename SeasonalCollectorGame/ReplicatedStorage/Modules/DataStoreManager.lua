-- DataStoreManager.lua
-- Handles persistent data storage
-- Place in ReplicatedStorage/Modules

local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")

-- ============================================
-- DATASTORES
-- ============================================
local playerDataStore = DataStoreService:GetDataStore("PlayerData")
local leaderboardDataStore = DataStoreService:GetDataStore("Leaderboards")

-- ============================================
-- PLAYER DATA FUNCTIONS
-- ============================================
local function savePlayerData(player, data)
	local success, err = pcall(function()
		playerDataStore:SetAsync(player.UserId, data)
	end)
	
	if not success then
		warn("⚠️ Failed to save data for " .. player.Name .. ": " .. tostring(err))
		return false
	end
	
	return true
end

local function loadPlayerData(player)
	local success, data = pcall(function()
		return playerDataStore:GetAsync(player.UserId)
	end)
	
	if not success then
		warn("⚠️ Failed to load data for " .. player.Name)
		return nil
	end
	
	return data
end

-- ============================================
-- LEADERBOARD FUNCTIONS
-- ============================================
local function saveLeaderboard(leaderboardType, data)
	local success, err = pcall(function()
		leaderboardDataStore:SetAsync(leaderboardType, data)
	end)
	
	if not success then
		warn("⚠️ Failed to save leaderboard: " .. tostring(err))
		return false
	end
	
	return true
end

local function loadLeaderboard(leaderboardType)
	local success, data = pcall(function()
		return leaderboardDataStore:GetAsync(leaderboardType)
	end)
	
	if not success then
		return nil
	end
	
	return data
end

-- ============================================
-- EXPORT
-- ============================================
return {
	SavePlayerData = savePlayerData,
	LoadPlayerData = loadPlayerData,
	SaveLeaderboard = saveLeaderboard,
	LoadLeaderboard = loadLeaderboard,
}
