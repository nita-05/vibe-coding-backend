# Testing Guide

Use this checklist to verify the Vibe Coding platform end-to-end.

---

## 1. AI pipeline (web UI)

1. Start backend (`uvicorn app.main:app --reload`)
2. Start frontend (`npm run dev`)
3. Visit http://localhost:5173
4. Enter a natural-language prompt, e.g.
   ```
   Create a tall glowing red capture-the-flag arena with blue and red bases.
   ```
5. Click **Generate Script**
6. Confirm:
   - Validation banner shows “Safe to use”
   - Code editor contains Lua script
   - Voice guide can describe how to play

---

## 2. Manual Roblox Studio test

1. Click **Copy Code** in the UI
2. Open Roblox Studio → **File → New → Baseplate**
3. In **Explorer**, right-click `ServerScriptService` → **Insert Object → Script**
4. Delete default code and paste the generated script
5. Click **Play**
6. Verify that what you described appears:
   - Colors, sizes, and glowing effects match the prompt
   - Touch events (flags, checkpoints) work
   - Leaderboards/teams update as you play

> Detailed instructions live in `HOW_TO_USE_IN_ROBLOX_STUDIO.md`.

---

## 3. Automated Roblox publishing (optional)

> Requires `ROBLOX_API_KEY`, `ROBLOX_UNIVERSE_ID`, `ROBLOX_PLACE_ID` in `backend/.env`.

1. In the UI, click **Publish to Roblox**
2. Provide a place name/description
3. Backend calls Roblox Open Cloud to upload a new place version
4. Success response includes:
   - `place_id`
   - `version_number`
   - `play_url` and `embed_url`
5. Open the `play_url` in a browser to confirm the new version is live

---

## 4. API sanity checks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Basic health check |
| `/api/generate` | POST | Generates Lua from prompt |
| `/api/draft` | POST | Saves a draft |
| `/api/drafts` | GET | Lists drafts |
| `/api/roblox/status` | GET | Confirms Roblox credentials |
| `/api/roblox/publish` | POST | Publishes to Roblox |

Use `curl` or Thunder Client to verify JSON responses.

---

## 5. CI + build verification

On every PR/push:

1. GitHub Actions installs backend deps and runs `python -m compileall backend`
2. Installs frontend deps and runs `npm run build`
3. Uploads `frontend/dist` as an artifact

Check the CI tab to ensure the workflow passes before merging.

---

All tests passing? You’re ready to invite Roblox creators for feedback.

