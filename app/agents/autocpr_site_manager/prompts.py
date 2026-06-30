"""Deterministic, bilingual answer scaffolding for the AutoCPR Site Manager agent.

No LLM in the MVP: the agent composes a structured site-operations incident answer
from a fixed, source-aware guidance block per scenario. The guidance is available
in **English and Chinese** — the agent picks the language from the query (or
``context.lang``). Everything here is either (a) directly grounded in the in-repo
SOP/KB, or (b) clearly labeled ``general operations guidance, not official SOP``.
No invented ALLCPR policies, prices, thresholds, contacts, vendor instructions, or
device diagnoses.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence

# --- exact phrases the agent must use when something is genuinely undefined ---
NEEDS_OFFICIAL_SOP = "needs official SOP source"
DATA_NOT_PROVIDED = "data not provided"
NEEDS_VENDOR = "needs engineer/vendor confirmation"
HUMAN_REVIEW_REQUIRED = "human review required"

# --- source-status labels (provenance of the answer; language-neutral) ---
SS_OFFICIAL = "official SOP source"
SS_EXTRACTED = "extracted SOP reference"
SS_MANIKIN = "Smart Manikin source"
SS_GENERAL = "general operations guidance, not official SOP"
SS_MISSING = "missing source"

# --- fixed wording (bilingual) ---
SAFE_PHOTO_NOTE = "如果安全且不影响处理，请上传/保存照片或截图作为证据。"
SAFE_PHOTO_NOTE_EN = "If it is safe and does not interfere with handling, please upload/save photos or screenshots as evidence."
ATTACHMENT_ACK = "已收到附件描述；如需视觉确认请人工查看照片（本助手不分析图片内容）。"
ATTACHMENT_ACK_EN = "Attachment descriptions received; if visual confirmation is needed, a human should review the images. This assistant does not analyze image content."

DEFAULT_LANG = "en"

_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def normalize_language(value: Any) -> Optional[str]:
    """Normalize supported user/context language hints to ``"en"`` or ``"zh"``."""
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    lowered = raw.lower().replace("_", "-")
    if lowered in {"en", "english"} or lowered.startswith("en-"):
        return "en"
    if lowered in {"zh", "chinese", "中文", "汉语", "普通话"} or lowered.startswith("zh-"):
        return "zh"
    return None


def detect_language(question: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Pick answer language from context hint, then deterministic CJK detection."""
    ctx = context or {}
    for key in ("lang", "language", "locale"):
        normalized = normalize_language(ctx.get(key))
        if normalized:
            return normalized
    return "zh" if _CJK_RE.search(question or "") else DEFAULT_LANG

# Keyword triggers that force human review regardless of scenario. Bilingual.
ESCALATION_TRIGGERS: Sequence[str] = (
    "refund", "退款", "退费", "cancel", "cancellation", "取消", "lease", "租约",
    "租赁", "deposit", "押金", "payment", "付款", "pay ", "invoice", "price",
    "pricing", "价格", "policy", "政策", "legal", "法律", "compliance", "合规",
    "insurance", "保险", "no-show", "no show", "缺席", "complaint", "投诉",
    "certificate not", "未发证", "证书没有", "wrong location", "走错",
    "hardware damage", "硬件损坏", "vendor", "厂商", "supplier", "sign a lease",
)

MISSING_DATA_TRIGGERS: Sequence[str] = (
    "missing", "缺失", "no data", "not available", "没有数据", "数据缺失",
    "data not provided", "找不到数据", "no enrichment", "缺数据",
)


def has_escalation_trigger(text: str) -> bool:
    low = (text or "").lower()
    return any(kw in low for kw in ESCALATION_TRIGGERS)


def has_missing_data_trigger(text: str) -> bool:
    low = (text or "").lower()
    return any(kw in low for kw in MISSING_DATA_TRIGGERS)


# Language-neutral per-scenario metadata (severity, exact phrases, source status).
SCENARIO_META: Dict[str, Dict[str, object]] = {
    "site_operations_general": {"severity": "medium", "phrases": [NEEDS_OFFICIAL_SOP], "source_status": [SS_GENERAL, NEEDS_OFFICIAL_SOP]},
    "electricity_outage": {"severity": "high", "phrases": [NEEDS_OFFICIAL_SOP], "source_status": [SS_GENERAL, NEEDS_OFFICIAL_SOP]},
    "internet_outage": {"severity": "high", "phrases": [NEEDS_OFFICIAL_SOP], "source_status": [SS_GENERAL, NEEDS_OFFICIAL_SOP]},
    "venue_access_issue": {"severity": "high", "phrases": [NEEDS_OFFICIAL_SOP], "source_status": [SS_GENERAL, SS_MANIKIN, NEEDS_OFFICIAL_SOP]},
    "smart_manikin_troubleshooting": {"severity": "medium", "phrases": [NEEDS_VENDOR], "source_status": [SS_MANIKIN, NEEDS_VENDOR]},
    "class_cannot_start": {"severity": "high", "phrases": [NEEDS_OFFICIAL_SOP], "source_status": [SS_GENERAL, NEEDS_OFFICIAL_SOP]},
    "instructor_no_show": {"severity": "high", "phrases": [NEEDS_OFFICIAL_SOP], "source_status": [SS_GENERAL, NEEDS_OFFICIAL_SOP]},
    "student_checkin_issue": {"severity": "medium", "phrases": [NEEDS_OFFICIAL_SOP], "source_status": [SS_GENERAL, NEEDS_OFFICIAL_SOP]},
    "completion_or_certificate_issue": {"severity": "medium", "phrases": [NEEDS_OFFICIAL_SOP], "source_status": [SS_MANIKIN, SS_GENERAL, NEEDS_OFFICIAL_SOP]},
    "safety_or_emergency": {"severity": "critical", "phrases": [NEEDS_OFFICIAL_SOP], "source_status": [SS_GENERAL, NEEDS_OFFICIAL_SOP]},
    "incident_report": {"severity": "medium", "phrases": [NEEDS_OFFICIAL_SOP], "source_status": [SS_GENERAL, NEEDS_OFFICIAL_SOP]},
    "escalation_guidance": {"severity": "high", "phrases": [NEEDS_OFFICIAL_SOP], "source_status": [SS_GENERAL, NEEDS_OFFICIAL_SOP]},
    "site_opening_reference": {"severity": "low", "phrases": [], "source_status": [SS_OFFICIAL, SS_EXTRACTED]},
    "dashboard_metric_explanation": {"severity": "low", "phrases": [], "source_status": [SS_EXTRACTED]},
    "zip_site_evaluation": {"severity": "low", "phrases": [DATA_NOT_PROVIDED, NEEDS_OFFICIAL_SOP], "source_status": [SS_EXTRACTED, DATA_NOT_PROVIDED, NEEDS_OFFICIAL_SOP]},
    "course_type_recommendation": {"severity": "low", "phrases": [NEEDS_OFFICIAL_SOP], "source_status": [SS_EXTRACTED, NEEDS_OFFICIAL_SOP]},
    "competitor_analysis": {"severity": "low", "phrases": [], "source_status": [SS_EXTRACTED]},
    "enrichment_data_check": {"severity": "low", "phrases": [DATA_NOT_PROVIDED], "source_status": [SS_EXTRACTED, DATA_NOT_PROVIDED]},
    "missing_data_troubleshooting": {"severity": "low", "phrases": [DATA_NOT_PROVIDED], "source_status": [SS_GENERAL, DATA_NOT_PROVIDED]},
    "improvement_optimization": {"severity": "low", "phrases": [], "source_status": [SS_EXTRACTED]},
    "sop_training": {"severity": "low", "phrases": [], "source_status": [SS_EXTRACTED]},
    "unknown": {"severity": "low", "phrases": [NEEDS_OFFICIAL_SOP], "source_status": [SS_MISSING, NEEDS_OFFICIAL_SOP]},
}

# ===================== English guidance text =====================
GUIDANCE_EN: Dict[str, Dict[str, object]] = {
    "site_operations_general": {
        "issue_type": "General site operations",
        "lead": "General on-site (site operations) handling: confirm safety first, identify the issue type, follow the matching SOP section, collect info + evidence, and escalate decisions to a supervisor. Before class, also run the readiness check.",
        "immediate_safety_check": [
            "Confirm there is no personal-safety risk (fire, smoke, shock, injury, suspicious person).",
            "If any emergency/safety risk → handle as safety_or_emergency first.",
        ],
        "steps": [
            "Identify the specific issue type (power / internet / access / device / class can't start / instructor no-show, etc.).",
            "Follow the matching SOP section (see sop.md).",
            "Before-class check: power, network, door/gate access + passcode/lockbox, correct floor/room, device powered + paired, check-in/roster, signage.",
            "Record time, place, and impact; collect evidence; escalate to a supervisor if needed.",
        ],
        "information_to_collect": [
            "Site/room, class time, issue time, people on site.",
            "The specific symptom and what was already tried.",
        ],
        "evidence_requested": ["Photos/screenshots of the scene (when safe).", SAFE_PHOTO_NOTE_EN],
        "contacts": ["Supervisor / venue / property, depending on the issue type."],
        "customer_communication": ["Tell students it's being handled; any reschedule/refund/compensation wording needs supervisor or official SOP confirmation."],
        "do_not_decide_without_approval": ["Do not self-decide reschedule/refund/compensation.", "Do not promise a recovery time or compensation."],
        "next_actions": ["Identify the issue type and open the matching SOP section.", "Collect info + evidence; escalate to a supervisor if needed."],
    },
    "electricity_outage": {
        "issue_type": "Electricity outage",
        "lead": "A power outage is a site-operations incident. Ensure personal safety first, then determine scope, notify the venue, record evidence, and let the supervisor decide whether class continues and any reschedule/refund.",
        "immediate_safety_check": [
            "Confirm people are safe: anyone injured? any smell of smoke/burning? shock risk?",
            "If there is danger (fire, smoke, shock, injury) → handle as safety_or_emergency and call 911.",
            "Move carefully in the dark — watch aisles, steps, and equipment.",
        ],
        "steps": [
            "Confirm the scope: this room only / whole building / whole area (check the hallway, other rooms, nearby shops).",
            "If only this room tripped: if safe and allowed, ask the venue/property to reset it — do NOT operate the breaker yourself.",
            "Record the outage start time and the affected classes/times.",
            "Notify the venue/property contact to confirm cause and estimated restore time.",
            "Assess whether class can continue (devices need power; the Smart Manikin tablet needs power).",
            "If it may restore soon, ask waiting students to hold; if not, wait for the supervisor's reschedule/refund decision.",
        ],
        "information_to_collect": [
            "Outage scope (room/building/area).",
            "Outage start time and estimated restore time.",
            "Affected class, time, headcount on site.",
            "Venue/property contact and the communication log.",
        ],
        "evidence_requested": [
            "When safe: photo/video of the dark room or outage scene.",
            "Only if safe and allowed: photo of the breaker/power area (do not operate it).",
            "Venue/property communication screenshot or message.",
            "The affected class time and location.",
            SAFE_PHOTO_NOTE_EN,
        ],
        "contacts": [
            "Venue/property contact (confirm cause and restore).",
            "Supervisor (can class continue? reschedule/refund).",
            "If safety is involved → 911 + supervisor immediately.",
        ],
        "customer_communication": [
            "Honestly tell students the situation and that it's being handled; do not promise a specific reschedule/refund yet.",
            "Official reschedule/refund/compensation wording needs supervisor / official SOP confirmation.",
        ],
        "do_not_decide_without_approval": [
            "Do not self-decide a refund/reschedule/compensation amount.",
            "Do not operate or repair electrical equipment yourself.",
            "Do not promise a restore time or compensation.",
        ],
        "next_actions": [
            "Finish collecting info and evidence.",
            "Contact the venue/property and notify the supervisor.",
            "If class cannot continue → human review required; wait for the supervisor's reschedule/refund decision.",
        ],
    },
    "internet_outage": {
        "issue_type": "Internet or Wi-Fi outage",
        "lead": "Network outage handling: confirm scope and whether it affects class/device, try basic recovery, record evidence, and escalate if needed. Note: a Smart Manikin session runs over the Bluetooth PAD↔manikin link; some sites have no Wi-Fi.",
        "immediate_safety_check": ["A network outage usually has no personal-safety risk; if combined with a power/safety issue, handle safety first."],
        "steps": [
            "Confirm scope: one device / the whole room / the whole building.",
            "Basic checks (if safe and authorized): confirm the router/network device has power; power-cycle the router only if it belongs to this site and you're authorized.",
            "Determine which part is affected: general internet/platform loading vs only device pairing.",
            "Record the start time and the affected class.",
            "If it's the venue's network → contact venue/property; if it's the platform/system → escalate to supervisor/tech.",
        ],
        "information_to_collect": ["Outage scope and start time.", "Affected class, time, headcount.", "The exact error message or symptom."],
        "evidence_requested": [
            "Screenshot of the Wi-Fi/network error.",
            "Screenshot of the platform/course loading failure.",
            "Photo of the relevant device/tablet status, if related.",
            SAFE_PHOTO_NOTE_EN,
        ],
        "contacts": ["Venue/property (site network).", "Supervisor / tech (platform or system)."],
        "customer_communication": ["Honestly say it's being investigated; reschedule/refund wording needs supervisor or official SOP confirmation."],
        "do_not_decide_without_approval": ["Do not self-decide a refund/reschedule.", "Do not change network equipment that isn't this site's or that you're not authorized to touch."],
        "next_actions": ["Determine scope, do basic checks, and capture error screenshots.", "Contact the right owner; if class is blocked → human review required."],
    },
    "venue_access_issue": {
        "issue_type": "Venue access / room-entry issue",
        "lead": "Door/room-entry issue: first verify the address and room, the door/gate passcode and instruction video, contact the venue, and record arrival time and attempts; if you still can't get in, escalate to a supervisor.",
        "immediate_safety_check": [
            "If locked outside with weather/safety risk, get people to a safe spot first.",
            "Do not force a door or climb in — that risks injury and legal exposure.",
        ],
        "steps": [
            "Verify the class's address, floor, and room number are correct (check the assignment).",
            "Check for a room passcode / gate passcode / lockbox and the instruction video (per the site's own materials).",
            "After-hours main-gate entry: use the site-provided gate video + passcode (only what the site files support).",
            "Contact the venue/property to open or confirm the entry method.",
            "Record arrival time, the entry attempts, and the contact log.",
        ],
        "information_to_collect": ["Class address, floor, room, arrival time.", "Entry methods already tried (passcode/lockbox/contacting venue).", "Headcount waiting."],
        "evidence_requested": [
            "When safe: photo of the locked door/signage.",
            "Screenshot of the address/room assignment.",
            "Arrival timestamp.",
            "Record of attempts to contact the venue (call/message screenshots).",
            SAFE_PHOTO_NOTE_EN,
        ],
        "contacts": ["Venue/property contact (open door / confirm entry).", "Supervisor (prolonged lockout / whether to reschedule)."],
        "customer_communication": ["Honestly say you're arranging entry; do not promise a specific reschedule/refund."],
        "do_not_decide_without_approval": [
            "Do not force entry or damage the lock.",
            "Do not self-decide a refund/reschedule.",
            "If access rights / key ownership are unclear → needs official SOP source / venue confirmation.",
        ],
        "next_actions": ["Verify the room + passcode/video materials and contact the venue.", "Record arrival time and attempts; if still no entry → human review required."],
    },
    "smart_manikin_troubleshooting": {
        "issue_type": "Smart Manikin / training device issue",
        "lead": (
            "Smart Manikin support is operational site-ops support, strictly limited to what the SOP source files document (not hardware diagnosis). "
            "First collect the symptom and check the items the source documents: power (manikin + tablet plugged into the power strip), display (black "
            "screen / app self-restart), in-course session state (an accidental touch can exit the course and lose progress), Bluetooth pairing between "
            "the PAD and manikin, and tablet/PAD status."
        ),
        "immediate_safety_check": ["A device issue usually has no personal-safety risk; if there is a power smell/heat/shock risk, handle as safety_or_emergency."],
        "steps": [
            "Bluetooth won't connect when unplugged → keep the manikin + PAD powered with the power strip; if it still won't connect while plugged in, use only the source-recorded manikin restart step.",
            "PAD may show connected while TRAINING receives no data → confirm both states, keep manikin + PAD powered, and escalate if still failing.",
            "Can't find the room / wrong floor → use the classroom-finding video, source-backed room/gate materials, and signage notes.",
            "Forgot the completion photo → photograph the All Session Done / Pass screen and email it to support@allcpr.org.",
            "Black screen / app self-restart loses progress → the source records the issue but no documented fix; collect evidence and escalate to engineer/vendor.",
        ],
        "information_to_collect": [
            "The exact symptom and when it happened (which course step).",
            "Power / display / Bluetooth / tablet-PAD status.",
            "The exact error message (if any).",
            "Class/session context.",
        ],
        "evidence_requested": [
            "Photo/video of the device status.",
            "Photo/screenshot of the tablet/PAD screen.",
            "Photo of the power/connection state.",
            "The exact error message.",
            SAFE_PHOTO_NOTE_EN,
        ],
        "contacts": [
            "If it isn't one of the documented known items → escalate to engineer/vendor (needs engineer/vendor confirmation).",
            "Supervisor (when class is affected).",
        ],
        "customer_communication": ["Honestly say the device is being checked; do not claim hardware damage or give an undocumented diagnosis."],
        "do_not_decide_without_approval": [
            "Do not assert hardware damage, root cause, or any undocumented device procedure.",
            "Cite only source-supported certificate/completion rules; otherwise → needs official SOP source.",
        ],
        "next_actions": [
            "Collect the symptom and run the power/display/Bluetooth/tablet-PAD checks.",
            "If a documented fix doesn't resolve it, or the issue isn't covered by the source → escalate to engineer/vendor.",
        ],
    },
    "class_cannot_start": {
        "issue_type": "Class cannot start",
        "lead": "Class can't start: first find the root cause (power/internet/access/device/instructor no-show/roster), handle it via the matching section, reassure waiting students, record impact, and let a supervisor decide on reschedule/refund.",
        "immediate_safety_check": ["Confirm no people/device/venue safety risk."],
        "steps": [
            "Locate the root cause: power / network / access / device / instructor / roster / other.",
            "Switch to the matching SOP section to handle the root cause.",
            "Record the affected start time, headcount, and wait time.",
            "Reassure waiting students with confirmed info only (no reschedule/refund promise).",
            "If not quickly solvable → escalate to a supervisor for reschedule/refund/compensation.",
        ],
        "information_to_collect": ["Root-cause category and the specific symptom.", "Class time/place/headcount.", "What was tried and the result."],
        "evidence_requested": ["Root-cause-specific photos/screenshots (per the matching section).", "Students-arrived / arrival-time record.", SAFE_PHOTO_NOTE_EN],
        "contacts": ["Supervisor (reschedule/refund).", "Venue / tech / engineer, depending on the root cause."],
        "customer_communication": ["Honestly say it's being handled; no reschedule/refund promise."],
        "do_not_decide_without_approval": ["Do not self-decide reschedule/refund/compensation.", "Do not promise a specific recovery time."],
        "next_actions": ["Locate and handle the root cause; record impact.", "If not resolved in time → human review required; escalate to a supervisor."],
    },
    "instructor_no_show": {
        "issue_type": "Instructor no-show or late",
        "lead": "Instructor no-show/late: try to contact the instructor, log attempts and student impact, escalate to a supervisor promptly, and let the supervisor decide substitute/reschedule/refund. The handling policy needs official SOP confirmation.",
        "immediate_safety_check": ["Confirm students on site are safe and waiting in an orderly way."],
        "steps": [
            "Immediately try to contact the instructor (call/message) and log each attempt with its time and result.",
            "Confirm whether a substitute can be arranged (supervisor/scheduling decides — the specialist does not promise).",
            "Record the scheduled class time/place and headcount on site.",
            "Escalate to the supervisor promptly and wait for the substitute/reschedule/refund decision.",
            "Reassure waiting students with confirmed info.",
        ],
        "information_to_collect": ["Scheduled class time and place.", "The contact-attempt log.", "Instructor name (if any).", "Affected headcount."],
        "evidence_requested": ["Scheduled class time/place info.", "Contact-attempt record (call/message screenshots).", "Students-arrived count.", SAFE_PHOTO_NOTE_EN],
        "contacts": ["The instructor.", "Supervisor / scheduling (substitute, reschedule, refund)."],
        "customer_communication": ["Honestly say you're contacting the instructor and handling it; do not promise a substitute time or refund yourself."],
        "do_not_decide_without_approval": ["Do not self-decide reschedule/refund/substitute promises.", "The official no-show policy → needs official SOP source."],
        "next_actions": ["Contact the instructor and log attempts.", "Escalate to a supervisor; human review required (substitute/reschedule/refund)."],
    },
    "student_checkin_issue": {
        "issue_type": "Student check-in / roster issue",
        "lead": "Check-in/roster issue: verify the student's identity against the registration record, log any mismatch, escalate not-on-roster or registration anomalies to a supervisor, and do not self-decide whether to admit/back-fill.",
        "immediate_safety_check": ["No personal-safety risk (unless combined with another event)."],
        "steps": [
            "Verify the student name against the registration/roster (Enrollware, etc.).",
            "Confirm they're not at the wrong class/time/place.",
            "Record mismatches: not on roster, name mismatch, duplicate, unpaid flag, etc.",
            "Not-on-roster or registration anomalies → escalate; the supervisor decides whether to admit/back-fill.",
        ],
        "information_to_collect": ["Student name, class, time.", "The matching roster record or what's missing."],
        "evidence_requested": ["Screenshot of the check-in/roster screen.", "Student registration confirmation (e.g. email/screenshot).", "The relevant error message.", SAFE_PHOTO_NOTE_EN],
        "contacts": ["Supervisor / registration back-office."],
        "customer_communication": ["Honestly say you're verifying; do not promise back-fill or admission yourself."],
        "do_not_decide_without_approval": ["Do not self-decide whether to admit a not-on-roster student.", "Refund/back-fill/payment matters → escalate, needs official SOP source."],
        "next_actions": ["Verify the roster and record the mismatch.", "Escalate anomalies to a supervisor."],
    },
    "completion_or_certificate_issue": {
        "issue_type": "Completion / certificate evidence issue",
        "lead": "Completion/certificate evidence: per the source, after finishing the student photographs the 'All Session Done/Pass' screen and emails it to support@allcpr.org as the basis for the certificate. Any other official certificate-issuance rules need official SOP confirmation.",
        "immediate_safety_check": ["No personal-safety risk."],
        "steps": [
            "Confirm the student reached the 'All Session Done/Pass' screen (the source-recorded completion marker).",
            "Remind/help the student photograph that screen and email it to support@allcpr.org (source-supported).",
            "Record the student name, class, session info, and the specific problem (no photo, not scored, no cert).",
            "Certificate-not-issued / scoring rules → escalate, needs official SOP source.",
        ],
        "information_to_collect": ["Student name, class, session time.", "Completion status and the specific anomaly."],
        "evidence_requested": [
            "Screenshot/photo of the completion status ('All Session Done/Pass' screen).",
            "Student name/class/session info.",
            "The source-required completion photo (if applicable).",
            "The relevant error message.",
            SAFE_PHOTO_NOTE_EN,
        ],
        "contacts": ["support@allcpr.org (completion photo).", "Supervisor (certificate issuance/scoring)."],
        "customer_communication": ["You may cite the source-supported completion-photo flow; do not invent certificate timelines/rules → needs official SOP source."],
        "do_not_decide_without_approval": ["Do not invent certificate timelines, scoring rules, or re-issue policy.", "Official certificate rules → needs official SOP source."],
        "next_actions": ["Confirm the completion screen and complete the support@allcpr.org photo submission.", "Issuance/scoring problems → escalate to a supervisor."],
    },
    "safety_or_emergency": {
        "issue_type": "Safety / emergency",
        "lead": "Safety always comes before evidence. Ensure everyone is safe first, call 911 and evacuate if needed; only after people are safe, record and collect evidence, and escalate to a supervisor immediately.",
        "immediate_safety_check": [
            "Life safety first: injury/fire/smoke/shock/gas → call 911 and evacuate as needed.",
            "Move people to a safe area; do not return to a dangerous area for belongings or photos.",
            "Do not prioritize taking photos over people's safety.",
        ],
        "steps": [
            "Ensure everyone is safe; evacuate and call 911 if needed.",
            "After people are safe, record the event time, place, people involved, and what happened.",
            "Only if safe and not interfering, then take scene photos/video.",
            "Escalate to a supervisor immediately; follow supervisor/official guidance afterward.",
        ],
        "information_to_collect": ["Event time and place.", "Affected/injured people and their condition.", "Emergency actions taken (911/evacuate/first aid)."],
        "evidence_requested": [
            "Do not prioritize photos before people are safe.",
            "Collect photos/video only after people are safe.",
            "Event time and place.",
            "Affected-people information.",
            SAFE_PHOTO_NOTE_EN,
        ],
        "contacts": ["Emergency: 911.", "Supervisor (escalate immediately).", "Venue/property (if venue safety is involved)."],
        "customer_communication": ["Prioritize safety and calm guidance; do not publish an unconfirmed cause or liability conclusion."],
        "do_not_decide_without_approval": ["Do not judge accident liability or promise compensation externally.", "Official incident handling/notification/insurance → needs official SOP source."],
        "next_actions": ["Ensure safety; call 911 and evacuate if needed.", "After people are safe, record + collect evidence and escalate to a supervisor (human review required)."],
    },
    "incident_report": {
        "issue_type": "Incident report",
        "lead": "On-site incident report (general template, not official SOP): record the time, place, site, event type, what happened, impact, actions taken, evidence, escalation target, and items awaiting a supervisor decision.",
        "immediate_safety_check": ["If the event is ongoing and involves safety → handle as safety_or_emergency first, then write the report."],
        "steps": [
            "Record the basics: site, room, class time, event time, recorder.",
            "Event type and what happened: what, when, who.",
            "Impact: affected classes/students/devices; was class interrupted.",
            "Actions taken and the result.",
            "Evidence: list of photos/screenshots/comms.",
            "Escalation target and items awaiting supervisor/official decision (reschedule/refund/compensation).",
        ],
        "information_to_collect": ["Site/room/class time/event time/recorder.", "Event type, what happened, impact, actions taken."],
        "evidence_requested": ["List of related photos/screenshots/video.", "Communication log (venue/instructor/supervisor).", SAFE_PHOTO_NOTE_EN],
        "contacts": ["Supervisor (submit the incident report and the decisions)."],
        "customer_communication": ["In the record, separate 'facts' from 'to be confirmed/decided'; no unconfirmed conclusions or promises."],
        "do_not_decide_without_approval": ["A record is not a decision; reschedule/refund/compensation still need a supervisor or official SOP.", "An official company report template (if any) → needs official SOP source."],
        "next_actions": ["Fill the incident report using the structure above and attach the evidence list.", "Submit it to a supervisor, marking the items to be decided."],
    },
    "escalation_guidance": {
        "issue_type": "Escalation",
        "lead": "Escalation: for anything affecting cost/contract/insurance/safety/customer decisions (refund, reschedule, lease, deposit, payment, legal/compliance, complaint, instructor absence, wrong location, certificate not issued, hardware damage, vendor/engineering), the specialist may not self-decide — escalate to a supervisor and, as needed, to engineer/vendor or the venue.",
        "immediate_safety_check": ["If a safety risk is involved → handle safety first."],
        "steps": [
            "Classify the escalation: customer/policy (refund/reschedule/complaint), device/engineering (vendor/engineer), venue (venue/property), safety (911 + supervisor).",
            "Package the context (time/place/impact/attempts/evidence) to submit together.",
            "Escalate to the right owner and wait for the decision.",
        ],
        "information_to_collect": ["Event context and what was tried.", "The specific decision needed."],
        "evidence_requested": ["Screenshots/photos/records supporting the escalation.", SAFE_PHOTO_NOTE_EN],
        "contacts": [
            "Supervisor (customer/policy/class decisions).",
            "Engineer / vendor (device root cause, needs engineer/vendor confirmation).",
            "Venue / property (venue/access/power).",
        ],
        "customer_communication": ["Say it's being escalated; do not promise a solution before the decision."],
        "do_not_decide_without_approval": ["Refund/reschedule/compensation/contract/insurance/price/policy → must escalate, needs official SOP source."],
        "next_actions": ["Package the context and escalate to the right owner."],
    },
    "site_opening_reference": {
        "issue_type": "Site-opening reference",
        "lead": (
            "Site-opening (site selection) reference — region first, then site. Use the maps-scraper-intel dashboard's modeled ZIP layer to screen ZIPs, "
            "then the Field Assessment Form + the official site-selection scoring sheet. Official formula "
            "Final = 0.12P+0.10C+0.08T+0.10D+0.15L+0.18S+0.12B+0.15O, inputs scored 100/85/70/50/20; bands ≥85 Priority / 75-84.9 Management Review / "
            "65-74.9 Hold/Compare / <65 Reject; hard elimination: access control/cameras not installable, network not adequate, blind spot, high safety risk."
        ),
        "immediate_safety_check": [],
        "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["Screen ZIPs with the dashboard's ZIP layer; on-site, score with the Field Assessment Form + scoring sheet.", "See the site-opening appendix in sop.md."],
    },
    "dashboard_metric_explanation": {
        "issue_type": "Dashboard metric explanation",
        "lead": (
            "The dashboard has two layers: a historical ALLCPR layer (real Enrollware/operating evidence) and a modeled national layer (a public-data "
            "estimate for every US ZIP). Treat modeled = estimate and historical = proven; never present a modeled estimate as proven. The ZIP detail "
            "panel shows the 11 enrichment categories, scores, a plain-English summary, a recommended next action, and risk flags."
        ),
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["Before quoting a metric, confirm whether it's on the modeled or the historical layer."],
    },
    "zip_site_evaluation": {
        "issue_type": "ZIP / site evaluation",
        "lead": (
            "To judge whether a ZIP is worth opening, work region-first: use the dashboard's modeled national ZIP layer to pick ZIPs worth pursuing, then "
            "read the 11 enrichment categories for demand/competition. The modeled ZIP opportunity score is a public-data estimate; it is NOT the on-site "
            "site-selection score, and there is no signed-off mapping between them yet."
        ),
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["Look up this ZIP in the dashboard ZIP detail panel.", "If the ZIP isn't enriched/validated, request manual validation before deciding."],
    },
    "course_type_recommendation": {
        "issue_type": "Course-type recommendation",
        "lead": (
            "Recommend a demand tilt, not a brand: AHA BLS weighs healthcare-workforce density most; ARC BLS weighs healthcare + workplace demand; "
            "Red Cross CPR/First Aid weighs population, schools, workplace, childcare, and general-public demand. The data models demand tilts "
            "(healthcare/BLS vs community/CPR), not brand preference."
        ),
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["Read the ZIP's healthcare vs community demand signals on the dashboard.", "Confirm the AHA-vs-ARC brand decision rule with management first."],
    },
    "competitor_analysis": {
        "issue_type": "Competitor analysis",
        "lead": (
            "Read competition two ways (don't assume one): market validation (providers exist because demand is real) and competition risk (saturation can "
            "suppress a new site's fill rate). Use the BLS/CPR Competitors, CPR Training Center, and Related Training Providers categories, and cross-check "
            "the modeled competition_gap_score (high = little competition) and scoring-sheet dimension C."
        ),
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["Judge competitor density together with the ZIP's underlying demand."],
    },
    "enrichment_data_check": {
        "issue_type": "Enrichment data check",
        "lead": (
            "The 11 Google Places enrichment categories: Hospital, Urgent Care, Clinic, Doctor Office, Nursing Facility, CPR Training Center, EMT School, "
            "Medical Assistant School, First Aid Certification, BLS/CPR Competitors, Related Training Providers. A missing category for a ZIP means it "
            "hasn't been enriched yet — not a negative signal."
        ),
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["Check category coverage in the ZIP detail panel.", "If a category is absent, request manual validation/enrichment for that ZIP."],
    },
    "missing_data_troubleshooting": {
        "issue_type": "Missing-data handling",
        "lead": "When a ZIP value, dashboard metric, threshold, price/policy, or device diagnosis is absent, do not invent it. Return the gap plus the next action. Missing enrichment is not a negative signal — it just means the ZIP hasn't been enriched/validated yet.",
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["Request manual validation/enrichment for the ZIP instead of issuing a verdict.", "Escalate the gap to the BD lead per SM-BD-SOP-001 §10."],
    },
    "improvement_optimization": {
        "issue_type": "Improvement & optimization",
        "lead": (
            "After opening, run a weekly site review (sign-ups, attendance, completions, no-show rate, refund/reschedule rate, technical incidents, site "
            "feedback) → decide optimize/hold/scale/exit. Test-before-scale gate (SM-BD-SOP-001 §6.9): Google Ads 7d + CPS 3d (weekday + weekend); "
            ">5 sign-ups in a week OR 10 total → may open; else management decides."
        ),
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["Run the weekly site-check and compare against the open/hold/scale criteria."],
    },
    "sop_training": {
        "issue_type": "SOP / onboarding",
        "lead": (
            "Specialist onboarding: the primary job is site operations (power, internet, access, device, class can't start, instructor no-show, check-in, "
            "completion/certificate, safety, incident report, escalation). Site-opening/selection and the dashboard are supporting references. Full flow in sop.md."
        ),
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["Read the site-operations sections of sop.md.", "Use the before-class readiness checklist."],
    },
    "unknown": {
        "issue_type": "Unknown",
        "lead": (
            "I can handle site-operations incidents (power, internet, access, Smart Manikin, class can't start, instructor no-show, check-in, completion/"
            "certificate, safety, incident report, escalation) plus site-opening/selection, dashboard, and course-tilt reference questions. I couldn't "
            "confidently classify this one — please add details or have a person confirm."
        ),
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["Add the site, class time, and specific symptom, or name the SOP step in question.", "If it's a policy/customer decision, route to a supervisor."],
    },
}

# ===================== Chinese guidance text =====================
GUIDANCE_ZH: Dict[str, Dict[str, object]] = {
    "site_operations_general": {
        "issue_type": "现场运营 / General site operations",
        "lead": "现场运营（管点）通用处理：先确认安全，再判断问题类型，按对应 SOP 处理，收集信息与证据，必要时上报主管。课前还应完成站点检查。",
        "immediate_safety_check": ["确认现场没有人身安全风险（火、烟、触电、受伤、可疑人员）。", "若有任何紧急或安全风险 → 立即按 safety_or_emergency 处理。"],
        "steps": [
            "判断具体问题类型（停电 / 断网 / 门禁 / 设备 / 课程无法开始 / 老师未到 等）。",
            "按对应 SOP 章节处理（见 sop.md）。",
            "课前站点检查：电、网、门禁/钥匙、教室、设备开机与连接、签到名单、指示牌。",
            "记录时间、地点、影响范围，收集证据，必要时上报主管。",
        ],
        "information_to_collect": ["站点 / 教室、班级时间、问题发生时间、在场人数。", "问题的具体现象与已尝试的处理。"],
        "evidence_requested": ["现场情况的照片/截图（安全前提下）。", SAFE_PHOTO_NOTE],
        "contacts": ["主管 / 场地方 / 物业（视问题类型而定）。"],
        "customer_communication": ["如实告知学员正在处理；正式的改期/退费/补偿说法需主管或官方 SOP 确认。"],
        "do_not_decide_without_approval": ["不要自行决定退费/改期/补偿。", "不要承诺恢复时间或赔偿。"],
        "next_actions": ["确定问题类型并打开对应 SOP 章节。", "收集信息与证据，必要时上报主管。"],
    },
    "electricity_outage": {
        "issue_type": "停电 / Electricity outage",
        "lead": "停电属于现场运营事件。先保证人身安全，再判断范围、通知场地方、记录证据，最后由主管决定课程是否继续与改期/退费。",
        "immediate_safety_check": ["确认现场人员安全：是否有人受伤、是否有烟味/焦味/触电风险。", "若有危险（火、烟、触电、受伤）→ 立即按 safety_or_emergency 处理并拨打 911。", "在黑暗中注意通道、台阶、设备，避免摔倒。"],
        "steps": [
            "确认停电范围：仅本教室 / 整栋楼 / 整片区域（看走廊、其他房间、邻近商铺）。",
            "是否仅本房间跳闸：如安全且被允许，请场地方/物业复位；专员不要自行操作配电箱。",
            "记录停电开始时间、受影响的班级与时间。",
            "通知场地/物业联系人，确认原因与预计恢复时间。",
            "评估课程能否继续（设备依赖供电；Smart Manikin 平板需供电）。",
            "若短时可恢复，安抚在场学员稍候；若不能恢复，等待主管对改期/退费的决定。",
        ],
        "information_to_collect": ["停电范围（房间/楼/区域）。", "停电开始时间与预计恢复时间。", "受影响班级、时间、在场学员人数。", "场地/物业联系人及沟通记录。"],
        "evidence_requested": [
            "在安全前提下：黑暗教室或停电现场的照片/视频。",
            "仅在安全且被允许时：配电箱/电闸区域照片（不要自行操作）。",
            "场地方/物业的沟通截图或消息。",
            "受影响的班级时间与地点。",
            SAFE_PHOTO_NOTE,
        ],
        "contacts": ["场地/物业联系人（确认原因与复电）。", "主管（课程能否继续、改期/退费决定）。", "若涉及安全 → 立即 911 + 主管。"],
        "customer_communication": ["如实告知学员当前情况与正在处理，先不要承诺具体改期/退费方案。", "改期/退费/补偿的正式说法需主管 / 官方 SOP 确认。"],
        "do_not_decide_without_approval": ["不要自行决定退费/改期/补偿金额。", "不要自行操作或维修电力设备。", "不要承诺恢复时间或赔偿。"],
        "next_actions": ["完成信息与证据收集。", "联系场地/物业并通知主管。", "若课程无法继续 → human review required，等待主管决定改期/退费。"],
    },
    "internet_outage": {
        "issue_type": "断网 / Internet or Wi-Fi outage",
        "lead": "网络故障处理：先确认范围与是否影响课程/设备，尝试基础恢复，记录证据，必要时上报。注意：Smart Manikin 训练靠 PAD↔假人蓝牙，部分站点本身无 Wi-Fi。",
        "immediate_safety_check": ["网络故障一般无人身安全风险；若同时伴随停电/安全问题，优先处理安全。"],
        "steps": [
            "确认范围：仅某设备 / 整个教室 / 整栋楼。",
            "基础排查（安全且允许时）：确认路由器/网络设备通电、重启路由器（如属于本站点且被授权）。",
            "确认受影响的是哪一环：上网/平台加载，还是仅设备连接。",
            "记录故障开始时间与受影响班级。",
            "若属场地方网络 → 联系场地/物业；若属平台/系统 → 上报主管/技术。",
        ],
        "information_to_collect": ["故障范围与开始时间。", "受影响的班级、时间、在场人数。", "具体报错信息或现象。"],
        "evidence_requested": ["Wi-Fi/网络报错的截图。", "平台/课程加载失败的截图。", "相关设备/平板状态照片（如有关联）。", SAFE_PHOTO_NOTE],
        "contacts": ["场地/物业（场地网络问题）。", "主管 / 技术（平台或系统问题）。"],
        "customer_communication": ["如实告知学员正在排查；正式改期/退费说法需主管或官方 SOP 确认。"],
        "do_not_decide_without_approval": ["不要自行决定退费/改期。", "不要改动不属于本站点或未授权的网络设备。"],
        "next_actions": ["完成范围判断与基础排查并收集报错截图。", "联系对应负责人；若课程受阻 → human review required。"],
    },
    "venue_access_issue": {
        "issue_type": "门禁 / 教室进入问题 / Venue access issue",
        "lead": "门禁/教室进入问题：先核对地址与房间、门/大门密码与 instruction 视频，联系场地方，记录到场时间与尝试记录；无法进入时上报主管。",
        "immediate_safety_check": ["若被锁在户外且涉及天气/安全风险，先确保人员处于安全位置。", "不要强行破门或翻越，避免人身与法律风险。"],
        "steps": [
            "核对班级的地址、楼层、房间号是否正确（参考分配信息）。",
            "确认是否有房间密码 / 大门密码 / lockbox，以及 instruction 视频（按站点资料）。",
            "办公时间外的大门进入：按站点提供的大门视频与密码（仅限站点资料支持的内容）。",
            "联系场地/物业开门或确认进入方式。",
            "记录到场时间、尝试进入的过程与联系记录。",
        ],
        "information_to_collect": ["班级地址、楼层、房间号、到场时间。", "已尝试的进入方式（密码/lockbox/联系场地方）。", "在场学员人数与等待情况。"],
        "evidence_requested": ["在安全前提下：锁着的门/指示牌照片。", "地址/房间分配信息截图。", "到场时间戳。", "联系场地方的尝试记录（通话/消息截图）。", SAFE_PHOTO_NOTE],
        "contacts": ["场地/物业联系人（开门 / 确认进入方式）。", "主管（长时间无法进入、是否改期）。"],
        "customer_communication": ["如实告知学员正在联系开门；不要承诺具体改期/退费。"],
        "do_not_decide_without_approval": ["不要强行进入或破坏门锁。", "不要自行决定退费/改期。", "具体门禁权限/钥匙归属若不确定 → 需场地方/官方确认。"],
        "next_actions": ["核对房间与密码/视频资料并联系场地方。", "记录到场时间与尝试；无法进入 → human review required。"],
    },
    "smart_manikin_troubleshooting": {
        "issue_type": "Smart Manikin / 训练设备问题",
        "lead": "Smart Manikin 支持属于现场运营支持，且严格限于 SOP 源文件记录的内容（非硬件诊断）。先收集症状并检查源文件记录的项：供电（假人+平板接到插线板）、显示（黑屏/app 自重启）、课程中状态（误触会退出课程并丢失进度）、PAD↔假人蓝牙配对、平板/PAD 状态。",
        "immediate_safety_check": ["设备问题一般无人身安全风险；若涉及电源异味/发热/触电风险，按 safety_or_emergency 处理。"],
        "steps": [
            "Bluetooth 连不上 → 用插线板让假人和 PAD 保持供电；如果插电后仍连不上，只使用来源记录的重启假人步骤。",
            "PAD 可能显示 connected 但 TRAINING 收不到数据 → 确认两个状态，让假人和 PAD 保持供电；仍失败则升级。",
            "找不到房间/走错楼层 → 使用课堂查找视频、来源支持的房间/大门资料和指示牌记录。",
            "忘记完成截图 → 拍 All Session Done / Pass 界面并邮件到 support@allcpr.org。",
            "黑屏 / app 自重启导致进度丢失 → 源文件记录了该问题但未记录修复方法，收集证据并升级工程师/厂商。",
        ],
        "information_to_collect": ["具体症状与出现时机（课程哪一步）。", "供电/显示/蓝牙/平板-PAD 状态。", "确切的报错信息（如有）。", "班级/会话上下文。"],
        "evidence_requested": ["设备状态的照片/视频。", "平板/PAD 屏幕的照片/截图。", "供电/连接状态的照片。", "确切的报错信息。", SAFE_PHOTO_NOTE],
        "contacts": ["若非以上有记录的已知项 → 上报工程师/厂商（needs engineer/vendor confirmation）。", "主管（影响课程时）。"],
        "customer_communication": ["如实告知学员设备正在排查；不要声称硬件损坏或给出未记录的诊断。"],
        "do_not_decide_without_approval": ["不要断言硬件损坏、根因、校准或任何源文件未记录的重置步骤。", "证书/完课规则只引用源文件支持的内容；其余 → needs official SOP source。"],
        "next_actions": ["收集症状并执行 供电/显示/蓝牙/平板-PAD 检查。", "若已知项的修复无效或问题未被源文件覆盖 → 上报工程师/厂商。"],
    },
    "class_cannot_start": {
        "issue_type": "课程无法开始 / Class cannot start",
        "lead": "课程无法开始：先确认根因（停电/断网/门禁/设备/老师未到/签到问题），按对应 SOP 处理，安抚在场学员，记录影响，必要时由主管决定改期/退费。",
        "immediate_safety_check": ["确认现场无安全风险（人员、设备、场地）。"],
        "steps": [
            "定位根因：电 / 网 / 门禁 / 设备 / 老师未到 / 签到名单 / 其他。",
            "转到对应 SOP 章节处理根因。",
            "记录开始受影响的时间、在场学员人数与等待时间。",
            "安抚在场学员，给出当前可确认的信息（不承诺改期/退费）。",
            "若短时无法解决 → 上报主管，由主管决定改期/退费/补偿。",
        ],
        "information_to_collect": ["根因类别与具体现象。", "班级时间、地点、在场学员人数。", "已尝试的处理与结果。"],
        "evidence_requested": ["根因相关的照片/截图（按对应场景）。", "在场学员情况/到场时间记录。", SAFE_PHOTO_NOTE],
        "contacts": ["主管（改期/退费决定）。", "场地方 / 技术 / 工程师（视根因而定）。"],
        "customer_communication": ["如实告知正在处理；正式改期/退费说法需主管或官方 SOP 确认。"],
        "do_not_decide_without_approval": ["不要自行决定改期/退费/补偿。", "不要承诺具体恢复时间。"],
        "next_actions": ["定位并处理根因，记录影响。", "若无法及时解决 → human review required，上报主管。"],
    },
    "instructor_no_show": {
        "issue_type": "老师未到 / 迟到 / Instructor no-show or late",
        "lead": "老师未到/迟到：尝试联系老师，记录联系尝试与学员影响，及时上报主管，由主管决定替补/改期/退费。具体处理政策需官方 SOP 确认。",
        "immediate_safety_check": ["确认现场学员安全、有序等待。"],
        "steps": [
            "立即尝试联系老师（电话/消息），记录每次联系的时间与结果。",
            "确认是否有替补老师可安排（由主管/排课决定，专员不自行承诺）。",
            "记录预定上课时间、地点与在场学员人数。",
            "及时上报主管，等待替补/改期/退费决定。",
            "安抚在场学员，给出当前可确认信息。",
        ],
        "information_to_collect": ["预定班级时间与地点。", "联系老师的尝试记录。", "老师姓名（如有）。", "受影响学员人数。"],
        "evidence_requested": ["预定班级时间/地点信息。", "联系老师的尝试记录（通话/消息截图）。", "在场学员人数/到场记录。", SAFE_PHOTO_NOTE],
        "contacts": ["老师本人。", "主管 / 排课（替补、改期、退费决定）。"],
        "customer_communication": ["如实告知正在联系老师并处理；不要自行承诺替补时间或退费。"],
        "do_not_decide_without_approval": ["不要自行决定改期/退费/替补承诺。", "老师未到的正式处理政策 → needs official SOP source。"],
        "next_actions": ["联系老师并记录尝试。", "上报主管，human review required（替补/改期/退费）。"],
    },
    "student_checkin_issue": {
        "issue_type": "学员签到 / 名单问题 / Student check-in or roster issue",
        "lead": "签到/名单问题：核对学员身份与报名记录，记录不一致之处，不在名单或报名异常的情况上报主管，不自行决定是否放行/补录。",
        "immediate_safety_check": ["无人身安全风险（除非伴随其他事件）。"],
        "steps": [
            "核对学员姓名与报名/名单记录（Enrollware 等）。",
            "确认是否走错班级/时间/地点。",
            "记录不一致：不在名单、姓名不符、重复、未付款标记等。",
            "不在名单或报名异常 → 上报主管，由主管决定是否放行/补录。",
        ],
        "information_to_collect": ["学员姓名、班级、时间。", "报名/名单中的对应记录或缺失情况。"],
        "evidence_requested": ["签到/名单界面的截图。", "学员报名确认（如邮件/截图）。", "相关报错信息。", SAFE_PHOTO_NOTE],
        "contacts": ["主管 / 报名后台负责人。"],
        "customer_communication": ["如实告知正在核对；不要自行承诺补录或放行。"],
        "do_not_decide_without_approval": ["不要自行决定是否放行不在名单的学员。", "退款/补录/付款相关 → 上报，needs official SOP source。"],
        "next_actions": ["核对名单并记录不一致。", "异常 → 上报主管。"],
    },
    "completion_or_certificate_issue": {
        "issue_type": "完课 / 证书证据问题 / Completion or certificate evidence issue",
        "lead": "完课/证书证据问题：依据源文件，完成后需拍“All Session Done/Pass”界面并邮件到 support@allcpr.org 作为发证依据。证书签发的其余正式规则需官方 SOP 确认。",
        "immediate_safety_check": ["无人身安全风险。"],
        "steps": [
            "确认学员是否已完成并看到“All Session Done/Pass”界面（源文件记录的完课标志）。",
            "提醒/协助学员拍照该界面并邮件到 support@allcpr.org（源文件支持）。",
            "记录学员姓名、班级、会话信息与具体问题（如未拍照、未计分、未出证）。",
            "证书未签发/计分规则等正式问题 → 上报，needs official SOP source。",
        ],
        "information_to_collect": ["学员姓名、班级、会话时间。", "完课状态与具体异常。"],
        "evidence_requested": ["完课状态的截图/照片（“All Session Done/Pass”界面）。", "学员姓名/班级/会话信息。", "源文件要求的完课照片（如适用）。", "相关报错信息。", SAFE_PHOTO_NOTE],
        "contacts": ["support@allcpr.org（完课照片）。", "主管（证书签发/计分问题）。"],
        "customer_communication": ["可引用源文件支持的完课照片流程；证书签发时限/规则不要编造 → 需官方 SOP。"],
        "do_not_decide_without_approval": ["不要编造证书签发时限、计分规则或补发政策。", "证书相关正式规则 → needs official SOP source。"],
        "next_actions": ["确认完课界面并完成 support@allcpr.org 照片提交。", "签发/计分类问题 → 上报主管。"],
    },
    "safety_or_emergency": {
        "issue_type": "安全 / 紧急事件 / Safety or emergency",
        "lead": "安全永远优先于取证。先确保所有人安全，必要时立即拨打 911 并疏散；人安全之后再记录与取证，并立即上报主管。",
        "immediate_safety_check": ["生命安全第一：如有受伤/火/烟/触电/煤气等危险，立即拨打 911 并按需要疏散。", "将人员撤离到安全区域，不要返回危险区域取物或拍照。", "不要在人员未安全前优先拍照取证。"],
        "steps": [
            "确保所有人安全、必要时疏散并报警（911）。",
            "人员安全后，记录事件时间、地点、涉及人员与经过。",
            "仅在安全且不影响处理时，再补拍现场照片/视频。",
            "立即上报主管；按主管/官方指引后续处理。",
        ],
        "information_to_collect": ["事件时间与地点。", "受影响/受伤人员与情况。", "已采取的应急措施（报警/疏散/急救）。"],
        "evidence_requested": ["不要在人员安全之前优先拍照。", "仅在人员安全之后再收集照片/视频。", "事件时间与地点。", "受影响人员信息。", SAFE_PHOTO_NOTE],
        "contacts": ["紧急情况：911。", "主管（立即上报）。", "场地/物业（如涉及场地安全）。"],
        "customer_communication": ["以人员安全与冷静引导为先；不要发布未经确认的事故结论或责任判断。"],
        "do_not_decide_without_approval": ["不要判断事故责任或对外承诺赔偿。", "正式事故处理/通报/保险流程 → needs official SOP source。"],
        "next_actions": ["确保安全、必要时 911 与疏散。", "人安全后记录与取证，立即上报主管（human review required）。"],
    },
    "incident_report": {
        "issue_type": "现场事件记录 / Incident report",
        "lead": "现场事件记录（通用模板，非官方 SOP）：记录时间、地点、站点、事件类型、经过、影响、已采取措施、证据、上报对象与待主管决定事项。",
        "immediate_safety_check": ["若事件仍在进行且涉及安全 → 先按 safety_or_emergency 处理，再写记录。"],
        "steps": [
            "记录基本信息：站点、教室、班级时间、事件发生时间、记录人。",
            "事件类型与经过：发生了什么、何时、涉及谁。",
            "影响：受影响的班级/学员/设备、是否中断课程。",
            "已采取措施与结果。",
            "证据：照片/截图/沟通记录清单。",
            "上报对象与待主管/官方决定的事项（改期/退费/赔偿）。",
        ],
        "information_to_collect": ["站点/教室/班级时间/事件时间/记录人。", "事件类型、经过、影响、已采取措施。"],
        "evidence_requested": ["相关照片/截图/视频清单。", "沟通记录（场地方/老师/主管）。", SAFE_PHOTO_NOTE],
        "contacts": ["主管（提交事件记录与决定事项）。"],
        "customer_communication": ["记录中区分“事实”与“待确认/待决定”，不要写入未经确认的结论或承诺。"],
        "do_not_decide_without_approval": ["记录不等于决定；改期/退费/赔偿仍需主管或官方 SOP 决定。", "正式事件记录模板若公司有规定 → needs official SOP source。"],
        "next_actions": ["用上面的结构填写事件记录并附证据清单。", "提交主管，标注待决定事项。"],
    },
    "escalation_guidance": {
        "issue_type": "升级 / 上报 / Escalation",
        "lead": "升级处理：涉及成本/合同/保险/安全/客户决定（退费、改期、租约、押金、付款、法律/合规、投诉、老师缺席、走错地点、证书未发、硬件损坏、厂商/工程问题）时，专员不得自行决定，应上报主管，并据情况转工程师/厂商或场地方。",
        "immediate_safety_check": ["若伴随安全风险 → 先处理安全。"],
        "steps": [
            "判断升级类型：客户/政策类（退费/改期/投诉）、设备/工程类（厂商/工程师）、场地类（场地方/物业）、安全类（911+主管）。",
            "整理上下文（时间、地点、影响、已尝试处理、证据）一并提交。",
            "上报对应负责人，等待决定。",
        ],
        "information_to_collect": ["事件上下文与已尝试处理。", "需要决定的具体问题。"],
        "evidence_requested": ["支撑升级的截图/照片/记录。", SAFE_PHOTO_NOTE],
        "contacts": ["主管（客户/政策/课程决定）。", "工程师 / 厂商（设备根因，needs engineer/vendor confirmation）。", "场地方 / 物业（场地/门禁/电网）。"],
        "customer_communication": ["告知正在升级处理；不要在升级结果前对外承诺方案。"],
        "do_not_decide_without_approval": ["退费/改期/赔偿/合同/保险/价格/政策 → 必须上报，needs official SOP source。"],
        "next_actions": ["整理上下文并上报对应负责人。"],
    },
    "site_opening_reference": {
        "issue_type": "开点参考 / Site-opening reference",
        "lead": "开点（选址）参考：先区域、后场地。用 maps-scraper-intel 仪表盘筛 ZIP，再用现场考察表 + 官方选址评分表打分。官方公式 Final = 0.12P+0.10C+0.08T+0.10D+0.15L+0.18S+0.12B+0.15O，输入 100/85/70/50/20；分档 ≥85 优先 / 75–84.9 管理层复核 / 65–74.9 暂缓 / <65 否决；硬性淘汰：门禁/摄像头不可装、网络不达标、监控盲区、安全风险高。",
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["区域筛选用仪表盘 ZIP 层；现场用考察表 + 选址评分表打分。", "详见 sop.md 的开点参考附录。"],
    },
    "dashboard_metric_explanation": {
        "issue_type": "仪表盘指标解释 / Dashboard metric",
        "lead": "仪表盘分两层：历史 ALLCPR 层（真实 Enrollware/运营证据）与建模全国层（每个 US ZIP 的公开数据估计）。建模=估计、历史=已验证，不要把建模当成已验证。ZIP 详情面板含 11 类富集、分数、白话总结、建议动作与风险标记。",
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["引用前先确认指标在“建模层”还是“历史层”。"],
    },
    "zip_site_evaluation": {
        "issue_type": "ZIP / 选址评估 / ZIP site evaluation",
        "lead": "判断 ZIP 是否值得开点：先用建模全国 ZIP 层选出值得追的 ZIP，再看 11 类富集的需求/竞争。建模 ZIP 机会分是公开数据估计，不等于现场选址评分表的分数，二者之间还没有签署的换算口径。",
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["在仪表盘 ZIP 详情面板查该 ZIP。", "若该 ZIP 未富集/未验证，先申请人工验证再下结论。"],
    },
    "course_type_recommendation": {
        "issue_type": "课程类型建议 / Course-type recommendation",
        "lead": "建议的是需求倾向，而非品牌：AHA BLS 最看重医疗从业密度；ARC BLS 看重医疗+职场需求；Red Cross CPR/First Aid 看重人口、学校、职场、托幼与大众需求。数据建模的是需求倾向（医疗/BLS 对 社区/CPR），不是品牌偏好。",
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["在仪表盘看该 ZIP 的医疗 vs 社区需求信号。", "AHA vs ARC 的品牌决策规则需先与管理层确认。"],
    },
    "competitor_analysis": {
        "issue_type": "竞争分析 / Competitor analysis",
        "lead": "竞争有两种读法（不要只取一种）：市场验证（有需求才有同行）与竞争风险（饱和会压低新点填课率）。用 BLS/CPR Competitors、CPR Training Center、Related Training Providers 类别，交叉对照建模 competition_gap_score（高=竞争少）与选址评分表维度 C。",
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["把竞争密度与该 ZIP 的底层需求一起看再判断。"],
    },
    "enrichment_data_check": {
        "issue_type": "富集数据检查 / Enrichment data check",
        "lead": "11 类 Google Places 富集：Hospital、Urgent Care、Clinic、Doctor Office、Nursing Facility、CPR Training Center、EMT School、Medical Assistant School、First Aid Certification、BLS/CPR Competitors、Related Training Providers。某 ZIP 缺某类=尚未富集，不是负面信号。",
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["在 ZIP 详情面板看类别覆盖。", "缺失类别 → 申请对该 ZIP 人工验证/富集。"],
    },
    "missing_data_troubleshooting": {
        "issue_type": "缺数据处理 / Missing-data handling",
        "lead": "ZIP 值、仪表盘指标、阈值、价格/政策或设备诊断缺失时，不要编造。返回缺口与下一步动作。缺富集不是负面信号，只表示该 ZIP 尚未富集/验证。",
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["对该 ZIP 申请人工验证/富集，而不是直接下结论。", "按 SM-BD-SOP-001 §10 将缺口上报 BD 负责人。"],
    },
    "improvement_optimization": {
        "issue_type": "改进优化 / Improvement & optimization",
        "lead": "开业后每周做站点复盘（报名、出勤、完课、缺席率、退费/改期率、技术事件、站点反馈）→ 决定 优化/暂缓/扩张/退出。开点的 test-before-scale 门槛（SM-BD-SOP-001 §6.9）：Google Ads 7 天 + CPS 3 天（含工作日与周末）；一周 >5 报名或累计 10 → 可开；否则管理层决定。",
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["跑每周站点检查并对照 开/暂缓/扩张 标准。"],
    },
    "sop_training": {
        "issue_type": "SOP / 上手培训 / SOP training",
        "lead": "专员上手：现在的主任务是 管点/现场运营（停电、断网、门禁、设备、课程无法开始、老师未到、签到、完课/证书、安全、事件记录、升级）。开点/选址与仪表盘是支持参考。完整流程见 sop.md。",
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["通读 sop.md 的现场运营各章节。", "课前用站点检查清单。"],
    },
    "unknown": {
        "issue_type": "未识别 / Unknown",
        "lead": "我可以处理 管点/现场运营事件（停电、断网、门禁、Smart Manikin、课程无法开始、老师未到、签到、完课/证书、安全、事件记录、升级），以及开点/选址、仪表盘、课程倾向等参考问题。这条没能确定归类，请补充信息或交人工确认。",
        "immediate_safety_check": [], "steps": [], "information_to_collect": [], "evidence_requested": [], "contacts": [],
        "customer_communication": [], "do_not_decide_without_approval": [],
        "next_actions": ["补充站点、班级时间、具体现象，或指明要问的 SOP 步骤。", "若属政策/客户决定，转主管。"],
    },
}

_TEXT = {"en": GUIDANCE_EN, "zh": GUIDANCE_ZH}


def guidance_for(scenario: str, lang: str = DEFAULT_LANG) -> Dict[str, object]:
    """Return the merged guidance block (neutral metadata + language text).

    Falls back to ``unknown`` for an unrecognized scenario and to the default
    language for an unrecognized ``lang``.
    """
    lang = lang if lang in _TEXT else DEFAULT_LANG
    meta = SCENARIO_META.get(scenario, SCENARIO_META["unknown"])
    text = _TEXT[lang].get(scenario, _TEXT[lang]["unknown"])
    merged: Dict[str, object] = {}
    merged.update(meta)
    merged.update(text)
    return merged


def _list(block: Dict[str, object], key: str) -> List[str]:
    return list(block.get(key, []))  # type: ignore[arg-type]


def lead_for(scenario: str, lang: str = DEFAULT_LANG) -> str:
    return str(guidance_for(scenario, lang).get("lead", ""))


def phrases_for(scenario: str) -> List[str]:
    return list(SCENARIO_META.get(scenario, SCENARIO_META["unknown"]).get("phrases", []))  # type: ignore[arg-type]


def next_actions_for(scenario: str, lang: str = DEFAULT_LANG) -> List[str]:
    return _list(guidance_for(scenario, lang), "next_actions")
