# Pilot instrument and card preview — 29 October 2026

## Delivered

`pilot_2026-10-29/preview/START_PILOT_PREVIEW.html` is a self-contained offline
project-review preview. It works without the PC's Python environment. The root
launcher `START_PILOT_PREVIEW.cmd` opens it in the default browser.

The questionnaire includes the course/instructor statement, adult/student/consent
controls, draft age groups and university year, budget and specific task choices,
optional software, separate mandatory requirements and preferences with required
active targets. No name, email, phone, university name or student ID is requested.
No OS eligibility question is included. Age groups are drafted as under 18,
18–20, 21–24, 25–29 and 30 or above; under-18 and decline selections stop profile
completion. Actual participant administration storage remains a separate gate.

Neutral panels contain all 51 verified configurations and 60 verified offers.
Each configuration appears once, with a selector for its dated retailer offers.
The panels retain all stock states and actual source/date, condition, OS, exact
hardware, unknowns and supporting identifiers. No photos have been substituted
from similar models. Card order is shuffled for browsing, without ranking scores.
Budget/mandatory-filter preview is available after a complete practice profile;
unknown required properties fail. It is not a frozen survey selection algorithm
or a participant assignment session. The future at-most-fifteen, budget-band,
exposure-aware recorded assignment plan remains unchanged.

Temporary 1–5/skip/unable controls allow wording and interaction review. The only
download is design feedback with a distinct `pilot_design_feedback_not_participant_data`
type, preview version, catalogue hashes and reviewer notes. It excludes practice
profiles, consent and ratings. No browser persistence, research import, tracking,
network collection, generated labels or model training is introduced.

## Verification

Headless Chrome checked the real exported HTML at 1440-pixel desktop and 390-pixel
mobile widths. Checks passed for adult/decline stopping, required active target,
inclusive budget and RAM/storage boundaries, unknown weight exclusion, descriptive
OS, all stock statuses, skip/unable without numeric ratings, feedback contents,
mobile overflow, zero remote requests and byte-identical canonical CSVs. No page
JavaScript errors occurred. Desktop/mobile screenshots were visually inspected.

Evidence: `staging/pilot-preview-qa/result.json`, desktop/mobile screenshots and
the explicitly QA-only feedback download. These are software checks, not pilot
participant results or manual source checks.

Rebuild with:

```powershell
.\.venv\Scripts\python.exe -m scripts.prepare_pilot_preview --output reports/pilot_2026-10-29/preview
```

Repeat the browser check, using the already installed local Playwright package:

```powershell
node tests/pilot_preview_browser.cjs staging/portable-test-tools/node_modules/playwright
```

## Milestone status and next review

The instrument/card preview is ready for Ro's review. Milestone 2 is not claimed
complete: no participant pilot has run. Open the HTML, try the questions/cards,
download design feedback and return its JSON in the chat. Resolve wording and
language, approved participant contact/storage/retention/withdrawal information,
study approvals and treatment of uncertain dates before creating an actual frozen
survey and conducting the genuine pilot. No blanket catalogue rereview is requested.
