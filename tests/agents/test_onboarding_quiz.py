"""Tests for the Smart Manikin site-representative onboarding certification quiz.

These cover the pure quiz data + scoring module (no web layer): exactly 20
questions, the answer key stays server-side, the 16/20 pass threshold, and the
critical auto-fail rule that overrides a high score.
"""
from __future__ import annotations

from app.agents.autocpr_site_manager.onboarding_quiz import (
    CRITICAL_QUESTION_IDS,
    ONBOARDING_QUESTIONS,
    PASSING_SCORE,
    TOTAL_QUESTIONS,
    public_questions,
    score_onboarding_attempt,
)


def _correct_answers() -> dict:
    return {q["id"]: q["correct_answer"] for q in ONBOARDING_QUESTIONS}


def _noncritical_ids() -> list:
    return [q["id"] for q in ONBOARDING_QUESTIONS if not q["critical"]]


def test_onboarding_quiz_has_exactly_20_questions():
    assert TOTAL_QUESTIONS == 20
    assert len(ONBOARDING_QUESTIONS) == 20
    ids = [q["id"] for q in ONBOARDING_QUESTIONS]
    assert len(set(ids)) == 20  # unique ids
    for q in ONBOARDING_QUESTIONS:
        assert q["id"]
        assert q["type"] in {"multiple_choice", "true_false"}
        assert q["prompt_en"] and q["prompt_zh"]
        assert q["options_en"] and q["options_zh"]
        assert len(q["options_en"]) == len(q["options_zh"])
        assert q["correct_answer"]


def test_public_questions_hide_answer_key():
    pub = public_questions()
    assert len(pub) == 20
    for q in pub:
        assert "correct_answer" not in q
        assert "explanation_en" not in q
        assert "explanation_zh" not in q
        # but still exposes what the frontend needs to render
        assert q["prompt_en"] and q["prompt_zh"]
        assert q["options_en"] and q["options_zh"]
        assert "critical" in q


def test_critical_question_ids_cover_the_five_required_concepts():
    flagged = {q["id"] for q in ONBOARDING_QUESTIONS if q["critical"]}
    assert set(CRITICAL_QUESTION_IDS) == flagged
    # the five auto-fail safety/documentation concepts
    assert flagged == {"q2", "q4", "q15", "q17", "q18"}
    for q in ONBOARDING_QUESTIONS:
        if q["critical"]:
            assert q["critical_concept"], f"{q['id']} missing critical_concept"


def test_onboarding_quiz_pass_threshold():
    # 16 correct, no critical misses -> passed
    answers = _correct_answers()
    for qid in _noncritical_ids()[:4]:
        answers[qid] = "Z"  # 4 non-critical wrong -> 16 correct
    result = score_onboarding_attempt(answers)
    assert result["score"] == 16
    assert result["total"] == 20
    assert result["passing_score"] == 16
    assert result["passed"] is True
    assert result["status"] == "passed"
    assert result["critical_misses"] == []


def test_onboarding_quiz_fails_below_threshold():
    answers = _correct_answers()
    for qid in _noncritical_ids()[:5]:
        answers[qid] = "Z"  # 5 non-critical wrong -> 15 correct
    result = score_onboarding_attempt(answers)
    assert result["score"] == 15
    assert result["passed"] is False
    assert result["status"] == "failed_score"
    assert result["critical_misses"] == []
    assert len(result["missed_questions"]) == 5


def test_onboarding_quiz_critical_auto_fail_even_with_high_score():
    # 19 correct but miss q2 (a critical concept) -> failed_critical
    answers = _correct_answers()
    answers["q2"] = "Z"
    result = score_onboarding_attempt(answers)
    assert result["score"] == 19
    assert result["passed"] is False
    assert result["status"] == "failed_critical"
    assert result["missed_questions"] == ["q2"]
    misses = result["critical_misses"]
    assert any(m["id"] == "q2" for m in misses)
    assert misses[0]["concept"]  # plain-language concept label present


def test_scoring_is_case_insensitive_and_treats_missing_as_wrong():
    lower = {q["id"]: str(q["correct_answer"]).lower() for q in ONBOARDING_QUESTIONS}
    assert score_onboarding_attempt(lower)["score"] == 20

    empty = score_onboarding_attempt({})
    assert empty["score"] == 0
    assert len(empty["missed_questions"]) == 20
    assert empty["status"] == "failed_critical"  # missing criticals fail hard
