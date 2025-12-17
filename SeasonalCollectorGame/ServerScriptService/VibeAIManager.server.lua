-- VibeAIManager.server.lua
-- Server-side bridge from Roblox -> Vibe Coding backend -> OpenAI
-- Place in ServerScriptService
--
-- Requirements:
-- - Enable HttpService in Roblox Studio (Game Settings -> Security -> Enable Http Requests)
-- - Set ReplicatedStorage/VibeConfig/BackendUrl to your FastAPI base URL (must be reachable from Roblox)
--
-- This is OPTIONAL: if not configured, it fails gracefully and does not affect gameplay systems.

local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

-- RemoteEvents
local Events = ReplicatedStorage:FindFirstChild("RemoteEvents")
if not Events then
	Events = Instance.new("Folder")
	Events.Name = "RemoteEvents"
	Events.Parent = ReplicatedStorage
end

local function getOrCreateEvent(name: string)
	local ev = Events:FindFirstChild(name)
	if not ev then
		ev = Instance.new("RemoteEvent")
		ev.Name = name
		ev.Parent = Events
	end
	return ev
end

local AIChatRequest = getOrCreateEvent("AIChatRequest")
local AIChatResponse = getOrCreateEvent("AIChatResponse")

-- Config (ReplicatedStorage so you can edit in Studio easily)
local vibeConfig = ReplicatedStorage:FindFirstChild("VibeConfig")
if not vibeConfig then
	vibeConfig = Instance.new("Folder")
	vibeConfig.Name = "VibeConfig"
	vibeConfig.Parent = ReplicatedStorage
end

local backendUrlValue = vibeConfig:FindFirstChild("BackendUrl")
if not backendUrlValue then
	backendUrlValue = Instance.new("StringValue")
	backendUrlValue.Name = "BackendUrl"
	backendUrlValue.Value = "http://localhost:8000" -- change to your hosted URL (https recommended)
	backendUrlValue.Parent = vibeConfig
end

-- Simple per-player cooldown to protect backend + costs
local lastCallAt: {[Player]: number} = {}
local COOLDOWN_SECONDS = 1.25
local MAX_MESSAGE_CHARS = 300

local function normalizeBaseUrl(url: string)
	url = tostring(url or "")
	url = url:gsub("%s+$", "")
	if url:sub(-1) == "/" then
		url = url:sub(1, -2)
	end
	return url
end

local function isConfigured()
	local url = normalizeBaseUrl(backendUrlValue.Value)
	return url ~= "" and url ~= "http://localhost:8000"
end

local function safeReply(player: Player, text: string)
	if player and player.Parent then
		AIChatResponse:FireClient(player, text)
	end
end

AIChatRequest.OnServerEvent:Connect(function(player: Player, userText: any)
	-- Validate
	if typeof(userText) ~= "string" then
		safeReply(player, "Please type a message.")
		return
	end

	userText = userText:sub(1, MAX_MESSAGE_CHARS)
	userText = userText:gsub("%s+$", "")
	if userText == "" then
		safeReply(player, "Please type a message.")
		return
	end

	-- Cooldown
	local now = os.clock()
	local last = lastCallAt[player]
	if last and (now - last) < COOLDOWN_SECONDS then
		safeReply(player, "One sec—try again in a moment.")
		return
	end
	lastCallAt[player] = now

	-- HttpService availability
	local okHttpEnabled, httpEnabled = pcall(function()
		return HttpService.HttpEnabled
	end)
	if not okHttpEnabled or not httpEnabled then
		safeReply(player, "Server setup needed: enable HttpService in Game Settings (Security).")
		return
	end

	-- Config
	local baseUrl = normalizeBaseUrl(backendUrlValue.Value)
	local endpoint = baseUrl .. "/api/ai/chat"

	-- If not configured, give helpful fallback
	if not isConfigured() then
		safeReply(player, "AI is not configured yet. Set ReplicatedStorage/VibeConfig/BackendUrl to your FastAPI URL.")
		return
	end

	-- Build request (matches backend/app/api/models.py AIChatRequest)
	local payload = {
		messages = {
			{ role = "user", content = userText }
		},
		system_prompt = "You are a helpful in-game assistant for the Roblox game 'Seasonal Coin Collector'. Keep responses short, friendly, and practical. You can explain coins, bank, hazards, vehicles, upgrades, and leveling.",
		temperature = 0.6,
		max_tokens = 180,
		context = {
			player_name = player.Name,
			game_name = "Seasonal Coin Collector",
		}
	}

	local body = HttpService:JSONEncode(payload)

	-- Make request
	local success, responseBody = pcall(function()
		return HttpService:PostAsync(endpoint, body, Enum.HttpContentType.ApplicationJson, false)
	end)

	if not success then
		safeReply(player, "AI request failed. Check BackendUrl and that HttpService is enabled.")
		return
	end

	-- Parse response: { message: str, success: bool, error?: str }
	local decodedOk, decoded = pcall(function()
		return HttpService:JSONDecode(responseBody)
	end)

	if not decodedOk or typeof(decoded) ~= "table" then
		safeReply(player, "AI returned an invalid response format.")
		return
	end

	local msg = decoded.message
	local ok = decoded.success
	if ok and typeof(msg) == "string" and msg ~= "" then
		safeReply(player, msg:sub(1, 600))
	else
		safeReply(player, "AI is having trouble responding right now.")
	end
end)

Players.PlayerRemoving:Connect(function(player: Player)
	lastCallAt[player] = nil
end)

print("✅ Vibe AI Manager initialized (optional AI assistant bridge)")
