"""Sub-issue detection and focused guidance for Smart Manikin incidents.

This layer is deterministic and source-conservative. It narrows the generic
Smart Manikin scenario into the staff's actual operational problem without
inventing device fixes beyond the reviewed SOP/source-derived notes.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from . import prompts

IPAD_PAD_POWER_OR_OPEN = "ipad_pad_power_or_open"
BLUETOOTH_CONNECTION = "bluetooth_connection"
TRAINING_NO_DATA = "training_no_data"
BLACK_SCREEN_APP_RESTART = "black_screen_app_restart"
COMPLETION_PHOTO = "completion_photo"
WRONG_ROOM_FLOOR = "wrong_room_floor"
DOCUMENTED_FIX_FAILED = "documented_fix_failed"

FIX_FAILED_TERMS = (
    "still not working",
    "fix did not work",
    "fix doesn't work",
    "tried but failed",
    "still no data",
    "still black screen",
    "source recorded fix does not work",
    "documented fix did not work",
    "does not work",
    "didn't work",
    "插电还是连不上",
    "重启还是不行",
    "还是不行",
    "修复无效",
    "试了没用",
)

_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        TRAINING_NO_DATA,
        (
            "training receives no data",
            "training no data",
            "pad connected but no data",
            "connected but training receives no data",
            "connected but no data",
            "显示 connected 但是没有数据",
            "connected 但是没有数据",
            "训练没数据",
            "pad 显示连接但没数据",
        ),
    ),
    (
        IPAD_PAD_POWER_OR_OPEN,
        (
            "ipad打不开",
            "ipad won't open",
            "ipad wont open",
            "ipad won't turn on",
            "ipad wont turn on",
            "pad打不开",
            "pad won't open",
            "pad wont open",
            "pad not opening",
            "tablet won't turn on",
            "tablet wont turn on",
            "tablet black screen",
            "ipad black screen",
            "pad black screen",
            "平板打不开",
            "平板开不了",
            "平板黑屏",
            # battery / charging / power-on wording (e.g. "iPad no battery")
            "no battery",
            "ipad battery",
            "ipad no battery",
            "ipad has no battery",
            "dead battery",
            "battery dead",
            "ipad dead",
            "out of battery",
            "battery empty",
            "low battery",
            "won't charge",
            "wont charge",
            "not charging",
            "won't power on",
            "wont power on",
            "ipad no power",
            "pad no battery",
            "tablet no battery",
            "tablet not charging",
            "tablet dead",
            "dead tablet",
            "tablet not turning on",
            "tablet won't power on",
            "tablet wont power on",
            "tablet no power",
            "没电",
            "没有电量",
            "电量低",
            "电池",
            "充不进电",
            "充不上电",
            "不充电",
            "没充电",
            "电用完了",
            "开不了机",
            "关机了",
            "自动关机",
        ),
    ),
    (
        BLUETOOTH_CONNECTION,
        (
            "bluetooth won't connect",
            "bluetooth wont connect",
            "bluetooth not connecting",
            "manikin cannot connect",
            "connection failed",
            "connected issue",
            "蓝牙连不上",
            "无法连接",
            "连不上",
        ),
    ),
    (
        BLACK_SCREEN_APP_RESTART,
        (
            "black screen",
            "screen is black",
            "blank screen",
            "app restart",
            "app self restart",
            "self-restart",
            "lost progress",
            "黑屏",
            "app 重启",
            "自重启",
            "进度丢失",
        ),
    ),
    (
        COMPLETION_PHOTO,
        (
            "completion photo",
            "forgot photo",
            "all session done",
            "pass screen",
            "support@allcpr",
            "support email",
            "完成照片",
            "完成截图",
            "忘记截图",
            "pass 界面",
        ),
    ),
    (
        WRONG_ROOM_FLOOR,
        (
            "wrong room",
            "wrong floor",
            "can't find room",
            "cant find room",
            "room/floor issue",
            "走错楼层",
            "找不到房间",
            "找不到教室",
            "房间不对",
            "楼层不对",
        ),
    ),
)


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def detect_smart_manikin_subissue(question: str) -> str:
    text = (question or "").casefold()
    fix_failed = is_documented_fix_failed_requested(question)
    for subissue, terms in _PATTERNS:
        if _contains_any(text, terms):
            return subissue
    return DOCUMENTED_FIX_FAILED if fix_failed else ""


def is_documented_fix_failed_requested(question: str) -> bool:
    return _contains_any((question or "").casefold(), FIX_FAILED_TERMS)


def documented_fix_available(subissue: str) -> bool:
    return subissue in {
        BLUETOOTH_CONNECTION,
        TRAINING_NO_DATA,
        COMPLETION_PHOTO,
        WRONG_ROOM_FLOOR,
    }


def focused_guidance(subissue: str, lang: str, fix_failed: bool = False) -> Optional[Dict[str, Any]]:
    """Return focused field overrides for one Smart Manikin sub-issue."""

    if not subissue:
        return None
    zh = lang == "zh"
    safe_photo = prompts.SAFE_PHOTO_NOTE if zh else prompts.SAFE_PHOTO_NOTE_EN

    if fix_failed:
        if zh:
            return {
                "lead": "已记录修复无效：停止重复未记录的尝试，保存证据，并升级工程师/厂商；如影响课程，同时通知主管。",
                "steps": [
                    "停止重复同一修复或尝试未记录的重置/校准步骤。",
                    "保存照片/视频证据，记录具体现象、时间、课程步骤和已尝试内容。",
                    "升级工程师/厂商。",
                    "如影响课程，通知主管。",
                    "不要编造硬件损坏、根因、重置或校准步骤。",
                ],
                "information_to_collect": ["具体现象与发生时间。", "已尝试的来源记录步骤与结果。", "课程/会话和设备状态。"],
                "evidence_requested": ["照片/视频证据。", "屏幕/连接/报错状态。", "已尝试步骤的记录。", safe_photo],
                "contacts": ["工程师 / 厂商（设备问题）。", "主管（影响课程时）。"],
                "next_actions": ["保存证据并升级工程师/厂商。", "影响课程时同步主管。"],
                "do_not_decide_without_approval": ["不要尝试未记录的重置/校准步骤。", "不要编造硬件损坏或根因。"],
            }
        return {
            "lead": "Documented fix did not work: stop repeating undocumented attempts, save evidence, and escalate to engineer/vendor; notify the supervisor if class is affected.",
            "steps": [
                "Stop repeating the same fix or trying undocumented reset/calibration steps.",
                "Save photo/video evidence and record the exact symptom, time, course step, and what was tried.",
                "Escalate to engineer/vendor.",
                "Notify the supervisor if class is affected.",
                "Do not invent hardware-damage, root-cause, reset, or calibration steps.",
            ],
            "information_to_collect": ["Exact symptom and time.", "Source-recorded step tried and result.", "Class/session and device status."],
            "evidence_requested": ["Photo/video evidence.", "Screen/connection/error state.", "Record of the attempted source step.", safe_photo],
            "contacts": ["Engineer/vendor (device issue).", "Supervisor (when class is affected)."],
            "next_actions": ["Save evidence and escalate to engineer/vendor.", "Notify supervisor if class is affected."],
            "do_not_decide_without_approval": ["Do not try undocumented reset/calibration steps.", "Do not invent hardware damage or root cause."],
        }

    data: Dict[str, Dict[str, Any]]
    if zh:
        data = {
            IPAD_PAD_POWER_OR_OPEN: {
                "lead": "iPad 没电 / 无法开机或充电：源文件没有记录 iPad 电池/电源修复方法。先确认已接电充电并保持供电、保存证据；若无法恢复，上报 ALLCPR 并升级工程师/厂商，影响课程时通知主管。",
                "steps": [
                    "确认 iPad 已连接自己的电源线/充电器，且插座或插线板确实有电（巡检 SOP 要求 iPad 全程保持连接电源）。",
                    "让它充几分钟电，查看是否有充电指示或能否开机。",
                    "拍摄 iPad 屏幕、充电线以及电源/充电状态的照片/视频。",
                    "若仍无法开机，源文件没有记录 iPad 电池/电源的修复方法——不要拆机、重置或维修。",
                    "保存证据，记录具体现象、时间和是否影响课程，然后上报 ALLCPR 并升级工程师/厂商；影响课程时通知主管。",
                ],
                "information_to_collect": ["iPad 电源/充电状态（是否插电、有无充电指示）。", "屏幕表现和发生时间。", "是否影响当前课程。"],
                "evidence_requested": ["iPad 屏幕照片/视频。", "电源/充电线与充电状态照片。", "具体报错或无反应状态。", safe_photo],
                "contacts": ["ALLCPR（上报无法恢复的设备问题）。", "工程师 / 厂商（无记录修复或仍打不开）。", "主管（影响课程时）。"],
                "next_actions": ["确认已接电充电并保存证据。", "无记录修复或仍打不开 → 上报 ALLCPR 并升级工程师/厂商。"],
                "do_not_decide_without_approval": ["未经授权不得拆卸或维修 iPad。", "不要尝试未记录的重置、校准或根因判断。"],
            },
            BLUETOOTH_CONNECTION: {
                "lead": "蓝牙连接问题：只使用源文件记录的供电与重启假人步骤；无效时保存证据并升级。",
                "steps": [
                    "用插线板让假人和 PAD 保持供电。",
                    "如果插电后仍连不上，只使用来源记录的重启假人步骤。",
                    "若仍失败，保存照片/视频和具体连接状态。",
                    "升级工程师/厂商；如影响课程，通知主管。",
                    "不要尝试未记录的重置、校准或根因判断。",
                ],
                "information_to_collect": ["供电状态。", "蓝牙连接状态。", "已尝试步骤和结果。"],
                "evidence_requested": ["PAD/假人连接状态照片。", "供电状态照片。", "失败提示或无连接状态。", safe_photo],
                "contacts": ["工程师 / 厂商（仍失败）。", "主管（影响课程时）。"],
                "next_actions": ["按来源记录的供电/重启假人步骤处理。", "无效则升级工程师/厂商。"],
            },
            TRAINING_NO_DATA: {
                "lead": "PAD 显示 connected 但 TRAINING 没数据：源文件记录了该现象。先确认 PAD 连接状态与 TRAINING 无数据，再按来源供电步骤处理；无效则升级。",
                "steps": [
                    "确认 PAD 显示 connected。",
                    "确认 TRAINING 页面确实收不到数据。",
                    "用插线板让假人和 PAD 保持供电。",
                    "如果仍无数据，保存照片/视频并升级工程师/厂商。",
                    "不要编造浏览器权限、Wi-Fi 或校准修复。",
                ],
                "information_to_collect": ["PAD connected 状态。", "TRAINING 无数据表现。", "供电状态和发生时间。"],
                "evidence_requested": ["PAD connected 屏幕。", "TRAINING 无数据画面。", "供电/连接状态照片。", safe_photo],
                "contacts": ["工程师 / 厂商（仍无数据）。", "主管（影响课程时）。"],
                "next_actions": ["确认 connected + no data。", "按来源供电步骤处理，无效则升级。"],
            },
            BLACK_SCREEN_APP_RESTART: {
                "lead": "黑屏/app 自重启：源文件记录了该问题，但未记录修复方法。不要编造恢复步骤，直接保存证据并升级。",
                "steps": [
                    "确认是黑屏、app 自重启或进度丢失。",
                    "源文件记录该问题，但没有记录修复方法。",
                    "保存照片/视频、发生时间和课程步骤。",
                    "升级工程师/厂商；如影响课程，通知主管。",
                    "不要尝试未记录的重置、恢复或校准步骤。",
                ],
                "information_to_collect": ["黑屏/重启/进度丢失的确切表现。", "发生时间与课程步骤。", "供电/显示/PAD 状态。"],
                "evidence_requested": ["黑屏或重启视频/照片。", "进度丢失/课程状态截图。", safe_photo],
                "contacts": ["工程师 / 厂商。", "主管（影响课程时）。"],
                "next_actions": ["保存证据。", "升级工程师/厂商。"],
            },
            COMPLETION_PHOTO: {
                "lead": "完成照片：源文件要求拍 All Session Done / Pass 界面并邮件到 support@allcpr.org。",
                "steps": [
                    "确认出现 All Session Done / Pass 界面。",
                    "拍摄该完成界面。",
                    "将照片邮件发送到 support@allcpr.org。",
                    "记录学员、班级和会话信息。",
                    "如果已经漏拍，升级主管；不要编造证书/完课政策。",
                ],
                "information_to_collect": ["学员、班级、会话信息。", "是否已看到完成界面。", "是否已发送邮件。"],
                "evidence_requested": ["All Session Done / Pass 界面照片。", "发送邮件记录。", safe_photo],
                "contacts": ["support@allcpr.org（完成照片）。", "主管（漏拍或证书问题）。"],
                "next_actions": ["拍完成界面并邮件到 support@allcpr.org。", "漏拍或证书问题 → 上报主管。"],
                "do_not_decide_without_approval": ["不要编造证书/完课政策、签发时限或补发规则。"],
            },
            WRONG_ROOM_FLOOR: {
                "lead": "找不到房间/走错楼层：使用来源支持的课堂查找视频、房间/大门资料，并按来源记录增加/使用指示牌；仍找不到时上报。",
                "steps": [
                    "核对地址、楼层和房间。",
                    "使用课堂查找视频和来源支持的房间/大门资料。",
                    "使用或增加指示牌（来源记录：二楼增添指示牌）。",
                    "若学员仍找不到或课程受影响，通知主管。",
                ],
                "information_to_collect": ["实际地址/楼层/房间。", "学员走错的位置。", "现场指示牌状态。"],
                "evidence_requested": ["地址/房间分配截图。", "入口/楼层/指示牌照片。", safe_photo],
                "contacts": ["主管（影响课程时）。", "场地/物业（建筑或指示问题）。"],
                "next_actions": ["核对地址/楼层/房间并使用来源资料。", "仍找不到或影响课程 → 上报主管。"],
            },
        }
    else:
        data = {
            IPAD_PAD_POWER_OR_OPEN: {
                "lead": "iPad has no battery / will not power on or charge: the source records no iPad battery/power fix. Confirm it is on charge and stays powered, save evidence, and report to ALLCPR / escalate to engineer/vendor if it does not recover.",
                "steps": [
                    "Confirm the iPad is connected to its own power cable/charger and the outlet or power strip actually has power (the inspection SOP requires the iPad to stay connected to power).",
                    "Leave it charging for a few minutes and check for a charging indicator or that it powers on.",
                    "Take a photo/video of the iPad screen, the charging cable, and the power/charging state.",
                    "If it still will not power on, no documented iPad/PAD open/power fix (battery included) is recorded in the source — do not open, reset, or repair it.",
                    "Save the evidence, note the exact symptom, time, and whether class is affected, then report to ALLCPR and escalate to engineer/vendor; notify the supervisor if class is affected.",
                ],
                "information_to_collect": ["iPad power/charging state (plugged in, charging indicator).", "Screen behavior and time.", "Whether class is affected."],
                "evidence_requested": ["Photo/video of iPad screen.", "Photo of the charging cable and power/charging state.", "Exact error or no-response state.", safe_photo],
                "contacts": ["ALLCPR (report unresolved device issues).", "Engineer/vendor (no documented fix or still not opening).", "Supervisor (when class is affected)."],
                "next_actions": ["Confirm it is on charge and save evidence.", "No documented fix or still not opening → report to ALLCPR and escalate to engineer/vendor."],
                "do_not_decide_without_approval": ["Do not dismantle or repair the iPad without authorization.", "Do not try undocumented reset, calibration, or root-cause steps."],
            },
            BLUETOOTH_CONNECTION: {
                "lead": "Bluetooth connection issue: use only the source-recorded power-strip and manikin-restart steps; if that fails, save evidence and escalate.",
                "steps": [
                    "Keep the manikin and PAD powered with the power strip.",
                    "If it still will not connect while plugged in, use only the source-recorded manikin restart step.",
                    "If it still fails, save photo/video and the exact connection state.",
                    "Escalate to engineer/vendor; notify supervisor if class is affected.",
                    "Do not try undocumented reset, calibration, or root-cause steps.",
                ],
                "information_to_collect": ["Power state.", "Bluetooth connection state.", "What was tried and result."],
                "evidence_requested": ["Photo of PAD/manikin connection state.", "Photo of power state.", "Failure message or no-connection state.", safe_photo],
                "contacts": ["Engineer/vendor (still failing).", "Supervisor (when class is affected)."],
                "next_actions": ["Use the source-recorded power/restart steps.", "Escalate to engineer/vendor if they fail."],
            },
            TRAINING_NO_DATA: {
                "lead": "PAD connected but TRAINING receives no data: the source records this condition. Confirm connected/no-data state, use the source-backed power step, and escalate if it still fails.",
                "steps": [
                    "Confirm the PAD says connected.",
                    "Confirm TRAINING receives no data.",
                    "Keep the manikin and PAD powered with the power strip.",
                    "If TRAINING still receives no data, save photo/video evidence and escalate to engineer/vendor.",
                    "Do not invent browser-permission, Wi-Fi, or calibration fixes.",
                ],
                "information_to_collect": ["PAD connected state.", "TRAINING no-data behavior.", "Power state and time."],
                "evidence_requested": ["PAD connected screen.", "TRAINING no-data screen.", "Power/connection state photo.", safe_photo],
                "contacts": ["Engineer/vendor (still no data).", "Supervisor (when class is affected)."],
                "next_actions": ["Confirm connected + no data.", "Use source-backed power step; escalate if it fails."],
            },
            BLACK_SCREEN_APP_RESTART: {
                "lead": "Black screen/app restart: the source records the issue but no documented fix. Save evidence and escalate; do not improvise recovery steps.",
                "steps": [
                    "Confirm whether this is black screen, app self-restart, or lost progress.",
                    "The source records this issue but no documented fix.",
                    "Save photo/video, exact time, and course step.",
                    "Escalate to engineer/vendor; notify supervisor if class is affected.",
                    "Do not try undocumented reset, recovery, or calibration steps.",
                ],
                "information_to_collect": ["Exact black-screen/restart/progress-loss symptom.", "Time and course step.", "Power/display/PAD status."],
                "evidence_requested": ["Photo/video of black screen or restart.", "Progress/course-state screenshot.", safe_photo],
                "contacts": ["Engineer/vendor.", "Supervisor (when class is affected)."],
                "next_actions": ["Save evidence.", "Escalate to engineer/vendor."],
            },
            COMPLETION_PHOTO: {
                "lead": "Completion photo: the source requires the All Session Done / Pass screen photo and email to support@allcpr.org.",
                "steps": [
                    "Confirm the All Session Done / Pass screen is visible.",
                    "Take a photo of that completion screen.",
                    "Email the photo to support@allcpr.org.",
                    "Record student, class, and session details.",
                    "If the photo was missed, escalate; do not invent completion/certificate policy.",
                ],
                "information_to_collect": ["Student/class/session details.", "Whether the completion screen was reached.", "Whether the email was sent."],
                "evidence_requested": ["All Session Done / Pass photo.", "Email-send record.", safe_photo],
                "contacts": ["support@allcpr.org (completion photo).", "Supervisor (missed photo or certificate issue)."],
                "next_actions": ["Photograph completion screen and email support@allcpr.org.", "Missed photo or certificate issue → escalate."],
                "do_not_decide_without_approval": ["Do not invent certificate/completion policy, issuance timelines, or re-issue rules."],
            },
            WRONG_ROOM_FLOOR: {
                "lead": "Wrong room/floor: use source-backed classroom-finding video and room/gate materials, plus signage notes; escalate if students still cannot find class.",
                "steps": [
                    "Confirm the address, floor, and room.",
                    "Use the classroom-finding video and source-backed room/gate materials.",
                    "Use or add signage where source-backed (recorded note: add 2F signage).",
                    "If students still cannot find the class or class is affected, notify supervisor.",
                ],
                "information_to_collect": ["Actual address/floor/room.", "Where students went wrong.", "Signage status."],
                "evidence_requested": ["Address/room assignment screenshot.", "Entrance/floor/signage photos.", safe_photo],
                "contacts": ["Supervisor (when class is affected).", "Venue/property (building/signage issue)."],
                "next_actions": ["Confirm address/floor/room and use source materials.", "Escalate if students still cannot find class."],
            },
        }
    return data.get(subissue)
