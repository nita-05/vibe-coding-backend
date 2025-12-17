-- CoinEffect.client.lua
-- Visual effects when collecting coins
-- Place in StarterPlayer/StarterPlayerScripts

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

-- ============================================
-- REMOTE EVENTS
-- ============================================
local Events = ReplicatedStorage:FindFirstChild("RemoteEvents")
if not Events then
	Events = Instance.new("Folder")
	Events.Name = "RemoteEvents"
	Events.Parent = ReplicatedStorage
end

local ShowCoinEffect = Events:FindFirstChild("ShowCoinEffect")
if not ShowCoinEffect then
	ShowCoinEffect = Instance.new("RemoteEvent")
	ShowCoinEffect.Name = "ShowCoinEffect"
	ShowCoinEffect.Parent = Events
end

-- ============================================
-- COIN EFFECT UI
-- ============================================
local screenGui = Instance.new("ScreenGui")
screenGui.Name = "CoinEffectUI"
screenGui.ResetOnSpawn = false
screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
screenGui.DisplayOrder = 100
screenGui.Parent = playerGui

-- ============================================
-- SHOW COIN EFFECT
-- ============================================
ShowCoinEffect.OnClientEvent:Connect(function(coinValue, tierName, position)
	-- Create floating text
	local textLabel = Instance.new("TextLabel")
	textLabel.Name = "CoinText"
	textLabel.Size = UDim2.new(0, 200, 0, 50)
	textLabel.Position = UDim2.new(0.5, -100, 0.5, 0)
	textLabel.BackgroundTransparency = 1
	textLabel.Text = "+" .. coinValue .. " Coins"
	textLabel.TextColor3 = Color3.fromRGB(255, 215, 0) -- Gold
	textLabel.TextSize = 32
	textLabel.Font = Enum.Font.GothamBold
	textLabel.TextStrokeTransparency = 0
	textLabel.TextStrokeColor3 = Color3.fromRGB(0, 0, 0)
	textLabel.Parent = screenGui
	
	-- Tier-based color
	if tierName == "Bronze" then
		textLabel.TextColor3 = Color3.fromRGB(205, 127, 50)
	elseif tierName == "Silver" then
		textLabel.TextColor3 = Color3.fromRGB(192, 192, 192)
	elseif tierName == "Gold" then
		textLabel.TextColor3 = Color3.fromRGB(255, 215, 0)
	elseif tierName == "Event" then
		textLabel.TextColor3 = Color3.fromRGB(255, 100, 255)
	end
	
	-- Animate
	local startPos = UDim2.new(0.5, -100, 0.5, 0)
	local endPos = UDim2.new(0.5, -100, 0.3, 0)
	
	textLabel.Position = startPos
	textLabel.TextTransparency = 0
	
	local tween = TweenService:Create(
		textLabel,
		TweenInfo.new(1.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
		{
			Position = endPos,
			TextTransparency = 1,
			TextSize = 40
		}
	)
	
	tween:Play()
	tween.Completed:Connect(function()
		textLabel:Destroy()
	end)
end)

print("✅ Coin Effect UI initialized")
