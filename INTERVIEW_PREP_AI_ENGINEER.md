# AI Engineer Interview Prep — Vibe Coding Platform (Roblox x GenAI)

This doc is written to match the role you pasted:

- **Design/build first working prototype** for Vibe Coding
- **Integrate AI** that translates text prompts → Roblox Lua scripts/environments
- **Smooth UX** for creating/editing/testing games
- **Optimize** scalability + performance

Use this as your “script” for interviews.

---

## What you built (your one-liner)

**Vibe Coding is a prompt-to-Roblox creation platform**: a React app sends a user’s game idea to a FastAPI backend, which uses OpenAI to generate a structured JSON response containing a complete Roblox Lua script + testing steps + assets + optimization tips, with optional Roblox Open Cloud publishing.

---

## System architecture (what to say)

### High level

- **Frontend (React + Vite + TS)**: prompt input, blueprint selection, editor (Monaco), and calls backend APIs.
- **Backend (FastAPI)**: routes for generation, drafts, blueprints, AI chat, and optional publish.
- **AI layer (OpenAI)**: prompt engineering + JSON response parsing + safety validation.
- **Persistence (SQLite)**: saves drafts (prompt/settings/result) for replay and iteration.
- **Publishing (Roblox Open Cloud)**: backend can push a generated `.rbxlx` (RBXLX XML) containing the script into an existing place.

### Concrete code map (point to files)

- **API server**: `backend/app/main.py` (FastAPI + CORS + routes)
- **Routes**: `backend/app/api/routes.py`
  - `POST /api/generate` (core)
  - `POST /api/draft`, `GET /api/draft/{id}`, `GET /api/drafts`
  - `GET /api/blueprints`
  - `POST /api/roblox/publish` (+ `/api/roblox/status`)
  - `POST /api/ai/chat` (NPC / in-game assistant style chat)
- **OpenAI client**: `backend/app/core/openai_client.py`
- **Prompt engineering + safety checks**: `backend/app/core/prompt_builder.py`
- **Roblox publishing**: `backend/app/core/roblox_client.py`
- **Frontend API wrapper**: `frontend/src/services/api.ts`

---

## Critical flow: prompt → Lua script

### What happens end-to-end

1. **Frontend** sends `{ prompt, blueprint_id, settings }` to `POST /api/generate`.
2. **Backend** uses `PromptBuilder.enhance_prompt()` to add blueprint guidance and “interpret natural language” context.
3. **OpenAIClient.generate_roblox_script()** calls OpenAI Chat Completions and requests **JSON output** (`response_format = json_object` when supported).
4. Backend **parses/repairs JSON** defensively (handles markdown fences + control characters).
5. Backend runs `PromptBuilder.validate_script_safety()` to flag risky Lua patterns and completeness warnings.
6. Backend returns a structured payload `{ title, narrative, lua_script, testing_steps, assets_needed, optimization_tips, validation }`.

### Why interviewers like this

- You built **a real product loop**: generate → inspect → iterate → save draft → publish.
- You use **structured outputs** to make AI reliable in a production UI.
- You added **guardrails** (script safety + completeness checks).

---

## Scalability + performance: what you should say (and what you’d improve next)

### What you already did

- **Structured JSON outputs** reduce UI parsing failures and make downstream handling deterministic.
- **Defensive parsing** handles messy model outputs (control chars, markdown wrapping).
- **Separation of concerns**: prompt building, model call, safety validation, publishing are isolated.

### Real-world improvements (say this if asked “what’s missing?”)

**Backend scalability**
- Add **rate limiting** per IP/user for `/api/generate` (prevents abuse + cost blowups).
- Add **request queue + worker** (Celery/RQ) if generation becomes heavy; return job IDs.
- Add **caching** for identical prompts/settings (optional, huge cost win).
- Add **streaming** (SSE/WebSocket) so users see partial output while the model is generating.

**Model reliability**
- Add **schema validation** (e.g., Pydantic JSON schema checks) and auto-retry with tighter instructions.
- Add **model fallback** (gpt-4o → gpt-4o-mini) for cost/latency tiers.
- Add **prompt versioning** (store “prompt template version” with drafts for reproducibility).

**Safety**
- Expand “dangerous patterns” to Roblox-specific exploit vectors and remove false positives.
- Add **output sandbox checks**: limit size, forbid RemoteEvent backdoors, forbid suspicious `HttpService` patterns, etc.

**Evaluation**
- Create a small **offline eval set**: prompts + expected properties (has spawns, has score UI, etc.).
- Track: **success rate**, “time-to-first-playable”, parse-failure rate, user edit distance.

---

## Interview Q&A (tailored to this JD)

### 1) “Design and build the first working prototype”

**Answer**:
“I shipped an end-to-end prototype: React UI → FastAPI → OpenAI generation → JSON response with Lua script + testing steps, plus drafts stored in SQLite and optional Roblox Open Cloud publishing. The goal was to minimize time-to-first-playable for Roblox creators.”

### 2) “How do you translate text prompts into Roblox scripts?”

**Answer**:
“I treat it as a structured generation problem. I use blueprint-aware prompt engineering to constrain the output, request JSON output so parsing is reliable, then validate the generated Lua for safety and completeness before showing it to the user.”

### 3) “How do you make user interaction smooth?”

**Answer**:
“On the frontend, the user selects a blueprint, enters a prompt, gets a generated script into an editor, and can save drafts. Next step is streaming so they see progress instantly, and adding inline validation highlights based on the safety report.”

### 4) “How do you optimize for performance and scale?”

**Answer**:
“The immediate wins are rate limiting and queueing model calls, plus caching repeated prompts. For UX performance, streaming output reduces perceived latency. For cost control, fallback models and prompt compression help.”

### 5) “Prompt engineering—what did you actually do?”

**Answer**:
“I created a system prompt that forces complete, runnable Roblox scripts and uses blueprint-specific constraints. I also added deterministic output formatting (JSON keys), plus validation heuristics (e.g., check obby has SpawnLocation and enough platforms).”

### 6) “How do you validate safety?”

**Answer**:
“I run a static scan for disallowed patterns (file access, OS execution, suspicious requires) and Roblox compatibility signals, and I return warnings/errors + risk score. In production, I’d extend this with a stricter Lua AST-based analyzer and allowlists.”

### 7) “Why FastAPI instead of Node?”

**Answer**:
“FastAPI is a great fit because the AI integration and schema validation are Python-native, and it’s fast to build typed APIs. The architecture is API-first, so swapping or adding a Node service is easy if needed.”

### 8) “How would you work with Roblox communities?”

**Answer**:
“I’d run structured playtests: collect prompts users actually type, measure success rate to ‘playable in Studio’, track where they edit the script, then update blueprints/prompt constraints and UI to close those gaps.”

---

## Your 60-second pitch (memorize)

“I built Vibe Coding, a prototype that turns natural language into working Roblox Lua. The React UI lets creators choose a blueprint, generate a script via a FastAPI backend, edit it in an editor, save drafts, and optionally publish to Roblox Open Cloud. Technically, I constrained generation with blueprint-aware prompt engineering, enforced structured JSON outputs for reliability, added safety/completeness validation, and designed the system to scale with rate limiting, queueing, and streaming as next steps.”

---

## Gap checklist vs the JD (what to add if you have time)

- **Scalability**: rate limiting, queue/worker, caching, streaming
- **Reliability**: schema validation + retry strategy + fallback models
- **Observability**: request IDs, logs, latency metrics, error dashboards
- **Evaluation**: offline prompt suite + success metrics
- **Community feedback loop**: collect real prompts + iterate blueprint constraints

---

## What to bring to the interview (concrete artifacts)

- A short demo: generate → edit → save draft → publish
- A slide or README section: “Architecture + safety + scaling roadmap”
- 3 examples: prompts and the generated scripts (good variety: obby, tycoon, fps)


