-- CoinNotification.client.lua
-- Guides players to showroom when they earn coins
-- Place in StarterPlayer/StarterPlayerScripts

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

-- ============================================
-- DISABLE COIN NOTIFICATIONS (USER REQUEST)
-- ============================================
local ENABLE_COIN_NOTIFICATIONS = false
if not ENABLE_COIN_NOTIFICATIONS then
	-- If an old UI exists (from earlier versions), remove it.
	local existing = playerGui:FindFirstChild("CoinNotificationUI")
	if existing then
		existing:Destroy()
	end
	print("🚫 Coin notifications disabled (showroom tips hidden)")
	return
end

-- ============================================
-- REMOTE EVENTS
-- ============================================
local Events = ReplicatedStorage:FindFirstChild("RemoteEvents")
if not Events then
	Events = Instance.new("Folder")
	Events.Name = "RemoteEvents"
	Events.Parent = ReplicatedStorage
end

local ShowCoinNotification = Events:FindFirstChild("ShowCoinNotification")
if not ShowCoinNotification then
	-- Client should not create RemoteEvents; leave nil if server didn't create it.
	ShowCoinNotification = nil
end

-- ============================================
-- NOTIFICATION UI
-- ============================================
local screenGui = Instance.new("ScreenGui")
screenGui.Name = "CoinNotificationUI"
screenGui.ResetOnSpawn = false
screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
screenGui.DisplayOrder = 90
screenGui.Parent = playerGui

-- Track if we've shown the showroom hint (only after 50 coins)
local hasShownShowroomHint = false
local playerTotalCoins = 0

-- ============================================
-- SHOW NOTIFICATION
-- ============================================
local function showNotification(message, showShowroomHint)
	local notificationFrame = Instance.new("Frame")
	notificationFrame.Name = "Notification"
	notificationFrame.Size = UDim2.new(0, 400, 0, 120)
	notificationFrame.Position = UDim2.new(0.5, -200, 0, -150)
	notificationFrame.BackgroundColor3 = Color3.fromRGB(30, 30, 40)
	notificationFrame.BorderSizePixel = 0
	notificationFrame.Parent = screenGui
	
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 10)
	corner.Parent = notificationFrame
	
	local stroke = Instance.new("UIStroke")
	stroke.Color = Color3.fromRGB(255, 215, 0)
	stroke.Thickness = 3
	stroke.Parent = notificationFrame
	
	-- Icon
	local icon = Instance.new("TextLabel")
	icon.Name = "Icon"
	icon.Size = UDim2.new(0, 50, 0, 50)
	icon.Position = UDim2.new(0, 10, 0, 10)
	icon.BackgroundTransparency = 1
	icon.Text = "💰"
	icon.TextSize = 40
	icon.Font = Enum.Font.GothamBold
	icon.Parent = notificationFrame
	
	-- Message
	local messageLabel = Instance.new("TextLabel")
	messageLabel.Name = "Message"
	messageLabel.Size = UDim2.new(1, -70, 0, 60)
	messageLabel.Position = UDim2.new(0, 70, 0, 10)
	messageLabel.BackgroundTransparency = 1
	messageLabel.Text = message
	messageLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
	messageLabel.TextSize = 18
	messageLabel.Font = Enum.Font.GothamBold
	messageLabel.TextXAlignment = Enum.TextXAlignment.Left
	messageLabel.TextYAlignment = Enum.TextYAlignment.Top
	messageLabel.TextWrapped = true
	messageLabel.Parent = notificationFrame
	
	-- Showroom hint (only after 50 coins)
	if showShowroomHint and playerTotalCoins >= 50 and not hasShownShowroomHint then
		hasShownShowroomHint = true
		
		local hintLabel = Instance.new("TextLabel")
		hintLabel.Name = "Hint"
		hintLabel.Size = UDim2.new(1, -20, 0, 40)
		hintLabel.Position = UDim2.new(0, 10, 0, 75)
		hintLabel.BackgroundTransparency = 1
		hintLabel.Text = "💡 Tip: Visit the Vehicle Showroom to buy your first two-wheeler!"
		hintLabel.TextColor3 = Color3.fromRGB(100, 200, 255)
		hintLabel.TextSize = 14
		hintLabel.Font = Enum.Font.Gotham
		hintLabel.TextXAlignment = Enum.TextXAlignment.Left
		hintLabel.TextYAlignment = Enum.TextYAlignment.Top
		hintLabel.TextWrapped = true
		hintLabel.Parent = notificationFrame
	end
	
	-- Animate in
	notificationFrame.Position = UDim2.new(0.5, -200, 0, -150)
	TweenService:Create(
		notificationFrame,
		TweenInfo.new(0.5, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
		{Position = UDim2.new(0.5, -200, 0, 20)}
	):Play()
	
	-- Auto-close after delay
	spawn(function()
		wait(5)
		TweenService:Create(
			notificationFrame,
			TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
			{Position = UDim2.new(0.5, -200, 0, -150), BackgroundTransparency = 1}
		):Play()
		wait(0.5)
		notificationFrame:Destroy()
	end)
end

-- ============================================
-- UPDATE COIN COUNT (from stats)
-- ============================================
local UpdateStats = Events:FindFirstChild("UpdateStats")
if UpdateStats then
	UpdateStats.OnClientEvent:Connect(function(data)
		if data and data.coins then
			playerTotalCoins = data.coins or 0
		end
	end)
end

-- ============================================
-- LISTEN FOR COIN COLLECTION
-- ============================================
local ShowCoinEffect = Events:FindFirstChild("ShowCoinEffect")
if ShowCoinEffect then
	ShowCoinEffect.OnClientEvent:Connect(function(coinValue, tierName, position)
		-- Update local coin count
		playerTotalCoins = playerTotalCoins + coinValue
		
		-- Only show notification for significant amounts (5+ coins) or when reaching milestones
		if coinValue >= 5 or playerTotalCoins == 50 then
			local message = "+" .. coinValue .. " Coins Collected!"
			-- Show showroom hint only when player reaches 50 coins
			local showHint = (playerTotalCoins >= 50)
			showNotification(message, showHint)
		end
	end)
end

-- Listen for direct notification events
ShowCoinNotification.OnClientEvent:Connect(function(message, showHint)
	showNotification(message, showHint)
end)

print("✅ Coin Notification UI initialized")
