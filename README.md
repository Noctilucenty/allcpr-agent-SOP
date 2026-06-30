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
| Health check | `/health` |

## Assistant UI

The `/` and `/agent` pages are intentionally simple:

1. Type a site-operations question.
2. Pick English or Chinese.
3. Optionally expand **Advanced details** for site, class time, or attachment
   description metadata.
4. Read a compact answer first: summary, first action, steps, evidence,
   escalation/human review, SOP image evidence, and sources.
5. Expand **Show full structured details** only when the complete answer payload
   is needed.

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
  "attachments_note": ""
}
```

## Supported Scenarios

- `electricity_outage`
- `internet_outage`
- `venue_access_issue`
- `smart_manikin_troubleshooting`
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
│       ├── schemas.py
│       ├── retriever.py
│       ├── kb_loader.py
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

The committed agent uses sanitized, source-derived markdown artifacts:

- `app/agents/autocpr_site_manager/sop.md`
- `app/agents/autocpr_site_manager/kb_seed.md`
- `app/agents/autocpr_site_manager/sop_source_analysis.md`

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

Generated media and the JSON index are ignored by git because they may contain
private SOP/venue material.

## Testing

Run the standalone test suite:

```bash
python -m pytest tests -q
```

Known-good local command used during setup:

```bash
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 -m pytest tests -q
```

Expected result at handoff: `104 passed`.

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
