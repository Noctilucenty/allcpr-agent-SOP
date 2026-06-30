"""Tests for deterministic 管点 / site-operations scenario classification."""
from __future__ import annotations

import pytest

from app.agents.autocpr_site_manager import scenarios


@pytest.mark.parametrize(
    "question, expected",
    [
        # --- site-operations incidents ---
        ("停电了怎么办？", "electricity_outage"),
        ("There is a power outage in the classroom", "electricity_outage"),
        ("教室没网了", "internet_outage"),
        ("the wifi is down", "internet_outage"),
        ("门打不开，进不去教室", "venue_access_issue"),
        ("can't get in, the door is locked", "venue_access_issue"),
        ("Smart Manikin 黑屏怎么办", "smart_manikin_troubleshooting"),
        ("蓝牙连不上", "smart_manikin_troubleshooting"),
        ("老师没到，课程无法开始怎么办", "instructor_no_show"),
        ("学生签到不在名单", "student_checkin_issue"),
        ("class mismatch", "student_checkin_issue"),
        ("student came to the wrong class time", "student_checkin_issue"),
        ("学员走错班级怎么办", "student_checkin_issue"),
        ("chose wrong course BLS vs CPR", "student_checkin_issue"),
        ("学生的证书没出来", "completion_or_certificate_issue"),
        ("学生到了但课程无法开始怎么办", "class_cannot_start"),
        ("现场有人受伤了", "safety_or_emergency"),
        ("怎么写现场事件报告", "incident_report"),
        ("什么时候要升级给主管", "escalation_guidance"),
        # --- site-intelligence references ---
        ("开点流程是什么", "site_opening_reference"),
        ("这个 ZIP 是否适合开点", "zip_site_evaluation"),
        ("Should we run AHA BLS or Red Cross CPR?", "course_type_recommendation"),
        ("what does healthcare density mean?", "dashboard_metric_explanation"),
        ("asdf qwer zxcv unrelated", "unknown"),
    ],
)
def test_classify(question, expected):
    assert scenarios.classify(question) == expected


@pytest.mark.parametrize(
    "question, expected",
    [
        ("停电了怎么办？", "electricity_outage"),
        ("What should I do if the power goes out?", "electricity_outage"),
        ("教室没网怎么办？", "internet_outage"),
        ("The classroom internet is down. What should I do?", "internet_outage"),
        ("门打不开怎么办？", "venue_access_issue"),
        ("The door is locked and I cannot access the room.", "venue_access_issue"),
        ("Smart Manikin 黑屏怎么办？", "smart_manikin_troubleshooting"),
        ("The Smart Manikin screen is black. What should I do?", "smart_manikin_troubleshooting"),
        ("老师没到，课程无法开始怎么办？", "instructor_no_show"),
        ("The instructor did not show up and class cannot start.", "instructor_no_show"),
        ("学生证书没出来怎么办？", "completion_or_certificate_issue"),
        ("The student certificate/completion is missing.", "completion_or_certificate_issue"),
        ("现场有人受伤怎么办？", "safety_or_emergency"),
        ("Someone is injured on site. What should I do?", "safety_or_emergency"),
        ("生成现场事故报告模板", "incident_report"),
        ("Generate an incident report template.", "incident_report"),
    ],
)
def test_requested_bilingual_scenario_examples(question, expected):
    assert scenarios.classify(question) == expected


def test_safety_wins_over_co_occurring_cause():
    # Safety must never be shadowed by a co-occurring cause keyword.
    assert scenarios.classify("停电了而且有人受伤") == "safety_or_emergency"


def test_named_cause_beats_generic_class_cannot_start():
    assert scenarios.classify("老师没到，课程无法开始") == "instructor_no_show"
    assert scenarios.classify("停电了，课程无法开始") == "electricity_outage"


def test_context_only_zip_falls_back_to_zip_evaluation():
    assert scenarios.classify("tell me about here", {"zip": "95110"}) == "zip_site_evaluation"


def test_empty_question_is_unknown():
    assert scenarios.classify("") == "unknown"
    assert scenarios.classify("", None) == "unknown"


@pytest.mark.parametrize(
    "scenario",
    [
        "electricity_outage",
        "internet_outage",
        "venue_access_issue",
        "smart_manikin_troubleshooting",
        "class_cannot_start",
        "instructor_no_show",
        "student_checkin_issue",
        "completion_or_certificate_issue",
        "safety_or_emergency",
        "incident_report",
        "escalation_guidance",
        "site_operations_general",
        "zip_site_evaluation",
        "course_type_recommendation",
        "unknown",
    ],
)
def test_always_review_scenarios(scenario):
    assert scenarios.requires_review(scenario) is True


@pytest.mark.parametrize(
    "scenario",
    [
        "dashboard_metric_explanation",
        "site_opening_reference",
        "sop_training",
        "competitor_analysis",
        "enrichment_data_check",
        "improvement_optimization",
    ],
)
def test_non_review_scenarios(scenario):
    assert scenarios.requires_review(scenario) is False


def test_primary_scenario_labels_present():
    primary = {
        "site_operations_general", "electricity_outage", "internet_outage",
        "venue_access_issue", "smart_manikin_troubleshooting", "class_cannot_start",
        "instructor_no_show", "student_checkin_issue",
        "completion_or_certificate_issue", "safety_or_emergency", "incident_report",
        "escalation_guidance", "site_opening_reference",
        "dashboard_metric_explanation", "zip_site_evaluation",
        "course_type_recommendation", "unknown",
    }
    assert primary <= set(scenarios.SCENARIOS)
