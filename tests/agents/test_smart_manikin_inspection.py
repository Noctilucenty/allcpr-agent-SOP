"""Tests for the Smart Manikin Site Representative Inspection SOP scenario."""
from __future__ import annotations

import pytest

from app.agents.autocpr_site_manager import answer_question
from app.agents.autocpr_site_manager.scenarios import classify
from app.agents.autocpr_site_manager import smart_manikin_inspection as smi

SCENARIO = "smart_manikin_site_inspection"


@pytest.mark.parametrize(
    "question",
    [
        "Smart Manikin 巡检怎么做",
        "巡检前要拍什么",
        "巡检后要做什么",
        "Weekly Site Check Report 怎么填",
        "设备坏了可以修吗",
        "器材摆放位置",
        "需要上传什么",
        "多久巡检一次",
        "现场要检查什么",
    ],
)
def test_inspection_questions_classify_to_inspection_scenario(question):
    assert classify(question) == SCENARIO


def test_inspection_overview_lists_full_workflow():
    ans = answer_question("Smart Manikin 巡检怎么做", {"lang": "en"})
    assert ans.scenario == SCENARIO
    joined = " ".join(ans.steps).lower()
    assert "before photo" in joined
    assert "after photo" in joined
    assert "weekly site check report" in joined
    assert "google drive" in joined


def test_inspection_frequency_answer():
    ans = answer_question("多久巡检一次", {"lang": "en"})
    assert ans.issue_subtype == smi.INSPECTION_FREQUENCY
    joined = " ".join(ans.steps).lower()
    assert "at least once per week" in joined
    assert "allcpr" in joined
    assert "complain" in joined
    assert "abnormality" in joined


def test_inspection_pre_check_photos_answer():
    ans = answer_question("巡检前要拍什么", {"lang": "en"})
    assert ans.issue_subtype == smi.PRE_CHECK_PHOTOS
    joined = " ".join(ans.steps).lower()
    for token in ("whole room", "smart manikin area", "supplies", "door or signage", "abnormal"):
        assert token in joined


def test_inspection_site_checklist_answer():
    ans = answer_question("现场要检查什么", {"lang": "en"})
    assert ans.issue_subtype == smi.SITE_CHECKLIST
    joined = " ".join(ans.steps).lower()
    for token in ("hygiene", "trash", "disinfect", "equipment", "access", "camera", "wi-fi", "signage", "safety"):
        assert token in joined


def test_inspection_equipment_answer_includes_devices_and_power_cable():
    ans = answer_question("inspection equipment check", {"lang": "en"})
    assert ans.issue_subtype == smi.EQUIPMENT_CHECK
    joined = " ".join(ans.steps)
    for token in ("Smart Manikin", "iPad", "AED Pads", "BVM", "Pocket Mask"):
        assert token in joined
    assert "power cable" in joined.lower()


def test_inspection_post_check_answer():
    ans = answer_question("巡检后要做什么", {"lang": "en"})
    assert ans.issue_subtype == smi.POST_CHECK_PHOTOS
    joined = " ".join(ans.steps).lower()
    assert "consistent" in joined  # similar angles
    assert "corrected result" in joined  # fixed-issue result photo


def test_inspection_upload_answer():
    ans = answer_question("需要上传什么", {"lang": "en"})
    assert ans.issue_subtype == smi.UPLOAD_MATERIALS
    joined = " ".join(ans.steps).lower()
    for token in ("before photos", "after photos", "weekly site check report", "issue photos", "google drive", "same day"):
        assert token in joined


def test_inspection_do_not_repair_answer():
    ans = answer_question("设备坏了可以修吗", {"lang": "en"})
    assert ans.issue_subtype == smi.DO_NOT_REPAIR
    blob = " ".join(ans.steps + ans.do_not_decide_without_approval).lower()
    assert "do not dismantle or repair" in blob
    for token in ("smart manikin", "ipad", "camera", "access control"):
        assert token in blob
    assert "report" in blob and "allcpr" in blob


def test_inspection_returns_source_backed_operational_refs():
    ans = answer_question("器材摆放位置", {"lang": "en"})
    ids = {ref.id for ref in ans.operational_references}
    assert "smart_manikin_site_inspection_equipment_placement" in ids
    assert all(ref.source_status == "official SOP source" for ref in ans.operational_references)
    joined = " ".join(item.value for ref in ans.operational_references for item in ref.items)
    for token in ("iPad", "AED Training Pads", "Pocket Mask", "BVM"):
        assert token in joined


def test_equipment_placement_answer_includes_diagram_labels():
    ans = answer_question("器材摆放位置", {"lang": "en"})
    steps = " ".join(ans.steps)
    assert "plugged in throughout the course" in steps
    assert "AED Training Pads" in steps
    assert "Pocket Mask" in steps


@pytest.mark.parametrize(
    "question, lang",
    [
        ("what should I do when I arrive", "en"),
        ("I arrived at the site, what now", "en"),
        ("arrival procedure", "en"),
        ("opening procedure", "en"),
        ("what do I check first", "en"),
        ("before I start", "en"),
        ("first thing to do", "en"),
        ("到场后要做什么", "zh"),
        ("我到分点了要干嘛", "zh"),
        ("开始前要做什么", "zh"),
        ("到店后流程", "zh"),
        ("专员到场流程", "zh"),
    ],
)
def test_arrival_procedure_routes_to_precheck(question, lang):
    ans = answer_question(question, {"lang": lang})
    assert ans.scenario == SCENARIO
    assert ans.issue_subtype == smi.PRE_CHECK_PHOTOS


def test_arrival_procedure_does_not_break_arrival_adjacent_scenarios():
    # Casual arrival phrasing must not steal these existing scenarios.
    assert classify("teacher did not arrive") == "instructor_no_show"
    assert classify("students arrived and class cannot start") == "class_cannot_start"


def test_arrival_answer_content_emphasizes_precheck_order():
    ans = answer_question("what should I do when I arrive", {"lang": "en"})
    blob = " ".join(ans.steps + ans.do_not_decide_without_approval + ans.contacts).lower()
    # before photos before any cleaning + the five required before photos
    assert "before any cleaning" in blob
    for token in ("whole room", "smart manikin area", "supplies / consumables area", "door or signage", "abnormal"):
        assert token in blob
    # continue the checklist after photos
    assert "continue the site checklist" in blob
    # do-not-repair and escalation
    assert "dismantle or repair" in blob
    assert "report to allcpr" in blob


def test_arrival_answer_content_chinese():
    ans = answer_question("到场后要做什么", {"lang": "zh"})
    blob = " ".join(ans.steps + ans.do_not_decide_without_approval + ans.contacts)
    assert "清洁" in blob  # before any cleaning
    for token in ("整个房间", "Smart Manikin 区域", "耗材", "门或路牌", "异常"):
        assert token in blob
    assert "现场检查清单" in blob
    assert "拆卸或维修" in blob
    assert "ALLCPR" in blob


def test_inspection_equipment_placement_returns_source_diagram():
    from app.agents.autocpr_site_manager.sop_media_index import build_media_index

    media = build_media_index()
    ans = answer_question("器材摆放位置")
    assert ans.scenario == SCENARIO
    if any("smart_manikin_site_inspection" in i.related_scenarios for i in media):
        assert ans.sop_images
        assert any("equipment placement diagram" in i.title for i in ans.sop_images)
        for i in ans.sop_images:
            assert i.url.startswith("/static/sop_media/")
            # source-only metadata: no image analysis, no local absolute paths
            assert "no image analysis" in i.description.lower()
            assert "/Users/" not in i.source_file


def test_inspection_answer_has_no_fine_or_penalty_wording():
    for q in ("Smart Manikin 巡检怎么做", "设备坏了可以修吗", "巡检前要拍什么"):
        for lang in ("en", "zh"):
            ans = answer_question(q, {"lang": lang})
            blob = ans.answer + " " + " ".join(ans.steps)
            for banned in ("fine", "penalty", "罚款", "扣款"):
                assert banned not in blob
