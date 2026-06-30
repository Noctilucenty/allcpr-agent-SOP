"""Sub-issue detection and focused guidance for non-Smart-Manikin scenarios.

Same deterministic, source-conservative pattern as ``smart_manikin_subissues``:
when a narrow query lands inside a broad scenario (access, check-in, completion,
power/internet), route it to the staff's actual operational problem and override
the generic guidance block with a short, focused answer — instead of dumping the
whole scenario bucket. Nothing here invents policy, codes, contacts, or device
fixes beyond what the reviewed SOP/source files already document.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from . import prompts

# --- venue_access_issue sub-issues ------------------------------------------
PASSCODE_NEEDED = "passcode_needed"
CODE_FAILED = "code_failed"
WRONG_ROOM_FLOOR = "wrong_room_floor"

# --- student_checkin_issue sub-issues ---------------------------------------
WRONG_COURSE = "wrong_course"
NOT_ON_ROSTER = "not_on_roster"

# --- completion_or_certificate_issue sub-issues -----------------------------
CERTIFICATE_ISSUE = "certificate_issue"

# --- electricity_outage / internet_outage sub-issue -------------------------
FIX_FAILED = "fix_failed"

# Short human-readable route category per scenario (used for the log/UI).
ROUTE_LABELS: Dict[str, str] = {
    "venue_access_issue": "access",
    "student_checkin_issue": "checkin",
    "completion_or_certificate_issue": "completion",
    "electricity_outage": "outage",
    "internet_outage": "outage",
}

# Sub-issues that involve a policy/customer decision staff may not self-make.
_POLICY_APPROVAL_SUBISSUES = {WRONG_COURSE, NOT_ON_ROSTER, CERTIFICATE_ISSUE}

# Shared "the basic/source fix already failed / still broken" markers. Outage
# scenarios reuse these to switch from basic-checks guidance to escalation.
_OUTAGE_FIX_FAILED_TERMS: Tuple[str, ...] = (
    "still down",
    "still no internet",
    "still no wifi",
    "still no wi-fi",
    "still no network",
    "still no power",
    "still no electricity",
    "still out",
    "still not working",
    "still not back",
    "fix did not work",
    "fix didn't work",
    "didn't work",
    "did not work",
    "after restart",
    "restarted but",
    "tried but",
    "还是没网",
    "还是没电",
    "还是不行",
    "还是没恢复",
    "重启还是",
    "试了没用",
    "修复无效",
)

# Code/keypad/passcode failure markers (access "code failed" path).
_CODE_FAILED_TERMS: Tuple[str, ...] = (
    "code failed",
    "code did not work",
    "code didn't work",
    "code not working",
    "code doesn't work",
    "wrong code",
    "wrong passcode",
    "passcode failed",
    "passcode not working",
    "passcode doesn't work",
    "keypad not working",
    "keypad failed",
    "keypad doesn't work",
    "won't unlock",
    "wont unlock",
    "will not unlock",
    "密码不对",
    "密码错误",
    "密码不管用",
    "密码没用",
    "密码进不去",
    "门禁失灵",
    "刷卡进不去",
    "打不开门",
)

# Code / passcode request markers (access "passcode" path).
_PASSCODE_TERMS: Tuple[str, ...] = (
    "passcode",
    "pass code",
    "room code",
    "door code",
    "gate code",
    "gate passcode",
    "keypad",
    "lockbox",
    "lock box",
    "access code",
    "门禁密码",
    "房间密码",
    "门密码",
    "大门密码",
    "密码是多少",
    "密码多少",
)

_WRONG_ROOM_TERMS: Tuple[str, ...] = (
    "wrong room",
    "wrong floor",
    "wrong building",
    "wrong address",
    "address mismatch",
    "can't find the room",
    "cant find the room",
    "can't find room",
    "cannot find the room",
    "走错楼层",
    "走错房间",
    "找不到房间",
    "找不到教室",
    "房间不对",
    "楼层不对",
    "地址不对",
)

_WRONG_COURSE_TERMS: Tuple[str, ...] = (
    "wrong course",
    "course mismatch",
    "bls vs cpr",
    "cpr vs bls",
    "chose wrong course",
    "wrong course type",
    "选错课",
    "选错课程",
    "课程不匹配",
    "课程不对",
    "报错课",
    "走错课",
)

_NOT_ON_ROSTER_TERMS: Tuple[str, ...] = (
    "not on roster",
    "not on the roster",
    "student not found",
    "not found on roster",
    "roster mismatch",
    "no roster record",
    "missing from roster",
    "不在名单",
    "名单找不到",
    "找不到名单",
    "名单上没有",
    "没有名单记录",
    "名单不符",
)

_CERTIFICATE_TERMS: Tuple[str, ...] = (
    "certificate",
    "certification",
    "cert ",
    "reissue",
    "re-issue",
    "re issue",
    "证书",
    "发证",
    "补发",
)

# Photo terms that mean "completion photo" rather than a certificate-policy
# question; these keep using the source-backed completion-photo flow.
_COMPLETION_PHOTO_TERMS: Tuple[str, ...] = (
    "photo",
    "screenshot",
    "all session done",
    "pass screen",
    "完成照片",
    "完成截图",
    "截图",
)


def _contains_any(text: str, terms: Tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def is_outage_fix_failed(question: str) -> bool:
    return _contains_any((question or "").casefold(), _OUTAGE_FIX_FAILED_TERMS)


def detect_subissue(scenario: str, question: str) -> str:
    """Return a focused sub-issue slug for ``scenario`` (or '' for the generic block)."""
    text = (question or "").casefold()

    if scenario == "venue_access_issue":
        if _contains_any(text, _CODE_FAILED_TERMS):
            return CODE_FAILED
        if _contains_any(text, _WRONG_ROOM_TERMS):
            return WRONG_ROOM_FLOOR
        if _contains_any(text, _PASSCODE_TERMS):
            return PASSCODE_NEEDED
        return ""

    if scenario == "student_checkin_issue":
        if _contains_any(text, _WRONG_COURSE_TERMS):
            return WRONG_COURSE
        if _contains_any(text, _NOT_ON_ROSTER_TERMS):
            return NOT_ON_ROSTER
        return ""

    if scenario == "completion_or_certificate_issue":
        # A certificate-policy question (not a "where do I send the photo" one).
        if _contains_any(text, _CERTIFICATE_TERMS) and not _contains_any(
            text, _COMPLETION_PHOTO_TERMS
        ):
            return CERTIFICATE_ISSUE
        return ""

    if scenario in {"electricity_outage", "internet_outage"}:
        if is_outage_fix_failed(question):
            return FIX_FAILED
        return ""

    return ""


def policy_approval_required(scenario: str, subissue: str) -> bool:
    return subissue in _POLICY_APPROVAL_SUBISSUES


def focused_guidance(
    scenario: str, subissue: str, lang: str
) -> Optional[Dict[str, Any]]:
    """Return focused field overrides for one scenario sub-issue, or None."""
    if not subissue:
        return None
    zh = lang == "zh"
    table = _GUIDANCE_ZH if zh else _GUIDANCE_EN
    block = table.get((scenario, subissue))
    if not block:
        return None
    safe_photo = prompts.SAFE_PHOTO_NOTE if zh else prompts.SAFE_PHOTO_NOTE_EN
    # Append the standard safe-photo note to every focused evidence list.
    out = {k: (list(v) if isinstance(v, list) else v) for k, v in block.items()}
    evidence = list(out.get("evidence_requested", []) or [])
    if safe_photo not in evidence:
        evidence.append(safe_photo)
    out["evidence_requested"] = evidence
    return out


# ===================== English focused guidance =====================
_GUIDANCE_EN: Dict[Tuple[str, str], Dict[str, Any]] = {
    ("venue_access_issue", PASSCODE_NEEDED): {
        "lead": "Room/gate passcode: confirm the class is at a listed site first, then use that site's room/gate passcode, lockbox note, and instruction video. If no listed site matches, do not guess — contact venue/property.",
        "steps": [
            "Confirm the class address, building, floor, and room match a listed site before using any code.",
            "Use the matching site's room passcode, gate/lockbox note, and instruction video (shown in the passcode panel).",
            "If no listed site matches, do not guess a code — contact venue/property and record arrival time and attempts.",
            "Escalate to a supervisor if class is delayed.",
        ],
        "information_to_collect": ["Class address, building, floor, room.", "Which listed site (if any) matches.", "Arrival time."],
        "evidence_requested": ["Screenshot of the address/room assignment.", "Arrival timestamp."],
        "contacts": ["Venue/property (if no listed site matches).", "Supervisor (if class is delayed)."],
        "next_actions": ["Confirm the matching site and use its source-backed code.", "No match → contact venue/property; escalate if class is delayed."],
    },
    ("venue_access_issue", CODE_FAILED): {
        "lead": "The access code did not work: stop retrying and do not force the door. Re-confirm you are at the matching site/room, contact venue/property to open or confirm the method, record the attempts, and escalate to a supervisor if class is delayed.",
        "steps": [
            "Stop retrying the same code and do not force the door.",
            "Re-confirm the correct site, building, floor, and room and that you used the matching site's code.",
            "Contact venue/property to open the door or confirm the current entry method.",
            "Record arrival time and the code attempts; escalate to a supervisor if class is delayed.",
        ],
        "information_to_collect": ["Site/building/floor/room and the code tried.", "Arrival time and number of attempts.", "Venue/property response."],
        "evidence_requested": ["Photo of the locked door/keypad (when safe).", "Arrival timestamp.", "Venue/property contact attempts (call/message)."],
        "contacts": ["Venue/property (open door / confirm method).", "Supervisor (if class is delayed)."],
        "next_actions": ["Contact venue/property and record the attempts.", "Escalate to a supervisor if class is delayed."],
    },
    ("venue_access_issue", WRONG_ROOM_FLOOR): {
        "lead": "Wrong room/floor: confirm the correct address, floor, and room from the assignment, use the matching site's instruction video and signage to guide students, and escalate if they still cannot find the class.",
        "steps": [
            "Confirm the correct address, floor, and room from the class assignment.",
            "Use the matching site's instruction video and room/gate materials; check the SOP images.",
            "Point students to building signage or meet them at the entrance.",
            "If students still cannot find the class or class is delayed, notify a supervisor.",
        ],
        "information_to_collect": ["Correct address/floor/room from the assignment.", "Where students actually went.", "Signage status."],
        "evidence_requested": ["Screenshot of the address/room assignment.", "Entrance/floor/signage photo (when safe)."],
        "contacts": ["Supervisor (if class is delayed).", "Venue/property (building/signage issue)."],
        "next_actions": ["Confirm address/floor/room and use the site's instruction materials.", "Escalate if students still cannot find the class."],
    },
    ("student_checkin_issue", WRONG_COURSE): {
        "lead": "Wrong course type (e.g. BLS vs CPR): verify what the student actually registered for, record expected vs actual course, and escalate to supervisor/registration. There is no self-service course switch, refund, or certificate decision.",
        "steps": [
            "Verify the student's registration and which course they actually registered for.",
            "Record the expected course vs the course running on site, the student's name, and what the student says happened.",
            "Take a roster/registration screenshot as evidence.",
            "Escalate to supervisor / registration back-office; do not switch course, refund, or promise a certificate yourself.",
        ],
        "information_to_collect": ["Student name and registered course.", "Expected course vs actual course on site.", "What the student says happened."],
        "evidence_requested": ["Roster/registration screenshot.", "Student registration confirmation (email/screenshot)."],
        "contacts": ["Supervisor / registration back-office."],
        "do_not_decide_without_approval": ["Do not switch the student's course type yourself.", "Do not promise a refund, reschedule, or certificate before approval."],
        "next_actions": ["Verify registration and record expected vs actual course.", "Escalate to supervisor / registration back-office."],
    },
    ("student_checkin_issue", NOT_ON_ROSTER): {
        "lead": "Student not on the roster: verify the name against the registration/roster, ask for the student's registration proof, capture a screenshot, and escalate the not-on-roster case — do not self-decide admission or back-fill.",
        "steps": [
            "Verify the student's name against the registration/roster (Enrollware, etc.).",
            "Ask the student for registration proof (confirmation email/screenshot).",
            "Screenshot the check-in/roster screen showing the student is missing.",
            "Escalate to supervisor / registration back-office; do not self-decide admission or back-fill.",
        ],
        "information_to_collect": ["Student name and class/time.", "Whether the student has registration proof.", "What the roster shows."],
        "evidence_requested": ["Check-in/roster screenshot showing the student is missing.", "Student registration confirmation (email/screenshot)."],
        "contacts": ["Supervisor / registration back-office."],
        "do_not_decide_without_approval": ["Do not self-decide whether to admit or back-fill a not-on-roster student.", "Refund/payment matters → escalate, needs official SOP source."],
        "next_actions": ["Verify the roster and collect registration proof.", "Escalate the not-on-roster case to a supervisor."],
    },
    ("completion_or_certificate_issue", CERTIFICATE_ISSUE): {
        "lead": "Certificate issue: do not invent eligibility, issuance timelines, or re-issue rules. Record the student/class/session and the exact problem, confirm whether the source-backed completion photo was submitted, and escalate — certificate rules need official SOP confirmation.",
        "steps": [
            "Record the student name, class, session, and the exact certificate problem (not issued / wrong certificate / not scored).",
            "Confirm whether the completion photo (All Session Done/Pass → support@allcpr.org) was submitted.",
            "Escalate to a supervisor; certificate issuance/scoring/re-issue rules need official SOP source.",
            "Do not promise certificate eligibility, timelines, or re-issue.",
        ],
        "information_to_collect": ["Student name, class, session.", "The exact certificate problem.", "Whether the completion photo was submitted."],
        "evidence_requested": ["The specific certificate error/screenshot.", "Completion-photo / All Session Done evidence (if any)."],
        "contacts": ["Supervisor (certificate issuance/scoring).", "support@allcpr.org (completion photo)."],
        "do_not_decide_without_approval": ["Do not invent certificate eligibility, issuance timelines, scoring, or re-issue rules.", "Certificate rules → needs official SOP source."],
        "next_actions": ["Record details and confirm completion-photo submission.", "Escalate to a supervisor; certificate rules need official SOP."],
    },
    ("electricity_outage", FIX_FAILED): {
        "lead": "Still no power after the basic checks: stop repeating the same steps. Record what was tried, capture evidence, escalate to venue/property and a supervisor, and start an incident report. Do not promise a restore time, refund, or reschedule.",
        "steps": [
            "Stop repeating the same basic checks; confirm it is still out and the scope (room/building/area).",
            "Record the outage start time, what was already tried, and the affected class/headcount.",
            "Escalate to venue/property for cause/restore time and to a supervisor for class continuation.",
            "Start an incident report and let the supervisor decide reschedule/refund.",
        ],
        "information_to_collect": ["Outage scope and start time.", "What was already tried and the venue response.", "Affected class, time, headcount."],
        "evidence_requested": ["Photo/video of the outage scene (when safe).", "Venue/property communication record."],
        "contacts": ["Venue/property (cause and restore time).", "Supervisor (class continuation, reschedule/refund)."],
        "next_actions": ["Escalate to venue/property and supervisor.", "Start an incident report; do not promise restore time, refund, or reschedule."],
    },
    ("internet_outage", FIX_FAILED): {
        "lead": "Still down after the basic checks: stop repeating the same steps. Separate venue network vs platform/system, record what was tried with screenshots, escalate to the right owner, and start an incident report.",
        "steps": [
            "Stop repeating the same checks; confirm whether it is the venue network or the course/platform that is still down.",
            "Record what was already tried, the start time, and the affected class/headcount.",
            "Capture screenshots of the Wi-Fi/network error or the platform loading failure and exact error text.",
            "Escalate venue-network issues to venue/property and platform/system issues to supervisor/tech; start an incident report.",
        ],
        "information_to_collect": ["Venue network vs platform/system.", "What was already tried and the start time.", "Affected class, time, headcount."],
        "evidence_requested": ["Screenshot of the Wi-Fi/network error.", "Screenshot of the platform loading failure and error text."],
        "contacts": ["Venue/property (site network).", "Supervisor / tech (platform or system)."],
        "next_actions": ["Escalate to the right owner (venue vs platform).", "Start an incident report; do not promise refund or reschedule."],
    },
}


# ===================== Chinese focused guidance =====================
_GUIDANCE_ZH: Dict[Tuple[str, str], Dict[str, Any]] = {
    ("venue_access_issue", PASSCODE_NEEDED): {
        "lead": "房间/大门密码：先确认班级是否在已记录的站点，再使用该站点的房间/大门密码、lockbox 说明和 instruction 视频。若没有匹配的站点，不要猜测密码，联系场地/物业。",
        "steps": [
            "先核对班级地址、楼、楼层、房间是否匹配某个已记录站点，再使用任何密码。",
            "使用匹配站点的房间密码、大门/lockbox 说明和 instruction 视频（见密码面板）。",
            "若没有匹配站点，不要猜密码——联系场地/物业，并记录到场时间与尝试。",
            "若课程被延误，上报主管。",
        ],
        "information_to_collect": ["班级地址、楼、楼层、房间。", "匹配的是哪个已记录站点（如有）。", "到场时间。"],
        "evidence_requested": ["地址/房间分配信息截图。", "到场时间戳。"],
        "contacts": ["场地/物业（无匹配站点时）。", "主管（课程被延误时）。"],
        "next_actions": ["确认匹配站点并使用其来源支持的密码。", "无匹配 → 联系场地/物业；课程延误则上报。"],
    },
    ("venue_access_issue", CODE_FAILED): {
        "lead": "密码进不去：不要反复试也不要强行破门。重新确认是否在匹配的站点/房间，联系场地/物业开门或确认方式，记录尝试，课程被延误时上报主管。",
        "steps": [
            "停止反复输入同一密码，不要强行破门。",
            "重新确认正确的站点、楼、楼层、房间，并确认用的是匹配站点的密码。",
            "联系场地/物业开门或确认当前进入方式。",
            "记录到场时间与密码尝试；课程被延误时上报主管。",
        ],
        "information_to_collect": ["站点/楼/楼层/房间与试过的密码。", "到场时间与尝试次数。", "场地/物业的回应。"],
        "evidence_requested": ["锁着的门/键盘照片（安全前提下）。", "到场时间戳。", "联系场地/物业的尝试记录（通话/消息）。"],
        "contacts": ["场地/物业（开门 / 确认方式）。", "主管（课程被延误时）。"],
        "next_actions": ["联系场地/物业并记录尝试。", "课程被延误则上报主管。"],
    },
    ("venue_access_issue", WRONG_ROOM_FLOOR): {
        "lead": "走错房间/楼层：先从分配信息确认正确的地址、楼层和房间，使用匹配站点的 instruction 视频和指示牌引导学员，若仍找不到则上报。",
        "steps": [
            "从班级分配信息确认正确的地址、楼层和房间。",
            "使用匹配站点的 instruction 视频和房间/大门资料；查看 SOP 图片。",
            "引导学员看楼内指示牌，或到入口接学员。",
            "若学员仍找不到或课程被延误，通知主管。",
        ],
        "information_to_collect": ["分配信息中的正确地址/楼层/房间。", "学员实际走到哪里。", "指示牌状态。"],
        "evidence_requested": ["地址/房间分配截图。", "入口/楼层/指示牌照片（安全前提下）。"],
        "contacts": ["主管（课程被延误时）。", "场地/物业（建筑/指示牌问题）。"],
        "next_actions": ["确认地址/楼层/房间并使用站点 instruction 资料。", "学员仍找不到则上报。"],
    },
    ("student_checkin_issue", WRONG_COURSE): {
        "lead": "选错课程（如 BLS 与 CPR）：核实学员实际报名的课程，记录应上课程与实际课程，上报主管/报名后台。不可自行换课、退款或决定证书。",
        "steps": [
            "核实学员的报名记录与实际报名的课程。",
            "记录应上课程与现场实际课程、学员姓名以及学员的说法。",
            "截图名单/报名记录作为证据。",
            "上报主管 / 报名后台；不要自行换课、退款或承诺证书。",
        ],
        "information_to_collect": ["学员姓名与报名课程。", "应上课程 vs 现场实际课程。", "学员的说法。"],
        "evidence_requested": ["名单/报名记录截图。", "学员报名确认（邮件/截图）。"],
        "contacts": ["主管 / 报名后台。"],
        "do_not_decide_without_approval": ["不要自行更换学员课程类型。", "未经批准不要承诺退款、改期或证书。"],
        "next_actions": ["核实报名并记录应上 vs 实际课程。", "上报主管 / 报名后台。"],
    },
    ("student_checkin_issue", NOT_ON_ROSTER): {
        "lead": "学员不在名单：核对姓名与报名/名单记录，索取学员的报名证明，截图，并上报不在名单的情况——不要自行决定放行或补录。",
        "steps": [
            "核对学员姓名与报名/名单记录（Enrollware 等）。",
            "向学员索取报名证明（确认邮件/截图）。",
            "截图签到/名单界面，显示该学员不在名单上。",
            "上报主管 / 报名后台；不要自行决定放行或补录。",
        ],
        "information_to_collect": ["学员姓名与班级/时间。", "学员是否有报名证明。", "名单显示的情况。"],
        "evidence_requested": ["显示学员不在名单的签到/名单截图。", "学员报名确认（邮件/截图）。"],
        "contacts": ["主管 / 报名后台。"],
        "do_not_decide_without_approval": ["不要自行决定是否放行或补录不在名单的学员。", "退款/付款相关 → 上报，needs official SOP source。"],
        "next_actions": ["核对名单并收集报名证明。", "将不在名单的情况上报主管。"],
    },
    ("completion_or_certificate_issue", CERTIFICATE_ISSUE): {
        "lead": "证书问题：不要编造资格、签发时限或补发规则。记录学员/班级/会话和具体问题，确认是否已提交来源支持的完成照片，并上报——证书规则需官方 SOP 确认。",
        "steps": [
            "记录学员姓名、班级、会话和具体证书问题（未签发 / 证书错误 / 未计分）。",
            "确认是否已提交完成照片（All Session Done/Pass → support@allcpr.org）。",
            "上报主管；证书签发/计分/补发规则需官方 SOP source。",
            "不要承诺证书资格、时限或补发。",
        ],
        "information_to_collect": ["学员姓名、班级、会话。", "具体证书问题。", "是否已提交完成照片。"],
        "evidence_requested": ["具体证书报错/截图。", "完成照片 / All Session Done 证据（如有）。"],
        "contacts": ["主管（证书签发/计分）。", "support@allcpr.org（完成照片）。"],
        "do_not_decide_without_approval": ["不要编造证书资格、签发时限、计分或补发规则。", "证书规则 → needs official SOP source。"],
        "next_actions": ["记录详情并确认完成照片是否已提交。", "上报主管；证书规则需官方 SOP。"],
    },
    ("electricity_outage", FIX_FAILED): {
        "lead": "基础排查后仍然没电：不要反复重复同样的步骤。记录已尝试内容，收集证据，上报场地/物业和主管，并开始写事件记录。不要承诺恢复时间、退款或改期。",
        "steps": [
            "停止重复同样的基础排查；确认仍然停电及范围（房间/楼/区域）。",
            "记录停电开始时间、已尝试内容、受影响的班级/人数。",
            "上报场地/物业确认原因与恢复时间，并上报主管决定课程是否继续。",
            "开始写事件记录，由主管决定改期/退费。",
        ],
        "information_to_collect": ["停电范围与开始时间。", "已尝试内容与场地回应。", "受影响班级、时间、人数。"],
        "evidence_requested": ["停电现场照片/视频（安全前提下）。", "场地/物业沟通记录。"],
        "contacts": ["场地/物业（原因与恢复时间）。", "主管（课程是否继续、改期/退费）。"],
        "next_actions": ["上报场地/物业与主管。", "开始写事件记录；不要承诺恢复时间、退款或改期。"],
    },
    ("internet_outage", FIX_FAILED): {
        "lead": "基础排查后仍然断网：不要反复重复同样的步骤。区分场地网络与平台/系统，记录已尝试内容并截图，上报对应负责人，并开始写事件记录。",
        "steps": [
            "停止重复同样的排查；确认仍然断的是场地网络还是课程/平台。",
            "记录已尝试内容、开始时间和受影响的班级/人数。",
            "截图 Wi-Fi/网络报错或平台加载失败及确切报错文字。",
            "场地网络问题上报场地/物业，平台/系统问题上报主管/技术；开始写事件记录。",
        ],
        "information_to_collect": ["场地网络 vs 平台/系统。", "已尝试内容与开始时间。", "受影响班级、时间、人数。"],
        "evidence_requested": ["Wi-Fi/网络报错截图。", "平台加载失败截图及报错文字。"],
        "contacts": ["场地/物业（场地网络）。", "主管 / 技术（平台或系统）。"],
        "next_actions": ["上报对应负责人（场地 vs 平台）。", "开始写事件记录；不要承诺退款或改期。"],
    },
}
