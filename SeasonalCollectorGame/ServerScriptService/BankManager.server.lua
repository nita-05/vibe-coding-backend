-- BankManager.server.lua
-- Creates bank building, banker NPC, and handles deposit/withdrawal
-- Place in ServerScriptService

local Workspace = game:GetService("Workspace")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local CollectionService = game:GetService("CollectionService")

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

local OpenBank = getOrCreateEvent("OpenBank")
local DepositCoins = getOrCreateEvent("DepositCoins")
local WithdrawCoins = getOrCreateEvent("WithdrawCoins")

-- ============================================
-- BANK CONFIGURATION
-- ============================================
local BANK_POSITION = Vector3.new(100, 5, 0) -- Adjust position as needed
local BANKER_POSITION = Vector3.new(100, 5, -5) -- Inside bank
local ENABLE_BANKER_NPC = false -- user wants only BrickMailbox, no overlay
local CLEANUP_EXISTING_NPCS = true -- removes old NPC overlays from previous runs
local OVERLAY_CLEANUP_INTERVAL_SECONDS = 0.5 -- keep removing if something respawns it

local function cleanupNpcOverlays()
	local function looksLikeNpcNameTag(gui)
		if not gui or not gui:IsA("BillboardGui") then return false end
		-- Any billboard that displays Banker / Keeper style text
		for _, d in ipairs(gui:GetDescendants()) do
			if d:IsA("TextLabel") then
				local t = tostring(d.Text or "")
				local tl = string.lower(t)
				if tl:find("banker", 1, true) then
					return true
				end
				if tl:match(" keeper$") then
					return true
				end
				if tl:find("shop", 1, true) and tl:find("keeper", 1, true) then
					return true
				end
			end
		end
		-- Also clean any legacy name tags by name
		return gui.Name == "NameTag"
	end

	local function looksLikeNpcPrompt(prompt)
		if not prompt or not prompt:IsA("ProximityPrompt") then return false end
		local a = tostring(prompt.ActionText or "")
		if a == "Talk to Banker" then return true end
		if a:match("^Talk to ") then return true end
		if a:match("^Shop at ") then return true end
		return false
	end

	-- Remove Banker + Shop Keeper NPCs + their UI, even if renamed
	for _, inst in ipairs(Workspace:GetDescendants()) do
		if inst:IsA("Model") then
			-- Direct name match
			local nl = string.lower(inst.Name or "")
			if nl == "banker" or nl:match(" keeper$") then
				inst:Destroy()
				continue
			end
		end

		if inst:IsA("BillboardGui") and looksLikeNpcNameTag(inst) then
			inst:Destroy()
			continue
		end

		if inst:IsA("ProximityPrompt") and looksLikeNpcPrompt(inst) then
			inst:Destroy()
			continue
		end
	end
end

-- Run cleanup immediately so the overlay never flashes on spawn
if CLEANUP_EXISTING_NPCS then
	cleanupNpcOverlays()
	-- And keep cleaning in case another script respawns UI/NPCs later
	task.spawn(function()
		while true do
			task.wait(OVERLAY_CLEANUP_INTERVAL_SECONDS)
			cleanupNpcOverlays()
		end
	end)
end

-- Deposit Station configuration:
-- Tag any Part/Model with "DepositStation" (recommended) OR name it "DepositStation"
-- and walking near it will open the Bank UI (no prompt overlay).
local DEPOSIT_STATION_TAG = "DepositStation"
local DEPOSIT_TOUCH_COOLDOWN_SECONDS = 1.0 -- cooldown for manual prompt spam
local DEPOSIT_DEFAULT_RADIUS_STUDS = 6 -- how close the player must be to deposit

-- BrickMailbox configuration (your map has 3 models named BrickMailbox under Workspace.Yard)
local MAILBOX_NAME = "BrickMailbox"
local MAILBOX_PARENT_NAME = "Yard" -- optional; if not found we scan whole Workspace

-- ============================================
-- CREATE BANK BUILDING
-- ============================================
local function createBankBuilding()
	local bankFolder = Instance.new("Folder")
	bankFolder.Name = "Bank"
	bankFolder.Parent = Workspace
	
	-- Main building base
	local base = Instance.new("Part")
	base.Name = "BankBase"
	base.Size = Vector3.new(30, 2, 30)
	base.Material = Enum.Material.Concrete
	base.BrickColor = BrickColor.new("Dark stone grey")
	base.Anchored = true
	base.Position = BANK_POSITION
	base.Parent = bankFolder
	
	-- Building walls
	local wall1 = Instance.new("Part")
	wall1.Name = "Wall1"
	wall1.Size = Vector3.new(30, 15, 2)
	wall1.Material = Enum.Material.Brick
	wall1.BrickColor = BrickColor.new("Dark stone grey")
	wall1.Anchored = true
	wall1.Position = BANK_POSITION + Vector3.new(0, 7.5, -14)
	wall1.Parent = bankFolder
	
	local wall2 = Instance.new("Part")
	wall2.Name = "Wall2"
	wall2.Size = Vector3.new(30, 15, 2)
	wall2.Material = Enum.Material.Brick
	wall2.BrickColor = BrickColor.new("Dark stone grey")
	wall2.Anchored = true
	wall2.Position = BANK_POSITION + Vector3.new(0, 7.5, 14)
	wall2.Parent = bankFolder
	
	local wall3 = Instance.new("Part")
	wall3.Name = "Wall3"
	wall3.Size = Vector3.new(2, 15, 30)
	wall3.Material = Enum.Material.Brick
	wall3.BrickColor = BrickColor.new("Dark stone grey")
	wall3.Anchored = true
	wall3.Position = BANK_POSITION + Vector3.new(-14, 7.5, 0)
	wall3.Parent = bankFolder
	
	local wall4 = Instance.new("Part")
	wall4.Name = "Wall4"
	wall4.Size = Vector3.new(2, 15, 30)
	wall4.Material = Enum.Material.Brick
	wall4.BrickColor = BrickColor.new("Dark stone grey")
	wall4.Anchored = true
	wall4.Position = BANK_POSITION + Vector3.new(14, 7.5, 0)
	wall4.Parent = bankFolder
	
	-- Roof
	local roof = Instance.new("Part")
	roof.Name = "Roof"
	roof.Size = Vector3.new(32, 1, 32)
	roof.Material = Enum.Material.Metal
	roof.BrickColor = BrickColor.new("Really black")
	roof.Anchored = true
	roof.Position = BANK_POSITION + Vector3.new(0, 15.5, 0)
	roof.Parent = bankFolder
	
	-- Entrance (opening in front wall)
	local entrance = Instance.new("Part")
	entrance.Name = "Entrance"
	entrance.Size = Vector3.new(8, 10, 2)
	entrance.Material = Enum.Material.Concrete
	entrance.BrickColor = BrickColor.new("Dark stone grey")
	entrance.Anchored = true
	entrance.Position = BANK_POSITION + Vector3.new(0, 5, -14)
	entrance.Transparency = 1
	entrance.CanCollide = false
	entrance.Parent = bankFolder
	
	-- Bank sign
	local sign = Instance.new("Part")
	sign.Name = "BankSign"
	sign.Size = Vector3.new(12, 3, 0.5)
	sign.Material = Enum.Material.Neon
	sign.BrickColor = BrickColor.new("Bright yellow")
	sign.Anchored = true
	sign.Position = BANK_POSITION + Vector3.new(0, 12, -13.5)
	sign.Parent = bankFolder
	
	local signLight = Instance.new("PointLight")
	signLight.Color = Color3.fromRGB(255, 255, 0)
	signLight.Brightness = 2
	signLight.Range = 20
	signLight.Parent = sign
	
	local signText = Instance.new("SurfaceGui")
	signText.Face = Enum.NormalId.Front
	signText.Parent = sign
	
	local signLabel = Instance.new("TextLabel")
	signLabel.Size = UDim2.new(1, 0, 1, 0)
	signLabel.BackgroundTransparency = 1
	signLabel.Text = "🏦 BANK"
	signLabel.TextColor3 = Color3.fromRGB(0, 0, 0)
	signLabel.TextSize = 24
	signLabel.Font = Enum.Font.GothamBold
	signLabel.Parent = signText
	
	-- Counter/desk for banker
	local counter = Instance.new("Part")
	counter.Name = "Counter"
	counter.Size = Vector3.new(10, 2, 4)
	counter.Material = Enum.Material.Wood
	counter.BrickColor = BrickColor.new("Brown")
	counter.Anchored = true
	counter.Position = BANK_POSITION + Vector3.new(0, 1, -8)
	counter.Parent = bankFolder
	
	return bankFolder
end

-- ============================================
-- CREATE BANKER NPC
-- ============================================
local function createBankerNPC()
	local npc = Instance.new("Model")
	npc.Name = "Banker"
	npc.Parent = Workspace:FindFirstChild("Bank") or Workspace
	
	-- HumanoidRootPart
	local rootPart = Instance.new("Part")
	rootPart.Name = "HumanoidRootPart"
	rootPart.Size = Vector3.new(2, 2, 1)
	rootPart.Material = Enum.Material.SmoothPlastic
	rootPart.BrickColor = BrickColor.new("Dark green") -- Professional banker color
	rootPart.Anchored = true
	rootPart.CanCollide = false
	rootPart.Position = BANKER_POSITION
	rootPart.Parent = npc
	
	-- Humanoid
	local humanoid = Instance.new("Humanoid")
	humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	humanoid.WalkSpeed = 0
	humanoid.Parent = npc
	
	-- Head
	local head = Instance.new("Part")
	head.Name = "Head"
	head.Size = Vector3.new(2, 1, 1)
	head.Material = Enum.Material.SmoothPlastic
	head.BrickColor = BrickColor.new("Bright yellow")
	head.Shape = Enum.PartType.Ball
	head.Anchored = true
	head.CanCollide = false
	head.Position = BANKER_POSITION + Vector3.new(0, 1.5, 0)
	head.Parent = npc
	
	local face = Instance.new("Decal")
	face.Texture = "rbxasset://textures/face.png"
	face.Face = Enum.NormalId.Front
	face.Parent = head
	
	-- Torso
	local torso = Instance.new("Part")
	torso.Name = "Torso"
	torso.Size = Vector3.new(2, 2, 1)
	torso.Material = Enum.Material.SmoothPlastic
	torso.BrickColor = BrickColor.new("Dark green")
	torso.Anchored = true
	torso.CanCollide = false
	torso.Position = BANKER_POSITION
	torso.Parent = npc
	
	-- Arms
	local leftArm = Instance.new("Part")
	leftArm.Name = "Left Arm"
	leftArm.Size = Vector3.new(1, 2, 1)
	leftArm.Material = Enum.Material.SmoothPlastic
	leftArm.BrickColor = BrickColor.new("Dark green")
	leftArm.Anchored = true
	leftArm.CanCollide = false
	leftArm.Position = BANKER_POSITION + Vector3.new(-1.5, 0, 0)
	leftArm.Parent = npc
	
	local rightArm = Instance.new("Part")
	rightArm.Name = "Right Arm"
	rightArm.Size = Vector3.new(1, 2, 1)
	rightArm.Material = Enum.Material.SmoothPlastic
	rightArm.BrickColor = BrickColor.new("Dark green")
	rightArm.Anchored = true
	rightArm.CanCollide = false
	rightArm.Position = BANKER_POSITION + Vector3.new(1.5, 0, 0)
	rightArm.Parent = npc
	
	-- Legs
	local leftLeg = Instance.new("Part")
	leftLeg.Name = "Left Leg"
	leftLeg.Size = Vector3.new(1, 2, 1)
	leftLeg.Material = Enum.Material.SmoothPlastic
	leftLeg.BrickColor = BrickColor.new("Really black")
	leftLeg.Anchored = true
	leftLeg.CanCollide = false
	leftLeg.Position = BANKER_POSITION + Vector3.new(-0.5, -2, 0)
	leftLeg.Parent = npc
	
	local rightLeg = Instance.new("Part")
	rightLeg.Name = "Right Leg"
	rightLeg.Size = Vector3.new(1, 2, 1)
	rightLeg.Material = Enum.Material.SmoothPlastic
	rightLeg.BrickColor = BrickColor.new("Really black")
	rightLeg.Anchored = true
	rightLeg.CanCollide = false
	rightLeg.Position = BANKER_POSITION + Vector3.new(0.5, -2, 0)
	rightLeg.Parent = npc
	
	-- Name tag
	local billboard = Instance.new("BillboardGui")
	billboard.Name = "NameTag"
	billboard.Size = UDim2.new(0, 150, 0, 35)
	billboard.StudsOffset = Vector3.new(0, 2.5, 0)
	billboard.AlwaysOnTop = true
	billboard.Parent = head
	
	local nameLabel = Instance.new("TextLabel")
	nameLabel.Size = UDim2.new(1, 0, 1, 0)
	nameLabel.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
	nameLabel.BackgroundTransparency = 0.4
	nameLabel.Text = "Banker"
	nameLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
	nameLabel.TextSize = 14
	nameLabel.Font = Enum.Font.GothamBold
	nameLabel.Parent = billboard
	
	-- Interaction prompt
	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "InteractionPrompt"
	prompt.ActionText = "Talk to Banker"
	prompt.KeyboardKeyCode = Enum.KeyCode.E
	prompt.HoldDuration = 0
	prompt.MaxActivationDistance = 10
	prompt.Parent = head
	
	prompt.Triggered:Connect(function(player)
		OpenBank:FireClient(player)
	end)
	
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
		{Position = BANKER_POSITION + Vector3.new(0, 0.5, 0)}
	)
	floatTween:Play()
	
	return npc
end

-- ============================================
-- BANK FUNCTIONS
-- ============================================
local function depositCoins(player, amount)
	if not player or not player.Parent then return false, "Player not found" end
	
	-- Get player data
	local playerData = _G.PlayerDataManager and _G.PlayerDataManager.GetPlayerData(player)
	if not playerData then
		return false, "Player data not found"
	end
	
	-- Validate amount
	amount = math.floor(amount)
	if amount <= 0 then
		return false, "Invalid amount"
	end
	
	-- Check if player has enough coins
	if (playerData.coins or 0) < amount then
		return false, "Not enough coins! You have " .. (playerData.coins or 0) .. " coins"
	end
	
	-- Deposit coins
	playerData.coins = (playerData.coins or 0) - amount
	playerData.bankBalance = (playerData.bankBalance or 0) + amount
	
	-- Save data
	local DataStoreManager = require(ReplicatedStorage:WaitForChild("Modules"):WaitForChild("DataStoreManager"))
	DataStoreManager.SavePlayerData(player, playerData)
	
	-- Update client
	local UpdateStats = getOrCreateEvent("UpdateStats")
	UpdateStats:FireClient(player, playerData)
	
	print("✅ " .. player.Name .. " deposited " .. amount .. " coins. Bank balance: " .. playerData.bankBalance)
	
	return true, "Deposited " .. amount .. " coins!"
end

local function depositAllWalletCoins(player)
	if not player or not player.Parent then return false, "Player not found" end

	local playerData = _G.PlayerDataManager and _G.PlayerDataManager.GetPlayerData(player)
	if not playerData then
		return false, "Player data not found"
	end

	local wallet = math.floor(playerData.coins or 0)
	if wallet <= 0 then
		return false, "No coins to deposit"
	end

	return depositCoins(player, wallet)
end

local function withdrawCoins(player, amount)
	if not player or not player.Parent then return false, "Player not found" end
	
	-- Get player data
	local playerData = _G.PlayerDataManager and _G.PlayerDataManager.GetPlayerData(player)
	if not playerData then
		return false, "Player data not found"
	end
	
	-- Validate amount
	amount = math.floor(amount)
	if amount <= 0 then
		return false, "Invalid amount"
	end
	
	-- Check if player has enough in bank
	if (playerData.bankBalance or 0) < amount then
		return false, "Not enough coins in bank! You have " .. (playerData.bankBalance or 0) .. " coins"
	end

	-- Wallet capacity check (smart withdraw)
	local capacity = math.floor(tonumber(playerData.walletCapacity) or 100)
	if capacity <= 0 then capacity = 100 end
	local wallet = math.floor(tonumber(playerData.coins) or 0)
	local space = math.max(0, capacity - wallet)
	if space <= 0 then
		return false, "Wallet is full (max " .. tostring(capacity) .. "). Deposit or spend coins first."
	end

	local actual = math.min(amount, space)
	local leftover = amount - actual

	-- Withdraw coins (only what fits)
	playerData.bankBalance = (playerData.bankBalance or 0) - actual
	playerData.coins = wallet + actual
	
	-- Save data
	local DataStoreManager = require(ReplicatedStorage:WaitForChild("Modules"):WaitForChild("DataStoreManager"))
	DataStoreManager.SavePlayerData(player, playerData)
	
	-- Update client
	local UpdateStats = getOrCreateEvent("UpdateStats")
	UpdateStats:FireClient(player, playerData)
	
	print("✅ " .. player.Name .. " withdrew " .. actual .. " coins. Bank balance: " .. playerData.bankBalance)

	if leftover > 0 then
		return true, "Withdrew " .. tostring(actual) .. " coins (wallet full; " .. tostring(leftover) .. " stayed in bank)."
	end
	return true, "Withdrew " .. tostring(actual) .. " coins!"
end

-- ============================================
-- REMOTE EVENT HANDLERS
-- ============================================
DepositCoins.OnServerEvent:Connect(function(player, amount)
	local success, message = depositCoins(player, amount)
	DepositCoins:FireClient(player, success, message)
end)

WithdrawCoins.OnServerEvent:Connect(function(player, amount)
	local success, message = withdrawCoins(player, amount)
	WithdrawCoins:FireClient(player, success, message)
end)

-- ============================================
-- DEPOSIT STATIONS (AUTO-DEPOSIT, NO OVERLAY)
-- ============================================
local lastDepositAt = {}
local depositStations = {} -- [Instance] = {getPosition = fn, radius = number}
local promptByStation = {} -- [Instance] = ProximityPrompt

local function getPlayerFromHit(hit)
	if not hit then return nil end
	local model = hit:FindFirstAncestorOfClass("Model")
	if not model then return nil end
	return Players:GetPlayerFromCharacter(model)
end

local function disableAnyPrompts(container)
	for _, d in ipairs(container:GetDescendants()) do
		if d:IsA("ProximityPrompt") then
			d.Enabled = false -- removes the overlay completely
		end
	end
end

local function ensureBankPrompt(stationInst: Instance)
	if not stationInst or not stationInst.Parent then return end
	if promptByStation[stationInst] and promptByStation[stationInst].Parent then
		return
	end
	-- Avoid repeated work
	if stationInst:GetAttribute("__BankPrompted") then
		return
	end
	stationInst:SetAttribute("__BankPrompted", true)

	-- Find an attachment part to host the prompt
	local hostPart: BasePart? = nil
	if stationInst:IsA("BasePart") then
		hostPart = stationInst
	elseif stationInst:IsA("Model") then
		hostPart = stationInst.PrimaryPart or stationInst:FindFirstChildWhichIsA("BasePart", true)
	end
	if not hostPart then return end

	-- Disable any existing prompts so we only have one clean interaction
	disableAnyPrompts(stationInst)

	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "BankPrompt"
	prompt.ActionText = "Open Bank"
	prompt.ObjectText = "BrickMailbox"
	prompt.KeyboardKeyCode = Enum.KeyCode.E
	prompt.HoldDuration = 0
	prompt.MaxActivationDistance = 10
	prompt.RequiresLineOfSight = false
	prompt.Parent = hostPart

	prompt.Triggered:Connect(function(player)
		local now = os.clock()
		local last = lastDepositAt[player]
		if last and (now - last) < DEPOSIT_TOUCH_COOLDOWN_SECONDS then
			return
		end
		lastDepositAt[player] = now
		OpenBank:FireClient(player, "mailbox")
	end)

	promptByStation[stationInst] = prompt
end

local function hookDepositPart(part)
	if not part or not part:IsA("BasePart") then return end
	if part:GetAttribute("__DepositHooked") then return end
	part:SetAttribute("__DepositHooked", true)

	-- Manual open only: no auto-open on touch
end

local function registerDepositStation(inst)
	if not inst then return end
	if depositStations[inst] then return end

	-- If the station is a Model, use its bounding box center. If it's a Part, use its position.
	if inst:IsA("BasePart") then
		depositStations[inst] = {
			getPosition = function()
				if inst.Parent then
					return inst.Position
				end
				return nil
			end,
			radius = math.max(DEPOSIT_DEFAULT_RADIUS_STUDS, math.max(inst.Size.X, inst.Size.Z) * 0.5),
		}
	elseif inst:IsA("Model") then
		depositStations[inst] = {
			getPosition = function()
				if inst.Parent then
					local cf = inst:GetPivot()
					return cf.Position
				end
				return nil
			end,
			radius = DEPOSIT_DEFAULT_RADIUS_STUDS,
		}
	end

	ensureBankPrompt(inst)
end

local function hookDepositModel(model)
	if not model or not model:IsA("Model") then return end
	if model:GetAttribute("__DepositHooked") then return end
	model:SetAttribute("__DepositHooked", true)

	registerDepositStation(model)
	ensureBankPrompt(model)

	-- Prefer PrimaryPart; otherwise hook all BaseParts in the model
	if model.PrimaryPart then
		hookDepositPart(model.PrimaryPart)
		return
	end

	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("BasePart") then
			hookDepositPart(d)
		end
	end
end

local function tryHookDepositInstance(inst)
	if not inst then return end

	if inst:IsA("BasePart") then
		registerDepositStation(inst)
		hookDepositPart(inst)
	elseif inst:IsA("Model") then
		registerDepositStation(inst)
		hookDepositModel(inst)
	end
end

local function scanAndHookDepositStations()
	-- 1) Tagged instances (best)
	for _, inst in ipairs(CollectionService:GetTagged(DEPOSIT_STATION_TAG)) do
		tryHookDepositInstance(inst)
	end

	-- 2) Fallback: anything named "DepositStation"
	for _, inst in ipairs(Workspace:GetDescendants()) do
		if inst.Name == "DepositStation" then
			tryHookDepositInstance(inst)
		end
	end
end

local function scanAndHookBrickMailboxes()
	local root = Workspace:FindFirstChild(MAILBOX_PARENT_NAME) or Workspace
	for _, inst in ipairs(root:GetDescendants()) do
		if inst.Name == MAILBOX_NAME and (inst:IsA("Model") or inst:IsA("BasePart")) then
			ensureBankPrompt(inst)
		end
	end
end

-- If mailboxes are added later (streaming / late loads), hook them too
Workspace.DescendantAdded:Connect(function(inst)
	if inst and inst.Name == MAILBOX_NAME and (inst:IsA("Model") or inst:IsA("BasePart")) then
		ensureBankPrompt(inst)
	end
end)

CollectionService:GetInstanceAddedSignal(DEPOSIT_STATION_TAG):Connect(function(inst)
	tryHookDepositInstance(inst)
end)

Players.PlayerRemoving:Connect(function(player)
	lastDepositAt[player] = nil
end)

-- ============================================
-- INITIALIZATION
-- ============================================
spawn(function()
	wait(2) -- Wait for workspace to load
	if CLEANUP_EXISTING_NPCS then
		cleanupNpcOverlays()
	end
	createBankBuilding()
	wait(0.5)
	if ENABLE_BANKER_NPC then
	createBankerNPC()
	end
	-- Prefer BrickMailbox prompts (your case)
	scanAndHookBrickMailboxes()

	-- Keep deposit-station support too (optional)
	scanAndHookDepositStations()
end)

-- ============================================
-- EXPORT API
-- ============================================
_G.BankManager = {
	DepositCoins = depositCoins,
	WithdrawCoins = withdrawCoins,
}

print("✅ Bank Manager initialized")
print("   - Bank building created")
if ENABLE_BANKER_NPC then
print("   - Banker NPC created")
else
	print("   - Banker NPC disabled (BrickMailbox only)")
end
