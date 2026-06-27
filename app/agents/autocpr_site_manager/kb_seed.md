# KB Seed — AutoCPR Site Management Specialist

Seed knowledge base for the agent's retriever. Grounded in `SOP/Smart Manikin*`
and the maps-scraper-intel data engine. Pairs with `sop.md` and
`sop_source_analysis.md`. Future production KB should import Kenny's official
`AutoCPR 开点 SOP（专员版）` (which is the same `SM-BD-SOP-001` family) plus any
updated thresholds.

## Purpose — 管点 / site operations first
Primary: help on-site staff handle real, class-day site-management incidents —
停电 / 断网 / 门禁·教室 / Smart Manikin / 课程无法开始 / 老师未到 / 签到名单 /
完课·证书 / 安全紧急 / 事件记录 / 升级 — safely and consistently, backed by SOP
sources or clearly-labeled general operations guidance, never by invented numbers
or policies. Secondary: site-opening (开点/选址) and the Site Intelligence
Dashboard are supporting references.

## Issue intake workflow
1. Safety first — confirm no fire/smoke/shock/injury/hazard; if any → safety SOP +
   911. 2. Identify the issue type. 3. Follow the matching SOP section. 4. Collect
info (site/room, class time, issue time, headcount, what happened, what was
tried). 5. Request evidence (see below). 6. Communicate honestly without promising
reschedule/refund. 7. Escalate decisions to a supervisor. Company decisions
(reschedule/refund/pricing/policy) are always `needs official SOP source`.

## Photo / evidence collection workflow
Ask for photos/screenshots/video **only when safe**: "如果安全且不影响处理，请上传/
保存照片或截图作为证据。" Never ask anyone to take an unsafe photo; in a safety/
emergency, people come before photos — collect evidence only after everyone is
safe. The agent records attachment *descriptions* only and does not analyze image
content: "已收到附件描述；如果需要视觉确认，请人工查看照片。"

## Before-class site readiness checklist (general ops)
Power on; network confirmed (a Smart Manikin session runs over Bluetooth
PAD↔manikin — one site records "无 Wi-Fi"); door/gate access + passcode/lockbox per
site materials; correct floor/room; training device powered + paired; check-in/
roster ready; signage in place. → `general operations guidance, not official SOP`.

## Incident handling summaries (general ops triage, not official SOP)
- **电 / electricity outage:** safety check → scope (room/building/area) → ask
  venue/property to reset (don't touch the breaker yourself) → record start time +
  affected classes → assess if class can continue (devices need power) → escalate
  reschedule/refund decision.
- **网 / internet outage:** scope → basic checks (only power-cycle the site's own
  router, if authorized) → general internet vs platform vs device pairing → record
  + screenshot → venue (site network) or supervisor/tech (platform). Training runs
  over Bluetooth, not Wi-Fi.
- **门禁 / venue access:** verify address/floor/room → room/gate passcode + lockbox +
  instruction video (site materials) → contact venue to open → log arrival time +
  attempts → **never force entry.**
- **课程无法开始 / class cannot start:** find the root cause → handle via its section →
  record impact → escalate reschedule/refund.
- **老师未到 / instructor no-show:** contact + log attempts → supervisor decides
  substitute/reschedule/refund → reassure students.
- **签到 / roster:** verify student vs registration → log mismatch → escalate
  anomalies (don't self-admit/back-fill).
- **完课·证书 / completion-certificate:** "All Session Done/Pass" screen → photo →
  email `support@allcpr.org` (source-supported); issuance/scoring rules =
  `needs official SOP source`.
- **安全 / safety-emergency:** 911 + evacuate if needed → people before photos →
  record after safe → escalate immediately.

## Incident report template (general ops)
Site / room / class time / event time / recorder · event type + what happened
(what·when·who) · impact (classes/students/devices, interrupted?) · actions taken +
result · evidence list (photos/screenshots/comms) · escalation target + items
awaiting supervisor/official decision. Separate facts from to-be-confirmed. An
official company template (if any) = `needs official SOP source`.

## Escalation logic
Specialist may NOT self-approve anything affecting cost/liability/contract/
insurance/safety/operations (SM-BD-SOP-001 §6.9/§10). Route: supervisor (customer/
policy/class), engineer/vendor (device root cause → `needs engineer/vendor
confirmation`), venue/property (venue/access/power), 911 (emergency). Refund/
reschedule/compensation/price/policy → `needs official SOP source`.

## Post-incident optimization
Log incidents; periodically review recurring issues + site outcomes → optimize /
hold / scale / exit; feed corrections back into the SOP/KB; add tests from real
incidents; audit the KB for unsupported claims (especially Smart Manikin).

## KB metadata plan (for the future vector DB)
Each KB chunk should eventually carry:
```json
{
  "doc_type": "site_operations_sop",
  "issue_type": "electricity_outage",
  "severity": "high",
  "source_status": "official_sop | extracted_sop_reference | smart_manikin_source | general_operations_guidance | needs_source",
  "source_file": "SOP/...",
  "owner": "ops | site manager | vendor | venue",
  "last_updated": "source date if known"
}
```

## AutoCPR Site Intelligence — purpose (supporting reference)
Help a site-management specialist decide **where** to open AutoCPR / Smart
Manikin sites, **how** to run the opening workflow, and **how** to read the Site
Intelligence Dashboard — backed by SOP and public-data evidence, never by
invented numbers.

## Role of maps-scraper-intel
`maps-scraper-intel` is the supporting **data engine** for ZIP/city/site
evaluation. It serves a read-only dashboard over pre-generated JSON: a modeled
national ZIP-opportunity layer (public-data estimate for every US ZIP) and a
historical ALLCPR layer (real Enrollware evidence). It does not call paid Places
APIs on load and does not run the scoring pipeline at request time.

## Site-management specialist workflow (summary)
先区域、后场地，先资料、后判断: screen ZIPs (A/B/C) → confirm potential ZIPs → list
L1 candidate addresses → confirm visit list → on-site Field Assessment Form +
photos/video → update `选址评分表` within 24h → BD review → management approval →
virtual-course/site test → procurement/buildout → opening acceptance + system
test → launch → weekly review. Full detail in `sop.md`.

## Old SOP reference patterns (from SOP/Smart Manikin*)
- Stage table: owner + action + output + entry condition; no skipping stages.
- Submission packet: Field Assessment Form + `选址评分表` + Drive photos/video +
  commercial terms + review conclusions, so an off-site approver can decide.
- Five-level input scoring 100 / 85 / 70 / 50 / 20.
- Status model: L1 候选 → L2 已联系 / Visit Scheduled → L3 已考察 / BD Approved /
  管理层审核中 / 虚拟课程发布 → L4 管理层通过 / 运营中.
- Test-before-spend gate before any lease/deposit/purchase.

## 11 Google Places enrichment categories (dashboard)
1. Hospital
2. Urgent Care
3. Clinic
4. Doctor Office
5. Nursing Facility
6. CPR Training Center
7. EMT School
8. Medical Assistant School
9. First Aid Certification
10. BLS / CPR Competitors
11. Related Training Providers

## Site-selection scoring model (选址评分表 — official, citable)
`Final = 0.12·P + 0.10·C + 0.08·T + 0.10·D + 0.15·L + 0.18·S + 0.12·B + 0.15·O`
- **P** Population Potential = `0.5·P1 + 0.3·P2 + 0.2·P3`
- **C** Competition = `0.5·C1 + 0.3·C2 + 0.2·C3`
- **T** Traffic Accessibility = `0.4·T1 + 0.35·T2 + 0.25·T3`
- **D** Demand Match = `0.35·D1 + 0.25·D2 + 0.25·D3 + 0.15·D4`
- **L** Layout = `0.3·L1 + 0.4·L2 + 0.15·L3 + 0.15·L4`
- **S** Security = `0.25·S1 + 0.25·S2 + 0.15·S3 + 0.20·S4 + 0.15·S5`
- **B** Business = `0.4·B1 + 0.2·B2 + 0.2·B3 + 0.2·B4`
- **O** Operational Fit = `0.2·(O1+O2+O3+O4+O5)`
Decision bands: **≥85 Priority Candidate; 75–84.9 Management Review;
65–74.9 Hold / Compare; <65 Reject.** Hard elimination: access control not
installable; camera not installable; network not adequate; unfixable blind spot;
high safety risk.

## Interpreting healthcare density
High hospital/urgent-care/clinic/nursing-facility density plus EMT/medical-
assistant/nursing schools indicates sustained **BLS-leaning** demand and
referral potential. Use the dashboard enrichment categories; if a ZIP is not
enriched, the value is `data not provided` — request manual validation rather
than guessing.

## Interpreting school / training demand
Nursing schools, EMT schools, medical-assistant schools, community colleges, and
universities feed both BLS (healthcare pipeline) and CPR/First Aid (general
student) demand. Childcare/daycare and schools push **CPR / First Aid** demand.

## Interpreting competitor density
Two valid readings — state both, don't assume one:
- **Market validation**: providers exist because demand is real.
- **Competition risk**: saturation can suppress a new site's fill rate.
Cross-check the modeled `competition_gap_score` (high = little competition) and
the `选址评分表` dimension **C**. Many nearby BLS/CPR competitors with strong
underlying demand can still be a good market; few competitors with weak demand
is not automatically good.

## Interpreting missing data
Missing enrichment or a missing dashboard metric is **not** a negative signal —
it means the ZIP hasn't been enriched/validated yet. Response: say `data not
provided`, recommend requesting manual validation/enrichment for that ZIP, and
avoid issuing a verdict on absent data.

## Course Fit Logic
- **AHA BLS** weighs **healthcare density** most (hospitals, clinics, nursing
  facilities, healthcare employment share).
- **ARC BLS** weighs **healthcare + workplace** demand.
- **Red Cross CPR / First Aid** weighs **population, schools, workplace,
  childcare, and general-public** demand.
- Competitor density can mean **both** market validation and competition risk.
Brand (AHA vs ARC) is **not** modeled from public data — any brand decision rule
is `needs official SOP source`. The dashboard models two demand *tilts*
(healthcare-workforce/BLS vs community/CPR), not brand.

## Smart Manikin issue intake & escalation (supporting operations knowledge only)
Scope note: this is supporting site-operations troubleshooting knowledge, not the
agent's main purpose, and it is limited to what the source files document.

Known-good device flow (from `Smart Manikin Instruction.docx` / Quick Start
Guide): firm surface; unplug & floor the tablet; prep AED pads + pocket mask
(CPR/First Aid) or BVM (BLS); disinfect; choose the correct module (First
Aid/CPR/AED vs BLS Healthcare Provider); log in; follow real-time feedback
("Push Deeper", "Rate too fast"); at "All Session Done / Pass" photograph the
screen and email `support@allcpr.org` for the certificate.

Documented issues + the recorded fix (from `Smart Manikins学生问题`; only these
are SOP-supported):
- Bluetooth won't connect when unplugged (freq 4) → keep manikin + pad powered
  (power strip); restart the manikin if still not connecting; while
  powered-but-unplugged the PAD may show paired but TRAINING gets no data.
- Wrong floor/room (freq 2–3) → classroom-finding video + room/gate passcode +
  add signage (recorded fix "二楼增添指示牌").
- Forgot completion photo (freq 2) → remind to email the "All Session Done/Pass"
  screen to `support@allcpr.org`.
- App self-restart / tablet black-screen → progress lost (freq 3): logged
  recurring with **no fix recorded** in the source → `needs engineer/vendor
  confirmation` (do not improvise a reset step).
Intake checklist (source-grounded only): power (plugged into the power strip),
display (black screen / app restart), in-course session state (accidental exit
loses progress), Bluetooth (PAD↔manikin) pairing, tablet/PAD status. Do **not**
assert hardware damage, device root cause, calibration, or any reset step the
source does not state; unknown root cause → vendor/engineer.

## Site Intelligence questions the agent should handle
- 这个 ZIP 是否适合开点？ (Use the modeled ZIP layer + enrichment; if not enriched,
  `data not provided` + request validation.)
- 这个城市适合 AHA BLS 还是 Red Cross CPR？ (Answer by demand tilt; brand rule =
  `needs official SOP source`.)
- 为什么这个 ZIP 是 high potential？ (Explain via the enrichment categories /
  modeled score drivers shown in the ZIP detail panel.)
- 竞争对手密度怎么看？ (Market-validation vs competition-risk; cross-check
  `competition_gap_score`.)
- enrichment 数据缺失怎么办？ (`data not provided`; request manual validation.)
- Smart Manikin 黑屏/加载失败怎么处理？ (Run the source-grounded intake above; the
  black-screen / load-failure issue has **no recorded fix** in the source →
  escalate, `needs engineer/vendor confirmation`. Do not improvise a reset step.)

## Test-before-open gate (SM-BD-SOP-001 §6.9)
Virtual course = Google Ads 7 days + CPS 3 days (must test weekday AND weekend);
**>5 sign-ups in one week OR 10 total → may open**; below that, management
decides. No lease/deposit/purchase before management's written test-pass
confirmation.

## Future production KB
Import Kenny's official `AutoCPR 开点 SOP（专员版）` and any updated thresholds;
add a signed-off mapping from the dashboard modeled ZIP score to the field
`选址评分表` bands; add the vendor hardware troubleshooting tree; replace the
keyword retriever with a vector DB and layer a Claude LLM on top for generation.
