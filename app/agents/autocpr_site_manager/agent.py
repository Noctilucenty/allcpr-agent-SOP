"""AutoCPR Site Management Specialist agent (deterministic 管点 MVP).

Pipeline per request:
1. classify the scenario (deterministic keyword rules) — ``scenarios.classify``
2. retrieve supporting KB chunks for provenance — ``SiteManagerRetriever``
3. build a structured site-operations incident answer from a fixed, source-aware
   guidance block — ``prompts.SCENARIO_GUIDANCE``
4. decide severity, confidence, evidence requests, contacts, and human review.

There is **no LLM and no paid API** here. Answers are assembled from the in-repo
SOP/KB only. Company decisions (reschedule/refund/policy/price), device root
causes, and anything not in the source files are surfaced with the exact phrases
``needs official SOP source`` / ``data not provided`` /
``needs engineer/vendor confirmation`` and routed to human review. The agent
records attachment *descriptions* only — it does not analyze image content.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import prompts
from .retriever import SiteManagerRetriever
from .scenarios import classify, requires_review
from .schemas import AgentAnswer, RetrievedChunk


def _unique_sources(chunks: List[RetrievedChunk]) -> List[str]:
    seen: List[str] = []
    for c in chunks:
        if c.source not in seen:
            seen.append(c.source)
    return seen


def _glist(block: Dict[str, Any], key: str) -> List[str]:
    return list(block.get(key, []) or [])


_LABELS: Dict[str, Dict[str, str]] = {
    "en": {
        "issue_type": "Issue type:",
        "severity": "Severity:",
        "immediate_safety_check": "Immediate safety check",
        "scenario": "Scenario:",
        "guidance": "Guidance:",
        "steps": "Step-by-step handling",
        "information_to_collect": "Information to collect",
        "evidence_requested": "Evidence to upload",
        "contacts": "Who to contact / escalate to",
        "customer_communication": "Student/customer communication",
        "do_not_decide_without_approval": "Do not decide without approval",
        "attachments": "Attachments:",
        "next_actions": "Next actions",
        "human_review": "Human review:",
        "sources": "Sources used:",
        "source_status": "Source status:",
        "sources_missing": "No direct KB match; using general operations guidance.",
        "review_required": (
            "Human review required — cost/contract/safety/customer decisions or uncertain "
            "information may be involved. Do not make external promises or decisions before "
            "supervisor confirmation."
        ),
        "review_not_required": (
            "Information reference only; no mandatory human review. Escalate if a decision "
            "or policy issue appears."
        ),
    },
    "zh": {
        "issue_type": "问题类型：",
        "severity": "严重程度：",
        "immediate_safety_check": "立即安全检查",
        "scenario": "场景分类：",
        "guidance": "处理建议：",
        "steps": "处理步骤",
        "information_to_collect": "需收集信息",
        "evidence_requested": "需上传/保存证据",
        "contacts": "联系与升级",
        "customer_communication": "学员/客户沟通",
        "do_not_decide_without_approval": "未经批准不得决定",
        "attachments": "附件：",
        "next_actions": "下一步",
        "human_review": "需人工复核：",
        "sources": "引用来源：",
        "source_status": "来源状态：",
        "sources_missing": "无直接命中；按通用运营建议处理。",
        "review_required": "需人工复核 — 涉及成本/合同/安全/客户决定或不确定信息，请在主管确认前不要据此对外承诺或自行决定。",
        "review_not_required": "信息性参考；涉及决定/政策时仍需上报。",
    },
}


def _source_status_display(statuses: List[str], lang: str) -> str:
    if lang != "zh":
        return "; ".join(statuses)
    displayed = []
    for status in statuses:
        if status == prompts.SS_GENERAL:
            displayed.append(f"{status} / 非官方 SOP 的通用运营建议")
        else:
            displayed.append(status)
    return "; ".join(displayed)


def _summarize_attachments(context: Optional[Dict[str, Any]], lang: str) -> str:
    """Return a non-analytic acknowledgement string for any attachments, else ''."""
    if not context:
        return ""
    atts = context.get("attachments")
    if not atts or not isinstance(atts, list):
        return ""
    descs = []
    for a in atts:
        if isinstance(a, dict):
            label = a.get("description") or a.get("filename") or a.get("type") or "attachment"
            descs.append(str(label))
    count = len(descs)
    listed = "; ".join(descs[:6])
    ack = prompts.ATTACHMENT_ACK_EN if lang == "en" else prompts.ATTACHMENT_ACK
    if not listed:
        return ack
    if lang == "en":
        return f"{ack} ({count}: {listed})"
    return f"{ack}（共 {count} 个：{listed}）"


def _section(title: str, body: Any) -> str:
    """Render one titled section; ``body`` may be a str or a list of strings."""
    if not body:
        return ""
    if isinstance(body, list):
        # number step lists, bullet everything else (caller picks via title)
        lines = "\n".join(f"- {item}" for item in body)
        return f"{title}\n{lines}"
    sep = " " if title.endswith(":") else ""
    if not title.endswith((":", "：")):
        sep = " "
    return f"{title}{sep}{body}"


class SiteManagerAgent:
    """Deterministic 管点 agent over the local SOP/KB.

    Pass a custom ``retriever`` for tests; otherwise one is built lazily from the
    packaged markdown KB.
    """

    def __init__(self, retriever: Optional[SiteManagerRetriever] = None) -> None:
        self._retriever = retriever or SiteManagerRetriever()

    def answer(self, question: str, context: Optional[Dict[str, Any]] = None) -> AgentAnswer:
        question = question or ""
        lang = prompts.detect_language(question, context)
        scenario = classify(question, context)
        guidance = prompts.guidance_for(scenario, lang)
        chunks = self._retriever.search(question, top_k=4)

        # ---- human review decision ----------------------------------------
        review = requires_review(scenario)
        if prompts.has_escalation_trigger(question):
            review = True
        if prompts.has_missing_data_trigger(question):
            review = True
        if not chunks and scenario in {
            "zip_site_evaluation",
            "dashboard_metric_explanation",
            "site_opening_reference",
        }:
            review = True

        # ---- confidence ----------------------------------------------------
        if scenario == "unknown":
            confidence = "low"
        elif review:
            confidence = "medium"
        else:
            confidence = "high"

        # ---- structured fields (from source-aware guidance) ----------------
        issue_type = str(guidance.get("issue_type", scenario))
        severity = str(guidance.get("severity", "medium"))
        immediate_safety_check = _glist(guidance, "immediate_safety_check")
        steps = _glist(guidance, "steps")
        information_to_collect = _glist(guidance, "information_to_collect")
        evidence_requested = _glist(guidance, "evidence_requested")
        contacts = _glist(guidance, "contacts")
        customer_communication = _glist(guidance, "customer_communication")
        do_not_decide = _glist(guidance, "do_not_decide_without_approval")
        next_actions = _glist(guidance, "next_actions")
        source_status = _glist(guidance, "source_status")
        sources = _unique_sources(chunks)

        attach_ack = _summarize_attachments(context, lang)

        # ---- compose the human-readable answer -----------------------------
        labels = _LABELS[lang]
        review_line = labels["review_required"] if review else labels["review_not_required"]
        sources_text = ", ".join(sources) if sources else labels["sources_missing"]
        source_status_text = _source_status_display(source_status, lang)

        parts = [
            _section(labels["issue_type"], issue_type),
            _section(labels["severity"], severity),
            _section(labels["immediate_safety_check"], immediate_safety_check),
            _section(labels["scenario"], scenario),
            _section(labels["guidance"], str(guidance.get("lead", ""))),
            _section(labels["steps"], steps),
            _section(labels["information_to_collect"], information_to_collect),
            _section(labels["evidence_requested"], evidence_requested),
            _section(labels["contacts"], contacts),
            _section(labels["customer_communication"], customer_communication),
            _section(labels["do_not_decide_without_approval"], do_not_decide),
            _section(labels["attachments"], attach_ack),
            _section(labels["next_actions"], next_actions),
            _section(labels["human_review"], review_line),
            _section(labels["sources"], sources_text),
            _section(labels["source_status"], source_status_text),
        ]
        answer_text = "\n\n".join(p for p in parts if p).strip()

        return AgentAnswer(
            answer=answer_text,
            scenario=scenario,
            confidence=confidence,
            sources=sources,
            needs_human_review=review,
            next_actions=next_actions,
            language=lang,
            issue_type=issue_type,
            severity=severity,
            immediate_safety_check=immediate_safety_check,
            steps=steps,
            information_to_collect=information_to_collect,
            evidence_requested=evidence_requested,
            contacts=contacts,
            customer_communication=customer_communication,
            do_not_decide_without_approval=do_not_decide,
            source_status=source_status,
            attachments_note=attach_ack,
        )


# Lazily-built module singleton so importing the package stays cheap and app
# startup is never blocked by index construction.
_AGENT: Optional[SiteManagerAgent] = None


def get_agent() -> SiteManagerAgent:
    global _AGENT
    if _AGENT is None:
        _AGENT = SiteManagerAgent()
    return _AGENT


def answer_question(question: str, context: Optional[Dict[str, Any]] = None) -> AgentAnswer:
    """Convenience entry point used by the API endpoint and tests."""
    return get_agent().answer(question, context)
