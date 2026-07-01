"""Local storage for Smart Manikin site-inspection records.

Distinct from incident logs (separate JSONL file, ``log_type == "inspection"``)
but reuses the same scrubbing/JSONL approach. Entries store checklist statuses,
photo-step acknowledgements, and the required-acknowledgement confirmation only —
never raw image bytes, local filesystem paths, or passcodes.
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from .incident_logs import _now_iso, _scrub

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LOG_PATH = PROJECT_ROOT / "data" / "inspection_logs.jsonl"

ALLOWED_STATUSES = {"open", "needs_support", "completed"}


def _log_path() -> Path:
    configured = os.environ.get("ALLCPR_INSPECTION_LOG_PATH")
    return Path(configured) if configured else DEFAULT_LOG_PATH


def _bool(value: Any) -> bool:
    return bool(value)


def _item_flags(items: List[Dict[str, Any]]) -> Dict[str, int]:
    """Derive fixed/needs-support counts from checklist item statuses."""
    fixed = 0
    needs_support = 0
    for item in items or []:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "")).strip().lower()
        if status in {"fixed", "fixed_on_site"} or _bool(item.get("fixed_on_site")):
            fixed += 1
        if status in {"problem", "needs_support"} or _bool(item.get("needs_support")):
            needs_support += 1
    return {"fixed_on_site_count": fixed, "needs_support_count": needs_support}


def _decide_status(payload: Dict[str, Any], needs_support_count: int) -> str:
    explicit = str(payload.get("status") or "").strip().lower()
    if explicit in ALLOWED_STATUSES:
        # An explicit needs_support always wins; otherwise honour what was sent.
        if needs_support_count > 0:
            return "needs_support"
        return explicit
    if needs_support_count > 0 or payload.get("problems_found"):
        return "needs_support"
    if (
        payload.get("completed_at")
        and payload.get("weekly_report_completed")
        and payload.get("upload_completed")
    ):
        return "completed"
    return "open"


def build_inspection_entry(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a concise, safe inspection-log entry from a request payload."""
    items = payload.get("site_checklist_items") or []
    derived = _item_flags(items)
    needs_support_count = max(
        int(payload.get("needs_support_count") or 0), derived["needs_support_count"]
    )
    fixed_on_site_count = max(
        int(payload.get("fixed_on_site_count") or 0), derived["fixed_on_site_count"]
    )
    status = _decide_status(payload, needs_support_count)

    notes: List[Dict[str, str]] = []
    note_text = str(payload.get("notes") or "").strip()
    if note_text:
        notes.append({"at": _now_iso(), "text": note_text, "created_by": "staff"})

    entry: Dict[str, Any] = {
        "id": uuid.uuid4().hex[:12],
        "log_type": "inspection",
        "scenario": "smart_manikin_site_inspection",
        "created_at": _now_iso(),
        "language": payload.get("language") or "en",
        "site": payload.get("site") or "Unknown site",
        "staff": payload.get("staff") or "",
        "started_at": payload.get("started_at") or "",
        "completed_at": payload.get("completed_at") or "",
        "inspection_warning_acknowledged": _bool(payload.get("inspection_warning_acknowledged")),
        "acknowledged_at": payload.get("acknowledged_at") or "",
        "before_photo_checks": payload.get("before_photo_checks") or {},
        "site_checklist_items": items,
        "post_photo_checks": payload.get("post_photo_checks") or {},
        "weekly_report_completed": _bool(payload.get("weekly_report_completed")),
        "upload_completed": _bool(payload.get("upload_completed")),
        "problems_found": list(payload.get("problems_found") or []),
        "fixed_on_site_count": fixed_on_site_count,
        "needs_support_count": needs_support_count,
        "status": status,
        "notes": notes,
        "inspection_actor_type": payload.get("inspection_actor_type") or "staff",
        "inspection_mode": payload.get("inspection_mode") or "full_site_inspection",
        "table_precheck": payload.get("table_precheck") or {},
    }
    return _scrub(entry)


def append_inspection_entry(payload: Dict[str, Any]) -> Dict[str, Any]:
    entry = build_inspection_entry(payload)
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


def list_inspection_logs(limit: int = 50) -> List[Dict[str, Any]]:
    limit = max(1, min(int(limit or 50), 200))
    return _read_all()[-limit:][::-1]


def get_inspection_log(log_id: str) -> Optional[Dict[str, Any]]:
    for entry in _read_all():
        if entry.get("id") == log_id:
            return entry
    return None


def patch_inspection_log(
    log_id: str,
    *,
    status: Optional[str] = None,
    note: Optional[str] = None,
    created_by: str = "staff",
) -> Optional[Dict[str, Any]]:
    entries = _read_all()
    patched: Optional[Dict[str, Any]] = None
    for entry in entries:
        if entry.get("id") != log_id:
            continue
        if status:
            if status not in ALLOWED_STATUSES:
                raise ValueError(f"invalid status: {status}")
            entry["status"] = status
        if note:
            notes = entry.setdefault("notes", [])
            if isinstance(notes, list):
                notes.append(
                    {
                        "at": _now_iso(),
                        "text": _scrub(str(note)),
                        "created_by": _scrub(created_by or "staff"),
                    }
                )
        patched = _scrub(entry)
        break
    if patched is None:
        return None
    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(_scrub(entry), ensure_ascii=False, separators=(",", ":")) + "\n")
    return patched
