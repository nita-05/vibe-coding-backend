from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class FileSpec:
    path: str
    content: str


def _server_autobuild_script() -> str:
    return """-- AutoBuildEnvironment.server.lua
-- Paste into ServerScriptService in an EMPTY place, then press Play.
-- It will create a simple coin-collector prototype environment.

local Workspace = game:GetService(\"Workspace\")
local ReplicatedStorage = game:GetService(\"ReplicatedStorage\")

local function getOrCreateFolder(parent: Instance, name: string)
\tlocal f = parent:FindFirstChild(name)
\tif not f then
\t\tf = Instance.new(\"Folder\")
\t\tf.Name = name
\t\tf.Parent = parent
\tend
\treturn f
end

-- Base terrain
if not Workspace:FindFirstChild(\"Ground\") then
\tlocal ground = Instance.new(\"Part\")
\tground.Name = \"Ground\"
\tground.Size = Vector3.new(512, 1, 512)
\tground.Anchored = true
\tground.Material = Enum.Material.Grass
\tground.Position = Vector3.new(0, 0, 0)
\tground.Parent = Workspace
end

-- Simple road strip
local road = Workspace:FindFirstChild(\"Road\")
if not road then
\troad = Instance.new(\"Part\")
\troad.Name = \"Road\"
\troad.Size = Vector3.new(80, 1, 320)
\troad.Anchored = true
\troad.Material = Enum.Material.Asphalt
\troad.Color = Color3.fromRGB(35, 35, 35)
\troad.Position = Vector3.new(0, 0.5, 0)
\troad.Parent = Workspace
end

-- Folders
local coinsFolder = getOrCreateFolder(Workspace, \"Coins\")
local obstaclesFolder = getOrCreateFolder(Workspace, \"Obstacles\")

-- RemoteEvents
local events = ReplicatedStorage:FindFirstChild(\"RemoteEvents\")
if not events then
\tevents = Instance.new(\"Folder\")
\tevents.Name = \"RemoteEvents\"
\tevents.Parent = ReplicatedStorage
end
local coinEvt = events:FindFirstChild(\"CoinCollected\")
if not coinEvt then
\tcoinEvt = Instance.new(\"RemoteEvent\")
\tcoinEvt.Name = \"CoinCollected\"
\tcoinEvt.Parent = events
end

-- Spawn coin parts along road
if coinsFolder:GetAttribute(\"__CoinsSpawned\") ~= true then
\tcoinsFolder:SetAttribute(\"__CoinsSpawned\", true)
\tfor i = 1, 40 do
\t\tlocal c = Instance.new(\"Part\")
\t\tc.Name = \"Coin\"
\t\tc.Shape = Enum.PartType.Cylinder
\t\tc.Size = Vector3.new(1.2, 0.3, 1.2)
\t\tc.Anchored = true
\t\tc.CanCollide = false
\t\tc.Material = Enum.Material.Neon
\t\tc.Color = Color3.fromRGB(255, 220, 0)
\t\tlocal x = math.random(-16, 16)
\t\tlocal z = -140 + (i * 7)
\t\tc.CFrame = CFrame.new(road.Position + Vector3.new(x, 2.2, z)) * CFrame.Angles(0, 0, math.rad(90))
\t\tc.Parent = coinsFolder
\tend
end

-- Spawn a few simple obstacle blocks
if obstaclesFolder:GetAttribute(\"__ObstaclesSpawned\") ~= true then
\tobstaclesFolder:SetAttribute(\"__ObstaclesSpawned\", true)
\tfor i = 1, 16 do
\t\tlocal b = Instance.new(\"Part\")
\t\tb.Name = \"Obstacle\"
\t\tb.Size = Vector3.new(math.random(3, 7), math.random(3, 5), math.random(3, 7))
\t\tb.Anchored = true
\t\tb.CanCollide = true
\t\tb.Material = Enum.Material.Concrete
\t\tb.Color = Color3.fromRGB(200, 60, 60)
\t\tlocal x = math.random(-28, 28)
\t\tlocal z = -140 + (i * 18)
\t\tb.Position = road.Position + Vector3.new(x, b.Size.Y/2 + 0.5, z)
\t\tb.Parent = obstaclesFolder
\tend
end

print(\"✅ AutoBuildEnvironment complete (Coins + Obstacles).\")
"""


def _coin_service_script() -> str:
    return """-- CoinService.server.lua
-- Coins are simple parts inside Workspace/Coins named "Coin".
-- Touching a coin awards +1 and destroys that coin.

local Players = game:GetService(\"Players\")
local Workspace = game:GetService(\"Workspace\")
local ReplicatedStorage = game:GetService(\"ReplicatedStorage\")

local events = ReplicatedStorage:WaitForChild(\"RemoteEvents\")
local coinEvt = events:WaitForChild(\"CoinCollected\")

local coinsFolder = Workspace:WaitForChild(\"Coins\")

local touchDebounce: {[BasePart]: boolean} = {}

local function ensureLeaderstats(plr: Player)
\tlocal ls = plr:FindFirstChild(\"leaderstats\")
\tif not ls then
\t\tls = Instance.new(\"Folder\")
\t\tls.Name = \"leaderstats\"
\t\tls.Parent = plr
\tend
\tlocal coins = ls:FindFirstChild(\"Coins\")
\tif not coins then
\t\tcoins = Instance.new(\"IntValue\")
\t\tcoins.Name = \"Coins\"
\t\tcoins.Value = 0
\t\tcoins.Parent = ls
\tend
\treturn coins
end

local function awardCoin(plr: Player)
\tlocal coins = ensureLeaderstats(plr)
\tcoins.Value += 1
\tcoinEvt:FireClient(plr, coins.Value)
end

local function hookCoin(part: BasePart)
\tif touchDebounce[part] ~= nil then return end
\ttouchDebounce[part] = false
\tpart.Touched:Connect(function(hit)
\t\tlocal char = hit:FindFirstAncestorOfClass(\"Model\")
\t\tlocal plr = char and Players:GetPlayerFromCharacter(char)
\t\tif not plr then return end
\t\tif touchDebounce[part] then return end
\t\ttouchDebounce[part] = true
\t\tawardCoin(plr)
\t\tpart:Destroy()
\tend)
end

for _, inst in ipairs(coinsFolder:GetChildren()) do
\tif inst:IsA(\"BasePart\") and inst.Name == \"Coin\" then
\t\thookCoin(inst)
\tend
end

coinsFolder.ChildAdded:Connect(function(inst)
\tif inst:IsA(\"BasePart\") and inst.Name == \"Coin\" then
\t\thookCoin(inst)
\tend
end)

Players.PlayerAdded:Connect(function(plr)
\tensureLeaderstats(plr)
end)

print(\"✅ CoinService initialized\")
"""


def _hazard_manager_script() -> str:
    return """-- HazardManager.server.lua (minimal)
-- Any part inside Workspace/Obstacles named "Obstacle" kills the player on touch.

local Workspace = game:GetService(\"Workspace\")
local Players = game:GetService(\"Players\")

local obstacles = Workspace:WaitForChild(\"Obstacles\")
local hitCooldown: {[Player]: number} = {}
local COOLDOWN = 0.75

local function kill(plr: Player)
\tlocal now = os.clock()
\tlocal last = hitCooldown[plr]
\tif last and (now - last) < COOLDOWN then return end
\thitCooldown[plr] = now
\tlocal hum = plr.Character and plr.Character:FindFirstChildOfClass(\"Humanoid\")
\tif hum and hum.Health > 0 then
\t\thum.Health = 0
\tend
end

local function hookObstacle(p: BasePart)
\tp.Touched:Connect(function(hit)
\t\tlocal char = hit:FindFirstAncestorOfClass(\"Model\")
\t\tlocal plr = char and Players:GetPlayerFromCharacter(char)
\t\tif plr then
\t\t\tkill(plr)
\t\tend
\tend)
end

for _, inst in ipairs(obstacles:GetChildren()) do
\tif inst:IsA(\"BasePart\") and inst.Name == \"Obstacle\" then
\t\thookObstacle(inst)
\tend
end

obstacles.ChildAdded:Connect(function(inst)
\tif inst:IsA(\"BasePart\") and inst.Name == \"Obstacle\" then
\t\thookObstacle(inst)
\tend
end)

print(\"✅ HazardManager initialized (cars are NOT used as obstacles)\")
"""


def _ui_script() -> str:
    return """-- GameUI.client.lua
-- Shows a simple coin counter.

local Players = game:GetService(\"Players\")
local ReplicatedStorage = game:GetService(\"ReplicatedStorage\")

local player = Players.LocalPlayer
local events = ReplicatedStorage:WaitForChild(\"RemoteEvents\")
local coinEvt = events:WaitForChild(\"CoinCollected\")

local gui = Instance.new(\"ScreenGui\")
gui.Name = \"CoinUI\"
gui.ResetOnSpawn = false
gui.Parent = player:WaitForChild(\"PlayerGui\")

local label = Instance.new(\"TextLabel\")
label.Size = UDim2.new(0, 220, 0, 42)
label.Position = UDim2.new(0, 16, 0, 16)
label.BackgroundTransparency = 0.25
label.BackgroundColor3 = Color3.fromRGB(20, 20, 20)
label.TextColor3 = Color3.fromRGB(255, 255, 255)
label.Font = Enum.Font.GothamBold
label.TextSize = 20
label.Text = \"Coins: 0\"
label.Parent = gui

coinEvt.OnClientEvent:Connect(function(total)
\tlabel.Text = \"Coins: \" .. tostring(total)
end)
"""


def coin_collector_pack(prompt: str) -> Dict[str, Any]:
    _ = prompt  # prompt-aware templates can be added later

    files: List[FileSpec] = [
        FileSpec(path="ServerScriptService/AutoBuildEnvironment.server.lua", content=_server_autobuild_script()),
        FileSpec(path="ServerScriptService/CoinService.server.lua", content=_coin_service_script()),
        FileSpec(path="ServerScriptService/HazardManager.server.lua", content=_hazard_manager_script()),
        FileSpec(path="StarterPlayer/StarterPlayerScripts/GameUI.client.lua", content=_ui_script()),
    ]

    return {
        "title": "Coin Collector (Prototype)",
        "description": "A simple, playable coin collector with obstacles. Paste scripts into Roblox Studio and press Play.",
        "files": [
            {"path": f.path, "content": f.content} for f in files
        ],
        "setup_instructions": [
            "Create a NEW Roblox place (Baseplate is fine).",
            "In Explorer: create the script files listed under the given paths.",
            "Press Play: AutoBuildEnvironment will generate Coins + Obstacles folders.",
            "Touch coins to collect them; touching obstacles kills the player.",
        ],
        "notes": [
            "This is the offline fallback pack (no AI key required).",
            "Cars are not used as obstacles in this prototype.",
        ],
    }


def seasonal_collector_pack_ai(_: str) -> Dict[str, Any]:
    """Offline fallback for the 'Seasonal Collector (AI)' game type.

    This is intentionally small; real AI should generate richer gameplay when OPENAI_API_KEY is set.
    """

    files = [
        {
            "path": "ServerScriptService/AutoBuildSeasonalCollector.server.lua",
            "content": """-- AutoBuildSeasonalCollector.server.lua
-- Builds a tiny seasonal coin collector map (no repo imports).

local Workspace = game:GetService("Workspace")
local Lighting = game:GetService("Lighting")

local function getOrCreateFolder(parent: Instance, name: string)
\tlocal f = parent:FindFirstChild(name)
\tif not f then
\t\tf = Instance.new("Folder")
\t\tf.Name = name
\t\tf.Parent = parent
\tend
\treturn f
end

local coins = getOrCreateFolder(Workspace, "Coins")
local obstacles = getOrCreateFolder(Workspace, "Obstacles")

if not Workspace:FindFirstChild("Ground") then
\tlocal g = Instance.new("Part")
\tg.Name = "Ground"
\tg.Size = Vector3.new(420, 1, 420)
\tg.Anchored = true
\tg.Material = Enum.Material.Grass
\tg.Position = Vector3.new(0, 0, 0)
\tg.Parent = Workspace
end

local road = Workspace:FindFirstChild("Road")
if not road then
\troad = Instance.new("Part")
\troad.Name = "Road"
\troad.Size = Vector3.new(70, 1, 260)
\troad.Anchored = true
\troad.Material = Enum.Material.Asphalt
\troad.Color = Color3.fromRGB(35, 35, 35)
\troad.Position = Vector3.new(0, 0.5, 0)
\troad.Parent = Workspace
end

local function spawnCoin(pos: Vector3)
\tlocal c = Instance.new("Part")
\tc.Name = "Coin"
\tc.Shape = Enum.PartType.Cylinder
\tc.Size = Vector3.new(1.2, 0.3, 1.2)
\tc.Anchored = true
\tc.CanCollide = false
\tc.Material = Enum.Material.Neon
\tc.Color = Color3.fromRGB(255, 220, 0)
\tc.CFrame = CFrame.new(pos) * CFrame.Angles(0, 0, math.rad(90))
\tc.Parent = coins
end

local function spawnObstacle(pos: Vector3)
\tlocal o = Instance.new("Part")
\to.Name = "Obstacle"
\to.Anchored = true
\to.CanCollide = true
\to.Size = Vector3.new(math.random(3, 6), math.random(3, 5), math.random(3, 6))
\to.Material = Enum.Material.Concrete
\to.Color = Color3.fromRGB(210, 70, 70)
\to.Position = pos + Vector3.new(0, o.Size.Y/2 + 0.5, 0)
\to.Parent = obstacles
end

if coins:GetAttribute("__Spawned") ~= true then
\tcoins:SetAttribute("__Spawned", true)
\tfor i = 1, 36 do
\t\tspawnCoin(road.Position + Vector3.new(math.random(-14, 14), 2.2, -120 + (i * 7)))
\tend
end

if obstacles:GetAttribute("__Spawned") ~= true then
\tobstacles:SetAttribute("__Spawned", true)
\tfor i = 1, 14 do
\t\tspawnObstacle(road.Position + Vector3.new(math.random(-20, 20), 0, -110 + (i * 16)))
\tend
end

-- simple seasonal vibe (cycle)
Lighting.ClockTime = 14
print("✅ Seasonal Collector map built")
""",
        },
        {
            "path": "ServerScriptService/SeasonManager.server.lua",
            "content": """-- SeasonManager.server.lua
-- Simple season/day-night flavor (no external assets).

local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local events = ReplicatedStorage:FindFirstChild("RemoteEvents")
if not events then
\tevents = Instance.new("Folder")
\tevents.Name = "RemoteEvents"
\tevents.Parent = ReplicatedStorage
end

local seasonEvt = events:FindFirstChild("SeasonChanged")
if not seasonEvt then
\tseasonEvt = Instance.new("RemoteEvent")
\tseasonEvt.Name = "SeasonChanged"
\tseasonEvt.Parent = events
end

local seasons = {
\t{ name = "Spring", ambient = Color3.fromRGB(180, 255, 200), time = 9 },
\t{ name = "Summer", ambient = Color3.fromRGB(255, 245, 210), time = 14 },
\t{ name = "Autumn", ambient = Color3.fromRGB(255, 215, 160), time = 17 },
\t{ name = "Winter", ambient = Color3.fromRGB(210, 235, 255), time = 20 },
}

local idx = 1
task.spawn(function()
\twhile true do
\t\tlocal s = seasons[idx]
\t\tLighting.Ambient = s.ambient
\t\tLighting.ClockTime = s.time
\t\tseasonEvt:FireAllClients(s.name)
\t\tidx += 1
\t\tif idx > #seasons then idx = 1 end
\t\ttask.wait(30)
\tend
end)

print("✅ SeasonManager initialized")
""",
        },
        {
            "path": "ServerScriptService/CoinService.server.lua",
            "content": _coin_service_script(),
        },
        {
            "path": "ServerScriptService/HazardManager.server.lua",
            "content": _hazard_manager_script(),
        },
        {
            "path": "StarterPlayer/StarterPlayerScripts/SeasonalUI.client.lua",
            "content": """-- SeasonalUI.client.lua
-- Shows coins + current season.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local player = Players.LocalPlayer
local events = ReplicatedStorage:WaitForChild("RemoteEvents")
local coinEvt = events:WaitForChild("CoinCollected")
local seasonEvt = events:WaitForChild("SeasonChanged")

local gui = Instance.new("ScreenGui")
gui.Name = "SeasonalUI"
gui.ResetOnSpawn = false
gui.Parent = player:WaitForChild("PlayerGui")

local label = Instance.new("TextLabel")
label.Size = UDim2.new(0, 320, 0, 42)
label.Position = UDim2.new(0, 16, 0, 16)
label.BackgroundTransparency = 0.25
label.BackgroundColor3 = Color3.fromRGB(20, 20, 20)
label.TextColor3 = Color3.fromRGB(255, 255, 255)
label.Font = Enum.Font.GothamBold
label.TextSize = 18
label.Text = "Coins: 0 | Season: Summer"
label.Parent = gui

local coins = 0
local season = "Summer"

local function refresh()
\tlabel.Text = ("Coins: %d | Season: %s"):format(coins, season)
end

coinEvt.OnClientEvent:Connect(function(total)
\tcoins = tonumber(total) or coins
\trefresh()
end)

seasonEvt.OnClientEvent:Connect(function(name)
\tseason = tostring(name or season)
\trefresh()
end)
""",
        },
    ]

    return {
        "title": "Seasonal Collector (Prototype)",
        "description": "A small seasonal coin collector with obstacles and a season cycle (offline fallback).",
        "files": files,
        "setup_instructions": [
            "Create a NEW Roblox place (Baseplate is fine).",
            "Create the scripts at the listed paths.",
            "Press Play: the map builds, coins spawn, obstacles kill, season cycles every 30 seconds.",
        ],
        "notes": [
            "Offline fallback pack (no AI key required).",
            "Cars are not used as obstacles.",
        ],
    }


def obby_pack(_: str) -> Dict[str, Any]:
    # Minimal fallback: AI should normally generate this when OPENAI_API_KEY is set.
    files = [
        {
            "path": "ServerScriptService/AutoBuildObby.server.lua",
            "content": """-- AutoBuildObby.server.lua
-- Creates a simple 10-stage obby with checkpoints + finish pad.

local Workspace = game:GetService("Workspace")

local function getOrCreateFolder(parent: Instance, name: string)
\tlocal f = parent:FindFirstChild(name)
\tif not f then
\t\tf = Instance.new("Folder")
\t\tf.Name = name
\t\tf.Parent = parent
\tend
\treturn f
end

local folder = getOrCreateFolder(Workspace, "Obby")
if folder:GetAttribute("__Built") == true then return end
folder:SetAttribute("__Built", true)

-- SpawnLocation
local sp = Workspace:FindFirstChildOfClass("SpawnLocation")
if not sp then
\tsp = Instance.new("SpawnLocation")
\tsp.Size = Vector3.new(8, 1, 8)
\tsp.Anchored = true
\tsp.Position = Vector3.new(0, 3, 0)
\tsp.Parent = Workspace
end

local function mk(name, pos, size, color, material)
\tlocal p = Instance.new("Part")
\tp.Name = name
\tp.Anchored = true
\tp.Size = size
\tp.Position = pos
\tp.Color = color
\tp.Material = material
\tp.Parent = folder
\treturn p
end

mk("Start", Vector3.new(0, 2, 0), Vector3.new(20, 1, 20), Color3.fromRGB(60, 200, 90), Enum.Material.Grass)

local x, y, z = 0, 5, 0
for i = 1, 10 do
\tx += 16
\tz += 10
\tmk(("Stage_%02d"):format(i), Vector3.new(x, y, z), Vector3.new(12, 1, 12), Color3.fromRGB(75, 120, 255), Enum.Material.SmoothPlastic)

\tlocal checkpoint = Instance.new("SpawnLocation")
\tcheckpoint.Name = "Checkpoint_" .. i
\tcheckpoint.Anchored = true
\tcheckpoint.Size = Vector3.new(8, 1, 8)
\tcheckpoint.Position = Vector3.new(x, y + 2, z)
\tcheckpoint.Neutral = true
\tcheckpoint.Enabled = true
\tcheckpoint.Parent = folder

\tlocal kill = mk("KillBrick_" .. i, Vector3.new(x - 8, y + 1, z - 5), Vector3.new(10, 1, 10), Color3.fromRGB(255, 70, 70), Enum.Material.Neon)
\tkill:SetAttribute("__Kill", true)
end

local finish = mk("Finish", Vector3.new(x + 18, y, z + 10), Vector3.new(18, 1, 18), Color3.fromRGB(255, 220, 0), Enum.Material.Neon)
finish:SetAttribute("__Finish", true)

print("✅ Obby built")
""",
        },
        {
            "path": "ServerScriptService/ObbyRules.server.lua",
            "content": """-- ObbyRules.server.lua
-- Kill bricks reset player; finish pad prints a win message.

local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")

local folder = Workspace:WaitForChild("Obby")

local function kill(plr: Player)
\tlocal hum = plr.Character and plr.Character:FindFirstChildOfClass("Humanoid")
\tif hum and hum.Health > 0 then hum.Health = 0 end
end

local function hook(part: BasePart)
\tpart.Touched:Connect(function(hit)
\t\tlocal char = hit:FindFirstAncestorOfClass("Model")
\t\tlocal plr = char and Players:GetPlayerFromCharacter(char)
\t\tif not plr then return end
\t\tif part:GetAttribute("__Kill") then
\t\t\tkill(plr)
\t\telseif part:GetAttribute("__Finish") then
\t\t\tprint(("🏁 %s finished the obby!"):format(plr.Name))
\t\tend
\tend)
end

for _, inst in ipairs(folder:GetDescendants()) do
\tif inst:IsA("BasePart") and (inst:GetAttribute("__Kill") or inst:GetAttribute("__Finish")) then
\t\thook(inst)
\tend
end

folder.DescendantAdded:Connect(function(inst)
\tif inst:IsA("BasePart") and (inst:GetAttribute("__Kill") or inst:GetAttribute("__Finish")) then
\t\thook(inst)
\tend
end)
""",
        },
    ]

    return {
        "title": "Obby (Prototype)",
        "description": "A simple 10-stage obby with checkpoints + kill bricks.",
        "files": files,
        "setup_instructions": [
            "Create a NEW Roblox place (Baseplate is fine).",
            "Create the two ServerScriptService scripts and press Play.",
        ],
        "notes": [
            "Offline fallback pack (no AI key required).",
            "For best results, use AI with your own prompt to customize stages.",
        ],
    }


def runner_pack(_: str) -> Dict[str, Any]:
    files = [
        {
            "path": "ServerScriptService/AutoBuildRunner.server.lua",
            "content": """-- AutoBuildRunner.server.lua
-- Creates a simple endless runner lane + obstacle folder.

local Workspace = game:GetService("Workspace")

local lane = Workspace:FindFirstChild("RunnerLane")
if not lane then
\tlane = Instance.new("Part")
\tlane.Name = "RunnerLane"
\tlane.Anchored = true
\tlane.Size = Vector3.new(30, 1, 600)
\tlane.Material = Enum.Material.Asphalt
\tlane.Color = Color3.fromRGB(35, 35, 35)
\tlane.Position = Vector3.new(0, 0.5, -250)
\tlane.Parent = Workspace
end

local folder = Workspace:FindFirstChild("RunnerObstacles")
if not folder then
\tfolder = Instance.new("Folder")
\tfolder.Name = "RunnerObstacles"
\tfolder.Parent = Workspace
end

print("✅ Runner lane built")
""",
        },
        {
            "path": "ServerScriptService/RunnerManager.server.lua",
            "content": """-- RunnerManager.server.lua
-- Spawns obstacles; touching them resets the player.

local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")

local folder = Workspace:WaitForChild("RunnerObstacles")

local SPAWN_EVERY = 1.0
local LIFETIME = 18

local function reset(plr: Player)
\tif plr and plr.Character then plr:LoadCharacter() end
end

local function hook(p: BasePart)
\tp.Touched:Connect(function(hit)
\t\tlocal char = hit:FindFirstAncestorOfClass("Model")
\t\tlocal plr = char and Players:GetPlayerFromCharacter(char)
\t\tif plr then reset(plr) end
\tend)
end

local function spawnObstacle()
\tlocal p = Instance.new("Part")
\tp.Name = "RunnerObstacle"
\tp.Anchored = true
\tp.Size = Vector3.new(math.random(3, 7), math.random(3, 6), math.random(3, 7))
\tp.Color = Color3.fromRGB(220, 70, 70)
\tp.Material = Enum.Material.Concrete
\tp.Position = Vector3.new(math.random(-10, 10), p.Size.Y/2 + 0.5, -60 - math.random(0, 220))
\tp.Parent = folder
\thook(p)
\ttask.delay(LIFETIME, function() if p.Parent then p:Destroy() end end)
end

task.spawn(function()
\twhile true do
\t\ttask.wait(SPAWN_EVERY)
\t\tif math.random() < 0.45 then spawnObstacle() end
\tend
end)

print("✅ RunnerManager initialized")
""",
        },
        {
            "path": "StarterPlayer/StarterPlayerScripts/RunnerUI.client.lua",
            "content": """-- RunnerUI.client.lua
-- Shows distance traveled.

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local player = Players.LocalPlayer

local gui = Instance.new("ScreenGui")
gui.Name = "RunnerUI"
gui.ResetOnSpawn = false
gui.Parent = player:WaitForChild("PlayerGui")

local label = Instance.new("TextLabel")
label.Size = UDim2.new(0, 260, 0, 42)
label.Position = UDim2.new(0, 16, 0, 16)
label.BackgroundTransparency = 0.25
label.BackgroundColor3 = Color3.fromRGB(20, 20, 20)
label.TextColor3 = Color3.fromRGB(255, 255, 255)
label.Font = Enum.Font.GothamBold
label.TextSize = 20
label.Text = "Distance: 0"
label.Parent = gui

local startZ = nil
RunService.RenderStepped:Connect(function()
\tlocal char = player.Character
\tlocal hrp = char and char:FindFirstChild("HumanoidRootPart")
\tif not hrp then return end
\tif not startZ then startZ = hrp.Position.Z end
\tlocal dist = math.max(0, startZ - hrp.Position.Z)
\tlabel.Text = ("Distance: %d"):format(dist)
end)
""",
        },
    ]

    return {
        "title": "Endless Runner (Prototype)",
        "description": "A simple endless runner with spawning obstacles and a distance UI.",
        "files": files,
        "setup_instructions": [
            "Create a NEW Roblox place (Baseplate is fine).",
            "Create the scripts at the listed paths.",
            "Press Play: the lane is built; obstacles spawn; distance UI updates.",
        ],
        "notes": [
            "Offline fallback pack (no AI key required).",
            "Cars are not used as obstacles.",
        ],
    }


def tycoon_pack(_: str) -> Dict[str, Any]:
    files = [
        {
            "path": "ServerScriptService/AutoBuildTycoon.server.lua",
            "content": """-- AutoBuildTycoon.server.lua
-- Creates a minimal tycoon: a dropper + collector + upgrade button.

local Workspace = game:GetService("Workspace")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local function getOrCreateFolder(parent: Instance, name: string)
\tlocal f = parent:FindFirstChild(name)
\tif not f then
\t\tf = Instance.new("Folder")
\t\tf.Name = name
\t\tf.Parent = parent
\tend
\treturn f
end

local events = ReplicatedStorage:FindFirstChild("RemoteEvents")
if not events then
\tevents = Instance.new("Folder")
\tevents.Name = "RemoteEvents"
\tevents.Parent = ReplicatedStorage
end
local buyEvt = events:FindFirstChild("TycoonBuyUpgrade")
if not buyEvt then
\tbuyEvt = Instance.new("RemoteEvent")
\tbuyEvt.Name = "TycoonBuyUpgrade"
\tbuyEvt.Parent = events
end

local folder = getOrCreateFolder(Workspace, "Tycoon")
if folder:GetAttribute("__Built") == true then return end
folder:SetAttribute("__Built", true)

local base = Instance.new("Part")
base.Name = "TycoonBase"
base.Anchored = true
base.Size = Vector3.new(60, 1, 60)
base.Position = Vector3.new(0, 0.5, 0)
base.Material = Enum.Material.Concrete
base.Color = Color3.fromRGB(90, 90, 110)
base.Parent = folder

local dropper = Instance.new("Part")
dropper.Name = "Dropper"
dropper.Anchored = true
dropper.Size = Vector3.new(8, 8, 8)
dropper.Position = Vector3.new(-18, 5, 0)
dropper.Material = Enum.Material.Metal
dropper.Color = Color3.fromRGB(170, 170, 170)
dropper.Parent = folder

local collector = Instance.new("Part")
collector.Name = "Collector"
collector.Anchored = true
collector.Size = Vector3.new(14, 2, 14)
collector.Position = Vector3.new(18, 1.5, 0)
collector.Material = Enum.Material.Neon
collector.Color = Color3.fromRGB(50, 220, 120)
collector.Parent = folder

local buy = Instance.new("Part")
buy.Name = "UpgradeButton"
buy.Anchored = true
buy.Size = Vector3.new(10, 1, 10)
buy.Position = Vector3.new(0, 1.2, -18)
buy.Material = Enum.Material.Neon
buy.Color = Color3.fromRGB(255, 220, 0)
buy.Parent = folder
buy:SetAttribute("__Cost", 10)

print("✅ Tycoon built")
""",
        },
        {
            "path": "ServerScriptService/TycoonManager.server.lua",
            "content": """-- TycoonManager.server.lua
-- Dropper spawns Cash balls; collector awards Money; upgrade button increases rate.

local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local folder = Workspace:WaitForChild("Tycoon")
local dropper = folder:WaitForChild("Dropper")
local collector = folder:WaitForChild("Collector")
local button = folder:WaitForChild("UpgradeButton")

local events = ReplicatedStorage:WaitForChild("RemoteEvents")
local buyEvt = events:WaitForChild("TycoonBuyUpgrade")

local RATE_ATTR = "__DropRate"
folder:SetAttribute(RATE_ATTR, folder:GetAttribute(RATE_ATTR) or 1.0)

local function ensureLeaderstats(plr: Player)
\tlocal ls = plr:FindFirstChild("leaderstats")
\tif not ls then
\t\tls = Instance.new("Folder")
\t\tls.Name = "leaderstats"
\t\tls.Parent = plr
\tend
\tlocal money = ls:FindFirstChild("Money")
\tif not money then
\t\tmoney = Instance.new("IntValue")
\t\tmoney.Name = "Money"
\t\tmoney.Value = 0
\t\tmoney.Parent = ls
\tend
\treturn money
end

Players.PlayerAdded:Connect(function(plr) ensureLeaderstats(plr) end)

local function spawnCash()
\tlocal cash = Instance.new("Part")
\tcash.Name = "Cash"
\tcash.Shape = Enum.PartType.Ball
\tcash.Size = Vector3.new(1.5, 1.5, 1.5)
\tcash.Material = Enum.Material.Neon
\tcash.Color = Color3.fromRGB(80, 220, 120)
\tcash.Position = dropper.Position + Vector3.new(0, 6, 0)
\tcash.CanCollide = true
\tcash.Anchored = false
\tcash.Parent = folder
\ttask.delay(10, function() if cash and cash.Parent then cash:Destroy() end end)
end

task.spawn(function()
\twhile true do
\t\tlocal rate = tonumber(folder:GetAttribute(RATE_ATTR)) or 1.0
\t\tspawnCash()
\t\ttask.wait(math.max(0.2, 1.0 / rate))
\tend
end)

collector.Touched:Connect(function(hit)
\tif hit and hit:IsA("BasePart") and hit.Name == "Cash" then
\t\thit:Destroy()
\t\t-- award to the player touching the collector (best effort)
\t\tlocal char = hit:FindFirstAncestorOfClass("Model")
\t\tlocal plr = char and Players:GetPlayerFromCharacter(char)
\t\tif plr then
\t\t\tlocal money = ensureLeaderstats(plr)
\t\t\tmoney.Value += 1
\t\tend
\tend
end)

button.Touched:Connect(function(hit)
\tlocal char = hit:FindFirstAncestorOfClass("Model")
\tlocal plr = char and Players:GetPlayerFromCharacter(char)
\tif not plr then return end
\t-- prompt UI
\tbuyEvt:FireClient(plr, tonumber(button:GetAttribute("__Cost")) or 10)
end)

buyEvt.OnServerEvent:Connect(function(plr: Player)
\tlocal money = ensureLeaderstats(plr)
\tlocal cost = tonumber(button:GetAttribute("__Cost")) or 10
\tif money.Value < cost then return end
\tmoney.Value -= cost
\tlocal rate = tonumber(folder:GetAttribute(RATE_ATTR)) or 1.0
\trate += 0.35
\tfolder:SetAttribute(RATE_ATTR, rate)
\tbutton:SetAttribute("__Cost", math.floor(cost * 1.6))
end)

print("✅ TycoonManager initialized")
""",
        },
        {
            "path": "StarterPlayer/StarterPlayerScripts/TycoonUI.client.lua",
            "content": """-- TycoonUI.client.lua
-- Shows Money and upgrade cost prompt.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local player = Players.LocalPlayer
local events = ReplicatedStorage:WaitForChild("RemoteEvents")
local buyEvt = events:WaitForChild("TycoonBuyUpgrade")

local gui = Instance.new("ScreenGui")
gui.Name = "TycoonUI"
gui.ResetOnSpawn = false
gui.Parent = player:WaitForChild("PlayerGui")

local label = Instance.new("TextLabel")
label.Size = UDim2.new(0, 260, 0, 42)
label.Position = UDim2.new(0, 16, 0, 16)
label.BackgroundTransparency = 0.25
label.BackgroundColor3 = Color3.fromRGB(20, 20, 20)
label.TextColor3 = Color3.fromRGB(255, 255, 255)
label.Font = Enum.Font.GothamBold
label.TextSize = 20
label.Text = "Money: 0"
label.Parent = gui

local hint = Instance.new("TextLabel")
hint.Size = UDim2.new(0, 420, 0, 36)
hint.Position = UDim2.new(0, 16, 0, 62)
hint.BackgroundTransparency = 1
hint.TextColor3 = Color3.fromRGB(255, 240, 200)
hint.Font = Enum.Font.Gotham
hint.TextSize = 16
hint.Text = ""
hint.Parent = gui

local function update()
\tlocal ls = player:FindFirstChild("leaderstats")
\tlocal money = ls and ls:FindFirstChild("Money")
\tif money then label.Text = "Money: " .. tostring(money.Value) end
end

player.ChildAdded:Connect(update)
task.spawn(function()
\twhile true do
\t\tupdate()
\t\ttask.wait(0.3)
\tend
end)

buyEvt.OnClientEvent:Connect(function(cost)
\thint.Text = ("Press the yellow button to upgrade. Cost: %s (touch to buy)"):format(tostring(cost))
\ttask.delay(2.5, function() if hint then hint.Text = "" end end)
\t-- Send server purchase request
\tbuyEvt:FireServer()
end)
""",
        },
    ]

    return {
        "title": "Tycoon (Prototype)",
        "description": "A minimal tycoon: dropper + collector + upgrade button.",
        "files": files,
        "setup_instructions": [
            "Create a NEW Roblox place (Baseplate is fine).",
            "Create scripts at the listed paths and press Play.",
        ],
        "notes": [
            "Offline fallback pack (no AI key required).",
            "Use AI prompts to add more upgrades and expand the tycoon.",
        ],
    }
