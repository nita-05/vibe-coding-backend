-- RemoteEventsBootstrap.server.lua
-- Creates RemoteEvents early on the server to avoid client-side duplicates.
-- Place in ServerScriptService

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Events = ReplicatedStorage:FindFirstChild("RemoteEvents")
if not Events then
	Events = Instance.new("Folder")
	Events.Name = "RemoteEvents"
	Events.Parent = ReplicatedStorage
end

local function ensureRemoteEvent(name: string)
	local ev = Events:FindFirstChild(name)
	if not ev then
		ev = Instance.new("RemoteEvent")
		ev.Name = name
		ev.Parent = Events
	end
	return ev
end

-- Bank
ensureRemoteEvent("OpenBank")
ensureRemoteEvent("DepositCoins")
ensureRemoteEvent("WithdrawCoins")

-- Shop
ensureRemoteEvent("OpenShop")
ensureRemoteEvent("PurchaseShopItem")

-- Common (already used elsewhere, but safe to ensure)
ensureRemoteEvent("UpdateStats")
ensureRemoteEvent("UpdateLives")
ensureRemoteEvent("LifeMessage")
ensureRemoteEvent("GameOver")
ensureRemoteEvent("RequestRestart")

-- NPC / Dialog
ensureRemoteEvent("ShowNPCDialog")

-- Vibe AI (Roblox -> FastAPI -> OpenAI)
ensureRemoteEvent("AIChatRequest")
ensureRemoteEvent("AIChatResponse")

print("✅ RemoteEvents bootstrap initialized")
