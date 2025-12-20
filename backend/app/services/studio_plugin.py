from __future__ import annotations

from typing import Any, Dict


def generate_import_plugin_rbxmx(*, base_url: str, session_id: str, plugin_name: str = "VibeCodingImporter") -> str:
    """Generate a text .rbxmx plugin that imports a session pack into Studio.

    This is a best-effort approach: users still need HttpService enabled.
    """

    base_url = (base_url or "").rstrip("/")

    # Minimal RBXMX model containing a Plugin script.
    # Note: Roblox Studio supports importing .rbxmx; user can place it into Plugins folder.
    # The script uses HttpService to fetch the pack and writes scripts into correct services.

    lua = f'''-- Vibe Coding Importer Plugin
-- Auto-imports a generated pack into Roblox Studio.
-- Requirements: Game Settings -> Security -> Enable Studio Access to API Services + Http Requests.

local HttpService = game:GetService("HttpService")
local Selection = game:GetService("Selection")

local BASE_URL = {base_url!r}
local SESSION_ID = {session_id!r}

local function ensureFolder(parent, name)
    local f = parent:FindFirstChild(name)
    if not f then
        f = Instance.new("Folder")
        f.Name = name
        f.Parent = parent
    end
    return f
end

local function ensureScript(parent, name, isLocal)
    local s = parent:FindFirstChild(name)
    if not s then
        s = Instance.new(isLocal and "LocalScript" or "Script")
        s.Name = name
        s.Parent = parent
    end
    return s
end

local function splitPath(p)
    local parts = {{}}
    for seg in string.gmatch(p, "[^/]+") do
        table.insert(parts, seg)
    end
    return parts
end

local function importFile(path, content)
    path = string.gsub(path or "", "\\\\", "/")
    local parts = splitPath(path)
    if #parts < 2 then return end

    local rootName = parts[1]
    local service

    if rootName == "ServerScriptService" then
        service = game:GetService("ServerScriptService")
    elseif rootName == "ReplicatedStorage" then
        service = game:GetService("ReplicatedStorage")
    elseif rootName == "StarterPlayer" then
        service = game:GetService("StarterPlayer")
    else
        -- Unknown root; skip
        return
    end

    local parent = service

    -- Walk folders except final filename
    for i = 2, #parts - 1 do
        local seg = parts[i]
        parent = ensureFolder(parent, seg)
    end

    local filename = parts[#parts]
    local name = filename:gsub("%.lua$", "")

    local isLocal = false
    -- Heuristic: anything under StarterPlayerScripts is LocalScript
    for _, seg in ipairs(parts) do
        if seg == "StarterPlayerScripts" then
            isLocal = true
            break
        end
    end

    local s = ensureScript(parent, name, isLocal)
    s.Source = content or ""

    return s
end

local function fetchPack()
    local url = BASE_URL .. "/api/roblox/sessions/" .. SESSION_ID
    local ok, body = pcall(function()
        return HttpService:GetAsync(url)
    end)
    if not ok then
        error("VibeCodingImporter: failed to fetch pack. Check HttpService + URL.\n" .. tostring(body))
    end
    local decoded = HttpService:JSONDecode(body)
    return decoded
end

local toolbar = plugin:CreateToolbar("Vibe Coding")
local button = toolbar:CreateButton("Import", "Import latest Vibe Coding pack into this place", "")

button.Click:Connect(function()
    local pack = fetchPack()
    local files = pack.files or {{}}
    local created = {{}}
    for _, f in ipairs(files) do
        if type(f) == "table" then
            local s = importFile(f.path, f.content)
            if s then table.insert(created, s) end
        end
    end

    if #created > 0 then
        Selection:Set(created)
    end

    print("✅ Vibe Coding: imported " .. tostring(#created) .. " scripts")
end)
'''

    # RBXMX XML wrapper (Script inside a Model)
    # Roblox XML requires special escaping for script source.
    def xml_escape(s: str) -> str:
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    lua_xml = xml_escape(lua)

    return f'''<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="4">
  <Item class="Model">
    <Properties>
      <string name="Name">{xml_escape(plugin_name)}</string>
    </Properties>
    <Item class="Script">
      <Properties>
        <string name="Name">Importer</string>
        <string name="Source">{lua_xml}</string>
      </Properties>
    </Item>
  </Item>
</roblox>
'''
