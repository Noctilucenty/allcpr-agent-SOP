"""Redacted July 2026 ICPIS SOP structured source loader.

The staff-only DOCX stays local. This module only exposes the committed,
redacted JSON extraction: safe workflow sections, troubleshooting labels,
escalation matrix rows, and public figure metadata. Section 21 raw access
content is intentionally absent.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

PACKAGE_ROOT = Path(__file__).resolve().parent
STRUCTURED_PATH = PACKAGE_ROOT / "icpis_sop_structured.json"


@lru_cache(maxsize=1)
def load_icpis_sop() -> Dict[str, Any]:
    try:
        return json.loads(STRUCTURED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def section(name: str) -> Any:
    return (load_icpis_sop().get("sections") or {}).get(name)


def troubleshooting_phrases() -> List[str]:
    rows = section("troubleshooting_index") or []
    return [str(row.get("user_says", "")) for row in rows if isinstance(row, dict)]


def safe_ai_context() -> Dict[str, Any]:
    """Small allowlisted SOP context for AI intent/summary calls.

    This contains no operational-reference item values, no manager records, no
    answer keys, and no raw Section 21 content.
    """
    payload = load_icpis_sop()
    sections = payload.get("sections") or {}
    return {
        "version": payload.get("version", ""),
        "source_name": payload.get("source_name", ""),
        "redacted_for_repo": bool(payload.get("redacted_for_repo")),
        "section_titles": [
            "safety_rules",
            "staff_full_site_inspection",
            "student_quick_class_readiness",
            "table_station_setup",
            "tablet_power",
            "black_screen_app_load",
            "bluetooth_connection",
            "camera_browser_permission",
            "wifi_internet",
            "facility_power",
            "access_issue",
            "timer_logout_reset",
            "missing_supplies_dirty_damaged",
            "weekly_site_check_report",
            "new_site_assessment_reference",
            "business_trip_reference",
            "escalation_matrix",
            "troubleshooting_index",
        ],
        "troubleshooting_index": sections.get("troubleshooting_index", []),
        "escalation_matrix": sections.get("escalation_matrix", []),
        "safe_figures": sections.get("safe_figures", []),
        "redaction_boundary": {
            "raw_section_21_included": False,
            "ai_may_receive_access_codes": False,
            "ai_may_receive_staff_pin": False,
            "ai_may_receive_wifi_password": False,
        },
    }
