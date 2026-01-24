from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from openai import OpenAI

from app.settings import settings


def _client() -> OpenAI:
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY not configured on server.",
        )
    # Deployment-friendly defaults: bounded latency + small retry budget.
    # Timeout set to 45 seconds to stay under most deployment platform limits (30-60s)
    # For complex custom prompts, this should be sufficient
    return OpenAI(api_key=settings.openai_api_key, timeout=45.0, max_retries=2)


def chat(*, messages: List[Dict[str, str]], system_prompt: str, temperature: float, max_tokens: int) -> str:
    try:
        resp = _client().chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"Upstream AI error: {e}")


def chat_stream(*, messages: List[Dict[str, str]], system_prompt: str, temperature: float, max_tokens: int):
    """Yield assistant tokens as they stream from OpenAI."""
    try:
        stream = _client().chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for event in stream:
            try:
                delta = event.choices[0].delta.content  # type: ignore[attr-defined]
            except Exception:
                delta = None
            if delta:
                yield delta
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"Upstream AI error: {e}")


def generate_json(
    *,
    prompt: str,
    system_prompt: str,
    temperature: float,
    max_tokens: int,
    extra_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate a JSON object from a prompt.

    Uses response_format=json_object when supported.
    Falls back to JSON extraction if model returns text.
    """

    user_payload: Dict[str, Any] = {"prompt": prompt}
    if extra_context:
        user_payload["context"] = extra_context

    try:
        resp = _client().chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload)},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        text = (resp.choices[0].message.content or "").strip()
    except TypeError:
        # Some models/SDK versions may not support response_format
        resp = _client().chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload)},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text = (resp.choices[0].message.content or "").strip()
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"Upstream AI error: {e}")

    # Parse JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Best-effort: extract first {...} block
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                pass
        raise HTTPException(status_code=502, detail="AI returned non-JSON output.")
