"""System-wide fuzzy/casual intent routing coverage.

Staff type casual, incomplete, bilingual phrases — not exact SOP wording. These
tests lock in deterministic routing for every major operational category, plus
the precedence rules that must not regress, and the passcode redaction guarantees.
"""
from __future__ import annotations

import pytest

from app.agents.autocpr_site_manager import answer_question, staff_access
from app.agents.autocpr_site_manager.scenarios import classify


# (question, expected_scenario) — >=3 English + >=2 Chinese per category.
FUZZY_CASES = [
    # A) venue / access / passcode
    ("door locked", "venue_access_issue"),
    ("locked out", "venue_access_issue"),
    ("can't get in", "venue_access_issue"),
    ("front door locked", "venue_access_issue"),
    ("keybox password", "venue_access_issue"),
    ("门锁了", "venue_access_issue"),
    ("进不去", "venue_access_issue"),
    ("钥匙盒密码", "venue_access_issue"),
    # B) arrival / inspection procedure
    ("what should I do when I arrive", "smart_manikin_site_inspection"),
    ("opening procedure", "smart_manikin_site_inspection"),
    ("first thing to do", "smart_manikin_site_inspection"),
    ("到场后要做什么", "smart_manikin_site_inspection"),
    ("我到分点了要干嘛", "smart_manikin_site_inspection"),
    # C) device / iPad / PAD
    ("ipad not working", "smart_manikin_troubleshooting"),
    ("ipad black screen", "smart_manikin_troubleshooting"),
    ("app black screen", "smart_manikin_troubleshooting"),
    ("平板没反应", "smart_manikin_troubleshooting"),
    ("设备打不开", "smart_manikin_troubleshooting"),
    # D) bluetooth / connection
    ("bluetooth not connecting", "smart_manikin_troubleshooting"),
    ("can't pair", "smart_manikin_troubleshooting"),
    ("connection failed", "smart_manikin_troubleshooting"),
    ("蓝牙连不上", "smart_manikin_troubleshooting"),
    ("假人连接不上", "smart_manikin_troubleshooting"),
    # E) training / no data
    ("training data missing", "smart_manikin_troubleshooting"),
    ("no training data", "smart_manikin_troubleshooting"),
    ("设备没数据", "smart_manikin_troubleshooting"),
    # F) class mismatch / wrong course
    ("student chose wrong course", "student_checkin_issue"),
    ("picked wrong course", "student_checkin_issue"),
    ("not their class", "student_checkin_issue"),
    ("选错课", "student_checkin_issue"),
    ("不是这个班", "student_checkin_issue"),
    # G) roster / check-in
    ("student not on list", "student_checkin_issue"),
    ("can't find student", "student_checkin_issue"),
    ("registration not showing", "student_checkin_issue"),
    ("找不到名字", "student_checkin_issue"),
    ("名单没有", "student_checkin_issue"),
    # H) instructor no-show / class cannot start
    ("teacher did not arrive", "instructor_no_show"),
    ("no instructor", "instructor_no_show"),
    ("教练没来", "instructor_no_show"),
    ("students arrived and class cannot start", "class_cannot_start"),
    ("students waiting", "class_cannot_start"),
    ("学员在等", "class_cannot_start"),
    # I) refund / reschedule / cancel / compensation
    ("refund", "escalation_guidance"),
    ("student wants money back", "escalation_guidance"),
    ("change date", "escalation_guidance"),
    ("改时间", "escalation_guidance"),
    ("取消课程", "escalation_guidance"),
    # J) certificate / completion
    ("certificate missing", "completion_or_certificate_issue"),
    ("didn't receive certificate", "completion_or_certificate_issue"),
    ("证书没收到", "completion_or_certificate_issue"),
    ("证书名字错", "completion_or_certificate_issue"),
    # K) power / internet / platform
    ("power out", "electricity_outage"),
    ("outlet not working", "electricity_outage"),
    ("插座没电", "electricity_outage"),
    ("website not loading", "internet_outage"),
    ("wifi down", "internet_outage"),
    ("网站打不开", "internet_outage"),
    # L) camera / monitoring
    ("camera offline", "incident_report"),
    ("camera not working", "incident_report"),
    ("摄像头坏了", "incident_report"),
    ("监控看不到", "incident_report"),
    # M) safety / injury / hazard
    ("student injured", "safety_or_emergency"),
    ("someone got hurt", "safety_or_emergency"),
    ("water leak", "safety_or_emergency"),
    ("漏水", "safety_or_emergency"),
    ("有人受伤", "safety_or_emergency"),
    # N) cleaning / supplies
    ("trash full", "smart_manikin_site_inspection"),
    ("no gloves", "smart_manikin_site_inspection"),
    ("supplies missing", "smart_manikin_site_inspection"),
    ("垃圾满了", "smart_manikin_site_inspection"),
    ("房间很脏", "smart_manikin_site_inspection"),
    # O) equipment placement
    ("where to put equipment", "smart_manikin_site_inspection"),
    ("where does the ipad go", "smart_manikin_site_inspection"),
    ("器材怎么摆", "smart_manikin_site_inspection"),
    ("iPad放哪里", "smart_manikin_site_inspection"),
    # P) incident / escalation
    ("what should I report", "incident_report"),
    ("怎么上报", "escalation_guidance"),
    ("需要报告", "incident_report"),
]


@pytest.mark.parametrize("question, scenario", FUZZY_CASES)
def test_fuzzy_phrases_route_to_expected_scenario(question, scenario):
    assert classify(question) == scenario


@pytest.mark.parametrize("question, scenario", FUZZY_CASES)
def test_fuzzy_phrases_are_never_unknown(question, scenario):
    ans = answer_question(question)
    assert ans.scenario != "unknown"
    assert ans.steps or ans.next_actions or ans.immediate_safety_check


# --- precedence rules that must not regress ---------------------------------
def test_precedence_regressions():
    assert classify("teacher did not arrive") == "instructor_no_show"
    assert classify("instructor did not show") == "instructor_no_show"
    assert classify("students arrived and class cannot start") == "class_cannot_start"
    # arrival/procedure → inspection pre-check
    a = answer_question("what should I do when I arrive", {"lang": "en"})
    assert a.scenario == "smart_manikin_site_inspection"
    assert a.issue_subtype == "pre_check_photos"


def test_refund_reschedule_cancel_still_require_approval():
    for q in ("refund", "student wants money back", "change date", "取消课程"):
        ans = answer_question(q, {"lang": "en"})
        assert ans.needs_human_review is True


def test_truly_unsupported_stays_unknown():
    for q in ("what's the weather", "tell me a joke", "今天股票怎么样"):
        assert classify(q) == "unknown"


# --- content assertions (one per a few categories) --------------------------
def test_device_fuzzy_has_source_or_escalation():
    ans = answer_question("ipad black screen", {"lang": "en"})
    low = ans.answer.lower()
    assert "engineer/vendor" in low or "escalate" in low


def test_camera_fuzzy_routes_to_report_and_escalation():
    ans = answer_question("camera offline", {"lang": "en"})
    assert ans.scenario == "incident_report"
    assert ans.steps


# --- passcode security across fuzzy access phrases ---------------------------
FUZZY_ACCESS = ["door locked", "locked out", "can't get in", "keybox password",
                "门锁了", "进不去", "钥匙盒密码", "what is the door code"]


@pytest.mark.parametrize("question", FUZZY_ACCESS)
def test_fuzzy_access_redacted_by_default(question):
    ans = answer_question(question)
    assert ans.scenario == "venue_access_issue"
    assert ans.passcode_ref_available is True  # refs exist...
    assert ans.passcode_revealed is False       # ...but not revealed
    joined = " ".join(item.value for ref in ans.operational_references for item in ref.items)
    for code in ("2745", "224466", "6285", "DoBeUSA", "DoBesince2016"):
        assert code not in joined
    assert "2745" not in ans.answer  # not in steps/full text either


@pytest.mark.parametrize("question", FUZZY_ACCESS)
def test_fuzzy_access_reveals_codes_only_when_unlocked(monkeypatch, question):
    monkeypatch.setenv("ALLCPR_STAFF_ACCESS_PIN", "2745")
    token = staff_access.issue_token()
    ans = answer_question(question, staff_access_token=token)
    assert ans.staff_access_unlocked is True
    joined = " ".join(item.value for ref in ans.operational_references for item in ref.items)
    assert "2745" in joined  # source-backed code revealed for staff


def test_invalid_token_keeps_fuzzy_access_redacted(monkeypatch):
    monkeypatch.setenv("ALLCPR_STAFF_ACCESS_PIN", "2745")
    ans = answer_question("door locked", staff_access_token="bogus.sig")
    assert ans.staff_access_unlocked is False
    joined = " ".join(item.value for ref in ans.operational_references for item in ref.items)
    assert "2745" not in joined
