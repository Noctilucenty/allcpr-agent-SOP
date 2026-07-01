"""Smart Manikin Site Representative onboarding certification quiz.

Operational-readiness test (not a school quiz): 20 questions drawn only from the
official Smart Manikin Site Representative Inspection SOP and the operational
rules already encoded in this repo (see ``sop.md``,
``smart_manikin_site_inspection_sop.json`` and the guided-inspection copy in
``app/web/site_ops_agent.html``).

The correct answers, explanations and critical-concept flags live here on the
server. ``public_questions()`` returns a copy with the answer key stripped so the
frontend can render the test without leaking it. ``score_onboarding_attempt()`` is
the single source of truth for pass/fail — the frontend never decides.

Rules:
* total = 20, passing score = 16
* five questions are ``critical``: missing any one is an automatic fail even at a
  passing score (before-photos-first, no staged photos, safety hazards, reporting
  unresolved issues, and no unauthorized repair).
"""
from __future__ import annotations

from typing import Any, Dict, List

TOTAL_QUESTIONS = 20
PASSING_SCORE = 16

# Keys that must never be exposed to the browser via /api/onboarding-quiz.
_ANSWER_KEY_FIELDS = ("correct_answer", "explanation_en", "explanation_zh")

ONBOARDING_QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": "q1",
        "type": "multiple_choice",
        "critical": False,
        "critical_concept": "",
        "prompt_en": "How often should each Smart Manikin site be inspected?",
        "prompt_zh": "每个 Smart Manikin 分点应该多久巡检一次？",
        "options_en": [
            "A. Once per month",
            "B. At least once per week",
            "C. Only when students complain",
            "D. Only before large classes",
        ],
        "options_zh": [
            "A. 每月一次",
            "B. 至少每周一次",
            "C. 只有学生投诉时",
            "D. 只有大课前",
        ],
        "correct_answer": "B",
        "explanation_en": "Each site should be inspected at least once per week.",
        "explanation_zh": "每个分点至少每周巡检一次。",
    },
    {
        "id": "q2",
        "type": "multiple_choice",
        "critical": True,
        "critical_concept": "before photos before cleaning",
        "prompt_en": "What is the first thing you must do before cleaning, moving, "
        "fixing, or organizing anything at the site?",
        "prompt_zh": "到达分点后，在清洁、移动、修理或整理任何东西之前，第一件事是什么？",
        "options_en": [
            "A. Empty the trash",
            "B. Turn on the iPad",
            "C. Take before photos",
            "D. Call the supervisor",
        ],
        "options_zh": [
            "A. 倒垃圾",
            "B. 打开 iPad",
            "C. 拍巡检前照片",
            "D. 打电话给主管",
        ],
        "correct_answer": "C",
        "explanation_en": "Before photos must be taken before any cleaning, moving, "
        "fixing, or organizing.",
        "explanation_zh": "必须先拍巡检前照片，再进行任何清洁、移动、修理或整理。",
    },
    {
        "id": "q3",
        "type": "multiple_choice",
        "critical": False,
        "critical_concept": "",
        "prompt_en": "Which areas should be included in before photos?",
        "prompt_zh": "巡检前照片应该包含哪些区域？",
        "options_en": [
            "A. Whole room",
            "B. Smart Manikin area",
            "C. Supplies/consumables area",
            "D. Door/signage",
            "E. Problem areas if any",
            "F. All of the above",
        ],
        "options_zh": [
            "A. 整个房间",
            "B. Smart Manikin 区域",
            "C. 用品/耗材区域",
            "D. 门口/路牌",
            "E. 如有问题，拍问题区域",
            "F. 以上全部",
        ],
        "correct_answer": "F",
        "explanation_en": "Before photos should document the full site condition "
        "before work starts.",
        "explanation_zh": "巡检前照片要记录开始工作前的完整现场状态。",
    },
    {
        "id": "q4",
        "type": "true_false",
        "critical": True,
        "critical_concept": "no old/fake/staged photos",
        "prompt_en": "It is acceptable to use old photos if the site looks the same.",
        "prompt_zh": "如果分点看起来差不多，可以使用旧照片。",
        "options_en": ["A. True", "B. False"],
        "options_zh": ["A. 对", "B. 错"],
        "correct_answer": "B",
        "explanation_en": "Inspection photos must be real, current, and complete. Old "
        "or staged photos are not acceptable.",
        "explanation_zh": "巡检照片必须真实、当前、完整。不能使用旧照片或摆拍替代照片。",
    },
    {
        "id": "q5",
        "type": "multiple_choice",
        "critical": False,
        "critical_concept": "",
        "prompt_en": "Which items are part of the hygiene/site condition check?",
        "prompt_zh": "哪些属于卫生/现场状态检查？",
        "options_en": [
            "A. Overall cleanliness",
            "B. Trash",
            "C. Floor condition",
            "D. All of the above",
        ],
        "options_zh": [
            "A. 整体清洁",
            "B. 垃圾",
            "C. 地面情况",
            "D. 以上全部",
        ],
        "correct_answer": "D",
        "explanation_en": "Hygiene includes overall cleanliness, trash, floor "
        "condition, and visible cleanliness issues.",
        "explanation_zh": "卫生检查包括整体清洁、垃圾、地面情况和明显清洁问题。",
    },
    {
        "id": "q6",
        "type": "multiple_choice",
        "critical": False,
        "critical_concept": "",
        "prompt_en": "What should you do with the trash can during inspection?",
        "prompt_zh": "巡检时垃圾桶应该怎么处理？",
        "options_en": [
            "A. Ignore it unless it is completely full",
            "B. Empty it and replace the trash bag if needed",
            "C. Only take a photo",
            "D. Ask students to handle it",
        ],
        "options_zh": [
            "A. 除非完全满了，否则不用管",
            "B. 倒垃圾，必要时更换垃圾袋",
            "C. 只拍照",
            "D. 让学生处理",
        ],
        "correct_answer": "B",
        "explanation_en": "Trash should be checked, emptied, and handled as part of "
        "site care.",
        "explanation_zh": "垃圾需要检查、清理，并作为分点维护的一部分处理。",
    },
    {
        "id": "q7",
        "type": "multiple_choice",
        "critical": False,
        "critical_concept": "",
        "prompt_en": "What must be disinfected during site care?",
        "prompt_zh": "分点维护时哪些需要消毒？",
        "options_en": [
            "A. Only the table",
            "B. Only the iPad",
            "C. Teaching equipment and commonly used training items",
            "D. Only visibly dirty items",
        ],
        "options_zh": [
            "A. 只有桌子",
            "B. 只有 iPad",
            "C. 教学设备和常用训练物品",
            "D. 只有看起来脏的物品",
        ],
        "correct_answer": "C",
        "explanation_en": "Teaching equipment and commonly used training items should "
        "be disinfected.",
        "explanation_zh": "教学设备和常用训练物品都应消毒。",
    },
    {
        "id": "q8",
        "type": "multiple_choice",
        "critical": False,
        "critical_concept": "",
        "prompt_en": "How much disinfecting supply should be available?",
        "prompt_zh": "消毒用品应该准备多少？",
        "options_en": [
            "A. Enough for one class",
            "B. Enough for one day",
            "C. Enough for one week",
            "D. No required amount",
        ],
        "options_zh": [
            "A. 足够一节课",
            "B. 足够一天",
            "C. 足够一周",
            "D. 没有要求",
        ],
        "correct_answer": "C",
        "explanation_en": "Supplies should be sufficient for one week.",
        "explanation_zh": "用品应足够一周使用。",
    },
    {
        "id": "q9",
        "type": "multiple_choice",
        "critical": False,
        "critical_concept": "",
        "prompt_en": "Which equipment must be checked for completeness and correct "
        "placement?",
        "prompt_zh": "哪些设备需要检查是否完整并摆放正确？",
        "options_en": [
            "A. Smart Manikin",
            "B. iPad",
            "C. AED pads",
            "D. BVM",
            "E. Pocket Mask",
            "F. All of the above",
        ],
        "options_zh": [
            "A. Smart Manikin",
            "B. iPad",
            "C. AED pads",
            "D. BVM",
            "E. Pocket Mask",
            "F. 以上全部",
        ],
        "correct_answer": "F",
        "explanation_en": "The station should have all required training equipment "
        "complete and in the correct place.",
        "explanation_zh": "分点应确保所有必需训练设备完整并放在正确位置。",
    },
    {
        "id": "q10",
        "type": "true_false",
        "critical": False,
        "critical_concept": "",
        "prompt_en": "The iPad and Smart Manikin should be connected to power cables.",
        "prompt_zh": "iPad 和 Smart Manikin 应该连接电源线。",
        "options_en": ["A. True", "B. False"],
        "options_zh": ["A. 对", "B. 错"],
        "correct_answer": "A",
        "explanation_en": "Power connection is part of the equipment check.",
        "explanation_zh": "电源连接是设备检查的一部分。",
    },
    {
        "id": "q11",
        "type": "multiple_choice",
        "critical": False,
        "critical_concept": "",
        "prompt_en": "What should you confirm about the camera?",
        "prompt_zh": "摄像头需要确认什么？",
        "options_en": [
            "A. It is physically present only",
            "B. It is online",
            "C. It is turned away for privacy",
            "D. It does not need checking",
        ],
        "options_zh": [
            "A. 只要实物在就可以",
            "B. 确认在线",
            "C. 转向一边保护隐私",
            "D. 不需要检查",
        ],
        "correct_answer": "B",
        "explanation_en": "The camera should be checked to confirm it is online.",
        "explanation_zh": "摄像头需要确认在线。",
    },
    {
        "id": "q12",
        "type": "multiple_choice",
        "critical": False,
        "critical_concept": "",
        "prompt_en": "What should you confirm about Wi-Fi?",
        "prompt_zh": "Wi-Fi 需要确认什么？",
        "options_en": [
            "A. Wi-Fi is normal",
            "B. Wi-Fi does not matter",
            "C. Only students need Wi-Fi",
            "D. Check only if someone complains",
        ],
        "options_zh": [
            "A. Wi-Fi 正常",
            "B. Wi-Fi 不重要",
            "C. 只有学生需要 Wi-Fi",
            "D. 只有有人投诉才检查",
        ],
        "correct_answer": "A",
        "explanation_en": "Wi-Fi should be checked as part of site readiness.",
        "explanation_zh": "Wi-Fi 是分点可用性检查的一部分。",
    },
    {
        "id": "q13",
        "type": "multiple_choice",
        "critical": False,
        "critical_concept": "",
        "prompt_en": "Which access items should be checked?",
        "prompt_zh": "哪些门禁/进入相关项目需要检查？",
        "options_en": [
            "A. Door access",
            "B. Lockbox",
            "C. Access code",
            "D. All of the above",
        ],
        "options_zh": [
            "A. 门禁/门口进入",
            "B. Lockbox",
            "C. Access Code",
            "D. 以上全部",
        ],
        "correct_answer": "D",
        "explanation_en": "Door access, lockbox, and access code are all part of site "
        "access readiness.",
        "explanation_zh": "门禁、Lockbox 和 Access Code 都属于分点进入条件检查。",
    },
    {
        "id": "q14",
        "type": "multiple_choice",
        "critical": False,
        "critical_concept": "",
        "prompt_en": "What should you check about signs/signage?",
        "prompt_zh": "路牌/标识需要检查什么？",
        "options_en": [
            "A. They are complete and clear",
            "B. They are decorative only",
            "C. They are hidden",
            "D. They are only needed during exams",
        ],
        "options_zh": [
            "A. 完整且清楚",
            "B. 只是装饰",
            "C. 应该藏起来",
            "D. 只有考试时需要",
        ],
        "correct_answer": "A",
        "explanation_en": "Signage should be complete and clear for students and "
        "staff.",
        "explanation_zh": "路牌/标识应完整清楚，方便学生和员工识别。",
    },
    {
        "id": "q15",
        "type": "multiple_choice",
        "critical": True,
        "critical_concept": "safety hazards",
        "prompt_en": "Which safety hazards must be checked?",
        "prompt_zh": "哪些安全隐患需要检查？",
        "options_en": [
            "A. Water hazards",
            "B. Electrical hazards",
            "C. Equipment hazards",
            "D. All visible safety hazards",
        ],
        "options_zh": [
            "A. 水渍/漏水隐患",
            "B. 用电隐患",
            "C. 设备隐患",
            "D. 所有可见安全隐患",
        ],
        "correct_answer": "D",
        "explanation_en": "All visible safety hazards should be checked and handled or "
        "reported.",
        "explanation_zh": "所有可见安全隐患都需要检查，并处理或上报。",
    },
    {
        "id": "q16",
        "type": "multiple_choice",
        "critical": False,
        "critical_concept": "",
        "prompt_en": "If you find a simple issue that can be safely fixed on site, what "
        "should you do?",
        "prompt_zh": "如果发现一个可以现场安全解决的小问题，应该怎么做？",
        "options_en": [
            "A. Leave it for the next inspector",
            "B. Fix it immediately and document it",
            "C. Hide it from the report",
            "D. Only take a photo",
        ],
        "options_zh": [
            "A. 留给下一个巡检人员",
            "B. 立即处理并记录",
            "C. 不写进报告",
            "D. 只拍照",
        ],
        "correct_answer": "B",
        "explanation_en": "Simple safe issues should be fixed on site and documented.",
        "explanation_zh": "可以安全现场解决的小问题应现场处理并记录。",
    },
    {
        "id": "q17",
        "type": "multiple_choice",
        "critical": True,
        "critical_concept": "report unresolved issues",
        "prompt_en": "If you find a problem that cannot be fixed on site, what should "
        "you do?",
        "prompt_zh": "如果发现现场无法解决的问题，应该怎么做？",
        "options_en": [
            "A. Ignore it",
            "B. Take photos and report to ALLCPR promptly",
            "C. Try to repair equipment yourself",
            "D. Wait until next week",
        ],
        "options_zh": [
            "A. 忽略",
            "B. 拍照并及时上报 ALLCPR",
            "C. 自己尝试维修设备",
            "D. 等到下周再说",
        ],
        "correct_answer": "B",
        "explanation_en": "Unresolved issues must be documented with photos and "
        "reported promptly.",
        "explanation_zh": "无法解决的问题必须拍照记录并及时上报。",
    },
    {
        "id": "q18",
        "type": "true_false",
        "critical": True,
        "critical_concept": "no unauthorized repair",
        "prompt_en": "You may dismantle or repair the Smart Manikin, iPad, camera, "
        "access control, or similar equipment if you think you know the problem.",
        "prompt_zh": "如果你认为自己知道问题原因，可以拆卸或维修 Smart Manikin、iPad、"
        "摄像头、门禁或类似设备。",
        "options_en": ["A. True", "B. False"],
        "options_zh": ["A. 对", "B. 错"],
        "correct_answer": "B",
        "explanation_en": "Do not dismantle or repair Smart Manikin, iPad, camera, "
        "access control, or similar equipment without authorization.",
        "explanation_zh": "未经授权不得拆卸或维修 Smart Manikin、iPad、摄像头、门禁或类似设备。",
    },
    {
        "id": "q19",
        "type": "multiple_choice",
        "critical": False,
        "critical_concept": "",
        "prompt_en": "What must be uploaded after inspection?",
        "prompt_zh": "巡检后需要上传什么？",
        "options_en": [
            "A. Before photos",
            "B. After photos",
            "C. Completed Weekly Site Check Report",
            "D. Issue photos if any",
            "E. All of the above",
        ],
        "options_zh": [
            "A. 巡检前照片",
            "B. 巡检后照片",
            "C. 完成的每周分点巡检表",
            "D. 如有问题，上传问题照片",
            "E. 以上全部",
        ],
        "correct_answer": "E",
        "explanation_en": "Inspection materials should include before photos, after "
        "photos, the report, and issue photos if any.",
        "explanation_zh": "巡检资料应包括巡检前照片、巡检后照片、巡检表，以及如有问题的问题照片。",
    },
    {
        "id": "q20",
        "type": "multiple_choice",
        "critical": False,
        "critical_concept": "",
        "prompt_en": "You arrive and the room is messy, trash is full, disinfecting "
        "wipes are low, and the Smart Manikin is not plugged in. What is the best "
        "correct sequence?",
        "prompt_zh": "你到达分点后发现房间凌乱、垃圾满了、消毒湿巾不足、Smart Manikin "
        "没有插电。正确顺序是什么？",
        "options_en": [
            "A. Clean first, then take photos, then submit the report",
            "B. Take before photos, clean/organize, empty trash, check/report "
            "supplies, plug in equipment, take after photos, complete report, "
            "upload materials",
            "C. Only report the problem and leave",
            "D. Plug in the manikin and skip the rest",
        ],
        "options_zh": [
            "A. 先清洁，再拍照，再提交报告",
            "B. 先拍巡检前照片，清洁整理，倒垃圾，检查/上报用品，连接设备电源，"
            "拍巡检后照片，完成报告并上传资料",
            "C. 只上报问题然后离开",
            "D. 只给假人插电，其他跳过",
        ],
        "correct_answer": "B",
        "explanation_en": "The correct workflow is before photos first, then site "
        "care, equipment/power/supplies check, after photos, report, and upload.",
        "explanation_zh": "正确流程是先拍巡检前照片，再维护现场、检查设备/电源/用品，"
        "最后拍巡检后照片、填表并上传。",
    },
]

# Derived once at import; used by scoring and by tests.
CRITICAL_QUESTION_IDS = tuple(q["id"] for q in ONBOARDING_QUESTIONS if q["critical"])

# Fast lookup of the answer key + critical metadata, kept private to this module.
_BY_ID: Dict[str, Dict[str, Any]] = {q["id"]: q for q in ONBOARDING_QUESTIONS}


def _validate() -> None:
    """Fail fast at import if the quiz definition drifts from its contract."""
    if len(ONBOARDING_QUESTIONS) != TOTAL_QUESTIONS:
        raise ValueError(
            f"onboarding quiz must have exactly {TOTAL_QUESTIONS} questions, "
            f"found {len(ONBOARDING_QUESTIONS)}"
        )
    ids = [q["id"] for q in ONBOARDING_QUESTIONS]
    if len(set(ids)) != len(ids):
        raise ValueError("onboarding quiz question ids must be unique")
    for q in ONBOARDING_QUESTIONS:
        if not q.get("correct_answer"):
            raise ValueError(f"question {q.get('id')} is missing a correct_answer")
        if q.get("critical") and not q.get("critical_concept"):
            raise ValueError(f"critical question {q.get('id')} needs a critical_concept")


_validate()


def public_questions() -> List[Dict[str, Any]]:
    """Return the quiz for the frontend with the answer key removed.

    Keeps ``critical``/``critical_concept`` (harmless labels) but drops
    ``correct_answer`` and both ``explanation_*`` fields so the browser cannot
    read the key from the payload.
    """
    out: List[Dict[str, Any]] = []
    for q in ONBOARDING_QUESTIONS:
        out.append({k: v for k, v in q.items() if k not in _ANSWER_KEY_FIELDS})
    return out


def score_onboarding_attempt(answers: Dict[str, Any]) -> Dict[str, Any]:
    """Score a submitted attempt. Server-authoritative — the frontend never decides.

    ``answers`` maps question id -> chosen option letter (e.g. ``{"q1": "B"}``).
    Comparison is case-insensitive and whitespace-tolerant; a missing or blank
    answer counts as wrong.

    Returns a dict with ``score``, ``total``, ``passing_score``, ``passed``,
    ``status`` (``"passed"`` | ``"failed_critical"`` | ``"failed_score"``),
    ``missed_questions`` (ids) and ``critical_misses`` (``{id, concept}``).
    Critical misses take precedence over score: any critical miss is an automatic
    fail even at a passing score.
    """
    answers = answers if isinstance(answers, dict) else {}
    score = 0
    missed: List[str] = []
    critical_misses: List[Dict[str, str]] = []

    for q in ONBOARDING_QUESTIONS:
        qid = q["id"]
        submitted = str(answers.get(qid, "")).strip().upper()
        correct = str(q["correct_answer"]).strip().upper()
        if submitted == correct:
            score += 1
        else:
            missed.append(qid)
            if q["critical"]:
                critical_misses.append({"id": qid, "concept": q["critical_concept"]})

    passed = score >= PASSING_SCORE and not critical_misses
    if passed:
        status = "passed"
    elif critical_misses:
        status = "failed_critical"
    else:
        status = "failed_score"

    return {
        "score": score,
        "total": TOTAL_QUESTIONS,
        "passing_score": PASSING_SCORE,
        "passed": passed,
        "status": status,
        "missed_questions": missed,
        "critical_misses": critical_misses,
    }
