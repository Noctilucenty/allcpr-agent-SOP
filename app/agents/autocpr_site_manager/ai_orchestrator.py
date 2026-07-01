"""Optional AI orchestration layer for the Site Manager agent.

The deterministic SOP engine stays the ONLY source of truth. When enabled, an
AI layer may do two narrow, bounded things:

1. **Interpret** — normalize messy user language into a cleaner question and
   extract structured hints (scenario/subtype/urgency), constrained to labels
   that already exist in this repo. Unknown labels are dropped.
2. **Summarize** — rewrite the *already source-backed* answer into a short field
   summary. Its input is an allowlisted, secret-free subset of the answer; its
   output is scrubbed against real secret values as defense-in-depth.

The AI never invents SOP steps or policy, never sees or reveals passcodes / PINs
/ answer keys, never scores onboarding tests, and never makes an authorization
decision (refunds, reschedules, certificates, access) — those remain in the
deterministic endpoints. Every sensitive decision is unchanged whether AI is on
or off.

Disabled by default. If ``ALLCPR_AI_ENABLED`` is not truthy OR ``OPENAI_API_KEY``
is absent, every function is a no-op and the app behaves exactly as before. The
network call lives in a single function (``_complete``) that tests monkeypatch;
tests never hit a real API.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from .scenarios import SCENARIOS
from .schemas import AgentAnswer
from .sop_operational_refs import load_operational_ref_payload

# ---------------------------------------------------------------------------
# Config / feature flag
# ---------------------------------------------------------------------------
ENABLED_ENV = "ALLCPR_AI_ENABLED"
KEY_ENV = "OPENAI_API_KEY"
MODEL_ENV = "ALLCPR_AI_MODEL"
DEFAULT_MODEL = "gpt-4o-mini"
API_URL = "https://api.openai.com/v1/chat/completions"

# Labels the AI is allowed to choose from. Anything else is ignored.
ALLOWED_SCENARIOS = set(SCENARIOS)
ALLOWED_SUBTYPES = {
    # Smart Manikin sub-issues
    "ipad_pad_power_or_open", "bluetooth_connection", "training_no_data",
    "black_screen_app_restart", "completion_photo", "wrong_room_floor",
    # general sub-issues
    "passcode_needed", "code_failed", "wrong_course", "not_on_roster",
    "certificate_issue", "fix_failed",
}
ALLOWED_URGENCY = {"normal", "class_blocked", "safety_concern"}
ALLOWED_CONFIDENCE = {"low", "medium", "high"}

_TRUTHY = {"1", "true", "yes", "on"}


def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in _TRUTHY


def ai_enabled() -> bool:
    """AI runs only when explicitly enabled AND an API key is present."""
    return _truthy(os.environ.get(ENABLED_ENV)) and bool(os.environ.get(KEY_ENV))


def _model() -> str:
    return (os.environ.get(MODEL_ENV) or "").strip() or DEFAULT_MODEL


# ---------------------------------------------------------------------------
# Secret grounding — redact real passcode values out of any AI text.
# ---------------------------------------------------------------------------
_SECRET_CACHE: Optional[List[str]] = None
REDACTED = "[redacted]"


def sensitive_values() -> List[str]:
    """Real secret values (room/gate/lockbox codes, Wi-Fi creds, internal links)
    pulled straight from the reviewed source. Used to scrub AI output so a model
    can never surface a real passcode — even one it hallucinated verbatim."""
    global _SECRET_CACHE
    if _SECRET_CACHE is not None:
        return _SECRET_CACHE
    values: List[str] = []
    try:
        for ref in load_operational_ref_payload():
            for item in ref.get("items", []) or []:
                if str(item.get("sensitivity", "")).strip().lower() == "internal":
                    val = str(item.get("value", "")).strip()
                    if len(val) >= 3:
                        values.append(val)
    except Exception:
        values = []
    # longest first so substrings don't leave fragments behind
    _SECRET_CACHE = sorted(set(values), key=len, reverse=True)
    return _SECRET_CACHE


def redact_text(text: Any) -> Any:
    if not isinstance(text, str) or not text:
        return text
    out = text
    for secret in sensitive_values():
        if secret and secret in out:
            out = out.replace(secret, REDACTED)
    return out


def _scrub(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _scrub(v) for k, v in value.items()}
    return value


def _clean_str(value: Any, limit: int = 600) -> str:
    return redact_text(str(value or "").strip())[:limit]


# ---------------------------------------------------------------------------
# Network boundary — the ONLY place that calls the API. Monkeypatched in tests.
# ---------------------------------------------------------------------------
INTENT_TAG = "site-ops intent normalizer"
SUMMARY_TAG = "site-ops answer summarizer"


def _complete(system: str, user: str) -> str:
    """POST a chat completion and return the raw assistant text (JSON string).

    Raises on any error; callers catch and fall back to deterministic behavior.
    The API key is read from the environment and never logged or returned.
    """
    import urllib.request

    key = os.environ[KEY_ENV]
    body = json.dumps({
        "model": _model(),
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=12) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def _safe_json(text: str) -> Optional[dict]:
    try:
        obj = json.loads(text)
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


# ---------------------------------------------------------------------------
# Stage 1: intent normalization
# ---------------------------------------------------------------------------
_INTENT_SYSTEM = (
    "You are the " + INTENT_TAG + " for an internal site-operations SOP assistant. "
    "You do NOT answer questions and NEVER invent SOP steps, policy, passcodes, or "
    "PINs. Read the user's messy message and return ONLY a compact JSON object with "
    "keys: normalized_question, scenario_hint, subtype_hint, urgency, site_hint, "
    "class_time_hint, missing_fields, suggested_clarifying_question, confidence. "
    "scenario_hint MUST be one of this exact list or \"\": " + ", ".join(sorted(ALLOWED_SCENARIOS)) + ". "
    "subtype_hint MUST be one of this exact list or \"\": " + ", ".join(sorted(ALLOWED_SUBTYPES)) + ". "
    "urgency is one of normal|class_blocked|safety_concern. confidence is one of "
    "low|medium|high. missing_fields is a short list of missing facts. If unsure, "
    "leave a field empty. Never output any passcode, code, or secret."
)


def _intent_user(question: str, context: Optional[Dict[str, Any]]) -> str:
    ctx = context or {}
    return json.dumps({
        "message": str(question or "")[:1200],
        "known_site": ctx.get("site") or ctx.get("location") or "",
        "known_class_time": ctx.get("class_time") or "",
    }, ensure_ascii=False)


def refine_intent(question: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Best-effort structured intent. Returns None if AI is off or anything fails.
    Output is validated against the allowed label sets; unknown labels are dropped."""
    if not ai_enabled():
        return None
    try:
        raw = _complete(_INTENT_SYSTEM, _intent_user(question, context))
    except Exception:
        return None
    obj = _safe_json(raw)
    if obj is None:
        return None
    return _sanitize_intent(obj, fallback_question=str(question or ""))


def _sanitize_intent(obj: Dict[str, Any], *, fallback_question: str) -> Dict[str, Any]:
    scenario_hint = str(obj.get("scenario_hint") or "").strip()
    if scenario_hint not in ALLOWED_SCENARIOS:
        scenario_hint = ""
    subtype_hint = str(obj.get("subtype_hint") or "").strip()
    if subtype_hint not in ALLOWED_SUBTYPES:
        subtype_hint = ""
    urgency = str(obj.get("urgency") or "").strip()
    if urgency not in ALLOWED_URGENCY:
        urgency = "normal"
    confidence = str(obj.get("confidence") or "").strip()
    if confidence not in ALLOWED_CONFIDENCE:
        confidence = "low"
    normalized = str(obj.get("normalized_question") or "").strip() or fallback_question
    missing = [str(x)[:40] for x in (obj.get("missing_fields") or [])][:6]
    return {
        "normalized_question": _clean_str(normalized, 600),
        "scenario_hint": scenario_hint,
        "subtype_hint": subtype_hint,
        "urgency": urgency,
        "site_hint": _clean_str(obj.get("site_hint"), 120),
        "class_time_hint": _clean_str(obj.get("class_time_hint"), 60),
        "missing_fields": missing,
        "suggested_clarifying_question": _clean_str(obj.get("suggested_clarifying_question"), 200),
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Stage 2: safe summarizer
# ---------------------------------------------------------------------------
_SUMMARY_SYSTEM = (
    "You are the " + SUMMARY_TAG + " for an internal site-operations SOP assistant. "
    "You are given an already source-backed answer as JSON. Rewrite it into a "
    "short, plain field summary. Use ONLY the facts provided — do NOT add steps, "
    "policy, contacts, or any passcode/code. Do NOT approve refunds, reschedules, "
    "certificates, or access. Return ONLY JSON with keys: short_title, "
    "plain_summary, top_3_steps (<=3 short strings drawn from the given steps), "
    "clarifying_question (\"\" if none). Keep it calm and concise."
)

_SAFE_PHOTO_HINT = "If it is safe and does not interfere"


def _summary_input(answer: AgentAnswer) -> Dict[str, Any]:
    """An allowlisted, secret-free view of the answer. Operational references,
    the raw answer text, and image paths are deliberately excluded so the model
    can never receive a passcode."""
    steps = (answer.steps or answer.next_actions or answer.immediate_safety_check or [])[:6]
    locked_passcode = (
        answer.passcode_ref_available and not answer.staff_access_unlocked
    )
    return {
        "scenario": answer.scenario,
        "issue_type": answer.issue_type,
        "severity": answer.severity or "info",
        "needs_human_review": answer.needs_human_review,
        "steps": list(steps),
        "evidence": [e for e in answer.evidence_requested if _SAFE_PHOTO_HINT not in e][:6],
        "escalate_to": list(answer.contacts[:4]),
        "do_not": list(answer.do_not_decide_without_approval[:5]),
        "source_labels": list(answer.source_status[:5]),
        "language": answer.language,
        # a NOTE that a passcode is locked — never the value itself
        "passcode_locked_note": bool(locked_passcode),
    }


def summarize_answer(answer: AgentAnswer) -> Optional[Dict[str, Any]]:
    """Best-effort short summary of a source-backed answer. Returns None if AI is
    off or anything fails. Input is secret-free; output is scrubbed again."""
    if not ai_enabled():
        return None
    payload = _scrub(_summary_input(answer))
    try:
        raw = _complete(_SUMMARY_SYSTEM, json.dumps(payload, ensure_ascii=False))
    except Exception:
        return None
    obj = _safe_json(raw)
    if obj is None:
        return None
    out = {
        "short_title": _clean_str(obj.get("short_title"), 80),
        "plain_summary": _clean_str(obj.get("plain_summary"), 600),
        "top_3_steps": [_clean_str(s, 240) for s in (obj.get("top_3_steps") or []) if str(s).strip()][:3],
        "clarifying_question": _clean_str(obj.get("clarifying_question"), 200),
    }
    return _scrub(out)


# ---------------------------------------------------------------------------
# Orchestration entry point
# ---------------------------------------------------------------------------
def _stage(used_intent: bool, used_summary: bool) -> str:
    if used_intent and used_summary:
        return "both"
    if used_intent:
        return "intent"
    if used_summary:
        return "summary"
    return ""


def answer_with_orchestration(
    question: str,
    context: Optional[Dict[str, Any]] = None,
    *,
    staff_access_token: Optional[str] = None,
) -> AgentAnswer:
    """Deterministic-first answer with an optional AI interpret/summarize layer.

    Always returns a valid ``AgentAnswer``. The AI is best-effort: any failure
    (disabled, no key, network error, bad JSON) falls back to the exact
    deterministic answer. Sensitive decisions never pass through the AI.
    """
    # Local import avoids an import cycle with agent.py.
    from .agent import answer_question

    intent = refine_intent(question, context) if ai_enabled() else None
    used_intent = intent is not None

    # The deterministic classifier remains authoritative — the AI only supplies a
    # cleaner phrasing of the user's own words as its input.
    routed_question = question
    if intent and intent.get("normalized_question"):
        routed_question = intent["normalized_question"]

    answer = answer_question(routed_question, context, staff_access_token=staff_access_token)

    if intent:
        answer.ai_scenario_hint = intent.get("scenario_hint", "")
        answer.ai_subtype_hint = intent.get("subtype_hint", "")
        answer.ai_confidence = intent.get("confidence", "")
        answer.ai_clarifying_question = intent.get("suggested_clarifying_question", "")

    summary = summarize_answer(answer) if ai_enabled() else None
    used_summary = summary is not None
    if summary:
        answer.ai_short_title = summary.get("short_title", "")
        answer.ai_summary = summary.get("plain_summary", "")
        answer.ai_top_steps = summary.get("top_3_steps", [])
        if summary.get("clarifying_question"):
            answer.ai_clarifying_question = summary["clarifying_question"]

    answer.ai_used = used_intent or used_summary
    answer.ai_stage = _stage(used_intent, used_summary)

    # Defense-in-depth: scrub every AI-authored field against real secrets.
    answer.ai_short_title = redact_text(answer.ai_short_title)
    answer.ai_summary = redact_text(answer.ai_summary)
    answer.ai_top_steps = [redact_text(s) for s in answer.ai_top_steps]
    answer.ai_clarifying_question = redact_text(answer.ai_clarifying_question)
    return answer
