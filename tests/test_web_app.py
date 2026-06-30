"""Tests for the standalone AllCPR agent web app."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import web_app


@pytest.fixture(autouse=True)
def isolated_incident_log(monkeypatch, tmp_path):
    monkeypatch.setenv("ALLCPR_INCIDENT_LOG_PATH", str(tmp_path / "incident_logs.jsonl"))


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
        assert "/static/ALLCPR.webp" in body
        assert 'id="q"' in body
        assert "Site details / optional context" in body
        assert "SOP source images" in body
        assert "Internal SOP passcode" in body
        assert "iPad / PAD" in body
        assert "operational_references" in body
        assert ".opref" in body
        assert "Live site log" in body
        assert "log-list" in body
        assert "Power outage" in body
        assert "Smart Manikin issue" in body
        assert "/api/agents/autocpr-site-manager/ask" in body
        assert "/api/incident-logs" in body


def test_agent_api_returns_operational_references_for_matching_access_site():
    client = TestClient(web_app.app)
    resp = client.post(
        "/api/agents/autocpr-site-manager/ask",
        json={"question": "door locked, what is the room passcode?", "context": {"site": "Santa Clara", "lang": "en"}},
    )
    assert resp.status_code == 200
    payload = resp.json()
    refs = payload["operational_references"]
    assert refs
    joined = " ".join(item["value"] for ref in refs for item in ref["items"])
    assert "2745" in joined
    assert payload["incident_log_id"]


def test_ask_endpoint_creates_incident_log_entry():
    client = TestClient(web_app.app)
    resp = client.post(
        "/api/agents/autocpr-site-manager/ask",
        json={
            "question": "The door is locked and I cannot access the room.",
            "context": {
                "site": "Santa Clara",
                "class_time": "2026-06-30 15:00",
                "browser_timestamp": "2026-06-30T22:30:00.000Z",
                "attachments": [{"type": "note", "description": "door keypad shows red light"}],
                "lang": "en",
            },
        },
    )
    assert resp.status_code == 200
    payload = resp.json()
    log_id = payload["incident_log_id"]
    assert log_id

    logs = client.get("/api/incident-logs?limit=10")
    assert logs.status_code == 200
    entries = logs.json()
    assert entries[0]["id"] == log_id
    assert entries[0]["site"] == "Santa Clara"
    assert entries[0]["class_time"] == "2026-06-30 15:00"
    assert entries[0]["question"] == "The door is locked and I cannot access the room."
    assert entries[0]["scenario"] == "venue_access_issue"
    assert entries[0]["severity"] == payload["severity"]
    assert entries[0]["needs_human_review"] is True
    assert entries[0]["status"] == "open"
    assert entries[0]["attachment_description"] == "door keypad shows red light"
    assert entries[0]["first_action"]
    assert entries[0]["operational_reference_titles"]
    assert entries[0]["access_refs_shown"] is True
    assert entries[0]["trusted_passcode_refs_shown"] is True


def test_incident_log_marks_no_passcode_when_source_not_matching_site():
    client = TestClient(web_app.app)
    resp = client.post(
        "/api/agents/autocpr-site-manager/ask",
        json={
            "question": "door locked, what is the passcode?",
            "context": {"site": "Palo Alto", "lang": "en"},
        },
    )
    assert resp.status_code == 200
    log = client.get("/api/incident-logs").json()[0]
    assert log["access_refs_shown"] is True
    assert log["trusted_passcode_refs_shown"] is False


def test_incident_log_get_and_patch_status_and_note():
    client = TestClient(web_app.app)
    created = client.post(
        "/api/incident-logs",
        json={"question": "Smart Manikin screen is black.", "context": {"site": "Newark", "lang": "en"}},
    )
    assert created.status_code == 200
    log_id = created.json()["id"]

    fetched = client.get(f"/api/incident-logs/{log_id}")
    assert fetched.status_code == 200
    assert fetched.json()["site"] == "Newark"

    patched = client.patch(
        f"/api/incident-logs/{log_id}",
        json={"status": "escalated", "note": "Called supervisor.", "created_by": "staff"},
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["status"] == "escalated"
    assert body["notes"][-1]["text"] == "Called supervisor."

    listed = client.get("/api/incident-logs").json()
    assert listed[0]["status"] == "escalated"
    assert listed[0]["notes"][-1]["text"] == "Called supervisor."


def test_invalid_log_status_rejected_safely():
    client = TestClient(web_app.app)
    created = client.post(
        "/api/incident-logs",
        json={"question": "Power outage.", "context": {"site": "Unknown site", "lang": "en"}},
    )
    log_id = created.json()["id"]
    bad = client.patch(f"/api/incident-logs/{log_id}", json={"status": "deleted"})
    assert bad.status_code == 400
    assert client.get(f"/api/incident-logs/{log_id}").json()["status"] == "open"


def test_incident_log_does_not_store_local_paths():
    client = TestClient(web_app.app)
    resp = client.post(
        "/api/agents/autocpr-site-manager/ask",
        json={
            "question": "door locked",
            "context": {
                "site": "/Users/noctilucenteasteliq/Desktop/Developer/allcpr_agent/SOP",
                "lang": "en",
            },
        },
    )
    assert resp.status_code == 200
    log = client.get("/api/incident-logs").json()[0]
    joined = str(log)
    assert "/Users/" not in joined
    assert "/Desktop/Developer/" not in joined
    assert "noctilucenteasteliq" not in joined


def test_static_sop_media_route_available_even_before_index():
    client = TestClient(web_app.app)
    resp = client.get("/static/sop_media/not-found.png")
    assert resp.status_code == 404


def test_allcpr_logo_static_route_available():
    client = TestClient(web_app.app)
    resp = client.get("/static/ALLCPR.webp")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/webp"
