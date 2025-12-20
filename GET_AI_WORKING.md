# 🤖 Get AI Working in Your Seasonal Collector Game

This guide will help you get the AI NPC working in your Roblox game step-by-step.

---

## ✅ Step 1: Deploy Backend to Render (If Not Done Yet)

### Option A: If you haven't deployed yet

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click "New +" → "Web Service"**
3. **Connect GitHub**: Select your repo `nita-05/vibe-coding-backend`
4. **Configure Settings**:
   - **Name**: `vibe-coding-backend` (or any name)
   - **Root Directory**: `backend` ⚠️ **CRITICAL!**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Add Environment Variables**:
   - `OPENAI_API_KEY` = Your OpenAI API key (starts with `sk-`)
   - `OPENAI_MODEL` = `gpt-4o-mini`
   - `CORS_ORIGINS` = `*`
   - `DATABASE_URL` = `sqlite:///./vibe_coding.db`
6. **Click "Create Web Service"** and wait ~2-5 minutes
7. **Copy your Render URL** (e.g., `https://vibe-coding-backend-xxxx.onrender.com`)

### Option B: If already deployed

Just get your Render URL from the Render dashboard!

---

## ✅ Step 2: Enable HttpService in Roblox Studio

1. **Open your game** in Roblox Studio
2. Click **"Game Settings"** (Home tab, or File → Game Settings)
3. Go to **"Security"** tab
4. Check these boxes:
   - ✅ **"Enable Studio Access to API Services"**
   - ✅ **"Allow HTTP Requests"** (HttpService)
5. Click **"Save"**

**Important:** Without this, your game cannot connect to the backend!

---

## ✅ Step 3: Set Backend URL in Roblox

1. In **Explorer** (left panel), find **ReplicatedStorage**
2. **Create VibeConfig folder** (if it doesn't exist):
   - Right-click **ReplicatedStorage**
   - Click **"Insert Object"** → **"Folder"**
   - Name it: `VibeConfig`
3. **Create BackendUrl StringValue**:
   - Right-click **VibeConfig** folder
   - Click **"Insert Object"** → **"StringValue"**
   - Name it: `BackendUrl`
   - In the **Properties** panel, set the **Value** to your Render URL
   - **Example**: `https://vibe-coding-backend-xxxx.onrender.com`
   - ⚠️ **NO trailing slash!** (Don't add `/` at the end)

**Visual Guide:**
```
ReplicatedStorage
  └── VibeConfig (Folder)
      └── BackendUrl (StringValue) = "https://your-render-url.onrender.com"
```

---

## ✅ Step 4: Verify VibeAIManager Script is Present

1. In **Explorer**, go to **ServerScriptService**
2. Make sure **VibeAIManager.server.lua** exists
3. If it's missing, the script should be at:
   `SeasonalCollectorGame/ServerScriptService/VibeAIManager.server.lua`

---

## ✅ Step 5: Test Your Backend First

Before testing in-game, verify your backend works:

1. **Open your Render URL** in a browser:
   ```
   https://YOUR-RENDER-URL.onrender.com/health
   ```
2. **You should see**:
   ```json
   {"status": "healthy", "service": "vibe-coding-api"}
   ```
3. **If you see this**, your backend is working! ✅

**Note:** On free tier, first request after sleep takes ~30 seconds (normal).

---

## ✅ Step 6: Test AI in Roblox Studio

1. **Press Play** in Roblox Studio (F5)
2. **Find the Vibe AI NPC** in your game
   - Look for an NPC named "Vibe AI" or similar
   - It should be somewhere in your game world
3. **Walk up to the NPC** and press **E** to interact
4. **Type a message** in the chat box, for example:
   - "How do I collect coins?"
   - "What is this game about?"
   - "How do I level up?"
5. **Press Enter** or click Send
6. **Wait for AI response** (may take 2-5 seconds)

---

## 🎉 Success Indicators

✅ **AI is working if:**
- You get a helpful response from the AI
- The response is related to your question
- No error messages appear

❌ **If you see errors:**

| Error Message | Solution |
|---------------|----------|
| "Server setup needed: enable HttpService..." | Go back to Step 2, enable HttpService |
| "AI is not configured yet..." | Go back to Step 3, set BackendUrl correctly |
| "AI request failed..." | Check your Render URL is correct, backend is running |
| "AI is having trouble responding..." | Check your OpenAI API key in Render environment variables |

---

## 🔍 Troubleshooting

### Backend not responding?
- Check Render dashboard - is service "Live"?
- Test `/health` endpoint in browser first
- Free tier services sleep after 15 min - wait ~30 sec for first request

### Can't find Vibe AI NPC?
- Check if NPCManager.server.lua creates the NPC
- Look in your game world for any NPC
- Check Output window for error messages

### HttpService errors?
- Make sure you enabled it in Game Settings → Security
- Restart Roblox Studio after enabling
- Check Output window for specific error messages

### Still not working?
1. **Check Output window** in Roblox Studio (View → Output)
2. Look for error messages from VibeAIManager
3. Verify BackendUrl value is correct (no trailing slash!)
4. Test backend `/health` endpoint in browser
5. Check Render logs for backend errors

---

## 📝 Quick Checklist

Before testing, make sure:
- [ ] Backend deployed to Render
- [ ] Render URL copied
- [ ] HttpService enabled in Game Settings
- [ ] BackendUrl set in ReplicatedStorage/VibeConfig
- [ ] BackendUrl has NO trailing slash
- [ ] VibeAIManager.server.lua is in ServerScriptService
- [ ] Backend `/health` endpoint works in browser
- [ ] OpenAI API key is set in Render environment variables

---

## 🚀 Next Steps

Once AI is working:
- Test different questions
- Customize the system prompt in VibeAIManager.server.lua (line 124)
- Adjust AI settings (temperature, max_tokens) if needed
- Consider upgrading Render plan for always-on service

**You're all set! Your Seasonal Collector Game now has AI! 🎮✨**
