# SOP Library Audit — ALLCPR Site Operations Agent

This audit classifies every file in `SOP_library/` by how it serves the ALLCPR
Site Operations Agent **today**. It is the human-readable companion to the
machine-readable
[`app/agents/autocpr_site_manager/sop_library_audit.json`](../app/agents/autocpr_site_manager/sop_library_audit.json).

The original SOP files are **kept as-is** — this pass only decides which ones get
converted into ordered, step-by-step app workflows, which are indexed as
templates/references, and which stay in the library without affecting the app.

> No raw passcodes appear in this audit. Per-site door/lockbox/Wi-Fi codes were
> already excluded from the curated library (they live only in the redacted,
> staff-gated operational-reference layer inside the app).

## Categories
- **active_workflow** — directly useful now; converted into an app
  workflow/checklist that staff follow step by step.
- **reference_template** — useful as a form/template/reference; indexed and
  linked, but not an active staff workflow yet.
- **archive_only** — kept in the library, not consumed by the assistant.

## A. Used by the assistant now (active_workflow)
| File | Used for |
| --- | --- |
| `01_Core_SOPs/Smart Manikin 专员分点巡检 SOP.docx` | The **Smart Manikin Full Site Inspection** workflow — arrival & before photos, table/station pre-check, site checklist, on-site handling, after photos, Weekly Site Check Report, upload, and do-not-repair rules. Staff-only (PIN-gated). |
| `02_Forms_and_Templates/ICPIS Weekly Site Check Report.docx` | The **report step** of the full inspection: site result, problems found, actions taken, whether ALLCPR support is needed. |

These two power the ordered workflow in
[`sop_workflows.json`](../app/agents/autocpr_site_manager/sop_workflows.json)
(`smart_manikin_full_site_inspection`) and the guided UI.

## B. Templates / references only (reference_template)
Indexed and available, but **not** wired into the default staff inspection:

- **New Site Assessment (future workflow)** — `Smart Manikins 新地点开发 SOP.docx`,
  `Smart Manikin 现场考察表.docx`, `SMART MANIKIN SITE FIELD ASSESSMENT FORM.pdf`,
  `Smart Manikin 选址评分表.xlsm`, `新点审批 邮件申请模版.docx`. Captured as an
  ordered reference workflow (`smart_manikin_new_site_assessment`) that is **not**
  shown in the default UI.
- **Business Trip Process (reference workflow)** — `Short Term Business Trip SOP.docx`
  plus the seven `03_Business_Trip_Forms/` attachments and
  `Mileage Reimbursement Policy for ALLCPR Instructor.docx`. Only relevant when
  staff travel; captured as `business_trip_process` and **deliberately kept out of
  the site-inspection flow**.
- **Partner / strategy references** — `Smart Manikin ICPIS 合作分点开发与运营 SOP.docx`
  (partner role boundaries) and `Smart Manikin New Market Expansion SOP.docx`
  (market-level strategy). Reference only.
- **Site signage asset** — `分点指示牌 1.0版本.pdf`. A print asset the inspection
  references (signage-complete check); not converted to steps.

## C. Excluded from the app (archive_only)
- `README.md` — the library index/documentation itself, not an operational SOP.

## Pictures / diagrams
Images support the workflows but never replace written steps. The only image
wired into an active workflow is the **equipment placement diagram** (page 3 of
the inspection SOP), surfaced via `/api/inspection-reference` with an explicit
caution: *"Reference only; do not repair or dismantle equipment."* It helps with
the table/station pre-check, equipment placement, and supplies checks — it is
**not** shown as repair instructions. See `sop_media_index.json` and the
`image_references` block of `sop_workflows.json`.

## What still needs official clarification
- The **New Site Assessment** and **Business Trip Process** workflows are drafted
  from the source SOPs as reference-only; wiring either into the staff UI needs a
  product decision (and, for new-site, sign-off on the scoring↔decision-band
  mapping already flagged in `sop_source_analysis.md`).
- The Weekly Site Check Report's exact upload destination is per-site Google Drive
  folders; the workflow records "upload completed" but does not manage Drive
  itself.
- Anything touching cost/lease/refund/insurance/safety stays a **human-review**
  handoff, per the source SOPs — the app never self-approves these.
