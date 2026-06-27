"""AutoCPR Site Management Specialist agent (MVP).

Deterministic, dependency-light agent that answers internal site-management /
site-opening questions from the in-repo SOP/KB and the maps-scraper-intel data
engine. No LLM, no paid APIs, no secrets. See ``README.md`` for the full design.

Public entry point::

    from app.agents.autocpr_site_manager import answer_question
    ans = answer_question("Smart Manikin black screen", context=None)
"""
from __future__ import annotations

from .agent import SiteManagerAgent, answer_question, get_agent
from .schemas import AgentAnswer, AgentAskRequest, RetrievedChunk

__all__ = [
    "SiteManagerAgent",
    "answer_question",
    "get_agent",
    "AgentAnswer",
    "AgentAskRequest",
    "RetrievedChunk",
]
