# Vibe Coding Platform

**Describe a Roblox game idea and instantly get a working Lua script ready for Roblox Studio or Open Cloud publishing.**

## Project Overview

Vibe Coding is a natural-language interface for Roblox creators. The AI interprets prompts, outputs complete Lua scripts (including visuals, mechanics, and instructions), and guides you through testing inside Roblox Studio or publishing straight to Roblox via Open Cloud.

## Tech Stack

### Backend
- **FastAPI** – Python API server
- **OpenAI API** – GPT-4/GPT-4o script generation
- **SQLite** – Local persistence (upgradable to Postgres)
- **Roblox Open Cloud** – Optional place publishing

### Frontend
- **React 18** - UI library
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **TypeScript** - Type safety

### AI Integration
- **OpenAI GPT-4/GPT-3.5** - Text-to-Lua generation
- **Prompt Engineering** - Roblox-specific optimization

## Features

✅ Natural-language to Lua generation (Obby, Tycoon, Simulator, Racing, Story, FPS)  
✅ Voice-enabled interactive guide for first-time testers  
✅ Monaco code editor, draft saving, blueprint templates  
✅ Accurate visual output (colors, sizes, glowing effects match prompts)  
✅ Roblox Studio testing instructions + tooling  
✅ Optional Roblox Open Cloud publishing (existing universe/place)  
✅ GitHub Actions CI (backend compile + frontend build)

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API key

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
# Edit .env if needed
npm run dev
```

## Environment Variables

### Backend (`backend/.env`)
| Key | Description |
|-----|-------------|
| `OPENAI_API_KEY` | Required OpenAI key |
| `OPENAI_MODEL` | GPT model (default `gpt-4o`) |
| `ROBLOX_API_KEY` | Roblox Open Cloud key *(optional)* |
| `ROBLOX_UNIVERSE_ID` | Universe ID for publishing *(optional)* |
| `ROBLOX_PLACE_ID` | Place ID to overwrite *(optional)* |
| `DATABASE_URL` | Default `sqlite:///./vibe_coding.db` |
| `CORS_ORIGINS` | Allowed frontend origins |
| `PORT` | Backend port (default `8000`) |

### Frontend (`frontend/.env`)
| Key | Description |
|-----|-------------|
| `VITE_API_URL` | Backend base URL |

## Project Structure

```
vibe
├── backend
│   ├── app
│   │   ├── api
│   │   ├── core
│   │   └── database
│   ├── requirements.txt
│   └── env.template
├── frontend
│   ├── src
│   ├── package.json
│   └── vite.config.ts
├── docs (guides in repo root)
│   ├── SETUP.md
│   ├── TESTING_GUIDE.md
│   └── HOW_TO_USE_IN_ROBLOX_STUDIO.md
└── .github/workflows/ci.yml
```

## Documentation

- `SETUP.md` – prerequisites, env vars, running locally
- `TESTING_GUIDE.md` – step-by-step verification + publishing
- `HOW_TO_USE_IN_ROBLOX_STUDIO.md` – Roblox Studio workflow

## Deployment / CI

GitHub Actions (`.github/workflows/ci.yml`) installs backend deps, compiles Python sources, installs frontend deps, builds the app, and uploads `frontend/dist` as an artifact on every push/PR to `main`/`master`.

## Development

- Backend: http://localhost:8000
- Frontend: http://localhost:5173

## License

MIT

