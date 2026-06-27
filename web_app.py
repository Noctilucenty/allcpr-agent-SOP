"""Standalone AllCPR Site Operations Agent web app.

This app is intentionally separate from maps-scraper-intel. It serves the
AllCPR-branded site-operations UI at both ``/`` and ``/agent`` and exposes the
deterministic local agent endpoint. No paid APIs, no secrets, no dashboard.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.agents.autocpr_site_manager import answer_question
from app.agents.autocpr_site_manager.schemas import AgentAnswer, AgentAskRequest

ROOT = Path(__file__).resolve().parent
SITE_OPS_AGENT_HTML = ROOT / "app" / "web" / "site_ops_agent.html"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

app = FastAPI(title="AllCPR Site Operations Agent")


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
    return answer_question(req.question, req.context)


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    return _agent_page()


@app.get("/agent", response_class=HTMLResponse)
def site_ops_agent_page() -> HTMLResponse:
    return _agent_page()
