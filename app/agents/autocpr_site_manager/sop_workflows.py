"""Step-by-step SOP workflows + SOP-library audit access.

This module loads the reviewed JSON layers that turn the curated ``SOP_library``
into ordered operational workflows:

- ``sop_workflows.json``    — ordered tutorials (arrive -> before photos -> table
  pre-check -> ... -> report -> upload -> final log), plus image references.
- ``sop_library_audit.json``— machine-readable classification of every library
  file (active_workflow / reference_template / archive_only).

It also builds the enriched ``/api/inspection-reference`` payload: the equipment
placement diagram wrapped with title/source/use_for/related_steps and an explicit
"reference only; do not repair or dismantle" caution. It never OCRs or inspects
image pixels, and never emits passcodes.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

PACKAGE_ROOT = Path(__file__).resolve().parent
WORKFLOWS_PATH = PACKAGE_ROOT / "sop_workflows.json"
AUDIT_PATH = PACKAGE_ROOT / "sop_library_audit.json"

FULL_INSPECTION_ID = "smart_manikin_full_site_inspection"
STUDENT_QUICK_CHECK_ID = "student_quick_class_readiness_check"

# Caution shown with every inspection reference image so the diagram is never
# read as a repair instruction.
INSPECTION_REFERENCE_CAUTION = {
    "en": "Reference only; do not repair or dismantle equipment.",
    "zh": "仅供参考；请勿维修或拆卸设备。",
}


@lru_cache(maxsize=1)
def load_workflows() -> Dict[str, Any]:
    try:
        return json.loads(WORKFLOWS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


@lru_cache(maxsize=1)
def load_audit() -> Dict[str, Any]:
    try:
        return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def list_workflows() -> List[Dict[str, Any]]:
    return list(load_workflows().get("workflows", []) or [])


def get_workflow(workflow_id: str) -> Optional[Dict[str, Any]]:
    for wf in list_workflows():
        if wf.get("workflow_id") == workflow_id:
            return wf
    return None


def full_inspection_workflow() -> Optional[Dict[str, Any]]:
    return get_workflow(FULL_INSPECTION_ID)


def student_quick_check_workflow() -> Optional[Dict[str, Any]]:
    return get_workflow(STUDENT_QUICK_CHECK_ID)


def audit_entries() -> List[Dict[str, Any]]:
    return list(load_audit().get("entries", []) or [])


def image_references() -> List[Dict[str, Any]]:
    return list(load_workflows().get("image_references", []) or [])


def build_inspection_reference(lang: str = "en") -> List[Dict[str, Any]]:
    """Return the guided-inspection image reference(s), metadata only.

    Each item carries: title, image path/url, source, use_for, related_steps, and
    a caution. Backed by the committed SOP media index (the equipment placement
    diagram) so the app can explain what the picture is for and what to compare —
    never as repair instructions, and never emitting passcodes.
    """
    from .sop_media_index import find_relevant_sop_media

    caution = INSPECTION_REFERENCE_CAUTION.get(lang, INSPECTION_REFERENCE_CAUTION["en"])
    refs = {r.get("media_index_id"): r for r in image_references()}
    media = find_relevant_sop_media(
        "器材摆放 equipment placement supplies table station",
        "smart_manikin_site_inspection",
        top_k=3,
    )
    out: List[Dict[str, Any]] = []
    for item in media:
        data = item.model_dump() if hasattr(item, "model_dump") else item.dict()
        ref = refs.get(data.get("id"), {})
        out.append(
            {
                "title": data.get("title") or "Equipment placement reference",
                "image_path": data.get("url"),
                "url": data.get("url"),
                "source": data.get("source_file"),
                "use_for": ref.get(
                    "what_it_shows",
                    "Standard table/station placement reference for the site inspection.",
                ),
                "what_user_should_compare": ref.get(
                    "what_user_should_compare",
                    "Compare the actual station before moving anything.",
                ),
                "related_steps": [
                    "smart_manikin_full_site_inspection#step_3_table_station_precheck",
                    "smart_manikin_full_site_inspection#step_6_equipment_function_placement",
                ],
                "caution": caution,
            }
        )
    # Always guarantee at least the source-backed caption, even if the media index
    # is empty in a stripped deployment (so the UI/API contract never regresses).
    if not out and refs:
        ref = next(iter(refs.values()))
        out.append(
            {
                "title": "Smart Manikin 专员分点巡检 SOP — equipment placement diagram",
                "image_path": None,
                "url": None,
                "source": ref.get("source_file"),
                "use_for": ref.get("what_it_shows", ""),
                "what_user_should_compare": ref.get("what_user_should_compare", ""),
                "related_steps": [ref.get("related_workflow_step", "")],
                "caution": caution,
            }
        )
    return out
