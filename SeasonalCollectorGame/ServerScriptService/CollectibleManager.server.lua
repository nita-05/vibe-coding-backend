-- CollectibleManager.server.lua
-- Manages collectible spawning, rarity, and event-specific models
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

local CollectItem = getOrCreateEvent("CollectItem")
local ShowCollectionEffect = getOrCreateEvent("ShowCollectionEffect")

-- ============================================
-- CONFIGURATION
-- ============================================
local CONFIG = {
	-- Spawning
	MaxCollectibles = 50,
	BaseSpawnRate = 3, -- seconds
	SpawnRadius = 200,
	
	-- Rarity system
	RarityChances = {
		Common = 0.70,    -- 70%
		Rare = 0.20,      -- 20%
		Epic = 0.08,      -- 8%
		Legendary = 0.02, -- 2%
	},
	
	-- Points by rarity
	RarityPoints = {
		Common = {10, 20},
		Rare = {30, 50},
		Epic = {75, 100},
		Legendary = {150, 200},
	},
	
	-- Respawn time
	RespawnTime = 5, -- seconds
}

-- ============================================
-- EVENT-SPECIFIC COLLECTIBLE MODELS
-- ============================================
local COLLECTIBLE_MODELS = {
	Snow = {
		Common = {
			material = Enum.Material.Snow,
			color = Color3.fromRGB(240, 248, 255),
			size = {3, 5},
		},
		Rare = {
			material = Enum.Material.Neon,
			color = Color3.fromRGB(173, 216, 230),
			size = {5, 7},
		},
		Epic = {
			material = Enum.Material.Neon,
			color = Color3.fromRGB(100, 200, 255),
			size = {7, 10},
		},
		Legendary = {
			material = Enum.Material.Neon,
			color = Color3.fromRGB(255, 255, 255),
			size = {10, 15},
		},
	},
	
	Halloween = {
		Common = {
			material = Enum.Material.Plastic,
			color = Color3.fromRGB(255, 140, 0), -- Orange pumpkin
			size = {3, 5},
		},
		Rare = {
			material = Enum.Material.Neon,
			color = Color3.fromRGB(255, 100, 0),
			size = {5, 7},
		},
		Epic = {
			material = Enum.Material.Neon,
			color = Color3.fromRGB(200, 0, 0), -- Red
			size = {7, 10},
		},
		Legendary = {
			material = Enum.Material.Neon,
			color = Color3.fromRGB(255, 215, 0), -- Gold
			size = {10, 15},
		},
	},
	
	Festival = {
		Common = {
			material = Enum.Material.Neon,
			color = Color3.fromRGB(255, 200, 100),
			size = {3, 5},
		},
		Rare = {
			material = Enum.Material.Neon,
			color = Color3.fromRGB(100, 200, 255),
			size = {5, 7},
		},
		Epic = {
			material = Enum.Material.Neon,
			color = Color3.fromRGB(255, 100, 200),
			size = {7, 10},
		},
		Legendary = {
			material = Enum.Material.Neon,
			color = Color3.fromRGB(255, 255, 0), -- Bright yellow
			size = {10, 15},
		},
	},
}

-- ============================================
-- COLLECTIBLE FOLDER
-- ============================================
local collectibleFolder = Instance.new("Folder")
collectibleFolder.Name = "Collectibles"
collectibleFolder.Parent = Workspace

-- ============================================
-- SPAWN POINTS
-- ============================================
local function getSpawnPoints()
	local spawnPoints = {}
	
	-- Find roads (parts with "Road" in name or dark grey color)
	for _, part in ipairs(Workspace:GetDescendants()) do
		if part:IsA("BasePart") and part.Name:find("Road") then
			table.insert(spawnPoints, part)
		end
	end
	
	-- Find houses (parts with "House" or "Building" in name)
	for _, part in ipairs(Workspace:GetDescendants()) do
		if part:IsA("BasePart") and (part.Name:find("House") or part.Name:find("Building")) then
			table.insert(spawnPoints, part)
		end
	end
	
	-- Find trees
	for _, part in ipairs(Workspace:GetDescendants()) do
		if part:IsA("BasePart") and part.Name:find("Tree") then
			table.insert(spawnPoints, part)
		end
	end
	
	-- If no specific spawn points found, use baseplate/ground
	if #spawnPoints == 0 then
		local baseplate = Workspace:FindFirstChild("Baseplate")
		if baseplate then
			table.insert(spawnPoints, baseplate)
		end
	end
	
	return spawnPoints
end

-- ============================================
-- RARITY SYSTEM
-- ============================================
local function getRandomRarity()
	local rand = math.random()
	local cumulative = 0
	
	for rarity, chance in pairs(CONFIG.RarityChances) do
		cumulative = cumulative + chance
		if rand <= cumulative then
			return rarity
		end
	end
	
	return "Common"
end

-- ============================================
-- CREATE COLLECTIBLE
-- ============================================
local function createCollectible(position, eventName, rarity)
	eventName = eventName or _G.EventManager and _G.EventManager.GetCurrentEvent() or "Snow"
	rarity = rarity or getRandomRarity()
	
	local model = COLLECTIBLE_MODELS[eventName] or COLLECTIBLE_MODELS.Snow
	local config = model[rarity] or model.Common
	
	local size = math.random(config.size[1], config.size[2])
	
	-- Create collectible part
	local collectible = Instance.new("Part")
	collectible.Name = "Collectible"
	collectible.Size = Vector3.new(size, size, size)
	collectible.Shape = Enum.PartType.Ball
	collectible.Material = config.material
	collectible.BrickColor = BrickColor.new(config.color)
	collectible.Transparency = 0.1
	collectible.Reflectance = 0.3
	collectible.Anchored = true
	collectible.CanCollide = false
	collectible.Position = position
	collectible.Parent = collectibleFolder
	
	-- Store rarity
	local rarityValue = Instance.new("StringValue")
	rarityValue.Name = "Rarity"
	rarityValue.Value = rarity
	rarityValue.Parent = collectible
	
	-- Add glow
	local light = Instance.new("PointLight")
	light.Color = config.color
	light.Brightness = 1.5
	light.Range = size * 3
	light.Parent = collectible
	
	-- Floating animation
	local floatTween = TweenService:Create(
		collectible,
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
	
	-- Rotation
	local rotationTween = TweenService:Create(
		collectible,
		TweenInfo.new(
			5,
			Enum.EasingStyle.Linear,
			Enum.EasingDirection.InOut,
			-1
		),
		{CFrame = collectible.CFrame * CFrame.Angles(0, math.rad(360), 0)}
	)
	rotationTween:Play()
	
	-- Shimmer particles
	local attachment = Instance.new("Attachment")
	attachment.Parent = collectible
	
	local particles = Instance.new("ParticleEmitter")
	particles.Parent = attachment
	particles.Texture = "rbxasset://textures/particles/sparkles.png"
	particles.Color = ColorSequence.new(config.color)
	particles.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0),
		NumberSequenceKeypoint.new(1, 1)
	})
	particles.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1),
		NumberSequenceKeypoint.new(1, 0)
	})
	particles.Lifetime = NumberRange.new(1, 2)
	particles.Rate = 20
	particles.Speed = NumberRange.new(2, 4)
	particles.SpreadAngle = Vector2.new(45, 45)
	
	-- Touch detection with magnet radius support
	local collected = false
	
	-- Check proximity (magnet effect)
	spawn(function()
		while collectible and collectible.Parent and not collected do
			wait(0.1)
			
			for _, player in ipairs(Players:GetPlayers()) do
				if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
					local playerData = _G.PlayerDataManager and _G.PlayerDataManager.GetPlayerData(player)
					if playerData and playerData.magnetRadius > 0 then
						local distance = (player.Character.HumanoidRootPart.Position - collectible.Position).Magnitude
						if distance <= playerData.magnetRadius then
							-- Auto-collect via magnet
							collected = true
							local pointsRange = CONFIG.RarityPoints[rarity] or CONFIG.RarityPoints.Common
							local points = math.random(pointsRange[1], pointsRange[2])
							
							if _G.PlayerDataManager then
								local awardedPoints = _G.PlayerDataManager.AddPoints(player, points, rarity)
								points = awardedPoints
							end
							
							ShowCollectionEffect:FireClient(player, points, rarity, collectible.Position)
							
							-- Collection animation
							TweenService:Create(
								collectible,
								TweenInfo.new(0.3, Enum.EasingStyle.Back),
								{Size = collectible.Size * 1.5, Transparency = 1}
							):Play()
							
							wait(0.3)
							collectible:Destroy()
							
							-- Respawn
							spawn(function()
								wait(CONFIG.RespawnTime)
								if #collectibleFolder:GetChildren() < CONFIG.MaxCollectibles then
									local spawnPoints = getSpawnPoints()
									if #spawnPoints > 0 then
										local spawnPoint = spawnPoints[math.random(1, #spawnPoints)]
										local newPos = spawnPoint.Position + Vector3.new(
											math.random(-10, 10),
											3,
											math.random(-10, 10)
										)
										createCollectible(newPos, eventName)
									end
								end
							end)
							
							return
						end
					end
				end
			end
		end
	end)
	
	collectible.Touched:Connect(function(hit)
		if collected then return end
		
		local humanoid = hit.Parent:FindFirstChildOfClass("Humanoid")
		if humanoid then
			local player = Players:GetPlayerFromCharacter(hit.Parent)
			if player then
				collected = true
				
				-- Get points
				local pointsRange = CONFIG.RarityPoints[rarity] or CONFIG.RarityPoints.Common
				local points = math.random(pointsRange[1], pointsRange[2])
				
				-- Award points
				if _G.PlayerDataManager then
					local awardedPoints = _G.PlayerDataManager.AddPoints(player, points, rarity)
					points = awardedPoints -- Use the actual points awarded (after multipliers)
				end
				
				-- Show effect
				ShowCollectionEffect:FireClient(player, points, rarity, collectible.Position)
				
				-- Play sound
				local sound = Instance.new("Sound")
				sound.SoundId = "rbxasset://sounds/impact_water.wav"
				sound.Volume = 0.5
				sound.Parent = collectible
				sound:Play()
				
				-- Collection animation
				TweenService:Create(
					collectible,
					TweenInfo.new(0.3, Enum.EasingStyle.Back),
					{Size = collectible.Size * 1.5, Transparency = 1}
				):Play()
				
				wait(0.3)
				collectible:Destroy()
				
				-- Respawn after delay
				spawn(function()
					wait(CONFIG.RespawnTime)
					if #collectibleFolder:GetChildren() < CONFIG.MaxCollectibles then
						local spawnPoints = getSpawnPoints()
						if #spawnPoints > 0 then
							local spawnPoint = spawnPoints[math.random(1, #spawnPoints)]
							local newPos = spawnPoint.Position + Vector3.new(
								math.random(-10, 10),
								3,
								math.random(-10, 10)
							)
							createCollectible(newPos, eventName)
						end
					end
				end)
			end
		end
	end)
	
	return collectible
end

-- ============================================
-- SPAWNING SYSTEM
-- ============================================
local function spawnCollectibles()
	local spawnPoints = getSpawnPoints()
	if #spawnPoints == 0 then return end
	
	local currentEvent = _G.EventManager and _G.EventManager.GetCurrentEvent() or "Snow"
	
	while true do
		wait(CONFIG.BaseSpawnRate)
		
		local currentCount = #collectibleFolder:GetChildren()
		if currentCount < CONFIG.MaxCollectibles then
			local spawnPoint = spawnPoints[math.random(1, #spawnPoints)]
			local position = spawnPoint.Position + Vector3.new(
				math.random(-10, 10),
				3,
				math.random(-10, 10)
			)
			
			createCollectible(position, currentEvent)
		end
	end
end

-- ============================================
-- EVENT SWITCHING
-- ============================================
local function switchEvent(newEvent)
	-- Clear existing collectibles
	for _, collectible in ipairs(collectibleFolder:GetChildren()) do
		collectible:Destroy()
	end
	
	-- Spawn new event collectibles
	spawn(function()
		wait(1)
		local spawnPoints = getSpawnPoints()
		for i = 1, math.min(20, CONFIG.MaxCollectibles) do
			if #spawnPoints > 0 then
				local spawnPoint = spawnPoints[math.random(1, #spawnPoints)]
				local position = spawnPoint.Position + Vector3.new(
					math.random(-10, 10),
					3,
					math.random(-10, 10)
				)
				createCollectible(position, newEvent)
				wait(0.2)
			end
		end
	end)
end

-- ============================================
-- INITIALIZATION
-- ============================================
spawn(function()
	wait(2) -- Wait for EventManager
	spawnCollectibles()
end)

-- ============================================
-- EXPORT API
-- ============================================
_G.CollectibleManager = {
	SwitchEvent = switchEvent,
	GetConfig = function()
		return CONFIG
	end,
}

print("✅ Collectible Manager initialized")
print("   - Max collectibles: " .. CONFIG.MaxCollectibles)
print("   - Rarity system: Common, Rare, Epic, Legendary")
