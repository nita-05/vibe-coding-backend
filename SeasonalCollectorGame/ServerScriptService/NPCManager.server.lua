-- NPCManager.server.lua
-- Manages NPCs: Event Guide, Shop, Quest
-- Place in ServerScriptService

local Workspace = game:GetService("Workspace")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

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

local ShowNPCDialog = getOrCreateEvent("ShowNPCDialog")
local OpenShop = getOrCreateEvent("OpenShop")
local OpenQuest = getOrCreateEvent("OpenQuest")

-- ============================================
-- NPC FOLDER
-- ============================================
local npcFolder = Instance.new("Folder")
npcFolder.Name = "NPCs"
npcFolder.Parent = Workspace

-- ============================================
-- CREATE NPC MODEL (Enhanced - Better Proportions)
-- ============================================
local function createNPCModel(name, position, npcType)
	local npc = Instance.new("Model")
	npc.Name = name
	npc.Parent = npcFolder
	
	-- HumanoidRootPart (proper size)
	local rootPart = Instance.new("Part")
	rootPart.Name = "HumanoidRootPart"
	rootPart.Size = Vector3.new(2, 2, 1)
	rootPart.Material = Enum.Material.SmoothPlastic
	rootPart.BrickColor = BrickColor.new("Bright blue")
	rootPart.Anchored = true
	rootPart.CanCollide = false
	rootPart.Position = position
	rootPart.Parent = npc
	
	-- Humanoid
	local humanoid = Instance.new("Humanoid")
	humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	humanoid.WalkSpeed = 0 -- Don't move
	humanoid.Parent = npc
	
	-- Head (proper size and shape)
	local head = Instance.new("Part")
	head.Name = "Head"
	head.Size = Vector3.new(2, 1, 1)
	head.Material = Enum.Material.SmoothPlastic
	head.BrickColor = BrickColor.new("Bright yellow")
	head.Shape = Enum.PartType.Ball
	head.Anchored = true
	head.CanCollide = false
	head.Position = position + Vector3.new(0, 1.5, 0)
	head.Parent = npc
	
	-- Face (proper texture)
	local face = Instance.new("Decal")
	face.Texture = "rbxasset://textures/face.png"
	face.Face = Enum.NormalId.Front
	face.Parent = head
	
	-- Torso (proper proportions)
	local torso = Instance.new("Part")
	torso.Name = "Torso"
	torso.Size = Vector3.new(2, 2, 1)
	torso.Material = Enum.Material.SmoothPlastic
	-- Shop Keeper: Business attire color
	if npcType == "Shop" then
		torso.BrickColor = BrickColor.new("Dark green") -- Business-like
	else
		torso.BrickColor = BrickColor.new("Bright blue")
	end
	torso.Anchored = true
	torso.CanCollide = false
	torso.Position = position
	torso.Parent = npc
	
	-- Arms (for better appearance)
	local leftArm = Instance.new("Part")
	leftArm.Name = "Left Arm"
	leftArm.Size = Vector3.new(1, 2, 1)
	leftArm.Material = Enum.Material.SmoothPlastic
	leftArm.BrickColor = torso.BrickColor
	leftArm.Anchored = true
	leftArm.CanCollide = false
	leftArm.Position = position + Vector3.new(-1.5, 0, 0)
	leftArm.Parent = npc
	
	local rightArm = Instance.new("Part")
	rightArm.Name = "Right Arm"
	rightArm.Size = Vector3.new(1, 2, 1)
	rightArm.Material = Enum.Material.SmoothPlastic
	rightArm.BrickColor = torso.BrickColor
	rightArm.Anchored = true
	rightArm.CanCollide = false
	rightArm.Position = position + Vector3.new(1.5, 0, 0)
	rightArm.Parent = npc
	
	-- Legs
	local leftLeg = Instance.new("Part")
	leftLeg.Name = "Left Leg"
	leftLeg.Size = Vector3.new(1, 2, 1)
	leftLeg.Material = Enum.Material.SmoothPlastic
	leftLeg.BrickColor = BrickColor.new("Really black") -- Pants
	leftLeg.Anchored = true
	leftLeg.CanCollide = false
	leftLeg.Position = position + Vector3.new(-0.5, -2, 0)
	leftLeg.Parent = npc
	
	local rightLeg = Instance.new("Part")
	rightLeg.Name = "Right Leg"
	rightLeg.Size = Vector3.new(1, 2, 1)
	rightLeg.Material = Enum.Material.SmoothPlastic
	rightLeg.BrickColor = BrickColor.new("Really black") -- Pants
	rightLeg.Anchored = true
	rightLeg.CanCollide = false
	rightLeg.Position = position + Vector3.new(0.5, -2, 0)
	rightLeg.Parent = npc
	
	-- Store NPC type
	local typeValue = Instance.new("StringValue")
	typeValue.Name = "NPCType"
	typeValue.Value = npcType
	typeValue.Parent = npc
	
	-- Use head for name tag and prompt
	local head = npc:FindFirstChild("Head")
	if not head then return npc end
	
	-- Name tag (REDUCED SIZE to prevent overlapping)
	local billboard = Instance.new("BillboardGui")
	billboard.Name = "NameTag"
	billboard.Size = UDim2.new(0, 150, 0, 35) -- Smaller to reduce overlap
	billboard.StudsOffset = Vector3.new(0, 2.5, 0) -- Slightly lower
	billboard.AlwaysOnTop = true
	billboard.Parent = head
	
	local nameLabel = Instance.new("TextLabel")
	nameLabel.Size = UDim2.new(1, 0, 1, 0)
	nameLabel.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
	nameLabel.BackgroundTransparency = 0.4 -- More transparent
	nameLabel.Text = name
	nameLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
	nameLabel.TextSize = 14 -- Smaller text
	nameLabel.Font = Enum.Font.GothamBold
	nameLabel.Parent = billboard
	
	-- Interaction prompt
	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "InteractionPrompt"
	prompt.ActionText = "Talk to " .. name
	prompt.KeyboardKeyCode = Enum.KeyCode.E
	prompt.HoldDuration = 0
	prompt.MaxActivationDistance = 10
	prompt.Parent = head
	
	-- Floating animation
	local floatTween = TweenService:Create(
		rootPart,
		TweenInfo.new(
			2,
			Enum.EasingStyle.Sine,
			Enum.EasingDirection.InOut,
			-1,
			true
		),
		{Position = position + Vector3.new(0, 0.5, 0)}
	)
	floatTween:Play()
	
	return npc
end

-- ============================================
-- EVENT GUIDE NPC (REMOVED - User Request)
-- ============================================
local function createEventGuideNPC()
	-- DISABLED: User requested removal of guidance text
	-- return
	local npc = createNPCModel("Event Guide", Vector3.new(50, 5, 50), "EventGuide") -- Moved far away
	
	local prompt = npc.Head:FindFirstChild("InteractionPrompt")
	if prompt then
		prompt.Triggered:Connect(function(player)
			local currentEvent = _G.EventManager and _G.EventManager.GetCurrentEvent() or "Snow"
			local remainingTime = _G.EventManager and _G.EventManager.GetRemainingTime() or 0
			
			local eventName = _G.EventManager and _G.EventManager.GetEventConfig(currentEvent).name or currentEvent
			local minutes = math.floor(remainingTime / 60)
			local seconds = math.floor(remainingTime % 60)
			
			local message = "Current Event: " .. eventName .. "\n"
			message = message .. "Time Remaining: " .. minutes .. "m " .. seconds .. "s\n\n"
			message = message .. "💰 Collect COINS around town!\n"
			message = message .. "🛒 Visit the Shop (green marker) to buy upgrades!\n"
			message = message .. "🚗 Visit the Showroom (blue marker) to buy vehicles!"
			
			ShowNPCDialog:FireClient(player, "Event Guide", message)
		end)
	end
end

-- ============================================
-- SHOP NPC (REMOVED - User Request)
-- ============================================
local function createShopNPC()
	-- DISABLED: User requested removal of visual guide NPCs
	return
end

-- ============================================
-- QUEST NPC (REMOVED - User Request)
-- ============================================
local function createQuestNPC()
	-- DISABLED: User requested removal of guidance text
	-- return
	local npc = createNPCModel("Quest Master", Vector3.new(-50, 5, -50), "Quest") -- Moved far away
	
	local prompt = npc.Head:FindFirstChild("InteractionPrompt")
	if prompt then
		prompt.Triggered:Connect(function(player)
			-- Generate daily quest
			local quests = {
				{
					title = "Collect 50 Items",
					description = "Collect 50 collectibles to complete this quest!",
					target = 50,
					type = "Collect",
					reward = 500,
				},
				{
					title = "Find 5 Rare Items",
					description = "Collect 5 rare or better items!",
					target = 5,
					type = "Rare",
					reward = 750,
				},
			}
			
			local quest = quests[math.random(1, #quests)]
			OpenQuest:FireClient(player, quest)
		end)
	end
end

-- ============================================
-- SHOWROOM GUIDE NPC (REMOVED - User Request)
-- ============================================
local function createShowroomGuideNPC()
	-- DISABLED: User requested removal of visual guide NPCs
	return
end

-- ============================================
-- VIBE AI ASSISTANT NPC (optional)
-- ============================================
local function createVibeAIAssistantNPC()
	local npc = createNPCModel("Vibe AI", Vector3.new(0, 5, 25), "VibeAI")
	local prompt = npc.Head:FindFirstChild("InteractionPrompt")
	if prompt then
		prompt.ActionText = "Ask Vibe AI"
		prompt.Triggered:Connect(function(player)
			ShowNPCDialog:FireClient(player, "Vibe AI", "Ask me anything about the game.\nTip: coins, bank, hazards, vehicles, upgrades, leveling.", {
				mode = "ai"
			})
		end)
	end
end

-- ============================================
-- INITIALIZATION
-- ============================================
spawn(function()
	wait(2) -- Wait for workspace to load
	-- createEventGuideNPC() -- DISABLED: User requested removal
	-- createShopNPC() -- DISABLED: User requested removal
	-- createQuestNPC() -- DISABLED: User requested removal
	-- createShowroomGuideNPC() -- DISABLED: User requested removal
	createVibeAIAssistantNPC()
end)

-- ============================================
-- EXPORT API
-- ============================================
_G.NPCManager = {
	GetNPCs = function()
		return npcFolder:GetChildren()
	end,
}

print("✅ NPC Manager initialized")
print("   - Event Guide NPC")
print("   - Shop NPC")
print("   - Quest NPC")
print("   - Showroom Guide NPC")
