"""Tests for the 管点 agent behavior and the FastAPI endpoint."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import web_app
from app.agents.autocpr_site_manager import answer_question, prompts
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
    low = ans.answer.lower()
    assert "needs engineer/vendor confirmation" in low
    assert "no documented fix" in low
    for unsupported in ("wi-fi", "wifi", "browser", "permission", "reset", "calibration"):
        assert unsupported not in low


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
        "language", "attachments_note",
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
