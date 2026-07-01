"""Tests for the standalone AllCPR agent web app."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import web_app


@pytest.fixture(autouse=True)
def isolated_incident_log(monkeypatch, tmp_path):
    monkeypatch.setenv("ALLCPR_INCIDENT_LOG_PATH", str(tmp_path / "incident_logs.jsonl"))
    monkeypatch.setenv("ALLCPR_INSPECTION_LOG_PATH", str(tmp_path / "inspection_logs.jsonl"))
    monkeypatch.setenv(
        "ALLCPR_ONBOARDING_ATTEMPT_PATH", str(tmp_path / "onboarding_attempts.jsonl")
    )


def _completed_inspection_payload(**overrides):
    payload = {
        "site": "Santa Clara",
        "staff": "Alex",
        "started_at": "2026-06-30T09:00:00.000Z",
        "completed_at": "2026-06-30T09:30:00.000Z",
        "inspection_warning_acknowledged": True,
        "acknowledged_at": "2026-06-30T09:00:00.000Z",
        "before_photo_checks": {"whole_room": True, "smart_manikin": True, "supplies": True, "door": True},
        "site_checklist_items": [
            {"item": "hygiene", "status": "ok"},
            {"item": "camera", "status": "ok"},
        ],
        "post_photo_checks": {"whole_room": True, "smart_manikin": True},
        "weekly_report_completed": True,
        "upload_completed": True,
        "problems_found": [],
        "fixed_on_site_count": 0,
        "needs_support_count": 0,
        "language": "en",
    }
    payload.update(overrides)
    return payload


def test_inspection_log_create_and_acknowledgement_stored():
    client = TestClient(web_app.app)
    resp = client.post("/api/inspection-logs", json=_completed_inspection_payload())
    assert resp.status_code == 200
    entry = resp.json()
    assert entry["log_type"] == "inspection"
    assert entry["status"] == "completed"
    assert entry["inspection_warning_acknowledged"] is True
    assert entry["acknowledged_at"]
    assert entry["weekly_report_completed"] is True
    assert entry["upload_completed"] is True
    assert entry["before_photo_checks"]
    assert entry["post_photo_checks"]

    listed = client.get("/api/inspection-logs?limit=10").json()
    assert listed[0]["id"] == entry["id"]
    fetched = client.get(f"/api/inspection-logs/{entry['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["site"] == "Santa Clara"


def test_inspection_log_problem_marks_needs_support():
    client = TestClient(web_app.app)
    payload = _completed_inspection_payload(
        site_checklist_items=[
            {"item": "camera", "status": "problem", "issue": "camera offline", "needs_support": True},
        ],
        problems_found=["camera offline"],
        needs_support_count=1,
    )
    resp = client.post("/api/inspection-logs", json=payload)
    assert resp.status_code == 200
    entry = resp.json()
    assert entry["status"] == "needs_support"
    assert entry["needs_support_count"] == 1
    assert entry["problems_found"] == ["camera offline"]


def test_inspection_log_patch_status_and_note():
    client = TestClient(web_app.app)
    created = client.post("/api/inspection-logs", json=_completed_inspection_payload())
    log_id = created.json()["id"]
    patched = client.patch(
        f"/api/inspection-logs/{log_id}", json={"status": "needs_support", "note": "follow up camera"}
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "needs_support"
    assert patched.json()["notes"][-1]["text"] == "follow up camera"

    bad = client.patch(f"/api/inspection-logs/{log_id}", json={"status": "deleted"})
    assert bad.status_code == 400


def test_inspection_log_does_not_store_local_paths_or_images():
    client = TestClient(web_app.app)
    payload = _completed_inspection_payload(
        site="/Users/noctilucenteasteliq/Desktop/Developer/allcpr_agent/SOP",
        notes="photo saved at /Users/noctilucenteasteliq/Pictures/img.png",
    )
    client.post("/api/inspection-logs", json=payload)
    log = client.get("/api/inspection-logs").json()[0]
    blob = str(log)
    assert "/Users/" not in blob
    assert "noctilucenteasteliq" not in blob


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
        assert "Training no data" in body
        assert "Fix failed" in body
        assert "operational_references" in body
        assert ".opref" in body
        assert "Live site log" in body
        assert "log-list" in body
        assert "Power outage" in body
        assert "Smart Manikin issue" in body
        assert "/api/agents/autocpr-site-manager/ask" in body
        assert "/api/incident-logs" in body


def test_ui_has_staff_access_unlock_controls():
    client = TestClient(web_app.app)
    body = client.get("/agent").text
    # Staff-access control, PIN form, and bilingual copy keys present.
    assert 'id="staff-access"' in body
    assert 'id="sa-toggle"' in body
    assert 'id="sa-pin"' in body
    assert "/api/staff-access/unlock" in body
    assert "sessionStorage" in body
    assert "localStorage" not in body  # token must not be stored in localStorage
    for label in ("staffAccess:", "staffUnlockBtn:", "staffPinLabel:", "staffUnlocked:", "staffPinInvalid:"):
        assert body.count(label) >= 2  # en + zh


def test_ui_has_guided_inspection_workflow():
    client = TestClient(web_app.app)
    body = client.get("/agent").text
    # Entry point + bilingual label
    assert 'id="start-inspection"' in body
    assert "Start Inspection" in body
    assert "开始巡检" in body
    # Acknowledgement modal exists and gates the flow (flow hidden until ack)
    assert 'id="insp-ack"' in body
    assert 'id="insp-flow" hidden' in body
    assert "Important inspection reminder" in body
    assert "巡检前重要提醒" in body
    assert "I understand" in body and "我已知晓" in body
    # Acknowledgement reminder must NOT contain fine/penalty wording (en + zh)
    for banned in ("fine", "penalty", "罚款", "扣款"):
        assert banned not in body
    # Before / site checklist / after / report / upload / do-not sections present
    assert "inspBeforeItems:" in body
    assert "inspAfterItems:" in body
    assert "inspUploadItems:" in body
    assert "inspReportItems:" in body
    assert "inspDoNotItems:" in body
    # Site checklist covers the full SOP item set
    for item in ("Hygiene", "Trash", "Disinfect", "power cables", "Camera online", "Wi-Fi normal", "Signage", "safety hazards"):
        assert item in body
    # Do-not-repair warning present
    assert "Do not dismantle or repair Smart Manikin" in body
    # Inspection decision chips present
    for chip in ("ciFrequency:", "ciBefore:", "ciChecklist:", "ciUpload:", "ciDoNot:", "ciStart:"):
        assert body.count(chip) >= 2  # en + zh
    # Inspection log endpoint wired in the page
    assert "/api/inspection-logs" in body
    assert "inspection_warning_acknowledged" in body


def test_inspection_reference_endpoint_returns_placement_diagram():
    client = TestClient(web_app.app)
    resp = client.get("/api/inspection-reference")
    assert resp.status_code == 200
    items = resp.json()
    # Only asserts when the media index/diagram is present in this checkout.
    if items:
        assert any("equipment placement diagram" in (i.get("title") or "") for i in items)
        for i in items:
            assert i["url"].startswith("/static/sop_media/")
            assert "/Users/" not in i.get("source_file", "")


def test_ui_guided_inspection_shows_reference_image():
    client = TestClient(web_app.app)
    body = client.get("/agent").text
    assert 'id="insp-reference"' in body
    assert "/api/inspection-reference" in body
    assert "loadInspectionReference" in body
    assert body.count("inspReference:") >= 2  # en + zh


def test_ui_decision_tree_default_routing_keys_are_defined():
    """The sub-issue default-open map must reference real pill keys and labels,
    so a routed narrow query opens an existing panel (no undefined keys)."""
    client = TestClient(web_app.app)
    body = client.get("/agent").text
    assert "SUB_DEFAULT" in body
    assert "issue_subtype" in body
    # every panel key the router can default-open must exist as a pill key
    for key in ("passcode", "venue", "access", "classmatch", "incident"):
        assert f"key:'{key}'" in body
    # and the copy labels those pills depend on must be defined (en + zh)
    for label in ("aPasscode:", "aClassMismatch:", "aVenue:", "aAccess:", "aIncident:"):
        assert body.count(label) >= 2


def test_agent_api_redacts_passcode_by_default():
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
    assert "2745" not in joined
    assert "Restricted internal passcode" in joined
    assert payload["passcode_ref_available"] is True
    assert payload["passcode_revealed"] is False
    assert payload["staff_access_unlocked"] is False
    assert payload["incident_log_id"]


def test_staff_unlock_then_reveal_passcode_via_api(monkeypatch):
    monkeypatch.setenv("ALLCPR_STAFF_ACCESS_PIN", "1234")
    client = TestClient(web_app.app)

    bad = client.post("/api/staff-access/unlock", json={"pin": "0000"})
    assert bad.status_code == 401

    unlock = client.post("/api/staff-access/unlock", json={"pin": "1234"})
    assert unlock.status_code == 200
    token = unlock.json()["token"]
    assert token and token != "1234"

    resp = client.post(
        "/api/agents/autocpr-site-manager/ask",
        json={
            "question": "door locked, what is the room passcode?",
            "context": {"site": "Santa Clara", "lang": "en"},
            "staff_access_token": token,
        },
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["staff_access_unlocked"] is True
    assert payload["passcode_revealed"] is True
    joined = " ".join(item["value"] for ref in payload["operational_references"] for item in ref["items"])
    assert "2745" in joined


def test_logs_never_store_raw_passcodes_even_when_unlocked(monkeypatch):
    monkeypatch.setenv("ALLCPR_STAFF_ACCESS_PIN", "1234")
    client = TestClient(web_app.app)
    token = client.post("/api/staff-access/unlock", json={"pin": "1234"}).json()["token"]
    client.post(
        "/api/agents/autocpr-site-manager/ask",
        json={
            "question": "door locked, what is the room passcode?",
            "context": {"site": "Santa Clara", "lang": "en"},
            "staff_access_token": token,
        },
    )
    log = client.get("/api/incident-logs").json()[0]
    blob = str(log)
    # No raw codes / Wi-Fi password anywhere in the persisted log entry.
    for secret in ("2745", "224466", "6285", "DoBeUSA", "DoBesince2016"):
        assert secret not in blob
    assert log["passcode_revealed"] is True
    assert log["staff_access_unlocked"] is True


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


def test_smart_manikin_log_stores_subissue_and_fix_failed_path():
    client = TestClient(web_app.app)
    resp = client.post(
        "/api/agents/autocpr-site-manager/ask",
        json={
            "question": "Bluetooth fix did not work",
            "context": {"site": "Santa Clara", "lang": "en"},
        },
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["smart_manikin_subissue"] == "documented_fix_failed"
    assert payload["documented_fix_failed_requested"] is True

    log = client.get("/api/incident-logs").json()[0]
    assert log["smart_manikin_subissue"] == "documented_fix_failed"
    assert log["documented_fix_failed_requested"] is True
    assert "engineer/vendor" in log["smart_manikin_escalation_targets"]
    assert "supervisor" in log["smart_manikin_escalation_targets"]


def test_smart_manikin_log_stores_ipad_subissue_without_documented_fix():
    client = TestClient(web_app.app)
    resp = client.post(
        "/api/agents/autocpr-site-manager/ask",
        json={"question": "ipad打不开", "context": {"lang": "en"}},
    )
    assert resp.status_code == 200
    log = client.get("/api/incident-logs").json()[0]
    assert log["smart_manikin_subissue"] == "ipad_pad_power_or_open"
    assert log["documented_fix_available"] is False
    assert log["documented_fix_failed_requested"] is False


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


def _passing_answers(**overrides):
    """A correct answer key, with optional per-question overrides for failures."""
    from app.agents.autocpr_site_manager.onboarding_quiz import ONBOARDING_QUESTIONS

    answers = {q["id"]: q["correct_answer"] for q in ONBOARDING_QUESTIONS}
    answers.update(overrides)
    return answers


def test_onboarding_quiz_endpoint_returns_20_questions_without_answer_key():
    client = TestClient(web_app.app)
    resp = client.get("/api/onboarding-quiz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 20
    assert data["passing_score"] == 16
    assert len(data["questions"]) == 20
    for q in data["questions"]:
        assert "correct_answer" not in q  # answer key must not leak to the browser
        assert "explanation_en" not in q
        assert q["prompt_en"] and q["prompt_zh"]
        assert q["options_en"] and q["options_zh"]


def test_onboarding_attempt_create_and_list():
    client = TestClient(web_app.app)
    resp = client.post(
        "/api/onboarding-attempts",
        json={"staff": "Alex", "site": "Santa Clara", "language": "en", "answers": _passing_answers()},
    )
    assert resp.status_code == 200
    entry = resp.json()
    assert entry["log_type"] == "onboarding_attempt"
    assert entry["score"] == 20
    assert entry["total"] == 20
    assert entry["passing_score"] == 16
    assert entry["passed"] is True
    assert entry["status"] == "passed"
    assert entry["critical_misses"] == []
    assert entry["staff"] == "Alex"
    assert entry["site"] == "Santa Clara"
    assert entry["created_at"]

    listed = client.get("/api/onboarding-attempts?limit=10").json()
    assert listed[0]["id"] == entry["id"]
    assert listed[0]["staff"] == "Alex"


def test_onboarding_attempt_below_threshold_fails_by_score():
    client = TestClient(web_app.app)
    # miss 5 non-critical questions -> 15/20, no critical misses
    wrong = {"q1": "Z", "q3": "Z", "q5": "Z", "q6": "Z", "q7": "Z"}
    resp = client.post(
        "/api/onboarding-attempts",
        json={"staff": "Sam", "language": "en", "answers": _passing_answers(**wrong)},
    )
    entry = resp.json()
    assert entry["score"] == 15
    assert entry["passed"] is False
    assert entry["status"] == "failed_score"
    assert entry["critical_misses"] == []


def test_onboarding_attempt_critical_miss_auto_fails_via_api():
    client = TestClient(web_app.app)
    # 19 correct but miss q2 (critical: before photos before cleaning)
    resp = client.post(
        "/api/onboarding-attempts",
        json={"staff": "Robin", "language": "en", "answers": _passing_answers(q2="A")},
    )
    entry = resp.json()
    assert entry["score"] == 19
    assert entry["passed"] is False
    assert entry["status"] == "failed_critical"
    assert entry["critical_misses"][0]["id"] == "q2"
    assert entry["critical_misses"][0]["concept"]


def test_onboarding_attempt_server_ignores_client_supplied_score():
    client = TestClient(web_app.app)
    resp = client.post(
        "/api/onboarding-attempts",
        json={"staff": "Cheater", "language": "en", "answers": {}, "score": 20, "passed": True},
    )
    entry = resp.json()
    assert entry["score"] == 0            # recomputed, not trusted
    assert entry["passed"] is False


def test_onboarding_attempt_does_not_store_local_paths_or_private_usernames():
    client = TestClient(web_app.app)
    client.post(
        "/api/onboarding-attempts",
        json={
            "staff": "/Users/noctilucenteasteliq/Desktop/Developer/allcpr_agent",
            "site": "/Users/noctilucenteasteliq/sites/sc",
            "language": "en",
            "answers": _passing_answers(),
        },
    )
    log = client.get("/api/onboarding-attempts").json()[0]
    blob = str(log)
    assert "/Users/" not in blob
    assert "noctilucenteasteliq" not in blob
    assert "/Desktop/Developer/" not in blob


def test_ui_has_onboarding_test_workflow():
    client = TestClient(web_app.app)
    body = client.get("/agent").text
    # Entry point near Start Inspection + bilingual label
    assert 'id="start-onboarding"' in body
    assert "Onboarding Test" in body
    assert "入职测试" in body
    # Modal exists
    assert 'id="onb-overlay"' in body
    assert 'id="onb-questions"' in body
    # Quiz + attempt endpoints wired in the page
    assert "/api/onboarding-quiz" in body
    assert "/api/onboarding-attempts" in body
    # Result / critical-miss copy present (en + zh keys)
    assert "Failed due to critical miss" in body
    assert body.count("onboardingCriticalMisses:") >= 2
    assert body.count("onboardingPassed:") >= 2
    assert "16/20" in body
    # Must not use fine / penalty / scary wording (en + zh), like the inspection copy
    for banned in ("fine", "penalty", "罚款", "扣款"):
        assert banned not in body


def test_static_sop_media_route_available_even_before_index():
    client = TestClient(web_app.app)
    resp = client.get("/static/sop_media/not-found.png")
    assert resp.status_code == 404


def test_allcpr_logo_static_route_available():
    client = TestClient(web_app.app)
    resp = client.get("/static/ALLCPR.webp")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/webp"
