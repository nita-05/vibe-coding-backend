-- EnvironmentManager.server.lua
-- Non-destructive environment overlays for events
-- Place in ServerScriptService

local Workspace = game:GetService("Workspace")
local Lighting = game:GetService("Lighting")
local TweenService = game:GetService("TweenService")
local RunService = game:GetService("RunService")

-- ============================================
-- EFFECTS FOLDER
-- ============================================
local effectsFolder = Instance.new("Folder")
effectsFolder.Name = "EventEffects"
effectsFolder.Parent = Workspace

-- ============================================
-- CLEAR EFFECTS
-- ============================================
local function clearEffects()
	for _, effect in ipairs(effectsFolder:GetChildren()) do
		effect:Destroy()
	end
end

-- ============================================
-- SNOW EVENT EFFECTS
-- ============================================
local function applySnowEffects()
	clearEffects()
	
	-- Snow particles
	local snowFolder = Instance.new("Folder")
	snowFolder.Name = "SnowParticles"
	snowFolder.Parent = effectsFolder
	
	for i = 1, 5 do
		local attachment = Instance.new("Attachment")
		attachment.Parent = Workspace.Terrain or Workspace:FindFirstChild("Baseplate")
		attachment.Position = Vector3.new(
			math.random(-200, 200),
			100 + math.random(0, 50),
			math.random(-200, 200)
		)
		
		local snow = Instance.new("ParticleEmitter")
		snow.Parent = attachment
		snow.Texture = "rbxasset://textures/particles/smoke.png"
		snow.Color = ColorSequence.new(Color3.fromRGB(255, 255, 255))
		snow.Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 0.3),
			NumberSequenceKeypoint.new(1, 1)
		})
		snow.Size = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 1),
			NumberSequenceKeypoint.new(1, 0)
		})
		snow.Lifetime = NumberRange.new(10, 15)
		snow.Rate = 50
		snow.Speed = NumberRange.new(1, 3)
		snow.SpreadAngle = Vector2.new(60, 60)
		snow.EmissionDirection = Enum.NormalId.Top
		snow.LightEmission = 0.2
	end
end

-- ============================================
-- HALLOWEEN EVENT EFFECTS
-- ============================================
local function applyHalloweenEffects()
	clearEffects()
	
	-- Spooky fog
	local fogFolder = Instance.new("Folder")
	fogFolder.Name = "HalloweenFog"
	fogFolder.Parent = effectsFolder
	
	for i = 1, 8 do
		local attachment = Instance.new("Attachment")
		attachment.Parent = Workspace.Terrain or Workspace:FindFirstChild("Baseplate")
		attachment.Position = Vector3.new(
			math.random(-200, 200),
			5 + math.random(0, 10),
			math.random(-200, 200)
		)
		
		local fog = Instance.new("ParticleEmitter")
		fog.Parent = attachment
		fog.Texture = "rbxasset://textures/particles/smoke.png"
		fog.Color = ColorSequence.new(Color3.fromRGB(20, 10, 15))
		fog.Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 0.5),
			NumberSequenceKeypoint.new(1, 1)
		})
		fog.Size = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 5),
			NumberSequenceKeypoint.new(1, 10)
		})
		fog.Lifetime = NumberRange.new(5, 10)
		fog.Rate = 30
		fog.Speed = NumberRange.new(0.5, 1.5)
		fog.SpreadAngle = Vector2.new(45, 45)
		fog.EmissionDirection = Enum.NormalId.Top
	end
	
	-- Orange glow lights
	for i = 1, 10 do
		local light = Instance.new("Part")
		light.Name = "HalloweenLight"
		light.Size = Vector3.new(1, 1, 1)
		light.Material = Enum.Material.Neon
		light.BrickColor = BrickColor.new("Bright orange")
		light.Transparency = 0.5
		light.Anchored = true
		light.CanCollide = false
		light.Position = Vector3.new(
			math.random(-150, 150),
			math.random(5, 15),
			math.random(-150, 150)
		)
		light.Parent = fogFolder
		
		local pointLight = Instance.new("PointLight")
		pointLight.Color = Color3.fromRGB(255, 140, 0)
		pointLight.Brightness = 2
		pointLight.Range = 15
		pointLight.Parent = light
		
		-- Pulsing
		TweenService:Create(
			pointLight,
			TweenInfo.new(2, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true),
			{Brightness = 4}
		):Play()
	end
end

-- ============================================
-- FESTIVAL EVENT EFFECTS
-- ============================================
local function applyFestivalEffects()
	clearEffects()
	
	-- Colorful lights
	local lightsFolder = Instance.new("Folder")
	lightsFolder.Name = "FestivalLights"
	lightsFolder.Parent = effectsFolder
	
	local colors = {
		Color3.fromRGB(255, 100, 100),
		Color3.fromRGB(100, 255, 100),
		Color3.fromRGB(100, 100, 255),
		Color3.fromRGB(255, 255, 100),
		Color3.fromRGB(255, 100, 255),
	}
	
	for i = 1, 15 do
		local light = Instance.new("Part")
		light.Name = "FestivalLight"
		light.Size = Vector3.new(1, 1, 1)
		light.Material = Enum.Material.Neon
		light.BrickColor = BrickColor.new(colors[math.random(1, #colors)])
		light.Transparency = 0.3
		light.Anchored = true
		light.CanCollide = false
		light.Position = Vector3.new(
			math.random(-150, 150),
			math.random(10, 30),
			math.random(-150, 150)
		)
		light.Parent = lightsFolder
		
		local pointLight = Instance.new("PointLight")
		pointLight.Color = light.BrickColor.Color
		pointLight.Brightness = 2
		pointLight.Range = 20
		pointLight.Parent = light
		
		-- Color cycling
		spawn(function()
			while light and light.Parent do
				wait(1)
				local newColor = colors[math.random(1, #colors)]
				TweenService:Create(
					light,
					TweenInfo.new(1, Enum.EasingStyle.Sine),
					{BrickColor = BrickColor.new(newColor)}
				):Play()
				TweenService:Create(
					pointLight,
					TweenInfo.new(1, Enum.EasingStyle.Sine),
					{Color = newColor}
				):Play()
			end
		end)
	end
	
	-- Firework particles (occasional)
	spawn(function()
		while lightsFolder and lightsFolder.Parent do
			wait(5)
			local firework = Instance.new("Part")
			firework.Size = Vector3.new(1, 1, 1)
			firework.Transparency = 1
			firework.Anchored = true
			firework.CanCollide = false
			firework.Position = Vector3.new(
				math.random(-100, 100),
				math.random(50, 80),
				math.random(-100, 100)
			)
			firework.Parent = lightsFolder
			
			local attachment = Instance.new("Attachment")
			attachment.Parent = firework
			
			local particles = Instance.new("ParticleEmitter")
			particles.Parent = attachment
			particles.Texture = "rbxasset://textures/particles/sparkles.png"
			particles.Color = ColorSequence.new(colors[math.random(1, #colors)])
			particles.Transparency = NumberSequence.new({
				NumberSequenceKeypoint.new(0, 0),
				NumberSequenceKeypoint.new(1, 1)
			})
			particles.Size = NumberSequence.new({
				NumberSequenceKeypoint.new(0, 2),
				NumberSequenceKeypoint.new(1, 0)
			})
			particles.Lifetime = NumberRange.new(1, 2)
			particles.Rate = 100
			particles.Speed = NumberRange.new(10, 20)
			particles.SpreadAngle = Vector2.new(45, 45)
			particles.Enabled = true
			
			wait(1)
			particles.Enabled = false
			wait(2)
			firework:Destroy()
		end
	end)
end

-- ============================================
-- SWITCH EVENT
-- ============================================
local function switchEvent(eventName)
	if eventName == "Snow" then
		applySnowEffects()
	elseif eventName == "Halloween" then
		applyHalloweenEffects()
	elseif eventName == "Festival" then
		applyFestivalEffects()
	end
	
	print("✅ Applied " .. eventName .. " environment effects")
end

-- ============================================
-- INITIALIZATION
-- ============================================
spawn(function()
	wait(1)
	local currentEvent = _G.EventManager and _G.EventManager.GetCurrentEvent() or "Snow"
	switchEvent(currentEvent)
end)

-- ============================================
-- EXPORT API
-- ============================================
_G.EnvironmentManager = {
	SwitchEvent = switchEvent,
}

print("✅ Environment Manager initialized")
print("   - Non-destructive overlays")
print("   - Event-specific effects")
