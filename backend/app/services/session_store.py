from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SessionItem:
    created_at: float
    pack: Dict[str, Any]


class SessionStore:
    """In-memory session store for prototype.

    For production scale, swap to Redis/Postgres. This is intentionally simple.
    """

    def __init__(self, ttl_seconds: int = 60 * 60 * 2):
        self._ttl = ttl_seconds
        self._items: Dict[str, SessionItem] = {}

    def _gc(self) -> None:
        now = time.time()
        expired = [sid for sid, item in self._items.items() if (now - item.created_at) > self._ttl]
        for sid in expired:
            self._items.pop(sid, None)

    def create(self, pack: Dict[str, Any]) -> str:
        self._gc()
        sid = uuid.uuid4().hex
        self._items[sid] = SessionItem(created_at=time.time(), pack=pack)
        return sid

    def get(self, sid: str) -> Optional[Dict[str, Any]]:
        self._gc()
        item = self._items.get(sid)
        if not item:
            return None
        return item.pack


session_store = SessionStore()
