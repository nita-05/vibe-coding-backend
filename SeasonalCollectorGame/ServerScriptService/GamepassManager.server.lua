-- GamepassManager.server.lua
-- Handles gamepass purchases (fair monetization)
-- Place in ServerScriptService

local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- ============================================
-- GAMEPASS IDs (Set these in Roblox Studio)
-- ============================================
local GAMEPASS_IDS = {
	DoublePoints = 0, -- Replace with actual gamepass ID
	MagnetBoost = 0,  -- Replace with actual gamepass ID
	EventPass = 0,    -- Replace with actual gamepass ID (cosmetics only)
}

-- ============================================
-- PLAYER GAMEPASSES
-- ============================================
local playerGamepasses = {} -- [player] = {DoublePoints = true, ...}

-- ============================================
-- CHECK GAMEPASS
-- ============================================
local function playerOwnsGamepass(player, gamepassName)
	return playerGamepasses[player] and playerGamepasses[player][gamepassName] or false
end

-- ============================================
-- GAMEPASS EFFECTS
-- ============================================
local function applyGamepassEffects(player)
	local gamepasses = playerGamepasses[player]
	if not gamepasses then return end
	
	-- Double Points effect is handled in PlayerDataManager
	-- Magnet Boost effect is handled in CollectibleManager
	-- Event Pass is cosmetic only (can add special effects)
end

-- ============================================
-- PURCHASE HANDLER
-- ============================================
MarketplaceService.ProcessReceipt = function(receiptInfo)
	local playerId = receiptInfo.PlayerId
	local productId = receiptInfo.ProductId
	local player = Players:GetPlayerByUserId(playerId)
	
	if not player then
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end
	
	-- Check which gamepass
	for gamepassName, gamepassId in pairs(GAMEPASS_IDS) do
		if productId == gamepassId then
			-- Grant gamepass
			if not playerGamepasses[player] then
				playerGamepasses[player] = {}
			end
			playerGamepasses[player][gamepassName] = true
			
			applyGamepassEffects(player)
			
			print("✅ " .. player.Name .. " purchased " .. gamepassName)
			return Enum.ProductPurchaseDecision.PurchaseGranted
		end
	end
	
	return Enum.ProductPurchaseDecision.NotProcessedYet
end

-- ============================================
-- CHECK ON JOIN
-- ============================================
Players.PlayerAdded:Connect(function(player)
	-- Check owned gamepasses
	for gamepassName, gamepassId in pairs(GAMEPASS_IDS) do
		if gamepassId > 0 then
			local success, owns = pcall(function()
				return MarketplaceService:UserOwnsGamePassAsync(player.UserId, gamepassId)
			end)
			
			if success and owns then
				if not playerGamepasses[player] then
					playerGamepasses[player] = {}
				end
				playerGamepasses[player][gamepassName] = true
				applyGamepassEffects(player)
			end
		end
	end
end)

Players.PlayerRemoving:Connect(function(player)
	playerGamepasses[player] = nil
end)

-- ============================================
-- EXPORT API
-- ============================================
_G.GamepassManager = {
	PlayerOwnsGamepass = playerOwnsGamepass,
	GetPlayerGamepasses = function(player)
		return playerGamepasses[player] or {}
	end,
}

print("✅ Gamepass Manager initialized")
print("   - Double Points gamepass")
print("   - Magnet Boost gamepass")
print("   - Event Pass (cosmetics)")
