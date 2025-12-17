# 🔧 Quick Fix Guide - Module Loading Errors

## ⚠️ Current Errors

1. **Infinite yield possible on VehicleConfig** - VehicleConfig module not loading
2. **VehicleService not found** - Because VehicleConfig failed to load
3. **DataStoreManager errors** - Module not found (less critical, uses fallback)

## ✅ Fix Steps (5 minutes)

### Step 1: Fix VehicleConfig (CRITICAL)

1. Open Roblox Studio
2. Go to **ReplicatedStorage** → **Modules**
3. Find **VehicleConfig.lua**
4. **Right-click** on it
5. Select **"Change to"** → **"ModuleScript"**
6. The icon should change to a module icon (blue box with M)

### Step 2: Fix DataStoreManager (Optional but Recommended)

1. In **ReplicatedStorage** → **Modules**
2. Find **DataStoreManager.lua**
3. **Right-click** → **"Change to"** → **"ModuleScript"**

### Step 3: Verify Script Types

**Server Scripts** (should be Script):
- ✅ All files in `ServerScriptService/*.server.lua` → **Script** type

**Client Scripts** (should be LocalScript):
- ✅ All files in `StarterPlayer/StarterPlayerScripts/*.client.lua` → **LocalScript** type

**Modules** (should be ModuleScript):
- ✅ `ReplicatedStorage/Modules/VehicleConfig` → **ModuleScript**
- ✅ `ReplicatedStorage/Modules/DataStoreManager` → **ModuleScript**

### Step 4: Test

1. Click **Play** in Roblox Studio
2. Check **Output** window:
   - Should see: `✅ VehicleConfig loaded successfully`
   - Should see: `✅ Vehicle Service initialized`
   - Should NOT see: `Infinite yield possible`

## 🎯 Expected Result

After fixing:
- ✅ No "Infinite yield" errors
- ✅ VehicleService loads successfully
- ✅ Showroom opens and shows vehicles
- ✅ Coins can be collected
- ✅ Vehicles can be purchased

## 📝 Why This Happens

Roblox Studio doesn't automatically set file types. When you paste `.lua` files:
- They default to **Script** type
- But modules MUST be **ModuleScript** type
- Client scripts MUST be **LocalScript** type

The `.lua` extension is just for organization - the actual **type** matters in Studio!

---

**This is the #1 most common setup issue. Fix VehicleConfig first!**
