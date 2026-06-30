"""Reviewed SOP-derived operational references.

This module intentionally does not OCR images or inspect media pixels. It only
loads the committed, reviewed JSON extraction layer and deterministically matches
references by scenario, query keywords, and optional site context.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .schemas import OperationalReference

PACKAGE_ROOT = Path(__file__).resolve().parent
REFS_PATH = PACKAGE_ROOT / "sop_operational_refs.json"

_WORD_RE = re.compile(r"[a-z0-9]+")
_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")
_GENERIC_TERMS = {
    "smart manikin",
    "manikin",
    "假人",
    "door",
    "access",
    "room",
    "房间",
    "门禁",
    "密码",
}


def _norm(text: Any) -> str:
    return str(text or "").casefold()


def _context_text(context: Optional[Dict[str, Any]]) -> str:
    if not context:
        return ""
    values: List[str] = []
    for key in ("site", "location", "address", "room", "building", "city"):
        if context.get(key):
            values.append(str(context[key]))
    return " ".join(values)


def _contains(text: str, term: str) -> bool:
    term_l = _norm(term).strip()
    if not term_l:
        return False
    if _CJK_RE.search(term_l):
        return term_l in text
    if " " in term_l:
        return term_l in text
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(term_l)}(?![a-z0-9])", text))


def _has_site_match(raw: Dict[str, Any], question: str, context: Optional[Dict[str, Any]]) -> bool:
    haystack = _norm(f"{question} {_context_text(context)}")
    return any(_contains(haystack, alias) for alias in raw.get("site_aliases", []) or [])


def _has_site_context(context: Optional[Dict[str, Any]]) -> bool:
    return bool(_context_text(context).strip())


def _specific_match_count(raw: Dict[str, Any], question: str, context: Optional[Dict[str, Any]]) -> int:
    haystack = _norm(f"{question} {_context_text(context)}")
    count = 0
    for term in raw.get("applies_to", []) or []:
        term_l = _norm(term).strip()
        if not term_l or term_l in _GENERIC_TERMS:
            continue
        if _contains(haystack, term_l):
            count += 1
    return count


@lru_cache(maxsize=1)
def load_operational_ref_payload() -> List[Dict[str, Any]]:
    """Load raw refs for matching while keeping return fields schema-controlled."""

    try:
        payload = json.loads(REFS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    refs = payload.get("references", []) if isinstance(payload, dict) else []
    return [ref for ref in refs if isinstance(ref, dict)]


def find_operational_references(
    question: str,
    scenario: str,
    context: Optional[Dict[str, Any]] = None,
    *,
    limit: int = 3,
) -> List[OperationalReference]:
    """Return relevant reviewed operational references for an answer.

    Site-specific access refs only return when the question/context names a
    matching site, room, address, or alias. Generic access questions get the
    source-needed fallback rather than a dump of every known passcode.
    """

    scored: List[Tuple[int, str, Dict[str, Any]]] = []
    for raw in load_operational_ref_payload():
        if raw.get("scenario") != scenario:
            continue

        site_match = _has_site_match(raw, question, context)
        matches = _specific_match_count(raw, question, context)
        allow_unscoped_access_ref = (
            scenario == "venue_access_issue"
            and not _has_site_context(context)
            and matches > 0
        )
        if raw.get("requires_site_match") and not site_match and not allow_unscoped_access_ref:
            continue

        priority = int(raw.get("priority", 0) or 0)
        score = priority + (35 if site_match else 0) + (12 * matches)

        # General references remain useful for their exact scenario even when the
        # query has no extra keyword; topic refs need a direct keyword or a high
        # enough priority to be useful as scenario-level staff guidance.
        if matches or site_match or not raw.get("requires_site_match"):
            scored.append((score, str(raw.get("id", "")), raw))

    scored.sort(key=lambda item: (-item[0], item[1]))
    refs: List[OperationalReference] = []
    for _, _, raw in scored[:limit]:
        try:
            refs.append(OperationalReference(**raw))
        except (TypeError, ValueError):
            continue
    return refs
