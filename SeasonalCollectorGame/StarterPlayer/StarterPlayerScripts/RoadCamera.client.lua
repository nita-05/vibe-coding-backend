-- RoadCamera.client.lua
-- Makes camera feel more "road-wise" when player is on a road
-- Place in StarterPlayer/StarterPlayerScripts

local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")
local Lighting = game:GetService("Lighting")
local RunService = game:GetService("RunService")

local player = Players.LocalPlayer
local camera = Workspace.CurrentCamera

local CHECK_INTERVAL = 0.2

local ROAD_FOV = 80
local NORMAL_FOV = 70

-- Cinematic third-person offset when on road
local ROAD_CAMERA_OFFSET = Vector3.new(0, 1.25, -2.4)
local NORMAL_CAMERA_OFFSET = Vector3.new(0, 0, 0)

-- Speed-based camera feel
local MAX_SPEED_FOR_EFFECT = 80 -- studs/s
local EXTRA_FOV_AT_MAX_SPEED = 6

-- Post-processing (enabled only on road)
local EFFECTS_FOLDER_NAME = "RoadCinematicEffects"
local MAX_MOTION_BLUR = 0.45
local COLOR_TINT = Color3.fromRGB(255, 250, 240)
local CONTRAST_ON_ROAD = 0.08
local SATURATION_ON_ROAD = 0.05

-- Gentle camera shake when traffic cars pass nearby
local TRAFFIC_FOLDER_PATH = {"Obstacles", "TrafficCars"}
local TRAFFIC_SCAN_INTERVAL = 1.0
local TRAFFIC_SHAKE_RADIUS = 26
local TRAFFIC_SHAKE_MAX_OFFSET = 0.18 -- studs (very subtle)
local TRAFFIC_SHAKE_MAX_ROT_DEG = 0.8 -- degrees (very subtle)
local TRAFFIC_SHAKE_SMOOTH = 0.18 -- 0..1 (higher = snappier)
local SHAKE_FREQ = 10

local function clamp(n, lo, hi)
	if n < lo then return lo end
	if n > hi then return hi end
	return n
end

local function looksLikeRoad(inst: Instance)
	if not inst then return false end
	if inst == Workspace.Terrain then
		return false
	end
	if inst:IsA("BasePart") then
		local n = string.lower(inst.Name or "")
		if n:find("road", 1, true) or n:find("street", 1, true) or n:find("track", 1, true) then
			return true
		end
		local mat = inst.Material
		if mat == Enum.Material.Asphalt or mat == Enum.Material.Concrete then
			return true
		end
	end
	return false
end

local currentMode = "normal"
local fovTween

local effectsFolder = Lighting:FindFirstChild(EFFECTS_FOLDER_NAME)
if not effectsFolder then
	effectsFolder = Instance.new("Folder")
	effectsFolder.Name = EFFECTS_FOLDER_NAME
	effectsFolder.Parent = Lighting
end

local motionBlur = effectsFolder:FindFirstChild("MotionBlur")
if not motionBlur then
	motionBlur = Instance.new("BlurEffect")
	motionBlur.Name = "MotionBlur"
	motionBlur.Size = 0
	motionBlur.Enabled = false
	motionBlur.Parent = effectsFolder
end

local color = effectsFolder:FindFirstChild("ColorCorrection")
if not color then
	color = Instance.new("ColorCorrectionEffect")
	color.Name = "ColorCorrection"
	color.Enabled = false
	color.TintColor = COLOR_TINT
	color.Contrast = 0
	color.Saturation = 0
	color.Parent = effectsFolder
end

local function setFov(target)
	if not camera then return end
	if fovTween then
		fovTween:Cancel()
		fovTween = nil
	end
	fovTween = TweenService:Create(camera, TweenInfo.new(0.25, Enum.EasingStyle.Sine, Enum.EasingDirection.Out), {FieldOfView = target})
	fovTween:Play()
end

local function setCinematicEffects(enabled: boolean)
	motionBlur.Enabled = enabled
	color.Enabled = enabled
	if not enabled then
		motionBlur.Size = 0
		color.Contrast = 0
		color.Saturation = 0
	end
end

local function setCameraOffset(humanoid, offset)
	if humanoid then
		humanoid.CameraOffset = offset
	end
end

local function update()
	local char = player.Character
	local hrp = char and char:FindFirstChild("HumanoidRootPart")
	local humanoid = char and char:FindFirstChildOfClass("Humanoid")
	if not hrp or not humanoid then
		return
	end

	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = {char}
	params.IgnoreWater = true

	local result = Workspace:Raycast(hrp.Position, Vector3.new(0, -25, 0), params)
	local onRoad = result and looksLikeRoad(result.Instance)

	if onRoad and currentMode ~= "road" then
		currentMode = "road"
		setCinematicEffects(true)
		setCameraOffset(humanoid, ROAD_CAMERA_OFFSET)
	elseif (not onRoad) and currentMode ~= "normal" then
		currentMode = "normal"
		setFov(NORMAL_FOV)
		setCinematicEffects(false)
		setCameraOffset(humanoid, NORMAL_CAMERA_OFFSET)
	end

	-- Speed-based cinematic feel (only when on road)
	if currentMode == "road" then
		local v = hrp.AssemblyLinearVelocity
		local speed = Vector3.new(v.X, 0, v.Z).Magnitude
		local t = clamp(speed / MAX_SPEED_FOR_EFFECT, 0, 1)

		setFov(ROAD_FOV + (EXTRA_FOV_AT_MAX_SPEED * t))
		motionBlur.Size = 3 + (MAX_MOTION_BLUR * 20 * t) -- BlurEffect uses size scale
		color.Contrast = CONTRAST_ON_ROAD * t
		color.Saturation = SATURATION_ON_ROAD * t
	end
end

player.CharacterAdded:Connect(function()
	currentMode = "normal"
	camera = Workspace.CurrentCamera
	if camera then
		camera.FieldOfView = NORMAL_FOV
	end
	setCinematicEffects(false)
end)

-- ============================================
-- Traffic shake (runs every frame, but scans cars infrequently)
-- ============================================
local trafficParts = {}
local lastTrafficScan = 0
local shakeStrength = 0

local function getTrafficFolder()
	local cur: Instance? = Workspace
	for _, name in ipairs(TRAFFIC_FOLDER_PATH) do
		if not cur then return nil end
		cur = cur:FindFirstChild(name)
	end
	return cur
end

local function scanTrafficParts()
	trafficParts = {}
	local folder = getTrafficFolder()
	if not folder then return end

	for _, inst in ipairs(folder:GetDescendants()) do
		if inst:IsA("BasePart") then
			-- prefer primary parts when possible; but this still works even if we only find body parts
			table.insert(trafficParts, inst)
		end
	end
end

local function closestTrafficDistance(pos: Vector3)
	local best = math.huge
	for _, p in ipairs(trafficParts) do
		if p and p.Parent then
			local d = (p.Position - pos).Magnitude
			if d < best then
				best = d
			end
		end
	end
	return best
end

RunService.RenderStepped:Connect(function(dt)
	-- Only shake when in road mode
	if currentMode ~= "road" then
		shakeStrength = 0
		return
	end

	local char = player.Character
	local hrp = char and char:FindFirstChild("HumanoidRootPart")
	if not hrp then
		shakeStrength = 0
		return
	end

	-- refresh traffic list occasionally
	local now = os.clock()
	if (now - lastTrafficScan) >= TRAFFIC_SCAN_INTERVAL then
		lastTrafficScan = now
		scanTrafficParts()
	end

	local dist = closestTrafficDistance(hrp.Position)
	local target = 0
	if dist < math.huge then
		local t = clamp((TRAFFIC_SHAKE_RADIUS - dist) / TRAFFIC_SHAKE_RADIUS, 0, 1)
		target = t * t -- ease in stronger when very close
	end

	-- smooth
	shakeStrength = shakeStrength + ((target - shakeStrength) * clamp(dt / TRAFFIC_SHAKE_SMOOTH, 0, 1))
	if shakeStrength <= 0.001 then
		return
	end

	-- Perlin noise based shake (stable, not jittery)
	local t = now * SHAKE_FREQ
	local nx = math.noise(t, 0, 0)
	local ny = math.noise(0, t, 0)
	local nr = math.noise(0, 0, t)

	local off = Vector3.new(nx, ny * 0.6, 0) * (TRAFFIC_SHAKE_MAX_OFFSET * shakeStrength)
	local rot = math.rad(TRAFFIC_SHAKE_MAX_ROT_DEG) * shakeStrength
	local ang = Vector3.new(0, 0, nr * rot)

	if camera then
		camera.CFrame = camera.CFrame * CFrame.new(off) * CFrame.Angles(ang.X, ang.Y, ang.Z)
	end
end)

task.spawn(function()
	while true do
		task.wait(CHECK_INTERVAL)
		update()
	end
end)

print("✅ RoadCamera initialized")
