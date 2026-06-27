# AutoCPR 管点 / 现场运营 SOP（专员版）— Site Operations Workflow

Working SOP for the AutoCPR Site **Operations** Specialist agent. The primary job
is handling on-site, class-day incidents (停电 / 断网 / 门禁 / 设备 / 课程无法开始 /
老师未到 / 签到 / 完课·证书 / 安全 / 事件记录 / 升级). Site-opening (开点/选址) and
the Site Intelligence Dashboard are **supporting references** (Appendix §15).

Source-status convention used in every section:
- `source-supported SOP` — taken from an in-repo SOP file (citable).
- `Smart Manikin source-supported` — taken from the Smart Manikin files.
- `general operations guidance, not official SOP` — common-sense incident triage;
  **not** an official ALLCPR rule. Final company decisions (reschedule/refund/
  pricing/policy) are `needs official SOP source`.
- `needs official SOP source` / `data not provided` /
  `needs engineer/vendor confirmation` — used verbatim where something is undefined.

Global rules:
- **Safety first, always.** People before photos. Never ask anyone to take an
  unsafe photo: "如果安全且不影响处理，请上传/保存照片或截图作为证据。"
- The specialist may **not** self-approve anything affecting cost, liability,
  contract, insurance, safety, or operations (SM-BD-SOP-001 §6.9/§10) — escalate.
- Do not invent ALLCPR policies, prices, refund rules, thresholds, contacts,
  vendor instructions, device diagnoses, or SOP rules.

---

## 1. Site Operations Overview / 管点总览
- **Issue type:** any on-site/class-day operational event.
- **Severity:** varies (info → critical).
- **Immediate safety check:** confirm no fire/smoke/shock/injury/hazard; if any →
  go to §11 Safety/Emergency first.
- **Step-by-step:** (1) ensure safety → (2) identify the issue type → (3) follow
  the matching section below → (4) collect info + evidence → (5) communicate
  carefully → (6) escalate decisions to a supervisor.
- **Information to collect:** site/room, class time, issue time, people on site,
  what happened, what was tried.
- **Evidence:** scene photos/screenshots when safe.
- **Contacts/escalate:** supervisor; venue/property; engineer/vendor; 911 for
  emergencies.
- **Customer communication:** be honest that it's being handled; never promise a
  reschedule/refund/compensation amount.
- **Next action:** route to the specific SOP section.
- **Human review:** required whenever a company decision, safety, or unconfirmed
  data is involved.
- **Source status:** `general operations guidance, not official SOP`;
  final policy = `needs official SOP source`.

## 2. Before-Class Site Readiness Checklist / 课前站点检查
- **Issue type:** preventive pre-class check.
- **Severity:** low.
- **Immediate safety check:** room safe and clear, exits accessible.
- **Step-by-step:** confirm power; confirm network (note: a Smart Manikin session
  runs over the Bluetooth PAD↔manikin link — one site records "无 Wi-Fi"); confirm
  door/gate access + passcode/lockbox per site instructions; confirm the room is
  the correct floor/room; power on and pair the training device; confirm the
  check-in/roster is ready; confirm signage is in place.
- **Information to collect:** anything not ready → log + fix or escalate early.
- **Evidence:** photo of a ready room / device paired, if useful.
- **Contacts/escalate:** venue/property for access or facilities; supervisor for
  staffing/roster gaps.
- **Customer communication:** n/a pre-class.
- **Next action:** resolve any gap before students arrive.
- **Human review:** required if a readiness gap can't be fixed before class.
- **Source status:** `general operations guidance, not official SOP`; device steps
  are `Smart Manikin source-supported`.

## 3. Electricity Outage SOP / 停电处理
- **Issue type:** 停电 / power outage. **Severity:** high.
- **Immediate safety check:** injuries? smoke/burning smell? shock risk? If yes →
  §11 + call 911. Move carefully in the dark.
- **Step-by-step:** confirm scope (room / building / area); if only this room
  tripped, ask venue/property to reset — **do not operate the breaker yourself**;
  record outage start time + affected classes; notify the venue/property contact
  for cause + ETA; assess whether class can continue (devices need power; the
  Smart Manikin tablet needs power); if not, wait for the supervisor's decision.
- **Information to collect:** scope, start time, ETA, affected class/time/headcount,
  venue contact + comms log.
- **Evidence:** (if safe) dark-room photo/video; (only if safe & allowed) breaker
  area photo — don't operate it; venue comms screenshot; affected class/time.
- **Contacts/escalate:** venue/property (cause/restore); supervisor (continue?
  reschedule/refund); safety → 911 + supervisor.
- **Customer communication:** tell students it's being handled; don't promise a
  specific reschedule/refund.
- **Next action:** collect info/evidence, notify venue + supervisor; if class can't
  continue → `human review required`.
- **Human review:** required for any reschedule/refund/compensation decision.
- **Source status:** `general operations guidance, not official SOP`;
  reschedule/refund policy = `needs official SOP source`.

## 4. Internet / Wi-Fi Outage SOP / 网络故障处理
- **Issue type:** 断网 / Wi-Fi/internet outage. **Severity:** high.
- **Immediate safety check:** usually none; if combined with a power/safety issue,
  handle safety first.
- **Step-by-step:** confirm scope (one device / room / building); basic checks if
  safe & authorized (power-cycle the site's own router only); determine whether
  it's general internet vs platform loading vs device pairing; record start time +
  affected class; venue network → venue/property; platform/system → supervisor/tech.
  Note: the Smart Manikin training session itself runs over Bluetooth PAD↔manikin,
  not Wi-Fi.
- **Information to collect:** scope, start time, affected class/headcount, exact
  error message.
- **Evidence:** Wi-Fi/network error screenshot; platform/session loading error
  screenshot; device/tablet status photo if relevant.
- **Contacts/escalate:** venue/property (site network); supervisor/tech (platform).
- **Customer communication:** being investigated; no reschedule/refund promise.
- **Next action:** scope + basic checks + screenshots; if class blocked →
  `human review required`.
- **Human review:** required for reschedule/refund.
- **Source status:** `general operations guidance, not official SOP`; policy =
  `needs official SOP source`.

## 5. Venue Access / Door / Room Issue SOP / 门禁与教室问题
- **Issue type:** 门打不开 / 进不去 / access. **Severity:** high.
- **Immediate safety check:** if locked outside with weather/safety risk, get to a
  safe spot; **never force a door or climb in** (injury + legal risk).
- **Step-by-step:** verify the class address/floor/room is correct; check for a
  room passcode / gate passcode / lockbox and the instruction video (per the
  site's own materials); after-hours main-gate access per the site's provided
  video + passcode (only what the site files support); contact venue/property to
  open or confirm entry; record arrival time + entry attempts.
- **Information to collect:** address/floor/room, arrival time, attempts made,
  students waiting.
- **Evidence:** (if safe) photo of the locked door/signage; address/room
  assignment screenshot; arrival timestamp; venue-contact attempt log.
- **Contacts/escalate:** venue/property (open/confirm); supervisor (prolonged
  lockout / reschedule).
- **Customer communication:** contacting for entry; no reschedule/refund promise.
- **Next action:** verify room + passcodes/video, contact venue, log attempts; if
  still no entry → `human review required`.
- **Human review:** required; access rights/key ownership if unclear →
  `needs official SOP source`.
- **Source status:** `general operations guidance, not official SOP`; site
  passcode/video handling is `Smart Manikin source-supported` (student-instruction
  files).

## 6. Smart Manikin / Training Equipment Issue SOP / 设备故障处理
**Strictly limited to what the Smart Manikin source files document — not hardware
diagnosis.** Supporting site-ops knowledge only.
- **Issue type:** Smart Manikin / training device. **Severity:** medium.
- **Immediate safety check:** usually none; power smell/heat/shock risk → §11.
- **Symptom intake (source-grounded only):** power (manikin + tablet plugged into
  the power strip), display (black screen / app self-restart), in-course session
  state (an accidental touch can exit the course and lose progress), Bluetooth
  pairing between the PAD and manikin, tablet/PAD status. (The session runs over
  Bluetooth; one site records "无 Wi-Fi" — do **not** treat Wi-Fi/browser/
  permissions as device-session factors; they are not in the source files.)
- **Documented issues + the recorded fix (only these are supported):**
  - **Bluetooth won't connect when unplugged** (freq 4): keep manikin + pad
    powered (power strip); if it still won't connect while plugged in, **restart
    the manikin** (recorded fix). Note: while powered-but-unplugged the PAD may
    show *connected* but TRAINING gets no data.
  - **Wrong floor/room** (freq 2–3): classroom-finding video + room/gate passcode +
    add signage (recorded fix "二楼增添指示牌").
  - **Forgot completion photo** (freq 2): photograph the "All Session Done/Pass"
    screen and email it to `support@allcpr.org` for the certificate.
  - **App self-restart / tablet black-screen → progress lost** (freq 3): the source
    logs this but records **no fix** — do **not** improvise a reset/recovery step →
    `needs engineer/vendor confirmation`.
- **Information to collect:** exact symptom + timing (which course step); power/
  display/Bluetooth/tablet-PAD status; exact error text; class/session context.
- **Evidence:** device status photo/video; tablet/PAD screen photo/screenshot;
  power/connection-state photo; exact error message.
- **Contacts/escalate:** engineer/vendor for anything outside the documented items
  (`needs engineer/vendor confirmation`); supervisor when class is affected.
- **Customer communication:** being checked; never claim hardware damage or give an
  undocumented diagnosis.
- **Next action:** collect symptom + run the documented checks; if a documented fix
  doesn't resolve it, or the issue isn't covered → escalate to engineer/vendor.
- **Human review:** required.
- **Source status:** `Smart Manikin source-supported`; unknown root cause =
  `needs engineer/vendor confirmation`; certificate/completion rules beyond the
  source = `needs official SOP source`.

## 7. Class Cannot Start SOP / 课程无法开始处理
- **Issue type:** 课程无法开始. **Severity:** high.
- **Immediate safety check:** confirm no people/device/venue safety risk.
- **Step-by-step:** locate the root cause (power / network / access / device /
  instructor / roster / other) → handle via the matching section; record affected
  start time + headcount + wait; reassure students with confirmed info only;
  if not quickly solvable → escalate to a supervisor for reschedule/refund.
- **Information to collect:** root-cause class, class time/place/headcount, what was
  tried.
- **Evidence:** root-cause-specific photos/screenshots; students-arrived/time log.
- **Contacts/escalate:** supervisor (reschedule/refund); venue/tech/vendor by cause.
- **Customer communication:** handling in progress; no reschedule/refund promise.
- **Next action:** fix the root cause; if not timely → `human review required`.
- **Human review:** required.
- **Source status:** `general operations guidance, not official SOP`; policy =
  `needs official SOP source`.

## 8. Instructor No-Show / Late SOP / 老师未到或迟到处理
- **Issue type:** 老师没到/迟到. **Severity:** high.
- **Immediate safety check:** students safe and orderly.
- **Step-by-step:** immediately try to contact the instructor (call/message) and
  log each attempt + time; check whether a substitute can be arranged (supervisor/
  scheduling decides — specialist does not promise); record class time/place +
  headcount; escalate to supervisor for substitute/reschedule/refund decision;
  reassure students with confirmed info.
- **Information to collect:** scheduled class time/place, contact-attempt log,
  instructor name (if any), affected headcount.
- **Evidence:** class schedule info; contact-attempt log (call/message
  screenshots); students-arrived count.
- **Contacts/escalate:** the instructor; supervisor/scheduling (substitute/
  reschedule/refund).
- **Customer communication:** contacting the instructor; no substitute-time or
  refund promise.
- **Next action:** contact + log; escalate → `human review required`.
- **Human review:** required; the no-show handling policy = `needs official SOP source`.
- **Source status:** `general operations guidance, not official SOP`.

## 9. Student Check-in / Roster Issue SOP / 学员签到名单问题
- **Issue type:** 签到/名单. **Severity:** medium.
- **Immediate safety check:** none unless combined with another event.
- **Step-by-step:** verify the student vs the roster/registration (Enrollware
  etc.); confirm they're not at the wrong class/time/place; record mismatches
  (not on roster, name mismatch, duplicate, unpaid flag); not-on-roster or
  registration anomalies → escalate, don't self-decide admit/back-fill.
- **Information to collect:** student name/class/time; the matching or missing
  roster record.
- **Evidence:** check-in/roster screenshot; registration confirmation; error text.
- **Contacts/escalate:** supervisor / registration back-office.
- **Customer communication:** verifying; no admit/back-fill promise.
- **Next action:** verify + log mismatch; anomaly → escalate.
- **Human review:** required; refund/back-fill/payment → `needs official SOP source`.
- **Source status:** `general operations guidance, not official SOP`.

## 10. Completion / Certificate Evidence Issue SOP / 完课与证书证据问题
- **Issue type:** 完课/证书证据. **Severity:** medium.
- **Immediate safety check:** none.
- **Step-by-step:** confirm the student reached the "All Session Done/Pass" screen
  (the source-recorded completion marker); remind/help them photograph it and email
  `support@allcpr.org` (source-supported); record name/class/session + the specific
  problem (no photo, not scored, no cert); certificate-not-issued / scoring rules →
  escalate, `needs official SOP source`.
- **Information to collect:** student name/class/session; completion status + the
  specific anomaly.
- **Evidence:** completion-status screenshot/photo ("All Session Done/Pass");
  student/class/session info; the source-required completion photo if applicable;
  error text.
- **Contacts/escalate:** `support@allcpr.org` (completion photo); supervisor
  (issuance/scoring).
- **Customer communication:** may cite the source-supported completion-photo flow;
  do not invent certificate timelines/rules → `needs official SOP source`.
- **Next action:** confirm the completion screen + email; issuance/scoring → escalate.
- **Human review:** required.
- **Source status:** completion-photo flow is `Smart Manikin source-supported`;
  issuance/scoring rules = `needs official SOP source`.

## 11. Safety / Emergency Issue SOP / 安全与紧急事件
- **Issue type:** 安全/紧急. **Severity:** critical.
- **Immediate safety check (do this first):** life safety first — injury/fire/
  smoke/shock/gas → call **911** and evacuate as needed; move people to safety;
  **do not return** to a dangerous area for belongings or photos; **do not
  prioritize photos over people's safety.**
- **Step-by-step:** ensure everyone is safe (evacuate + 911 if needed) → after
  people are safe, record time/place/people/what happened → only then, if safe,
  take scene photos/video → escalate to supervisor immediately and follow
  supervisor/official guidance.
- **Information to collect:** event time/place; affected/injured people; emergency
  actions taken (911/evacuate/first aid).
- **Evidence:** **only after people are safe** — photos/video; event time/place;
  affected people. ("如果安全且不影响处理…")
- **Contacts/escalate:** 911 (emergency); supervisor (immediately); venue/property
  if venue safety.
- **Customer communication:** prioritize safety + calm guidance; do not publish an
  unconfirmed cause or liability conclusion.
- **Next action:** ensure safety → record/evidence after safe → escalate
  (`human review required`).
- **Human review:** required; incident handling/notification/insurance =
  `needs official SOP source`.
- **Source status:** `general operations guidance, not official SOP`.

## 12. Incident Report SOP / 现场事件记录
- **Issue type:** 现场事件记录. **Severity:** medium.
- **Immediate safety check:** if the event is ongoing and unsafe → §11 first.
- **Step-by-step (template):** basics (site, room, class time, event time,
  recorder) → event type + what happened (what/when/who) → impact (classes/
  students/devices, was class interrupted) → actions taken + result → evidence list
  (photos/screenshots/comms) → escalation target + items awaiting supervisor/
  official decision (reschedule/refund/compensation).
- **Information to collect:** all of the above.
- **Evidence:** list of related photos/screenshots/video; comms log (venue/
  instructor/supervisor).
- **Contacts/escalate:** supervisor (submit report + decisions).
- **Customer communication:** separate "facts" from "to-be-confirmed/decided"; no
  unconfirmed conclusions or promises in the record.
- **Next action:** fill the structure + attach evidence list; submit to supervisor.
- **Human review:** required; an official company report template (if any) =
  `needs official SOP source`.
- **Source status:** `general operations guidance, not official SOP`.

## 13. Escalation SOP / 升级处理
- **Issue type:** 升级/上报. **Severity:** high.
- **Immediate safety check:** if a safety risk is involved → handle safety first.
- **Step-by-step:** classify the escalation — customer/policy (refund/reschedule/
  complaint), device/engineering (vendor/engineer), venue (venue/property), safety
  (911 + supervisor); package the context (time/place/impact/attempts/evidence);
  escalate to the right owner and wait for the decision.
- **Information to collect:** context + what decision is needed.
- **Evidence:** supporting screenshots/photos/records.
- **Contacts/escalate:** supervisor (customer/policy/class); engineer/vendor
  (device root cause, `needs engineer/vendor confirmation`); venue/property (venue/
  access/power).
- **Customer communication:** escalating; no solution promise before the decision.
- **Next action:** package context + escalate.
- **Human review:** required; refund/reschedule/compensation/contract/insurance/
  price/policy → `needs official SOP source`.
- **Source status:** `general operations guidance, not official SOP`; the
  no-self-approval rule is `source-supported SOP` (SM-BD-SOP-001 §6.9/§10).

## 14. Post-Incident Review and Optimization / 事后复盘优化
- Log each incident; run a periodic review of recurring issues (signage,
  instructions, device workarounds, the KB) and site outcomes (sign-ups,
  attendance, completions, no-show/refund rates, technical incidents) → decide
  optimize / hold / scale / exit.
- Feed confirmed corrections back into this SOP and the KB; add tests from real
  incidents; periodically audit the KB for unsupported claims (especially Smart
  Manikin).
- **Source status:** review cadence is `extracted SOP reference` (Expansion SOP
  §7.9 / ICPIS Weekly Site Check); the improvement loop itself is
  `general operations guidance, not official SOP`.

## 15. Site Opening Reference Appendix / 开点参考附录 (secondary)
Site-opening is a **supporting reference**, not the agent's primary job. Region
first, then site ("先区域、后场地"): use the maps-scraper-intel dashboard's modeled
national ZIP layer to choose ZIPs to pursue, then run the on-site Field Assessment
Form (现场考察表) + the **official `选址评分表`** scoring model:

`Final = 0.12·P + 0.10·C + 0.08·T + 0.10·D + 0.15·L + 0.18·S + 0.12·B + 0.15·O`
- Each input is scored 100 / 85 / 70 / 50 / 20.
- Decision bands: **≥85 Priority Candidate; 75–84.9 Management Review; 65–74.9
  Hold/Compare; <65 Reject.**
- Hard-elimination (cannot be scored around): access control not installable;
  cameras not installable / can't cover entrance + equipment; network not adequate;
  unfixable surveillance blind spot; high surrounding safety risk.

Course-fit is a **demand tilt, not a brand**: AHA BLS weighs healthcare-workforce
density most; ARC BLS weighs healthcare + workplace; Red Cross CPR/First Aid weighs
population, schools, workplace, childcare, general public. The AHA-vs-ARC brand
rule itself is `needs official SOP source`. The modeled ZIP opportunity score is a
public-data estimate and is **not** the field `选址评分表` score; a signed-off
mapping between them is `needs official SOP source`. Test-before-spend gate
(SM-BD-SOP-001 §6.9): Google Ads 7d + CPS 3d (weekday + weekend); >5 sign-ups in a
week OR 10 total → may open; else management decides.
- **Source status:** `source-supported SOP` / `official SOP source` (scoring sheet
  + BD SOP); ZIP-score↔field-score mapping = `needs official SOP source`.
