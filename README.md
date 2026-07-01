# AllCPR AI Agent

**Release:** `v0.8b1`

Standalone internal **AllCPR Site Operations Agent** for 管点 / site-operations
support. The app helps staff handle on-site incidents such as power outages,
internet issues, locked doors, Smart Manikin problems, instructor no-shows,
check-in/completion issues, safety events, and incident-report drafting.

The project is intentionally separate from `maps-scraper-intel`: opening
`/` serves the agent, not the map dashboard.

## What This Agent Does

- Classifies site-operations incidents with deterministic bilingual keyword
  rules.
- Retrieves supporting local SOP/KB snippets from markdown files.
- Returns a structured answer with safety checks, handling steps, evidence to
  collect, escalation guidance, customer/student communication, source status,
  and human-review flags.
- Shows relevant local SOP source images under the answer when deterministic
  metadata matching finds a safe scenario match.
- Supports English and Chinese responses.
- Uses local source material only. There is no LLM call, no paid API, and no
  secret handling.

## What This Agent Does Not Do

- It does not decide refunds, reschedules, cancellations, compensation, official
  certificate policy, final class-continuation decisions, vendor diagnosis, or
  official customer notices.
- It does not invent SOP rules, Smart Manikin fixes, prices, contacts, or
  vendor instructions.
- It does not analyze image content. Attachment descriptions are accepted as
  metadata only; visual confirmation must be reviewed by a human.

## Current Product Surface

| Surface | Path |
| --- | --- |
| Agent UI | `/` |
| Agent UI alias | `/agent` |
| Structured API | `POST /api/agents/autocpr-site-manager/ask` |
| Staff passcode unlock | `POST /api/staff-access/unlock` |
| Incident logs | `GET/POST /api/incident-logs`, `GET/PATCH /api/incident-logs/{id}` |
| Inspection logs | `GET/POST /api/inspection-logs`, `GET/PATCH /api/inspection-logs/{id}` |
| Inspection reference image | `GET /api/inspection-reference` |
| Health check | `/health` |

## Assistant UI

The `/` and `/agent` pages use a simplified, first-time-staff layout so the
default screen answers "what am I doing right now?":

1. Type a site-operations question, or pick one of the six **Common Incidents**
   (door locked, power outage, internet down, Smart Manikin issue,
   student/check-in issue, incident report).
2. Pick English or Chinese.
3. Use the **Site Tools** row to *Start Inspection* or take the *Onboarding
   Test*.
4. Read one concise answer card: scenario, severity, and the top 3 next steps
   first. Evidence, escalation, "do not", full SOP, and source references are
   collapsed behind tabs and expand on click (one at a time).
5. Optionally expand **Advanced details** for site, class time, or attachment
   description metadata.

Staff-only tooling — staff access unlock, the live site log, and the
staff-gated **Manager Review** panel — lives in the **Activity** drawer
(closed by default; opens from the header, lazy-loads on open). Manager Review
stays locked until staff access is unlocked.

The UI does not claim to analyze uploaded or SOP images. SOP image labels come
from source filenames, folders, and document names only.

## Local Quick Start

```bash
cd ~/Desktop/Developer/allcpr_agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn web_app:app --host 127.0.0.1 --port 8012
```

Then open:

- `http://127.0.0.1:8012/`
- `http://127.0.0.1:8012/agent`

If you are using the local framework Python already installed on this machine:

```bash
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 -m uvicorn web_app:app --host 127.0.0.1 --port 8012
```

## Example API Calls

English:

```bash
curl -s http://127.0.0.1:8012/api/agents/autocpr-site-manager/ask \
  -H 'content-type: application/json' \
  -d '{
    "question": "What should I do if the power goes out?",
    "context": { "lang": "en", "site": "Santa Clara", "class_time": "09:00" }
  }'
```

Chinese:

```bash
curl -s http://127.0.0.1:8012/api/agents/autocpr-site-manager/ask \
  -H 'content-type: application/json' \
  -d '{
    "question": "停电了怎么办？",
    "context": { "lang": "zh", "site": "Santa Clara", "class_time": "09:00" }
  }'
```

With attachment metadata:

```bash
curl -s http://127.0.0.1:8012/api/agents/autocpr-site-manager/ask \
  -H 'content-type: application/json' \
  -d '{
    "question": "The classroom power is out.",
    "context": {
      "lang": "en",
      "attachments": [
        { "type": "photo", "description": "dark classroom photo", "filename": "outage.jpg" }
      ]
    }
  }'
```

## Language Selection

The agent chooses a response language deterministically:

1. `context.lang`, `context.language`, or `context.locale` wins when provided.
2. Supported English hints: `en`, `english`, `en-US`.
3. Supported Chinese hints: `zh`, `zh-CN`, `chinese`, `中文`.
4. If no context language is supplied, the question is scanned for meaningful CJK
   characters.
5. CJK detected → Chinese response. Otherwise → English response.

Mixed-language questions follow the explicit context language when provided.

## API Response Shape

The endpoint returns `AgentAnswer`:

```json
{
  "answer": "Human-readable structured answer",
  "scenario": "electricity_outage",
  "confidence": "medium",
  "sources": ["sop.md", "kb_seed.md"],
  "needs_human_review": true,
  "next_actions": [],
  "language": "en",
  "issue_type": "Electricity outage",
  "severity": "high",
  "immediate_safety_check": [],
  "steps": [],
  "information_to_collect": [],
  "evidence_requested": [],
  "contacts": [],
  "customer_communication": [],
  "do_not_decide_without_approval": [],
  "source_status": [],
  "attachments_note": "",
  "issue_subtype": "",
  "route_detail": "",
  "policy_approval_required": false
}
```

`issue_subtype` carries the focused sub-issue a narrow query routed to (for
example `passcode_needed`, `code_failed`, `wrong_course`, `certificate_issue`,
`fix_failed`), `route_detail` is its short route category (`access`, `checkin`,
`completion`, `outage`), and `policy_approval_required` flags sub-issues that
need supervisor/registration approval. Smart Manikin keeps its own
`smart_manikin_subissue` field.

## Supported Scenarios

- `electricity_outage`
- `internet_outage`
- `venue_access_issue`
- `smart_manikin_troubleshooting`
- `smart_manikin_site_inspection`
- `class_cannot_start`
- `instructor_no_show`
- `student_checkin_issue`
- `completion_or_certificate_issue`
- `safety_or_emergency`
- `incident_report`
- `escalation_guidance`
- `site_operations_general`
- Supporting site-intelligence references: `site_opening_reference`,
  `dashboard_metric_explanation`, `zip_site_evaluation`,
  `course_type_recommendation`

## Source Fidelity Rules

The agent labels provenance explicitly:

- `official SOP source`
- `extracted SOP reference`
- `Smart Manikin source`
- `general operations guidance, not official SOP`
- `missing source`

General operational triage is allowed for common incidents, but the answer must
clearly label it as **general operations guidance, not official SOP**. Official
company decisions require source or human review.

### Focused Sub-Issue Routing

A narrow question gets a short, focused answer for the exact sub-issue instead of
the whole scenario bucket. Detection is deterministic keyword matching and never
invents policy, codes, or fixes:

- `venue_access_issue` → `passcode_needed`, `code_failed`, `wrong_room_floor`.
- `student_checkin_issue` → `wrong_course`, `not_on_roster`.
- `completion_or_certificate_issue` → `certificate_issue` (no invented
  eligibility/re-issue rules).
- `electricity_outage` / `internet_outage` → `fix_failed` (still down after the
  basic checks → escalate and start an incident report, do not repeat basics).
- `smart_manikin_troubleshooting` keeps its dedicated routing (see below).

The decision-tree UI opens the matching panel by default (passcode query →
passcode panel, code-failed → venue/property, wrong course → roster, etc.).

### Fuzzy / casual intent routing

Staff rarely type exact SOP wording, so routing is deterministic keyword matching
over a broad bilingual phrase set — casual, incomplete, and typo-ish variants map
to the correct scenario/subtype without any LLM guessing. Coverage spans every
major category: access/passcode, arrival/inspection procedure, iPad/PAD & device,
Bluetooth/connection, training/no-data, wrong-course/roster, instructor-no-show/
class-cannot-start, refund/reschedule/cancel (always approval-gated), certificate/
completion, power/internet/platform, camera/monitoring, safety/injury, cleaning/
supplies, and equipment placement.

Precedence is ordered so safety always wins and specific scenarios beat generic
ones. Guardrails that must hold: `teacher did not arrive` → `instructor_no_show`;
`students arrived and class cannot start` → `class_cannot_start`; arrival/procedure
phrasing → `smart_manikin_site_inspection` / `pre_check_photos`; and truly
unsupported questions stay `unknown` rather than being force-fit. See
`tests/agents/test_fuzzy_routing.py`.

### Passcode panel behavior

The Passcode chip renders from matched operational references, not a hardcoded
message. When a site-less access question is asked, every site's passcode row is
surfaced as *availability*:

- **Locked (default):** rows show the site + label + source with the value replaced
  by the redaction message — never a raw code, and never the misleading "no
  source-backed passcode extracted" when references exist.
- **Unlocked (valid staff token):** the source-backed codes are revealed with the
  "Internal use only. Verify site/building/room before using." warning; multiple
  sites are shown with clear labels.
- A query naming a **non-matching** site (e.g. Palo Alto) still gets only the
  source-needed fallback, never another site's codes.

Site-specific access codes are shown for a matching site directly; redaction is
enforced backend-side in all cases (`passcode_ref_available` /
`passcode_revealed` / `staff_access_unlocked` flags drive the panel).

### Smart Manikin Constraints

The Smart Manikin behavior is intentionally conservative.

Supported by source files:

- Bluetooth/power connection guidance.
- Completion photo/email guidance.
- Wrong room/floor signage issue.

Not supported and therefore not invented:

- Browser dependency.
- Permissions dependency.
- Wi-Fi dependency for Smart Manikin.
- Black-screen fix.
- App self-restart fix.
- Reset/calibration instructions.
- Vendor root cause.
- Hardware diagnosis.

For black-screen/app-restart issues, the agent says the source records the issue
but no documented fix is recorded, and routes it to
`needs engineer/vendor confirmation`.

## Staff Access & Passcode Redaction

Because a site may be used by **both students and staff**, source-backed internal
passcodes are hidden by default. Redaction happens **backend-side** (not
frontend-only), so the API response itself carries no secret values in the
default/public mode.

What is redacted by default (any operational-reference item marked
`sensitivity: internal`):

- Santa Clara lockbox / room passcode and weekend access-card code.
- Newark Suite 2018 passcode and front-gate lockbox code.
- Internal Wi-Fi credentials and internal instruction-video links.
- Any future internal `access_code` / `password` / `keybox` / `door_code` /
  `passcode` item.

In the default mode the value is replaced with
`Restricted internal passcode. Staff must unlock internal access to view it.`
(Chinese: `内部密码已隐藏。员工需先解锁内部权限后查看。`).

**Staff unlock** reveals source-backed codes for one session:

1. Set a server PIN: `ALLCPR_STAFF_ACCESS_PIN=<pin>` (unset → unlock is impossible
   and everything stays redacted).
2. `POST /api/staff-access/unlock` with `{ "pin": "..." }` returns
   `{ "ok": true, "token": "<expiry>.<hmac>" }`. The token is an HMAC signature,
   **never the raw PIN**, and is short-lived.
3. The UI stores the token in `sessionStorage` (not `localStorage`) and sends it
   as `staff_access_token` on the next ask. With a valid token, codes are shown
   with the warning `Internal use only. Verify site/building/room before using.`

Logs never contain raw passcodes, PINs, or Wi-Fi credentials — only the booleans
`staff_access_unlocked`, `passcode_ref_available`, and `passcode_revealed`.

## Smart Manikin Site Representative Inspection SOP

The `smart_manikin_site_inspection` scenario answers weekly site-check questions
from the reviewed source
`app/agents/autocpr_site_manager/smart_manikin_site_inspection_sop.json`
(extracted from *Smart Manikin 专员分点巡检 SOP*, June 29 2026). Narrow questions
route to focused sub-issues: `inspection_frequency`, `pre_check_photos`,
`site_checklist`, `equipment_check`, `access_camera_wifi_signage_safety`,
`post_check_photos`, `weekly_site_check_report`, `upload_materials`,
`do_not_repair`, `issue_escalation`, `equipment_placement`.

The page-3 equipment-placement diagram is indexed as a source image
(`Smart Manikin 专员分点巡检 SOP — equipment placement diagram`) and surfaces for
equipment-placement / 器材摆放 / supplies queries. No image content is analyzed.

### Guided Inspection Workflow

The Q&A page also offers **Start Inspection / 开始巡检** — a fast, mobile-friendly
guided checklist, not a document dump:

1. **Required acknowledgement** before the checklist unlocks: before photos must be
   taken before any cleaning, after photos after the site is arranged, and records
   must be real and complete. The reminder states only that an incomplete/invalid
   record **may require review or explanation to ALLCPR** — the source SOP does not
   state any fine/penalty, so the app uses no fine/penalty wording.
2. **Before photos** checklist (whole room, Smart Manikin area, supplies, door/
   signage, abnormal area).
3. **Site checklist** (hygiene, trash, disinfection, equipment, power cables,
   access, camera, Wi-Fi, signage, safety) with `OK` / `Fixed on site` /
   `Problem — needs support` per item.
4. **After photos** checklist (similar angles; fixed-result photo if any).
5. **Weekly Site Check Report** reminder and **Upload materials** checklist
   (corresponding site Google Drive folder, same day recommended).
6. **Do-not** warnings (no unauthorized dismantle/repair; report unresolved issues
   to ALLCPR; records must be real/complete).
7. **Finish** writes an inspection log. The acknowledgement
   (`inspection_warning_acknowledged` + `acknowledged_at`), checklist statuses, and
   photo-step acknowledgements are stored — **never raw images or local paths**. If
   any item is a problem the log status becomes `needs_support`.

## Repository Layout

```text
.
├── web_app.py
├── app/
│   ├── web/site_ops_agent.html
│   └── agents/autocpr_site_manager/
│       ├── agent.py
│       ├── prompts.py
│       ├── scenarios.py
│       ├── scenario_subissues.py
│       ├── smart_manikin_subissues.py
│       ├── smart_manikin_inspection.py
│       ├── smart_manikin_site_inspection_sop.json
│       ├── staff_access.py
│       ├── schemas.py
│       ├── retriever.py
│       ├── kb_loader.py
│       ├── sop_operational_refs.py
│       ├── sop_operational_refs.json
│       ├── incident_logs.py
│       ├── inspection_logs.py
│       ├── sop.md
│       ├── kb_seed.md
│       └── sop_source_analysis.md
├── VERSION
└── tests/
```

## SOP Source Handling

The live local workspace may contain raw `SOP/Smart Manikin*` folders beside the
app for private auditing and future KB refresh work. Those raw folders are
excluded from this public repository because they may contain private operational
materials such as venue media, room instructions, contacts, or access details.

The committed agent uses sanitized, source-derived artifacts:

- `app/agents/autocpr_site_manager/sop.md`
- `app/agents/autocpr_site_manager/kb_seed.md`
- `app/agents/autocpr_site_manager/sop_source_analysis.md`
- `app/agents/autocpr_site_manager/sop_operational_refs.json`

If the team decides to publish raw SOP assets later, use a private repository or
Git LFS after auditing the files for secrets and private venue details.

## Local SOP Image Support

When raw SOP folders are present locally, the app can build a local media index:

- Extracted/copied media folder: `app/web/static/sop_media/`
- Local JSON index: `app/agents/autocpr_site_manager/sop_media_index.json`
- Served URL path: `/static/sop_media/<filename>`
- Indexer: `app/agents/autocpr_site_manager/sop_media_index.py`

The indexer scans local `SOP/` files for:

- Raw `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif` images.
- Images embedded in `.docx` under `word/media/`.
- Images embedded in `.pptx` under `ppt/media/`.

Matching is deterministic by scenario and tags derived from source filenames,
folder names, and document names. For example, Smart Manikin questions can match
Smart Manikin instruction/quick-start images, while a general power outage does
not receive random Smart Manikin images.

Generated SOP media and the JSON index are committed for this private/internal
deployment so Render can serve source-image references. The raw `SOP/` archive
remains ignored.

## Live Incident Logs

Every `/api/agents/autocpr-site-manager/ask` call appends a lightweight internal
incident log entry. The log records the user-entered site/location, class time,
scenario, severity, first actions, evidence, escalation, SOP image count,
matched operational references, the routed `issue_subtype`/`route_detail` and
`policy_approval_required` flag, the passcode-access booleans
(`staff_access_unlocked` / `passcode_ref_available` / `passcode_revealed`), and the
Smart Manikin sub-issue when relevant. It does not store uploaded image files,
local filesystem paths, raw passcodes, or the raw full answer payload.

Default local storage:

```text
data/incident_logs.jsonl
```

Override with:

```bash
ALLCPR_INCIDENT_LOG_PATH=/path/to/incident_logs.jsonl
```

### Inspection Logs

Completed guided inspections are stored separately (`log_type: inspection`) via
`POST /api/inspection-logs`. Each entry records site, inspector, start/complete
times, the acknowledgement, before/after photo-step checks, the site-checklist
item statuses, weekly-report/upload completion, problems found, fixed/needs-support
counts, and a status of `open` / `needs_support` / `completed`. It never stores raw
image bytes, local filesystem paths, or passcodes.

Default local storage:

```text
data/inspection_logs.jsonl
```

Override with:

```bash
ALLCPR_INSPECTION_LOG_PATH=/path/to/inspection_logs.jsonl
```

Render note: this MVP stores logs locally on the running Render instance. For
production durability across restarts/redeploys, move the log path to a Render
persistent disk or an external database. No external database is required for the
current private MVP.

## Testing

Run the standalone test suite:

```bash
python -m pytest tests -q
```

Known-good local command used during setup:

```bash
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 -m pytest tests -q
```

Expected result at handoff: run the current suite and confirm all tests pass.

## Deployment Notes

This is a FastAPI app. Any platform that can run Python and install
`requirements.txt` can serve it:

```bash
uvicorn web_app:app --host 0.0.0.0 --port "$PORT"
```

The app is local/deterministic. It does not require external API keys.

## Remaining Official Data Needed

The following areas still require official SOP/source confirmation before the
agent should provide final policy guidance:

- Refund, reschedule, cancellation, and compensation rules.
- Official certificate issuance/reissue policy.
- Official customer/student notification templates.
- Final class-continuation decision rules.
- Venue/property escalation contact process.
- Smart Manikin vendor troubleshooting tree and vendor contacts.
- Image/evidence retention policy.

Until those sources are added, the agent will continue to route those matters to
human review instead of inventing policy.
