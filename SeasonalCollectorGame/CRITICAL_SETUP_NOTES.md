# ⚠️ CRITICAL SETUP NOTES

## 🔴 REQUIRED: ModuleScript Types in Roblox Studio

### **VehicleConfig MUST be a ModuleScript!**

**Location:** `ReplicatedStorage/Modules/VehicleConfig`

**Action Required:**
1. In Roblox Studio, navigate to `ReplicatedStorage/Modules/`
2. Find `VehicleConfig.lua`
3. **Right-click** → **Change to** → **ModuleScript**
4. The file should show as `VehicleConfig` (ModuleScript) not `VehicleConfig` (Script)

**Why this is critical:**
- VehicleService needs VehicleConfig to load vehicles
- ShowroomUI needs VehicleConfig to display vehicles
- Without it, you'll see "Infinite yield possible" errors
- Showroom will be empty and vehicles won't work

---

### **DataStoreManager MUST be a ModuleScript!**

**Location:** `ReplicatedStorage/Modules/DataStoreManager`

**Action Required:**
1. In Roblox Studio, navigate to `ReplicatedStorage/Modules/`
2. Find `DataStoreManager.lua`
3. **Right-click** → **Change to** → **ModuleScript**

**Why this is critical:**
- PlayerDataManager needs it to save/load player data
- LeaderboardManager needs it to save/load leaderboards
- Without it, data won't persist between sessions

---

## ✅ Verification Checklist

After setting up in Roblox Studio:

- [ ] VehicleConfig is a **ModuleScript** (not Script)
- [ ] DataStoreManager is a **ModuleScript** (not Script)
- [ ] All `.client.lua` files are **LocalScript** type
- [ ] All `.server.lua` files are **Script** type
- [ ] No "Infinite yield" errors in Output
- [ ] Showroom opens and shows vehicles
- [ ] Coins can be collected
- [ ] Vehicles can be purchased

---

## 🐛 Common Errors & Fixes

### Error: "Infinite yield possible on VehicleConfig"
**Fix:** VehicleConfig must be a ModuleScript, not a Script

### Error: "VehicleService not found"
**Fix:** VehicleService is waiting for VehicleConfig. Fix VehicleConfig first.

### Error: "DataStoreManager module not found"
**Fix:** DataStoreManager must be a ModuleScript in ReplicatedStorage/Modules

### Showroom is empty
**Fix:** VehicleConfig module not loading. Check it's a ModuleScript.

---

## 📋 File Type Reference

| File Location | Must Be | Type |
|--------------|---------|------|
| `ReplicatedStorage/Modules/VehicleConfig` | ModuleScript | ⚠️ CRITICAL |
| `ReplicatedStorage/Modules/DataStoreManager` | ModuleScript | ⚠️ CRITICAL |
| `ServerScriptService/*.server.lua` | Script | ✅ Default |
| `StarterPlayer/StarterPlayerScripts/*.client.lua` | LocalScript | ⚠️ Must change |

---

**The game will NOT work properly until VehicleConfig is set as ModuleScript!**
