"""Lightweight local incident log storage for the site-operations assistant.

The MVP uses JSONL so it can run on the current private Render deployment without
external services. Entries are concise summaries of generated guidance; they do
not store uploaded files, raw full answer payloads, or local filesystem paths.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schemas import AgentAnswer

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LOG_PATH = PROJECT_ROOT / "data" / "incident_logs.jsonl"

ALLOWED_STATUSES = {"open", "watching", "resolved", "escalated"}

_LOCAL_PATH_RE = re.compile(
    r"(/Users/[^\s,;]+|/Desktop/Developer/[^\s,;]+|[A-Za-z]:\\[^\s,;]+)"
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _log_path() -> Path:
    configured = os.environ.get("ALLCPR_INCIDENT_LOG_PATH")
    return Path(configured) if configured else DEFAULT_LOG_PATH


def _scrub(value: Any) -> Any:
    if isinstance(value, str):
        return _LOCAL_PATH_RE.sub("[local path removed]", value)
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _scrub(v) for k, v in value.items()}
    return value


def _attachment_description(context: Optional[Dict[str, Any]]) -> str:
    atts = (context or {}).get("attachments")
    if not isinstance(atts, list):
        return ""
    descs: List[str] = []
    for att in atts[:4]:
        if isinstance(att, dict):
            desc = att.get("description") or att.get("filename") or att.get("type")
            if desc:
                descs.append(str(desc))
    return "; ".join(descs)


def _created_at(context: Optional[Dict[str, Any]]) -> str:
    raw = (context or {}).get("browser_timestamp")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return _now_iso()


def _access_ref_flags(answer: AgentAnswer) -> Dict[str, bool]:
    access_refs = [
        ref for ref in answer.operational_references
        if ref.scenario == "venue_access_issue"
    ]
    passcode_items = [
        item
        for ref in access_refs
        for item in ref.items
        if item.fact_type == "access_code" and item.sensitivity == "internal"
    ]
    return {
        "access_refs_shown": bool(access_refs),
        "trusted_passcode_refs_shown": bool(passcode_items),
    }


def build_log_entry(
    question: str,
    context: Optional[Dict[str, Any]],
    answer: AgentAnswer,
    *,
    created_by: str = "staff",
) -> Dict[str, Any]:
    """Create a concise, safe incident-log entry from an agent answer."""

    ctx = context or {}
    first_action = (answer.steps or answer.next_actions or answer.immediate_safety_check)[:3]
    entry: Dict[str, Any] = {
        "id": uuid.uuid4().hex[:12],
        "created_at": _created_at(ctx),
        "language": answer.language,
        "question": question or "",
        "scenario": answer.scenario,
        "issue_type": answer.issue_type,
        "severity": answer.severity,
        "confidence": answer.confidence,
        "needs_human_review": answer.needs_human_review,
        "site": ctx.get("site") or ctx.get("location") or "Unknown site",
        "class_time": ctx.get("class_time") or "",
        "attachment_description": _attachment_description(ctx),
        "first_action": first_action,
        "evidence_requested": answer.evidence_requested[:3],
        "contacts": answer.contacts[:3],
        "source_status": answer.source_status,
        "sop_image_count": len(answer.sop_images),
        "operational_reference_titles": [ref.title for ref in answer.operational_references[:3]],
        **_access_ref_flags(answer),
        "status": "open",
        "created_by": created_by or "staff",
        "assigned_to": "",
        "notes": [],
    }
    return _scrub(entry)


def append_log_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_entry = _scrub(entry)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(safe_entry, ensure_ascii=False, separators=(",", ":")) + "\n")
    return safe_entry


def append_answer_log(
    question: str,
    context: Optional[Dict[str, Any]],
    answer: AgentAnswer,
    *,
    created_by: str = "staff",
) -> Dict[str, Any]:
    return append_log_entry(build_log_entry(question, context, answer, created_by=created_by))


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


def list_logs(limit: int = 50) -> List[Dict[str, Any]]:
    limit = max(1, min(int(limit or 50), 200))
    return _read_all()[-limit:][::-1]


def get_log(log_id: str) -> Optional[Dict[str, Any]]:
    for entry in _read_all():
        if entry.get("id") == log_id:
            return entry
    return None


def patch_log(
    log_id: str,
    *,
    status: Optional[str] = None,
    note: Optional[str] = None,
    assigned_to: Optional[str] = None,
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
        if assigned_to is not None:
            entry["assigned_to"] = _scrub(str(assigned_to))
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
