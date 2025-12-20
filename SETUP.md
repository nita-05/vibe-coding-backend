# Vibe Coding Platform – Setup Guide

This guide walks through setting up the backend, frontend, and Roblox Open Cloud integration for the Vibe Coding prototype.

---

## 1. Prerequisites

- **Python 3.11**
- **Node.js 18+** (includes npm)
- **Git**
- **OpenAI API key**
- *(Optional but recommended)* Roblox Open Cloud key with `Places:Write` permission for the target universe/place

---

## 2. Clone and install

```bash
git clone https://github.com/<your-org>/vibe.git
cd vibe
```

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```bash
cd ../frontend
npm install
```

---

## 3. Environment variables

### Backend (`backend/.env`)

Use `env.template` as a reference:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

ROBLOX_API_KEY=your_open_cloud_key
ROBLOX_UNIVERSE_ID=your_universe_id
ROBLOX_PLACE_ID=your_place_id

DATABASE_URL=sqlite:///./vibe_coding.db
CORS_ORIGINS=http://localhost:5173
PORT=8000
```

> Roblox values are optional but required for one-click publishing.

### Frontend (`frontend/.env`)

```
VITE_API_URL=http://localhost:8000
```

---

## 4. Running locally

### Backend

```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

Server runs on http://localhost:8000

### Frontend

```bash
cd frontend
npm run dev
```

App runs on http://localhost:5173

---

## 5. CI workflow

The repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that:

1. Installs backend dependencies and compiles Python sources
2. Installs frontend dependencies and runs `npm run build`
3. Uploads the built `frontend/dist` as an artifact

No additional configuration is required once the repo is pushed to GitHub.

---

## 6. Roblox Open Cloud checklist

1. Enable **Open Cloud** for your Roblox game
2. Create an API key with `Places:Write` permission scoped to your universe/place
3. Copy the Universe ID and Place ID from the Roblox Creator Dashboard
4. Add them to `backend/.env`
5. Restart the backend to apply the new credentials

---

## 7. Next steps

- Follow `TESTING_GUIDE.md` to validate the AI pipeline
- Review `HOW_TO_USE_IN_ROBLOX_STUDIO.md` for manual testing inside Roblox Studio
- Use `/api/roblox/publish` (available from the UI) to push updates directly to an existing Roblox place

You're ready to build, test, and publish Roblox games with natural-language prompts!

