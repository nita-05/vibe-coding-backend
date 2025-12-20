from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class FileSpec:
    path: str
    content: str


def _repo_root() -> Path:
    # backend/app/services/repo_templates.py -> repo root is 3 parents up
    return Path(__file__).resolve().parents[3]


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _safe_relpath(p: Path, root: Path) -> str:
    rel = p.resolve().relative_to(root.resolve())
    return str(rel).replace("\\", "/")


def seasonal_collector_pack() -> Dict[str, Any]:
    """Exports the existing SeasonalCollectorGame scripts into a pack.

    This is the "second template" that matches your full game structure.
    """

    root = _repo_root()
    game_root = root / "SeasonalCollectorGame"

    include_dirs = [
        game_root / "ServerScriptService",
        game_root / "StarterPlayer" / "StarterPlayerScripts",
        game_root / "ReplicatedStorage" / "Modules",
    ]

    files: List[FileSpec] = []

    for d in include_dirs:
        if not d.exists() or not d.is_dir():
            continue
        for p in sorted(d.rglob("*.lua")):
            if not p.is_file():
                continue
            rel = _safe_relpath(p, game_root)
            files.append(FileSpec(path=rel, content=_read_text(p)))

    if not files:
        return {
            "title": "SeasonalCollectorGame (Full Structure)",
            "description": "Could not find SeasonalCollectorGame scripts in this deployment.",
            "files": [],
            "setup_instructions": [
                "This environment doesn’t contain the SeasonalCollectorGame folder.",
                "Run the backend from the repo root checkout so it can read SeasonalCollectorGame/.",
            ],
            "notes": [
                "If deployed, you may need to include the SeasonalCollectorGame folder in the build artifact.",
            ],
        }

    return {
        "title": "SeasonalCollectorGame (Full Structure)",
        "description": "Exports your existing SeasonalCollectorGame scripts into a copy/paste pack.",
        "files": [{"path": f.path, "content": f.content} for f in files],
        "setup_instructions": [
            "In Roblox Studio, open your place.",
            "Create the folders (ServerScriptService / ReplicatedStorage / StarterPlayer) if missing.",
            "Create each .lua file at the exact path shown and paste its contents.",
            "Press Play to test.",
        ],
        "notes": [
            "This template is an export of your repo’s current SeasonalCollectorGame scripts.",
            "For AI edits, use ‘Regenerate with changes’ so the model can modify the exported files.",
        ],
    }
