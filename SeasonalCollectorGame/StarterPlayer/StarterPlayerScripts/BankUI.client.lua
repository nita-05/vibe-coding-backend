-- BankUI.client.lua
-- Bank deposit/withdrawal interface
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
local OpenBank = Events:WaitForChild("OpenBank")
local DepositCoins = Events:WaitForChild("DepositCoins")
local WithdrawCoins = Events:WaitForChild("WithdrawCoins")
local UpdateStats = Events:WaitForChild("UpdateStats")

-- ============================================
-- UI SETUP
-- ============================================
local screenGui = Instance.new("ScreenGui")
screenGui.Name = "BankUI"
screenGui.ResetOnSpawn = false
screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
screenGui.DisplayOrder = 70
screenGui.Enabled = false
screenGui.Parent = playerGui

-- Main frame
local mainFrame = Instance.new("Frame")
mainFrame.Name = "MainFrame"
mainFrame.Size = UDim2.new(0, 500, 0, 400)
mainFrame.Position = UDim2.new(0.5, -250, 0.5, -200)
mainFrame.BackgroundColor3 = Color3.fromRGB(40, 40, 50)
mainFrame.BorderSizePixel = 0
mainFrame.Parent = screenGui

local mainCorner = Instance.new("UICorner")
mainCorner.CornerRadius = UDim.new(0, 15)
mainCorner.Parent = mainFrame

local stroke = Instance.new("UIStroke")
stroke.Color = Color3.fromRGB(255, 215, 0)
stroke.Thickness = 3
stroke.Parent = mainFrame

-- Title
local titleLabel = Instance.new("TextLabel")
titleLabel.Name = "Title"
titleLabel.Size = UDim2.new(1, -20, 0, 50)
titleLabel.Position = UDim2.new(0, 10, 0, 10)
titleLabel.BackgroundTransparency = 1
titleLabel.Text = "🏦 BANK"
titleLabel.TextColor3 = Color3.fromRGB(255, 215, 0)
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

-- ============================================
-- MAILBOX MODE (Deposit/Withdraw chooser)
-- ============================================
local mailboxMode = false
local lastMailboxAction = "deposit" -- "deposit" | "withdraw"

local function setMode(action)
	action = (action == "withdraw") and "withdraw" or "deposit"
	lastMailboxAction = action

	if action == "deposit" then
		depositFrame.Visible = true
		quickDepositFrame.Visible = true
		withdrawFrame.Visible = false
		quickWithdrawFrame.Visible = false
	else
		depositFrame.Visible = false
		quickDepositFrame.Visible = false
		withdrawFrame.Visible = true
		quickWithdrawFrame.Visible = true
	end
end

local function focusAction()
	if lastMailboxAction == "deposit" then
		depositInput:CaptureFocus()
	else
		withdrawInput:CaptureFocus()
	end
end

-- Modal picker shown when opened from BrickMailbox
local pickerOverlay = Instance.new("Frame")
pickerOverlay.Name = "MailboxPickerOverlay"
pickerOverlay.Size = UDim2.new(1, 0, 1, 0)
pickerOverlay.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
pickerOverlay.BackgroundTransparency = 0.35
pickerOverlay.Visible = false
pickerOverlay.ZIndex = 50
pickerOverlay.Parent = screenGui

local pickerFrame = Instance.new("Frame")
pickerFrame.Name = "MailboxPickerFrame"
pickerFrame.Size = UDim2.new(0, 360, 0, 190)
pickerFrame.Position = UDim2.new(0.5, -180, 0.5, -95)
pickerFrame.BackgroundColor3 = Color3.fromRGB(25, 25, 35)
pickerFrame.BorderSizePixel = 0
pickerFrame.ZIndex = 51
pickerFrame.Parent = pickerOverlay

local pickerCorner = Instance.new("UICorner")
pickerCorner.CornerRadius = UDim.new(0, 14)
pickerCorner.Parent = pickerFrame

local pickerStroke = Instance.new("UIStroke")
pickerStroke.Color = Color3.fromRGB(255, 215, 0)
pickerStroke.Thickness = 2
pickerStroke.Parent = pickerFrame

local pickerTitle = Instance.new("TextLabel")
pickerTitle.Size = UDim2.new(1, -20, 0, 40)
pickerTitle.Position = UDim2.new(0, 10, 0, 10)
pickerTitle.BackgroundTransparency = 1
pickerTitle.Text = "🏦 BrickMailbox"
pickerTitle.TextColor3 = Color3.fromRGB(255, 215, 0)
pickerTitle.TextSize = 22
pickerTitle.Font = Enum.Font.GothamBold
pickerTitle.TextXAlignment = Enum.TextXAlignment.Left
pickerTitle.ZIndex = 52
pickerTitle.Parent = pickerFrame

local pickerDesc = Instance.new("TextLabel")
pickerDesc.Size = UDim2.new(1, -20, 0, 30)
pickerDesc.Position = UDim2.new(0, 10, 0, 50)
pickerDesc.BackgroundTransparency = 1
pickerDesc.Text = "What do you want to do?"
pickerDesc.TextColor3 = Color3.fromRGB(220, 220, 220)
pickerDesc.TextSize = 14
pickerDesc.Font = Enum.Font.Gotham
pickerDesc.TextXAlignment = Enum.TextXAlignment.Left
pickerDesc.ZIndex = 52
pickerDesc.Parent = pickerFrame

local depositPick = Instance.new("TextButton")
depositPick.Size = UDim2.new(0.5, -15, 0, 55)
depositPick.Position = UDim2.new(0, 10, 0, 95)
depositPick.BackgroundColor3 = Color3.fromRGB(50, 200, 50)
depositPick.Text = "Deposit"
depositPick.TextColor3 = Color3.fromRGB(255, 255, 255)
depositPick.TextSize = 18
depositPick.Font = Enum.Font.GothamBold
depositPick.ZIndex = 52
depositPick.Parent = pickerFrame

local depCorner = Instance.new("UICorner")
depCorner.CornerRadius = UDim.new(0, 10)
depCorner.Parent = depositPick

local withdrawPick = Instance.new("TextButton")
withdrawPick.Size = UDim2.new(0.5, -15, 0, 55)
withdrawPick.Position = UDim2.new(0.5, 5, 0, 95)
withdrawPick.BackgroundColor3 = Color3.fromRGB(200, 50, 50)
withdrawPick.Text = "Withdraw"
withdrawPick.TextColor3 = Color3.fromRGB(255, 255, 255)
withdrawPick.TextSize = 18
withdrawPick.Font = Enum.Font.GothamBold
withdrawPick.ZIndex = 52
withdrawPick.Parent = pickerFrame

local withCorner = Instance.new("UICorner")
withCorner.CornerRadius = UDim.new(0, 10)
withCorner.Parent = withdrawPick

local pickerClose = Instance.new("TextButton")
pickerClose.Size = UDim2.new(0, 34, 0, 34)
pickerClose.Position = UDim2.new(1, -44, 0, 10)
pickerClose.BackgroundColor3 = Color3.fromRGB(60, 60, 80)
pickerClose.Text = "✕"
pickerClose.TextColor3 = Color3.fromRGB(255, 255, 255)
pickerClose.TextSize = 18
pickerClose.Font = Enum.Font.GothamBold
pickerClose.ZIndex = 52
pickerClose.Parent = pickerFrame

local pickerCloseCorner = Instance.new("UICorner")
pickerCloseCorner.CornerRadius = UDim.new(0, 8)
pickerCloseCorner.Parent = pickerClose

local function hidePicker()
	pickerOverlay.Visible = false
end

local function showPicker()
	pickerOverlay.Visible = true
end

pickerClose.MouseButton1Click:Connect(function()
	hidePicker()
	screenGui.Enabled = false
end)

depositPick.MouseButton1Click:Connect(function()
	hidePicker()
	setMode("deposit")
	focusAction()
end)

withdrawPick.MouseButton1Click:Connect(function()
	hidePicker()
	setMode("withdraw")
	focusAction()
end)

-- Balance display
local balanceFrame = Instance.new("Frame")
balanceFrame.Name = "BalanceFrame"
balanceFrame.Size = UDim2.new(1, -20, 0, 80)
balanceFrame.Position = UDim2.new(0, 10, 0, 70)
balanceFrame.BackgroundColor3 = Color3.fromRGB(30, 30, 40)
balanceFrame.BorderSizePixel = 0
balanceFrame.Parent = mainFrame

local balanceCorner = Instance.new("UICorner")
balanceCorner.CornerRadius = UDim.new(0, 10)
balanceCorner.Parent = balanceFrame

local walletLabel = Instance.new("TextLabel")
walletLabel.Name = "WalletLabel"
walletLabel.Size = UDim2.new(0.5, -5, 0, 35)
walletLabel.Position = UDim2.new(0, 10, 0, 10)
walletLabel.BackgroundTransparency = 1
walletLabel.Text = "Wallet: 0"
walletLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
walletLabel.TextSize = 18
walletLabel.Font = Enum.Font.GothamBold
walletLabel.TextXAlignment = Enum.TextXAlignment.Left
walletLabel.Parent = balanceFrame

local bankLabel = Instance.new("TextLabel")
bankLabel.Name = "BankLabel"
bankLabel.Size = UDim2.new(0.5, -5, 0, 35)
bankLabel.Position = UDim2.new(0.5, 5, 0, 10)
bankLabel.BackgroundTransparency = 1
bankLabel.Text = "Bank: 0"
bankLabel.TextColor3 = Color3.fromRGB(100, 200, 255)
bankLabel.TextSize = 18
bankLabel.Font = Enum.Font.GothamBold
bankLabel.TextXAlignment = Enum.TextXAlignment.Left
bankLabel.Parent = balanceFrame

local totalLabel = Instance.new("TextLabel")
totalLabel.Name = "TotalLabel"
totalLabel.Size = UDim2.new(1, -20, 0, 30)
totalLabel.Position = UDim2.new(0, 10, 0, 45)
totalLabel.BackgroundTransparency = 1
totalLabel.Text = "Total: 0"
totalLabel.TextColor3 = Color3.fromRGB(255, 215, 0)
totalLabel.TextSize = 16
totalLabel.Font = Enum.Font.Gotham
totalLabel.TextXAlignment = Enum.TextXAlignment.Left
totalLabel.Parent = balanceFrame

-- Deposit section
local depositFrame = Instance.new("Frame")
depositFrame.Name = "DepositFrame"
depositFrame.Size = UDim2.new(1, -20, 0, 140)
depositFrame.Position = UDim2.new(0, 10, 0, 160)
depositFrame.BackgroundColor3 = Color3.fromRGB(30, 30, 40)
depositFrame.BorderSizePixel = 0
depositFrame.Parent = mainFrame

local depositCorner = Instance.new("UICorner")
depositCorner.CornerRadius = UDim.new(0, 10)
depositCorner.Parent = depositFrame

local depositTitle = Instance.new("TextLabel")
depositTitle.Name = "DepositTitle"
depositTitle.Size = UDim2.new(1, -20, 0, 30)
depositTitle.Position = UDim2.new(0, 10, 0, 10)
depositTitle.BackgroundTransparency = 1
depositTitle.Text = "💰 Deposit Coins"
depositTitle.TextColor3 = Color3.fromRGB(100, 200, 100)
depositTitle.TextSize = 20
depositTitle.Font = Enum.Font.GothamBold
depositTitle.TextXAlignment = Enum.TextXAlignment.Left
depositTitle.Parent = depositFrame

local depositInput = Instance.new("TextBox")
depositInput.Name = "DepositInput"
depositInput.Size = UDim2.new(1, -20, 0, 40)
depositInput.Position = UDim2.new(0, 10, 0, 45)
depositInput.BackgroundColor3 = Color3.fromRGB(20, 20, 30)
depositInput.BorderSizePixel = 0
depositInput.Text = ""
depositInput.PlaceholderText = "Enter amount to deposit"
depositInput.TextColor3 = Color3.fromRGB(255, 255, 255)
depositInput.PlaceholderColor3 = Color3.fromRGB(150, 150, 150)
depositInput.TextSize = 18
depositInput.Font = Enum.Font.Gotham
depositInput.Parent = depositFrame

local depositInputCorner = Instance.new("UICorner")
depositInputCorner.CornerRadius = UDim.new(0, 8)
depositInputCorner.Parent = depositInput

local depositButton = Instance.new("TextButton")
depositButton.Name = "DepositButton"
depositButton.Size = UDim2.new(1, -20, 0, 40)
depositButton.Position = UDim2.new(0, 10, 0, 95)
depositButton.BackgroundColor3 = Color3.fromRGB(50, 200, 50)
depositButton.Text = "Deposit"
depositButton.TextColor3 = Color3.fromRGB(255, 255, 255)
depositButton.TextSize = 18
depositButton.Font = Enum.Font.GothamBold
depositButton.Parent = depositFrame

local depositButtonCorner = Instance.new("UICorner")
depositButtonCorner.CornerRadius = UDim.new(0, 8)
depositButtonCorner.Parent = depositButton

-- Withdraw section
local withdrawFrame = Instance.new("Frame")
withdrawFrame.Name = "WithdrawFrame"
withdrawFrame.Size = UDim2.new(1, -20, 0, 140)
withdrawFrame.Position = UDim2.new(0, 10, 0, 310)
withdrawFrame.BackgroundColor3 = Color3.fromRGB(30, 30, 40)
withdrawFrame.BorderSizePixel = 0
withdrawFrame.Parent = mainFrame

local withdrawCorner = Instance.new("UICorner")
withdrawCorner.CornerRadius = UDim.new(0, 10)
withdrawCorner.Parent = withdrawFrame

local withdrawTitle = Instance.new("TextLabel")
withdrawTitle.Name = "WithdrawTitle"
withdrawTitle.Size = UDim2.new(1, -20, 0, 30)
withdrawTitle.Position = UDim2.new(0, 10, 0, 10)
withdrawTitle.BackgroundTransparency = 1
withdrawTitle.Text = "💸 Withdraw Coins"
withdrawTitle.TextColor3 = Color3.fromRGB(200, 100, 100)
withdrawTitle.TextSize = 20
withdrawTitle.Font = Enum.Font.GothamBold
withdrawTitle.TextXAlignment = Enum.TextXAlignment.Left
withdrawTitle.Parent = withdrawFrame

local withdrawInput = Instance.new("TextBox")
withdrawInput.Name = "WithdrawInput"
withdrawInput.Size = UDim2.new(1, -20, 0, 40)
withdrawInput.Position = UDim2.new(0, 10, 0, 45)
withdrawInput.BackgroundColor3 = Color3.fromRGB(20, 20, 30)
withdrawInput.BorderSizePixel = 0
withdrawInput.Text = ""
withdrawInput.PlaceholderText = "Enter amount to withdraw"
withdrawInput.TextColor3 = Color3.fromRGB(255, 255, 255)
withdrawInput.PlaceholderColor3 = Color3.fromRGB(150, 150, 150)
withdrawInput.TextSize = 18
withdrawInput.Font = Enum.Font.Gotham
withdrawInput.Parent = withdrawFrame

local withdrawInputCorner = Instance.new("UICorner")
withdrawInputCorner.CornerRadius = UDim.new(0, 8)
withdrawInputCorner.Parent = withdrawInput

local withdrawButton = Instance.new("TextButton")
withdrawButton.Name = "WithdrawButton"
withdrawButton.Size = UDim2.new(1, -20, 0, 40)
withdrawButton.Position = UDim2.new(0, 10, 0, 95)
withdrawButton.BackgroundColor3 = Color3.fromRGB(200, 50, 50)
withdrawButton.Text = "Withdraw"
withdrawButton.TextColor3 = Color3.fromRGB(255, 255, 255)
withdrawButton.TextSize = 18
withdrawButton.Font = Enum.Font.GothamBold
withdrawButton.Parent = withdrawFrame

local withdrawButtonCorner = Instance.new("UICorner")
withdrawButtonCorner.CornerRadius = UDim.new(0, 8)
withdrawButtonCorner.Parent = withdrawButton

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

-- Quick deposit buttons
local quickDepositFrame = Instance.new("Frame")
quickDepositFrame.Name = "QuickDepositFrame"
quickDepositFrame.Size = UDim2.new(1, -20, 0, 35)
quickDepositFrame.Position = UDim2.new(0, 10, 0, 125)
quickDepositFrame.BackgroundTransparency = 1
quickDepositFrame.Parent = mainFrame

local function createQuickButton(text, amount, parent, isAll)
	local button = Instance.new("TextButton")
	button.Size = UDim2.new(0, 70, 1, 0)
	button.BackgroundColor3 = Color3.fromRGB(50, 150, 50)
	button.Text = text
	button.TextColor3 = Color3.fromRGB(255, 255, 255)
	button.TextSize = 14
	button.Font = Enum.Font.GothamBold
	button.Parent = parent
	
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 5)
	corner.Parent = button
	
	if isAll then
		button.MouseButton1Click:Connect(function()
			local walletAmount = tonumber(walletLabel.Text:match("%d+")) or 0
			depositInput.Text = tostring(walletAmount)
		end)
	else
		button.MouseButton1Click:Connect(function()
			depositInput.Text = tostring(amount)
		end)
	end
	
	return button
end

createQuickButton("All", 0, quickDepositFrame, true)
createQuickButton("100", 100, quickDepositFrame, false)
createQuickButton("500", 500, quickDepositFrame, false)
createQuickButton("1000", 1000, quickDepositFrame, false)

-- Position quick buttons
local quickButtons = quickDepositFrame:GetChildren()
for i, button in ipairs(quickButtons) do
	if button:IsA("TextButton") then
		button.Position = UDim2.new(0, (i - 1) * 80, 0, 0)
	end
end

-- Quick withdraw buttons
local quickWithdrawFrame = Instance.new("Frame")
quickWithdrawFrame.Name = "QuickWithdrawFrame"
quickWithdrawFrame.Size = UDim2.new(1, -20, 0, 35)
quickWithdrawFrame.Position = UDim2.new(0, 10, 0, 275)
quickWithdrawFrame.BackgroundTransparency = 1
quickWithdrawFrame.Parent = mainFrame

local function createQuickWithdrawButton(text, amount, parent, isAll)
	local button = Instance.new("TextButton")
	button.Size = UDim2.new(0, 70, 1, 0)
	button.BackgroundColor3 = Color3.fromRGB(150, 50, 50)
	button.Text = text
	button.TextColor3 = Color3.fromRGB(255, 255, 255)
	button.TextSize = 14
	button.Font = Enum.Font.GothamBold
	button.Parent = parent
	
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 5)
	corner.Parent = button
	
	if isAll then
		button.MouseButton1Click:Connect(function()
			local bankAmount = tonumber(bankLabel.Text:match("%d+")) or 0
			withdrawInput.Text = tostring(bankAmount)
		end)
	else
		button.MouseButton1Click:Connect(function()
			withdrawInput.Text = tostring(amount)
		end)
	end
	
	return button
end

createQuickWithdrawButton("All", 0, quickWithdrawFrame, true)
createQuickWithdrawButton("100", 100, quickWithdrawFrame, false)
createQuickWithdrawButton("500", 500, quickWithdrawFrame, false)
createQuickWithdrawButton("1000", 1000, quickWithdrawFrame, false)

-- Position quick withdraw buttons
local quickWithdrawButtons = quickWithdrawFrame:GetChildren()
for i, button in ipairs(quickWithdrawButtons) do
	if button:IsA("TextButton") then
		button.Position = UDim2.new(0, (i - 1) * 80, 0, 0)
	end
end

-- ============================================
-- FUNCTIONS
-- ============================================
local function updateBalance(wallet, bank)
	wallet = wallet or 0
	bank = bank or 0
	
	walletLabel.Text = "Wallet: " .. wallet
	bankLabel.Text = "Bank: " .. bank
	totalLabel.Text = "Total: " .. (wallet + bank)
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

local function closeBankUI()
	-- hide picker if it's open
	if pickerOverlay then
		pickerOverlay.Visible = false
	end
	-- release focus if player is typing
	if depositInput and depositInput:IsFocused() then
		depositInput:ReleaseFocus()
	end
	if withdrawInput and withdrawInput:IsFocused() then
		withdrawInput:ReleaseFocus()
	end
	screenGui.Enabled = false
end

-- ============================================
-- BUTTON HANDLERS
-- ============================================
depositButton.MouseButton1Click:Connect(function()
	local amount = tonumber(depositInput.Text)
	if not amount or amount <= 0 then
		showMessage("Please enter a valid amount", Color3.fromRGB(255, 100, 100))
		return
	end
	
	DepositCoins:FireServer(amount)
end)

withdrawButton.MouseButton1Click:Connect(function()
	local amount = tonumber(withdrawInput.Text)
	if not amount or amount <= 0 then
		showMessage("Please enter a valid amount", Color3.fromRGB(255, 100, 100))
		return
	end
	
	WithdrawCoins:FireServer(amount)
end)

-- Update "All" buttons (no longer needed, handled in button creation)

-- ============================================
-- EVENT HANDLERS
-- ============================================
OpenBank.OnClientEvent:Connect(function(source)
	screenGui.Enabled = true

	-- This experience uses BrickMailbox as the bank interaction.
	-- Always treat OpenBank as mailbox mode to avoid showing both sections + overlap issues.
	mailboxMode = true

	-- Show picker each time you come near the mailbox
	showPicker()
	-- Default to last action (so it remembers your preference)
	setMode(lastMailboxAction)
	
	-- Animate in
	mainFrame.Size = UDim2.new(0, 0, 0, 0)
	mainFrame.Position = UDim2.new(0.5, 0, 0.5, 0)
	TweenService:Create(
		mainFrame,
		TweenInfo.new(0.3, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
		{Size = UDim2.new(0, 500, 0, 400), Position = UDim2.new(0.5, -250, 0.5, -200)}
	):Play()
end)

DepositCoins.OnClientEvent:Connect(function(success, message)
	if success then
		showMessage(message, Color3.fromRGB(100, 255, 100))
		depositInput.Text = ""
		if mailboxMode then
			lastMailboxAction = "deposit"
		end

		-- Auto-close after a successful action
		task.delay(0.8, function()
			closeBankUI()
		end)
	else
		showMessage(message, Color3.fromRGB(255, 100, 100))
	end
end)

WithdrawCoins.OnClientEvent:Connect(function(success, message)
	if success then
		showMessage(message, Color3.fromRGB(100, 255, 100))
		withdrawInput.Text = ""
		if mailboxMode then
			lastMailboxAction = "withdraw"
		end

		-- Auto-close after a successful action
		task.delay(0.8, function()
			closeBankUI()
		end)
	else
		showMessage(message, Color3.fromRGB(255, 100, 100))
	end
end)

UpdateStats.OnClientEvent:Connect(function(data)
	if data then
		updateBalance(data.coins or 0, data.bankBalance or 0)
	end
end)

print("✅ Bank UI initialized")
