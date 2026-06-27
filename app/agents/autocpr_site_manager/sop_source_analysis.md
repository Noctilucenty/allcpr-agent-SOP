# SOP Source Analysis

Analysis of the source material under `SOP/`, produced for the AutoCPR Site
Management Specialist agent. This is an **analysis of reference material**; the
agent's own working SOP is `sop.md` and its KB is `kb_seed.md`.

> The user confirmed the SOP "专员版" is **already in the repo** — it is the set
> of documents inside the three `SOP/Smart Manikin*` folders. Where a number,
> formula, threshold, or rule below is quoted, it is taken directly from those
> source files and may be cited. Anything genuinely unstated is flagged under
> "What Is Not Official Yet".

## SOP Folder Location
`~/Desktop/Developer/maps-scraper-intel/SOP/`

It contains three near-parallel folders:
- `SOP/Smart Manikin/`   (primary)
- `SOP/Smart Manikin 2/` (has the extra/unique material: scoring sheet,
  device instruction, student issues, email templates, proposal)
- `SOP/Smart Manikin 3/` (duplicate of `Smart Manikin/`)

## Files Found (text-bearing documents)
Readable and analyzed:
- `Smart Manikin*/SOP/Smart Manikins 新地点开发 SOP.docx`
- `Smart Manikin*/SOP/Smart Manikin 现场考察表.docx`
- `Smart Manikin*/Untitled document.docx`
- `Smart Manikin*/SOP/附件2 投资人版本SOP/Smart Manikin ICPIS 合作分点开发与运营 SOP.docx`
- `Smart Manikin*/SOP/附件2 投资人版本SOP/ICPIS Weekly Site Check Report.docx`
- `Smart Manikin 2/Smart Manikin Instruction.docx`
- `Smart Manikin 2/Smart Manikin Learning Station_ Quick Start Guide.pptx`
- `Smart Manikin 2/SOP/新点审批 邮件申请模版.docx`
- `Smart Manikin 2/SOP/Short Term Business Trip SOP.docx`
- `Smart Manikin 2/SOP/Smart Manikin 选址评分表.xlsm`
- `Smart Manikin 2/Smart Manikins学生问题.xlsx`
- `Smart Manikin 2/SM 每站点每日注册量.xlsx`, `SM Venue数据表.xlsx`, `Camera.xlsx`,
  `Smart Manikins Insurance Research(.xlsx/Result.docx)`
- `Smart Manikin 2/系统开发proposal/Smart Manikin 一体化 AI 运营平台 Proposal.docx`
- `Smart Manikin*/SOP/附件1 短期出差申请表/*.docx` (trip request/itinerary/log/
  expense/report templates)

Present but NOT machine-read (binary media / scanned forms):
- `*/分点指示牌 1.0版本.pdf`, `场地漏斗/.../field assessment form *.pdf`
  (these PDFs duplicate the `现场考察表.docx` content, which WAS read).
- `场地漏斗/...` photos (`.jpeg/.png`) and walkthrough videos (`.MOV/.mp4`) per
  candidate address — real evidence packets, not text.
- `ALLCPR Smart Manikin Expansion Plan 2026.pptx` (deck, skimmed).

## Per-File Summary

### `Smart Manikins 新地点开发 SOP.docx`  ★ primary specialist SOP
- type: docx | readable: yes
- summary: `Gosvea 2026 SM-BD-SOP-001`, V1.1, 发布 06/05/2026, 责任部门 BD,
  审批人 **Kenny**. Defines the end-to-end specialist (BD 执行人) workflow for
  opening a new Smart Manikin site: ZipCode 初筛 (mark A/B/C) → 潜在 ZipCode 确认
  → L1 候选场地整理 → 拜访名单 (Visit/Call/Need-info/Hold/Reject) → 实地考察 (Field
  Assessment Form + photos/video to the "场地漏斗" Drive) → 选址评分表 update
  within 24h → BD 复核 → 管理层审批 → 虚拟课程 & 站点测试 → 教具采购/装修 → 开业前
  验收/系统测试 → 正式开业.
- useful patterns: stage table (owner / action / output / entry condition);
  "submission packet" standard; hard-elimination conditions; L1–L4 status model;
  exception-handling rule ("do not self-approve anything affecting cost,
  liability, contract, insurance, safety, or operations").
- agent relevance: the backbone of `sop.md` sections 1–13 and the
  `site_opening_checklist` / `escalation_guidance` scenarios.
- limitations: refers out to the scoring sheet and field form for exact fields.

### `Untitled document.docx`  ★ English expansion SOP
- type: docx | readable: yes
- summary: "Smart Manikin New Market Expansion SOP" V1.0, 04/10/2026, owner
  Kenny Team. Strategic/market-level: pilot-first principles, market selection
  criteria (demand/site/business/technical), 9-step workflow, student-journey
  control points, KPIs (market/marketing/operational/scaling), risk management
  (technical/operational/commercial/partner), escalation rules, exit/hold.
- useful patterns: KPI taxonomy; risk → owner → action mapping; escalation
  trigger list; exit/hold criteria.
- agent relevance: `improvement_optimization`, `escalation_guidance`,
  `dashboard_metric_explanation` framing, and post-launch review in `sop.md`.

### `Smart Manikin 选址评分表.xlsm`  ★ official scoring model
- type: xlsm | readable: yes (openpyxl)
- summary: the site-selection score. Sheets: `候选点位评分表` (live candidates,
  e.g. Santa Clara, Newark, SF, Oakland, Mountain View), `评分说明` (formula),
  `现场考察汇报表` (field summary). Formula:
  `Final = 0.12P + 0.10C + 0.08T + 0.10D + 0.15L + 0.18S + 0.12B + 0.15O`
  with sub-weights (e.g. `P = 0.5P1+0.3P2+0.2P3`, `S = 0.25S1+0.25S2+0.15S3+
  0.20S4+0.15S5`). Inputs use a 5-level scale `100/85/70/50/20`. Decision bands:
  **≥85 Priority Candidate; 75–84.9 Management Review; 65–74.9 Hold/Compare;
  <65 Reject**. Hard elimination: access control not installable; camera not
  installable; network not adequate; unfixable blind spot; high safety risk.
- agent relevance: `zip_site_evaluation`, `dashboard_metric_explanation`,
  `competitor_analysis`. The eight dimensions are the vocabulary the agent uses
  to explain "why is this site/ZIP good or not".
- limitations: per-input scoring is human judgement (执行人 fills blue/yellow
  cells; green auto-computes). The score is a comparison tool between candidate
  addresses, not a public ZIP score.

### `Smart Manikin 现场考察表.docx`  ★ field assessment form
- type: docx | readable: yes
- summary: "SMART MANIKIN SITE FIELD ASSESSMENT FORM" — 8 sections: basic info;
  location/area (accessibility, parking, safety, amenities); property/room
  (building, rent/cost, infrastructure); operational feasibility (hours/access,
  entry & security control, student experience); renovation/installation;
  compliance/risk; additional items; final recommendation
  (Strongly Recommend / Recommend with Conditions / Needs Further Review /
  Do Not Recommend).
- agent relevance: the concrete `site_opening_checklist` content; pairs with
  the scoring sheet.

### `新点审批 邮件申请模版.docx`  ★ approval workflow templates
- type: docx | readable: yes
- summary: three email templates — 场地审批申请, 虚拟课程测试结果汇报, 费用审批申请
  (with W-9 / cashier's-check handling). Encodes the virtual-course test gate.
- key rule (from BD SOP §6.9): virtual course = Google Ads 7 days + CPS 3 days
  (must test both weekday and weekend); **>5 sign-ups in one week OR 10 total →
  may open**; below that, management decides.
- agent relevance: `escalation_guidance`, `site_opening_checklist` (when can I
  open?), and the human-review handoff for payment/lease.

### `Smart Manikin ICPIS 合作分点开发与运营 SOP.docx`
- type: docx | readable: yes
- summary: `SM-ICPIS-SOP-001` V1.0 — partner/investor operating version. ICPIS
  is a "co-investing operating partner" (site hygiene, inspection, consumables,
  local promotion via 软文/Eventbrite) under ALLCPR's course/cert/brand/system
  control. Same approve-before-spend discipline; brand-consistency rules.
- agent relevance: clarifies role boundaries and what a partner may NOT promise
  (refunds, certs, pricing) → feeds `escalation_guidance`.

### `Smart Manikin Instruction.docx` + `Quick Start Guide.pptx`
- type: docx / pptx | readable: yes
- summary: device operation ("Quick Start"): place manikin on firm surface,
  unplug tablet & set on floor, prep AED pads + pocket mask (CPR/First Aid) or
  BVM (BLS), disinfect, pick module (First Aid/CPR/AED vs BLS Healthcare
  Provider), log in, perform CPR with real-time feedback ("Push Deeper", "Rate
  too fast"), and at "All Session Done / Pass" **take a photo and email it to
  support@allcpr.org** for the certificate. Student email template adds: online
  course completion required ≥1 day before; classroom-finding video; room
  passcode; after-hours main-gate access video + passcode.
- agent relevance: `smart_manikin_troubleshooting` known-good operation flow and
  the certificate/completion-photo escalation.

### `Smart Manikins学生问题.xlsx`  ★ real issue log
- type: xlsx | readable: yes
- summary: recurring student/device issues with frequency + current fix:
  - can't find room / went to wrong floor (freq 2–3) → add 2F signage;
  - chose wrong course (BLS vs CPR);
  - pressed screen instead of manikin during the bleeding/again steps;
  - accidental touch exits the course, losing progress;
  - **app self-restarts → progress lost (freq 3)**; **tablet black-screen then
    restart → progress lost**;
  - **Bluetooth won't connect when unplugged (freq 4)** → keep pad + manikin on
    a power strip / plugged in; if still not connecting while plugged in,
    restart the manikin. (Even when "connected" while unpowered, the PAD shows
    connected but TRAINING receives no data.)
  - forgot to photograph the completion screen → must be reminded.
- agent relevance: the grounded, symptom-level `smart_manikin_troubleshooting`
  knowledge. These are operational symptoms + workarounds, **not** vendor
  root-cause diagnoses.

### Other files (inventory-level)
- `Short Term Business Trip SOP.docx` + `附件1 短期出差申请表/*` — trip request,
  itinerary checklist, daily activity/evidence log, expense package, trip
  report, mileage policy. Relevant to the "实地考察" step (a specialist requests a
  short trip before site visits).
- `ICPIS Weekly Site Check Report.docx` — weekly site-check report template
  (post-launch review cadence).
- `SM Venue数据表.xlsx`, `SM 每站点每日注册量.xlsx`, `Camera.xlsx`,
  `Smart Manikins Insurance Research*` — venue master data, per-site daily
  registrations, camera inventory, insurance research. Operational data, not
  SOP rules.
- `Smart Manikin 一体化 AI 运营平台 Proposal.docx` — the vision for an
  integrated AI operations platform (this agent is an early piece of it).
- `场地漏斗/<address>/...` — per-candidate evidence packets (field-assessment
  PDFs, entrance/path/room photos, walkthrough videos). The "submission packet"
  the SOP requires.

## Reusable SOP Patterns
- **Stage table**: each stage = owner + main action + output + entry condition;
  no skipping stages.
- **Checklist style**: explicit yes/no/limited/unknown checkboxes (field form),
  five-level scoring `100/85/70/50/20` (scoring sheet).
- **Submission packet standard**: field form + scoring sheet + Drive photos/
  video + commercial terms + review conclusions, so an off-site approver can
  decide.
- **Hard-elimination gate**: a fixed list that cannot be "scored around"
  (access control, camera, network, blind spot, safety).
- **Status model**: L1 候选 → L2 已联系/Visit Scheduled → L3 已考察/BD Approved/
  管理层审核中/虚拟课程发布 → L4 管理层通过/运营中.
- **Test-before-spend gate**: virtual course + ads test with a numeric
  sign-up threshold before any lease/deposit/purchase.
- **Escalation/exception rule**: never self-approve cost/liability/contract/
  insurance/safety/operations changes.
- **Documentation style**: bilingual (Chinese SOP body + English forms),
  Drive-folder-per-address naming `ZipCode - Address - City`.

## Smart Manikin Knowledge (only what the sources support)
Known operation (from device instruction): firm surface, unplug & floor the
tablet, prep AED pads + mask/BVM, disinfect, choose the correct module, log in,
follow real-time feedback, photograph "All Session Done / Pass", email
support@allcpr.org for the certificate.

Documented recurring issues from the student-issue log, with the fix the source
records (and only that):
- Bluetooth won't connect when unplugged (freq 4) → keep manikin + pad powered
  (power strip); restart the manikin if it still won't connect; powered-but-
  unplugged the PAD may show paired but TRAINING gets no data.
- wrong floor/room (freq 2–3) → add signage (recorded fix "二楼增添指示牌") +
  classroom-finding video.
- forgot completion photo (freq 2) → remind to email `support@allcpr.org`.
- app self-restart / tablet black-screen → progress lost (freq 3): the source
  logs this but records **no fix** → escalate (`needs engineer/vendor
  confirmation`); do not improvise a reset step.
- Other logged symptoms with no recorded fix (chose wrong course BLS vs CPR;
  pressed the screen instead of the manikin; accidental touch exits the course;
  baby-choking strike location hard to find; older students struggle to follow
  the AI feedback) → treat as `needs engineer/vendor confirmation` /
  `needs official SOP source`.

These are **symptom-level operational notes**. No source file gives a vendor
hardware root-cause tree, and the source does **not** mention browser,
permissions, or Wi-Fi/cellular as device-session factors (one site records "no
Wi-Fi"; the session runs over the Bluetooth PAD↔manikin link). So the intake
checklist is limited to power / display / in-course session / Bluetooth /
tablet-PAD; unresolved or hardware-suspected issues are escalated as
`needs engineer/vendor confirmation` — the agent must not assert hardware
damage, root cause, or any undocumented reset/calibration step.

## Site-Opening / Site-Management Relevance
- The BD SOP's "先区域、后场地，先资料、后判断" maps cleanly onto the maps-scraper
  dashboard: use the modeled national ZIP layer for "先区域" (which ZIPs to even
  pursue), then the field 选址评分表 + Field Assessment Form for "后场地".
- The scoring sheet's eight dimensions (P/C/T/D/L/S/B/O) give the agent a
  shared vocabulary to explain a candidate's strengths/weaknesses.
- The hard-elimination list + test-before-spend gate define when the agent must
  stop and route to human review (lease/payment/safety).

## What Is Not Official Yet
- A single signed-off mapping from the dashboard's **modeled ZIP opportunity
  score** to the field **选址评分表 decision bands** (the two scores measure
  different things: public-data ZIP potential vs. on-site address suitability).
  → `needs official SOP source`.
- A confirmed **AHA vs ARC brand** decision rule. The data/SOP encode demand
  *tilts* (healthcare-workforce/BLS vs community/CPR), not brand preference.
- A confirmed **vendor hardware troubleshooting tree** for the Smart Manikin
  device. → `needs engineer/vendor confirmation`.
- Current authoritative **prices/policies** beyond the example figures in the
  email templates and `app/config.py` (which are explicitly labeled estimates).

## Gaps / Missing Sources (needed from Claude / Kenny / team)
- ZIP-score ↔ field-score cutoff sign-off.
- Course-type (brand) decision policy.
- Smart Manikin vendor diagnostic/escalation contacts and root-cause tree.
- Any updated price/refund/cancellation policy of record.

## Extraction Notes (reproducibility)
- `.docx` → `textutil -convert txt -stdout <file>` (macOS built-in).
- `.xlsx` / `.xlsm` → `openpyxl` (already in `requirements.txt`).
- `.pptx` → `zipfile` + regex over `ppt/slides/slideN.xml` `<a:t>` runs.
- `.pdf` → not parsed (no `pdftotext`/`mutool`); the field-assessment PDFs
  duplicate `现场考察表.docx`, which was parsed. No paid tools/APIs were used.
