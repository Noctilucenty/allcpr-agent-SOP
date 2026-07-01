"""Pydantic schemas for the AutoCPR Site Management Specialist agent.

Kept deliberately framework-light (plain fields + defaults) so they validate
identically under pydantic v1 or v2, matching whatever FastAPI pulls in.

The answer envelope now doubles as a structured **site-operations incident**
response: the original six fields (answer/scenario/confidence/sources/
needs_human_review/next_actions) are unchanged for backward compatibility, and
the new fields below are all optional with empty defaults, so existing callers
and tests keep working.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AgentAskRequest(BaseModel):
    """Request body for ``POST /api/agents/autocpr-site-manager/ask``.

    ``context`` is free-form but typically carries ``site``, ``class_time``,
    ``issue_time``, ``zip``, ``city``, ``course_type``, ``audience`` (default
    "internal"), ``stage``, and optionally ``attachments`` — a list of
    ``{"type", "description", "filename"}`` dicts describing photos/screenshots
    the user attached. The agent records attachment *descriptions* only; it does
    not analyze image content unless a real vision pipeline is wired in.
    """

    question: str
    context: Optional[Dict[str, Any]] = None
    # Optional short-lived staff token (from POST /api/staff-access/unlock). When
    # valid, source-backed internal passcodes are revealed for that response only.
    staff_access_token: Optional[str] = None


class StaffAccessUnlockRequest(BaseModel):
    """Request body for ``POST /api/staff-access/unlock``."""

    pin: str


class RetrievedChunk(BaseModel):
    """One KB chunk returned by the retriever, with its relevance score."""

    source: str
    text: str
    score: float


class SopMediaItem(BaseModel):
    """One local SOP image/media item matched to an answer.

    Metadata is deliberately conservative: it is derived from filenames, folder
    names, and source document names. The agent does not visually analyze images.
    """

    id: str
    source_file: str
    extracted_path: str
    url: str
    media_type: str = "image"
    title: str
    description: str
    tags: List[str] = []
    related_scenarios: List[str] = []


class OperationalReferenceItem(BaseModel):
    """One reviewed SOP-derived operational detail for staff use."""

    label: str
    value: str
    sensitivity: str = "normal"  # "normal" | "internal" | "source_needed"
    fact_type: Optional[str] = None


class OperationalReference(BaseModel):
    """A structured, source-backed operational reference matched to an answer."""

    id: str
    title: str
    scenario: str
    source_status: str
    priority: int = 0
    items: List[OperationalReferenceItem] = []
    media_tags: List[str] = []
    do_not: List[str] = []


class AgentAnswer(BaseModel):
    """Structured answer envelope returned by the agent and the endpoint.

    For site-operations incidents the structured fields are populated; for
    informational/site-intelligence questions most of them stay empty and the
    human-readable ``answer`` carries the response.
    """

    # --- original contract (unchanged) ---
    answer: str
    scenario: str
    confidence: str  # "high" | "medium" | "low"
    sources: List[str] = []
    needs_human_review: bool = False
    next_actions: List[str] = []
    language: str = "en"

    # --- structured site-operations incident fields (optional) ---
    issue_type: str = ""
    severity: str = ""  # "info" | "low" | "medium" | "high" | "critical"
    immediate_safety_check: List[str] = []
    steps: List[str] = []
    information_to_collect: List[str] = []
    evidence_requested: List[str] = []
    contacts: List[str] = []
    customer_communication: List[str] = []
    do_not_decide_without_approval: List[str] = []
    # Provenance labels, e.g. "official SOP source", "extracted SOP reference",
    # "Smart Manikin source", "general operations guidance, not official SOP",
    # "missing source".
    source_status: List[str] = []
    attachments_note: str = ""
    answer_summary: str = ""
    sop_images: List[SopMediaItem] = []
    operational_references: List[OperationalReference] = []
    incident_log_id: str = ""
    smart_manikin_subissue: str = ""
    documented_fix_available: bool = False
    documented_fix_failed_requested: bool = False
    # General (non-Smart-Manikin) sub-issue routing. ``issue_subtype`` is the
    # focused sub-issue slug (e.g. "passcode_needed", "wrong_course"),
    # ``route_detail`` is a short route category (e.g. "access", "checkin"), and
    # ``policy_approval_required`` flags sub-issues that need supervisor approval.
    issue_subtype: str = ""
    route_detail: str = ""
    policy_approval_required: bool = False
    # Staff-access / passcode redaction state for this response.
    # ``passcode_ref_available`` = a source-backed internal passcode matched;
    # ``passcode_revealed`` = it was actually shown (requires a valid staff token);
    # ``staff_access_unlocked`` = the request carried a valid staff token.
    staff_access_unlocked: bool = False
    passcode_ref_available: bool = False
    passcode_revealed: bool = False

    # --- optional AI orchestration layer (empty/false unless AI is enabled) ---
    # The AI only interprets messy language and summarizes the already
    # source-backed answer; it never changes any field above. ``ai_scenario_hint``
    # / ``ai_subtype_hint`` are validated against known labels; the summary fields
    # are scrubbed against real secret values.
    ai_used: bool = False
    ai_stage: str = ""  # "" | "intent" | "summary" | "both"
    ai_confidence: str = ""  # "" | "low" | "medium" | "high"
    ai_scenario_hint: str = ""
    ai_subtype_hint: str = ""
    ai_short_title: str = ""
    ai_summary: str = ""
    ai_top_steps: List[str] = []
    ai_clarifying_question: str = ""


class IncidentLogPatch(BaseModel):
    """Small mutable fields for a live incident log entry."""

    status: Optional[str] = None
    note: Optional[str] = None
    assigned_to: Optional[str] = None
    created_by: Optional[str] = None


class InspectionLogRequest(BaseModel):
    """A completed (or in-progress) Smart Manikin site inspection record.

    Stores checklist statuses and photo-step acknowledgements only — never raw
    image bytes, local file paths, or passcodes.
    """

    site: Optional[str] = None
    staff: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    inspection_warning_acknowledged: bool = False
    acknowledged_at: Optional[str] = None
    before_photo_checks: Any = None
    site_checklist_items: List[Dict[str, Any]] = []
    post_photo_checks: Any = None
    weekly_report_completed: bool = False
    upload_completed: bool = False
    problems_found: List[str] = []
    fixed_on_site_count: int = 0
    needs_support_count: int = 0
    status: Optional[str] = None
    notes: Optional[str] = None
    # Full-site-inspection extras: a compact Table/Station pre-check (what is
    # present on the Smart Manikin table) plus who/what mode ran the inspection.
    inspection_actor_type: Optional[str] = None
    inspection_mode: Optional[str] = None
    table_precheck: Any = None
    language: str = "en"


class InspectionLogPatch(BaseModel):
    """Small mutable fields for an inspection log entry."""

    status: Optional[str] = None
    note: Optional[str] = None
    created_by: Optional[str] = None


class StudentSiteCheckRequest(BaseModel):
    """A lightweight quick class-readiness report from a light user.

    Report-only: the user simply flags visible problems (access, room, station,
    iPad, manikin, supplies) before/during class. Carries no staff duties. Stores
    only these plain fields — never raw image bytes, local paths, passcodes, staff
    PINs, or answer keys.
    """

    site: Optional[str] = None
    class_time: Optional[str] = None
    name_optional: Optional[str] = None
    issue_categories: List[str] = []
    description: Optional[str] = None
    photo_taken: bool = False
    class_blocked: bool = False
    safety_concern: bool = False
    language: str = "en"


class OnboardingAttemptRequest(BaseModel):
    """A submitted Smart Manikin onboarding-test attempt.

    ``answers`` maps question id -> chosen option letter (e.g. ``{"q1": "B"}``).
    The server recomputes the score/pass-fail from the answers — any score-like
    field a client might send is ignored. Stores the result only; never raw image
    bytes, local file paths, passcodes, or staff PINs.
    """

    staff: Optional[str] = None
    site: Optional[str] = None
    language: str = "en"
    answers: Dict[str, Any] = {}
