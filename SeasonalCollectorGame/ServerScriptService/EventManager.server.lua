-- EventManager.server.lua
-- Core event system - manages event switching and synchronization
-- Place in ServerScriptService

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local Lighting = game:GetService("Lighting")
local Workspace = game:GetService("Workspace")

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

local EventChanged = getOrCreateEvent("EventChanged")
local EventUpdate = getOrCreateEvent("EventUpdate")

-- ============================================
-- EVENT CONFIGURATION
-- ============================================
local EVENT_CONFIG = {
	Snow = {
		name = "Snow Event",
		duration = 3600, -- 1 hour (can be changed)
		coinMultiplier = 1.0, -- Base multiplier
		lighting = {
			brightness = 1.8,
			ambient = Color3.fromRGB(140, 160, 180),
			fogColor = Color3.fromRGB(230, 240, 250),
			fogStart = 100,
			fogEnd = 500,
			timeOfDay = 14,
		},
		skybox = "Default", -- Use default sky
		particles = "Snow",
		decorations = "Snow",
	},
	
	Halloween = {
		name = "Halloween Event",
		duration = 3600,
		coinMultiplier = 1.5, -- 50% bonus during Halloween
		lighting = {
			brightness = 0.5,
			ambient = Color3.fromRGB(50, 30, 40),
			fogColor = Color3.fromRGB(20, 10, 15),
			fogStart = 0,
			fogEnd = 200,
			timeOfDay = 20, -- Night
		},
		skybox = "Halloween",
		particles = "Halloween",
		decorations = "Halloween",
	},
	
	Festival = {
		name = "Festival Event",
		duration = 3600,
		lighting = {
			brightness = 2.2,
			ambient = Color3.fromRGB(255, 240, 200),
			fogColor = Color3.fromRGB(255, 250, 240),
			fogStart = 50,
			fogEnd = 400,
			timeOfDay = 16, -- Evening
		},
		skybox = "Festival",
		particles = "Festival",
		decorations = "Festival",
	},
}

-- ============================================
-- CURRENT EVENT STATE
-- ============================================
local currentEvent = "Snow" -- Default event
local eventStartTime = tick()
local eventEndTime = tick() + EVENT_CONFIG[currentEvent].duration

-- ============================================
-- EVENT SWITCHING
-- ============================================
local function applyEventLighting(eventName)
	local config = EVENT_CONFIG[eventName]
	if not config then return end
	
	local lighting = config.lighting
	Lighting.Brightness = lighting.brightness
	Lighting.Ambient = lighting.ambient
	Lighting.FogColor = lighting.fogColor
	Lighting.FogStart = lighting.fogStart
	Lighting.FogEnd = lighting.fogEnd
	Lighting.TimeOfDay = lighting.timeOfDay
	
	print("✅ Applied " .. eventName .. " lighting")
end

local function applyEventSkybox(eventName)
	local config = EVENT_CONFIG[eventName]
	if not config then return end
	
	-- Skybox handling (can be expanded with custom skyboxes)
	if eventName == "Halloween" then
		-- Dark sky for Halloween
		Lighting.Sky.SkyboxBk = "rbxasset://textures/sky/sky512_bk.tex"
		Lighting.Sky.SkyboxDn = "rbxasset://textures/sky/sky512_dn.tex"
		Lighting.Sky.SkyboxFt = "rbxasset://textures/sky/sky512_ft.tex"
		Lighting.Sky.SkyboxLf = "rbxasset://textures/sky/sky512_lf.tex"
		Lighting.Sky.SkyboxRt = "rbxasset://textures/sky/sky512_rt.tex"
		Lighting.Sky.SkyboxUp = "rbxasset://textures/sky/sky512_up.tex"
	elseif eventName == "Festival" then
		-- Bright sky for Festival
		Lighting.Sky.SkyboxBk = "rbxasset://textures/sky/sky512_bk.tex"
		Lighting.Sky.SkyboxDn = "rbxasset://textures/sky/sky512_dn.tex"
		Lighting.Sky.SkyboxFt = "rbxasset://textures/sky/sky512_ft.tex"
		Lighting.Sky.SkyboxLf = "rbxasset://textures/sky/sky512_lf.tex"
		Lighting.Sky.SkyboxRt = "rbxasset://textures/sky/sky512_rt.tex"
		Lighting.Sky.SkyboxUp = "rbxasset://textures/sky/sky512_up.tex"
	else
		-- Default sky for Snow
		Lighting.Sky.SkyboxBk = "rbxasset://textures/sky/sky512_bk.tex"
		Lighting.Sky.SkyboxDn = "rbxasset://textures/sky/sky512_dn.tex"
		Lighting.Sky.SkyboxFt = "rbxasset://textures/sky/sky512_ft.tex"
		Lighting.Sky.SkyboxLf = "rbxasset://textures/sky/sky512_lf.tex"
		Lighting.Sky.SkyboxRt = "rbxasset://textures/sky/sky512_rt.tex"
		Lighting.Sky.SkyboxUp = "rbxasset://textures/sky/sky512_up.tex"
	end
	
	print("✅ Applied " .. eventName .. " skybox")
end

local function switchEvent(newEvent)
	if not EVENT_CONFIG[newEvent] then
		warn("⚠️ Invalid event: " .. tostring(newEvent))
		return false
	end
	
	-- Update state
	currentEvent = newEvent
	eventStartTime = tick()
	eventEndTime = tick() + EVENT_CONFIG[newEvent].duration
	
	-- Apply event settings
	applyEventLighting(newEvent)
	applyEventSkybox(newEvent)
	
	-- Notify all systems
	if _G.CollectibleManager then
		_G.CollectibleManager.SwitchEvent(newEvent)
	end
	
	-- Notify EnvironmentManager
	spawn(function()
		wait(0.5) -- Wait for EnvironmentManager to load
		if _G.EnvironmentManager then
			_G.EnvironmentManager.SwitchEvent(newEvent)
		end
	end)
	
	if _G.LeaderboardManager then
		_G.LeaderboardManager.ResetEventLeaderboard()
	end
	
	-- Broadcast to all players
	for _, player in ipairs(Players:GetPlayers()) do
		EventChanged:FireClient(player, newEvent, eventEndTime)
	end
	
	print("🎉 Event switched to: " .. newEvent)
	return true
end

-- ============================================
-- EVENT TIMER
-- ============================================
local function checkEventTimer()
	local currentTime = tick()
	
	if currentTime >= eventEndTime then
		-- Event ended - switch to next event
		local events = {"Snow", "Halloween", "Festival"}
		local currentIndex = 1
		for i, event in ipairs(events) do
			if event == currentEvent then
				currentIndex = i
				break
			end
		end
		
		local nextIndex = (currentIndex % #events) + 1
		switchEvent(events[nextIndex])
	end
end

-- ============================================
-- INITIALIZATION
-- ============================================
local function initialize()
	-- Apply default event (Snow)
	switchEvent("Snow")
	
	-- Start event timer
	spawn(function()
		while true do
			wait(10) -- Check every 10 seconds
			checkEventTimer()
			
			-- Update all players with remaining time
			local remainingTime = eventEndTime - tick()
			for _, player in ipairs(Players:GetPlayers()) do
				EventUpdate:FireClient(player, currentEvent, remainingTime)
			end
		end
	end)
end

-- ============================================
-- PLAYER JOIN HANDLING
-- ============================================
Players.PlayerAdded:Connect(function(player)
	-- Send current event info to new player
	wait(1)
	local remainingTime = eventEndTime - tick()
	EventChanged:FireClient(player, currentEvent, eventEndTime)
end)

-- ============================================
-- EXPORT API
-- ============================================
_G.EventManager = {
	GetCurrentEvent = function()
		return currentEvent
	end,
	
	GetEventConfig = function(eventName)
		return EVENT_CONFIG[eventName]
	end,
	
	GetCoinMultiplier = function()
		local config = EVENT_CONFIG[currentEvent]
		return config and config.coinMultiplier or 1.0
	end,
	
	SwitchEvent = switchEvent,
	
	GetRemainingTime = function()
		return eventEndTime - tick()
	end,
	
	GetEventStartTime = function()
		return eventStartTime
	end,
}

-- Initialize on server start
initialize()

print("✅ Event Manager initialized")
print("   - Current event: " .. currentEvent)
print("   - Auto-switching enabled")
