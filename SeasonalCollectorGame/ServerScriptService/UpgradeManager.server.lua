-- UpgradeManager.server.lua
-- Handles upgrade purchases (server-side validation)
-- Place in ServerScriptService

local ReplicatedStorage = game:GetService("ReplicatedStorage")

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

local PurchaseUpgrade = getOrCreateEvent("PurchaseUpgrade")
local PurchaseResponse = getOrCreateEvent("PurchaseResponse")

-- ============================================
-- HANDLE PURCHASE
-- ============================================
PurchaseUpgrade.OnServerEvent:Connect(function(player, upgradeType)
	if not _G.PlayerDataManager then
		PurchaseResponse:FireClient(player, false, "System not ready")
		return
	end
	
	local success, message = _G.PlayerDataManager.PurchaseUpgrade(player, upgradeType)
	PurchaseResponse:FireClient(player, success, message)
end)

print("✅ Upgrade Manager initialized")
