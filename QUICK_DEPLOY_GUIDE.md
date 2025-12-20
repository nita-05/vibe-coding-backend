# 🚀 Quick Render Deployment Guide - Seasonal Collector Game AI

This guide will help you deploy your backend to Render so your Roblox game can use AI features!

---

## ✅ Prerequisites Checklist

Before starting, make sure you have:
- [ ] A GitHub account
- [ ] A Render account (sign up at https://render.com - it's free!)
- [ ] An OpenAI API key (get it from https://platform.openai.com/api-keys)
- [ ] Your code pushed to GitHub (we'll help with this)

---

## Step 1: Clean Up Git Repository

Your repository has some files that shouldn't be committed (like `venv/` and `__pycache__/`). Let's fix this:

```powershell
cd c:\Users\nitab\OneDrive\Desktop\vibe
git rm -r --cached backend/venv/
git rm -r --cached backend/**/__pycache__/
git commit -m "Remove venv and cache files from git"
```

---

## Step 2: Push to GitHub

If you haven't already, create a GitHub repository and push your code:

```powershell
# If you haven't initialized git yet:
git init
git add .
git commit -m "Initial commit - Seasonal Collector Game with AI backend"

# Add your GitHub remote (replace YOUR_USERNAME with your GitHub username):
git remote add origin https://github.com/YOUR_USERNAME/vibe.git

# Push to GitHub:
git branch -M main
git push -u origin main
```

**Note:** If you get an error about large files, you may need to use Git LFS or remove large files first.

---

## Step 3: Deploy to Render

### 3.1 Create a New Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** button (top right)
3. Select **"Web Service"**

### 3.2 Connect Your GitHub Repository

1. Click **"Connect account"** if you haven't connected GitHub yet
2. Authorize Render to access your repositories
3. Select your repository: `YOUR_USERNAME/vibe` (or whatever you named it)

### 3.3 Configure the Service

Fill in these settings:

| Setting | Value |
|---------|-------|
| **Name** | `vibe-coding-backend` (or any name you like) |
| **Region** | Choose closest to you (e.g., `Oregon (US West)`) |
| **Branch** | `main` (or `master` if that's your branch) |
| **Root Directory** | `backend` ⚠️ **THIS IS CRITICAL!** |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

**Important:** Make sure **Root Directory** is set to `backend` (not the root of the repo!)

### 3.4 Add Environment Variables

Scroll down to **"Environment Variables"** section and click **"Add Environment Variable"** for each:

| Key | Value | Notes |
|-----|-------|-------|
| `OPENAI_API_KEY` | `sk-your-actual-key-here` | Your OpenAI API key (starts with `sk-`) |
| `OPENAI_MODEL` | `gpt-4o-mini` | Or `gpt-4o` for better quality (more expensive) |
| `CORS_ORIGINS` | `*` | Allows Roblox to connect |
| `DATABASE_URL` | `sqlite:///./vibe_coding.db` | Default SQLite (works fine for free tier) |
| `PORT` | (leave empty) | Render sets this automatically |

**Click "Create Web Service"** when done!

---

## Step 4: Wait for Deployment

Render will:
1. Clone your repository
2. Install dependencies from `requirements.txt`
3. Start your FastAPI server

This takes about 2-5 minutes. You'll see build logs in real-time.

---

## Step 5: Get Your Render URL

Once deployment is complete, you'll see:
- **Status:** Live ✅
- **URL:** `https://vibe-coding-backend-xxxx.onrender.com` (or similar)

**Copy this URL!** You'll need it for Roblox.

---

## Step 6: Test Your Backend

Open your browser and visit:
```
https://YOUR-RENDER-URL/health
```

You should see:
```json
{"status": "healthy", "service": "vibe-coding-api"}
```

If you see this, your backend is working! 🎉

---

## Step 7: Connect Roblox Game to Render

### 7.1 Enable HttpService in Roblox Studio

1. Open your game in **Roblox Studio**
2. Click **Game Settings** (Home tab)
3. Go to **Security** tab
4. Check **"Enable Studio Access to API Services"**
5. Check **"Allow HTTP Requests"** (HttpService)
6. Click **"Save"**

### 7.2 Set Backend URL in Roblox

1. In **Explorer** (left panel), find **ReplicatedStorage**
2. Look for **VibeConfig** folder (if it doesn't exist, create it):
   - Right-click **ReplicatedStorage** → **Insert Object** → **Folder**
   - Name it `VibeConfig`
3. Inside **VibeConfig**, create a **StringValue**:
   - Right-click **VibeConfig** → **Insert Object** → **StringValue**
   - Name it `BackendUrl`
   - Set the **Value** to your Render URL: `https://YOUR-RENDER-URL.onrender.com`
   - **Important:** No trailing slash! (e.g., `https://vibe-coding-backend-xxxx.onrender.com`)

### 7.3 Test in Game

1. Press **Play** in Roblox Studio
2. Walk to the **Vibe AI** NPC in your game
3. Press **E** to interact
4. Type a message like: "How do I collect coins?"
5. Press Enter

If everything works, you'll get an AI response! 🤖

---

## 🐛 Troubleshooting

### Backend won't deploy
- ✅ Check that **Root Directory** is set to `backend`
- ✅ Make sure `requirements.txt` exists in `backend/` folder
- ✅ Check build logs in Render dashboard for errors

### Roblox can't connect
- ✅ Verify HttpService is enabled in Game Settings
- ✅ Check that `BackendUrl` is set correctly (no trailing slash)
- ✅ Make sure Render service is running (not sleeping)
- ✅ Test the `/health` endpoint in browser first

### Backend is "sleeping"
- Free Render services sleep after 15 minutes of inactivity
- First request after sleep takes ~30 seconds to wake up
- This is normal on the free tier
- Upgrade to paid plan ($7/month) for always-on service

### AI not responding
- ✅ Check your OpenAI API key is correct
- ✅ Verify you have credits in your OpenAI account
- ✅ Check Render logs for error messages

---

## 📝 Quick Reference

**Render URL Format:**
```
https://YOUR-SERVICE-NAME.onrender.com
```

**Health Check:**
```
GET https://YOUR-SERVICE-NAME.onrender.com/health
```

**AI Chat Endpoint (used by Roblox):**
```
POST https://YOUR-SERVICE-NAME.onrender.com/api/ai/chat
```

**Roblox Config Location:**
```
ReplicatedStorage → VibeConfig → BackendUrl (StringValue)
```

---

## ✅ Success Checklist

- [ ] Code pushed to GitHub
- [ ] Render service created and deployed
- [ ] Health endpoint returns `{"status": "healthy"}`
- [ ] HttpService enabled in Roblox Studio
- [ ] BackendUrl set in ReplicatedStorage
- [ ] AI NPC responds to player messages in-game

---

**You're all set!** Your Seasonal Collector Game now has AI features powered by Render! 🎮✨
