# AutoCPR Site Management Specialist Agent — 管点 / Site Operations AI Agent

A deterministic, dependency-light internal AI agent that helps on-site staff
handle real **管点 / site-operations incidents** (停电、断网、门禁、Smart Manikin、
课程无法开始、老师未到、签到、完课/证书、安全、事件记录、升级), grounded in the
in-repo SOP/KB and the `maps-scraper-intel` data engine. Site-opening (开点/选址)
and the Site Intelligence Dashboard are supporting references.

No LLM, no paid APIs, no secrets. Company decisions (reschedule/refund/policy/
price), device root causes, and anything not in the source files are surfaced with
the exact phrases `needs official SOP source` / `data not provided` /
`needs engineer/vendor confirmation` and routed to human review — never invented.

## What it is / is not
- **Is:** an on-site incident assistant for the site-operations specialist —
  safe triage, info + evidence collection, careful customer communication, and
  escalation.
- **Is not** primarily an ALLCPR.org customer-service chatbot. ALLCPR.org is only
  supporting business/course background.
- The old `SOP/` files were analyzed as reference material
  ([`sop_source_analysis.md`](sop_source_analysis.md)); the **Smart Manikin SOPs
  are supporting operational knowledge only** and are used strictly as the files
  document them (see the fidelity rules below).

---

## 1）技术路径 (technical path)
- **Now — text-based internal AI agent:** deterministic pipeline
  `classify → retrieve (BM25 over markdown KB) → compose structured incident
  answer`. Endpoint `POST /api/agents/autocpr-site-manager/ask` returns a
  structured `AgentAnswer` (issue type, severity, safety check, steps, info to
  collect, evidence to upload, contacts, customer comms, do-not-decide, next
  actions, human review, sources, source status).
- **Next — incident workflow form + image/evidence upload:** the request already
  accepts `context.attachments` metadata (descriptions only — the agent does not
  analyze image content unless a real vision pipeline is added).
- **Next — vector DB / KB:** swap the keyword retriever for pgvector/Chroma/
  Pinecone behind the same `SiteManagerRetriever.search` interface; attach the
  metadata plan (below).
- **Next — digital human / voice** front end on top of the same endpoint.
- **Next — production feedback loop:** incident logs → human corrections → SOP/KB
  refresh → new tests.

## 2）SOP
The working SOP ([`sop.md`](sop.md)) is now a 管点/site-operations SOP with these
modules, each carrying issue type · severity · immediate safety check · steps ·
info to collect · evidence · contacts/escalate · customer communication · next
action · human-review condition · source status:
停电 · 断网 · 门禁/教室 · Smart Manikin · 课程无法开始 · 老师未到 · 学员签到 ·
完课/证书 · 安全事件 · 事件记录 · 升级处理 — plus before-class readiness,
post-incident review, and a site-opening reference appendix.

Source status is explicit everywhere: `official SOP source` / `extracted SOP
reference` / `Smart Manikin source` / `general operations guidance, not official
SOP` / `missing source`. Common-sense incident triage is allowed but always
labeled `general operations guidance, not official SOP`; final company decisions
remain `needs official SOP source`.

### Smart Manikin fidelity rules (kept)
Use only what the Smart Manikin source files document. Supported: Bluetooth/power
connection guidance, completion-photo→`support@allcpr.org`, wrong-room→signage.
The black-screen/app-restart issue is logged with **no recorded fix** → must
escalate (`needs engineer/vendor confirmation`), never an invented fix. Browser/
permissions/Wi-Fi are **not** Smart Manikin dependencies (the session runs over
Bluetooth; one site records "无 Wi-Fi"). Never invent root causes, reset/
calibration steps, vendor instructions, hardware diagnoses, or certificate rules.

## 3）矢量数据库 / KB
Sources to index: SOP docs, Smart Manikin docs, incident logs, screenshot/photo
evidence references, escalation contacts, venue docs. MVP = local markdown
([`sop.md`](sop.md), [`kb_seed.md`](kb_seed.md),
[`sop_source_analysis.md`](sop_source_analysis.md)) + stdlib BM25 (bilingual
tokenizer). Each chunk should carry the metadata plan:
```json
{ "doc_type": "site_operations_sop", "issue_type": "electricity_outage",
  "severity": "high", "source_status": "general_operations_guidance",
  "source_file": "SOP/...", "owner": "ops", "last_updated": "..." }
```
Future vector DB: pgvector / Chroma / Pinecone behind the same retriever
interface, optionally with a Claude LLM layered on top for generation.

## 4）场景设计 (demo scenarios)
1. 停电了怎么办？ → `electricity_outage`
2. 教室没网怎么办？ → `internet_outage`
3. 门打不开怎么办？ → `venue_access_issue`
4. Smart Manikin 黑屏怎么办？ → `smart_manikin_troubleshooting`
5. 老师没到怎么办？ → `instructor_no_show`
6. 学生到了但课程无法开始怎么办？ → `class_cannot_start`
7. 完课/证书证据异常怎么办？ → `completion_or_certificate_issue`
8. 现场安全问题怎么办？ → `safety_or_emergency`
Each returns a structured incident answer with safety check, steps, evidence
requests, contacts, customer comms, and human-review flag.

## 5）改进优化 (improvement loop)
Incident logs → human correction loop → unresolved-question log → SOP versioning →
KB refresh → tests built from real incidents → periodic audit for unsupported
claims (especially Smart Manikin).

---

## How to run locally
```bash
uvicorn web_app:app --host 0.0.0.0 --port 8000
curl -s localhost:8000/api/agents/autocpr-site-manager/ask \
  -H 'content-type: application/json' \
  -d '{"question":"停电了怎么办？","context":{"site":"Santa Clara","class_time":"2026-06-26 09:00","attachments":[{"type":"photo","description":"dark classroom","filename":"outage_room.jpg"}]}}'
```
In Python: `from app.agents.autocpr_site_manager import answer_question`.

## How to test
```bash
python -m pytest tests/agents -q
```
> The checked-out `.venv` currently has a broken pytest (`_pytest/_code/*.py`
> missing) and a stale path. Use the framework Python, which has a working pytest
> and all app deps:
> `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 -m pytest tests/agents -q`

## What official data is still needed (from Kenny / Claude / team)
Official 管点 SOP (if separate); electricity-outage policy; internet-outage policy;
venue contact process; escalation contact list; reschedule/refund decision rules
when class cannot continue; instructor no-show policy; customer/student
notification templates; Smart Manikin vendor troubleshooting tree/contact;
image/evidence retention policy; and a signed-off mapping from the modeled ZIP
score to the field `选址评分表` bands.
