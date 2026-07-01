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
    "smart_manikin_site_inspection",
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
        # casual safety wording
        "got hurt", "someone got hurt", "someone hurt", "someone is hurt",
        "hurt", "water leak", "leaking water", "leak", "blood", "electrical hazard",
        "wire exposed", "exposed wire", "trip hazard", "有人受伤", "有人摔倒",
        "受伤了", "漏水", "水漏", "电线危险", "电线裸露", "流血", "安全隐患",
        "有危险", "冒火",
    )),
    ("electricity_outage", (
        "停电", "没电", "断电", "电断了", "跳闸", "power outage", "power's out",
        "power is out", "no power", "lost power", "电力", "电源没了", "电没了",
        "电跳了", "breaker tripped", "blackout", "power goes out",
        "power went out", "power go out", "no electricity", "breaker issue",
        "lights out", "电闸", "power still", "still no power",
        "still no electricity", "还是没电", "电还是没",
        # casual / bilingual
        "power out", "power's off", "power off", "outlet not working",
        "outlet dead", "no outlet", "socket not working", "plug not working",
        "插座没电", "插座坏", "没有电", "断电了", "停电了",
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
        # casual / bilingual
        "wifi down", "wi-fi down", "wifi broken", "wi-fi broken", "wifi not working",
        "website not loading", "website won't load", "website not opening",
        "site not loading", "platform down", "platform not opening", "can't load",
        "won't load", "page not loading", "网站打不开", "网站打不开了", "网站",
        "wifi坏了", "wi-fi坏了", "网坏了", "平台打不开", "平台打不开了", "打不开网页",
    )),
    ("venue_access_issue", (
        "门打不开", "进不去", "门禁", "access", "door", "key", "钥匙", "lock",
        "锁", "room unavailable", "教室进不去", "打不开门", "lockbox", "gate",
        "大门", "进不了", "无法进入", "can't get in", "cannot enter",
        "locked out", "找不到钥匙", "open the door", "门卡", "刷卡进不去",
        "passcode", "门密码", "房间密码", "door code", "gate code", "keypad",
        "wrong room", "wrong floor", "building entrance", "address mismatch",
        "门禁密码", "锁盒", "楼层不对", "房间不对", "地址不对",
        # casual / incomplete / bilingual access wording
        "door closed", "door won't open", "door wont open", "door does not open",
        "door doesn't open", "can't open door", "cant open door", "open door",
        "front door", "office door", "room locked", "suite locked", "keybox",
        "access code", "password", "what is the code", "what's the code",
        "how do i enter", "how to get in", "access issue", "entry issue",
        "let me in", "door won't unlock", "门锁了", "门关着", "怎么进门", "门口密码",
        "密码是多少", "门锁密码", "进门密码", "进门", "办公室门", "房间打不开",
        "门锁着", "分点进不去", "钥匙盒密码", "keybox password", "lockbox 密码",
        "钥匙盒", "刷卡", "开门",
    )),
    # Site Representative weekly inspection. Placed before smart_manikin_trouble-
    # shooting so an inspection question that also mentions "Smart Manikin" routes
    # here. Keywords are inspection-specific (the generic "网络/门禁/摄像头" terms
    # stay shadowed by the earlier outage/access rules on purpose).
    ("smart_manikin_site_inspection", (
        "巡检", "分点巡检", "每周巡检", "每周分点巡检表", "巡检前", "巡检后",
        "巡检拍照", "前照片", "后照片", "上传资料", "上传什么", "要上传", "耗材",
        "消毒", "器材摆放", "摆放位置", "不得维修", "不得拆卸", "可以修吗",
        "能修吗", "可以修", "设备坏", "site inspection", "weekly site check",
        "weekly site check report", "site representative", "smart manikin inspection",
        "before photo", "after photo", "pre-check", "post-check", "inspection photo",
        "upload materials", "equipment placement", "do not repair", "do not dismantle",
        "disinfect equipment", "consumables check", "inspection frequency",
        "现场检查", "现场要检查", "检查清单", "巡检检查", "site checklist",
        "site check items", "check items", "inspection", "inspect", "巡视",
        # Arrival / procedure / what-to-do phrasing routes here too (no need for
        # the word "inspection"/"巡检"). Phrases are specific enough not to steal
        # from instructor-no-show ("did not arrive") or class-cannot-start
        # ("students arrived").
        "when i arrive", "arrived at the site", "i arrived at", "arrival procedure",
        "opening procedure", "site procedure", "site rep procedure",
        "site representative procedure", "weekly check procedure",
        "smart manikin site procedure", "what do i check first",
        "what should i check first", "check first", "before i start",
        "start of inspection", "first thing to do", "first thing",
        "到场后", "到场流程", "专员到场", "到分点", "到店后", "到现场后",
        "开始前", "第一件事", "分点流程",
        # cleaning / supplies / consumables (site checklist items)
        "trash full", "trash", "empty trash", "no wipes", "out of wipes",
        "no gloves", "out of gloves", "supplies missing", "supplies low",
        "restock", "dirty room", "room is dirty", "need disinfect", "need to clean",
        "mask adapter", "mask adaptor", "垃圾满了", "垃圾满", "倒垃圾", "没有湿巾",
        "没有手套", "耗材不够", "耗材没了", "补货", "房间很脏", "房间脏", "需要打扫",
        "面罩转接头",
        # equipment placement / layout
        "器材怎么摆", "怎么摆", "放哪里", "放哪儿", "放在哪", "ipad放哪", "aed放哪",
        "假人怎么摆", "where to put", "where should i put", "where does the ipad go",
        "where do the pads go", "setup layout", "station layout", "manikin layout",
        "how to set up the station", "how to arrange",
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
        # casual device / bluetooth / data / connection wording
        "ipad not working", "ipad dead", "ipad not turning on", "ipad not responding",
        "ipad frozen", "app black screen", "app黑屏", "launch app", "opens black",
        "black tab", "reload didn't work", "reload did not work", "reload not working",
        "平板没反应", "设备打不开", "设备没反应", "设备不工作", "设备黑屏",
        "can't pair", "cant pair", "can't connect", "cant connect", "won't pair",
        "connection failed", "device disconnected", "manikin not connected",
        "not paired", "pairing failed", "连接不上", "假人连接不上", "设备断开",
        "连不上", "配对失败", "断开连接", "training data missing", "no training data",
        "training no data", "no data on ipad", "设备没数据", "进度没保存",
        "progress not saved", "训练数据没了",
    )),
    ("instructor_no_show", (
        "老师没到", "老师没来", "老师还没到", "老师迟到", "老师缺席", "讲师没到",
        "讲师没来", "讲师迟到", "讲师缺席", "instructor no-show",
        "instructor no show", "instructor didn't show", "instructor absent",
        "instructor late", "instructor isn't here", "no instructor",
        "teacher no-show", "teacher didn't show", "instructor did not show",
        "teacher did not show", "teacher did not arrive", "teacher late",
        "teacher absent", "did not show up",
        # casual instructor wording
        "no teacher", "instructor hasn't arrived", "instructor hasnt arrived",
        "teacher hasn't arrived", "teacher hasnt arrived", "instructor not here",
        "teacher not here", "教练没来", "教练没到", "教练迟到", "教练缺席",
        "老师不在", "讲师不在", "没有老师", "没有讲师",
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
        # casual roster / wrong-course wording
        "chose wrong class", "picked wrong course", "picked wrong class",
        "student picked wrong", "wrong course type", "in wrong course",
        "not their class", "roster doesn't match", "roster does not match",
        "name missing", "name not on list", "can't find student", "cant find student",
        "student not on list", "registration not showing", "not registered showing",
        "选错时间", "不是这个班", "不是这个课", "名单不匹配", "找不到名字",
        "名单没有", "名单上没有", "报名没显示", "报名没有显示", "名字不在",
    )),
    ("completion_or_certificate_issue", (
        "completion", "certificate", "证书", "不计分", "没完成", "完课", "结业",
        "证书没", "未发证", "没拿到证书", "completion record", "完课记录",
        "completion status", "没出证", "证没出", "没收到证书",
        "certification not", "didn't pass", "没通过记录",
        # casual certificate / completion-record wording
        "certificate missing", "certificate wrong name", "wrong name on certificate",
        "didn't receive certificate", "did not receive certificate",
        "certificate not received", "certificate not generated", "no certificate",
        "need completion proof", "completion proof", "completion not showing",
        "completion not showing up", "score not showing", "grade not showing",
        "证书没收到", "证书名字错", "证书写错", "完课证明", "证书没有出来",
        "证书出不来", "成绩没有显示", "成绩不显示", "没有证书", "完成记录没了",
    )),
    ("class_cannot_start", (
        "课程无法开始", "class cannot start", "can't start class",
        "cannot start the class", "class can't begin", "students arrived",
        "学生到了", "学生已到", "无法开课", "开不了课", "课开不了", "上不了课",
        "课程开始不了", "课程不能开始", "课没法开始",
        # casual class-start wording
        "students waiting", "students are waiting", "class can't run",
        "class cannot run", "can't run class", "cannot run the class",
        "class delayed", "学员在等", "学员在等待", "学生在等", "不能上课",
        "无法上课", "课上不了",
    )),
    ("incident_report", (
        "incident report", "事故记录", "现场报告", "汇报模板", "incident log",
        "事件记录", "事件报告", "写报告", "报告模板", "incident form",
        "事故报告", "现场记录", "如何记录事件", "怎么写报告", "write report",
        "create incident summary", "report template", "生成报告",
        # casual report / camera-monitoring wording (document + escalate to ALLCPR)
        "what should i report", "need to report", "need escalation note",
        "record the issue", "log the issue", "需要报告", "记录问题", "怎么记录",
        "怎么上报事件", "camera offline", "camera not working", "camera down",
        "camera is down", "video not showing", "no video", "monitor offline",
        "cctv offline", "摄像头离线", "摄像头坏了", "摄像头不工作", "摄像头掉线",
        "监控看不到", "监控离线", "监控坏了", "看不到监控",
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
        # casual refund / reschedule / cancel / compensation wording (approval req.)
        "money back", "wants money back", "want a refund", "wants a refund",
        "refund request", "get a refund", "change date", "change the date",
        "change time", "move the class", "credit", "give credit", "make up class",
        "退钱", "要退钱", "想退款", "改时间", "改课", "改课时间", "换时间",
        "取消课程", "赔偿", "补课",
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
