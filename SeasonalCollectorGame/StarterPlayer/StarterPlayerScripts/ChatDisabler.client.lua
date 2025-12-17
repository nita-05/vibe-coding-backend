-- ChatDisabler.client.lua
-- Hides the Roblox chat UI on the client side
-- Place in StarterPlayer/StarterPlayerScripts

local Players = game:GetService("Players")
local StarterGui = game:GetService("StarterGui")
local TextChatService = game:GetService("TextChatService")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

-- Method 1: Hide chat using StarterGui (works for classic chat)
StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Chat, false)

-- Method 2: Hide TextChatService UI (works for new chat system)
if TextChatService then
	-- Wait for chat UI to load
	wait(1)
	
	-- Find and hide TextChatService UI elements
	local chatUI = playerGui:FindFirstChild("Chat")
	if chatUI then
		chatUI.Enabled = false
	end
	
	-- Hide TextChatService's main UI
	local textChatUI = TextChatService:FindFirstChild("ChatWindow")
	if textChatUI then
		textChatUI.Visible = false
	end
	
	-- Hide chat input
	local chatInput = TextChatService:FindFirstChild("ChatInputBar")
	if chatInput then
		chatInput.Visible = false
	end
end

-- Method 3: Hide chat UI when it's added
playerGui.ChildAdded:Connect(function(child)
	if child.Name == "Chat" then
		child.Enabled = false
	end
end)

-- Also hide any existing chat UI
if playerGui:FindFirstChild("Chat") then
	playerGui.Chat.Enabled = false
end

print("✅ Chat UI disabled")
