"""Tests for onboarding-attempt storage (JSONL, mirrors inspection_logs)."""
from __future__ import annotations

import pytest

from app.agents.autocpr_site_manager.onboarding_attempts import (
    append_onboarding_attempt,
    build_onboarding_attempt,
    list_onboarding_attempts,
)
from app.agents.autocpr_site_manager.onboarding_quiz import ONBOARDING_QUESTIONS


@pytest.fixture(autouse=True)
def isolated_attempt_path(monkeypatch, tmp_path):
    monkeypatch.setenv(
        "ALLCPR_ONBOARDING_ATTEMPT_PATH", str(tmp_path / "onboarding_attempts.jsonl")
    )


def _correct_answers() -> dict:
    return {q["id"]: q["correct_answer"] for q in ONBOARDING_QUESTIONS}


def test_build_attempt_rescoring_ignores_client_supplied_score():
    # A malicious client claims a perfect pass but answers nothing.
    payload = {
        "staff": "Alex",
        "site": "Santa Clara",
        "language": "en",
        "answers": {},
        "score": 20,          # must be ignored
        "passed": True,       # must be ignored
        "status": "passed",   # must be ignored
    }
    entry = build_onboarding_attempt(payload)
    assert entry["log_type"] == "onboarding_attempt"
    assert entry["score"] == 0            # recomputed from (empty) answers
    assert entry["passed"] is False
    assert entry["status"] == "failed_critical"
    assert entry["total"] == 20
    assert entry["passing_score"] == 16


def test_append_and_list_newest_first():
    first = append_onboarding_attempt(
        {"staff": "Alex", "site": "Santa Clara", "language": "en", "answers": _correct_answers()}
    )
    second = append_onboarding_attempt(
        {"staff": "Bao", "site": "Newark", "language": "zh", "answers": {}}
    )
    assert first["passed"] is True and first["status"] == "passed"
    assert second["passed"] is False

    listed = list_onboarding_attempts(limit=10)
    assert listed[0]["id"] == second["id"]   # newest first
    assert listed[1]["id"] == first["id"]
    assert listed[0]["staff"] == "Bao"


def test_attempt_does_not_store_local_paths_or_private_usernames():
    entry = append_onboarding_attempt(
        {
            "staff": "/Users/noctilucenteasteliq/Desktop/Developer/allcpr_agent",
            "site": "/Users/noctilucenteasteliq/sites/santa_clara",
            "language": "en",
            "answers": _correct_answers(),
        }
    )
    blob = str(list_onboarding_attempts())
    assert "/Users/" not in blob
    assert "noctilucenteasteliq" not in blob
    assert "/Desktop/Developer/" not in blob
    # sanity: the entry itself is what we listed
    assert entry["id"] in blob


def test_attempt_never_stores_image_bytes_or_raw_files():
    entry = build_onboarding_attempt(
        {
            "staff": "Alex",
            "site": "Santa Clara",
            "language": "en",
            "answers": _correct_answers(),
            "photo_bytes": "data:image/png;base64,AAAA",  # should be dropped
        }
    )
    assert "photo_bytes" not in entry
    # only a small, known set of keys is persisted
    assert set(entry) == {
        "id", "log_type", "created_at", "language", "staff", "site", "answers",
        "score", "total", "passing_score", "passed", "status",
        "missed_questions", "critical_misses",
    }
