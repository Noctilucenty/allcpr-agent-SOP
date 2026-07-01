"""Local storage for lightweight quick class-readiness reports.

Distinct from the staff inspection log (separate JSONL file,
``log_type == "student_site_check"``). A quick check is a light user simply
reporting visible problems before/during class — it carries no staff duties.

Stores only what was reported: site, class time, optional name, issue
categories, a short description, and whether a photo was taken. Never raw image
bytes, local filesystem paths, passcodes, staff PINs, or answer keys — the same
scrubbing used by the incident/inspection logs is applied to every entry.
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from .incident_logs import _now_iso, _scrub

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LOG_PATH = PROJECT_ROOT / "data" / "student_site_checks.jsonl"

# A quick report is never "done" on its own — it always awaits staff review, and
# a safety concern escalates. Kept separate from the inspection status set.
ALLOWED_STATUSES = {"submitted", "needs_staff_review", "safety_escalation"}


def _log_path() -> Path:
    configured = os.environ.get("ALLCPR_STUDENT_CHECK_LOG_PATH")
    return Path(configured) if configured else DEFAULT_LOG_PATH


def _decide_status(safety_concern: bool) -> str:
    """A safety concern always escalates; everything else awaits staff review."""
    return "safety_escalation" if safety_concern else "needs_staff_review"


def build_student_check_entry(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a concise, safe quick-check entry from a request payload."""
    safety = bool(payload.get("safety_concern"))
    entry: Dict[str, Any] = {
        "id": uuid.uuid4().hex[:12],
        "log_type": "student_site_check",
        "inspection_actor_type": "quick_check",
        "inspection_mode": "quick_class_readiness",
        "created_at": _now_iso(),
        "language": payload.get("language") or "en",
        "site": payload.get("site") or "Unknown site",
        "class_time": payload.get("class_time") or "",
        "name_optional": payload.get("name_optional") or "",
        "issue_categories": [str(x) for x in (payload.get("issue_categories") or [])],
        "description": str(payload.get("description") or ""),
        "photo_taken": bool(payload.get("photo_taken")),
        "class_blocked": bool(payload.get("class_blocked")),
        "safety_concern": safety,
        "status": _decide_status(safety),
    }
    return _scrub(entry)


def append_student_check(payload: Dict[str, Any]) -> Dict[str, Any]:
    entry = build_student_check_entry(payload)
    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")
    return entry


def _read_all() -> List[Dict[str, Any]]:
    path = _log_path()
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


def list_student_checks(limit: int = 50) -> List[Dict[str, Any]]:
    limit = max(1, min(int(limit or 50), 200))
    return _read_all()[-limit:][::-1]


def get_student_check(check_id: str) -> Optional[Dict[str, Any]]:
    for entry in _read_all():
        if entry.get("id") == check_id:
            return entry
    return None
