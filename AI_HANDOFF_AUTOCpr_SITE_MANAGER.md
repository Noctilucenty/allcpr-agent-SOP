# AutoCPR Site Manager Agent — AI Handoff

> Persistent context file so any AI (or teammate) can continue this work if
> interrupted. Update after every meaningful step.

## Move to Standalone Repo (2026-06-26)
Canonical location is now `~/Desktop/Developer/allcpr_agent`.

- `/` and `/agent` both serve the AllCPR Site Operations Agent UI.
- `POST /api/agents/autocpr-site-manager/ask` remains the structured agent API.
- Smart Manikin SOP source folders were moved into `SOP/Smart Manikin*` here
  rather than duplicated.
- The old `maps-scraper-intel` dashboard should no longer carry the agent route,
  UI, tests, or handoff.
- Run:

```bash
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 -m uvicorn web_app:app --host 127.0.0.1 --port 8012
```

## Bilingual Agent Upgrade (2026-06-26)
The agent now supports English and Chinese responses. Language is selected by
`context.lang`, `context.language`, or `context.locale` first (`en`, `english`,
`en-US`, `zh`, `zh-CN`, `chinese`, `中文` are normalized), then by deterministic
CJK detection in the question. The `/agent` page includes a language selector and
sends `context.lang` to `POST /api/agents/autocpr-site-manager/ask`.

- **Files changed:** `app/agents/autocpr_site_manager/prompts.py`,
  `app/agents/autocpr_site_manager/agent.py`,
  `app/agents/autocpr_site_manager/schemas.py`,
  `app/agents/autocpr_site_manager/scenarios.py`,
  `app/web/site_ops_agent.html`,
  `tests/agents/test_autocpr_site_manager_agent.py`,
  `tests/agents/test_autocpr_site_manager_scenarios.py`,
  `tests/test_web_app.py`, and this handoff file.
- **Behavior:** Chinese questions return Chinese headings/guidance; English
  questions return English headings/guidance; mixed questions honor the context
  language when provided. `AgentAnswer.language` records the selected language.
  `AgentAnswer.attachments_note` records the non-visual attachment acknowledgement.
- **Source fidelity:** Source filenames and `source_status` values remain
  traceable. Chinese prose adds `非官方 SOP 的通用运营建议` beside
  `general operations guidance, not official SOP`. Smart Manikin black-screen /
  app-restart still says the source records the issue but no documented fix is
  recorded, and routes to `needs engineer/vendor confirmation`; no Wi-Fi/browser/
  permissions/reset/calibration/root-cause/vendor diagnosis was added.
- **Attachment/image handling:** Attachment descriptions are acknowledged only.
  English: "Attachment descriptions received; if visual confirmation is needed, a
  human should review the images. This assistant does not analyze image content."
  Chinese: "已收到附件描述；如需视觉确认请人工查看照片（本助手不分析图片内容）。"
- **Tests run:** `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12
  -m pytest tests/agents tests/test_web_app.py tests/test_healthcheck.py -q`
  → **138 passed**.
- **Live verification:** ran
  `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 -m uvicorn
  web_app:app --host 127.0.0.1 --port 8012`; verified `GET /agent` returns 200,
  the HTML contains `English`, `中文`, `Ask Agent`, the endpoint URL, and
  `lang:selectedLang`; verified live POSTs for:
  `What should I do if the power goes out?` → English outage response;
  `停电了怎么办？` → Chinese outage response;
  `The Smart Manikin screen is black. What should I do?` → English response with
  `no documented fix` + `needs engineer/vendor confirmation` and no unsupported
  Smart Manikin terms; attachment metadata → acknowledgement without image
  analysis. In-app browser automation was not exposed in this session, so visual
  click-through was verified by live HTML/API checks instead.
- **Remaining issues:** no known bilingual implementation issues. Official SOP
  gaps remain the same: refund/reschedule/certificate policy, official customer
  notices, final class-continuation decisions, vendor hardware diagnosis, and
  contact lists still require source/human review.

## Update — Pivot to 管点 / Site Operations agent (2026-06-26)
The MVP was upgraded from a static Q&A endpoint into a structured **site-operations
incident** agent. Existing work (retriever, KB loader, fidelity-audited Smart
Manikin content, endpoint, tests, handoff) was **reused, not rebuilt**.

- **New primary scenarios:** `site_operations_general`, `electricity_outage`,
  `internet_outage`, `venue_access_issue`, `smart_manikin_troubleshooting`,
  `class_cannot_start`, `instructor_no_show`, `student_checkin_issue`,
  `completion_or_certificate_issue`, `safety_or_emergency`, `incident_report`,
  `escalation_guidance`, `site_opening_reference`, `dashboard_metric_explanation`,
  `zip_site_evaluation`, `course_type_recommendation`, `unknown`. Old site-intel
  labels (sop_training, competitor_analysis, enrichment_data_check,
  missing_data_troubleshooting, improvement_optimization) are kept for backward
  compatibility. Rule order: **safety first**; a named cause (instructor/outage/
  venue/device) beats the generic `class_cannot_start` symptom.
- **Structured `AgentAnswer`** (new optional fields, backward compatible):
  `issue_type, severity, immediate_safety_check, steps, information_to_collect,
  evidence_requested, contacts, customer_communication,
  do_not_decide_without_approval, source_status` — plus the original six fields.
- **Photo/evidence support:** every incident asks for safe evidence with the exact
  wording "如果安全且不影响处理，请上传/保存照片或截图作为证据。" Safety scenarios put
  people before photos. `context.attachments` (descriptions only) is acknowledged
  with "已收到附件描述；如果需要视觉确认，请人工查看照片。" — the agent does NOT analyze
  image content.
- **Common-knowledge rule:** general incident triage is allowed but always labeled
  `general operations guidance, not official SOP`; company decisions (reschedule/
  refund/policy/price) remain `needs official SOP source`.
- **Smart Manikin strict-source rule kept:** Bluetooth/power + completion-photo +
  wrong-room/signage are source-supported; black-screen/app-restart has no recorded
  fix → `needs engineer/vendor confirmation`; no browser/permissions/Wi-Fi as
  device dependencies; no invented root cause/reset/calibration/vendor/cert rules.
- **Files changed:** `schemas.py`, `scenarios.py`, `prompts.py`, `agent.py`,
  `sop.md` (15-section ops SOP + opening appendix), `kb_seed.md` (ops + metadata
  plan), `README.md` (answers Claude Wang's 1–5), all three test files, this file.
  Endpoint unchanged: `POST /api/agents/autocpr-site-manager/ask`.
- **Tests run (framework python, venv pytest still broken):**
  `…/python3.12 -m pytest tests/agents tests/test_web_app.py tests/test_healthcheck.py -q`
  → **112 passed**.
- **Remaining official data needed:** official 管点 SOP (if separate); electricity-
  outage policy; internet-outage policy; venue contact process; escalation contact
  list; reschedule/refund rules when class can't continue; instructor no-show
  policy; customer/student notification templates; Smart Manikin vendor
  troubleshooting tree/contact; image/evidence retention policy.

## Current Task
Build the MVP foundation for an **AutoCPR Site Management Specialist Digital
Human Agent** inside `~/Desktop/Developer/maps-scraper-intel`.

## Boss Request Context
Claude Wang requested a plan around:
1）技术路径 2）SOP 3）矢量数据库 / KB 4）场景设计 5）改进优化

He also asked Kenny to share: `AutoCPR 开点 SOP（专员版）`.

**Update (resolved during this build):** the user clarified that the SOP is
**already in the repo**, inside the three `SOP/Smart Manikin*` folders. Those
documents ARE the working specialist site-opening SOP (see "SOP Folder Check").
So the agent is built on real source content, not placeholders. Anything still
genuinely unstated (e.g. a single canonical, signed-off "open/no-open"
ZIP-score cutoff that ties the dashboard's modeled ZIP score to the field
选址评分表) is still marked `needs official SOP source`.

## Correct Interpretation
This agent is **NOT** mainly an ALLCPR.org customer-service chatbot.

Core = `AutoCPR 开点 SOP（专员版）` (the Smart Manikin 新点开发 / New Market
Expansion SOP) + site-opening / site-management specialist workflow + Site
Intelligence Dashboard guidance.

`maps-scraper-intel` is the supporting data engine for ZIP/city/site
evaluation. ALLCPR.org is only supporting business/course background. Smart
Manikin SOPs are supporting equipment/operations knowledge.

## Repo / Working Directory
Work only inside: `~/Desktop/Developer/maps-scraper-intel`
Do NOT create `~/Desktop/ALLCPR_agent`. Do NOT modify unrelated dashboard/API
behavior. Do NOT use paid APIs. Do NOT print/store secrets.

## SOP Folder Check
`SOP/` exists at repo root. It contains three near-parallel folders:
`Smart Manikin`, `Smart Manikin 2`, `Smart Manikin 3` (folders 1 and 3 are
duplicates of each other; folder 2 holds the extra/unique material). Full file
inventory and per-file summaries are in
`app/agents/autocpr_site_manager/sop_source_analysis.md`.

The text-extractable SOP documents (read this build) were extracted with:
- `.docx`  → macOS `textutil -convert txt` (no pip dep)
- `.xlsx` / `.xlsm` → `openpyxl` (already a project dependency)
- `.pptx`  → `zipfile` + XML (no pip dep)
- `.pdf`   → not extracted (no `pdftotext`/`mutool` installed; field-assessment
  PDFs duplicate the `现场考察表.docx` content which WAS read).

## Key SOP Findings (real source content — citable, not invented)
- **`Smart Manikins 新地点开发 SOP.docx`** = `Gosvea 2026 SM-BD-SOP-001` V1.1,
  发布 06/05/2026, 责任部门 BD, **审批人 Kenny**. The specialist site-opening
  workflow: ZipCode 初筛 (A/B/C) → 潜在 ZipCode 确认 → L1 场地整理 → 拜访名单 →
  实地考察 (Field Assessment Form) → 选址评分表更新 → BD 复核 → 管理层审批 →
  虚拟课程测试 → 教具采购/装修 → 开业验收. Includes hard-elimination conditions
  and L1–L4 status model.
- **`Untitled document.docx`** = English "Smart Manikin New Market Expansion
  SOP" V1.0, 04/10/2026, owner Kenny Team. 9-step expansion workflow, team
  roles (Kenny/AL/Jonathon/Daniel/Andy), student-journey control points, KPIs,
  risk management, escalation rules, exit/hold criteria.
- **`Smart Manikin 选址评分表.xlsm`** = the OFFICIAL site-selection scoring
  model. `Final = 0.12P + 0.10C + 0.08T + 0.10D + 0.15L + 0.18S + 0.12B +
  0.15O`. Inputs scored 100/85/70/50/20. Decision bands: **≥85 Priority
  Candidate; 75–84.9 Management Review; 65–74.9 Hold/Compare; <65 Reject**.
  Hard elimination: access control can't be installed; camera can't be
  installed; network fails; unfixable blind spot; high safety risk.
- **`Smart Manikin 现场考察表.docx`** = the Field Assessment Form (site,
  parking, safety, infrastructure, access/security, renovation, compliance,
  final recommendation).
- **`新点审批 邮件申请模版.docx`** = email templates for 场地审批 / 虚拟课程测试
  汇报 / 费用审批. Virtual-course test rule (from BD SOP): CPS 3-day ads (incl.
  one weekend) + Google Ads 7-day; **>5 sign-ups in a week OR 10 total → may
  open**; otherwise management decides.
- **`Smart Manikin ICPIS 合作分点开发与运营 SOP.docx`** = `SM-ICPIS-SOP-001`
  V1.0 — partner/investor operating version (roles, brand control, escalation).
- **`Smart Manikin Instruction.docx` / Quick Start Guide.pptx** = device
  operation steps + student instruction email (room passcode handling, after-
  hours gate access, completion-photo → support@allcpr.org).
- **`Smart Manikins学生问题.xlsx`** = real recurring issues: black-screen/app
  restart loses progress; Bluetooth won't connect unless manikin + pad are
  powered (restart manikin if needed); students go to wrong floor/room (→
  signage); students forget the completion photo.

## Smart Manikin Source-Fidelity Audit (2026-06-26)
Re-inspected the actual files (not the earlier summary) to confirm every Smart
Manikin claim is directly supported, per the user's instruction to use only what
the source documents say. Files re-read:
`SOP/Smart Manikin 2/Smart Manikins学生问题.xlsx` (sheet 学生问题),
`SOP/Smart Manikin 2/Smart Manikin Instruction.docx`,
`SOP/Smart Manikin 2/场地漏斗/3200 Patrick Henry Dr.../Santa Clara Instruction.docx`.

Verified-and-kept (quoted in the docs):
- Device flow, module names (First Aid/CPR/AED vs BLS Healthcare Provider), pocket
  mask vs BVM, "Push Deeper" / "Rate too fast", "ALL Session Done and Pass → photo
  → email support@allcpr.org → certificate" — all in `Smart Manikin Instruction.docx`.
- Bluetooth fix ("放置一个插线板...若插电也显示连接不上时，重启manikins"; PAD shows
  connected while unplugged-but-powered yet TRAINING gets no data) — student-issue
  sheet, freq 4.
- Wrong floor/room → "二楼增添指示牌" (freq 2–3); forgot completion photo (freq 2);
  room/gate passcode + classroom video — student sheet + Instruction.docx.

Corrected (were NOT supported → fixed in sop.md/kb_seed.md/prompts.py/source
analysis):
1. **Black-screen / app self-restart**: the sheet logs it (freq 3) with the
   当前解决方案 cell **empty** → no recorded fix. Removed the invented "have the
   student restart the attempt"; now framed as no-fix → `needs engineer/vendor
   confirmation`.
2. **Intake checklist** had `browser / permissions / Wi-Fi/cellular` (from the
   original task prompt, not the files). Removed them; the Santa Clara file records
   "无Wi-Fi" and the session runs over the Bluetooth PAD↔manikin link. Intake is now
   power / display / in-course session / Bluetooth / tablet-PAD only.
A regression test (`test_smart_manikin_troubleshooting_behavior`) now guards
against re-introducing the invented fix or the unsupported intake factors.

## Files Created / Changed
- `AI_HANDOFF_AUTOCpr_SITE_MANAGER.md` (this file)
- `app/agents/__init__.py`
- `app/agents/autocpr_site_manager/__init__.py`
- `app/agents/autocpr_site_manager/README.md`
- `app/agents/autocpr_site_manager/agent.py`
- `app/agents/autocpr_site_manager/schemas.py`
- `app/agents/autocpr_site_manager/kb_loader.py`
- `app/agents/autocpr_site_manager/retriever.py`
- `app/agents/autocpr_site_manager/prompts.py`
- `app/agents/autocpr_site_manager/scenarios.py`
- `app/agents/autocpr_site_manager/sop.md`
- `app/agents/autocpr_site_manager/kb_seed.md`
- `app/agents/autocpr_site_manager/sop_source_analysis.md`
- `tests/agents/__init__.py`
- `tests/agents/test_autocpr_site_manager_agent.py`
- `tests/agents/test_autocpr_site_manager_retriever.py`
- `tests/agents/test_autocpr_site_manager_scenarios.py`
- `web_app.py` (added `POST /api/agents/autocpr-site-manager/ask` + 2-line import
  only; existing routes untouched)
- `tests/test_web_app.py` (one-line fix: `test_health` now asserts against
  `app.config.PRODUCT_VERSION` instead of the stale literal `"v1.0.0"`)

## Endpoint
`POST /api/agents/autocpr-site-manager/ask`
Request: `{ "question": str, "context": { "zip"?, "city"?, "course_type"?,
"audience"?, "stage"? } }`
Response: `AgentAnswer { answer, scenario, confidence, sources,
needs_human_review, next_actions }`.

## How to Run
```bash
# local dashboard + agent endpoint
uvicorn web_app:app --host 0.0.0.0 --port 8000
# then POST to http://localhost:8000/api/agents/autocpr-site-manager/ask
```

## Tests Run (actual results — 2026-06-26)
> **Environment note:** the checked-out `.venv` has a broken pytest
> (`_pytest/_code/*.py` source files missing — only stale `.pyc` remain) and a
> stale interpreter path (`.venv/bin/pip` points at an old
> `~/Desktop/maps-scraper-intel/.venv`, pre-`Developer/` move), so
> `.venv/bin/python -m pytest` and `.venv/bin/pip` fail/hang. The **framework
> Python** `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12`
> has a working pytest 9.0.3 **and** all app deps (fastapi, pydantic, starlette,
> requests, openpyxl, anyio), so the suite was run with it. The venv was **not**
> modified. `.venv/bin/python` still works for plain app imports (it's a symlink
> to the framework python).

```bash
FW=/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12
$FW -m pytest tests/agents -q
#  -> 42 passed
$FW -m pytest tests/test_web_app.py tests/test_healthcheck.py -q
#  -> 39 passed  (after fixing one pre-existing stale assertion, see below)
```

**Pre-existing failure found + fixed (user-confirmed):** `tests/test_web_app.py::
test_health` asserted `version == "v1.0.0"`, but `app/config.py` is `v2.0` (from
the v2.0 release commits, not this work). User confirmed v2.0 is correct; the
assertion now reads from `app.config.PRODUCT_VERSION` so it tracks future bumps.
This was the only edit to an existing test; no existing API/dashboard behavior
was changed.

## Important Behavior Rules (enforced in agent.py / prompts.py)
- Answer only from SOP/KB + available maps-scraper-intel data.
- When official SOP / ZIP score / dashboard metric / internal threshold /
  price / policy / device diagnosis is missing, say one of:
  `needs official SOP source`, `data not provided`,
  `needs engineer/vendor confirmation`.
- No hallucination. No secrets. No paid APIs. No dashboard rewrite. No breaking
  existing tests/API behavior.

## Progress Log
- [done] Confirmed cwd = maps-scraper-intel; learned FastAPI layout (web_app.py
  + app/main.py import; tests use TestClient).
- [done] Confirmed `SOP/` exists; inventoried the three Smart Manikin folders.
- [done] Extracted + read the core SOP docx/xlsm/xlsx (BD SOP, Expansion SOP,
  scoring sheet, field form, ICPIS SOP, device instruction, student issues).
- [done] Created this handoff file + project memory.
- [done] Created `sop_source_analysis.md`.
- [done] Implemented agent package (schemas, scenarios, prompts, kb_loader,
  retriever, agent) + `sop.md` + `kb_seed.md`.
- [done] Added FastAPI endpoint.
- [done] Added tests; ran new tests + web_app regression.
- [done] Wrote README + final report.

## Remaining Work / Future
- Swap the keyword retriever for a real vector DB (pgvector/Chroma/Pinecone)
  when scaling the KB.
- Wire a real LLM (latest Claude model) for answer generation on top of the
  deterministic retrieval (MVP is intentionally deterministic, no LLM).
- Add a digital-human / voice front end.
- Deeper Site Intelligence integration (read modeled ZIP details live).

## Missing Data / Needed From Team
- A single canonical, signed-off ZIP-score → open/no-open cutoff that maps the
  dashboard's modeled ZIP opportunity score to the field 选址评分表 bands.
- Confirmed course-type (AHA vs ARC brand) decision rule — no public dataset
  encodes brand preference; the SOP scores demand tilts, not brand.
- Confirmed Smart Manikin vendor hardware troubleshooting tree (current device
  knowledge is operational symptoms only, not root-cause hardware diagnosis).
- Confirmation of any updated price/policy numbers beyond the example figures
  in the email templates and config.
