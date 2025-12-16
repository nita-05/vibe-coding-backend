# How to Get Roblox Universe ID and Place ID

## Quick Answer

**You need 3 things for Roblox Open Cloud publishing:**
1. ✅ **ROBLOX_API_KEY** - You have this!
2. ❓ **ROBLOX_UNIVERSE_ID** - The game/universe ID
3. ❓ **ROBLOX_PLACE_ID** - The specific place ID within that universe

---

## Step-by-Step Guide

### Step 1: Get Your Universe ID

1. **Go to Roblox Creator Dashboard**: https://create.roblox.com
2. **Sign in** with your Roblox account
3. **Click "Games"** in the left sidebar
4. **Select your game** (or create a new one)
5. **Look at the URL** - it will be: `https://create.roblox.com/games/{UNIVERSE_ID}/overview`
   - The number in the URL is your **Universe ID**
   - Example: `https://create.roblox.com/games/123456789/overview` → Universe ID is `123456789`

**OR**

1. **Open Roblox Studio**
2. **File → Publish to Roblox As...** (or open existing game)
3. **Check the URL** in the browser after publishing
4. **Universe ID** is in the URL

---

### Step 2: Get Your Place ID

1. **In Roblox Creator Dashboard**: https://create.roblox.com
2. **Go to your game** (the one with your Universe ID)
3. **Click "Places"** tab (left sidebar)
4. **Click on a place** (or create a new one)
5. **Look at the URL** - it will be: `https://create.roblox.com/games/{UNIVERSE_ID}/places/{PLACE_ID}/overview`
   - The second number is your **Place ID**
   - Example: `https://create.roblox.com/games/123456789/places/987654321/overview` → Place ID is `987654321`

**OR**

1. **Open your game in Roblox Studio**
2. **File → Publish to Roblox** (or open existing place)
3. **Check the URL** after publishing
4. **Place ID** is the second number in the URL

---

### Step 3: Alternative Method (From Game Page)

1. **Go to your game's page** on Roblox.com
2. **Look at the URL**: `https://www.roblox.com/games/{PLACE_ID}/Game-Name`
   - The number is your **Place ID**
3. **To get Universe ID**:
   - Click "..." menu → "Copy Game Link"
   - Or check in Roblox Studio when you open the game

---

## Example

If your game URL is:
```
https://www.roblox.com/games/987654321/My-Awesome-Game
```

Then:
- **PLACE_ID** = `987654321`
- **UNIVERSE_ID** = (check in Creator Dashboard or Studio)

---

## Important Notes

⚠️ **You must own or have edit access to the place/universe**

⚠️ **The API key must have `Places:Write` permission** for that universe

⚠️ **The place must already exist** - you can't create new places via API (only update existing ones)

---

## Quick Test

After adding all 3 values to your `.env`:

```bash
# Restart backend
# Then check status:
curl http://localhost:8000/api/roblox/status
```

Should return:
```json
{
  "configured": true,
  "place_id": "987654321",
  "message": "Roblox API is configured"
}
```

---

## Still Need Help?

1. **Check Roblox Developer Forum**: https://devforum.roblox.com
2. **Roblox Open Cloud Docs**: https://create.roblox.com/docs/open-cloud
3. **Make sure your API key has correct permissions** in Roblox Developer Portal

