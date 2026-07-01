"""Smart Manikin Site Representative Inspection SOP — loader, sub-issue routing,
focused Q&A guidance, and operational references.

All content is sourced from ``smart_manikin_site_inspection_sop.json`` (the
reviewed extraction of the official Word SOP). Nothing here invents steps, codes,
penalties, or rules beyond that source. The scenario is informational/checklist
guidance: it does not gate on human review.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schemas import OperationalReference, OperationalReferenceItem

SCENARIO = "smart_manikin_site_inspection"
ROUTE_DETAIL = "inspection"
SOURCE_STATUS = "official SOP source"

PACKAGE_ROOT = Path(__file__).resolve().parent
SOP_PATH = PACKAGE_ROOT / "smart_manikin_site_inspection_sop.json"

# --- sub-issue slugs --------------------------------------------------------
INSPECTION_FREQUENCY = "inspection_frequency"
PRE_CHECK_PHOTOS = "pre_check_photos"
SITE_CHECKLIST = "site_checklist"
EQUIPMENT_CHECK = "equipment_check"
ACCESS_CAMERA_WIFI = "access_camera_wifi_signage_safety"
POST_CHECK_PHOTOS = "post_check_photos"
WEEKLY_REPORT = "weekly_site_check_report"
UPLOAD_MATERIALS = "upload_materials"
DO_NOT_REPAIR = "do_not_repair"
ISSUE_ESCALATION = "issue_escalation"
EQUIPMENT_PLACEMENT = "equipment_placement"
TABLE_STATION_PRECHECK = "table_station_precheck"
INSPECTION_ORDER = "inspection_order"


@lru_cache(maxsize=1)
def load_sop() -> Dict[str, Any]:
    try:
        return json.loads(SOP_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _sec(key: str, lang: str) -> List[str]:
    """Return one localized section list from the SOP json."""
    block = load_sop().get(key) or {}
    if isinstance(block, dict):
        return list(block.get(lang) or block.get("en") or [])
    return []


# Ordered (subtype, terms) rules. First hit wins; ``do_not_repair`` and
# ``equipment_placement`` lead so they are not shadowed by the broad
# ``equipment`` / ``checklist`` terms.
_RULES = [
    (DO_NOT_REPAIR, (
        "可以修", "能修", "修吗", "维修", "不得维修", "不得拆卸", "拆卸",
        "坏了", "设备坏", "can i repair", "can i fix", "repair", "dismantle",
        "do not repair", "fix it myself",
    )),
    # Table / station pre-check ("what should be on the table") and inspection
    # order ("what order do I inspect") lead so they win over the broader
    # placement / checklist / arrival rules.
    (TABLE_STATION_PRECHECK, (
        "on the table", "on the station", "what's on the table", "whats on the table",
        "what should be on the table", "what should be on the station", "table setup",
        "table pre-check", "table precheck", "station pre-check", "station precheck",
        "table/station", "table / station", "桌上", "桌面", "桌子", "训练站",
        "桌上应该有什么", "桌上有什么", "桌面上有什么", "站点桌面",
    )),
    (INSPECTION_ORDER, (
        "what order", "in what order", "which order", "inspection order",
        "order do i inspect", "order to inspect", "sequence of", "sequence",
        "巡检顺序", "检查顺序", "步骤顺序", "先检查什么", "顺序是什么", "按什么顺序",
    )),
    (EQUIPMENT_PLACEMENT, (
        "器材摆放", "摆放位置", "摆放", "equipment placement", "placement",
        "where to place", "layout", "器材怎么摆", "怎么摆", "放哪里", "放哪儿",
        "放在哪", "ipad放哪", "aed放哪", "假人怎么摆", "where to put",
        "where should i put", "where does the ipad go", "where do the pads go",
        "setup layout", "station layout", "manikin layout",
        "how to set up the station", "how to arrange",
    )),
    (INSPECTION_FREQUENCY, (
        "多久", "频率", "几次", "how often", "frequency", "once a week",
        "once per week", "how frequently",
    )),
    (PRE_CHECK_PHOTOS, (
        "巡检前", "前照片", "before photo", "before-photo", "pre-check",
        "pre check", "precheck", "before cleaning",
        # Arrival / procedure / what-to-do phrasing defaults to the pre-check step.
        "when i arrive", "arrived at the site", "i arrived at", "arrival procedure",
        "opening procedure", "site procedure", "site rep procedure",
        "site representative procedure", "weekly check procedure",
        "smart manikin site procedure", "what do i check first",
        "what should i check first", "check first", "before i start",
        "start of inspection", "first thing to do", "first thing",
        "到场后", "到场流程", "专员到场", "到分点", "到店后", "到现场后",
        "开始前", "第一件事", "分点流程",
    )),
    (POST_CHECK_PHOTOS, (
        "巡检后", "后照片", "after photo", "after-photo", "post-check",
        "post check", "postcheck", "巡检后要", "做完巡检",
    )),
    (UPLOAD_MATERIALS, (
        "上传", "upload", "google drive", "drive 文件夹", "要传什么",
    )),
    (WEEKLY_REPORT, (
        "巡检表", "weekly site check report", "weekly report", "site check report",
        "怎么填", "填表", "fill the report",
    )),
    (EQUIPMENT_CHECK, (
        "设备", "器材", "equipment", "ipad", "aed", "bvm", "pocket mask",
        "电源线", "power cable",
    )),
    (ACCESS_CAMERA_WIFI, (
        "门禁", "摄像头", "camera", "监控", "wifi", "wi-fi", "网络", "network",
        "路牌", "指示牌", "signage", "安全隐患", "安全", "access code", "lockbox",
    )),
    (SITE_CHECKLIST, (
        "现场检查", "现场要检查", "检查什么", "检查项", "site checklist", "checklist",
        "check items", "what to check", "现场检查项",
        # cleaning / supplies / consumables map to the site checklist
        "trash", "empty trash", "no wipes", "out of wipes", "no gloves",
        "out of gloves", "supplies", "restock", "dirty room", "room is dirty",
        "need disinfect", "need to clean", "mask adapter", "mask adaptor",
        "垃圾", "倒垃圾", "没有湿巾", "没有手套", "耗材", "补货", "房间很脏",
        "房间脏", "需要打扫", "面罩转接头",
    )),
    (ISSUE_ESCALATION, (
        "无法解决", "解决不了", "上报", "report to allcpr", "escalate", "cannot fix",
        "can't fix", "现场不能解决",
    )),
]


def detect_inspection_subtype(question: str) -> str:
    """Return a focused inspection sub-issue slug, or '' for the overview."""
    text = (question or "").casefold()
    for subtype, terms in _RULES:
        if any(term in text for term in terms):
            return subtype
    return ""


def focused_guidance(subtype: str, lang: str) -> Optional[Dict[str, Any]]:
    """Return focused field overrides for an inspection sub-issue, or None."""
    if not subtype:
        return None
    zh = lang == "zh"

    def lead(en: str, zh_text: str) -> str:
        return zh_text if zh else en

    if subtype == INSPECTION_FREQUENCY:
        return {
            "lead": lead(
                "Inspection frequency per the SOP.",
                "巡检频率（依据 SOP）。",
            ),
            "steps": _sec("frequency", lang),
            "next_actions": _sec("frequency", lang),
        }
    if subtype == PRE_CHECK_PHOTOS:
        # Arrival / pre-check order: check the site and photograph it BEFORE any
        # cleaning, then continue the checklist, fix on-site only, escalate the
        # rest, and finish with after photos + report + upload.
        dont_first = lead(
            "Do not clean, move, organize, or fix anything first — first check the overall site condition.",
            "先不要清洁、搬动、整理或修理任何东西——先检查整体现场情况。",
        )
        checklist_line = lead(
            "Then continue the site checklist: hygiene, trash, disinfection supplies, "
            "equipment, access/Lockbox/Access Code, camera, Wi-Fi, signage, and safety hazards.",
            "然后继续现场检查清单：卫生、垃圾、消毒用品、设备、门禁/Lockbox/Access Code、"
            "摄像头、Wi-Fi、路牌、安全隐患。",
        )
        after_line = lead(
            "After work is complete, take after photos from similar angles, then complete the "
            "Weekly Site Check Report and upload materials to the corresponding site Google Drive folder.",
            "完成后，从相近角度拍巡检后照片，再填写每周分点巡检表并上传资料到对应分点 Google Drive 文件夹。",
        )
        steps = [dont_first] + _sec("pre_check_photos", lang) + [checklist_line]
        steps += _sec("on_site_handling", lang) + [after_line]
        return {
            "lead": lead(
                "On arrival, do not clean or organize first — check the overall site, then take "
                "before photos before any cleaning.",
                "到场后先不要清洁或整理——先检查整体现场，再在任何清洁前拍巡检前照片。",
            ),
            "steps": steps,
            "contacts": [lead("ALLCPR (report unresolved issues).", "ALLCPR（上报无法解决的问题）。")],
            "do_not_decide_without_approval": [
                lead(
                    "Do not dismantle or repair Smart Manikin, iPad, camera, access control, or similar equipment without authorization.",
                    "未经授权不得拆卸或维修 Smart Manikin、iPad、摄像头、门禁或类似设备。",
                ),
                lead(
                    "Inspection records and photos must be real and complete.",
                    "巡检记录和照片必须真实、完整。",
                ),
            ],
            "next_actions": [
                lead("Take before photos before any cleaning.", "在任何清洁前先拍巡检前照片。"),
                lead(
                    "Continue the site checklist, then after photos, report, and upload.",
                    "继续现场检查清单，再拍巡检后照片、填表并上传。",
                ),
            ],
        }
    if subtype == SITE_CHECKLIST:
        return {
            "lead": lead(
                "Check items per the Weekly Site Check Report.",
                "按每周分点巡检表逐项检查。",
            ),
            "steps": _sec("site_checklist", lang),
        }
    if subtype == EQUIPMENT_CHECK:
        items = [s for s in _sec("site_checklist", lang) if _is_equipment_line(s)]
        return {
            "lead": lead(
                "Equipment and power check.",
                "设备与供电检查。",
            ),
            "steps": items or _sec("equipment_placement", lang),
        }
    if subtype == ACCESS_CAMERA_WIFI:
        items = [s for s in _sec("site_checklist", lang) if _is_environment_line(s)]
        return {
            "lead": lead(
                "Access, camera, Wi-Fi, signage, and safety checks.",
                "门禁、摄像头、Wi-Fi、路牌与安全检查。",
            ),
            "steps": items,
        }
    if subtype == POST_CHECK_PHOTOS:
        steps = list(_sec("post_check_photos", lang))
        steps += _sec("weekly_site_check_report", lang)[:1]
        steps += _sec("upload_materials", lang)[:1]
        return {
            "lead": lead(
                "After all inspection and cleaning is done, take after photos, "
                "fill the Weekly Site Check Report, and upload materials.",
                "完成所有巡检与清洁后，拍巡检后照片、填写每周分点巡检表并上传资料。",
            ),
            "steps": steps,
            "next_actions": _sec("upload_materials", lang),
        }
    if subtype == WEEKLY_REPORT:
        return {
            "lead": lead(
                "Complete the Weekly Site Check Report after inspection.",
                "巡检后填写每周分点巡检表。",
            ),
            "steps": _sec("weekly_site_check_report", lang),
        }
    if subtype == UPLOAD_MATERIALS:
        return {
            "lead": lead(
                "Upload materials to the corresponding site Google Drive folder.",
                "上传资料到对应分点的 Google Drive 文件夹。",
            ),
            "steps": _sec("upload_materials", lang),
            "next_actions": _sec("upload_materials", lang),
        }
    if subtype == DO_NOT_REPAIR:
        steps = _sec("do_not_repair", lang)
        return {
            "lead": lead(
                "Do not dismantle or repair equipment without authorization; "
                "report unresolved issues to ALLCPR.",
                "未经授权不得拆卸或维修设备；无法解决的问题上报 ALLCPR。",
            ),
            "steps": steps,
            "contacts": [lead("ALLCPR (report unresolved equipment issues).", "ALLCPR（上报无法解决的设备问题）。")],
            "do_not_decide_without_approval": [
                lead(
                    "Do not dismantle or repair Smart Manikin, iPad, camera, access control, or similar equipment without authorization.",
                    "未经授权不得拆卸或维修 Smart Manikin、iPad、摄像头、门禁或类似设备。",
                ),
                lead(
                    "Do not improvise undocumented repairs.",
                    "不要进行未记录的临时维修。",
                ),
            ],
            "next_actions": [
                lead("Take photos and report to ALLCPR.", "拍照并上报 ALLCPR。"),
            ],
        }
    if subtype == ISSUE_ESCALATION:
        return {
            "lead": lead(
                "Fix what you can on site; photo and report what you cannot to ALLCPR.",
                "能现场解决的立即处理；无法解决的拍照并上报 ALLCPR。",
            ),
            "steps": _sec("on_site_handling", lang),
            "contacts": [lead("ALLCPR (report unresolved issues).", "ALLCPR（上报无法解决的问题）。")],
            "next_actions": _sec("on_site_handling", lang),
        }
    if subtype == EQUIPMENT_PLACEMENT:
        return {
            "lead": lead(
                "Equipment placement (page-3 diagram). Source-backed labels only.",
                "器材摆放（第 3 页图）。仅使用来源支持的标签。",
            ),
            "steps": _sec("equipment_placement", lang),
        }
    if subtype == TABLE_STATION_PRECHECK:
        block = load_sop().get("table_station_precheck", {})
        intro = block.get("intro_zh" if zh else "intro_en", "")
        if_problem = block.get("if_problem_zh" if zh else "if_problem_en", "")
        dont_move = lead(
            "Before moving anything, take before photos — do not clean, move, or organize first.",
            "移动任何东西前，先拍巡检前照片——不要先清洁、搬动或整理。",
        )
        compare = lead(
            "Use the table/station placement reference to compare these items:",
            "用桌面/训练站摆放参考对比以下物品：",
        )
        steps = [dont_move, compare] + _sec("table_station_precheck", lang)
        if if_problem:
            steps.append(if_problem)
        return {
            "lead": intro or lead(
                "Table/station pre-check: before moving anything, take before photos, then compare the station against the standard placement reference.",
                "桌面/训练站预检查：移动任何东西前先拍巡检前照片，再与标准摆放参考对比。",
            ),
            "steps": steps,
            "contacts": [lead("ALLCPR (report unresolved / missing items).", "ALLCPR（上报无法解决或缺失的物品）。")],
            "do_not_decide_without_approval": [
                lead(
                    "Do not invent a replacement or repair; do not dismantle the Smart Manikin / iPad.",
                    "不要臆造替代品或维修；不要拆卸 Smart Manikin / iPad。",
                ),
                lead(
                    "The placement diagram is a reference only — not repair instructions.",
                    "摆放图仅供参考——不是维修说明。",
                ),
            ],
            "next_actions": [
                lead("Mark each item Present / Missing / Problem, then continue the checklist.",
                     "逐项标记在场 / 缺失 / 问题，再继续检查清单。"),
                lead("Photograph, note, and report any missing or broken item to ALLCPR.",
                     "对任何缺失或损坏的物品拍照、记录并上报 ALLCPR。"),
            ],
        }
    if subtype == INSPECTION_ORDER:
        return {
            "lead": lead(
                "Inspection order (per the SOP). Take before photos before cleaning or moving anything, then work through the steps in order.",
                "巡检顺序（依据 SOP）。在清洁或移动任何东西前先拍巡检前照片，再按顺序逐步完成。",
            ),
            "steps": _ordered_step_titles(lang),
            "next_actions": [
                lead("Start with before photos, then the table/station pre-check.",
                     "先拍巡检前照片，再做桌面/训练站预检查。"),
            ],
        }
    return None


def _ordered_step_titles(lang: str) -> List[str]:
    """Return the numbered full-inspection step titles from the workflow layer."""
    from . import sop_workflows

    wf = sop_workflows.full_inspection_workflow() or {}
    key = "title_zh" if lang == "zh" else "title_en"
    titles = []
    for i, step in enumerate(wf.get("steps", []) or [], start=1):
        title = step.get(key) or step.get("title_en") or step.get("id", "")
        titles.append(f"{i}. {title}")
    return titles


def _is_equipment_line(line: str) -> bool:
    low = line.casefold()
    if any(k in low for k in ("disinfect", "消毒", "safety", "安全", "hygiene", "卫生")):
        return False
    return any(k in low for k in ("equipment", "power", "设备", "供电", "ipad", "manikin"))


def _is_environment_line(line: str) -> bool:
    low = line.casefold()
    return any(
        k in low
        for k in (
            "access", "camera", "network", "wi-fi", "wifi", "signage", "safety",
            "门禁", "摄像头", "网络", "路牌", "安全",
        )
    )


def inspection_operational_references(question: str, lang: str) -> List[OperationalReference]:
    """Return source-backed operational references for the inspection scenario."""
    zh = lang == "zh"
    sop = load_sop()
    title_workflow = (
        "Smart Manikin 分点巡检 — 工作流程"
        if zh
        else "Smart Manikin site inspection — workflow"
    )
    title_placement = (
        "Smart Manikin 分点巡检 — 器材摆放"
        if zh
        else "Smart Manikin site inspection — equipment placement"
    )

    def item(label_en: str, label_zh: str, value: str) -> OperationalReferenceItem:
        return OperationalReferenceItem(
            label=label_zh if zh else label_en,
            value=value,
            sensitivity="normal",
            fact_type="inspection",
        )

    freq = "；".join(_sec("frequency", lang)) if zh else "; ".join(_sec("frequency", lang))
    report_form = sop.get("record_form_zh" if zh else "record_form_en", "")
    workflow = OperationalReference(
        id="smart_manikin_site_inspection_overview",
        title=title_workflow,
        scenario=SCENARIO,
        source_status=SOURCE_STATUS,
        priority=20,
        items=[
            item("Frequency", "频率", freq),
            item(
                "Record form",
                "记录表",
                report_form,
            ),
            item(
                "Before photos",
                "巡检前照片",
                _join(_sec("pre_check_photos", lang)[1:5], zh),
            ),
            item(
                "After photos",
                "巡检后照片",
                _join(_sec("post_check_photos", lang)[2:6], zh),
            ),
            item(
                "Upload",
                "上传",
                _join(_sec("upload_materials", lang)[1:5], zh),
            ),
        ],
        media_tags=["巡检", "inspection", "weekly site check"],
        do_not=list(_sec("do_not_repair", lang)[:2]),
    )

    placement_block = sop.get("equipment_placement", {})
    placement = OperationalReference(
        id="smart_manikin_site_inspection_equipment_placement",
        title=title_placement,
        scenario=SCENARIO,
        source_status=SOURCE_STATUS,
        priority=10,
        items=[
            item(
                "Equipment placement",
                "器材摆放",
                _join(_sec("equipment_placement", lang), zh),
            ),
            item(
                "Source note",
                "来源说明",
                placement_block.get("source_note_zh" if zh else "source_note_en", ""),
            ),
        ],
        media_tags=["equipment", "placement", "器材", "摆放", "巡检"],
        do_not=[],
    )
    return [workflow, placement]


def _join(items: List[str], zh: bool) -> str:
    sep = "；" if zh else "; "
    return sep.join(s.rstrip("。.") for s in items if s)
