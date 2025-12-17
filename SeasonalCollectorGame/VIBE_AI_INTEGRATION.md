# Vibe AI Integration (SeasonalCollectorGame ↔ Vibe Coding Platform)

This adds an **in-game “Vibe AI” NPC** that sends player questions to your **FastAPI backend** (`/api/ai/chat`), which then uses OpenAI to respond.

Nothing in coins/bank/events/hazards/leveling changes—this is an optional add-on.

---

## 1) Run your Vibe Coding backend

From repo root:

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Confirm it works:
- `GET /health` returns healthy
- `POST /api/ai/chat` returns `{ message, success }`

---

## 2) Make the backend reachable from Roblox

Roblox **cannot** reach `localhost` on your PC.

Use one of these:
- **Deploy** your backend (recommended): Render/Fly.io/Azure/etc. with HTTPS
- **Use a tunnel** for testing: ngrok/cloudflared to expose `https://...`

Your backend URL should look like:
- `https://your-domain.com`

---

## 3) Roblox Studio settings

In Roblox Studio:
- **Game Settings → Security → Enable Studio Access to API Services**
- **Enable HTTP Requests (HttpService)**

---

## 4) Configure BackendUrl in Roblox

In Explorer:
- `ReplicatedStorage`
  - `VibeConfig`
    - `BackendUrl` (StringValue)

Set `BackendUrl.Value` to your deployed/tunneled base URL (no trailing slash), for example:
- `https://your-domain.com`

---

## 5) Test in-game

1. Press Play
2. Walk to `Vibe AI`
3. Press **E**
4. Type a question (example):
   - “How do I level up fast?”
   - “What happens if my wallet is full?”
5. Press Enter or Send

If backend is not configured, the AI will respond with a helpful setup message.

---

## Troubleshooting

- **“Server setup needed: enable HttpService…”**
  - Enable HTTP requests / API services in Studio
- **“AI request failed…”**
  - `BackendUrl` is wrong or not reachable from Roblox
  - backend is down
  - tunnel URL changed


