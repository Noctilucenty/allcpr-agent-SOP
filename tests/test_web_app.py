"""Tests for the standalone AllCPR agent web app."""
from __future__ import annotations

from fastapi.testclient import TestClient

import web_app


def test_health_ok():
    client = TestClient(web_app.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["version"] == "v0.8b1"


def test_root_and_agent_serve_bilingual_ui():
    client = TestClient(web_app.app)
    for path in ("/", "/agent"):
        resp = client.get(path)
        assert resp.status_code == 200
        body = resp.text
        assert "English" in body
        assert "中文" in body
        assert "Get SOP Guidance" in body
        assert "Site Operations Assistant" in body
        assert 'id="q"' in body
        assert "Site details / optional context" in body
        assert "SOP source images" in body
        assert "Power outage" in body
        assert "Smart Manikin issue" in body
        assert "/api/agents/autocpr-site-manager/ask" in body


def test_static_sop_media_route_available_even_before_index():
    client = TestClient(web_app.app)
    resp = client.get("/static/sop_media/not-found.png")
    assert resp.status_code == 404
