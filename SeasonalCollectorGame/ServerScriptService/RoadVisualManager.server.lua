-- RoadVisualManager.server.lua
-- Automatically upgrades road visuals: lane lines + edge lines
-- Place in ServerScriptService

local Workspace = game:GetService("Workspace")
local CollectionService = game:GetService("CollectionService")

local ROAD_TAG = "Road" -- optional (if you tag your road parts)

local DECOR_FOLDER_NAME = "RoadDecor"
local LINE_HEIGHT = 0.08
local LINE_THICKNESS = 0.25
local CENTER_GAP = 0.4

local EDGE_LINE_THICKNESS = 0.22
local EDGE_INSET = 0.7

local REFRESH_INTERVAL = 5

local function looksLikeRoadPart(part: Instance)
	if not part or not part:IsA("BasePart") then return false end
	local name = string.lower(part.Name or "")
	if name:find("road", 1, true) or name:find("street", 1, true) or name:find("track", 1, true) then
		return true
	end
	local mat = part.Material
	return (mat == Enum.Material.Asphalt or mat == Enum.Material.Concrete)
end

local function getDecorFolder()
	local f = Workspace:FindFirstChild(DECOR_FOLDER_NAME)
	if not f then
		f = Instance.new("Folder")
		f.Name = DECOR_FOLDER_NAME
		f.Parent = Workspace
	end
	return f
end

local function safeIgnore(part: Instance)
	if not part or not part.Parent then return true end
	local ignoreNames = {"Obstacles", "Coins", "Collectibles", "Bank", "Players", "RoadDecor"}
	for _, n in ipairs(ignoreNames) do
		local folder = Workspace:FindFirstChild(n)
		if folder and part:IsDescendantOf(folder) then
			return true
		end
	end
	return false
end

local function clearRoadDecorFor(road: BasePart, decorFolder: Folder)
	local key = tostring(road:GetDebugId())
	for _, d in ipairs(decorFolder:GetChildren()) do
		if d:GetAttribute("RoadKey") == key then
			d:Destroy()
		end
	end
end

local function makeLine(parent: Instance, size: Vector3, cf: CFrame, color: Color3, key: string)
	local p = Instance.new("Part")
	p.Name = "RoadLine"
	p.Anchored = true
	p.CanCollide = false
	p.CanTouch = false
	p.CanQuery = false
	p.Material = Enum.Material.Neon
	p.Color = color
	p.Size = size
	p.CFrame = cf
	p:SetAttribute("RoadKey", key)
	p.Parent = parent
	return p
end

local function decorateRoad(road: BasePart)
	if not road or not road.Parent then return end
	if safeIgnore(road) then return end

	-- Don’t decorate tiny pieces
	if math.max(road.Size.X, road.Size.Z) < 18 then return end

	local decorFolder = getDecorFolder()
	local key = tostring(road:GetDebugId())
	clearRoadDecorFor(road, decorFolder)

	-- Determine road direction (assume long axis is Z)
	local longIsZ = road.Size.Z >= road.Size.X
	local forward = longIsZ and road.CFrame.LookVector or road.CFrame.RightVector
	local right = longIsZ and road.CFrame.RightVector or -road.CFrame.LookVector

	local length = longIsZ and road.Size.Z or road.Size.X
	local width = longIsZ and road.Size.X or road.Size.Z

	local y = (road.Position.Y + (road.Size.Y * 0.5)) + LINE_HEIGHT

	-- Center double yellow
	local centerLen = math.max(6, length - 2)
	local centerSize = Vector3.new(LINE_THICKNESS, 0.12, centerLen)

	local centerCf = CFrame.new(Vector3.new(road.Position.X, y, road.Position.Z), Vector3.new(road.Position.X, y, road.Position.Z) + forward)
	local leftCf = centerCf * CFrame.new(-CENTER_GAP, 0, 0)
	local rightCf = centerCf * CFrame.new(CENTER_GAP, 0, 0)

	makeLine(decorFolder, centerSize, leftCf, Color3.fromRGB(255, 220, 0), key)
	makeLine(decorFolder, centerSize, rightCf, Color3.fromRGB(255, 220, 0), key)

	-- Edge white lines
	local edgeLen = centerLen
	local edgeSize = Vector3.new(EDGE_LINE_THICKNESS, 0.12, edgeLen)
	local halfW = (width * 0.5)
	local edgeOffset = math.max(EDGE_INSET, halfW - 1)

	local edgeLCf = centerCf * CFrame.new(-edgeOffset, 0, 0)
	local edgeRCf = centerCf * CFrame.new(edgeOffset, 0, 0)

	makeLine(decorFolder, edgeSize, edgeLCf, Color3.fromRGB(245, 245, 245), key)
	makeLine(decorFolder, edgeSize, edgeRCf, Color3.fromRGB(245, 245, 245), key)
end

local function getRoadCandidates()
	local roads = {}

	for _, inst in ipairs(CollectionService:GetTagged(ROAD_TAG)) do
		if inst:IsA("BasePart") and not safeIgnore(inst) then
			roads[inst] = true
		end
	end

	for _, inst in ipairs(Workspace:GetDescendants()) do
		if inst:IsA("BasePart") and looksLikeRoadPart(inst) and not safeIgnore(inst) then
			roads[inst] = true
		end
	end

	local list = {}
	for r, _ in pairs(roads) do
		table.insert(list, r)
	end
	return list
end

task.spawn(function()
	task.wait(2)
	while true do
		local roads = getRoadCandidates()
		for _, road in ipairs(roads) do
			decorateRoad(road)
		end
		task.wait(REFRESH_INTERVAL)
	end
end)

print("✅ RoadVisualManager initialized (lane + edge lines)")
