-- QuestUI.client.lua
-- Shows quest interface
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
local OpenQuest = Events:FindFirstChild("OpenQuest")
if not OpenQuest then
	OpenQuest = Instance.new("RemoteEvent")
	OpenQuest.Name = "OpenQuest"
	OpenQuest.Parent = Events
end

-- ============================================
-- QUEST UI
-- ============================================
local screenGui = Instance.new("ScreenGui")
screenGui.Name = "QuestUI"
screenGui.ResetOnSpawn = false
screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
screenGui.DisplayOrder = 55
screenGui.Enabled = false
screenGui.Parent = playerGui

local questFrame = Instance.new("Frame")
questFrame.Name = "QuestFrame"
questFrame.Size = UDim2.new(0, 400, 0, 300)
questFrame.Position = UDim2.new(0.5, -200, 0.5, -150)
questFrame.BackgroundColor3 = Color3.fromRGB(40, 40, 40)
questFrame.BorderSizePixel = 0
questFrame.Parent = screenGui

local questCorner = Instance.new("UICorner")
questCorner.CornerRadius = UDim.new(0, 15)
questCorner.Parent = questFrame

local title = Instance.new("TextLabel")
title.Name = "Title"
title.Size = UDim2.new(1, 0, 0, 50)
title.Position = UDim2.new(0, 0, 0, 0)
title.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
title.Text = "📋 QUEST"
title.TextColor3 = Color3.fromRGB(255, 255, 255)
title.TextSize = 24
title.Font = Enum.Font.GothamBold
title.Parent = questFrame

local titleCorner = Instance.new("UICorner")
titleCorner.CornerRadius = UDim.new(0, 15)
titleCorner.Parent = title

local questTitle = Instance.new("TextLabel")
questTitle.Name = "QuestTitle"
questTitle.Size = UDim2.new(1, -20, 0, 40)
questTitle.Position = UDim2.new(0, 10, 0, 60)
questTitle.BackgroundTransparency = 1
questTitle.Text = "Quest Name"
questTitle.TextColor3 = Color3.fromRGB(255, 255, 255)
questTitle.TextSize = 20
questTitle.Font = Enum.Font.GothamBold
questTitle.TextXAlignment = Enum.TextXAlignment.Left
questTitle.Parent = questFrame

local questDesc = Instance.new("TextLabel")
questDesc.Name = "QuestDesc"
questDesc.Size = UDim2.new(1, -20, 0, 80)
questDesc.Position = UDim2.new(0, 10, 0, 105)
questDesc.BackgroundTransparency = 1
questDesc.Text = "Quest description"
questDesc.TextColor3 = Color3.fromRGB(200, 200, 200)
questDesc.TextSize = 16
questDesc.Font = Enum.Font.Gotham
questDesc.TextXAlignment = Enum.TextXAlignment.Left
questDesc.TextYAlignment = Enum.TextYAlignment.Top
questDesc.TextWrapped = true
questDesc.Parent = questFrame

local rewardLabel = Instance.new("TextLabel")
rewardLabel.Name = "RewardLabel"
rewardLabel.Size = UDim2.new(1, -20, 0, 30)
rewardLabel.Position = UDim2.new(0, 10, 0, 190)
rewardLabel.BackgroundTransparency = 1
rewardLabel.Text = "Reward: 0 Points"
rewardLabel.TextColor3 = Color3.fromRGB(255, 215, 0)
rewardLabel.TextSize = 18
rewardLabel.Font = Enum.Font.GothamBold
rewardLabel.TextXAlignment = Enum.TextXAlignment.Left
rewardLabel.Parent = questFrame

local acceptButton = Instance.new("TextButton")
acceptButton.Name = "AcceptButton"
acceptButton.Size = UDim2.new(0, 150, 0, 40)
acceptButton.Position = UDim2.new(0.5, -160, 1, -50)
acceptButton.BackgroundColor3 = Color3.fromRGB(50, 200, 50)
acceptButton.Text = "Accept"
acceptButton.TextColor3 = Color3.fromRGB(255, 255, 255)
acceptButton.TextSize = 18
acceptButton.Font = Enum.Font.GothamBold
acceptButton.Parent = questFrame

local acceptCorner = Instance.new("UICorner")
acceptCorner.CornerRadius = UDim.new(0, 8)
acceptCorner.Parent = acceptButton

local closeButton = Instance.new("TextButton")
closeButton.Name = "CloseButton"
closeButton.Size = UDim2.new(0, 150, 0, 40)
closeButton.Position = UDim2.new(0.5, 10, 1, -50)
closeButton.BackgroundColor3 = Color3.fromRGB(200, 50, 50)
closeButton.Text = "Close"
closeButton.TextColor3 = Color3.fromRGB(255, 255, 255)
closeButton.TextSize = 18
closeButton.Font = Enum.Font.GothamBold
closeButton.Parent = questFrame

local closeCorner = Instance.new("UICorner")
closeCorner.CornerRadius = UDim.new(0, 8)
closeCorner.Parent = closeButton

closeButton.MouseButton1Click:Connect(function()
	screenGui.Enabled = false
end)

acceptButton.MouseButton1Click:Connect(function()
	-- Accept quest (can be expanded with quest tracking)
	print("✅ Quest accepted!")
	screenGui.Enabled = false
end)

OpenQuest.OnClientEvent:Connect(function(quest)
	if quest then
		questTitle.Text = quest.title or "Quest"
		questDesc.Text = quest.description or "No description"
		rewardLabel.Text = "Reward: " .. tostring(quest.reward or 0) .. " Points"
		screenGui.Enabled = true
		
		-- Animate in
		questFrame.Size = UDim2.new(0, 0, 0, 0)
		questFrame.Position = UDim2.new(0.5, 0, 0.5, 0)
		TweenService:Create(
			questFrame,
			TweenInfo.new(0.3, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
			{Size = UDim2.new(0, 400, 0, 300), Position = UDim2.new(0.5, -200, 0.5, -150)}
		):Play()
	end
end)

print("✅ Quest UI initialized")
