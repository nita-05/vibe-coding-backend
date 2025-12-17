-- ShopManager.server.lua
-- Creates shop buildings, shopkeeper NPCs, and manages shop items
-- Place in ServerScriptService

local Workspace = game:GetService("Workspace")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local ENABLE_SHOPKEEPER_NPCS = false -- remove floating overlays (user wants mailbox-only)

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

local OpenShop = getOrCreateEvent("OpenShop")
local PurchaseShopItem = getOrCreateEvent("PurchaseShopItem")

-- ============================================
-- SHOP CONFIGURATION
-- ============================================
local SHOP_CONFIG = {
	{
		name = "General Store",
		position = Vector3.new(-100, 5, 0),
		shopkeeperPosition = Vector3.new(-100, 5, -5),
		items = {
			{
				name = "Speed Boost Potion",
				description = "Increases movement speed by 20% for 5 minutes",
				price = 50,
				type = "Consumable",
				icon = "⚡",
			},
			{
				name = "Coin Magnet",
				description = "Attracts nearby coins automatically for 10 minutes",
				price = 100,
				type = "Consumable",
				icon = "🧲",
			},
			{
				name = "Lucky Charm",
				description = "Increases rare coin spawn chance by 15% permanently",
				price = 500,
				type = "Upgrade",
				icon = "🍀",
			},
			{
				name = "Backpack Upgrade",
				description = "Increases coin collection capacity by 50",
				price = 300,
				type = "Upgrade",
				icon = "🎒",
			},
		},
	},
	{
		name = "Equipment Shop",
		position = Vector3.new(0, 5, 100),
		shopkeeperPosition = Vector3.new(0, 5, 95),
		items = {
			{
				name = "Golden Pickaxe",
				description = "Increases coin value by 25%",
				price = 750,
				type = "Equipment",
				icon = "⛏️",
			},
			{
				name = "Diamond Ring",
				description = "Doubles rare coin spawn chance",
				price = 1500,
				type = "Equipment",
				icon = "💍",
			},
			{
				name = "Magic Boots",
				description = "Increases movement speed by 30% permanently",
				price = 1000,
				type = "Equipment",
				icon = "👢",
			},
		},
	},
}

-- ============================================
-- CREATE SHOP BUILDING
-- ============================================
local function createShopBuilding(shopData)
	local shopFolder = Instance.new("Folder")
	shopFolder.Name = shopData.name
	shopFolder.Parent = Workspace
	
	-- Main building base
	local base = Instance.new("Part")
	base.Name = "ShopBase"
	base.Size = Vector3.new(25, 2, 25)
	base.Material = Enum.Material.Concrete
	base.BrickColor = BrickColor.new("Medium stone grey")
	base.Anchored = true
	base.Position = shopData.position
	base.Parent = shopFolder
	
	-- Building walls
	local wall1 = Instance.new("Part")
	wall1.Name = "Wall1"
	wall1.Size = Vector3.new(25, 12, 2)
	wall1.Material = Enum.Material.Brick
	wall1.BrickColor = BrickColor.new("Medium stone grey")
	wall1.Anchored = true
	wall1.Position = shopData.position + Vector3.new(0, 6, -11.5)
	wall1.Parent = shopFolder
	
	local wall2 = Instance.new("Part")
	wall2.Name = "Wall2"
	wall2.Size = Vector3.new(25, 12, 2)
	wall2.Material = Enum.Material.Brick
	wall2.BrickColor = BrickColor.new("Medium stone grey")
	wall2.Anchored = true
	wall2.Position = shopData.position + Vector3.new(0, 6, 11.5)
	wall2.Parent = shopFolder
	
	local wall3 = Instance.new("Part")
	wall3.Name = "Wall3"
	wall3.Size = Vector3.new(2, 12, 25)
	wall3.Material = Enum.Material.Brick
	wall3.BrickColor = BrickColor.new("Medium stone grey")
	wall3.Anchored = true
	wall3.Position = shopData.position + Vector3.new(-11.5, 6, 0)
	wall3.Parent = shopFolder
	
	local wall4 = Instance.new("Part")
	wall4.Name = "Wall4"
	wall4.Size = Vector3.new(2, 12, 25)
	wall4.Material = Enum.Material.Brick
	wall4.BrickColor = BrickColor.new("Medium stone grey")
	wall4.Anchored = true
	wall4.Position = shopData.position + Vector3.new(11.5, 6, 0)
	wall4.Parent = shopFolder
	
	-- Roof
	local roof = Instance.new("Part")
	roof.Name = "Roof"
	roof.Size = Vector3.new(27, 1, 27)
	roof.Material = Enum.Material.Metal
	roof.BrickColor = BrickColor.new("Really black")
	roof.Anchored = true
	roof.Position = shopData.position + Vector3.new(0, 12.5, 0)
	roof.Parent = shopFolder
	
	-- Entrance
	local entrance = Instance.new("Part")
	entrance.Name = "Entrance"
	entrance.Size = Vector3.new(6, 8, 2)
	entrance.Material = Enum.Material.Concrete
	entrance.BrickColor = BrickColor.new("Medium stone grey")
	entrance.Anchored = true
	entrance.Position = shopData.position + Vector3.new(0, 4, -11.5)
	entrance.Transparency = 1
	entrance.CanCollide = false
	entrance.Parent = shopFolder
	
	-- Shop sign
	local sign = Instance.new("Part")
	sign.Name = "ShopSign"
	sign.Size = Vector3.new(10, 2.5, 0.5)
	sign.Material = Enum.Material.Neon
	sign.BrickColor = BrickColor.new("Bright blue")
	sign.Anchored = true
	sign.Position = shopData.position + Vector3.new(0, 10, -11)
	sign.Parent = shopFolder
	
	local signLight = Instance.new("PointLight")
	signLight.Color = Color3.fromRGB(100, 150, 255)
	signLight.Brightness = 1.5
	signLight.Range = 15
	signLight.Parent = sign
	
	local signText = Instance.new("SurfaceGui")
	signText.Face = Enum.NormalId.Front
	signText.Parent = sign
	
	local signLabel = Instance.new("TextLabel")
	signLabel.Size = UDim2.new(1, 0, 1, 0)
	signLabel.BackgroundTransparency = 1
	signLabel.Text = "🛒 " .. shopData.name
	signLabel.TextColor3 = Color3.fromRGB(0, 0, 0)
	signLabel.TextSize = 20
	signLabel.Font = Enum.Font.GothamBold
	signLabel.Parent = signText
	
	-- Counter
	local counter = Instance.new("Part")
	counter.Name = "Counter"
	counter.Size = Vector3.new(8, 1.5, 3)
	counter.Material = Enum.Material.Wood
	counter.BrickColor = BrickColor.new("Brown")
	counter.Anchored = true
	counter.Position = shopData.position + Vector3.new(0, 0.75, -8)
	counter.Parent = shopFolder
	
	return shopFolder
end

-- ============================================
-- CREATE SHOPKEEPER NPC
-- ============================================
local function createShopkeeperNPC(shopData)
	local npc = Instance.new("Model")
	npc.Name = shopData.name .. " Keeper"
	npc.Parent = Workspace:FindFirstChild(shopData.name) or Workspace
	
	-- HumanoidRootPart
	local rootPart = Instance.new("Part")
	rootPart.Name = "HumanoidRootPart"
	rootPart.Size = Vector3.new(2, 2, 1)
	rootPart.Material = Enum.Material.SmoothPlastic
	rootPart.BrickColor = BrickColor.new("Bright orange") -- Shopkeeper color
	rootPart.Anchored = true
	rootPart.CanCollide = false
	rootPart.Position = shopData.shopkeeperPosition
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
	head.Position = shopData.shopkeeperPosition + Vector3.new(0, 1.5, 0)
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
	torso.BrickColor = BrickColor.new("Bright orange")
	torso.Anchored = true
	torso.CanCollide = false
	torso.Position = shopData.shopkeeperPosition
	torso.Parent = npc
	
	-- Arms
	local leftArm = Instance.new("Part")
	leftArm.Name = "Left Arm"
	leftArm.Size = Vector3.new(1, 2, 1)
	leftArm.Material = Enum.Material.SmoothPlastic
	leftArm.BrickColor = BrickColor.new("Bright orange")
	leftArm.Anchored = true
	leftArm.CanCollide = false
	leftArm.Position = shopData.shopkeeperPosition + Vector3.new(-1.5, 0, 0)
	leftArm.Parent = npc
	
	local rightArm = Instance.new("Part")
	rightArm.Name = "Right Arm"
	rightArm.Size = Vector3.new(1, 2, 1)
	rightArm.Material = Enum.Material.SmoothPlastic
	rightArm.BrickColor = BrickColor.new("Bright orange")
	rightArm.Anchored = true
	rightArm.CanCollide = false
	rightArm.Position = shopData.shopkeeperPosition + Vector3.new(1.5, 0, 0)
	rightArm.Parent = npc
	
	-- Legs
	local leftLeg = Instance.new("Part")
	leftLeg.Name = "Left Leg"
	leftLeg.Size = Vector3.new(1, 2, 1)
	leftLeg.Material = Enum.Material.SmoothPlastic
	leftLeg.BrickColor = BrickColor.new("Really black")
	leftLeg.Anchored = true
	leftLeg.CanCollide = false
	leftLeg.Position = shopData.shopkeeperPosition + Vector3.new(-0.5, -2, 0)
	leftLeg.Parent = npc
	
	local rightLeg = Instance.new("Part")
	rightLeg.Name = "Right Leg"
	rightLeg.Size = Vector3.new(1, 2, 1)
	rightLeg.Material = Enum.Material.SmoothPlastic
	rightLeg.BrickColor = BrickColor.new("Really black")
	rightLeg.Anchored = true
	rightLeg.CanCollide = false
	rightLeg.Position = shopData.shopkeeperPosition + Vector3.new(0.5, -2, 0)
	rightLeg.Parent = npc
	
	-- Name tag
	local billboard = Instance.new("BillboardGui")
	billboard.Name = "NameTag"
	billboard.Size = UDim2.new(0, 200, 0, 35)
	billboard.StudsOffset = Vector3.new(0, 2.5, 0)
	billboard.AlwaysOnTop = true
	billboard.Parent = head
	
	local nameLabel = Instance.new("TextLabel")
	nameLabel.Size = UDim2.new(1, 0, 1, 0)
	nameLabel.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
	nameLabel.BackgroundTransparency = 0.4
	nameLabel.Text = shopData.name .. " Keeper"
	nameLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
	nameLabel.TextSize = 14
	nameLabel.Font = Enum.Font.GothamBold
	nameLabel.Parent = billboard
	
	-- Interaction prompt
	local prompt = Instance.new("ProximityPrompt")
	prompt.Name = "InteractionPrompt"
	prompt.ActionText = "Shop at " .. shopData.name
	prompt.KeyboardKeyCode = Enum.KeyCode.E
	prompt.HoldDuration = 0
	prompt.MaxActivationDistance = 10
	prompt.Parent = head
	
	prompt.Triggered:Connect(function(player)
		OpenShop:FireClient(player, shopData)
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
		{Position = shopData.shopkeeperPosition + Vector3.new(0, 0.5, 0)}
	)
	floatTween:Play()
	
	return npc
end

-- ============================================
-- PURCHASE ITEM
-- ============================================
local function purchaseItem(player, shopName, itemName)
	if not player or not player.Parent then return false, "Player not found" end
	
	-- Find shop data
	local shopData = nil
	for _, shop in ipairs(SHOP_CONFIG) do
		if shop.name == shopName then
			shopData = shop
			break
		end
	end
	
	if not shopData then
		return false, "Shop not found"
	end
	
	-- Find item
	local itemData = nil
	for _, item in ipairs(shopData.items) do
		if item.name == itemName then
			itemData = item
			break
		end
	end
	
	if not itemData then
		return false, "Item not found"
	end
	
	-- Get player data
	local playerData = _G.PlayerDataManager and _G.PlayerDataManager.GetPlayerData(player)
	if not playerData then
		return false, "Player data not found"
	end
	
	-- Check if player has enough coins
	local totalCoins = (playerData.coins or 0) + (playerData.bankBalance or 0)
	if totalCoins < itemData.price then
		return false, "Not enough coins! Need " .. itemData.price .. " coins"
	end
	
	-- Deduct coins (prefer wallet, then bank)
	local remaining = itemData.price
	if (playerData.coins or 0) >= remaining then
		playerData.coins = (playerData.coins or 0) - remaining
		remaining = 0
	else
		remaining = remaining - (playerData.coins or 0)
		playerData.coins = 0
		if (playerData.bankBalance or 0) >= remaining then
			playerData.bankBalance = (playerData.bankBalance or 0) - remaining
			remaining = 0
		else
			return false, "Not enough coins!"
		end
	end
	
	-- Add item to inventory
	if not playerData.inventory then
		playerData.inventory = {}
	end
	table.insert(playerData.inventory, {
		name = itemData.name,
		type = itemData.type,
		purchasedAt = os.time(),
	})
	
	-- Save data
	local DataStoreManager = require(ReplicatedStorage:WaitForChild("Modules"):WaitForChild("DataStoreManager"))
	DataStoreManager.SavePlayerData(player, playerData)
	
	-- Update client
	local UpdateStats = getOrCreateEvent("UpdateStats")
	UpdateStats:FireClient(player, playerData)
	
	print("✅ " .. player.Name .. " purchased " .. itemName .. " from " .. shopName)
	
	return true, "Purchased " .. itemName .. "!"
end

-- ============================================
-- REMOTE EVENT HANDLERS
-- ============================================
PurchaseShopItem.OnServerEvent:Connect(function(player, shopName, itemName)
	local success, message = purchaseItem(player, shopName, itemName)
	PurchaseShopItem:FireClient(player, success, message)
end)

-- ============================================
-- INITIALIZATION
-- ============================================
spawn(function()
	wait(2) -- Wait for workspace to load
	for _, shopData in ipairs(SHOP_CONFIG) do
		createShopBuilding(shopData)
		wait(0.5)
		if ENABLE_SHOPKEEPER_NPCS then
		createShopkeeperNPC(shopData)
		end
	end
end)

-- ============================================
-- EXPORT API
-- ============================================
_G.ShopManager = {
	GetShopConfig = function()
		return SHOP_CONFIG
	end,
	PurchaseItem = purchaseItem,
}

print("✅ Shop Manager initialized")
print("   - " .. #SHOP_CONFIG .. " shops created")
