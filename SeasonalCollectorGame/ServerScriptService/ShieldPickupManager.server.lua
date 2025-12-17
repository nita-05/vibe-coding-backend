-- ShieldPickupManager.server.lua
-- Touch a ShieldPickup to get a shield (ForceField)
-- Place in ServerScriptService

local Workspace = game:GetService("Workspace")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local CollectionService = game:GetService("CollectionService")

local SHIELD_TAG = "ShieldPickup"
local SHIELD_NAME = "ShieldPickup"

local RESPAWN_SECONDS = 20

-- ============================================
-- REMOTE EVENTS (optional)
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

local LifeMessage = getOrCreateEvent("LifeMessage")

local function giveShield(player: Player)
	local char = player.Character
	if not char then return end

	-- If they already have a shield, don't stack
	if char:FindFirstChildOfClass("ForceField") then
		LifeMessage:FireClient(player, "🛡️ Shield already active")	
		return
	end

	local ff = Instance.new("ForceField")
	ff.Name = "Shield"
	ff.Visible = true
	ff.Parent = char

	LifeMessage:FireClient(player, "🛡️ Shield gained!")
end

local function getPlayerFromHit(hit: Instance)
	if not hit then return nil end
	local model = hit:FindFirstAncestorOfClass("Model")
	if not model then return nil end
	return Players:GetPlayerFromCharacter(model)
end

local function hookShieldPart(part: BasePart)
	if not part or not part:IsA("BasePart") then return end
	if part:GetAttribute("__ShieldHooked") then return end
	part:SetAttribute("__ShieldHooked", true)
	part.CanTouch = true

	-- store original visuals once
	if part:GetAttribute("__OrigTransparency") == nil then
		part:SetAttribute("__OrigTransparency", part.Transparency)
	end
	if part:GetAttribute("__OrigCanCollide") == nil then
		part:SetAttribute("__OrigCanCollide", part.CanCollide)
	end

	part.Touched:Connect(function(hit)
		local player = getPlayerFromHit(hit)
		if not player then return end
		if not player.Character then return end

		-- simple debounce per pickup
		if part:GetAttribute("__ShieldBusy") then return end
		part:SetAttribute("__ShieldBusy", true)

		giveShield(player)

		-- hide + respawn (feels like a real game powerup)
		local origT = tonumber(part:GetAttribute("__OrigTransparency")) or 0
		local origC = (part:GetAttribute("__OrigCanCollide") == true)

		part.Transparency = 1
		part.CanTouch = false
		part.CanCollide = false

		task.delay(RESPAWN_SECONDS, function()
			if not part or not part.Parent then return end
			part.Transparency = origT
			part.CanTouch = true
			part.CanCollide = origC
			part:SetAttribute("__ShieldBusy", false)
		end)
	end)
end

local function hookInstance(inst: Instance)
	if not inst then return end

	if inst:IsA("BasePart") then
		hookShieldPart(inst)
		return
	end

	if inst:IsA("Model") then
		-- Prefer PrimaryPart; otherwise hook all parts
		if inst.PrimaryPart then
			hookShieldPart(inst.PrimaryPart)
			return
		end
		for _, d in ipairs(inst:GetDescendants()) do
			if d:IsA("BasePart") then
				hookShieldPart(d)
			end
		end
	end
end

local function scan()
	-- Tagged pickups
	for _, inst in ipairs(CollectionService:GetTagged(SHIELD_TAG)) do
		hookInstance(inst)
	end

	-- Named pickups
	for _, inst in ipairs(Workspace:GetDescendants()) do
		if inst.Name == SHIELD_NAME then
			hookInstance(inst)
		end
	end
end

CollectionService:GetInstanceAddedSignal(SHIELD_TAG):Connect(function(inst)
	hookInstance(inst)
end)

Workspace.DescendantAdded:Connect(function(inst)
	if inst and inst.Name == SHIELD_NAME then
		hookInstance(inst)
	end
end)

scan()
print("✅ Shield Pickup Manager initialized (touch ShieldPickup to gain shield)")
