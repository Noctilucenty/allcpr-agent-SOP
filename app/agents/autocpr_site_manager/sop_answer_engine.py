"""SOP knowledge-base retrieval + answer composition ("AI 整理后的 SOP 智能知识库").

Purpose
-------
Users describe a problem in their own messy wording ("the little screen thing is
frozen", "桌上少东西", "camera seems off"). The deterministic keyword classifier
in :mod:`scenarios` only routes exact vocabulary, so paraphrases fall through to
``unknown`` and the user gets no step-by-step help. This module bridges that gap.

How it stays SOP-backed (never invents content)
-----------------------------------------------
It does NOT write new steps. It maps a messy question to the closest existing
SOP *route* (a scenario or a Smart Manikin sub-issue) and then re-uses the
deterministic :func:`agent.answer_question` engine — via a canonical anchor
phrase that is guaranteed (and unit-tested) to route to that scenario/sub-issue —
to produce the real source-backed answer. Because the answer comes straight back
through ``answer_question``, every guardrail is inherited unchanged: passcodes are
redacted unless a valid staff token is present, source-status is preserved, and
"do not repair/dismantle" cautions stay attached.

Two matching layers, always degrading safely
--------------------------------------------
1. **Lexical** (always on, no API): BM25-style token/phrase overlap against each
   route's known trigger vocabulary. Catches paraphrases that still share words.
2. **AI intent hint** (optional): when the OpenAI intent layer is enabled it
   returns a *validated* ``scenario_hint`` / ``subtype_hint``; those sharpen the
   match for pure semantic paraphrases ("dummy" → manikin). Passed in by the
   caller; this module never calls the network itself.

If neither layer finds a confident match the result is ``found: False`` with a
"could not find this in the SOP — contact staff" note. Low-confidence matches are
flagged ``needs_human_review`` so the UI can say "possible match, confirm with
staff" rather than presenting a guess as authoritative.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from . import scenarios as _scenarios
from . import smart_manikin_subissues as _sub
from .retriever import tokenize
from .schemas import AgentAnswer

# ---------------------------------------------------------------------------
# Canonical anchor phrases. Each is a phrase that the deterministic classifier
# already routes to the intended scenario / sub-issue. A route is only useful if
# we can re-derive its real SOP answer, and the cleanest way to do that without
# duplicating agent.py is to feed a known-good phrase back through
# ``answer_question``. ``test_sop_answer_engine`` asserts every anchor still
# routes where we claim, so drift is caught.
# ---------------------------------------------------------------------------
_SUBISSUE_ANCHORS: Dict[str, str] = {
    _sub.IPAD_PAD_POWER_OR_OPEN: "ipad black screen",
    _sub.BLUETOOTH_CONNECTION: "bluetooth won't connect",
    _sub.TRAINING_NO_DATA: "training no data",
    _sub.BLACK_SCREEN_APP_RESTART: "app restart lost progress",
    _sub.CAMERA_BROWSER_PERMISSION: "camera permission denied",
    _sub.TIMER_LOGOUT_RESET: "timer reset",
    _sub.COMPLETION_PHOTO: "completion photo",
    _sub.WRONG_ROOM_FLOOR: "manikin room/floor issue",
}

# Extra plain-language vocabulary the source term lists do not spell out, so a
# lexical match can still fire on common paraphrases. These are HINT terms only —
# they never add SOP content, they just help pick an existing route.
_EXTRA_ROUTE_TERMS: Dict[str, Tuple[str, ...]] = {
    _sub.BLUETOOTH_CONNECTION: (
        "dummy won't link", "won't link", "wont link", "link up", "not linking",
        "pair", "pairing", "won't pair", "connect to app", "connect to the app",
        "device won't connect", "设备连不上", "连不上手机", "连接不上",
    ),
    _sub.IPAD_PAD_POWER_OR_OPEN: (
        "apple logo", "stuck on logo", "frozen screen", "screen frozen",
        "little screen", "screen thing", "won't respond", "unresponsive",
        "屏幕卡住", "卡在", "死机",
    ),
    "class_cannot_start": (
        "can't start class", "cannot start class", "can't start the class",
        "cannot start the practice", "can't get the session going",
        "practice session", "start the session", "student can't start",
        "student cannot start", "学生开始不了", "开始不了课程", "开不了课",
    ),
    "smart_manikin_site_inspection": (
        "what should be on the table", "what's on the desk", "on the desk",
        "on the table", "missing from the table", "table missing",
        "nothing on the desk", "desk missing", "桌上少东西", "桌上应该有什么",
        "少东西", "缺东西", "table looks wrong", "desk looks wrong",
        "equipment placement", "bvm missing", "breathing bag missing",
        "breathing bag thing missing", "i don't see the breathing bag",
        "pocket mask missing",
    ),
    "smart_manikin_troubleshooting": (
        "camera", "camera off", "camera not working", "camera broken",
        "webcam", "摄像头", "摄像头坏", "摄像头不工作",
    ),
}


class _Route:
    """One retrievable SOP route: a scenario or a Smart Manikin sub-issue."""

    __slots__ = ("route_id", "kind", "scenario", "subissue", "anchor", "terms",
                 "audience", "_term_tokens")

    def __init__(self, route_id: str, kind: str, scenario: str, subissue: str,
                 anchor: str, terms: Tuple[str, ...], audience: str) -> None:
        self.route_id = route_id
        self.kind = kind
        self.scenario = scenario
        self.subissue = subissue
        self.anchor = anchor
        self.terms = terms
        self.audience = audience
        toks: set[str] = set()
        for t in terms:
            toks.update(tokenize(t))
        self._term_tokens = toks


# Scenarios that are staff-only (their SOP workflow assumes a staff/site rep).
_STAFF_ONLY_SCENARIOS = {"smart_manikin_site_inspection"}


def _build_routes() -> List[_Route]:
    routes: List[_Route] = []

    # Sub-issue routes (Smart Manikin device problems) — most specific, first.
    for subissue, terms in _sub._PATTERNS:
        anchor = _SUBISSUE_ANCHORS.get(subissue)
        if not anchor:
            continue
        extra = _EXTRA_ROUTE_TERMS.get(subissue, ())
        routes.append(_Route(
            route_id=f"subissue:{subissue}",
            kind="subissue",
            scenario="smart_manikin_troubleshooting",
            subissue=subissue,
            anchor=anchor,
            terms=tuple(terms) + extra,
            audience="both",
        ))

    # Scenario routes — anchor is a keyword that classifies to the scenario.
    for scenario, keywords in _scenarios._RULES:
        if scenario == "unknown" or not keywords:
            continue
        anchor = keywords[0]
        extra = _EXTRA_ROUTE_TERMS.get(scenario, ())
        audience = "staff" if scenario in _STAFF_ONLY_SCENARIOS else "both"
        routes.append(_Route(
            route_id=f"scenario:{scenario}",
            kind="scenario",
            scenario=scenario,
            subissue="",
            anchor=anchor,
            terms=tuple(keywords) + extra,
            audience=audience,
        ))
    return routes


_ROUTES: Optional[List[_Route]] = None


def _routes() -> List[_Route]:
    global _ROUTES
    if _ROUTES is None:
        _ROUTES = _build_routes()
    return _ROUTES


def _score(route: _Route, query: str, q_tokens: set[str]) -> float:
    """Lexical relevance of ``route`` to the query.

    Token overlap gives a base signal; a whole trigger phrase appearing verbatim
    in the query is a much stronger signal, so it is weighted heavily.
    """
    overlap = len(q_tokens & route._term_tokens)
    phrase = 0
    low = query.lower()
    for t in route.terms:
        if len(t) >= 3 and t.lower() in low:
            phrase += 4
    return overlap + phrase


def retrieve_route(query: str, *, audience: str = "both") -> Optional[Tuple[_Route, float]]:
    """Return the best-matching route and its score, or ``None`` if nothing
    meaningfully overlaps. Staff-only routes are hidden from student audience."""
    q_tokens = set(tokenize(query or ""))
    if not q_tokens:
        return None
    best: Optional[Tuple[_Route, float]] = None
    for route in _routes():
        if audience == "student" and route.audience == "staff":
            continue
        s = _score(route, query, q_tokens)
        if s <= 0:
            continue
        if best is None or s > best[1]:
            best = (route, s)
    # Require at least a phrase hit or two overlapping tokens to count as a match —
    # a single common token ("the", tokenized away already, or "on") is too weak.
    if best is None or best[1] < 2:
        return None
    return best


def sop_assist_recommended(answer: AgentAnswer) -> bool:
    """Whether the deterministic answer is weak enough that a knowledge-base
    match would add value (messy wording the classifier could not route)."""
    return (
        answer.scenario == "unknown"
        or answer.confidence == "low"
        or not answer.steps
    )


# Standard reference-only caution (images/diagrams never authorize a repair).
_CAUTION = {
    "en": "Reference only; do not repair or dismantle equipment.",
    "zh": "仅供参考；请勿维修或拆卸设备。",
}
_NOT_FOUND_NOTE = {
    "en": "I could not find this in the SOP. Please contact staff/supervisor.",
    "zh": "未在 SOP 中找到相关内容，请联系员工/主管。",
}
_LOW_CONF_NOTE = {
    "en": "Possible SOP match — please confirm with staff before acting.",
    "zh": "可能的 SOP 匹配——执行前请与员工确认。",
}


def _image_refs(answer: AgentAnswer, lang: str) -> List[Dict[str, str]]:
    refs: List[Dict[str, str]] = []
    caution = _CAUTION["zh" if lang == "zh" else "en"]
    for img in (answer.sop_images or [])[:2]:
        url = getattr(img, "url", "") or getattr(img, "extracted_path", "")
        if not url:
            continue
        refs.append({
            "title": getattr(img, "title", "") or "SOP reference image",
            "path": url,
            "caution": caution,
        })
    return refs


def _sources(answer: AgentAnswer) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for s in (answer.sources or [])[:5]:
        out.append({"label": s, "type": "sop_source"})
    return out


def _is_sensitive_ref_item(item: Any) -> bool:
    sensitivity = str(getattr(item, "sensitivity", "") or "").lower()
    text = f"{getattr(item, 'label', '')} {getattr(item, 'value', '')}".lower()
    if sensitivity in {"internal", "restricted"}:
        return True
    return any(token in text for token in ("passcode", "password", "lockbox", "wi-fi", "wifi", "密码"))


def _raw_source_chunks(answer: AgentAnswer) -> List[Dict[str, str]]:
    from .ai_orchestrator import redact_text, sensitive_values  # local import avoids widening module coupling

    def scrub(text: str) -> str:
        out = str(redact_text(text) or "")
        for secret in sensitive_values():
            for token in re.findall(r"[A-Za-z0-9]{4,}", str(secret or "")):
                if any(ch.isdigit() for ch in token) and token in out:
                    out = out.replace(token, "[redacted]")
        return out

    chunks: List[Dict[str, str]] = []
    for ref in (answer.operational_references or []):
        for item in (getattr(ref, "items", None) or []):
            if _is_sensitive_ref_item(item):
                continue
            value = str(getattr(item, "value", "") or "").strip()
            if not value:
                continue
            chunks.append({
                "label": scrub(str(getattr(item, "label", "") or "Source note")),
                "value": scrub(value),
                "source": scrub(str(getattr(ref, "title", "") or getattr(ref, "id", "") or "")),
                "source_status": str(getattr(ref, "source_status", "") or ""),
            })
            if len(chunks) >= 10:
                return chunks
    return chunks


def _match_from_answer(
    answer: AgentAnswer,
    *,
    confidence: str,
    via: str,
    matched_issue: str,
    audience: str,
    lang: str,
    needs_review: bool,
    note: str,
) -> Dict[str, Any]:
    return {
        "found": True,
        "mode": "sop_backed",
        "via": via,
        "confidence": confidence,
        "matched_issue": matched_issue,
        "title": answer.issue_type or answer.scenario,
        "summary": (answer.answer_summary or "").strip(),
        "steps": [str(s) for s in (answer.steps or [])][:7],
        "evidence_requested": [str(s) for s in (answer.evidence_requested or [])][:6],
        "do_not": [str(s) for s in (answer.do_not_decide_without_approval or [])][:5],
        "escalate_to": [str(s) for s in (answer.contacts or [])][:4],
        "sources": _sources(answer),
        "image_references": _image_refs(answer, lang),
        "raw_retrieved_chunks": _raw_source_chunks(answer),
        "needs_human_review": bool(needs_review or answer.needs_human_review),
        "audience": audience,
        "note": note,
    }


def _not_found(lang: str, audience: str) -> Dict[str, Any]:
    return {
        "found": False,
        "mode": "sop_backed",
        "via": "",
        "confidence": "none",
        "matched_issue": "",
        "title": "",
        "summary": "",
        "steps": [],
        "evidence_requested": [],
        "do_not": [],
        "escalate_to": [],
        "sources": [],
        "image_references": [],
        "raw_retrieved_chunks": [],
        "needs_human_review": True,
        "audience": audience,
        "note": _NOT_FOUND_NOTE["zh" if lang == "zh" else "en"],
    }


def compose_sop_match(
    question: str,
    context: Optional[Dict[str, Any]] = None,
    *,
    lang: str = "en",
    audience: str = "both",
    staff_access_token: Optional[str] = None,
    deterministic_answer: Optional[AgentAnswer] = None,
    scenario_hint: str = "",
    subtype_hint: str = "",
) -> Dict[str, Any]:
    """Compose a SOP-backed knowledge-base match for a (possibly messy) question.

    ``deterministic_answer`` is the answer ``/ask`` already produced (pass it to
    avoid re-computing). ``scenario_hint`` / ``subtype_hint`` are the optional,
    already-validated AI intent hints. The answer is always source-backed: it is
    re-derived through :func:`agent.answer_question`, never authored here.
    """
    from .agent import answer_question  # local import avoids a cycle at import time

    answer = deterministic_answer or answer_question(
        question, context, staff_access_token=staff_access_token
    )

    # 1) Deterministic answer is already specific → present it as a high/medium
    #    confidence match (a clean condensed knowledge-base view of the same SOP).
    if not sop_assist_recommended(answer):
        return _match_from_answer(
            answer,
            confidence=answer.confidence or "medium",
            via="deterministic",
            matched_issue=answer.smart_manikin_subissue or answer.scenario,
            audience=audience,
            lang=answer.language or lang,
            needs_review=False,
            note="",
        )

    lang = answer.language or lang

    # 2) Weak/unknown → find the closest existing route.
    route: Optional[_Route] = None
    via = ""

    # 2a) Prefer a validated AI intent hint when present (semantic paraphrases).
    if subtype_hint and subtype_hint in _SUBISSUE_ANCHORS:
        route = next((r for r in _routes() if r.subissue == subtype_hint), None)
        via = "ai_hint"
    if route is None and scenario_hint:
        cand = next(
            (r for r in _routes() if r.kind == "scenario" and r.scenario == scenario_hint),
            None,
        )
        if cand and not (audience == "student" and cand.audience == "staff"):
            route = cand
            via = "ai_hint"

    # 2b) Fall back to always-on lexical retrieval.
    if route is None:
        hit = retrieve_route(question, audience=audience)
        if hit is not None:
            route, _ = hit
            via = "retrieval"

    if route is None:
        return _not_found(lang, audience)

    # Re-derive the real SOP answer for the matched route via its anchor phrase.
    routed = answer_question(route.anchor, context, staff_access_token=staff_access_token)
    if not routed.steps:
        return _not_found(lang, audience)

    return _match_from_answer(
        routed,
        confidence="low",  # matched by paraphrase → always confirm with staff
        via=via,
        matched_issue=route.subissue or route.scenario,
        audience=audience,
        lang=lang,
        needs_review=True,
        note=_LOW_CONF_NOTE["zh" if lang == "zh" else "en"],
    )
