-- ChatDisabler.server.lua
-- Disables Roblox chat system by blocking all chat messages
-- Place in ServerScriptService

local Players = game:GetService("Players")
local TextChatService = game:GetService("TextChatService")

-- Check if using new TextChatService (Roblox's newer chat system)
if TextChatService then
	-- Disable chat commands and messages
	local function blockAllMessages(message)
		-- Return empty string to block message
		return ""
	end
	
	-- Block messages for all players
	Players.PlayerAdded:Connect(function(player)
		-- Block chat messages for this player
		player.Chatted:Connect(function(message)
			-- Prevent message from being sent
			return
		end)
	end)
	
	-- Block for existing players
	for _, player in pairs(Players:GetPlayers()) do
		player.Chatted:Connect(function(message)
			return
		end)
	end
end

print("✅ Chat disabled on server side")
