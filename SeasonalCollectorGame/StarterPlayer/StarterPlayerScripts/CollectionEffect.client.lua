-- CollectionEffect.client.lua
-- Shows collection effects when items are collected
-- Place in StarterPlayer/StarterPlayerScripts

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

-- ============================================
-- REMOTE EVENTS
-- ============================================
-- Ensure RemoteEvents folder exists
local Events = ReplicatedStorage:FindFirstChild("RemoteEvents")
if not Events then
	Events = Instance.new("Folder")
	Events.Name = "RemoteEvents"
	Events.Parent = ReplicatedStorage
end

-- Create event if it doesn't exist
local ShowCollectionEffect = Events:FindFirstChild("ShowCollectionEffect")
if not ShowCollectionEffect then
	ShowCollectionEffect = Instance.new("RemoteEvent")
	ShowCollectionEffect.Name = "ShowCollectionEffect"
	ShowCollectionEffect.Parent = Events
end

-- ============================================
-- EFFECT UI
-- ============================================
local screenGui = Instance.new("ScreenGui")
screenGui.Name = "CollectionEffectUI"
screenGui.ResetOnSpawn = false
screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
screenGui.DisplayOrder = 100
screenGui.Parent = playerGui

ShowCollectionEffect.OnClientEvent:Connect(function(points, rarity, worldPosition)
	-- Create floating text
	local textLabel = Instance.new("TextLabel")
	textLabel.Name = "CollectionText"
	textLabel.Size = UDim2.new(0, 200, 0, 60)
	textLabel.Position = UDim2.new(0.5, -100, 0.3, 0)
	textLabel.BackgroundColor3 = Color3.fromRGB(50, 50, 50)
	textLabel.BackgroundTransparency = 0.3
	textLabel.BorderSizePixel = 0
	textLabel.Text = "+" .. points .. " Points!"
	textLabel.TextColor3 = Color3.fromRGB(100, 255, 100)
	textLabel.TextSize = 24
	textLabel.Font = Enum.Font.GothamBold
	textLabel.TextStrokeTransparency = 0.5
	textLabel.TextStrokeColor3 = Color3.fromRGB(0, 0, 0)
	textLabel.Parent = screenGui
	
	-- Rarity indicator
	if rarity == "Rare" then
		textLabel.TextColor3 = Color3.fromRGB(100, 200, 255)
	elseif rarity == "Epic" then
		textLabel.TextColor3 = Color3.fromRGB(200, 100, 255)
	elseif rarity == "Legendary" then
		textLabel.TextColor3 = Color3.fromRGB(255, 215, 0)
	end
	
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 10)
	corner.Parent = textLabel
	
	-- Animate in
	textLabel.Size = UDim2.new(0, 0, 0, 0)
	TweenService:Create(
		textLabel,
		TweenInfo.new(0.3, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
		{Size = UDim2.new(0, 200, 0, 60)}
	):Play()
	
	-- Animate up and fade
	wait(0.3)
	TweenService:Create(
		textLabel,
		TweenInfo.new(1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
		{Position = textLabel.Position - UDim2.new(0, 0, 0, 50), BackgroundTransparency = 1, TextTransparency = 1}
	):Play()
	
	wait(1)
	textLabel:Destroy()
end)

print("✅ Collection Effect UI initialized")
