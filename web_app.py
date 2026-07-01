"""Standalone AllCPR Site Operations Agent web app.

This app is intentionally separate from maps-scraper-intel. It serves the
AllCPR-branded site-operations UI at both ``/`` and ``/agent`` and exposes the
deterministic local agent endpoint. No paid APIs, no secrets, no dashboard.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.agents.autocpr_site_manager import answer_question
from app.agents.autocpr_site_manager.ai_orchestrator import (
    ai_enabled,
    ai_summary_payload,
    status_line as ai_status_line,
)
from app.agents.autocpr_site_manager.incident_logs import (
    append_answer_log,
    get_log,
    list_logs,
    patch_ai_metadata,
    patch_log,
)
from app.agents.autocpr_site_manager.inspection_logs import (
    append_inspection_entry,
    get_inspection_log,
    list_inspection_logs,
    patch_inspection_log,
)
from app.agents.autocpr_site_manager.onboarding_attempts import (
    append_onboarding_attempt,
    list_onboarding_attempts,
)
from app.agents.autocpr_site_manager.onboarding_quiz import (
    PASSING_SCORE,
    TOTAL_QUESTIONS,
    public_questions,
)
from app.agents.autocpr_site_manager.student_checks import (
    append_student_check,
    list_student_checks,
)
from app.agents.autocpr_site_manager import staff_access
from app.agents.autocpr_site_manager.schemas import (
    AgentAnswer,
    AgentAskRequest,
    IncidentLogPatch,
    InspectionLogPatch,
    InspectionLogRequest,
    OnboardingAttemptRequest,
    StaffAccessUnlockRequest,
    StudentSiteCheckRequest,
)
from app.agents.autocpr_site_manager.sop_media_index import MEDIA_ROOT

ROOT = Path(__file__).resolve().parent
SITE_OPS_AGENT_HTML = ROOT / "app" / "web" / "site_ops_agent.html"
STATIC_ROOT = ROOT / "app" / "web" / "static"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

@asynccontextmanager
async def _lifespan(_app: "FastAPI"):
    # One secret-free line so Render logs show which mode/model the app booted in.
    print(ai_status_line(), flush=True)
    yield


app = FastAPI(title="AllCPR Site Operations Agent", lifespan=_lifespan)
STATIC_ROOT.mkdir(parents=True, exist_ok=True)
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/static/sop_media", StaticFiles(directory=str(MEDIA_ROOT)), name="sop_media")
app.mount("/static", StaticFiles(directory=str(STATIC_ROOT)), name="static")


def _agent_page() -> HTMLResponse:
    if not SITE_OPS_AGENT_HTML.exists():
        return HTMLResponse(
            "<h1>Agent UI missing</h1>"
            f"<p>Expected {SITE_OPS_AGENT_HTML}</p>",
            status_code=500,
        )
    return HTMLResponse(SITE_OPS_AGENT_HTML.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "product": "AllCPR Site Operations Agent",
        "version": VERSION,
    }


@app.post("/api/staff-access/unlock")
def api_staff_access_unlock(req: StaffAccessUnlockRequest) -> dict:
    """Exchange a valid staff PIN for a short-lived signed access token.

    The PIN is never stored or logged; on success an HMAC-signed token (not the
    PIN) is returned for the frontend to keep in sessionStorage for the session.
    """
    if not staff_access.staff_access_configured():
        raise HTTPException(status_code=503, detail="staff access not configured")
    if not staff_access.verify_pin(req.pin):
        raise HTTPException(status_code=401, detail="invalid staff PIN")
    return {"ok": True, "token": staff_access.issue_token()}


@app.post("/api/agents/autocpr-site-manager/ask", response_model=AgentAnswer)
def api_agent_site_manager_ask(req: AgentAskRequest) -> AgentAnswer:
    # Fast path: return the deterministic, source-backed answer immediately so the
    # UI can render instructions without waiting on the AI. When AI is enabled,
    # ``ai_pending`` tells the client to fetch the summary separately (it "pops in"
    # on top when ready). AI never blocks or changes this answer.
    answer = answer_question(
        req.question, req.context, staff_access_token=req.staff_access_token
    )
    answer.ai_pending = ai_enabled()
    entry = append_answer_log(req.question, req.context, answer)
    answer.incident_log_id = str(entry.get("id", ""))
    return answer


@app.post("/api/agents/autocpr-site-manager/ai-summary")
def api_agent_site_manager_ai_summary(req: AgentAskRequest) -> dict:
    """Optional AI summary for a question already answered by ``/ask``.

    Runs the interpret/summarize layer and returns only the AI fields. Slower than
    ``/ask`` (it calls the model), so the client fetches it after rendering the
    deterministic answer. Returns ``ai_used: false`` if AI is off or the call
    fails — the client then keeps the instructions it already showed.
    """
    payload = ai_summary_payload(
        req.question, req.context, staff_access_token=req.staff_access_token
    )
    # Record the safe AI metadata onto the log entry created by /ask, if given.
    log_id = ""
    if isinstance(req.context, dict):
        log_id = str(req.context.get("incident_log_id") or "")
    if log_id and payload.get("ai_used"):
        patch_ai_metadata(log_id, payload)
    return payload


@app.post("/api/incident-logs")
def api_create_incident_log(req: AgentAskRequest) -> dict:
    answer = answer_question(req.question, req.context)
    return append_answer_log(req.question, req.context, answer)


@app.get("/api/incident-logs")
def api_list_incident_logs(limit: int = Query(default=50, ge=1, le=200)) -> list[dict]:
    return list_logs(limit)


@app.get("/api/incident-logs/{log_id}")
def api_get_incident_log(log_id: str) -> dict:
    entry = get_log(log_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="incident log not found")
    return entry


@app.patch("/api/incident-logs/{log_id}")
def api_patch_incident_log(log_id: str, patch: IncidentLogPatch) -> dict:
    try:
        entry = patch_log(
            log_id,
            status=patch.status,
            note=patch.note,
            assigned_to=patch.assigned_to,
            created_by=patch.created_by or "staff",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if entry is None:
        raise HTTPException(status_code=404, detail="incident log not found")
    return entry


@app.post("/api/inspection-logs")
def api_create_inspection_log(req: InspectionLogRequest) -> dict:
    payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    return append_inspection_entry(payload)


@app.get("/api/inspection-logs")
def api_list_inspection_logs(limit: int = Query(default=50, ge=1, le=200)) -> list[dict]:
    return list_inspection_logs(limit)


@app.post("/api/student-site-checks")
def api_create_student_check(req: StudentSiteCheckRequest) -> dict:
    """Save a lightweight quick class-readiness report (report-only, no staff
    duties). A safety concern is stored with a ``safety_escalation`` status."""
    payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    return append_student_check(payload)


@app.get("/api/student-site-checks")
def api_list_student_checks(limit: int = Query(default=50, ge=1, le=200)) -> list[dict]:
    return list_student_checks(limit)


@app.get("/api/inspection-reference")
def api_inspection_reference(lang: str = Query(default="en")) -> list[dict]:
    """Source-backed SOP media for the guided inspection flow (equipment placement
    diagram). Metadata only — no image analysis. Each item carries title, image
    path, source, use_for, related_steps, and a "reference only; do not repair or
    dismantle" caution."""
    from app.agents.autocpr_site_manager.sop_workflows import build_inspection_reference

    return build_inspection_reference("zh" if lang == "zh" else "en")


@app.get("/api/inspection-logs/{log_id}")
def api_get_inspection_log(log_id: str) -> dict:
    entry = get_inspection_log(log_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="inspection log not found")
    return entry


@app.patch("/api/inspection-logs/{log_id}")
def api_patch_inspection_log(log_id: str, patch: InspectionLogPatch) -> dict:
    try:
        entry = patch_inspection_log(
            log_id,
            status=patch.status,
            note=patch.note,
            created_by=patch.created_by or "staff",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if entry is None:
        raise HTTPException(status_code=404, detail="inspection log not found")
    return entry


@app.get("/api/onboarding-quiz")
def api_onboarding_quiz() -> dict:
    """Return the 20 onboarding questions for the browser — without the answer
    key. Scoring is server-side (POST /api/onboarding-attempts)."""
    return {
        "total": TOTAL_QUESTIONS,
        "passing_score": PASSING_SCORE,
        "questions": public_questions(),
    }


@app.post("/api/onboarding-attempts")
def api_create_onboarding_attempt(req: OnboardingAttemptRequest) -> dict:
    """Score a submitted attempt server-side and persist the result.

    The frontend never decides pass/fail — the score is recomputed from the
    answers in the storage layer, so a client-supplied score is ignored.
    """
    payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    return append_onboarding_attempt(payload)


@app.get("/api/onboarding-attempts")
def api_list_onboarding_attempts(
    limit: int = Query(default=50, ge=1, le=200),
    x_staff_access_token: str | None = Header(default=None),
) -> list[dict]:
    """Management review of onboarding results — gated behind staff access.

    Requires a valid staff token (from POST /api/staff-access/unlock) in the
    ``X-Staff-Access-Token`` header. Without it (or if staff access is not
    configured) nothing is returned. The response is a read-only summary: it
    omits the candidate's raw answer letters and never contained the answer key,
    passcodes, or the staff PIN.
    """
    if not staff_access.verify_token(x_staff_access_token):
        raise HTTPException(status_code=401, detail="staff access required")
    return [
        {k: v for k, v in attempt.items() if k != "answers"}
        for attempt in list_onboarding_attempts(limit)
    ]


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    return _agent_page()


@app.get("/agent", response_class=HTMLResponse)
def site_ops_agent_page() -> HTMLResponse:
    return _agent_page()
