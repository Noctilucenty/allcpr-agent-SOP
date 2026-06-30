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
