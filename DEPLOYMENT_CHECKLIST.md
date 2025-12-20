# ✅ Render Deployment Checklist

Use this checklist to ensure everything is ready for deployment!

## Pre-Deployment Checklist

### 1. Code Structure ✅
- [x] `backend/app/main.py` exists
- [x] `backend/app/api/routes.py` exists  
- [x] `backend/requirements.txt` exists
- [x] `backend/app/__init__.py` exists
- [x] All Python modules have proper structure

### 2. Git Repository
- [ ] Repository is on GitHub
- [ ] `venv/` folder is NOT committed (check `.gitignore`)
- [ ] `__pycache__/` folders are NOT committed
- [ ] `.env` file is NOT committed (contains secrets!)

### 3. Environment Variables Ready
- [ ] OpenAI API key obtained from https://platform.openai.com/api-keys
- [ ] API key starts with `sk-`
- [ ] You have credits in your OpenAI account

### 4. Render Account
- [ ] Account created at https://render.com
- [ ] GitHub account connected to Render

---

## Deployment Steps

### Step 1: Push to GitHub
```powershell
cd c:\Users\nitab\OneDrive\Desktop\vibe
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### Step 2: Create Render Service
- [ ] Go to Render Dashboard
- [ ] Click "New +" → "Web Service"
- [ ] Connect GitHub repository
- [ ] Set Root Directory: `backend`
- [ ] Set Build Command: `pip install -r requirements.txt`
- [ ] Set Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 3: Add Environment Variables
- [ ] `OPENAI_API_KEY` = your OpenAI key
- [ ] `OPENAI_MODEL` = `gpt-4o-mini`
- [ ] `CORS_ORIGINS` = `*`
- [ ] `DATABASE_URL` = `sqlite:///./vibe_coding.db`

### Step 4: Deploy
- [ ] Click "Create Web Service"
- [ ] Wait for build to complete (~2-5 minutes)
- [ ] Copy the Render URL (e.g., `https://vibe-coding-backend-xxxx.onrender.com`)

### Step 5: Test Backend
- [ ] Visit `https://YOUR-URL/health` in browser
- [ ] Should see: `{"status": "healthy", "service": "vibe-coding-api"}`

---

## Roblox Configuration

### Step 6: Enable HttpService
- [ ] Open Roblox Studio
- [ ] Game Settings → Security
- [ ] Enable "Studio Access to API Services"
- [ ] Enable "Allow HTTP Requests"

### Step 7: Set Backend URL
- [ ] In Explorer: ReplicatedStorage → VibeConfig → BackendUrl
- [ ] Set value to your Render URL (no trailing slash!)
- [ ] Example: `https://vibe-coding-backend-xxxx.onrender.com`

### Step 8: Test in Game
- [ ] Press Play in Roblox Studio
- [ ] Walk to Vibe AI NPC
- [ ] Press E to interact
- [ ] Type a message
- [ ] AI should respond!

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Build fails | Check Root Directory is `backend` |
| Can't connect from Roblox | Verify HttpService is enabled |
| AI not responding | Check OpenAI API key and credits |
| Service sleeping | Normal on free tier, wait ~30 sec for first request |
| 404 errors | Verify Start Command uses `$PORT` variable |

---

## Your Render URL

Once deployed, your URL will be:
```
https://YOUR-SERVICE-NAME.onrender.com
```

**Save this URL!** You'll need it for Roblox configuration.

---

## Need Help?

1. Check Render build logs for errors
2. Test `/health` endpoint first
3. Verify all environment variables are set
4. Check Roblox Output window for error messages

**Good luck with your deployment! 🚀**
