"""Tests for the deterministic SOP knowledge-base retrieval engine.

The engine bridges messy user wording to the closest source-backed SOP route
without inventing content and without any network call. These tests assert:
  * every canonical anchor still routes where the engine claims (no drift),
  * messy paraphrases that fall through the keyword classifier still resolve to a
    relevant, step-by-step SOP match flagged for staff confirmation,
  * genuinely unmatched text returns a safe "not found" result,
  * no real passcode ever appears in a match,
  * equipment issues carry a do-not-repair/dismantle caution,
  * staff-only routes are hidden from the student audience.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from app.agents.autocpr_site_manager import answer_question
from app.agents.autocpr_site_manager import sop_answer_engine as engine
from app.agents.autocpr_site_manager import ai_orchestrator as ai

PKG = Path(__file__).resolve().parents[2] / "app" / "agents" / "autocpr_site_manager"


def _secret_values():
    """Real internal secret values, pulled from the committed refs (never
    hardcoded) so the non-leak checks have something concrete to guard."""
    vals = set(ai.sensitive_values())
    refs = json.loads((PKG / "sop_operational_refs.json").read_text(encoding="utf-8"))
    for ref in refs.get("references", []):
        for item in ref.get("items", []):
            if (item.get("sensitivity") or "").lower() != "internal":
                continue
            for m in re.findall(r"[A-Za-z0-9]{4,}", str(item.get("value") or "")):
                if any(ch.isdigit() for ch in m):
                    vals.add(m)
    return {v for v in vals if len(v) >= 4}


SECRETS = _secret_values()


def _blob(match: dict) -> str:
    return json.dumps(match, ensure_ascii=False)


# ---- anchors stay honest ---------------------------------------------------
def test_subissue_anchors_route_to_their_subissue():
    for subissue, anchor in engine._SUBISSUE_ANCHORS.items():
        a = answer_question(anchor)
        assert a.scenario == "smart_manikin_troubleshooting", (anchor, a.scenario)
        assert a.smart_manikin_subissue == subissue, (anchor, a.smart_manikin_subissue)


def test_scenario_anchors_route_to_their_scenario():
    seen = set()
    for route in engine._routes():
        if route.kind != "scenario" or route.scenario in seen:
            continue
        seen.add(route.scenario)
        a = answer_question(route.anchor)
        assert a.scenario == route.scenario, (route.anchor, a.scenario)


# ---- messy wording resolves to a relevant SOP match ------------------------
def test_messy_wording_finds_relevant_sop_match():
    cases = {
        "i cant get the practice session going": "class_cannot_start",
        "学生开始不了课程": "class_cannot_start",
        "nothing is on the desk where it should be": "smart_manikin_site_inspection",
        "the dummy wont link up to the app": "bluetooth_connection",
    }
    for q, expect in cases.items():
        m = engine.compose_sop_match(q)
        assert m["found"], q
        assert m["matched_issue"] == expect, (q, m["matched_issue"])
        assert len(m["steps"]) >= 3, q
        # Paraphrase matches are low-confidence and must ask for staff confirmation.
        assert m["confidence"] == "low", q
        assert m["needs_human_review"] is True, q
        assert m["note"], q


def test_ipad_paraphrase_returns_power_steps():
    m = engine.compose_sop_match("the tablet screen is totally dark and nothing happens")
    assert m["found"]
    blob = " ".join(m["steps"]).lower()
    assert "charg" in blob or "power" in blob
    assert "unplug the tablet charging cable" not in blob


def test_sop_match_keeps_source_chunks_accessible_but_not_as_main_steps():
    m = engine.compose_sop_match("ipad no battery")
    assert m["found"]
    assert m["evidence_requested"]
    assert "raw_retrieved_chunks" in m
    main = " ".join(m["steps"]).lower()
    raw = " ".join(chunk.get("value", "") for chunk in m["raw_retrieved_chunks"]).lower()
    assert "unplug the tablet charging cable" not in main
    # Source-recorded context can still be inspected in the collapsed details.
    assert "source records no ipad battery" in raw or "unplug the tablet charging cable" in raw


def test_unmatched_text_is_not_found_safely():
    m = engine.compose_sop_match("zzxqq gibberish nonsense 12093 wharrgarbl")
    assert m["found"] is False
    assert m["steps"] == []
    assert m["needs_human_review"] is True
    assert m["note"]


def test_strong_query_passes_through_deterministically():
    m = engine.compose_sop_match("power outage")
    assert m["found"]
    assert m["via"] == "deterministic"
    assert m["matched_issue"] == "electricity_outage"


# ---- guardrails ------------------------------------------------------------
def test_match_never_leaks_a_passcode():
    assert SECRETS, "expected at least one internal secret to guard against"
    for q in ("the door is locked and I cannot get in", "door code", "wifi password",
              "the little screen thing is frozen", "camera seems off"):
        blob = _blob(engine.compose_sop_match(q, staff_access_token=None))
        for secret in SECRETS:
            assert secret not in blob, (q, secret)


def test_equipment_issue_carries_do_not_repair():
    m = engine.compose_sop_match("ipad no battery")
    dont = " ".join(m["do_not"]).lower()
    assert "repair" in dont or "dismantle" in dont or "reset" in dont


def test_reference_image_carries_reference_only_caution():
    # Any surfaced image must carry the reference-only / do-not-repair caution.
    for q in ("平板没电", "the tablet screen is dark"):
        m = engine.compose_sop_match(q)
        for img in m.get("image_references", []):
            assert "caution" in img and img["caution"], q
            low = img["caution"].lower()
            assert "reference only" in low or "参考" in img["caution"]


def test_student_audience_hides_staff_only_inspection_route():
    # The staff Full Site Inspection workflow is staff-only; a student asking a
    # table question must not be routed into it by retrieval.
    hit = engine.retrieve_route("what should be on the table", audience="student")
    if hit is not None:
        route, _ = hit
        assert route.audience != "staff"
    # And no secret leaks for a student-context match.
    m = engine.compose_sop_match("what should be on the table", audience="student")
    blob = _blob(m)
    for secret in SECRETS:
        assert secret not in blob


# ---- weakness heuristic ----------------------------------------------------
def test_sop_assist_recommended_flags_weak_answers_only():
    assert engine.sop_assist_recommended(answer_question("camera seems off")) is True
    assert engine.sop_assist_recommended(answer_question("power outage")) is False
