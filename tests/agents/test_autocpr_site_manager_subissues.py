"""Regression tests for non-Smart-Manikin sub-issue routing and coverage.

These lock in the "no generic dump" rule for access / check-in / completion /
power / internet: a narrow query must route to its focused answer (short,
source-backed, no invented policy) instead of the full scenario bucket.
"""
from __future__ import annotations

import pytest

from app.agents.autocpr_site_manager import answer_question, prompts
from app.agents.autocpr_site_manager.incident_logs import build_log_entry
from app.agents.autocpr_site_manager.scenario_subissues import detect_subissue


# --- sub-issue detection -----------------------------------------------------

@pytest.mark.parametrize(
    "question, scenario, expected",
    [
        ("what is the room passcode?", "venue_access_issue", "passcode_needed"),
        ("门禁密码是多少", "venue_access_issue", "passcode_needed"),
        ("the door code failed, keypad not working", "venue_access_issue", "code_failed"),
        ("密码不对，进不去", "venue_access_issue", "code_failed"),
        ("wrong room and floor", "venue_access_issue", "wrong_room_floor"),
        ("找不到房间", "venue_access_issue", "wrong_room_floor"),
        # casual locked-out phrasing now lands on the passcode panel (redacted
        # availability when locked, real codes only when unlocked)
        ("door locked", "venue_access_issue", "passcode_needed"),
        ("can't get in", "venue_access_issue", "passcode_needed"),
        ("门锁了", "venue_access_issue", "passcode_needed"),
        ("chose wrong course BLS vs CPR", "student_checkin_issue", "wrong_course"),
        ("选错课程了", "student_checkin_issue", "wrong_course"),
        ("student not on roster", "student_checkin_issue", "not_on_roster"),
        ("名单找不到这个学员", "student_checkin_issue", "not_on_roster"),
        ("certificate issue", "completion_or_certificate_issue", "certificate_issue"),
        ("证书没出来", "completion_or_certificate_issue", "certificate_issue"),
        ("forgot completion photo", "completion_or_certificate_issue", ""),
        ("power still no power after restart", "electricity_outage", "fix_failed"),
        ("internet still down after restart", "internet_outage", "fix_failed"),
        ("power outage", "electricity_outage", ""),
    ],
)
def test_detect_subissue(question, scenario, expected):
    assert detect_subissue(scenario, question) == expected


# --- focused answers don't dump unrelated subcases ---------------------------

def test_passcode_query_is_focused_not_generic_roster_dump():
    ans = answer_question("what is the room passcode?", {"lang": "en"})
    assert ans.scenario == "venue_access_issue"
    assert ans.issue_subtype == "passcode_needed"
    low = ans.answer.lower()
    assert "no listed site matches" in low
    # must not bleed into unrelated buckets
    assert "verify the student" not in low
    assert "instructor" not in low
    assert len(ans.steps) <= 5


def test_code_failed_leads_with_venue_and_record_attempt():
    ans = answer_question("the door code failed, keypad not working", {"lang": "en"})
    assert ans.issue_subtype == "code_failed"
    low = ans.answer.lower()
    assert ans.steps[0].lower().startswith("stop retrying")
    assert "venue/property" in low
    assert "do not force the door" in low
    assert any("venue" in c.lower() or "property" in c.lower() for c in ans.contacts)


def test_wrong_room_floor_confirms_location_and_uses_source_materials():
    ans = answer_question("students went to the wrong room and floor", {"lang": "en"})
    assert ans.issue_subtype == "wrong_room_floor"
    low = ans.answer.lower()
    assert "address, floor, and room" in low
    assert "instruction" in low or "signage" in low
    ids = {ref.id for ref in ans.operational_references}
    assert "venue_wrong_room_floor" in ids


def test_wrong_course_gives_escalation_and_source_boundary():
    ans = answer_question("student chose wrong course BLS vs CPR", {"lang": "en"})
    assert ans.scenario == "student_checkin_issue"
    assert ans.issue_subtype == "wrong_course"
    assert ans.policy_approval_required is True
    low = ans.answer.lower()
    assert "registration" in low
    assert "supervisor" in low or "registration back-office" in low
    assert "do not switch" in low


def test_not_on_roster_focuses_on_roster_and_proof():
    ans = answer_question("student not on roster", {"lang": "en"})
    assert ans.issue_subtype == "not_on_roster"
    assert ans.policy_approval_required is True
    low = ans.answer.lower()
    assert "registration proof" in low or "registration/roster" in low
    assert "do not self-decide" in low


def test_certificate_issue_does_not_invent_policy():
    ans = answer_question("certificate issue, wrong certificate", {"lang": "en"})
    assert ans.scenario == "completion_or_certificate_issue"
    assert ans.issue_subtype == "certificate_issue"
    assert ans.policy_approval_required is True
    low = ans.answer.lower()
    assert prompts.NEEDS_OFFICIAL_SOP in ans.answer
    assert "do not promise certificate" in low or "do not invent certificate" in low
    # must not assert an eligibility/timeline it cannot know
    assert "will be issued" not in low
    assert "business days" not in low


def test_forgot_completion_photo_still_uses_source_backed_flow():
    # The photo path should keep the documented support@allcpr.org flow, not the
    # certificate-policy override.
    ans = answer_question("I forgot to take the completion photo", {"lang": "en"})
    assert ans.issue_subtype != "certificate_issue"
    assert "support@allcpr.org" in ans.answer.lower()


# --- power / internet "still down" prioritizes escalation, not basics --------

def test_power_fix_failed_prioritizes_escalation_and_incident():
    ans = answer_question("power still no power after we reset the breaker", {"lang": "en"})
    assert ans.scenario == "electricity_outage"
    assert ans.issue_subtype == "fix_failed"
    low = ans.answer.lower()
    assert ans.steps[0].lower().startswith("stop repeating")
    assert "incident report" in low
    assert "escalate" in low


def test_internet_fix_failed_separates_venue_vs_platform():
    ans = answer_question("internet still down after restart", {"lang": "en"})
    assert ans.scenario == "internet_outage"
    assert ans.issue_subtype == "fix_failed"
    low = ans.answer.lower()
    assert "venue network" in low or "venue/property" in low
    assert "platform" in low
    assert "incident report" in low


def test_power_outage_steps_capped_at_five():
    for q in ("power outage", "停电了怎么办？"):
        ans = answer_question(q)
        assert len(ans.steps) <= 5


@pytest.mark.parametrize(
    "question",
    [
        "power outage", "internet down", "door locked", "what is the room passcode?",
        "the door code failed", "wrong room and floor", "class mismatch",
        "wrong course BLS vs CPR", "student not on roster", "certificate issue",
        "instructor no-show", "class cannot start", "generate incident report",
        "student injured", "need refund", "Smart Manikin black screen",
    ],
)
def test_primary_scenarios_keep_steps_focused(question):
    """No scenario should dump more than five main steps in the lead block."""
    ans = answer_question(question, {"lang": "en"})
    assert len(ans.steps) <= 5
    assert len(ans.evidence_requested) <= 5


# --- operational-reference coverage gaps -------------------------------------

@pytest.mark.parametrize(
    "question, ctx, scenario, expected_ref",
    [
        ("cannot access room", None, "venue_access_issue", "venue_access_general"),
        ("wrong room and floor", None, "venue_access_issue", "venue_wrong_room_floor"),
        ("门禁密码是多少", None, "venue_access_issue", "santa_clara_access"),
        ("completion not recorded", None, "completion_or_certificate_issue", "completion_photo_certificate"),
        ("student injured on site", {"lang": "en"}, "safety_or_emergency", "safety_emergency_handling"),
        ("internet still down after restart", None, "internet_outage", "internet_outage_handling"),
    ],
)
def test_coverage_gaps_now_return_refs(question, ctx, scenario, expected_ref):
    ans = answer_question(question, ctx)
    assert ans.scenario == scenario
    ids = {ref.id for ref in ans.operational_references}
    assert expected_ref in ids


def test_chinese_passcode_redacted_by_default_revealed_when_unlocked(monkeypatch):
    from app.agents.autocpr_site_manager import staff_access

    # Default/public mode: codes redacted, redaction notice present.
    locked = answer_question("门禁密码是多少")
    locked_joined = " ".join(item.value for ref in locked.operational_references for item in ref.items)
    assert "2745" not in locked_joined
    assert "224466" not in locked_joined
    assert "内部密码已隐藏" in locked_joined

    # Staff unlock reveals the source-backed codes for that response only.
    monkeypatch.setenv("ALLCPR_STAFF_ACCESS_PIN", "4321")
    token = staff_access.issue_token()
    unlocked = answer_question("门禁密码是多少", staff_access_token=token)
    unlocked_joined = " ".join(item.value for ref in unlocked.operational_references for item in ref.items)
    assert "2745" in unlocked_joined
    assert "224466" in unlocked_joined


def test_refund_reschedule_cancel_require_approval():
    for q in ("need refund", "need reschedule", "cancel the class"):
        ans = answer_question(q, {"lang": "en"})
        assert ans.needs_human_review is True
        joined = " ".join(ans.do_not_decide_without_approval).lower()
        assert "approval" in joined or "escalate" in joined


# --- power / internet do not pull unrelated images ---------------------------

def test_outage_fix_failed_returns_no_unrelated_images():
    for q in ("power still no power", "internet still down after restart"):
        ans = answer_question(q, {"lang": "en"})
        assert ans.sop_images == []


# --- incident log captures the new subtype fields ----------------------------

def test_incident_log_captures_subtype_and_focused_steps():
    ans = answer_question("the door code failed, keypad not working", {"lang": "en"})
    entry = build_log_entry("the door code failed", {"site": "Santa Clara"}, ans)
    assert entry["issue_subtype"] == "code_failed"
    assert entry["route_detail"] == "access"
    assert entry["policy_approval_required"] is False
    # focused first action, not a generic dump
    assert entry["first_action"] == ans.steps[:3]
    assert entry["first_action"][0].lower().startswith("stop retrying")


def test_incident_log_flags_policy_approval_for_wrong_course():
    ans = answer_question("chose wrong course BLS vs CPR", {"lang": "en"})
    entry = build_log_entry("chose wrong course", {"site": "Newark"}, ans)
    assert entry["issue_subtype"] == "wrong_course"
    assert entry["route_detail"] == "checkin"
    assert entry["policy_approval_required"] is True


def test_subissue_refs_do_not_leak_local_paths():
    for q in ("wrong room and floor", "门禁密码是多少", "certificate issue"):
        ans = answer_question(q, {"lang": "en"})
        joined = " ".join(
            [ref.title + " " + ref.source_status for ref in ans.operational_references]
            + [item.value for ref in ans.operational_references for item in ref.items]
        )
        assert "/Users/" not in joined
        assert "/Desktop/" not in joined
        assert "noctilucenteasteliq" not in joined
