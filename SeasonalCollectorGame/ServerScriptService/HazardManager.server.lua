-- HazardManager.server.lua
-- Obstacles / hazards to make gameplay more realistic.
--
-- How to use:
-- - Tag any Part or Model with CollectionService tag: "Hazard"
-- - Touching/being near it will damage the player and optionally take a few wallet coins.
--
-- This script also spawns a couple simple moving hazards near the player's Yard/mailboxes.
--
-- Place in ServerScriptService

local Workspace = game:GetService("Workspace")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Lighting = game:GetService("Lighting")
local CollectionService = game:GetService("CollectionService")
local TweenService = game:GetService("TweenService")

-- ============================================
-- CONFIG
-- ============================================
local HAZARD_TAG = "Hazard"
local DAMAGE_PER_HIT = 25
local HIT_COOLDOWN_SECONDS = 1.0

-- Spawn protection so players don't die instantly on spawn pads / safe areas
local SPAWN_GRACE_SECONDS = 2.5

-- Coin penalty (wallet only)
local ENABLE_COIN_PENALTY = false
local COIN_PENALTY_PER_HIT = 3

-- Detection
local USE_PROXIMITY_FALLBACK = true
local PROXIMITY_CHECK_INTERVAL_SECONDS = 0.2
local DEFAULT_HAZARD_RADIUS_STUDS = 5

-- Map collision obstacles (use existing map objects like trees/houses/buildings)
-- This avoids having to tag thousands of parts while still making "hitting stuff" matter.
local ENABLE_MAP_COLLISION_OBSTACLES = true
local MIN_IMPACT_SPEED_STUDS_PER_SEC = 10 -- require movement, prevents "standing near wall" spam

-- Off-road / nature hazards (grass, trees, leaving the road)
local ENABLE_OFFROAD_HAZARD = true
local OFFROAD_CHECK_INTERVAL_SECONDS = 0.5
local OFFROAD_RAYCAST_DISTANCE = 60
local OFFROAD_EXTRA_COIN_PENALTY = 2
local OFFROAD_MESSAGE_COOLDOWN_SECONDS = 2.0

-- Road obstacle tuning (medium difficulty)
local ROAD_HOLES_COUNT = 10 -- total holes across the whole map (distributed across roads)
local ROAD_HOLE_SIZE = 5 -- studs (smaller = easier)
local ROAD_HOLE_SPACING = 22 -- studs (bigger = easier)
local ROAD_SLIDER_TWEEN_SECONDS = 2.2 -- medium speed (smaller = harder)
local ROAD_SLIDER_CHANCE_PER_ROAD = 0.35 -- 35% of roads get a slider (medium)
local MIN_ROAD_PART_SIZE = 18 -- ignore tiny parts like sidewalk pieces

-- Moving traffic car obstacles (like your white car)
local ENABLE_TRAFFIC_CARS = true
local TRAFFIC_CAR_BASE_COUNT = 10
local TRAFFIC_CAR_EXTRA_PER_LEVEL = 4
local TRAFFIC_CAR_MAX_COUNT = 60
local TRAFFIC_SPAWN_INTERVAL_SECONDS = 1.5
local TRAFFIC_CAR_BASE_SPEED_STUDS_PER_SEC = 26
local TRAFFIC_CAR_SPEED_PER_LEVEL = 2
local TRAFFIC_CAR_LANE_OFFSET_STUDS = 3.5
local TRAFFIC_CAR_HEIGHT_ABOVE_ROAD = 2.2
local TRAFFIC_TEMPLATE_NAMES = {"Jeep", "Car", "Vehicle"}
local TRAFFIC_TEMPLATE_FOLDER_NAMES = {"TrafficCars", "Vehicles", "Cars"}
local TRAFFIC_STRIP_SCRIPTS_FROM_CLONES = true
local TRAFFIC_RANDOM_COLORS = true
local TRAFFIC_COLORS = {
	Color3.fromRGB(245, 245, 245),
	Color3.fromRGB(220, 220, 220),
	Color3.fromRGB(30, 30, 30),
	Color3.fromRGB(200, 40, 40),
	Color3.fromRGB(40, 120, 200),
	Color3.fromRGB(40, 180, 90),
}

-- Realism polish
local TRAFFIC_TWO_WAY_LANES = true -- laneSign decides direction
local TRAFFIC_MIN_ROAD_WIDTH_FOR_2_LANES = 14
local TRAFFIC_SPAWN_SAFE_DISTANCE = 60 -- don't spawn cars on top of players

-- Headlights
local TRAFFIC_HEADLIGHTS_ENABLED = true
local TRAFFIC_NIGHT_START = 18.5 -- 6:30 PM
local TRAFFIC_NIGHT_END = 6.0 -- 6:00 AM
local TRAFFIC_HEADLIGHT_BRIGHTNESS = 2.2
local TRAFFIC_HEADLIGHT_RANGE = 26

-- Horn
local TRAFFIC_HORN_ENABLED = true
local TRAFFIC_HORN_DISTANCE = 30
local TRAFFIC_HORN_COOLDOWN_SECONDS = 6
local TRAFFIC_HORN_SOUND_ID = "rbxassetid://301964312" -- replace with your preferred horn asset if needed

-- Convert existing static cars on roads into moving traffic
local TRAFFIC_ADOPT_STATIC_CARS = true
local TRAFFIC_ADOPT_MAX = 30
local TRAFFIC_ADOPT_NAME_KEYWORDS = {"car", "jeep", "truck", "vehicle"}

-- ============================================
-- REMOTE EVENTS (optional)
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

local LifeMessage = getOrCreateEvent("LifeMessage")

-- ============================================
-- STATE
-- ============================================
local lastHitAtByPlayer = {} -- [Player] = number
local hazards = {} -- [Instance] = {getPosition = fn, radius = number}
local lastOffroadMsgAt = {} -- [Player] = number
local touchConnByPlayer = {} -- [Player] = RBXScriptConnection
local protectUntilByPlayer = {} -- [Player] = number

local function getGlobalMaxPlayerLevel()
	local maxLevel = 1
	for _, plr in ipairs(Players:GetPlayers()) do
		local data = _G.PlayerDataManager and _G.PlayerDataManager.GetPlayerData(plr)
		local lvl = (data and tonumber(data.level)) or 1
		if lvl > maxLevel then
			maxLevel = lvl
		end
	end
	return maxLevel
end

local function clamp(n, lo, hi)
	if n < lo then return lo end
	if n > hi then return hi end
	return n
end

local function getPlayerFromHit(hit)
	if not hit then return nil end
	local model = hit:FindFirstAncestorOfClass("Model")
	if not model then return nil end
	return Players:GetPlayerFromCharacter(model)
end

local function takeWalletCoins(player, amount)
	if not ENABLE_COIN_PENALTY then return end
	amount = math.floor(tonumber(amount) or 0)
	if amount <= 0 then return end

	local data = _G.PlayerDataManager and _G.PlayerDataManager.GetPlayerData(player)
	if not data then return end

	local wallet = math.floor(data.coins or 0)
	if wallet <= 0 then return end

	local toTake = math.min(wallet, amount)
	data.coins = wallet - toTake

	local DataStoreManager = require(ReplicatedStorage:WaitForChild("Modules"):WaitForChild("DataStoreManager"))
	DataStoreManager.SavePlayerData(player, data)
	local UpdateStats = getOrCreateEvent("UpdateStats")
	UpdateStats:FireClient(player, data)
end

local function tryConsumeShield(player: Player)
	local char = player and player.Character
	if not char then return false end

	-- Support classic Roblox shield
	local ff = char:FindFirstChildOfClass("ForceField")
	if ff then
		ff:Destroy()
		return true
	end

	-- Support attribute-based shields (if any other scripts use it)
	if char:GetAttribute("ShieldActive") == true then
		char:SetAttribute("ShieldActive", false)
		return true
	end

	return false
end

local function damagePlayer(player)
	if not player or not player.Parent then return end

	local now = os.clock()
	local protectUntil = protectUntilByPlayer[player]
	if protectUntil and now < protectUntil then
		return
	end

	local last = lastHitAtByPlayer[player]
	if last and (now - last) < HIT_COOLDOWN_SECONDS then
		return
	end
	lastHitAtByPlayer[player] = now

	local char = player.Character
	local humanoid = char and char:FindFirstChildOfClass("Humanoid")
	if humanoid and humanoid.Health > 0 then
		-- Shield blocks one hit instead of dying
		if tryConsumeShield(player) then
			LifeMessage:FireClient(player, "🛡️ Shield protected you!")
			return
		end

		-- Instant death on any hazard / road obstacle / trees / grass / buildings
		humanoid.Health = 0
		takeWalletCoins(player, COIN_PENALTY_PER_HIT)
		LifeMessage:FireClient(player, "💀 You hit an obstacle!")
	end
end

local function isRoadSurface(rayResult)
	if not rayResult then return false end

	-- Terrain road is unlikely; treat by material if needed
	if rayResult.Instance == Workspace.Terrain then
		-- Grass/ground should be dangerous (not road)
		return false
	end

	local inst = rayResult.Instance
	if not inst or not inst:IsA("BasePart") then
		return false
	end

	local name = string.lower(inst.Name or "")
	if name:find("road", 1, true) or name:find("street", 1, true) or name:find("track", 1, true) then
		return true
	end

	-- Many roads are Asphalt/Concrete; allow those too
	local mat = inst.Material
	if mat == Enum.Material.Asphalt or mat == Enum.Material.Concrete then
		return true
	end

	return false
end

local function looksLikeRoadPart(part: Instance)
	if not part or not part:IsA("BasePart") then return false end
	local name = string.lower(part.Name or "")
	if name:find("road", 1, true) or name:find("street", 1, true) or name:find("track", 1, true) then
		return true
	end
	local mat = part.Material
	return (mat == Enum.Material.Asphalt or mat == Enum.Material.Concrete)
end

local function isNatureDanger(rayResult)
	if not rayResult then return false end

	-- Terrain material check
	if rayResult.Instance == Workspace.Terrain then
		local m = rayResult.Material
		if m == Enum.Material.Grass or m == Enum.Material.LeafyGrass then
			return true
		end
		return false
	end

	local inst = rayResult.Instance
	if not inst then return false end
	if inst:IsA("BasePart") then
		local name = string.lower(inst.Name or "")
		if name:find("grass", 1, true) or name:find("tree", 1, true) or name:find("bush", 1, true) then
			return true
		end
		local mat = inst.Material
		if mat == Enum.Material.Grass or mat == Enum.Material.LeafyGrass then
			return true
		end
	end

	-- If under a model called Tree/Bush
	local model = inst:FindFirstAncestorOfClass("Model")
	if model then
		local mn = string.lower(model.Name or "")
		if mn:find("tree", 1, true) or mn:find("bush", 1, true) then
			return true
		end
	end

	return false
end

local function hasHazardTagDeep(inst: Instance)
	local cur = inst
	while cur do
		if CollectionService:HasTag(cur, HAZARD_TAG) then
			return true
		end
		cur = cur.Parent
	end
	return false
end

local function looksLikeMapObstacle(part: BasePart)
	if not part then return false end
	if looksLikeRoadPart(part) then return false end

	-- Ignore coins/collectibles folders if they exist
	local coinsFolder = Workspace:FindFirstChild("Coins")
	if coinsFolder and part:IsDescendantOf(coinsFolder) then return false end
	local obstaclesFolder = Workspace:FindFirstChild("Obstacles")
	-- Spawned hazards in Obstacles folder should still count (they get the Hazard tag too),
	-- but we don't want the folder itself to influence checks.
	-- (No return here.)

	-- Terrain itself is handled by the off-road raycast logic.
	if part == Workspace.Terrain then return false end

	local n = string.lower(part.Name or "")
	if n:find("tree", 1, true) or n:find("bush", 1, true) or n:find("rock", 1, true) then
		return true
	end
	if n:find("house", 1, true) or n:find("building", 1, true) or n:find("wall", 1, true) then
		return true
	end
	if n:find("fence", 1, true) or n:find("gate", 1, true) or n:find("pole", 1, true) then
		return true
	end
	if n:find("lamp", 1, true) or n:find("sign", 1, true) or n:find("bench", 1, true) then
		return true
	end

	-- If part belongs to a model with an obstacle-like name
	local model = part:FindFirstAncestorOfClass("Model")
	if model then
		local mn = string.lower(model.Name or "")
		if mn:find("tree", 1, true) or mn:find("bush", 1, true) or mn:find("rock", 1, true) then
			return true
		end
		if mn:find("house", 1, true) or mn:find("building", 1, true) then
			return true
		end
	end

	-- Fallback heuristic: chunky parts (likely props/walls) count, tiny floor tiles do not.
	local maxXZ = math.max(part.Size.X, part.Size.Z)
	if maxXZ >= 6 and part.Size.Y >= 2 then
		return true
	end

	return false
end

local function registerHazard(inst)
	if not inst or hazards[inst] then return end

	if inst:IsA("BasePart") then
		hazards[inst] = {
			getPosition = function()
				if inst.Parent then return inst.Position end
				return nil
			end,
			radius = math.max(DEFAULT_HAZARD_RADIUS_STUDS, math.max(inst.Size.X, inst.Size.Z) * 0.5),
		}
	elseif inst:IsA("Model") then
		hazards[inst] = {
			getPosition = function()
				if inst.Parent then return inst:GetPivot().Position end
				return nil
			end,
			radius = DEFAULT_HAZARD_RADIUS_STUDS,
		}
	end
end

local function hookHazardTouched(inst)
	if inst:IsA("BasePart") then
		inst.Touched:Connect(function(hit)
			local player = getPlayerFromHit(hit)
			if player then
				damagePlayer(player)
			end
		end)
	elseif inst:IsA("Model") then
		for _, d in ipairs(inst:GetDescendants()) do
			if d:IsA("BasePart") then
				d.Touched:Connect(function(hit)
					local player = getPlayerFromHit(hit)
					if player then
						damagePlayer(player)
					end
				end)
			end
		end
	end
end

local function addHazard(inst)
	registerHazard(inst)
	hookHazardTouched(inst)
end

-- ============================================
-- SAMPLE OBSTACLES (simple moving bars)
-- ============================================
local function getYardCenter()
	-- Best-effort: find Workspace.Yard and a part inside to anchor obstacles near it
	local yard = Workspace:FindFirstChild("Yard")
	if yard then
		local anyPart = yard:FindFirstChildWhichIsA("BasePart", true)
		if anyPart then
			return anyPart.Position
		end
	end
	return Vector3.new(0, 5, 0)
end

local function spawnMovingHazards()
	local origin = getYardCenter()

	local folder = Workspace:FindFirstChild("Obstacles")
	if not folder then
		folder = Instance.new("Folder")
		folder.Name = "Obstacles"
		folder.Parent = Workspace
	end

	-- Rotating bar
	local rot = Instance.new("Part")
	rot.Name = "RotatingBarHazard"
	rot.Size = Vector3.new(14, 1, 1)
	rot.Anchored = true
	rot.CanCollide = true
	rot.Material = Enum.Material.Neon
	rot.Color = Color3.fromRGB(255, 80, 80)
	rot.Position = origin + Vector3.new(12, 3, 0)
	rot.Parent = folder
	CollectionService:AddTag(rot, HAZARD_TAG)

	task.spawn(function()
		while rot.Parent do
			rot.CFrame = rot.CFrame * CFrame.Angles(0, math.rad(4), 0)
			task.wait(0.03)
		end
	end)

	-- Sliding block
	local slide = Instance.new("Part")
	slide.Name = "SlidingBlockHazard"
	slide.Size = Vector3.new(3, 3, 3)
	slide.Anchored = true
	slide.CanCollide = true
	slide.Material = Enum.Material.Neon
	slide.Color = Color3.fromRGB(255, 120, 0)
	slide.Position = origin + Vector3.new(-12, 3, 0)
	slide.Parent = folder
	CollectionService:AddTag(slide, HAZARD_TAG)

	local p1 = slide.Position + Vector3.new(0, 0, -10)
	local p2 = slide.Position + Vector3.new(0, 0, 10)
	local info = TweenInfo.new(2, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true)
	local tween = TweenService:Create(slide, info, {Position = p2})
	slide.Position = p1
	tween:Play()

	-- ============================================
	-- ROAD OBSTACLES (holes + sliders)
	-- ============================================
	-- Clear previously spawned road obstacles (so re-testing doesn't stack)
	local roadFolder = folder:FindFirstChild("RoadObstacles")
	if roadFolder then
		roadFolder:Destroy()
	end
	roadFolder = Instance.new("Folder")
	roadFolder.Name = "RoadObstacles"
	roadFolder.Parent = folder

	-- Collect all road-like parts across the map (so any route has obstacles)
	local roads = {}
	for _, p in ipairs(Workspace:GetDescendants()) do
		if p:IsA("BasePart") and p.Parent and p.Parent ~= folder and not p:IsDescendantOf(folder) then
			local n = string.lower(p.Name or "")
			local isNamedRoad = n:find("road", 1, true) or n:find("street", 1, true) or n:find("track", 1, true)
			local isRoadMaterial = (p.Material == Enum.Material.Asphalt or p.Material == Enum.Material.Concrete)
			local bigEnough = (math.max(p.Size.X, p.Size.Z) >= MIN_ROAD_PART_SIZE)

			if (isNamedRoad or isRoadMaterial) and bigEnough then
				table.insert(roads, p)
			end
		end
	end

	if #roads > 0 then
		-- Shuffle roads so distribution feels random across routes
		for i = #roads, 2, -1 do
			local j = math.random(1, i)
			roads[i], roads[j] = roads[j], roads[i]
		end

		-- Distribute a total of ROAD_HOLES_COUNT across roads
		-- Scale difficulty by level (more + slightly larger holes, more sliders, faster sliders)
		local level = getGlobalMaxPlayerLevel()
		local totalHoles = clamp(ROAD_HOLES_COUNT + ((level - 1) * 3), ROAD_HOLES_COUNT, 70)
		local holeSize = clamp(ROAD_HOLE_SIZE + math.floor((level - 1) / 4), ROAD_HOLE_SIZE, 9)
		local sliderChance = clamp(ROAD_SLIDER_CHANCE_PER_ROAD + ((level - 1) * 0.05), ROAD_SLIDER_CHANCE_PER_ROAD, 0.9)
		local sliderTweenSeconds = clamp(ROAD_SLIDER_TWEEN_SECONDS - ((level - 1) * 0.08), 0.85, ROAD_SLIDER_TWEEN_SECONDS)

		local roadsToUse = math.min(#roads, totalHoles) -- if many roads, 1 hole per road on a subset
		local holesPerRoad = 1
		if #roads > 0 and #roads <= totalHoles then
			holesPerRoad = math.max(1, math.floor(totalHoles / #roads))
		end

		local holeIndex = 0
		for r = 1, roadsToUse do
			local road = roads[r]
			local roadCF = road.CFrame
			local forward = roadCF.LookVector
			local right = roadCF.RightVector

			local roadLen = math.max(road.Size.Z, 20)
			local roadHalfLen = (roadLen * 0.5) - 6
			local roadHalfWidth = (math.max(road.Size.X, 14) * 0.5) - 4

			-- Holes on this road
			for i = 1, holesPerRoad do
				if holeIndex >= totalHoles then
					break
				end
				holeIndex += 1

				-- pick a random offset along the road so holes aren't all in a line
				local along = math.random(-math.floor(roadHalfLen), math.floor(roadHalfLen))
				local side = math.random(-math.floor(roadHalfWidth), math.floor(roadHalfWidth))

				local hole = Instance.new("Part")
				hole.Name = "RoadHole_" .. holeIndex
				hole.Anchored = true
				hole.CanCollide = false
				hole.Material = Enum.Material.SmoothPlastic
				hole.Color = Color3.fromRGB(10, 10, 10)
				hole.Size = Vector3.new(holeSize, 1, holeSize)
				hole.CFrame = CFrame.new(road.Position + forward * along + right * side + Vector3.new(0, 0.2, 0)) * CFrame.Angles(0, math.rad(45), 0)
				hole.Parent = roadFolder
				CollectionService:AddTag(hole, HAZARD_TAG)

				local ring = Instance.new("Part")
				ring.Name = "RoadHoleRing_" .. holeIndex
				ring.Anchored = true
				ring.CanCollide = false
				ring.Material = Enum.Material.Neon
				ring.Color = Color3.fromRGB(255, 220, 0)
				ring.Size = Vector3.new(holeSize + 1.5, 0.2, holeSize + 1.5)
				ring.CFrame = CFrame.new(hole.Position + Vector3.new(0, 0.15, 0))
				ring.Parent = roadFolder
			end

			-- Slider on some roads (medium difficulty)
			if math.random() < sliderChance then
				local bar = Instance.new("Part")
				bar.Name = "RoadSliderBar_" .. r
				bar.Anchored = true
				bar.CanCollide = true
				bar.Material = Enum.Material.Neon
				bar.Color = Color3.fromRGB(255, 80, 80)
				bar.Size = Vector3.new(1, 3, math.min(road.Size.Z * 0.8, 18))

				local basePos = road.Position + Vector3.new(0, 2, 0)
				local halfWidth = math.max(6, (road.Size.X * 0.5) - 3)
				local leftPos = basePos - right * halfWidth
				local rightPos = basePos + right * halfWidth

				bar.CFrame = CFrame.new(leftPos, leftPos + forward)
				bar.Parent = roadFolder
				CollectionService:AddTag(bar, HAZARD_TAG)

				local barTween = TweenService:Create(bar, TweenInfo.new(sliderTweenSeconds, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true), {
					CFrame = CFrame.new(rightPos, rightPos + forward),
				})
				barTween:Play()
			end
		end

		-- ============================================
		-- TRAFFIC CARS (moving car obstacles on roads)
		-- ============================================
		if ENABLE_TRAFFIC_CARS then
			local trafficFolder = folder:FindFirstChild("TrafficCars")
			if trafficFolder then
				trafficFolder:Destroy()
			end
			trafficFolder = Instance.new("Folder")
			trafficFolder.Name = "TrafficCars"
			trafficFolder.Parent = folder
			local activeCars = {} -- [Model] = true

			local function gatherCarTemplates()
				local templates = {}

				local sources = {Workspace, ReplicatedStorage, ServerStorage}
				for _, src in ipairs(sources) do
					-- named templates (Jeep/Car/etc.)
					for _, nm in ipairs(TRAFFIC_TEMPLATE_NAMES) do
						local inst = src:FindFirstChild(nm, true)
						if inst and inst:IsA("Model") and inst:FindFirstChildWhichIsA("BasePart", true) then
							table.insert(templates, inst)
						end
					end

					-- folder-based templates (TrafficCars/Vehicles/Cars)
					for _, folderName in ipairs(TRAFFIC_TEMPLATE_FOLDER_NAMES) do
						local folder = src:FindFirstChild(folderName, true)
						if folder then
							for _, child in ipairs(folder:GetChildren()) do
								if child:IsA("Model") and child:FindFirstChildWhichIsA("BasePart", true) then
									table.insert(templates, child)
								end
							end
						end
					end
				end

				-- fallback: any model that contains "jeep" or "car" in Workspace
				if #templates == 0 then
					for _, inst in ipairs(Workspace:GetDescendants()) do
						if inst:IsA("Model") then
							local n = string.lower(inst.Name or "")
							if (n:find("jeep", 1, true) or n:find("car", 1, true) or n:find("truck", 1, true)) and inst:FindFirstChildWhichIsA("BasePart", true) then
								table.insert(templates, inst)
							end
						end
					end
				end

				return templates
			end

			local function buildSimpleCarModel()
				local car = Instance.new("Model")
				car.Name = "TrafficCar"

				local body = Instance.new("Part")
				body.Name = "Body"
				body.Size = Vector3.new(6, 2, 10)
				body.Material = Enum.Material.SmoothPlastic
				body.Color = Color3.fromRGB(240, 240, 240)
				body.Anchored = true
				body.CanCollide = true
				body.Parent = car
				car.PrimaryPart = body

				local top = Instance.new("Part")
				top.Name = "Top"
				top.Size = Vector3.new(5, 1.5, 4)
				top.Material = Enum.Material.SmoothPlastic
				top.Color = Color3.fromRGB(220, 220, 220)
				top.Anchored = true
				top.CanCollide = true
				top.Parent = car

				-- weld top to body so it follows
				local weld = Instance.new("WeldConstraint")
				weld.Part0 = body
				weld.Part1 = top
				weld.Parent = body

				return car
			end

			local templates = gatherCarTemplates()

			local function stripScripts(model: Model)
				if not TRAFFIC_STRIP_SCRIPTS_FROM_CLONES then return end
				for _, d in ipairs(model:GetDescendants()) do
					if d:IsA("Script") or d:IsA("LocalScript") then
						d:Destroy()
					end
				end
			end

			local function paintCar(model: Model)
				if not TRAFFIC_RANDOM_COLORS then return end
				local color = TRAFFIC_COLORS[math.random(1, #TRAFFIC_COLORS)]
				for _, d in ipairs(model:GetDescendants()) do
					if d:IsA("BasePart") then
						-- keep wheels dark if they exist
						local n = string.lower(d.Name or "")
						if n:find("wheel", 1, true) or n:find("tire", 1, true) then
							d.Color = Color3.fromRGB(25, 25, 25)
						else
							d.Color = color
						end
					end
				end
			end

			local function ensurePrimaryAndWelds(model: Model)
				if not model.PrimaryPart then
					model.PrimaryPart = model:FindFirstChildWhichIsA("BasePart", true)
				end
				local root = model.PrimaryPart
				if not root then return end

				-- Root is the mover (anchored); other parts should be unanchored and welded to it.
				root.Anchored = true
				root.CanCollide = true

				for _, d in ipairs(model:GetDescendants()) do
					if d:IsA("BasePart") then
						d.CanCollide = true
						if d ~= root then
							d.Anchored = false
						end
					end
				end

				-- Ensure everything follows PrimaryPart
				for _, d in ipairs(model:GetDescendants()) do
					if d:IsA("BasePart") and d ~= root then
						local hasWeld = false
						for _, w in ipairs(root:GetChildren()) do
							if w:IsA("WeldConstraint") and ((w.Part0 == root and w.Part1 == d) or (w.Part1 == root and w.Part0 == d)) then
								hasWeld = true
								break
							end
						end
						if not hasWeld then
							local wc = Instance.new("WeldConstraint")
							wc.Part0 = root
							wc.Part1 = d
							wc.Parent = root
						end
					end
				end
			end

			local function getTrafficTargetCount()
				local level = getGlobalMaxPlayerLevel()
				local target = TRAFFIC_CAR_BASE_COUNT + ((level - 1) * TRAFFIC_CAR_EXTRA_PER_LEVEL)
				return math.max(0, math.min(TRAFFIC_CAR_MAX_COUNT, target))
			end

			local function getTrafficSpeed()
				local level = getGlobalMaxPlayerLevel()
				local speed = TRAFFIC_CAR_BASE_SPEED_STUDS_PER_SEC + ((level - 1) * TRAFFIC_CAR_SPEED_PER_LEVEL)
				return math.max(10, speed)
			end

			local function getTrafficSpawnInterval()
				local level = getGlobalMaxPlayerLevel()
				-- Higher level = faster spawns (more intense)
				return math.max(0.5, TRAFFIC_SPAWN_INTERVAL_SECONDS - ((level - 1) * 0.08))
			end

			local function isNight()
				local t = Lighting.ClockTime
				if TRAFFIC_NIGHT_START < TRAFFIC_NIGHT_END then
					return (t >= TRAFFIC_NIGHT_START and t <= TRAFFIC_NIGHT_END)
				end
				return (t >= TRAFFIC_NIGHT_START or t <= TRAFFIC_NIGHT_END)
			end

			local function ensureCarLights(rootPart: BasePart)
				if not TRAFFIC_HEADLIGHTS_ENABLED then return end
				if rootPart:GetAttribute("__HasHeadlights") then return end
				rootPart:SetAttribute("__HasHeadlights", true)

				local sx = math.max(1.5, (rootPart.Size.X * 0.35))
				local sy = math.max(0.5, (rootPart.Size.Y * 0.15))
				local fz = math.max(2, (rootPart.Size.Z * 0.5) - 0.4) -- forward (local -Z)
				local bz = math.max(2, (rootPart.Size.Z * 0.5) - 0.4) -- backward (local +Z)

				local function mkHeadlight(name, xSign)
					local a = Instance.new("Attachment")
					a.Name = name .. "Attachment"
					a.Position = Vector3.new(sx * xSign, sy, -fz)
					a.Parent = rootPart

					local light = Instance.new("SpotLight")
					light.Name = name
					light.Enabled = false
					light.Brightness = TRAFFIC_HEADLIGHT_BRIGHTNESS
					light.Range = TRAFFIC_HEADLIGHT_RANGE
					light.Angle = 85
					light.Face = Enum.NormalId.Front
					light.Color = Color3.fromRGB(255, 245, 220)
					light.Parent = a
				end

				mkHeadlight("HeadlightL", -1)
				mkHeadlight("HeadlightR", 1)

				-- Tail lights (soft)
				local ta = Instance.new("Attachment")
				ta.Name = "TailLightAttachment"
				ta.Position = Vector3.new(0, sy, bz)
				ta.Parent = rootPart

				local tail = Instance.new("PointLight")
				tail.Name = "TailLight"
				tail.Enabled = false
				tail.Brightness = 1.2
				tail.Range = 10
				tail.Color = Color3.fromRGB(255, 60, 60)
				tail.Parent = ta
			end

			local function setCarLights(rootPart: BasePart, enabled: boolean)
				if not TRAFFIC_HEADLIGHTS_ENABLED then return end
				for _, d in ipairs(rootPart:GetDescendants()) do
					if d:IsA("SpotLight") or d:IsA("PointLight") then
						d.Enabled = enabled
					end
				end
			end

			local function ensureHorn(rootPart: BasePart)
				if not TRAFFIC_HORN_ENABLED then return nil end
				local s = rootPart:FindFirstChild("TrafficHorn")
				if s and s:IsA("Sound") then
					return s
				end
				s = Instance.new("Sound")
				s.Name = "TrafficHorn"
				s.SoundId = TRAFFIC_HORN_SOUND_ID
				s.Volume = 0.55
				s.RollOffMode = Enum.RollOffMode.InverseTapered
				s.RollOffMaxDistance = 80
				s.Parent = rootPart
				return s
			end

			local function minDistanceToPlayers(pos: Vector3)
				local best = math.huge
				for _, plr in ipairs(Players:GetPlayers()) do
					local hrp = plr.Character and plr.Character:FindFirstChild("HumanoidRootPart")
					if hrp and hrp:IsA("BasePart") then
						local d = (hrp.Position - pos).Magnitude
						if d < best then
							best = d
						end
					end
				end
				return best
			end

			local function spawnOneTrafficCar(road: BasePart)
				local carModel: Model
				if #templates > 0 then
					local chosen = templates[math.random(1, #templates)]
					carModel = chosen:Clone()
					carModel.Name = "TrafficCar_" .. tostring(math.random(1000, 9999))
				else
					carModel = buildSimpleCarModel()
					carModel.Name = "TrafficCar_" .. tostring(math.random(1000, 9999))
				end
				carModel.Parent = trafficFolder
				stripScripts(carModel)
				paintCar(carModel)
				ensurePrimaryAndWelds(carModel)

				local rp = carModel.PrimaryPart
				if not rp then
					carModel:Destroy()
					return
				end

				activeCars[carModel] = true

				-- Tag the whole model as Hazard so HazardManager instantly kills on touch
				CollectionService:AddTag(carModel, HAZARD_TAG)

				-- Add realism components
				ensureCarLights(rp)
				local horn = ensureHorn(rp)
				local lastHornAt = 0

				-- One-way loop: drive from one end to the other, then respawn and drive again
				local function startTrafficLoop()
					while carModel.Parent and trafficFolder.Parent do
						-- Choose a road/lane that doesn't spawn right on a player
						local r, a, b, dir
						for _ = 1, 10 do
							local cand = roads[math.random(1, #roads)]
							if cand and cand.Parent then
								local roadCF = cand.CFrame
								local forward = roadCF.LookVector
								local right = roadCF.RightVector
								local halfLen = (math.max(cand.Size.Z, 20) * 0.5) - 8

								-- lane selection (2-way lanes)
								local laneSign = (math.random() < 0.5) and -1 or 1
								local has2Lanes = TRAFFIC_TWO_WAY_LANES and (cand.Size.X >= TRAFFIC_MIN_ROAD_WIDTH_FOR_2_LANES)
								if not has2Lanes then
									laneSign = 0
								end
								local laneOffset = right * (TRAFFIC_CAR_LANE_OFFSET_STUDS * laneSign)

								local goForward
								if has2Lanes then
									-- opposite lanes go opposite directions
									goForward = (laneSign == -1)
								else
									goForward = (math.random() < 0.5)
								end

								local startPos = cand.Position - forward * halfLen + laneOffset + Vector3.new(0, TRAFFIC_CAR_HEIGHT_ABOVE_ROAD, 0)
								local endPos = cand.Position + forward * halfLen + laneOffset + Vector3.new(0, TRAFFIC_CAR_HEIGHT_ABOVE_ROAD, 0)

								local aa = goForward and startPos or endPos
								local bb = goForward and endPos or startPos
								local dd = goForward and forward or -forward

								if minDistanceToPlayers(aa) >= TRAFFIC_SPAWN_SAFE_DISTANCE then
									r, a, b, dir = cand, aa, bb, dd
									break
								end
							end
						end

						if not r or not a or not b or not dir then
							task.wait(0.4)
							continue
						end

						if not rp.Parent then break end
						rp.CFrame = CFrame.new(a, a + dir)

						local dist = (a - b).Magnitude
						local speed = getTrafficSpeed()
						local duration = math.max(1.1, dist / speed)

						-- Toggle headlights based on time
						setCarLights(rp, isNight())

						local tween = TweenService:Create(
							rp,
							TweenInfo.new(duration, Enum.EasingStyle.Linear, Enum.EasingDirection.InOut),
							{CFrame = CFrame.new(b, b + dir)}
						)
						tween:Play()

						-- While driving, occasionally honk if close to a player
						local startT = os.clock()
						while os.clock() - startT < duration and carModel.Parent and trafficFolder.Parent do
							if horn then
								local d = minDistanceToPlayers(rp.Position)
								if d <= TRAFFIC_HORN_DISTANCE then
									local now = os.clock()
									if (now - lastHornAt) >= TRAFFIC_HORN_COOLDOWN_SECONDS then
										lastHornAt = now
										horn.PlaybackSpeed = 0.95 + (math.random() * 0.1)
										horn:Play()
									end
								end
							end
							task.wait(0.35)
						end

						tween.Completed:Wait()
					end
					activeCars[carModel] = nil
				end

				task.spawn(startTrafficLoop)
			end

			local function modelLooksLikeCar(m: Model)
				if not m or not m:IsA("Model") then return false end
				if m:GetAttribute("__TrafficAdopted") then return false end
				-- don't re-adopt traffic cars we spawned
				if m:IsDescendantOf(trafficFolder) then return false end
				if m:IsDescendantOf(folder) then return false end
				if m:IsDescendantOf(Workspace:FindFirstChild("Players") or Workspace) then return false end

				local name = string.lower(m.Name or "")
				local ok = false
				for _, kw in ipairs(TRAFFIC_ADOPT_NAME_KEYWORDS) do
					if name:find(kw, 1, true) then
						ok = true
						break
					end
				end
				if not ok then return false end

				-- must have at least one part
				return (m:FindFirstChildWhichIsA("BasePart", true) ~= nil)
			end

			local function isModelOnRoad(m: Model)
				local pivot = m:GetPivot().Position
				local params = RaycastParams.new()
				params.FilterType = Enum.RaycastFilterType.Exclude
				params.FilterDescendantsInstances = {m, folder}
				params.IgnoreWater = true
				local result = Workspace:Raycast(pivot + Vector3.new(0, 6, 0), Vector3.new(0, -60, 0), params)
				if not result or not result.Instance then return false end
				return looksLikeRoadPart(result.Instance)
			end

			local function adoptStaticCars()
				if not TRAFFIC_ADOPT_STATIC_CARS then return end

				local adopted = 0
				for _, inst in ipairs(Workspace:GetDescendants()) do
					if adopted >= TRAFFIC_ADOPT_MAX then
						break
					end
					if inst:IsA("Model") and modelLooksLikeCar(inst) and isModelOnRoad(inst) then
						inst:SetAttribute("__TrafficAdopted", true)
						inst.Parent = trafficFolder
						stripScripts(inst)
						ensurePrimaryAndWelds(inst)

						local rp = inst.PrimaryPart
						if rp then
							CollectionService:AddTag(inst, HAZARD_TAG)
							ensureCarLights(rp)
							local horn = ensureHorn(rp)

							-- kick the same loop logic by temporarily wrapping as traffic car
							local carModel = inst
							activeCars[carModel] = true

							task.spawn(function()
								local lastHornAt = 0
								while carModel.Parent and trafficFolder.Parent do
									-- reuse the same per-lap logic by calling spawnOneTrafficCar-style inner loop
									-- (copy of loop used above but without creating a new model)
									local rSel, a, b, dir
									for _ = 1, 10 do
										local cand = roads[math.random(1, #roads)]
										if cand and cand.Parent then
											local roadCF = cand.CFrame
											local forward = roadCF.LookVector
											local right = roadCF.RightVector
											local halfLen = (math.max(cand.Size.Z, 20) * 0.5) - 8

											local laneSign = (math.random() < 0.5) and -1 or 1
											local has2Lanes = TRAFFIC_TWO_WAY_LANES and (cand.Size.X >= TRAFFIC_MIN_ROAD_WIDTH_FOR_2_LANES)
											if not has2Lanes then laneSign = 0 end
											local laneOffset = right * (TRAFFIC_CAR_LANE_OFFSET_STUDS * laneSign)

											local goForward
											if has2Lanes then
												goForward = (laneSign == -1)
											else
												goForward = (math.random() < 0.5)
											end

											local startPos = cand.Position - forward * halfLen + laneOffset + Vector3.new(0, TRAFFIC_CAR_HEIGHT_ABOVE_ROAD, 0)
											local endPos = cand.Position + forward * halfLen + laneOffset + Vector3.new(0, TRAFFIC_CAR_HEIGHT_ABOVE_ROAD, 0)

											local aa = goForward and startPos or endPos
											local bb = goForward and endPos or startPos
											local dd = goForward and forward or -forward

											if minDistanceToPlayers(aa) >= TRAFFIC_SPAWN_SAFE_DISTANCE then
												rSel, a, b, dir = cand, aa, bb, dd
												break
											end
										end
									end

									if not rSel or not a or not b or not dir then
										task.wait(0.4)
										continue
									end

									if not rp.Parent then break end
									rp.CFrame = CFrame.new(a, a + dir)
									setCarLights(rp, isNight())

									local dist = (a - b).Magnitude
									local speed = getTrafficSpeed()
									local duration = math.max(1.1, dist / speed)

									local tween = TweenService:Create(
										rp,
										TweenInfo.new(duration, Enum.EasingStyle.Linear, Enum.EasingDirection.InOut),
										{CFrame = CFrame.new(b, b + dir)}
									)
									tween:Play()

									local startT = os.clock()
									while os.clock() - startT < duration and carModel.Parent and trafficFolder.Parent do
										if horn then
											local d = minDistanceToPlayers(rp.Position)
											if d <= TRAFFIC_HORN_DISTANCE then
												local now = os.clock()
												if (now - lastHornAt) >= TRAFFIC_HORN_COOLDOWN_SECONDS then
													lastHornAt = now
													horn.PlaybackSpeed = 0.95 + (math.random() * 0.1)
													horn:Play()
												end
											end
										end
										task.wait(0.35)
									end

									tween.Completed:Wait()
								end
								activeCars[carModel] = nil
							end)
						end

						adopted += 1
					end
				end
			end

			local function countActiveCars()
				local n = 0
				for m, _ in pairs(activeCars) do
					if m and m.Parent then
						n += 1
					else
						activeCars[m] = nil
					end
				end
				return n
			end

			-- Keep spawning cars over time so roads feel alive.
			task.spawn(function()
				-- quick initial fill
				task.wait(0.2)
				while trafficFolder and trafficFolder.Parent do
					-- adopt any static cars placed on roads into traffic
					adoptStaticCars()

					local target = getTrafficTargetCount()
					local current = countActiveCars()
					local need = target - current

					-- If target decreased (e.g. players left), remove extras to keep performance stable
					if need < 0 then
						local toRemove = -need
						for m, _ in pairs(activeCars) do
							if toRemove <= 0 then break end
							if m and m.Parent then
								m:Destroy()
								toRemove -= 1
							end
						end
					end

					for _ = 1, math.max(0, need) do
						local road = roads[math.random(1, #roads)]
						if road and road.Parent then
							spawnOneTrafficCar(road)
						end
					end
					task.wait(getTrafficSpawnInterval())
				end
			end)
		end
	end
end

-- ============================================
-- INIT
-- ============================================
-- Register existing tagged hazards
for _, inst in ipairs(CollectionService:GetTagged(HAZARD_TAG)) do
	addHazard(inst)
end

CollectionService:GetInstanceAddedSignal(HAZARD_TAG):Connect(function(inst)
	addHazard(inst)
end)

if USE_PROXIMITY_FALLBACK then
	task.spawn(function()
		while true do
			task.wait(PROXIMITY_CHECK_INTERVAL_SECONDS)

			-- Clean up deleted hazards
			for inst, _ in pairs(hazards) do
				if not inst or not inst.Parent then
					hazards[inst] = nil
				end
			end

			for _, player in ipairs(Players:GetPlayers()) do
				local char = player.Character
				local hrp = char and char:FindFirstChild("HumanoidRootPart")
				if hrp then
					for inst, h in pairs(hazards) do
						local pos = h.getPosition and h.getPosition() or nil
						local radius = h.radius or DEFAULT_HAZARD_RADIUS_STUDS
						if pos and (hrp.Position - pos).Magnitude <= radius then
							damagePlayer(player)
						end
					end
				end
			end
		end
	end)
end

-- Off-road / grass / tree danger: if you're not on a road surface, you take damage + coin penalty.
if ENABLE_OFFROAD_HAZARD then
	task.spawn(function()
		while true do
			task.wait(OFFROAD_CHECK_INTERVAL_SECONDS)

			for _, player in ipairs(Players:GetPlayers()) do
				local char = player.Character
				local hrp = char and char:FindFirstChild("HumanoidRootPart")
				if hrp then
					local params = RaycastParams.new()
					params.FilterType = Enum.RaycastFilterType.Exclude
					-- Important: exclude Coins/Collectibles so floating pickups don't cause false "off-road" hits.
					local exclude = {char}
					local obs = Workspace:FindFirstChild("Obstacles")
					if obs then table.insert(exclude, obs) end
					local coins = Workspace:FindFirstChild("Coins")
					if coins then table.insert(exclude, coins) end
					local collectibles = Workspace:FindFirstChild("Collectibles")
					if collectibles then table.insert(exclude, collectibles) end
					params.FilterDescendantsInstances = exclude
					params.IgnoreWater = true

					local result = Workspace:Raycast(hrp.Position, Vector3.new(0, -OFFROAD_RAYCAST_DISTANCE, 0), params)

					local onRoad = isRoadSurface(result)
					-- Only treat nature (grass/trees) as dangerous; avoids killing players on spawn pads.
					local danger = (not onRoad) and isNatureDanger(result)

					if danger then
						-- Extra small coin penalty for being off-road
						takeWalletCoins(player, OFFROAD_EXTRA_COIN_PENALTY)
						damagePlayer(player)

						local now = os.clock()
						local last = lastOffroadMsgAt[player]
						if not last or (now - last) >= OFFROAD_MESSAGE_COOLDOWN_SECONDS then
							lastOffroadMsgAt[player] = now
							LifeMessage:FireClient(player, "Danger! Stay on the road—grass/trees are risky.")
						end
					end
				end
			end
		end
	end)
end

-- Map collision obstacles: detect when player runs into existing map props (trees/houses/buildings/etc.)
local function hookCharacterTouches(player: Player, character: Model)
	if not ENABLE_MAP_COLLISION_OBSTACLES then return end

	-- Clean previous
	if touchConnByPlayer[player] then
		touchConnByPlayer[player]:Disconnect()
		touchConnByPlayer[player] = nil
	end

	local hrp = character:FindFirstChild("HumanoidRootPart") or character:WaitForChild("HumanoidRootPart", 10)
	if not hrp or not hrp:IsA("BasePart") then
		return
	end

	touchConnByPlayer[player] = hrp.Touched:Connect(function(hit: BasePart)
		if not hit or not hit.Parent then return end
		if not player or not player.Parent then return end
		if not character or not character.Parent then return end

		-- Ignore self-collisions
		if hit:IsDescendantOf(character) then return end

		-- Require impact speed to avoid constant damage from gentle contact
		local v = hrp.AssemblyLinearVelocity
		local planarSpeed = Vector3.new(v.X, 0, v.Z).Magnitude
		if planarSpeed < MIN_IMPACT_SPEED_STUDS_PER_SEC then
			return
		end

		-- Tagged hazards always count
		if hasHazardTagDeep(hit) then
			damagePlayer(player)
			return
		end

		-- Existing map objects count if they look like obstacles (trees/houses/buildings/etc.)
		if hit:IsA("BasePart") and looksLikeMapObstacle(hit) then
			damagePlayer(player)
		end
	end)
end

task.delay(2, function()
	-- spawn example obstacles a bit after load
	spawnMovingHazards()
	print("✅ Spawned default obstacles in Workspace.Obstacles (no tagging needed)")
end)

Players.PlayerAdded:Connect(function(player)
	player.CharacterAdded:Connect(function(character)
		protectUntilByPlayer[player] = os.clock() + SPAWN_GRACE_SECONDS
		hookCharacterTouches(player, character)
	end)
end)

Players.PlayerRemoving:Connect(function(player)
	lastHitAtByPlayer[player] = nil
	lastOffroadMsgAt[player] = nil
	protectUntilByPlayer[player] = nil
	if touchConnByPlayer[player] then
		touchConnByPlayer[player]:Disconnect()
		touchConnByPlayer[player] = nil
	end
end)

print("✅ Hazard Manager initialized (obstacles enabled)")

