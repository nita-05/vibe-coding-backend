-- GameOverUI.client.lua
-- Shows Game Over screen and lets player restart fresh
-- Place in StarterPlayer/StarterPlayerScripts

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

local Events = ReplicatedStorage:WaitForChild("RemoteEvents")
local GameOver = Events:WaitForChild("GameOver")
local RequestRestart = Events:WaitForChild("RequestRestart")

local screenGui = Instance.new("ScreenGui")
screenGui.Name = "GameOverUI"
screenGui.ResetOnSpawn = false
screenGui.DisplayOrder = 200
screenGui.Enabled = false
screenGui.Parent = playerGui

local overlay = Instance.new("Frame")
overlay.Size = UDim2.new(1, 0, 1, 0)
overlay.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
overlay.BackgroundTransparency = 0.35
overlay.Parent = screenGui

local frame = Instance.new("Frame")
frame.Size = UDim2.new(0, 420, 0, 240)
frame.Position = UDim2.new(0.5, -210, 0.5, -120)
frame.BackgroundColor3 = Color3.fromRGB(25, 25, 35)
frame.BorderSizePixel = 0
frame.Parent = overlay

local frameCorner = Instance.new("UICorner")
frameCorner.CornerRadius = UDim.new(0, 16)
frameCorner.Parent = frame

local stroke = Instance.new("UIStroke")
stroke.Color = Color3.fromRGB(255, 80, 80)
stroke.Thickness = 3
stroke.Parent = frame

local title = Instance.new("TextLabel")
title.Size = UDim2.new(1, -30, 0, 60)
title.Position = UDim2.new(0, 15, 0, 20)
title.BackgroundTransparency = 1
title.Text = "GAME OVER"
title.TextColor3 = Color3.fromRGB(255, 80, 80)
title.TextSize = 36
title.Font = Enum.Font.GothamBlack
title.Parent = frame

local desc = Instance.new("TextLabel")
desc.Size = UDim2.new(1, -30, 0, 50)
desc.Position = UDim2.new(0, 15, 0, 90)
desc.BackgroundTransparency = 1
desc.Text = "You used all 3 lives.\nRestart to begin again from Level 1."
desc.TextColor3 = Color3.fromRGB(230, 230, 230)
desc.TextSize = 16
desc.Font = Enum.Font.Gotham

desc.TextWrapped = true
desc.Parent = frame

local restartButton = Instance.new("TextButton")
restartButton.Size = UDim2.new(1, -30, 0, 55)
restartButton.Position = UDim2.new(0, 15, 1, -80)
restartButton.BackgroundColor3 = Color3.fromRGB(50, 200, 50)
restartButton.BorderSizePixel = 0
restartButton.Text = "Restart"
restartButton.TextColor3 = Color3.fromRGB(255, 255, 255)
restartButton.TextSize = 22
restartButton.Font = Enum.Font.GothamBold
restartButton.Parent = frame

local btnCorner = Instance.new("UICorner")
btnCorner.CornerRadius = UDim.new(0, 12)
btnCorner.Parent = restartButton

local busy = false

local function show()
	busy = false
	restartButton.Text = "Restart"
	screenGui.Enabled = true

	-- simple pop-in animation
	frame.Size = UDim2.new(0, 0, 0, 0)
	frame.Position = UDim2.new(0.5, 0, 0.5, 0)
	TweenService:Create(
		frame,
		TweenInfo.new(0.25, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
		{Size = UDim2.new(0, 420, 0, 240), Position = UDim2.new(0.5, -210, 0.5, -120)}
	):Play()
end

local function hide()
	screenGui.Enabled = false
end

GameOver.OnClientEvent:Connect(function()
	show()
end)

restartButton.MouseButton1Click:Connect(function()
	if busy then return end
	busy = true
	restartButton.Text = "Restarting..."
	RequestRestart:FireServer()
	hide()
end)

player.CharacterAdded:Connect(function()
	-- safety: if you respawn for any reason, hide the overlay
	hide()
end)

print("✅ GameOver UI initialized")
