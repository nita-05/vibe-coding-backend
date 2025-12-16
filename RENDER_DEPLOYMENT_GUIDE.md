# Render Deployment Guide - Vibe Coding Backend + SeasonalCollectorGame

## ✅ What's in this repo:
- `backend/` - FastAPI server (deploy this to Render)
- `SeasonalCollectorGame/` - Roblox game code (for reference, not deployed)

## 🚀 Deploy Backend to Render

### Step 1: Push to GitHub (if not done)
```bash
cd C:\Users\nitab\OneDrive\Desktop\vibe
git push -u origin main
```

If push fails due to size, try:
```bash
git push -u origin main --force
```

### Step 2: Create Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New** → **Web Service**
3. Connect your GitHub repo: `nita-05/vibe-coding-backend`
4. Configure:

**Settings:**
- **Name**: `vibe-coding-backend`
- **Root Directory**: `backend` ⚠️ **IMPORTANT: Set this!**
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 3: Add Environment Variables

In Render → Your Service → **Environment**:

| Key | Value |
|-----|-------|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` (or `gpt-4o`) |
| `CORS_ORIGINS` | `*` |
| `DATABASE_URL` | `sqlite:///./vibe_coding.db` (or Postgres URL) |

### Step 4: Deploy

Click **Save** → Render will deploy automatically.

### Step 5: Get Your Render URL

After deployment, you'll get a URL like:
```
https://vibe-coding-backend.onrender.com
```

**Copy this URL!** You'll need it for the Roblox game.

---

## 🎮 Connect Roblox Game to Render Backend

### In Roblox Studio:

1. **Enable HttpService**:
   - Game Settings → Security → Enable **HttpService**

2. **Set Backend URL**:
   - In `ReplicatedStorage`, find or create `VibeConfig` folder
   - Create `StringValue` named `BackendUrl`
   - Set value to your Render URL: `https://vibe-coding-backend.onrender.com` (no trailing slash)

3. **Test**:
   - Play the game
   - Walk to **Vibe AI** NPC
   - Press **E** to interact
   - Type a message → AI should respond!

---

## ✅ Verify Deployment

1. **Test Backend Health**:
   - Visit: `https://YOUR-RENDER-URL/health`
   - Should return: `{"status": "healthy", "service": "vibe-coding-api"}`

2. **Test AI Chat Endpoint**:
   - Use Postman or curl:
   ```bash
   curl -X POST https://YOUR-RENDER-URL/api/ai/chat \
     -H "Content-Type: application/json" \
     -d '{"messages": [{"role": "user", "content": "Hello!"}], "system_prompt": "You are a helpful assistant."}'
   ```

---

## 🐛 Troubleshooting

**Render Error: "Root directory 'backend' does not exist"**
- ✅ Make sure you set **Root Directory** = `backend` in Render settings
- ✅ Verify `backend/` folder exists in your GitHub repo

**Roblox can't connect to backend**
- ✅ Check HttpService is enabled
- ✅ Verify BackendUrl is set correctly (no trailing slash)
- ✅ Check Render service is running (not sleeping)

**Backend sleeping (free tier)**
- Free Render services sleep after 15 min inactivity
- First request after sleep takes ~30 seconds
- Upgrade to paid plan for always-on

---

## 📝 Files Structure

```
vibe-coding-backend/
├── backend/              ← Deploy this to Render
│   ├── app/
│   ├── requirements.txt
│   └── ...
└── SeasonalCollectorGame/  ← Roblox game (not deployed)
    ├── ServerScriptService/
    └── ...
```

---

**Ready to deploy!** 🚀

