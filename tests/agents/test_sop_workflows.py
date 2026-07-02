"""Tests for the SOP library audit + step-by-step workflow conversion.

Covers the audit files, the ordered full-inspection workflow, the report-only
student quick check, the enriched inspection-reference endpoint, and the Q&A
routing for table/station and inspection-order questions — including that no
passcodes leak into any of it.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.agents.autocpr_site_manager import answer_question
from app.agents.autocpr_site_manager import sop_workflows
from app.agents.autocpr_site_manager.scenarios import SCENARIOS
from web_app import app

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOP_LIBRARY = PROJECT_ROOT / "SOP_library"
PKG = PROJECT_ROOT / "app" / "agents" / "autocpr_site_manager"
AUDIT_JSON = PKG / "sop_library_audit.json"
AUDIT_MD = SOP_LIBRARY / "AUDIT.md"
WORKFLOWS_JSON = PKG / "sop_workflows.json"
ICPIS_STRUCTURED_JSON = PKG / "icpis_sop_structured.json"


def _secret_tokens():
    """Derive the sensitive code/credential tokens from the committed operational
    refs (never hardcode secrets in this test file). Returns code-like tokens
    (4+ char digit runs and any word tokens from ``internal`` values) so the
    non-leak assertions have real secrets to guard against."""
    refs = json.loads((PKG / "sop_operational_refs.json").read_text(encoding="utf-8"))
    tokens: set[str] = set()
    for ref in refs.get("references", []):
        for item in ref.get("items", []):
            if (item.get("sensitivity") or "").lower() != "internal":
                continue
            val = str(item.get("value") or "")
            for m in re.findall(r"[A-Za-z0-9]{4,}", val):
                if any(ch.isdigit() for ch in m) or m.startswith("DoBe"):
                    tokens.add(m)
    return tokens


PASSCODES = _secret_tokens()


# ---- Part 1: audit files ---------------------------------------------------

def test_1_audit_md_exists():
    assert AUDIT_MD.exists(), "SOP_library/AUDIT.md must exist"
    assert AUDIT_MD.read_text(encoding="utf-8").strip()


def test_2_audit_json_exists():
    assert AUDIT_JSON.exists(), "sop_library_audit.json must exist"


def test_3_audit_includes_every_library_file():
    audited = {e["path"] for e in sop_workflows.audit_entries()}
    on_disk = {
        p.relative_to(PROJECT_ROOT).as_posix()
            for p in SOP_LIBRARY.rglob("*")
            # skip OS metadata / dotfiles (.DS_Store) and Word temp-lock files (~$...)
            # plus gitignored LOCAL-only credential/work-copy docs — they aren't
            # committed SOP documents
            if (
                p.is_file()
                and not p.name.startswith((".", "~$"))
                and ".LOCAL." not in p.name
                and "Staff Only SOP" not in p.name
            )
        }
    missing = on_disk - audited
    assert not missing, f"audit is missing files: {sorted(missing)}"


def test_4_each_entry_has_required_fields():
    for e in sop_workflows.audit_entries():
        for field in ("filename", "path", "category", "reason", "recommended_app_use"):
            assert e.get(field), f"{e.get('path')} missing {field}"
        assert e["category"] in {"active_workflow", "reference_template", "archive_only"}
        # Audit summary must never carry raw passcodes.
        blob = json.dumps(e, ensure_ascii=False)
        assert not any(code in blob for code in PASSCODES)


def test_5_inspection_sop_is_active_workflow():
    # Look up by the canonical 01_Core_SOPs path (the filename is not unique — a
    # duplicate copy may sit at the SOP_library root, classified archive_only).
    by_path = {e["path"]: e for e in sop_workflows.audit_entries()}
    insp = by_path["SOP_library/01_Core_SOPs/Smart Manikin 专员分点巡检 SOP.docx"]
    assert insp["category"] == "active_workflow"


def test_6_business_trip_forms_not_wired_into_inspection():
    entries = {e["path"]: e for e in sop_workflows.audit_entries()}
    trip_entries = [e for p, e in entries.items() if "03_Business_Trip_Forms/" in p]
    assert trip_entries, "expected business-trip form entries"
    for e in trip_entries:
        assert e["category"] == "reference_template"
        assert e["related_scenario"] != "smart_manikin_site_inspection"
        assert e["related_scenario"] == "business_trip_process"
    # And the reference-only business-trip workflow must not be wired into the UI
    # nor be part of the site inspection.
    trip_wf = sop_workflows.get_workflow("business_trip_process")
    assert trip_wf is not None
    assert trip_wf.get("wired_into_ui") is False
    assert trip_wf.get("not_part_of_site_inspection") is True
    # The full inspection workflow must not pull in any business-trip source file.
    full = sop_workflows.full_inspection_workflow()
    assert not any("Business_Trip" in s or "Business Trip" in s for s in full["source_files"])


# ---- Part 3: ordered workflows ---------------------------------------------

def test_7_workflows_file_and_module_exist():
    assert WORKFLOWS_JSON.exists()
    assert sop_workflows.list_workflows(), "workflows must load"


def test_all_workflow_scenarios_are_routable_contract_labels():
    missing = {
        wf["scenario"]
        for wf in sop_workflows.list_workflows()
        if wf.get("scenario") and wf["scenario"] not in SCENARIOS
    }
    assert missing == set()


def test_icpis_structured_source_exists_and_is_redacted():
    assert ICPIS_STRUCTURED_JSON.exists()
    payload = json.loads(ICPIS_STRUCTURED_JSON.read_text(encoding="utf-8"))
    assert payload["version"] == "Gosvea-2026-SOP-Auto CPR-ICPIS-01"
    assert payload["source_name"] == "AutoCPR ICPIS SOP 20260701"
    assert payload["staff_only_source"] is True
    assert payload["redacted_for_repo"] is True
    assert payload["raw_section_21_included"] is False
    blob = json.dumps(payload, ensure_ascii=False)
    assert not any(code in blob for code in PASSCODES)
    for forbidden in ("DoBeUSA", "DoBesince2016", "/Users/noctilucenteasteliq"):
        assert forbidden not in blob


def test_8_full_inspection_has_ordered_steps():
    full = sop_workflows.full_inspection_workflow()
    assert full is not None
    steps = full["steps"]
    assert len(steps) == 12
    # every step is a proper ordered tutorial entry
    for s in steps:
        assert s.get("id")
        assert s.get("title_en") and s.get("title_zh")
        assert isinstance(s.get("instructions_en"), list) and s["instructions_en"]
        for key in ("evidence_required", "if_problem", "do_not"):
            assert key in s
    assert full.get("requires_staff_pin") is True
    assert "student" in full.get("not_for", [])
    assert steps[0]["title_en"] == "Arrive and pause before touching setup"
    assert steps[1]["title_en"] == "Take before photos first"
    assert steps[2]["title_en"] == "Table / station pre-check"
    assert steps[9]["title_en"] == "Complete the Weekly Site Check Report"
    assert steps[10]["title_en"] == "Upload / report completion"
    assert steps[11]["title_en"] == "Final log"


def _step_index(steps, needle):
    for i, s in enumerate(steps):
        if needle in s["id"]:
            return i
    return -1


def test_9_before_photos_precede_cleaning_and_moving():
    steps = sop_workflows.full_inspection_workflow()["steps"]
    before = _step_index(steps, "before_photos")
    cleaning = _step_index(steps, "room_and_cleanliness")
    precheck = _step_index(steps, "table_station_precheck")
    assert before != -1 and cleaning != -1 and precheck != -1
    assert before < cleaning, "before photos must come before the cleaning step"
    assert before < precheck, "before photos must come before touching the station"
    # Step 1 must explicitly say not to clean/move before the before-photos.
    arrive = steps[0]
    do_not_blob = " ".join(arrive["do_not"]).lower()
    assert "clean" in do_not_blob or "move" in do_not_blob


def test_10_table_station_precheck_has_required_items():
    steps = sop_workflows.full_inspection_workflow()["steps"]
    precheck = steps[_step_index(steps, "table_station_precheck")]
    blob = " ".join(precheck["instructions_en"]).lower()
    for item in (
        "ipad",
        "smart manikin",
        "aed training pad",
        "consumables",
        "disinfecting wipes",
        "gloves",
        "mask adaptor",
        "pocket mask",
        "bvm",
        "connected to power",
    ):
        assert item in blob, f"table pre-check missing: {item}"


def test_11_missing_broken_items_reported_not_repaired():
    steps = sop_workflows.full_inspection_workflow()["steps"]
    precheck = steps[_step_index(steps, "table_station_precheck")]
    if_problem = " ".join(precheck["if_problem"]).lower()
    do_not = " ".join(precheck["do_not"]).lower()
    assert "photo" in if_problem
    assert "report" in if_problem
    assert "repair" in do_not or "dismantle" in do_not
    # No step anywhere should instruct the staffer to repair the device.
    for s in steps:
        instr = " ".join(s["instructions_en"]).lower()
        assert "dismantle the smart manikin" not in instr


def test_12_workflow_includes_after_photos():
    steps = sop_workflows.full_inspection_workflow()["steps"]
    assert _step_index(steps, "after_photos") != -1


def test_13_workflow_includes_weekly_site_check_report():
    steps = sop_workflows.full_inspection_workflow()["steps"]
    idx = _step_index(steps, "weekly_site_check_report")
    assert idx != -1
    blob = " ".join(steps[idx]["instructions_en"]).lower()
    assert "problems found" in blob and "actions taken" in blob


def test_14_workflow_includes_upload_materials():
    steps = sop_workflows.full_inspection_workflow()["steps"]
    idx = _step_index(steps, "upload_materials")
    assert idx != -1
    blob = " ".join(steps[idx]["instructions_en"]).lower()
    assert "before photos" in blob and "after photos" in blob


def test_15_student_quick_check_excludes_report_and_upload():
    quick = sop_workflows.student_quick_check_workflow()
    assert quick is not None
    assert quick.get("report_only") is True
    assert quick.get("no_pin_needed") is True
    assert "student" in quick.get("applies_to", [])
    assert len(quick.get("steps", [])) == 7
    excludes = " ".join(quick.get("excludes", [])).lower()
    assert "weekly site check report" in excludes
    assert "google drive upload" in excludes
    # The steps themselves must not instruct the report or a Google Drive upload
    # (the excludes list names them on purpose; the steps must not perform them).
    steps_blob = " ".join(
        " ".join(s.get("instructions_en", [])) for s in quick.get("steps", [])
    ).lower()
    assert "google drive" not in steps_blob
    assert "weekly site check report" not in steps_blob
    assert not any(code in json.dumps(quick, ensure_ascii=False) for code in PASSCODES)


def test_table_station_setup_structured_source_has_required_items_and_caution():
    payload = json.loads(ICPIS_STRUCTURED_JSON.read_text(encoding="utf-8"))
    setup = payload["sections"]["table_station_setup"]
    blob = json.dumps(setup, ensure_ascii=False).lower()
    for item in (
        "ipad", "manikins", "aed training pads", "consumables",
        "tissues / simulated gauze", "disinfecting wipes", "disposable gloves",
        "mask adaptors", "face shield optional", "pocket mask", "bvm",
        "power cables", "standard position",
    ):
        assert item in blob
    assert "do not repair or dismantle" in setup["caution"].lower()


def test_troubleshooting_structured_source_keeps_sop_boundaries():
    payload = json.loads(ICPIS_STRUCTURED_JSON.read_text(encoding="utf-8"))
    sections = payload["sections"]
    assert "No documented power" in json.dumps(sections["tablet_power"], ensure_ascii=False)
    assert "Reload / refresh once" in json.dumps(sections["black_screen_app_load"], ensure_ascii=False)
    assert "source-recorded manikin restart" in json.dumps(sections["bluetooth_connection"], ensure_ascii=False)
    assert "No documented device-session permission" in json.dumps(sections["camera_browser_permission"], ensure_ascii=False)
    assert "operate breakers" in json.dumps(sections["facility_power"], ensure_ascii=False)
    assert "Never reveal or guess codes" in json.dumps(sections["access_issue"], ensure_ascii=False)
    assert "ALLCPR support to confirm" in json.dumps(sections["timer_logout_reset"], ensure_ascii=False)
    assert "Promise or decide outcome" in json.dumps(sections["escalation_matrix"], ensure_ascii=False)


# ---- Part 4: inspection reference image metadata ---------------------------

def test_16_inspection_reference_has_metadata_and_caution():
    refs = sop_workflows.build_inspection_reference("en")
    assert refs, "expected at least one inspection reference"
    r = refs[0]
    for field in ("title", "image_path", "source", "use_for", "related_steps", "caution"):
        assert field in r, f"reference missing {field}"
    assert "do not repair" in r["caution"].lower()
    assert r["safe_to_show_to_students"] is True
    assert r["contains_access_info"] is False
    assert any("table_station_precheck" in s for s in r["related_steps"])
    # via the live endpoint too
    client = TestClient(app)
    resp = client.get("/api/inspection-reference")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload and "caution" in payload[0]
    assert "do not repair" in payload[0]["caution"].lower()


# ---- Part 5: Q&A routing ---------------------------------------------------

def _before_photos_first(step, zh):
    low = step.lower()
    if zh:
        return "巡检前照片" in step or "拍" in step
    return "before" in low and "photo" in low


def test_17_qa_table_returns_ordered_table_guidance():
    for q, zh in (
        ("what should be on the table", False),
        ("what should be on the desk", False),
        ("breathing bag thing missing", False),
        ("BVM missing", False),
        ("Pocket Mask missing", False),
        ("桌上应该有什么", True),
    ):
        a = answer_question(q)
        assert a.scenario == "smart_manikin_site_inspection"
        assert a.issue_subtype == "table_station_precheck"
        steps_blob = " ".join(a.steps).lower()
        # ordered: before photos first, then the item list
        assert _before_photos_first(a.steps[0], zh)
        items = ("ipad", "aed", "pocket mask", "bvm") if not zh else ("ipad", "aed", "pocket mask", "bvm")
        for item in items:
            assert item in steps_blob, f"missing {item} in table guidance"
        # if-problem / do-not-repair guidance present (bilingual)
        if zh:
            assert "上报" in " ".join(a.steps) or "报告" in " ".join(a.steps)
            assert "拆卸" in " ".join(a.steps) or "维修" in " ".join(a.steps)
        else:
            assert "report" in steps_blob
            assert "repair" in steps_blob or "dismantle" in steps_blob


def test_18_qa_order_returns_step_by_step_order():
    for q, zh in (("what order do I inspect", False), ("巡检顺序", True)):
        a = answer_question(q)
        assert a.scenario == "smart_manikin_site_inspection"
        assert a.issue_subtype == "inspection_order"
        assert len(a.steps) >= 10
        assert a.steps[0].startswith("1.")
        # before photos appear early in the ordered list (step 1 or 2)
        assert any(_before_photos_first(s, zh) for s in a.steps[:3])


def test_20_ipad_no_battery_returns_step_by_step():
    # English and Chinese battery/charge phrasing must route to the iPad power
    # sub-issue and return an ordered step-by-step (not just images), and must
    # not mis-route to a building power outage.
    for q, zh in (
        ("ipad no battery", False),
        ("iPad won't charge", False),
        ("ipad dead", False),
        ("tablet dead", False),
        ("tablet not turning on", False),
        ("tablet no power", False),
        ("平板没电", True),
        ("ipad没电", True),
        ("平板打不开", True),
    ):
        a = answer_question(q)
        assert a.scenario == "smart_manikin_troubleshooting", q
        assert a.smart_manikin_subissue == "ipad_pad_power_or_open", q
        assert len(a.steps) >= 4, q
        blob = " ".join(a.steps)
        if zh:
            assert "充电" in blob or "电源" in blob
            assert "上报" in blob or "升级" in blob  # report / escalate
            assert "拆" in blob or "维修" in blob      # do-not-repair
        else:
            low = blob.lower()
            assert "charg" in low or "power" in low
            assert "escalate" in low or "allcpr" in low
            assert "repair" in low or "reset" in low
    # a genuine building outage still routes to electricity_outage
    assert answer_question("教室没电了").scenario == "electricity_outage"


def test_new_troubleshooting_routes_match_icpis_sop():
    cases = [
        ("black tab", "black_screen_app_restart", ("reload", "no documented fix", "escalate")),
        ("camera permission denied", "camera_browser_permission", ("permission", "exact error", "escalate")),
        ("timer reset to 45 minutes", "timer_logout_reset", ("confirm", "normal", "ALLCPR")),
    ]
    for q, subissue, tokens in cases:
        a = answer_question(q, {"lang": "en"})
        assert a.scenario == "smart_manikin_troubleshooting"
        assert a.smart_manikin_subissue == subissue
        blob = " ".join(a.steps + a.do_not_decide_without_approval + a.contacts)
        for token in tokens:
            assert token.lower() in blob.lower()


def test_19_qa_does_not_expose_passcodes():
    for q in (
        "what should be on the table",
        "what order do I inspect",
        "桌上应该有什么",
        "巡检顺序",
        "equipment placement",
    ):
        a = answer_question(q)
        blob = a.answer + " " + " ".join(a.steps)
        assert not any(code in blob for code in PASSCODES), f"passcode leaked for: {q}"
