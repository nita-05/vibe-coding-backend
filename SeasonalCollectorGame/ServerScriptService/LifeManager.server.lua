-- LifeManager.server.lua
-- Adds a simple "lives / lifeline" system.
-- - Players start with DEFAULT_LIVES
-- - When humanoid dies: lose 1 life, respawn if lives remain
-- - When lives reach 0: apply penalty, reset lives, respawn
--
-- Place in ServerScriptService

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- ============================================
-- CONFIG
-- ============================================
local DEFAULT_LIVES = 3
local RESPAWN_DELAY_SECONDS = 1.5
-- IMPORTANT: when lives hit 0, we show Game Over + wait for Restart

-- Death penalty (makes bank/deposit the core loop)
local LOSE_WALLET_COINS_ON_DEATH = false
local DEATH_WALLET_LOSS_PERCENT = 0.25 -- lose 25% of wallet coins on each death
local DEATH_WALLET_MIN_LOSS = 1

-- ============================================
-- REMOTE EVENTS
-- ============================================
local Events = ReplicatedStorage:FindFirstChild("RemoteEvents")
if not Events then
	Events = Instance.new("Folder")
	Events.Name = "RemoteEvents"
	Events.Parent = ReplicatedStorage
end

local function getOrCreateEvent(name: string)
	local event = Events:FindFirstChild(name)
	if not event then
		event = Instance.new("RemoteEvent")
		event.Name = name
		event.Parent = Events
	end
	return event
end

local UpdateLives = getOrCreateEvent("UpdateLives")
local LifeMessage = getOrCreateEvent("LifeMessage") -- optional toast message
local GameOver = getOrCreateEvent("GameOver")
local RequestRestart = getOrCreateEvent("RequestRestart")

-- ============================================
-- STATE
-- ============================================
local livesByPlayer: {[Player]: number} = {}
local deathLock: {[Player]: boolean} = {}
local gameOverByPlayer: {[Player]: boolean} = {}

local function clampLives(n)
	n = tonumber(n) or 0
	if n < 0 then n = 0 end
	return math.floor(n)
end

local function setLives(player: Player, lives: number)
	livesByPlayer[player] = clampLives(lives)
	UpdateLives:FireClient(player, livesByPlayer[player], DEFAULT_LIVES)
end

local function getLives(player: Player)
	return livesByPlayer[player] or DEFAULT_LIVES
end

local function applyDeathCoinLoss(player: Player)
	if not LOSE_WALLET_COINS_ON_DEATH then
		return
	end

	local data = _G.PlayerDataManager and _G.PlayerDataManager.GetPlayerData(player)
	if not data then
		return
	end

	local wallet = math.floor(data.coins or 0)
	if wallet <= 0 then
		return
	end

	local loss = math.floor(wallet * DEATH_WALLET_LOSS_PERCENT)
	if loss < DEATH_WALLET_MIN_LOSS then
		loss = DEATH_WALLET_MIN_LOSS
	end
	if loss > wallet then
		loss = wallet
	end

	data.coins = wallet - loss

	local DataStoreManager = require(ReplicatedStorage:WaitForChild("Modules"):WaitForChild("DataStoreManager"))
	DataStoreManager.SavePlayerData(player, data)
	local UpdateStats = getOrCreateEvent("UpdateStats")
	UpdateStats:FireClient(player, data)

	LifeMessage:FireClient(player, "You dropped " .. tostring(loss) .. " coins! Deposit often to stay safe.")
end

local function onCharacterAdded(player: Player, character: Model)
	local humanoid = character:FindFirstChildOfClass("Humanoid") or character:WaitForChild("Humanoid", 10)
	if not humanoid then
		return
	end

	-- Ensure initial lives are sent
	UpdateLives:FireClient(player, getLives(player), DEFAULT_LIVES)

	humanoid.Died:Connect(function()
		if deathLock[player] then
			return
		end
		deathLock[player] = true

		-- If already game-over, ignore additional deaths until restart
		if gameOverByPlayer[player] then
			deathLock[player] = nil
			return
		end

		local lives = getLives(player) - 1
		if lives > 0 then
			applyDeathCoinLoss(player)
			setLives(player, lives)
			LifeMessage:FireClient(player, "You lost 1 life! Lives left: " .. tostring(lives))

			task.delay(RESPAWN_DELAY_SECONDS, function()
				if player and player.Parent then
					player:LoadCharacter()
				end
				deathLock[player] = nil
			end)
		else
			-- Game over (wait for Restart button)
			gameOverByPlayer[player] = true
			setLives(player, 0)
			LifeMessage:FireClient(player, "Game Over!")

			-- Apply coin loss for the final death (optional)
			applyDeathCoinLoss(player)
			GameOver:FireClient(player)
			deathLock[player] = nil
		end
	end)
end

-- We manage respawns ourselves so GameOver can hold the player until restart.
Players.CharacterAutoLoads = false

Players.PlayerAdded:Connect(function(player: Player)
	setLives(player, DEFAULT_LIVES)
	gameOverByPlayer[player] = nil

	player.CharacterAdded:Connect(function(character)
		onCharacterAdded(player, character)
	end)

	-- initial spawn
	player:LoadCharacter()
end)

Players.PlayerRemoving:Connect(function(player: Player)
	livesByPlayer[player] = nil
	deathLock[player] = nil
	gameOverByPlayer[player] = nil
end)

RequestRestart.OnServerEvent:Connect(function(player: Player)
	if not player or not player.Parent then return end
	if not gameOverByPlayer[player] then
		return
	end

	-- Hard reset stats: level 1, points 0, collected 0, wallet 0, bank 0, etc.
	if _G.PlayerDataManager and _G.PlayerDataManager.ResetPlayerDataToDefaults then
		_G.PlayerDataManager.ResetPlayerDataToDefaults(player)
	end

	gameOverByPlayer[player] = nil
	setLives(player, DEFAULT_LIVES)
	player:LoadCharacter()
	LifeMessage:FireClient(player, "Restarted! Good luck.")
end)

_G.LifeManager = {
	GetLives = getLives,
	SetLives = setLives,
	GetDefaultLives = function()
		return DEFAULT_LIVES
	end,
}

print("✅ Life Manager initialized (lives enabled)")
