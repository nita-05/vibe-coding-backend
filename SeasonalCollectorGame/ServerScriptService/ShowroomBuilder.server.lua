-- ShowroomBuilder.server.lua
-- Creates a proper vehicle showroom building structure
-- Place in ServerScriptService

local Workspace = game:GetService("Workspace")
local TweenService = game:GetService("TweenService")

-- ============================================
-- SHOWROOM CONFIGURATION (ENHANCED - Realistic Design)
-- ============================================
local SHOWROOM_CONFIG = {
	Position = Vector3.new(0, 5, 0), -- Default position (can be adjusted)
	Size = {
		Width = 50, -- Wider for better display
		Length = 80, -- Longer for more vehicles
		Height = 25, -- Taller for grand appearance
	},
	PlatformCount = 8, -- More platforms for better vehicle display
}

-- ============================================
-- CREATE SHOWROOM BUILDING
-- ============================================
local function createShowroomBuilding()
	-- Main showroom folder
	local showroomFolder = Instance.new("Folder")
	showroomFolder.Name = "VehicleShowroom"
	showroomFolder.Parent = Workspace
	
	-- ============================================
	-- FLOOR
	-- ============================================
	local floor = Instance.new("Part")
	floor.Name = "Floor"
	floor.Size = Vector3.new(SHOWROOM_CONFIG.Size.Width, 1, SHOWROOM_CONFIG.Size.Length)
	floor.Position = SHOWROOM_CONFIG.Position + Vector3.new(0, 0.5, 0)
	floor.Anchored = true
	floor.Material = Enum.Material.Concrete
	floor.BrickColor = BrickColor.new("Light gray")
	floor.Parent = showroomFolder
	
	-- Floor pattern (realistic tile pattern)
	local floorPattern = Instance.new("Decal")
	floorPattern.Face = Enum.NormalId.Top
	floorPattern.Texture = "rbxasset://textures/studs.png"
	floorPattern.Transparency = 0.7
	floorPattern.Parent = floor
	
	-- Add floor shine
	floor.Material = Enum.Material.SmoothPlastic
	floor.Reflectance = 0.1
	
	-- ============================================
	-- WALLS
	-- ============================================
	local wallThickness = 1
	
	-- Front wall (with entrance)
	local frontWall = Instance.new("Part")
	frontWall.Name = "FrontWall"
	frontWall.Size = Vector3.new(SHOWROOM_CONFIG.Size.Width, SHOWROOM_CONFIG.Size.Height, wallThickness)
	frontWall.Position = SHOWROOM_CONFIG.Position + Vector3.new(0, SHOWROOM_CONFIG.Size.Height / 2, -SHOWROOM_CONFIG.Size.Length / 2)
	frontWall.Anchored = true
	frontWall.Material = Enum.Material.Concrete
	frontWall.BrickColor = BrickColor.new("Dark stone grey")
	frontWall.Parent = showroomFolder
	
	-- Entrance opening (remove middle section)
	local entranceWidth = 8
	local leftWall = frontWall:Clone()
	leftWall.Name = "LeftFrontWall"
	leftWall.Size = Vector3.new((SHOWROOM_CONFIG.Size.Width - entranceWidth) / 2, SHOWROOM_CONFIG.Size.Height, wallThickness)
	leftWall.Position = frontWall.Position - Vector3.new(entranceWidth / 2 + (SHOWROOM_CONFIG.Size.Width - entranceWidth) / 4, 0, 0)
	leftWall.Parent = showroomFolder
	
	local rightWall = frontWall:Clone()
	rightWall.Name = "RightFrontWall"
	rightWall.Size = Vector3.new((SHOWROOM_CONFIG.Size.Width - entranceWidth) / 2, SHOWROOM_CONFIG.Size.Height, wallThickness)
	rightWall.Position = frontWall.Position + Vector3.new(entranceWidth / 2 + (SHOWROOM_CONFIG.Size.Width - entranceWidth) / 4, 0, 0)
	rightWall.Parent = showroomFolder
	
	frontWall:Destroy()
	
	-- Entrance header
	local entranceHeader = Instance.new("Part")
	entranceHeader.Name = "EntranceHeader"
	entranceHeader.Size = Vector3.new(entranceWidth, 2, wallThickness)
	entranceHeader.Position = SHOWROOM_CONFIG.Position + Vector3.new(0, SHOWROOM_CONFIG.Size.Height - 1, -SHOWROOM_CONFIG.Size.Length / 2)
	entranceHeader.Anchored = true
	entranceHeader.Material = Enum.Material.Concrete
	entranceHeader.BrickColor = BrickColor.new("Dark stone grey")
	entranceHeader.Parent = showroomFolder
	
	-- Back wall
	local backWall = Instance.new("Part")
	backWall.Name = "BackWall"
	backWall.Size = Vector3.new(SHOWROOM_CONFIG.Size.Width, SHOWROOM_CONFIG.Size.Height, wallThickness)
	backWall.Position = SHOWROOM_CONFIG.Position + Vector3.new(0, SHOWROOM_CONFIG.Size.Height / 2, SHOWROOM_CONFIG.Size.Length / 2)
	backWall.Anchored = true
	backWall.Material = Enum.Material.Concrete
	backWall.BrickColor = BrickColor.new("Dark stone grey")
	backWall.Parent = showroomFolder
	
	-- Left wall
	local leftSideWall = Instance.new("Part")
	leftSideWall.Name = "LeftWall"
	leftSideWall.Size = Vector3.new(wallThickness, SHOWROOM_CONFIG.Size.Height, SHOWROOM_CONFIG.Size.Length)
	leftSideWall.Position = SHOWROOM_CONFIG.Position + Vector3.new(-SHOWROOM_CONFIG.Size.Width / 2, SHOWROOM_CONFIG.Size.Height / 2, 0)
	leftSideWall.Anchored = true
	leftSideWall.Material = Enum.Material.Concrete
	leftSideWall.BrickColor = BrickColor.new("Dark stone grey")
	leftSideWall.Parent = showroomFolder
	
	-- Right wall
	local rightSideWall = Instance.new("Part")
	rightSideWall.Name = "RightWall"
	rightSideWall.Size = Vector3.new(wallThickness, SHOWROOM_CONFIG.Size.Height, SHOWROOM_CONFIG.Size.Length)
	rightSideWall.Position = SHOWROOM_CONFIG.Position + Vector3.new(SHOWROOM_CONFIG.Size.Width / 2, SHOWROOM_CONFIG.Size.Height / 2, 0)
	rightSideWall.Anchored = true
	rightSideWall.Material = Enum.Material.Concrete
	rightSideWall.BrickColor = BrickColor.new("Dark stone grey")
	rightSideWall.Parent = showroomFolder
	
	-- ============================================
	-- ROOF (Enhanced - Realistic Design)
	-- ============================================
	local roof = Instance.new("Part")
	roof.Name = "Roof"
	roof.Size = Vector3.new(SHOWROOM_CONFIG.Size.Width + 2, 2, SHOWROOM_CONFIG.Size.Length + 2)
	roof.Position = SHOWROOM_CONFIG.Position + Vector3.new(0, SHOWROOM_CONFIG.Size.Height + 1, 0)
	roof.Anchored = true
	roof.Material = Enum.Material.Metal
	roof.BrickColor = BrickColor.new("Dark stone grey")
	roof.Parent = showroomFolder
	
	-- Roof overhang
	local overhang = Instance.new("Part")
	overhang.Name = "Overhang"
	overhang.Size = Vector3.new(SHOWROOM_CONFIG.Size.Width + 4, 0.5, 2)
	overhang.Position = SHOWROOM_CONFIG.Position + Vector3.new(0, SHOWROOM_CONFIG.Size.Height + 0.5, -SHOWROOM_CONFIG.Size.Length / 2 - 1)
	overhang.Anchored = true
	overhang.Material = Enum.Material.Metal
	overhang.BrickColor = BrickColor.new("Dark stone grey")
	overhang.Parent = showroomFolder
	
	-- ============================================
	-- VEHICLE DISPLAY PLATFORMS
	-- ============================================
	local platformsFolder = Instance.new("Folder")
	platformsFolder.Name = "VehiclePlatforms"
	platformsFolder.Parent = showroomFolder
	
	local platformSpacing = SHOWROOM_CONFIG.Size.Length / (SHOWROOM_CONFIG.PlatformCount + 1)
	local platformWidth = (SHOWROOM_CONFIG.Size.Width - 10) / 2 -- Two rows
	
	for i = 1, SHOWROOM_CONFIG.PlatformCount do
		local row = math.ceil(i / 2)
		local side = (i % 2 == 1) and -1 or 1
		
		local platform = Instance.new("Part")
		platform.Name = "Platform" .. i
		platform.Size = Vector3.new(platformWidth - 2, 0.5, 8) -- Larger for better vehicle display
		platform.Position = SHOWROOM_CONFIG.Position + Vector3.new(
			side * (platformWidth / 2 + 2),
			1.5,
			-SHOWROOM_CONFIG.Size.Length / 2 + (row * platformSpacing)
		)
		platform.Anchored = true
		platform.Material = Enum.Material.SmoothPlastic
		platform.BrickColor = BrickColor.new("Light gray") -- More realistic color
		platform.Reflectance = 0.2 -- Shiny floor
		platform.Parent = platformsFolder
		
		-- Platform riser (elevated display - creates pedestal effect)
		local riser = Instance.new("Part")
		riser.Name = "Riser"
		riser.Size = Vector3.new(platformWidth - 2, 0.5, 8)
		riser.Position = platform.Position + Vector3.new(0, 0.25, 0)
		riser.Anchored = true
		riser.Material = Enum.Material.Metal
		riser.BrickColor = BrickColor.new("Dark stone grey")
		riser.Parent = platform
		
		-- Display area on riser (where vehicle will sit)
		local displayArea = Instance.new("Part")
		displayArea.Name = "DisplayArea"
		displayArea.Size = Vector3.new(platformWidth - 4, 0.1, 7)
		displayArea.Position = riser.Position + Vector3.new(0, 0.3, 0)
		displayArea.Anchored = true
		displayArea.Material = Enum.Material.SmoothPlastic
		displayArea.BrickColor = BrickColor.new("Light gray")
		displayArea.Reflectance = 0.3
		displayArea.CanCollide = false
		displayArea.Parent = platform
		
		-- Platform border (subtle, realistic)
		local border = Instance.new("Part")
		border.Name = "Border"
		border.Size = Vector3.new(platformWidth, 0.1, 8.2)
		border.Position = platform.Position + Vector3.new(0, 0.25, 0)
		border.Anchored = true
		border.Material = Enum.Material.Metal
		border.BrickColor = BrickColor.new("Dark stone grey")
		border.Transparency = 0
		border.Parent = platform
		
		-- Platform label (removed - vehicles will be displayed here instead)
		-- Vehicles will be spawned on platforms by VehicleService
	end
	
	-- ============================================
	-- SHOWROOM SIGN
	-- ============================================
	local sign = Instance.new("Part")
	sign.Name = "ShowroomSign"
	sign.Size = Vector3.new(12, 4, 1)
	sign.Position = SHOWROOM_CONFIG.Position + Vector3.new(0, SHOWROOM_CONFIG.Size.Height - 2, -SHOWROOM_CONFIG.Size.Length / 2 - 0.5)
	sign.Anchored = true
	sign.Material = Enum.Material.Neon
	sign.BrickColor = BrickColor.new("Bright blue")
	sign.Parent = showroomFolder
	
	-- Sign text
	local signGui = Instance.new("SurfaceGui")
	signGui.Face = Enum.NormalId.Front
	signGui.Parent = sign
	
	local signText = Instance.new("TextLabel")
	signText.Size = UDim2.new(1, 0, 1, 0)
	signText.BackgroundColor3 = Color3.fromRGB(0, 50, 150)
	signText.Text = "🚗 VEHICLE SHOWROOM 🚗"
	signText.TextColor3 = Color3.fromRGB(255, 255, 255)
	signText.TextSize = 24
	signText.Font = Enum.Font.GothamBold
	signText.TextStrokeTransparency = 0
	signText.TextStrokeColor3 = Color3.fromRGB(0, 0, 0)
	signText.Parent = signGui
	
	-- ============================================
	-- LIGHTING
	-- ============================================
	for i = 1, 4 do
		local light = Instance.new("PointLight")
		light.Color = Color3.fromRGB(255, 255, 200)
		light.Brightness = 2
		light.Range = 30
		light.Parent = roof
		
		-- Position lights
		local lightPart = Instance.new("Part")
		lightPart.Name = "Light" .. i
		lightPart.Size = Vector3.new(1, 1, 1)
		lightPart.Transparency = 1
		lightPart.Anchored = true
		lightPart.CanCollide = false
		lightPart.Parent = showroomFolder
		
		local xPos = (i % 2 == 1) and -SHOWROOM_CONFIG.Size.Width / 3 or SHOWROOM_CONFIG.Size.Width / 3
		local zPos = (i <= 2) and -SHOWROOM_CONFIG.Size.Length / 3 or SHOWROOM_CONFIG.Size.Length / 3
		lightPart.Position = SHOWROOM_CONFIG.Position + Vector3.new(xPos, SHOWROOM_CONFIG.Size.Height - 1, zPos)
		light.Parent = lightPart
	end
	
	-- ============================================
	-- INTERACTION POINT
	-- ============================================
	local interactionPoint = Instance.new("Part")
	interactionPoint.Name = "InteractionPoint"
	interactionPoint.Size = Vector3.new(6, 1, 6)
	interactionPoint.Position = SHOWROOM_CONFIG.Position + Vector3.new(0, 1, -SHOWROOM_CONFIG.Size.Length / 2 + 3)
	interactionPoint.Anchored = true
	interactionPoint.Transparency = 1
	interactionPoint.CanCollide = false
	interactionPoint.Parent = showroomFolder
	
	-- Interaction marker
	local marker = Instance.new("Part")
	marker.Name = "Marker"
	marker.Size = Vector3.new(4, 0.2, 4)
	marker.Position = interactionPoint.Position + Vector3.new(0, 0.1, 0)
	marker.Anchored = true
	marker.Material = Enum.Material.Neon
	marker.BrickColor = BrickColor.new("Bright yellow")
	marker.Transparency = 0.5
	marker.CanCollide = false
	marker.Parent = interactionPoint
	
	-- Pulsing animation
	local pulseTween = TweenService:Create(
		marker,
		TweenInfo.new(1, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true),
		{Transparency = 0.8}
	)
	pulseTween:Play()
	
	-- Billboard above interaction point
	local billboard = Instance.new("BillboardGui")
	billboard.Name = "ShowroomBillboard"
	billboard.Size = UDim2.new(0, 300, 0, 100)
	billboard.StudsOffset = Vector3.new(0, 5, 0)
	billboard.Parent = interactionPoint
	
	local billboardFrame = Instance.new("Frame")
	billboardFrame.Size = UDim2.new(1, 0, 1, 0)
	billboardFrame.BackgroundColor3 = Color3.fromRGB(0, 50, 150)
	billboardFrame.BackgroundTransparency = 0.2
	billboardFrame.BorderSizePixel = 0
	billboardFrame.Parent = billboard
	
	local billboardCorner = Instance.new("UICorner")
	billboardCorner.CornerRadius = UDim.new(0, 10)
	billboardCorner.Parent = billboardFrame
	
	local billboardText = Instance.new("TextLabel")
	billboardText.Size = UDim2.new(1, -20, 1, -20)
	billboardText.Position = UDim2.new(0, 10, 0, 10)
	billboardText.BackgroundTransparency = 1
	billboardText.Text = "🚗 VEHICLE SHOWROOM"
	billboardText.TextColor3 = Color3.fromRGB(255, 255, 255)
	billboardText.TextSize = 18
	billboardText.Font = Enum.Font.GothamBold
	billboardText.TextStrokeTransparency = 0
	billboardText.TextStrokeColor3 = Color3.fromRGB(0, 0, 0)
	billboardText.TextWrapped = true
	billboardText.Parent = billboardFrame
	-- Note: ProximityPrompt will show "Press E" automatically, no need to duplicate in billboard
	
	return interactionPoint
end

-- ============================================
-- INITIALIZATION
-- ============================================
spawn(function()
	wait(1) -- Wait for workspace to load
	local interactionPoint = createShowroomBuilding()
	print("✅ Showroom building created")
	print("   - Building structure: " .. SHOWROOM_CONFIG.Size.Width .. "x" .. SHOWROOM_CONFIG.Size.Length .. "x" .. SHOWROOM_CONFIG.Size.Height)
	print("   - Vehicle platforms: " .. SHOWROOM_CONFIG.PlatformCount)
	print("   - Interaction point ready")
end)

print("✅ Showroom Builder initialized")
