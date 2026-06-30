"""Standalone AllCPR Site Operations Agent web app.

This app is intentionally separate from maps-scraper-intel. It serves the
AllCPR-branded site-operations UI at both ``/`` and ``/agent`` and exposes the
deterministic local agent endpoint. No paid APIs, no secrets, no dashboard.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.agents.autocpr_site_manager import answer_question
from app.agents.autocpr_site_manager.incident_logs import (
    append_answer_log,
    get_log,
    list_logs,
    patch_log,
)
from app.agents.autocpr_site_manager.schemas import AgentAnswer, AgentAskRequest, IncidentLogPatch
from app.agents.autocpr_site_manager.sop_media_index import MEDIA_ROOT

ROOT = Path(__file__).resolve().parent
SITE_OPS_AGENT_HTML = ROOT / "app" / "web" / "site_ops_agent.html"
STATIC_ROOT = ROOT / "app" / "web" / "static"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

app = FastAPI(title="AllCPR Site Operations Agent")
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


@app.post("/api/agents/autocpr-site-manager/ask", response_model=AgentAnswer)
def api_agent_site_manager_ask(req: AgentAskRequest) -> AgentAnswer:
    answer = answer_question(req.question, req.context)
    entry = append_answer_log(req.question, req.context, answer)
    answer.incident_log_id = str(entry.get("id", ""))
    return answer


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


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    return _agent_page()


@app.get("/agent", response_class=HTMLResponse)
def site_ops_agent_page() -> HTMLResponse:
    return _agent_page()
