-- GameUI.client.lua
-- In-game HUD for endless runner (health, score, level, warnings)
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

local function getOrCreateEvent(name)
	local event = Events:FindFirstChild(name)
	if not event then
		event = Instance.new("RemoteEvent")
		event.Name = name
		event.Parent = Events
	end
	return event
end

local GameStarted = getOrCreateEvent("GameStarted")
local HitRegistered = getOrCreateEvent("HitRegistered")
local UpdateScore = getOrCreateEvent("UpdateScore")
local UpdateLevel = getOrCreateEvent("UpdateLevel")

-- ============================================
-- UI SETUP
-- ============================================
local screenGui = Instance.new("ScreenGui")
screenGui.Name = "GameUI"
screenGui.ResetOnSpawn = false
screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
screenGui.DisplayOrder = 10
screenGui.Parent = playerGui

-- Top bar (REMOVED - User Request)

-- Warning panel (hidden by default)
local warningPanel = Instance.new("Frame")
warningPanel.Name = "WarningPanel"
warningPanel.Size = UDim2.new(0, 400, 0, 100)
warningPanel.Position = UDim2.new(0.5, -200, 0.5, -50)
warningPanel.BackgroundColor3 = Color3.fromRGB(200, 50, 50)
warningPanel.BorderSizePixel = 0
warningPanel.Visible = false
warningPanel.Parent = screenGui

local warningCorner = Instance.new("UICorner")
warningCorner.CornerRadius = UDim.new(0, 10)
warningCorner.Parent = warningPanel

local warningText = Instance.new("TextLabel")
warningText.Size = UDim2.new(1, -40, 1, -40)
warningText.Position = UDim2.new(0, 20, 0, 20)
warningText.BackgroundTransparency = 1
warningText.Text = "⚠️ WARNING! ⚠️\nYou're taking damage!"
warningText.TextColor3 = Color3.fromRGB(255, 255, 255)
warningText.TextSize = 24
warningText.Font = Enum.Font.GothamBold
warningText.TextWrapped = true
warningText.Parent = warningPanel

-- ============================================
-- UPDATE HEALTH (REMOVED - User Request)
-- ============================================

-- ============================================
-- SHOW WARNING
-- ============================================
local function showWarning()
	warningPanel.Visible = true
	
	-- Pulse animation
	local pulse = TweenService:Create(
		warningPanel,
		TweenInfo.new(0.5, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true),
		{Size = UDim2.new(0, 420, 0, 110)}
	)
	pulse:Play()
	
	-- Hide after 3 seconds
	spawn(function()
		wait(3)
		pulse:Cancel()
		warningPanel.Visible = false
		warningPanel.Size = UDim2.new(0, 400, 0, 100)
	end)
end

-- ============================================
-- EVENT HANDLERS
-- ============================================
GameStarted.OnClientEvent:Connect(function(data)
	-- Score, Level, and Health removed - User Request
	-- Hide warning if visible
	warningPanel.Visible = false
end)

HitRegistered.OnClientEvent:Connect(function(data)
	-- Health bar removed - User Request
	
	if data.showWarning then
		showWarning()
	end
end)

-- UpdateScore and UpdateLevel handlers removed - User Request

print("✅ Game UI initialized")
