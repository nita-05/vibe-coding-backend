-- ObstacleManager.server.lua
-- Handles obstacles that kill players instantly on touch
-- Place in ServerScriptService

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

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

local UpdateLives = getOrCreateEvent("UpdateLives")
local LifeMessage = getOrCreateEvent("LifeMessage")

-- Spawn protection + shield support (prevents instant spawn-death)
local SPAWN_GRACE_SECONDS = 2.5
local protectUntilByPlayer = {} -- [Player] = number

local function tryConsumeShieldFromCharacter(character: Model)
	if not character then return false end
	local ff = character:FindFirstChildOfClass("ForceField")
	if ff then
		ff:Destroy()
		return true
	end
	if character:GetAttribute("ShieldActive") == true then
		character:SetAttribute("ShieldActive", false)
		return true
	end
	return false
end

-- ============================================
-- OBSTACLE DETECTION
-- ============================================
local function isObstacle(part)
	-- Check if part is an obstacle (white ball, hazard, etc.)
	if not part or not part.Parent then return false end
	
	-- Check by name
	local name = part.Name:lower()
	if name:find("obstacle") or name:find("hazard") or name:find("death") then
		return true
	end
	
	-- Check if part has "Obstacle" attribute
	if part:GetAttribute("IsObstacle") == true then
		return true
	end
	
	return false
end

-- ============================================
-- HANDLE OBSTACLE TOUCH
-- ============================================
local function onObstacleTouched(hit, obstacle)
	local character = hit.Parent
	local humanoid = character:FindFirstChild("Humanoid")
	
	if not humanoid or not character then return end
	
	local player = Players:GetPlayerFromCharacter(character)
	if not player then return end

	-- Spawn grace: ignore early touches right after spawn
	local now = os.clock()
	local protectUntil = protectUntilByPlayer[player]
	if protectUntil and now < protectUntil then
		return
	end

	-- Shield blocks one hit
	if tryConsumeShieldFromCharacter(character) then
		LifeMessage:FireClient(player, "🛡️ Shield protected you!")
		return
	end
	
	-- Instant death - set health to 0 immediately
	humanoid.Health = 0
	
	-- Optional: Show message
	LifeMessage:FireClient(player, "💀 Hit by obstacle!")
end

-- ============================================
-- SCAN AND SETUP OBSTACLES
-- ============================================
local function setupObstacle(obstacle)
	if not obstacle:IsA("BasePart") then return end
	
	-- Make sure it can be touched
	obstacle.CanTouch = true
	obstacle.CanCollide = true
	
	-- Connect touched event
	local connection
	connection = obstacle.Touched:Connect(function(hit)
		if hit and hit.Parent then
			local humanoid = hit.Parent:FindFirstChild("Humanoid")
			if humanoid then
				onObstacleTouched(hit, obstacle)
			end
		end
	end)
	
	-- Clean up connection when obstacle is removed
	obstacle.AncestryChanged:Connect(function()
		if not obstacle.Parent then
			if connection then
				connection:Disconnect()
			end
		end
	end)
end

-- ============================================
-- SCAN WORKSPACE FOR OBSTACLES
-- ============================================
local function scanForObstacles()
	local workspace = game:GetService("Workspace")
	
	-- Scan all parts in workspace
	for _, obj in ipairs(workspace:GetDescendants()) do
		if obj:IsA("BasePart") and isObstacle(obj) then
			setupObstacle(obj)
		end
	end
	
	-- Watch for new obstacles
	workspace.DescendantAdded:Connect(function(obj)
		if obj:IsA("BasePart") and isObstacle(obj) then
			setupObstacle(obj)
		end
	end)
end

-- ============================================
-- INITIALIZE
-- ============================================
task.wait(2) -- Wait for workspace to load
scanForObstacles()

Players.PlayerAdded:Connect(function(player)
	player.CharacterAdded:Connect(function()
		protectUntilByPlayer[player] = os.clock() + SPAWN_GRACE_SECONDS
	end)
end)

Players.PlayerRemoving:Connect(function(player)
	protectUntilByPlayer[player] = nil
end)

print("✅ Obstacle Manager initialized - Instant death on obstacle touch")
