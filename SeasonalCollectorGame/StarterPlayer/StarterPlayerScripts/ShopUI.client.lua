-- ShopUI.client.lua
-- Shop browsing and purchasing interface
-- Place in StarterPlayer/StarterPlayerScripts

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

-- ============================================
-- REMOTE EVENTS
-- ============================================
-- IMPORTANT: Client should NOT create RemoteEvents (can cause duplicates)
local Events = ReplicatedStorage:WaitForChild("RemoteEvents")
local OpenShop = Events:WaitForChild("OpenShop")
local PurchaseShopItem = Events:WaitForChild("PurchaseShopItem")
local UpdateStats = Events:WaitForChild("UpdateStats")

-- ============================================
-- UI SETUP
-- ============================================
local screenGui = Instance.new("ScreenGui")
screenGui.Name = "ShopUI"
screenGui.ResetOnSpawn = false
screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
screenGui.DisplayOrder = 70
screenGui.Enabled = false
screenGui.Parent = playerGui

-- Main frame
local mainFrame = Instance.new("Frame")
mainFrame.Name = "MainFrame"
mainFrame.Size = UDim2.new(0, 600, 0, 500)
mainFrame.Position = UDim2.new(0.5, -300, 0.5, -250)
mainFrame.BackgroundColor3 = Color3.fromRGB(40, 40, 50)
mainFrame.BorderSizePixel = 0
mainFrame.Parent = screenGui

local mainCorner = Instance.new("UICorner")
mainCorner.CornerRadius = UDim.new(0, 15)
mainCorner.Parent = mainFrame

local stroke = Instance.new("UIStroke")
stroke.Color = Color3.fromRGB(255, 200, 0)
stroke.Thickness = 3
stroke.Parent = mainFrame

-- Title
local titleLabel = Instance.new("TextLabel")
titleLabel.Name = "Title"
titleLabel.Size = UDim2.new(1, -20, 0, 50)
titleLabel.Position = UDim2.new(0, 10, 0, 10)
titleLabel.BackgroundTransparency = 1
titleLabel.Text = "🛒 SHOP"
titleLabel.TextColor3 = Color3.fromRGB(255, 200, 0)
titleLabel.TextSize = 28
titleLabel.Font = Enum.Font.GothamBold
titleLabel.TextXAlignment = Enum.TextXAlignment.Left
titleLabel.Parent = mainFrame

-- Close button
local closeButton = Instance.new("TextButton")
closeButton.Name = "CloseButton"
closeButton.Size = UDim2.new(0, 40, 0, 40)
closeButton.Position = UDim2.new(1, -50, 0, 10)
closeButton.BackgroundColor3 = Color3.fromRGB(200, 50, 50)
closeButton.Text = "✕"
closeButton.TextColor3 = Color3.fromRGB(255, 255, 255)
closeButton.TextSize = 24
closeButton.Font = Enum.Font.GothamBold
closeButton.Parent = mainFrame

local closeCorner = Instance.new("UICorner")
closeCorner.CornerRadius = UDim.new(0, 8)
closeCorner.Parent = closeButton

closeButton.MouseButton1Click:Connect(function()
	screenGui.Enabled = false
end)

-- Coin display
local coinLabel = Instance.new("TextLabel")
coinLabel.Name = "CoinLabel"
coinLabel.Size = UDim2.new(1, -20, 0, 30)
coinLabel.Position = UDim2.new(0, 10, 0, 60)
coinLabel.BackgroundTransparency = 1
coinLabel.Text = "💰 Coins: 0"
coinLabel.TextColor3 = Color3.fromRGB(255, 215, 0)
coinLabel.TextSize = 18
coinLabel.Font = Enum.Font.GothamBold
coinLabel.TextXAlignment = Enum.TextXAlignment.Left
coinLabel.Parent = mainFrame

-- Items scroll frame
local scrollFrame = Instance.new("ScrollingFrame")
scrollFrame.Name = "ItemsScrollFrame"
scrollFrame.Size = UDim2.new(1, -20, 1, -150)
scrollFrame.Position = UDim2.new(0, 10, 0, 100)
scrollFrame.BackgroundColor3 = Color3.fromRGB(30, 30, 40)
scrollFrame.BorderSizePixel = 0
scrollFrame.ScrollBarThickness = 8
scrollFrame.Parent = mainFrame

local scrollCorner = Instance.new("UICorner")
scrollCorner.CornerRadius = UDim.new(0, 10)
scrollCorner.Parent = scrollFrame

local itemsList = Instance.new("UIListLayout")
itemsList.Padding = UDim.new(0, 10)
itemsList.SortOrder = Enum.SortOrder.LayoutOrder
itemsList.Parent = scrollFrame

-- Message label
local messageLabel = Instance.new("TextLabel")
messageLabel.Name = "MessageLabel"
messageLabel.Size = UDim2.new(1, -20, 0, 30)
messageLabel.Position = UDim2.new(0, 10, 1, -40)
messageLabel.BackgroundTransparency = 1
messageLabel.Text = ""
messageLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
messageLabel.TextSize = 14
messageLabel.Font = Enum.Font.Gotham
messageLabel.TextXAlignment = Enum.TextXAlignment.Left
messageLabel.TextWrapped = true
messageLabel.Parent = mainFrame

-- ============================================
-- FUNCTIONS
-- ============================================
local currentShopData = nil
local playerCoins = 0
local playerBankBalance = 0

local function updateCoinDisplay()
	local wallet = playerCoins
	local bank = playerBankBalance
	local total = wallet + bank
	coinLabel.Text = "💰 Coins: " .. wallet .. " (Bank: " .. bank .. " | Total: " .. total .. ")"
end

local function showMessage(text, color)
	color = color or Color3.fromRGB(255, 255, 255)
	messageLabel.TextColor3 = color
	messageLabel.Text = text
	
	spawn(function()
		wait(3)
		if messageLabel.Text == text then
			messageLabel.Text = ""
		end
	end)
end

local function createItemFrame(itemData, index)
	local itemFrame = Instance.new("Frame")
	itemFrame.Name = "Item_" .. index
	itemFrame.Size = UDim2.new(1, -20, 0, 100)
	itemFrame.BackgroundColor3 = Color3.fromRGB(50, 50, 60)
	itemFrame.BorderSizePixel = 0
	itemFrame.Parent = scrollFrame
	
	local itemCorner = Instance.new("UICorner")
	itemCorner.CornerRadius = UDim.new(0, 8)
	itemCorner.Parent = itemFrame
	
	-- Item icon
	local iconLabel = Instance.new("TextLabel")
	iconLabel.Name = "Icon"
	iconLabel.Size = UDim2.new(0, 60, 0, 60)
	iconLabel.Position = UDim2.new(0, 10, 0, 20)
	iconLabel.BackgroundTransparency = 1
	iconLabel.Text = itemData.icon or "📦"
	iconLabel.TextSize = 40
	iconLabel.Font = Enum.Font.GothamBold
	iconLabel.Parent = itemFrame
	
	-- Item name
	local nameLabel = Instance.new("TextLabel")
	nameLabel.Name = "Name"
	nameLabel.Size = UDim2.new(0, 300, 0, 25)
	nameLabel.Position = UDim2.new(0, 80, 0, 15)
	nameLabel.BackgroundTransparency = 1
	nameLabel.Text = itemData.name
	nameLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
	nameLabel.TextSize = 18
	nameLabel.Font = Enum.Font.GothamBold
	nameLabel.TextXAlignment = Enum.TextXAlignment.Left
	nameLabel.Parent = itemFrame
	
	-- Item description
	local descLabel = Instance.new("TextLabel")
	descLabel.Name = "Description"
	descLabel.Size = UDim2.new(0, 300, 0, 40)
	descLabel.Position = UDim2.new(0, 80, 0, 40)
	descLabel.BackgroundTransparency = 1
	descLabel.Text = itemData.description
	descLabel.TextColor3 = Color3.fromRGB(200, 200, 200)
	descLabel.TextSize = 14
	descLabel.Font = Enum.Font.Gotham
	descLabel.TextXAlignment = Enum.TextXAlignment.Left
	descLabel.TextYAlignment = Enum.TextYAlignment.Top
	descLabel.TextWrapped = true
	descLabel.Parent = itemFrame
	
	-- Price
	local priceLabel = Instance.new("TextLabel")
	priceLabel.Name = "Price"
	priceLabel.Size = UDim2.new(0, 100, 0, 30)
	priceLabel.Position = UDim2.new(1, -120, 0, 15)
	priceLabel.BackgroundTransparency = 1
	priceLabel.Text = "💰 " .. itemData.price
	priceLabel.TextColor3 = Color3.fromRGB(255, 215, 0)
	priceLabel.TextSize = 18
	priceLabel.Font = Enum.Font.GothamBold
	priceLabel.TextXAlignment = Enum.TextXAlignment.Right
	priceLabel.Parent = itemFrame
	
	-- Buy button
	local buyButton = Instance.new("TextButton")
	buyButton.Name = "BuyButton"
	buyButton.Size = UDim2.new(0, 100, 0, 35)
	buyButton.Position = UDim2.new(1, -120, 0, 55)
	buyButton.BackgroundColor3 = Color3.fromRGB(50, 200, 50)
	buyButton.Text = "Buy"
	buyButton.TextColor3 = Color3.fromRGB(255, 255, 255)
	buyButton.TextSize = 16
	buyButton.Font = Enum.Font.GothamBold
	buyButton.Parent = itemFrame
	
	local buyCorner = Instance.new("UICorner")
	buyCorner.CornerRadius = UDim.new(0, 8)
	buyCorner.Parent = buyButton
	
	-- Check if player can afford (wallet + bank)
	local totalCoins = playerCoins + playerBankBalance
	local canAfford = totalCoins >= itemData.price
	if not canAfford then
		buyButton.BackgroundColor3 = Color3.fromRGB(100, 100, 100)
		buyButton.Text = "Can't Afford"
	end
	
	buyButton.MouseButton1Click:Connect(function()
		if canAfford then
			PurchaseShopItem:FireServer(currentShopData.name, itemData.name)
		else
			showMessage("Not enough coins! Need " .. itemData.price .. " coins", Color3.fromRGB(255, 100, 100))
		end
	end)
	
	return itemFrame
end

local function displayShop(shopData)
	currentShopData = shopData
	
	-- Clear existing items
	for _, child in ipairs(scrollFrame:GetChildren()) do
		if child:IsA("Frame") then
			child:Destroy()
		end
	end
	
	-- Update title
	titleLabel.Text = "🛒 " .. shopData.name
	
	-- Create item frames
	for i, item in ipairs(shopData.items) do
		local itemFrame = createItemFrame(item, i)
		itemFrame.LayoutOrder = i
	end
	
	-- Update scroll frame canvas size
	wait(0.1) -- Wait for layout to update
	scrollFrame.CanvasSize = UDim2.new(0, 0, 0, itemsList.AbsoluteContentSize.Y + 20)
	
	-- Update when layout changes
	local connection
	connection = itemsList:GetPropertyChangedSignal("AbsoluteContentSize"):Connect(function()
		scrollFrame.CanvasSize = UDim2.new(0, 0, 0, itemsList.AbsoluteContentSize.Y + 20)
	end)
end

-- ============================================
-- EVENT HANDLERS
-- ============================================
OpenShop.OnClientEvent:Connect(function(shopData)
	if not shopData then return end
	
	screenGui.Enabled = true
	displayShop(shopData)
	
	-- Animate in
	mainFrame.Size = UDim2.new(0, 0, 0, 0)
	mainFrame.Position = UDim2.new(0.5, 0, 0.5, 0)
	TweenService:Create(
		mainFrame,
		TweenInfo.new(0.3, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
		{Size = UDim2.new(0, 600, 0, 500), Position = UDim2.new(0.5, -300, 0.5, -250)}
	):Play()
end)

PurchaseShopItem.OnClientEvent:Connect(function(success, message)
	if success then
		showMessage(message, Color3.fromRGB(100, 255, 100))
		-- Refresh shop display
		if currentShopData then
			displayShop(currentShopData)
		end
	else
		showMessage(message, Color3.fromRGB(255, 100, 100))
	end
end)

UpdateStats.OnClientEvent:Connect(function(data)
	if data then
		playerCoins = data.coins or 0
		playerBankBalance = data.bankBalance or 0
		updateCoinDisplay()
		
		-- Refresh shop if open
		if currentShopData and screenGui.Enabled then
			displayShop(currentShopData)
		end
	end
end)

print("✅ Shop UI initialized")
