-- NPCDialogUI.client.lua
-- Shows NPC dialog when interacting
-- Place in StarterPlayer/StarterPlayerScripts

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local GuiService = game:GetService("GuiService")

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
local ShowNPCDialog = Events:FindFirstChild("ShowNPCDialog")
if not ShowNPCDialog then
	ShowNPCDialog = Instance.new("RemoteEvent")
	ShowNPCDialog.Name = "ShowNPCDialog"
	ShowNPCDialog.Parent = Events
end

local AIChatRequest = Events:FindFirstChild("AIChatRequest")
if not AIChatRequest then
	AIChatRequest = Instance.new("RemoteEvent")
	AIChatRequest.Name = "AIChatRequest"
	AIChatRequest.Parent = Events
end

local AIChatResponse = Events:FindFirstChild("AIChatResponse")
if not AIChatResponse then
	AIChatResponse = Instance.new("RemoteEvent")
	AIChatResponse.Name = "AIChatResponse"
	AIChatResponse.Parent = Events
end

-- ============================================
-- DIALOG UI
-- ============================================
local screenGui = Instance.new("ScreenGui")
screenGui.Name = "NPCDialogUI"
screenGui.ResetOnSpawn = false
screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
screenGui.DisplayOrder = 60
screenGui.Enabled = false
screenGui.Parent = playerGui

local dialogFrame = Instance.new("Frame")
dialogFrame.Name = "DialogFrame"
dialogFrame.Size = UDim2.new(0, 500, 0, 350) -- Increased height for better visibility
dialogFrame.Position = UDim2.new(0.5, -250, 0.5, -175) -- Centered on screen
dialogFrame.BackgroundColor3 = Color3.fromRGB(40, 40, 40)
dialogFrame.BorderSizePixel = 0
dialogFrame.Parent = screenGui

-- Make responsive for mobile/PC
local function updateDialogSize()
	local screenSize = workspace.CurrentCamera.ViewportSize
	
	-- Adjust for mobile (smaller screens)
	if screenSize.X < 800 then
		dialogFrame.Size = UDim2.new(0.9, 0, 0, 350)
		dialogFrame.Position = UDim2.new(0.5, 0, 0.5, -175)
	else
		dialogFrame.Size = UDim2.new(0, 500, 0, 350)
		dialogFrame.Position = UDim2.new(0.5, -250, 0.5, -175)
	end
end

-- Update on screen resize
workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(updateDialogSize)
updateDialogSize()

local dialogCorner = Instance.new("UICorner")
dialogCorner.CornerRadius = UDim.new(0, 15)
dialogCorner.Parent = dialogFrame

local titleLabel = Instance.new("TextLabel")
titleLabel.Name = "Title"
titleLabel.Size = UDim2.new(1, -20, 0, 40)
titleLabel.Position = UDim2.new(0, 10, 0, 10)
titleLabel.BackgroundTransparency = 1
titleLabel.Text = "NPC Name"
titleLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
titleLabel.TextSize = 22
titleLabel.Font = Enum.Font.GothamBold
titleLabel.TextXAlignment = Enum.TextXAlignment.Left
titleLabel.Parent = dialogFrame

-- Scrolling frame for messages
local scrollFrame = Instance.new("ScrollingFrame")
scrollFrame.Name = "MessageScroll"
scrollFrame.Size = UDim2.new(1, -20, 1, -100)
scrollFrame.Position = UDim2.new(0, 10, 0, 55)
scrollFrame.BackgroundTransparency = 1
scrollFrame.BorderSizePixel = 0
scrollFrame.ScrollBarThickness = 6
scrollFrame.ScrollBarImageColor3 = Color3.fromRGB(100, 100, 100)
scrollFrame.CanvasSize = UDim2.new(0, 0, 0, 0)
scrollFrame.Parent = dialogFrame

local messageLabel = Instance.new("TextLabel")
messageLabel.Name = "Message"
messageLabel.Size = UDim2.new(1, -10, 0, 0) -- Auto-size height
messageLabel.Position = UDim2.new(0, 5, 0, 5)
messageLabel.BackgroundTransparency = 1
messageLabel.Text = "Message here"
messageLabel.TextColor3 = Color3.fromRGB(200, 200, 200)
messageLabel.TextSize = 16
messageLabel.Font = Enum.Font.Gotham
messageLabel.TextXAlignment = Enum.TextXAlignment.Left
messageLabel.TextYAlignment = Enum.TextYAlignment.Top
messageLabel.TextWrapped = true
messageLabel.TextSize = 16
messageLabel.RichText = true
messageLabel.Parent = scrollFrame

-- AI chat input (hidden unless mode = "ai")
local inputBox = Instance.new("TextBox")
inputBox.Name = "AIInput"
inputBox.Size = UDim2.new(1, -140, 0, 35)
inputBox.Position = UDim2.new(0, 10, 1, -45)
inputBox.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
inputBox.TextColor3 = Color3.fromRGB(255, 255, 255)
inputBox.PlaceholderText = "Type your question..."
inputBox.PlaceholderColor3 = Color3.fromRGB(160, 160, 160)
inputBox.TextSize = 14
inputBox.Font = Enum.Font.Gotham
inputBox.ClearTextOnFocus = false
inputBox.Visible = false
inputBox.Parent = dialogFrame

local inputCorner = Instance.new("UICorner")
inputCorner.CornerRadius = UDim.new(0, 8)
inputCorner.Parent = inputBox

local sendButton = Instance.new("TextButton")
sendButton.Name = "SendButton"
sendButton.Size = UDim2.new(0, 80, 0, 35)
sendButton.Position = UDim2.new(1, -90, 1, -45)
sendButton.BackgroundColor3 = Color3.fromRGB(70, 130, 255)
sendButton.Text = "Send"
sendButton.TextColor3 = Color3.fromRGB(255, 255, 255)
sendButton.TextSize = 16
sendButton.Font = Enum.Font.GothamBold
sendButton.Visible = false
sendButton.Parent = dialogFrame

local sendCorner = Instance.new("UICorner")
sendCorner.CornerRadius = UDim.new(0, 8)
sendCorner.Parent = sendButton

local closeButton = Instance.new("TextButton")
closeButton.Name = "CloseButton"
closeButton.Size = UDim2.new(0, 100, 0, 35)
closeButton.Position = UDim2.new(0.5, -50, 1, -45)
closeButton.BackgroundColor3 = Color3.fromRGB(50, 200, 50)
closeButton.Text = "Close"
closeButton.TextColor3 = Color3.fromRGB(255, 255, 255)
closeButton.TextSize = 16
closeButton.Font = Enum.Font.GothamBold
closeButton.Parent = dialogFrame

local closeCorner = Instance.new("UICorner")
closeCorner.CornerRadius = UDim.new(0, 8)
closeCorner.Parent = closeButton

closeButton.MouseButton1Click:Connect(function()
	screenGui.Enabled = false
end)

local chatMode = "static" -- "static" | "ai"
local function appendLine(text: string)
	local current = messageLabel.Text or ""
	if current == "" then
		messageLabel.Text = text
	else
		messageLabel.Text = current .. "\n\n" .. text
	end
	
	-- Update canvas size for scrolling
	local textBounds = messageLabel.TextBounds
	messageLabel.Size = UDim2.new(1, -10, 0, math.max(textBounds.Y + 10, 50))
	scrollFrame.CanvasSize = UDim2.new(0, 0, 0, messageLabel.Size.Y.Offset + 10)
	
	-- Auto-scroll to bottom
	scrollFrame.CanvasPosition = Vector2.new(0, scrollFrame.CanvasSize.Y.Offset)
	
	-- Limit text length to prevent memory issues
	if #messageLabel.Text > 5000 then
		messageLabel.Text = messageLabel.Text:sub(-5000)
	end
end

local function setMode(mode: string)
	chatMode = mode or "static"
	if chatMode == "ai" then
		inputBox.Visible = true
		sendButton.Visible = true
		closeButton.Position = UDim2.new(0, 10, 1, -45)
		closeButton.Size = UDim2.new(0, 80, 0, 35)
		-- Adjust scroll frame size for input
		scrollFrame.Size = UDim2.new(1, -20, 1, -100)
	else
		inputBox.Visible = false
		sendButton.Visible = false
		closeButton.Position = UDim2.new(0.5, -50, 1, -45)
		closeButton.Size = UDim2.new(0, 100, 0, 35)
		-- Adjust scroll frame size without input
		scrollFrame.Size = UDim2.new(1, -20, 1, -60)
	end
end

local function sendAI()
	if chatMode ~= "ai" then return end
	local text = tostring(inputBox.Text or ""):gsub("%s+$", "")
	if text == "" then return end
	inputBox.Text = ""
	
	-- Ensure UI is visible
	if not screenGui.Enabled then
		screenGui.Enabled = true
	end
	
	appendLine("You: " .. text)
	appendLine("AI: Thinking...")
	
	-- Scroll to show the new message
	wait(0.1)
	scrollFrame.CanvasPosition = Vector2.new(0, scrollFrame.CanvasSize.Y.Offset)
	
	AIChatRequest:FireServer(text)
end

sendButton.MouseButton1Click:Connect(sendAI)
inputBox.FocusLost:Connect(function(enterPressed)
	if enterPressed then
		sendAI()
	end
end)

ShowNPCDialog.OnClientEvent:Connect(function(npcName, message, meta)
	titleLabel.Text = npcName
	messageLabel.Text = message
	
	-- Update canvas size
	local textBounds = messageLabel.TextBounds
	messageLabel.Size = UDim2.new(1, -10, 0, math.max(textBounds.Y + 10, 50))
	scrollFrame.CanvasSize = UDim2.new(0, 0, 0, messageLabel.Size.Y.Offset + 10)
	scrollFrame.CanvasPosition = Vector2.new(0, 0)

	if typeof(meta) == "table" and meta.mode == "ai" then
		setMode("ai")
	else
		setMode("static")
	end

	screenGui.Enabled = true
	
	-- Animate in with proper size
	updateDialogSize()
	local targetSize = dialogFrame.Size
	local targetPos = dialogFrame.Position
	dialogFrame.Size = UDim2.new(0, 0, 0, 0)
	dialogFrame.Position = UDim2.new(0.5, 0, 0.5, 0)
	TweenService:Create(
		dialogFrame,
		TweenInfo.new(0.3, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
		{Size = targetSize, Position = targetPos}
	):Play()
end)

AIChatResponse.OnClientEvent:Connect(function(reply)
	if chatMode ~= "ai" then return end
	if typeof(reply) ~= "string" or reply == "" then return end

	-- Ensure UI is visible
	if not screenGui.Enabled then
		screenGui.Enabled = true
	end

	local text = messageLabel.Text or ""
	if text:sub(-6) == "AI: ..." then
		messageLabel.Text = text:sub(1, -7) .. "AI: " .. reply
	else
		appendLine("AI: " .. reply)
	end
	
	-- Force update and scroll
	local textBounds = messageLabel.TextBounds
	messageLabel.Size = UDim2.new(1, -10, 0, math.max(textBounds.Y + 10, 50))
	scrollFrame.CanvasSize = UDim2.new(0, 0, 0, messageLabel.Size.Y.Offset + 10)
	
	-- Scroll to bottom to show latest message
	wait(0.1) -- Small delay to ensure text is rendered
	scrollFrame.CanvasPosition = Vector2.new(0, scrollFrame.CanvasSize.Y.Offset)
end)

print("✅ NPC Dialog UI initialized")
