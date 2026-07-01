"""Local storage for Smart Manikin onboarding-test attempts.

Mirrors ``inspection_logs.py``: append-only JSONL, reuses the same
``_scrub``/``_now_iso`` helpers, and an env-var override for test isolation
(``ALLCPR_ONBOARDING_ATTEMPT_PATH``). Entries record the certification result so
management can review who passed — never raw image bytes, local filesystem
paths, passcodes, or staff PINs.

The score is always recomputed here from the submitted answers via
``score_onboarding_attempt`` — a client-supplied ``score``/``passed``/``status``
is ignored, so the server stays the single source of truth.
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List

from .incident_logs import _now_iso, _scrub
from .onboarding_quiz import score_onboarding_attempt

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ATTEMPT_PATH = PROJECT_ROOT / "data" / "onboarding_attempts.jsonl"


def _attempt_path() -> Path:
    configured = os.environ.get("ALLCPR_ONBOARDING_ATTEMPT_PATH")
    return Path(configured) if configured else DEFAULT_ATTEMPT_PATH


def _clean_answers(raw: Any) -> Dict[str, str]:
    """Coerce answers to a small ``{qid: letter}`` string map.

    Anything that is not a flat string->scalar map is dropped, so image bytes,
    nested objects, or file references can never reach the log.
    """
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(value, (str, int, float, bool)):
            out[str(key)] = str(value)
    return out


def build_onboarding_attempt(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a concise, safe onboarding-attempt entry from a request payload.

    Only a fixed set of fields is persisted; the score/pass-fail is recomputed
    from the answers, not trusted from the payload.
    """
    answers = _clean_answers(payload.get("answers"))
    result = score_onboarding_attempt(answers)

    entry: Dict[str, Any] = {
        "id": uuid.uuid4().hex[:12],
        "log_type": "onboarding_attempt",
        "created_at": _now_iso(),
        "language": payload.get("language") or "en",
        "staff": payload.get("staff") or "",
        "site": payload.get("site") or "",
        "answers": answers,
        "score": result["score"],
        "total": result["total"],
        "passing_score": result["passing_score"],
        "passed": result["passed"],
        "status": result["status"],
        "missed_questions": result["missed_questions"],
        "critical_misses": result["critical_misses"],
    }
    return _scrub(entry)


def append_onboarding_attempt(payload: Dict[str, Any]) -> Dict[str, Any]:
    entry = build_onboarding_attempt(payload)
    path = _attempt_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")
    return entry


def _read_all() -> List[Dict[str, Any]]:
    path = _attempt_path()
    if not path.exists():
        return []
    entries: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            entries.append(_scrub(item))
    return entries


def list_onboarding_attempts(limit: int = 50) -> List[Dict[str, Any]]:
    limit = max(1, min(int(limit or 50), 200))
    return _read_all()[-limit:][::-1]
