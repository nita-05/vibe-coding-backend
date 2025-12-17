-- CoinService.server.lua
-- Manages coin spawning, collection, and event integration
-- EXTENDS existing collectible framework - replaces bubbles with coins
-- Place in ServerScriptService

local Workspace = game:GetService("Workspace")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local SoundService = game:GetService("SoundService")

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

local CollectCoin = getOrCreateEvent("CollectCoin")
local ShowCoinEffect = getOrCreateEvent("ShowCoinEffect")

-- ============================================
-- CONFIGURATION
-- ============================================
local CONFIG = {
	-- Spawning
	MaxCoins = 50,
	BaseSpawnRate = 3, -- seconds
	SpawnRadius = 200,
	
	-- Coin tiers (replaces rarity system)
	CoinTiers = {
		Bronze = {
			chance = 0.60,    -- 60%
			value = 1,
			color = Color3.fromRGB(205, 127, 50), -- Bronze
			material = Enum.Material.Metal,
			size = {2, 3},
		},
		Silver = {
			chance = 0.30,    -- 30%
			value = 5,
			color = Color3.fromRGB(192, 192, 192), -- Silver
			material = Enum.Material.Metal,
			size = {3, 4},
		},
		Gold = {
			chance = 0.08,    -- 8%
			value = 20,
			color = Color3.fromRGB(255, 215, 0), -- Gold
			material = Enum.Material.Metal,
			size = {4, 5},
		},
		Event = {
			chance = 0.02,    -- 2%
			value = 50,
			color = Color3.fromRGB(255, 100, 255), -- Event purple/pink
			material = Enum.Material.Neon,
			size = {5, 6},
		},
	},
	
	-- Respawn time
	RespawnTime = 5, -- seconds
}

-- ============================================
-- COIN FOLDER
-- ============================================
local coinFolder = Instance.new("Folder")
coinFolder.Name = "Coins"
coinFolder.Parent = Workspace

-- ============================================
-- SPAWN POINTS
-- ============================================
local function getSpawnPoints()
	local spawnPoints = {}
	
	-- Find spawn point folder (if exists)
	local spawnFolder = Workspace:FindFirstChild("CoinSpawnPoints")
	if spawnFolder then
		for _, point in ipairs(spawnFolder:GetChildren()) do
			if point:IsA("BasePart") then
				table.insert(spawnPoints, point)
			end
		end
	end
	
	-- Fallback: Use existing spawn points or generate on roads
	if #spawnPoints == 0 then
		-- Try to find roads, intersections, or use default spawns
		for _, part in ipairs(Workspace:GetDescendants()) do
			if part:IsA("BasePart") and part.Name:find("Road") or part.Name:find("Street") then
				table.insert(spawnPoints, part)
			end
		end
	end
	
	-- Default spawns if nothing found
	if #spawnPoints == 0 then
		for i = 1, 20 do
			local spawn = Instance.new("Part")
			spawn.Name = "CoinSpawn_" .. i
			spawn.Size = Vector3.new(1, 1, 1)
			spawn.Transparency = 1
			spawn.Anchored = true
			spawn.CanCollide = false
			spawn.Position = Vector3.new(
				math.random(-100, 100),
				5,
				math.random(-100, 100)
			)
			spawn.Parent = Workspace
			table.insert(spawnPoints, spawn)
		end
	end
	
	return spawnPoints
end

-- ============================================
-- GET RANDOM COIN TIER
-- ============================================
local function getRandomCoinTier(eventName)
	-- Event coins have higher chance during events
	local eventMultiplier = 1.0
	if _G.EventManager then
		local currentEvent = _G.EventManager.GetCurrentEvent()
		if currentEvent and currentEvent ~= "Snow" then
			eventMultiplier = 1.5 -- 50% more event coins during events
		end
	end
	
	local rand = math.random()
	local cumulative = 0
	
	for tierName, tierData in pairs(CONFIG.CoinTiers) do
		local chance = tierData.chance
		if tierName == "Event" then
			chance = chance * eventMultiplier
		end
		cumulative = cumulative + chance
		if rand <= cumulative then
			return tierName, tierData
		end
	end
	
	-- Default to Bronze
	return "Bronze", CONFIG.CoinTiers.Bronze
end

-- ============================================
-- CREATE COIN
-- ============================================
local function createCoin(position, eventName)
	eventName = eventName or (_G.EventManager and _G.EventManager.GetCurrentEvent()) or "Snow"
	
	local tierName, tierData = getRandomCoinTier(eventName)
	
	-- Apply event bonus to coin value
	local coinValue = tierData.value
	if _G.EventManager then
		local eventMultiplier = _G.EventManager.GetCoinMultiplier and _G.EventManager.GetCoinMultiplier() or 1.0
		coinValue = math.floor(coinValue * eventMultiplier)
	end
	
	local size = math.random(tierData.size[1], tierData.size[2])
	
	-- Create coin part (cylinder shape)
	local coin = Instance.new("Part")
	coin.Name = "Coin"
	coin.Size = Vector3.new(0.2, size, size)
	coin.Shape = Enum.PartType.Cylinder
	coin.Material = tierData.material
	coin.BrickColor = BrickColor.new(tierData.color)
	coin.Transparency = 0.1
	coin.Reflectance = 0.4
	coin.Anchored = true
	coin.CanCollide = false
	coin.Position = position
	coin.Parent = coinFolder
	
	-- Store coin data
	local coinValueObj = Instance.new("IntValue")
	coinValueObj.Name = "CoinValue"
	coinValueObj.Value = coinValue
	coinValueObj.Parent = coin
	
	local tierValue = Instance.new("StringValue")
	tierValue.Name = "Tier"
	tierValue.Value = tierName
	tierValue.Parent = coin
	
	-- Add glow
	local light = Instance.new("PointLight")
	light.Color = tierData.color
	light.Brightness = 1.2
	light.Range = size * 2
	light.Parent = coin
	
	-- Floating animation
	local floatTween = TweenService:Create(
		coin,
		TweenInfo.new(
			2 + math.random(),
			Enum.EasingStyle.Sine,
			Enum.EasingDirection.InOut,
			-1,
			true
		),
		{Position = position + Vector3.new(0, 2, 0)}
	)
	floatTween:Play()
	
	-- Rotation (coin spinning)
	local rotationTween = TweenService:Create(
		coin,
		TweenInfo.new(
			2,
			Enum.EasingStyle.Linear,
			Enum.EasingDirection.InOut,
			-1
		),
		{CFrame = coin.CFrame * CFrame.Angles(0, math.rad(360), 0)}
	)
	rotationTween:Play()
	
	-- Shimmer particles
	local attachment = Instance.new("Attachment")
	attachment.Parent = coin
	
	local particles = Instance.new("ParticleEmitter")
	particles.Parent = attachment
	particles.Texture = "rbxasset://textures/particles/sparkles.png"
	particles.Color = ColorSequence.new(tierData.color)
	particles.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0),
		NumberSequenceKeypoint.new(1, 1)
	})
	particles.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.5),
		NumberSequenceKeypoint.new(1, 0)
	})
	particles.Lifetime = NumberRange.new(1, 2)
	particles.Rate = 15
	particles.Speed = NumberRange.new(2, 4)
	particles.SpreadAngle = Vector2.new(45, 45)
	
	-- Touch detection with magnet radius support
	local collected = false
	local collectionConnection = nil
	
	-- Function to collect coin (prevents duplicate collection)
	local function collectCoin(player)
		if collected then return end

		-- Award coins (respects wallet capacity)
		local gained = coinValue
		if _G.PlayerDataManager and _G.PlayerDataManager.AddCoins then
			gained = _G.PlayerDataManager.AddCoins(player, coinValue) or 0
		else
			-- Fallback: Store coins temporarily
			if not _G.CoinStorage then _G.CoinStorage = {} end
			_G.CoinStorage[player] = (_G.CoinStorage[player] or 0) + coinValue
			gained = coinValue
		end

		-- If wallet is full, do NOT consume the coin
		if gained <= 0 then
			return
		end

		collected = true
							
		-- Disconnect touch event immediately
		if collectionConnection then
			collectionConnection:Disconnect()
			collectionConnection = nil
		end
				
				-- Show effect
				ShowCoinEffect:FireClient(player, gained, tierName, coin.Position)
				
		-- CoinNotification popups were removed (too noisy for current design).
		
		-- Play coin sound (use valid Roblox sound)
				local sound = Instance.new("Sound")
		sound.SoundId = "rbxasset://sounds/impact_water.wav" -- Valid Roblox sound
		sound.Volume = 0.4
				sound.Parent = coin
				sound:Play()
				sound.Ended:Connect(function()
					sound:Destroy()
				end)
				
				-- Collection animation
				TweenService:Create(
					coin,
					TweenInfo.new(0.3, Enum.EasingStyle.Back),
					{Size = coin.Size * 1.5, Transparency = 1}
				):Play()
				
		-- Stop all animations and particles immediately
		for _, child in ipairs(coin:GetDescendants()) do
			if child:IsA("Tween") then
				child:Cancel()
			elseif child:IsA("ParticleEmitter") then
				child.Enabled = false
			end
		end
		
		-- Destroy coin immediately (no wait)
		if coin and coin.Parent then
				coin:Destroy()
		end
				
				-- Respawn after delay
				spawn(function()
					wait(CONFIG.RespawnTime)
					if #coinFolder:GetChildren() < CONFIG.MaxCoins then
						local spawnPoints = getSpawnPoints()
						if #spawnPoints > 0 then
							local spawnPoint = spawnPoints[math.random(1, #spawnPoints)]
							local newPos = spawnPoint.Position + Vector3.new(
								math.random(-10, 10),
								3,
								math.random(-10, 10)
							)
							createCoin(newPos, eventName)
						end
					end
				end)
	end
	
	-- Check proximity (magnet effect)
	spawn(function()
		while coin and coin.Parent and not collected do
			wait(0.1)
			
			for _, player in ipairs(Players:GetPlayers()) do
				if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
					local playerData = _G.PlayerDataManager and _G.PlayerDataManager.GetPlayerData(player)
					if playerData and playerData.magnetRadius > 0 then
						local distance = (player.Character.HumanoidRootPart.Position - coin.Position).Magnitude
						if distance <= playerData.magnetRadius then
							-- Auto-collect via magnet
							collectCoin(player)
							return
						end
					end
				end
			end
		end
	end)
	
	-- Touch event
	collectionConnection = coin.Touched:Connect(function(hit)
		if collected then return end
		
		local humanoid = hit.Parent:FindFirstChildOfClass("Humanoid")
		if humanoid then
			local player = Players:GetPlayerFromCharacter(hit.Parent)
			if player then
				collectCoin(player)
			end
		end
	end)
	
	return coin
end

-- ============================================
-- SPAWNING SYSTEM
-- ============================================
local function spawnCoins()
	local spawnPoints = getSpawnPoints()
	if #spawnPoints == 0 then return end
	
	local currentEvent = _G.EventManager and _G.EventManager.GetCurrentEvent() or "Snow"
	
	while true do
		wait(CONFIG.BaseSpawnRate)
		
		local currentCount = #coinFolder:GetChildren()
		if currentCount < CONFIG.MaxCoins then
			local spawnPoint = spawnPoints[math.random(1, #spawnPoints)]
			local position = spawnPoint.Position + Vector3.new(
				math.random(-10, 10),
				3,
				math.random(-10, 10)
			)
			
			createCoin(position, currentEvent)
		end
	end
end

-- ============================================
-- EVENT SWITCHING
-- ============================================
local function switchEvent(newEvent)
	-- Clear existing coins
	for _, coin in ipairs(coinFolder:GetChildren()) do
		coin:Destroy()
	end
	
	-- Spawn new event coins
	spawn(function()
		wait(1)
		local spawnPoints = getSpawnPoints()
		for i = 1, math.min(20, CONFIG.MaxCoins) do
			if #spawnPoints > 0 then
				local spawnPoint = spawnPoints[math.random(1, #spawnPoints)]
				local position = spawnPoint.Position + Vector3.new(
					math.random(-10, 10),
					3,
					math.random(-10, 10)
				)
				createCoin(position, newEvent)
				wait(0.2)
			end
		end
	end)
end

-- ============================================
-- INITIALIZATION
-- ============================================
spawn(function()
	wait(2) -- Wait for EventManager and PlayerDataManager
	spawnCoins()
end)

-- ============================================
-- EXPORT API
-- ============================================
_G.CoinService = {
	SwitchEvent = switchEvent,
	GetConfig = function()
		return CONFIG
	end,
	GetCoinFolder = function()
		return coinFolder
	end,
}

print("✅ Coin Service initialized")
print("   - Max coins: " .. CONFIG.MaxCoins)
print("   - Coin tiers: Bronze (+1), Silver (+5), Gold (+20), Event (+50)")
