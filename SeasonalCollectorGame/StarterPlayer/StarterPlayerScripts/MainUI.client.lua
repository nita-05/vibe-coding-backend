-- MainUI.client.lua
-- Main game UI: Event status, progress, stats
-- Place in StarterPlayer/StarterPlayerScripts

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

-- ============================================
-- REMOTE EVENTS
-- ============================================
-- IMPORTANT: Client should NOT create RemoteEvents (can break server communication).
local Events = ReplicatedStorage:WaitForChild("RemoteEvents")

-- Not all of these are always used, but we still bind safely.
local UpdateStats = Events:WaitForChild("UpdateStats")
local UpdateLives = Events:WaitForChild("UpdateLives")
local LifeMessage = Events:WaitForChild("LifeMessage")

-- ============================================
-- UI SETUP
-- ============================================
local screenGui = Instance.new("ScreenGui")
screenGui.Name = "MainUI"
screenGui.ResetOnSpawn = false
screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
screenGui.Parent = playerGui

-- ============================================
-- EVENT STATUS PANEL (REMOVED - User Request)
-- ============================================
-- Event panel removed to reduce UI clutter

-- ============================================
-- STATS PANEL
-- ============================================
local statsPanel = Instance.new("Frame")
statsPanel.Name = "StatsPanel"
statsPanel.Size = UDim2.new(0, 250, 0, 210) -- Increased height for bank + level + lives
statsPanel.Position = UDim2.new(1, -260, 0, 10)
statsPanel.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
statsPanel.BackgroundTransparency = 0.2
statsPanel.BorderSizePixel = 0
statsPanel.Parent = screenGui

local statsCorner = Instance.new("UICorner")
statsCorner.CornerRadius = UDim.new(0, 10)
statsCorner.Parent = statsPanel

local statsTitle = Instance.new("TextLabel")
statsTitle.Name = "StatsTitle"
statsTitle.Size = UDim2.new(1, -20, 0, 30)
statsTitle.Position = UDim2.new(0, 10, 0, 10)
statsTitle.BackgroundTransparency = 1
statsTitle.Text = "📊 STATS"
statsTitle.TextColor3 = Color3.fromRGB(255, 255, 255)
statsTitle.TextSize = 18
statsTitle.Font = Enum.Font.GothamBold
statsTitle.TextXAlignment = Enum.TextXAlignment.Left
statsTitle.Parent = statsPanel

local pointsLabel = Instance.new("TextLabel")
pointsLabel.Name = "PointsLabel"
pointsLabel.Size = UDim2.new(1, -20, 0, 25)
pointsLabel.Position = UDim2.new(0, 10, 0, 45)
pointsLabel.BackgroundTransparency = 1
pointsLabel.Text = "Points: 0"
pointsLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
pointsLabel.TextSize = 16
pointsLabel.Font = Enum.Font.Gotham
pointsLabel.TextXAlignment = Enum.TextXAlignment.Left
pointsLabel.Parent = statsPanel

local collectedLabel = Instance.new("TextLabel")
collectedLabel.Name = "CollectedLabel"
collectedLabel.Size = UDim2.new(1, -20, 0, 25)
collectedLabel.Position = UDim2.new(0, 10, 0, 75)
collectedLabel.BackgroundTransparency = 1
collectedLabel.Text = "Collected: 0"
collectedLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
collectedLabel.TextSize = 16
collectedLabel.Font = Enum.Font.Gotham
collectedLabel.TextXAlignment = Enum.TextXAlignment.Left
collectedLabel.Parent = statsPanel

local coinsLabel = Instance.new("TextLabel")
coinsLabel.Name = "CoinsLabel"
coinsLabel.Size = UDim2.new(1, -20, 0, 25)
coinsLabel.Position = UDim2.new(0, 10, 0, 105)
coinsLabel.BackgroundTransparency = 1
coinsLabel.Text = "💰 Coins: 0"
coinsLabel.TextColor3 = Color3.fromRGB(255, 215, 0)
coinsLabel.TextSize = 16
coinsLabel.Font = Enum.Font.GothamBold
coinsLabel.TextXAlignment = Enum.TextXAlignment.Left
coinsLabel.Parent = statsPanel

local bankLabel = Instance.new("TextLabel")
bankLabel.Name = "BankLabel"
bankLabel.Size = UDim2.new(1, -20, 0, 25)
bankLabel.Position = UDim2.new(0, 10, 0, 130)
bankLabel.BackgroundTransparency = 1
bankLabel.Text = "🏦 Bank: 0"
bankLabel.TextColor3 = Color3.fromRGB(100, 200, 255)
bankLabel.TextSize = 16
bankLabel.Font = Enum.Font.GothamBold
bankLabel.TextXAlignment = Enum.TextXAlignment.Left
bankLabel.Parent = statsPanel

local levelLabel = Instance.new("TextLabel")
levelLabel.Name = "LevelLabel"
levelLabel.Size = UDim2.new(1, -20, 0, 25)
levelLabel.Position = UDim2.new(0, 10, 0, 155)
levelLabel.BackgroundTransparency = 1
levelLabel.Text = "⭐ Level: 1 (0/100 XP)"
levelLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
levelLabel.TextSize = 16
levelLabel.Font = Enum.Font.GothamBold
levelLabel.TextXAlignment = Enum.TextXAlignment.Left
levelLabel.Parent = statsPanel

local livesLabel = Instance.new("TextLabel")
livesLabel.Name = "LivesLabel"
livesLabel.Size = UDim2.new(1, -20, 0, 25)
livesLabel.Position = UDim2.new(0, 10, 0, 180)
livesLabel.BackgroundTransparency = 1
livesLabel.Text = "❤️ Lives: 3/3"
livesLabel.TextColor3 = Color3.fromRGB(255, 120, 120)
livesLabel.TextSize = 16
livesLabel.Font = Enum.Font.GothamBold
livesLabel.TextXAlignment = Enum.TextXAlignment.Left
livesLabel.Parent = statsPanel

-- Small toast for hazard/life messages
local lifeToast = Instance.new("TextLabel")
lifeToast.Name = "LifeToast"
lifeToast.Size = UDim2.new(0, 320, 0, 36)
lifeToast.Position = UDim2.new(0.5, -160, 0, 10)
lifeToast.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
lifeToast.BackgroundTransparency = 0.35
lifeToast.BorderSizePixel = 0
lifeToast.Text = ""
lifeToast.TextColor3 = Color3.fromRGB(255, 255, 255)
lifeToast.TextSize = 14
lifeToast.Font = Enum.Font.GothamBold
lifeToast.Visible = false
lifeToast.Parent = screenGui

local toastCorner = Instance.new("UICorner")
toastCorner.CornerRadius = UDim.new(0, 10)
toastCorner.Parent = lifeToast

local function showToast(text)
	lifeToast.Text = text
	lifeToast.Visible = true
	lifeToast.TextTransparency = 0

	task.spawn(function()
		task.wait(1.4)
		for i = 1, 10 do
			lifeToast.TextTransparency = i / 10
			task.wait(0.03)
		end
		lifeToast.Visible = false
	end)
end

-- Speed/Magnet display (REMOVED - User Request)

-- ============================================
-- UPDATE EVENT INFO (REMOVED - Event Panel Hidden)
-- ============================================
-- Event update handlers removed since event panel is hidden

-- ============================================
-- UPDATE STATS
-- ============================================
UpdateStats.OnClientEvent:Connect(function(data)
	if data then
		pointsLabel.Text = "Points: " .. tostring(data.eventPoints or 0)
		collectedLabel.Text = "Collected: " .. tostring(data.totalCollected or 0)
		local coins = tonumber(data.coins or 0) or 0
		local cap = tonumber(data.walletCapacity) or nil
		if cap then
			coinsLabel.Text = "💰 Coins: " .. tostring(coins) .. "/" .. tostring(cap)
		else
			coinsLabel.Text = "💰 Coins: " .. tostring(coins)
		end
		bankLabel.Text = "🏦 Bank: " .. tostring(data.bankBalance or 0)

		local level = tonumber(data.level or 1) or 1
		local xp = tonumber(data.xp or 0) or 0
		-- Mirror the same formula used on the server (keeps UI consistent without new remotes)
		local needed = 100 + ((level - 1) * 50) + math.floor(((level - 1) ^ 2) * 10)
		levelLabel.Text = "⭐ Level: " .. tostring(level) .. " (" .. tostring(xp) .. "/" .. tostring(needed) .. " XP)"
		
		-- Speed/Magnet display removed - User Request
	end
end)

UpdateLives.OnClientEvent:Connect(function(current, maxLives)
	current = tonumber(current) or 0
	maxLives = tonumber(maxLives) or 0
	livesLabel.Text = "❤️ Lives: " .. tostring(current) .. "/" .. tostring(maxLives)
end)

LifeMessage.OnClientEvent:Connect(function(text)
	if typeof(text) == "string" and text ~= "" then
		showToast(text)
	end
end)

print("✅ Main UI initialized")
