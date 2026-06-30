"""Tests for the 管点 agent behavior and the FastAPI endpoint."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import web_app
from app.agents.autocpr_site_manager import answer_question, prompts
from app.agents.autocpr_site_manager.sop_media_index import build_media_index
from app.agents.autocpr_site_manager.schemas import AgentAnswer

PKG_DIR = Path(__file__).resolve().parents[2] / "app" / "agents" / "autocpr_site_manager"


@pytest.fixture
def client():
    return TestClient(web_app.app)


# --- source/KB presence ------------------------------------------------------

@pytest.mark.parametrize("name", ["sop.md", "kb_seed.md", "sop_source_analysis.md"])
def test_kb_and_source_files_present(name):
    assert (PKG_DIR / name).is_file()


# --- response schema ---------------------------------------------------------

def test_answer_returns_valid_schema():
    ans = answer_question("how to use the dashboard?")
    assert isinstance(ans, AgentAnswer)
    assert ans.confidence in {"high", "medium", "low"}
    assert isinstance(ans.sources, list)
    assert isinstance(ans.next_actions, list)
    assert isinstance(ans.evidence_requested, list)
    assert isinstance(ans.source_status, list)
    assert ans.language in {"en", "zh"}
    assert isinstance(ans.sop_images, list)
    assert isinstance(ans.operational_references, list)
    assert isinstance(ans.answer_summary, str)
    assert ans.answer.strip()


def test_language_detection_english_question():
    ans = answer_question("What should I do if the power goes out?")
    assert ans.language == "en"
    assert ans.scenario == "electricity_outage"
    assert "Immediate safety check" in ans.answer
    assert "立即安全检查" not in ans.answer


def test_language_detection_chinese_question():
    ans = answer_question("停电了怎么办？")
    assert ans.language == "zh"
    assert ans.scenario == "electricity_outage"
    assert "立即安全检查" in ans.answer


def test_context_lang_forces_english_for_mixed_question():
    ans = answer_question("停电 power outage 怎么办？", {"lang": "en"})
    assert ans.language == "en"
    assert "Immediate safety check" in ans.answer
    assert "立即安全检查" not in ans.answer


def test_context_language_locale_force_chinese():
    ans = answer_question(
        "What should I do if the power goes out?",
        {"language": "zh-CN", "locale": "en-US"},
    )
    assert ans.language == "zh"
    assert "立即安全检查" in ans.answer


def test_context_locale_alias_forces_english():
    ans = answer_question("停电了怎么办？", {"locale": "en-US"})
    assert ans.language == "en"
    assert "Immediate safety check" in ans.answer


# --- electricity outage: the flagship incident response ----------------------

def test_electricity_outage_answer_structure():
    ans = answer_question("停电了怎么办？", {"site": "Santa Clara", "class_time": "09:00"})
    assert ans.scenario == "electricity_outage"
    assert ans.severity == "high"
    assert ans.needs_human_review is True
    # safety check present
    assert ans.immediate_safety_check
    # venue/site contact present
    assert any(("场地" in c) or ("物业" in c) or ("venue" in c.lower()) for c in ans.contacts)
    # evidence/photo request present, incl. the safe-photo wording
    assert ans.evidence_requested
    assert prompts.SAFE_PHOTO_NOTE in ans.evidence_requested
    # escalation + human review wording
    assert any("主管" in c for c in ans.contacts)
    assert prompts.HUMAN_REVIEW_REQUIRED in ans.answer
    # clearly labeled as general operations guidance, not official SOP
    assert prompts.SS_GENERAL in ans.source_status
    assert prompts.NEEDS_OFFICIAL_SOP in ans.source_status


def test_english_electricity_outage_answer_is_english_and_labeled():
    ans = answer_question("What should I do if the power goes out?")
    assert ans.language == "en"
    assert ans.scenario == "electricity_outage"
    assert "Immediate safety check" in ans.answer
    assert "general operations guidance, not official SOP" in ans.answer
    assert "Human review required" in ans.answer
    assert "upload/save photos or screenshots" in ans.answer
    assert "如果安全" not in ans.answer


def test_chinese_electricity_outage_answer_is_chinese_and_labeled():
    ans = answer_question("停电了怎么办？")
    assert ans.language == "zh"
    assert "立即安全检查" in ans.answer
    assert "非官方 SOP" in ans.answer
    assert "需人工复核" in ans.answer


@pytest.mark.parametrize(
    "question, scenario",
    [
        ("教室没网怎么办？", "internet_outage"),
        ("门打不开怎么办？", "venue_access_issue"),
        ("老师没到怎么办？", "instructor_no_show"),
        ("怎么写现场事件报告？", "incident_report"),
    ],
)
def test_incident_scenarios_request_evidence_and_review(question, scenario):
    ans = answer_question(question)
    assert ans.scenario == scenario
    assert ans.needs_human_review is True
    assert ans.evidence_requested  # every incident asks for evidence
    assert prompts.SAFE_PHOTO_NOTE in ans.evidence_requested


# --- safety: people before photos -------------------------------------------

def test_safety_emergency_prioritizes_people_over_photos():
    ans = answer_question("现场有人受伤了怎么办？")
    assert ans.scenario == "safety_or_emergency"
    assert ans.severity == "critical"
    assert ans.needs_human_review is True
    # must tell staff not to prioritize photos over safety, and mention 911
    joined = " ".join(ans.immediate_safety_check + ans.evidence_requested)
    assert "安全" in joined
    assert any("911" in c for c in ans.contacts)
    assert any("安全" in e for e in ans.evidence_requested)  # safety-gated evidence


# --- Smart Manikin: strictly source-grounded --------------------------------

def test_smart_manikin_is_source_grounded():
    ans = answer_question("Smart Manikin 黑屏，蓝牙连不上怎么办？")
    assert ans.scenario == "smart_manikin_troubleshooting"
    assert ans.needs_human_review is True
    assert prompts.SS_MANIKIN in ans.source_status
    assert prompts.NEEDS_VENDOR in ans.answer  # unknown root cause escalates
    low = ans.answer.lower()
    assert "bluetooth" in low or "蓝牙" in ans.answer
    # Fidelity: deterministic lead must not introduce unsupported device factors
    # or an invented black-screen fix.
    lead = prompts.lead_for("smart_manikin_troubleshooting").lower()
    for invented in ("browser", "permission", "wi-fi", "cellular"):
        assert invented not in lead
    assert "restart the attempt" not in low


def test_smart_manikin_black_screen_has_no_invented_fix():
    ans = answer_question("Smart Manikin app 自己重启 / black screen")
    # The source logs this but records no fix -> must escalate, not improvise.
    assert prompts.NEEDS_VENDOR in ans.answer
    assert "未记录" in ans.answer or "no fix" in ans.answer.lower()


def test_english_smart_manikin_black_screen_preserves_source_limits():
    ans = answer_question("The Smart Manikin screen is black. What should I do?")
    assert ans.language == "en"
    assert ans.scenario == "smart_manikin_troubleshooting"
    assert ans.smart_manikin_subissue == "black_screen_app_restart"
    low = ans.answer.lower()
    assert "needs engineer/vendor confirmation" in low
    assert "no documented fix" in low
    for unsupported in ("wi-fi", "wifi", "browser", "permission"):
        assert unsupported not in low
    assert "do not try undocumented reset" in low


@pytest.mark.parametrize(
    "question, subissue, fix_available",
    [
        ("ipad打不开", "ipad_pad_power_or_open", False),
        ("iPad won't turn on", "ipad_pad_power_or_open", False),
        ("PAD connected but TRAINING receives no data", "training_no_data", True),
        ("蓝牙连不上", "bluetooth_connection", True),
        ("黑屏", "black_screen_app_restart", False),
        ("完成照片怎么拍", "completion_photo", True),
        ("找不到房间", "wrong_room_floor", True),
    ],
)
def test_smart_manikin_subissue_detection(question, subissue, fix_available):
    ans = answer_question(question, {"lang": "en"})
    assert ans.scenario == "smart_manikin_troubleshooting"
    assert ans.smart_manikin_subissue == subissue
    assert ans.documented_fix_available is fix_available


def test_ipad_open_answer_is_focused_and_failure_aware():
    ans = answer_question("ipad打不开", {"lang": "en"})
    joined_steps = " ".join(ans.steps).lower()
    first_steps = " ".join(ans.steps[:3]).lower()
    assert ans.smart_manikin_subissue == "ipad_pad_power_or_open"
    assert "no documented ipad/pad open/power fix" in ans.answer.lower()
    assert "engineer/vendor" in ans.answer.lower()
    assert "photo/video" in joined_steps
    assert "completion photo" not in first_steps
    assert "wrong room" not in first_steps
    assert "all session done" not in first_steps
    assert "do not try undocumented reset" in ans.answer.lower()


def test_bluetooth_answer_mentions_source_backed_power_and_restart_then_escalates():
    ans = answer_question("Bluetooth won't connect", {"lang": "en"})
    low = ans.answer.lower()
    assert ans.smart_manikin_subissue == "bluetooth_connection"
    assert "power strip" in low
    assert "source-recorded manikin restart" in low
    assert "escalate to engineer/vendor" in low


def test_training_no_data_answer_is_specific():
    ans = answer_question("PAD connected but TRAINING receives no data", {"lang": "en"})
    low = ans.answer.lower()
    assert ans.smart_manikin_subissue == "training_no_data"
    assert "pad says connected" in low
    assert "training receives no data" in low
    assert "power strip" in low
    assert "engineer/vendor" in low


def test_completion_photo_answer_uses_source_email():
    ans = answer_question("How do I take the completion photo?", {"lang": "en"})
    low = ans.answer.lower()
    assert ans.smart_manikin_subissue == "completion_photo"
    assert "all session done / pass" in low
    assert "support@allcpr.org" in low
    assert "do not invent certificate" in low


def test_smart_manikin_fix_failed_prioritizes_escalation():
    ans = answer_question("Bluetooth fix did not work", {"lang": "en"})
    low = ans.answer.lower()
    assert ans.scenario == "smart_manikin_troubleshooting"
    assert ans.documented_fix_failed_requested is True
    assert ans.smart_manikin_subissue == "documented_fix_failed"
    assert ans.steps[0].startswith("Stop repeating")
    assert "escalate to engineer/vendor" in low
    assert "do not invent hardware-damage" in low
    ids = {ref.id for ref in ans.operational_references}
    assert "smart_manikin_fix_failed_escalation" in ids


def test_source_log_count_not_in_main_smart_steps():
    ans = answer_question("蓝牙连不上", {"lang": "en"})
    main = " ".join(ans.steps).lower()
    assert "source log count" not in main
    refs = " ".join(item.value for ref in ans.operational_references for item in ref.items)
    assert "4" in refs


def test_smart_manikin_question_returns_sop_image_when_media_exists():
    media = build_media_index()
    ans = answer_question("Smart Manikin 黑屏怎么办？")
    if media:
        assert ans.sop_images
        assert any("Smart Manikin" in item.title or "Smart Manikin" in item.source_file for item in ans.sop_images)
    for item in ans.sop_images:
        assert item.url.startswith("/static/sop_media/")
        assert "image analysis" in item.description.lower() or "no image analysis" in item.description.lower()


def test_venue_access_returns_operational_refs():
    ans = answer_question("门打不开怎么办？")
    assert ans.scenario == "venue_access_issue"
    assert ans.operational_references
    assert any(ref.id == "venue_access_general" for ref in ans.operational_references)
    joined = " ".join(
        item.value
        for ref in ans.operational_references
        for item in ref.items
    )
    assert "Confirm the class address" in joined


def test_smart_manikin_returns_documented_operational_refs():
    ans = answer_question("Smart Manikin iPad not working, Bluetooth won't connect")
    assert ans.scenario == "smart_manikin_troubleshooting"
    ids = {ref.id for ref in ans.operational_references}
    assert "smart_manikin_bluetooth_power" in ids
    assert "smart_manikin_ipad_pad_setup" in ids
    joined = " ".join(item.value for ref in ans.operational_references for item in ref.items)
    assert "power strip" in joined
    assert "Place the manikin on a firm surface" in joined


def test_outages_return_only_matching_operational_refs():
    for q in ("停电怎么办？", "教室没网怎么办？"):
        ans = answer_question(q)
        assert ans.scenario in {"electricity_outage", "internet_outage"}
        assert ans.operational_references
        assert all(ref.scenario == ans.scenario for ref in ans.operational_references)
        ids = {ref.id for ref in ans.operational_references}
        assert not {"santa_clara_access", "newark_access", "smart_manikin_ipad_pad_setup"} & ids


@pytest.mark.parametrize(
    "question, scenario, expected_ref",
    [
        ("power outage, no electricity", "electricity_outage", "power_outage_handling"),
        ("internet down, platform not loading", "internet_outage", "internet_outage_handling"),
        ("class cannot start", "class_cannot_start", "class_cannot_start_triage"),
        ("unsafe injury on site", "safety_or_emergency", "safety_emergency_handling"),
        ("generate incident report template", "incident_report", "incident_report_template"),
        ("need reschedule approval", "escalation_guidance", "approval_prep_refund_reschedule"),
    ],
)
def test_audited_incident_types_return_operational_refs(question, scenario, expected_ref):
    ans = answer_question(question, {"lang": "en"})
    assert ans.scenario == scenario
    assert any(ref.id == expected_ref for ref in ans.operational_references)
    joined = " ".join(
        [ref.title + " " + ref.source_status for ref in ans.operational_references]
        + [item.value for ref in ans.operational_references for item in ref.items]
    )
    assert "/Users/" not in joined
    assert "/Desktop/" not in joined


def test_class_mismatch_returns_helpful_checkin_reference():
    ans = answer_question("student came to the wrong class time", {"lang": "en"})
    assert ans.scenario == "student_checkin_issue"
    ids = {ref.id for ref in ans.operational_references}
    assert "class_mismatch_checkin" in ids
    joined = " ".join(item.value for ref in ans.operational_references for item in ref.items)
    assert "registration/roster" in joined
    assert "wrong class" in joined
    assert "wrong time" in joined
    assert "wrong place" in joined
    assert "supervisor / registration back-office" in joined
    assert "does not provide a self-service fix for wrong course choice" in joined
    assert any("Do not self-decide" in item for ref in ans.operational_references for item in ref.do_not)


def test_operational_refs_do_not_leak_local_absolute_paths():
    ans = answer_question("door locked at Newark", {"site": "Newark"})
    joined = " ".join(
        [ref.title + " " + ref.source_status for ref in ans.operational_references]
        + [item.value for ref in ans.operational_references for item in ref.items]
    )
    assert "/Users/" not in joined
    assert "/Desktop/" not in joined
    assert "noctilucenteasteliq" not in joined


def test_generic_passcode_question_returns_trusted_private_codes():
    ans = answer_question("what is the room passcode?")
    assert ans.scenario == "venue_access_issue"
    joined = " ".join(item.value for ref in ans.operational_references for item in ref.items)
    assert "Suite 3: 2745" in joined
    assert "Suite 2018: 224466" in joined
    assert "Lockbox code at the 1st-floor front gate: 6285" in joined


def test_nonmatching_explicit_site_does_not_receive_other_site_codes():
    ans = answer_question("what is the room passcode?", {"site": "Palo Alto", "lang": "en"})
    assert ans.scenario == "venue_access_issue"
    joined = " ".join(item.value for ref in ans.operational_references for item in ref.items)
    assert "If no listed site-specific trusted passcode matches" in joined
    assert "2745" not in joined
    assert "224466" not in joined
    assert "6285" not in joined


def test_trusted_passcode_only_for_matching_access_site():
    access = answer_question("door locked, what is the room passcode?", {"site": "Newark"})
    assert access.scenario == "venue_access_issue"
    joined = " ".join(item.value for ref in access.operational_references for item in ref.items)
    assert "224466" in joined
    assert "6285" in joined

    power = answer_question("power outage at Newark", {"site": "Newark", "lang": "en"})
    assert power.scenario == "electricity_outage"
    joined_power = " ".join(item.value for ref in power.operational_references for item in ref.items)
    assert "224466" not in joined_power
    assert "6285" not in joined_power


def test_venue_access_returns_sop_images_when_media_exists():
    media = build_media_index()
    ans = answer_question("门打不开怎么办？")
    assert ans.scenario == "venue_access_issue"
    if media:
        assert ans.sop_images
    for item in ans.sop_images:
        assert item.url.startswith("/static/sop_media/")


def test_electricity_outage_does_not_return_random_smart_manikin_image():
    ans = answer_question("What should I do if the power goes out?", {"lang": "en"})
    assert ans.scenario == "electricity_outage"
    assert ans.sop_images == []


def test_power_outage_does_not_receive_unrelated_images_or_refs():
    ans = answer_question("What should I do if the power goes out?", {"site": "Santa Clara", "lang": "en"})
    assert ans.scenario == "electricity_outage"
    assert ans.sop_images == []
    ids = {ref.id for ref in ans.operational_references}
    assert "power_outage_handling" in ids
    assert "santa_clara_access" not in ids
    joined = " ".join(item.value for ref in ans.operational_references for item in ref.items)
    assert "2745" not in joined


def test_sop_media_index_exposes_web_paths_not_local_paths():
    """The committed index must serve web URLs and never leak local machine paths
    (absolute paths, /Users/<name>/..., or username tokens in tags)."""
    items = build_media_index()
    leaky = {"users", "desktop", "developer", "private", "home", "noctilucenteasteliq"}
    for item in items:
        assert item.url.startswith("/static/sop_media/")
        assert not item.source_file.startswith("/")
        assert "Users" not in item.source_file and ":\\" not in item.source_file
        assert not leaky.intersection({t.lower() for t in item.tags})
        for tag in item.tags:
            assert "/" not in tag


def test_no_media_match_response_still_works():
    ans = answer_question("asdf qwer zxcv totally unrelated", {"lang": "en"})
    assert ans.scenario == "unknown"
    assert ans.sop_images == []
    assert ans.answer_summary


# --- common-knowledge labeling ----------------------------------------------

def test_common_knowledge_clearly_labeled_not_official():
    for q in ("停电了怎么办？", "教室没网怎么办？", "门打不开怎么办？"):
        ans = answer_question(q)
        assert prompts.SS_GENERAL in ans.source_status


# --- attachments: acknowledged, never claimed-as-analyzed --------------------

def test_attachments_acknowledged_without_claiming_analysis():
    ctx = {
        "site": "Santa Clara",
        "attachments": [{"type": "photo", "description": "dark classroom", "filename": "outage.jpg"}],
    }
    ans = answer_question("停电了怎么办？", ctx)
    assert prompts.ATTACHMENT_ACK in ans.answer
    assert prompts.ATTACHMENT_ACK in ans.attachments_note
    assert "dark classroom" in ans.answer


# --- escalation / unknown ----------------------------------------------------

def test_escalation_marks_human_review():
    ans = answer_question("学生要退款，而且要找主管")
    assert ans.scenario == "escalation_guidance"
    assert ans.needs_human_review is True


def test_unknown_is_low_confidence_and_reviewed():
    ans = answer_question("asdf qwer zxcv totally unrelated")
    assert ans.scenario == "unknown"
    assert ans.confidence == "low"
    assert ans.needs_human_review is True


# --- course-fit still works (site-intelligence reference) -------------------

def test_course_recommendation_flags_brand_rule_unknown():
    ans = answer_question("Should we run AHA BLS or Red Cross CPR in this city?")
    assert ans.scenario == "course_type_recommendation"
    # Demand-tilt explanation present (healthcare-workforce vs community demand).
    assert "医疗" in ans.answer or "healthcare" in ans.answer.lower()
    # Brand decision rule is genuinely undefined -> exact phrase surfaced.
    assert prompts.NEEDS_OFFICIAL_SOP in ans.answer


# --- API endpoint ------------------------------------------------------------

def test_endpoint_returns_structured_answer(client):
    resp = client.post(
        "/api/agents/autocpr-site-manager/ask",
        json={"question": "停电了怎么办？", "context": {"site": "Santa Clara", "audience": "internal"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    for key in (
        "answer", "scenario", "confidence", "sources", "needs_human_review",
        "next_actions", "issue_type", "severity", "immediate_safety_check",
        "steps", "information_to_collect", "evidence_requested", "contacts",
        "customer_communication", "do_not_decide_without_approval", "source_status",
        "language", "attachments_note", "answer_summary", "sop_images",
    ):
        assert key in body
    assert body["scenario"] == "electricity_outage"
    assert body["needs_human_review"] is True
    assert body["evidence_requested"]


def test_endpoint_returns_english_structured_answer(client):
    resp = client.post(
        "/api/agents/autocpr-site-manager/ask",
        json={"question": "What should I do if the power goes out?", "context": {"lang": "en"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["language"] == "en"
    assert body["scenario"] == "electricity_outage"
    assert body["issue_type"] == "Electricity outage"
    assert "Immediate safety check" in body["answer"]


def test_endpoint_requires_question(client):
    resp = client.post("/api/agents/autocpr-site-manager/ask", json={})
    assert resp.status_code == 422


# --- no regression to existing app ------------------------------------------

def test_health_still_ok(client):
    assert client.get("/health").status_code == 200
