"""Deterministic scenario classification for the AutoCPR Site Manager agent.

The agent is now primarily a 管点 / site-operations incident assistant, so the
label set leads with operational incidents (safety, outages, access, equipment,
class/instructor/check-in/completion) and keeps the site-intelligence labels as
secondary references.

MVP intent detection stays simple, transparent, ordered keyword matching — no
model call, no paid API. Order matters: the first matching rule wins, so the
highest-priority / most specific scenarios are listed first (safety always wins).
All matching is case-insensitive and bilingual (English + 中文).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# Canonical scenario labels (also the public contract for the endpoint).
# Primary = site-operations incidents + retained site-intelligence references.
SCENARIOS: List[str] = [
    "site_operations_general",
    "electricity_outage",
    "internet_outage",
    "venue_access_issue",
    "smart_manikin_troubleshooting",
    "class_cannot_start",
    "instructor_no_show",
    "student_checkin_issue",
    "completion_or_certificate_issue",
    "safety_or_emergency",
    "incident_report",
    "escalation_guidance",
    "site_opening_reference",
    "dashboard_metric_explanation",
    "zip_site_evaluation",
    "course_type_recommendation",
    "unknown",
    # --- legacy labels kept for backward compatibility ---
    "sop_training",
    "competitor_analysis",
    "enrichment_data_check",
    "missing_data_troubleshooting",
    "improvement_optimization",
]

# Scenarios that always require human review (incidents, policy, uncertain, or
# anything touching cost/contract/safety/customer decisions).
ALWAYS_REVIEW: set = {
    "site_operations_general",
    "electricity_outage",
    "internet_outage",
    "venue_access_issue",
    "smart_manikin_troubleshooting",
    "class_cannot_start",
    "instructor_no_show",
    "student_checkin_issue",
    "completion_or_certificate_issue",
    "safety_or_emergency",
    "incident_report",
    "escalation_guidance",
    "zip_site_evaluation",
    "course_type_recommendation",
    "missing_data_troubleshooting",
    "unknown",
}

# Ordered (scenario, keywords) rules. First hit wins. Safety is first so it can
# never be shadowed by a co-occurring cause keyword.
_RULES: List[Tuple[str, Tuple[str, ...]]] = [
    ("safety_or_emergency", (
        "安全", "危险", "emergency", "紧急", "evacuate", "疏散", "injury",
        "injured", "受伤", "fire", "火灾", "着火", "smoke", "冒烟", "晕倒",
        "faint", "passed out", "unconscious", "昏迷", "bleeding", "出血",
        "911", "报警", "medical emergency", "急救", "地震", "earthquake",
        "gas leak", "煤气", "hazard", "触电", "electric shock", "unsafe",
        "danger",
    )),
    ("electricity_outage", (
        "停电", "没电", "断电", "电断了", "跳闸", "power outage", "power's out",
        "power is out", "no power", "lost power", "电力", "电源没了", "电没了",
        "电跳了", "breaker tripped", "blackout", "power goes out",
        "power went out", "power go out", "no electricity", "breaker issue",
        "lights out", "电闸", "power still", "still no power",
        "still no electricity", "还是没电", "电还是没",
    )),
    ("internet_outage", (
        "没网", "断网", "网络", "网断了", "连不上网", "网卡", "wifi", "wi-fi",
        "internet down", "no internet", "no wifi", "network down",
        "internet outage", "internet is down", "classroom internet is down",
        "网络故障", "上不了网", "网络中断", "loading error", "加载不出来",
        "加载失败", "连接超时", "router", "platform not loading", "no network",
        "平台加载失败", "internet still", "wifi still", "wi-fi still",
        "network still", "platform still", "still no internet", "still no wifi",
        "还是没网", "网还是",
    )),
    ("venue_access_issue", (
        "门打不开", "进不去", "门禁", "access", "door", "key", "钥匙", "lock",
        "锁", "room unavailable", "教室进不去", "打不开门", "lockbox", "gate",
        "大门", "进不了", "无法进入", "can't get in", "cannot enter",
        "locked out", "找不到钥匙", "open the door", "门卡", "刷卡进不去",
        "passcode", "门密码", "房间密码", "door code", "gate code", "keypad",
        "wrong room", "wrong floor", "building entrance", "address mismatch",
        "门禁密码", "锁盒", "楼层不对", "房间不对", "地址不对",
    )),
    ("smart_manikin_troubleshooting", (
        "smart manikin", "manikin", "假人", "黑屏", "black screen", "blank screen",
        "蓝牙", "bluetooth", "平板", "tablet", "ipad", "pad ", "frozen", "freeze",
        "卡住", "死机", "屏幕", "aed pad", "pocket mask", "bvm", "完成截图",
        "completion photo", "completion screen", "won't connect", "wont connect",
        "无法连接", "掉线", "重启manikin", "training device", "练习设备", "教具",
        "all session done", "support@allcpr", "training receives no data",
        "support email", "connected but no data", "connected 但没数据", "训练没数据",
        "完成照片", "ipad打不开", "pad打不开", "ipad won't turn on",
        "ipad wont turn on", "ipad won't open", "ipad wont open",
        "pad not opening", "tablet won't turn on", "tablet wont turn on",
        "平板打不开", "平板开不了", "找不到房间", "找不到教室",
        "app restart", "lost progress", "忘记截图", "pass 界面",
        "source recorded fix does not work", "documented fix did not work",
        "fix did not work", "still not working", "修复无效", "还是不行",
        "试了没用", "插电还是连不上", "重启还是不行",
    )),
    ("instructor_no_show", (
        "老师没到", "老师没来", "老师还没到", "老师迟到", "老师缺席", "讲师没到",
        "讲师没来", "讲师迟到", "讲师缺席", "instructor no-show",
        "instructor no show", "instructor didn't show", "instructor absent",
        "instructor late", "instructor isn't here", "no instructor",
        "teacher no-show", "teacher didn't show", "instructor did not show",
        "teacher did not show", "teacher did not arrive", "teacher late",
        "teacher absent", "did not show up",
    )),
    ("student_checkin_issue", (
        "签到", "check-in", "checkin", "check in", "roster", "名单", "考勤",
        "student checkin", "学员名单", "学生名单", "报名名单", "sign-in",
        "签不了到", "签到不了", "attendance list", "名册", "签到表",
        "不在名单", "not on the roster", "not on roster", "class mismatch",
        "wrong class", "wrong class time", "wrong time", "wrong place",
        "wrong course", "course mismatch", "chose wrong course", "bls vs cpr",
        "走错班", "走错班级", "错班", "课程不匹配", "选错课", "选错课程",
        "走错时间", "走错地点", "走错教室", "wrong location",
        "student not found", "duplicate student", "cpr vs bls", "名单找不到",
        "时间不对", "地点不对",
    )),
    ("completion_or_certificate_issue", (
        "completion", "certificate", "证书", "不计分", "没完成", "完课", "结业",
        "证书没", "未发证", "没拿到证书", "completion record", "完课记录",
        "completion status", "没出证", "证没出", "没收到证书",
        "certification not", "didn't pass", "没通过记录",
    )),
    ("class_cannot_start", (
        "课程无法开始", "class cannot start", "can't start class",
        "cannot start the class", "class can't begin", "students arrived",
        "学生到了", "学生已到", "无法开课", "开不了课", "课开不了", "上不了课",
        "课程开始不了", "课程不能开始", "课没法开始",
    )),
    ("incident_report", (
        "incident report", "事故记录", "现场报告", "汇报模板", "incident log",
        "事件记录", "事件报告", "写报告", "报告模板", "incident form",
        "事故报告", "现场记录", "如何记录事件", "怎么写报告", "write report",
        "create incident summary", "report template", "生成报告",
    )),
    ("course_type_recommendation", (
        "aha bls", "arc bls", "arc cpr", "red cross", "course type",
        "which course", "课程类型", "推荐课程", "course recommendation",
        "bls or cpr", "bls 还是", "cpr 还是", "适合 aha", "还是 red cross",
        "哪种课程", "什么课程", "aha or", "应该开 bls", "应该开 cpr", "brand",
    )),
    ("zip_site_evaluation", (
        "适合开点", "should we open", "should i open", "open site in",
        "evaluate this zip", "evaluate site", "this zip", "this city",
        "这个 zip", "这个zip", "这个区域", "这个城市", "适合在", "potential of",
        "high potential", "邮编", "值不值得开", "适合不适合",
    )),
    ("site_opening_reference", (
        "开点", "选址", "new site", "site opening", "site selection", "开新点",
        "新点", "开店", "新地点", "选点", "拓店", "开发场地", "开点流程",
        "怎么开点", "选址评分",
    )),
    ("dashboard_metric_explanation", (
        "dashboard", "看板", "仪表盘", "means", "what does", "什么意思", "怎么看",
        "怎么理解", "how to read", "opportunity score", "validation confidence",
        "historical confidence", "data completeness", "healthcare density",
        "population density", "metric", "指标", "score mean", "分数是什么",
        "这个分数", "explain the", "modeled score", "how to use the dashboard",
    )),
    ("escalation_guidance", (
        "升级", "escalate", "escalation", "上报", "主管", "supervisor", "工程师",
        "engineer", "vendor", "厂商", "supplier", "场地方", "landlord", "refund",
        "退款", "退费", "reschedule", "改期", "cancel", "cancellation", "取消",
        "compensation", "补偿", "class continuation", "是否继续上课", "lease", "租约", "租赁",
        "deposit", "押金", "payment", "付款", "invoice", "policy", "政策",
        "legal", "法律", "compliance", "合规", "insurance", "保险", "complaint",
        "投诉", "找谁", "who to contact", "联系谁", "when to escalate",
        "什么时候升级", "什么时候上报",
    )),
    # --- legacy site-intelligence labels (kept for backward compatibility) ---
    ("competitor_analysis", (
        "competitor", "competition", "competitive", "竞争", "对手", "竞争对手",
        "competitor density", "竞争密度", "saturation", "饱和", "市场竞争",
        "competition gap",
    )),
    ("missing_data_troubleshooting", (
        "missing", "缺失", "no data", "not available", "没有数据", "数据缺失",
        "找不到数据", "data not provided", "lacking data", "empty data", "缺数据",
        "enrichment missing", "missing enrichment", "数据没有", "no enrichment",
    )),
    ("enrichment_data_check", (
        "enrichment", "enriched", "enrich", "富集", "11 categories",
        "places categories", "enrichment data", "enrichment categories",
        "category coverage", "数据富集",
    )),
    ("improvement_optimization", (
        "improve", "improvement", "optimize", "optimization", "优化", "改进",
        "post-launch", "post launch", "weekly review", "underperform",
        "under-perform", "表现不好", "scale", "扩张", "做得更好", "提升",
        "iterate", "review cycle", "复盘",
    )),
    ("sop_training", (
        "how to use", "怎么用", "如何使用", "教我", "teach me", "onboarding",
        "get started", "getting started", "new specialist", "新专员",
        "工作流程", "sop", "标准流程", "使用说明", "怎么操作", "如何操作",
    )),
    ("site_operations_general", (
        "管点", "site operations", "site ops", "站点运营", "运营", "现场管理",
        "site management", "管理站点", "日常运营", "站点管理", "on-site",
        "现场", "before class", "课前", "site readiness", "课前检查",
        "站点检查", "before-class",
    )),
]


def classify(question: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Return the best scenario label for ``question`` (+ optional ``context``).

    Deterministic, ordered keyword matching. Falls back to ``"unknown"``. If the
    question carries no useful keyword but ``context`` names a ZIP/city, lean
    toward ``zip_site_evaluation`` rather than ``unknown``.
    """
    text = (question or "").lower()
    for scenario, keywords in _RULES:
        for kw in keywords:
            if kw in text:
                return scenario

    ctx = context or {}
    if any(ctx.get(k) for k in ("zip", "city")):
        return "zip_site_evaluation"
    return "unknown"


def requires_review(scenario: str) -> bool:
    """Whether a scenario always needs human review regardless of confidence."""
    return scenario in ALWAYS_REVIEW
