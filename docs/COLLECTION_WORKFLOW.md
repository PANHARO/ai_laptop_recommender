# Laptop collection and verification workflow

This milestone implements the proposal's catalogue acquisition with automated extraction followed by manual checking. The four rankers, canonical field meanings, user eligibility constraints, sampling, participant handling and evaluation remain unchanged. There are no rating labels, surveys, model training, accounts or purchasing features in this tool.

## First batch

Install Python 3.11 or newer and open the project directory. Use your virtual environment's Python for every command below. The README gives Windows commands that do not require PowerShell activation.

```bash
python -m pip install -r requirements.txt
python -m laptop_collection collect --site all --limit 3 --max-pages 1
python -m laptop_collection review
```

The first command installs the collector/reviewer dependencies. Collection rechecks robots.txt and configured terms/about pages for each source before any product fetch. It prints actual extraction counts and failures. Open the localhost URL printed by Streamlit, usually `http://127.0.0.1:8501`. The server binds only to loopback. Keep that binding; this milestone is a local research tool.

Choose a candidate, click **Open laptop source**, and optionally **Open catalogue evidence**. Inspect the manufacturer SKU, shop SKU, actual delivered configuration, price, availability and explicit new-condition evidence. Use **Edit product fields** to correct the extraction. Preserve the original price notation and separate list/sale prices; an installment quote cannot become an outright purchase price.

Complete the evidence boxes and four unchecked confirmations before approving. The source page may not state new condition or an exact part number; leave such a candidate for review or obtain documented retailer/manufacturer evidence. An ordinary retail page alone does not confirm new condition. A shop's BECKIE or LLS inventory number is not a manufacturer SKU.

## Review actions

| Action | Local state | Canonical effect |
|---|---|---|
| Approve | approved, only if complete and nonconflicting | Checked source evidence, verified configuration or explicitly confirmed matching draft, a new immutable offer and an issue/audit decision |
| Needs Review | needs_review | New conflict evidence and quarantined issue; no verified configuration or offer |
| Reject | rejected | New pending evidence and excluded issue; no verified configuration or offer |
| Skip | skipped | No CSV write; the local decision is logged |

Needs Review saves your edits, notes, reviewer code and review time. Include skipped items in the sidebar filter to return to them. Approved and rejected decisions are final observations; a changed product or new price requires a new candidate observation. The interface never refreshes retailer pages in the background.

Skipped items are included in the default queue. Use **Find skipped** in the sidebar to clear retailer/search filters and show only skipped observations. Candidate labels include their saved decision. Reopening an editable review restores its most recently saved factual confirmations and notes. Save receipts and approval errors appear in a fixed corner alert so they remain visible while scrolling.

Manufacturer SKU is optional under the verification and deduplication rules. Keep missing part numbers blank; a shop inventory ID is not a replacement. When a SKU is available, it remains strong identity evidence. When it is absent, approval requires the complete delivered-hardware fields and the reviewer uses those fields conservatively for identity matching. Warranty duration and placement outside a second-hand category can be recorded as contextual evidence, but do not by themselves establish new condition. A documented retailer statement covering the exact listing or a clearly defined set of listings can support condition verification.

Core approval fields are the existing verified-configuration requirements: brand/model, delivered CPU/GPU, RAM, storage capacity/medium and identifiable display, plus the offer's positive finite outright USD price and provenance. Manufacturer SKU is optional metadata; preserve it when available and leave it blank when unavailable. Weight, VRAM, exact pixels, GPU type and OS remain optional when the proposal/schema permits missing data. Unknown required-by-profile attributes will still fail the later shared eligibility filter; the review tool does not invent a value or relax that rule. Literal placeholders such as Unknown do not complete a mandatory product field.

Catalogue cards are explicitly flagged. Beckie cards have exact shop locators and individual links, but some detail routes may show a generic or unrelated catalogue. Verify the card identity using the shop SKU, and retain Needs Review if the identity or facts cannot be confirmed. Preorder/check-stock/out-of-stock labels are retained, with no new availability eligibility policy introduced.

## Larger collection batches

```bash
python -m laptop_collection collect --site all --limit 40
python -m laptop_collection collect --site goldone --limit 40 --max-pages 8
python -m laptop_collection status
```

`--limit` is the maximum extracted observations per retailer, including previously staged observations. All three sources at 40 can produce up to 120 candidate observations. Pagination follows actual public pagination links; it does not generate hidden API requests. Default page cap is eight; valid explicit caps are 1–50. Actual counts can be lower due to missing pages, robots rules, errors or insufficient public listings. Forty candidates do not establish 40 distinct verified configurations; count the canonical verified configuration metric after review.

Delay is at least three seconds between requests to a source and respects a larger published crawl delay. Default timeout is 20 seconds with two bounded retries for timeouts/5xx. Authentication, 403/429, challenge walls and detected terms restrictions stop that source. Robots-disallowed paths are not fetched. Responses are size-limited. Logs and policy hashes are saved under `staging/runs/`; fetched public evidence is saved under `staging/evidence/`. No challenge solving, credential use, cookie import, IP changes or protected endpoint access is implemented.

## Manual URL and authorized export alternatives

The sidebar can queue an individual product URL without fetching it. For a list, put one public HTTPS product URL per line in a UTF-8 text file, then run:

```bash
python -m laptop_collection import-urls --site beckie --file my_urls.txt
python -m laptop_collection review
```

This performs zero network requests. You open the page yourself and enter its supported facts in the reviewer. It works when a retailer disallows automated retrieval. Set that source's `mode` to `manual_urls` in `config/collection_sources.json` if restrictions are identified; automatic collection will refuse it.

For a product export provided or explicitly authorized by the retailer, use a JSON array of product objects. Each object must have `source_url` and the actual `observed_date` in YYYY-MM-DD format. Other keys use the editable canonical names from the schema, with extra `full_name`, `manufacturer_sku_evidence`, `specification_evidence`, `condition_evidence` and `condition_evidence_url` where available. Numeric values may be numbers or plain unit-normalized strings; raw price wording belongs in `price_text`.

```bash
python -m laptop_collection import-export --site ptc --file authorized_products.json --authorization "Retailer permission reference and date"
```

The authorization reference is retained in staging. This imports supplied bytes only, never fetches a website and never marks anything verified. It is not a workaround for a scraping prohibition. Do not download restricted pages and relabel them as an authorized export.

## Deduplication and historical data

Candidate identity uses source/site, product URL, UTC observation date and extracted fields. Recollecting the same observation does not overwrite its review or add a second copy. A changed price or a later observation day creates another candidate and, after approval, a new offer ID. No existing offer is updated.

Hardware matching uses an exact manufacturer SKU when available, with complete delivered CPU/GPU, RAM, storage and display as the fallback when it is absent. Numeric formatting and trademark/prose differences are normalized only for identity comparisons, without assigning performance tiers. Known optional hardware contradictions also trigger a conflict. A shared model family or shop inventory code is insufficient. Conflicting records are not silently merged.

A matching verified configuration is reused without changing its recorded attributes. A matching draft/quarantined configuration requires explicit draft confirmation and resolution notes before promotion; nonempty hardware values and old source rows are preserved. A draft referenced by a rating/assignment cannot be edited/promoted here. Unknown or conflicting hardware requires a documented correction, not an ungrounded approval. A genuinely different delivered hardware variant requires the separate variant confirmation plus evidence/resolution text; it gets a new configuration ID. Do not use that option for price changes, wording differences or uncertain specifications.

The original `config/schema.json`, proposal lock, existing CSV records, validator and participant/profile/assignment files are preserved by this milestone. Nothing from previous chats is silently substituted for the repository's current files. Use the reviewer or collect a current observation to incorporate further corrections.

## Local audit and recovery

Retained retailer-message screenshots can support condition only for their
documented scope. The reviewer service accepts an optional `condition_document`
when an audited import supplies the relative path under `staging/evidence`,
SHA-256, contextual retailer URL, received date, factual scope and an explicit
new-condition determination. It validates the saved bytes and retailer, retains
the document on the review event, and creates a separate source evidence row
linked through the verified offer's `condition_evidence_id`. A private message
without a public URL is identified by its retained file; the contextual retailer
homepage is not represented as the message URL. Screenshot receipt dates do not
replace product observation dates, and ambiguous documents cannot approve an
offer. This does not mark any second manual check as passed.

Returned manual second-check CSVs are incorporated by
`laptop_collection.rechecks.apply_rechecks` against the original exported queue.
Configuration/offer/source fields must match exactly. Status, reviewer, actual
timezone-aware timestamp and factual findings are required. The service retains
the submitted findings, updates the linked source-check metadata and writes a
separate recoverable catalogue audit event. It does not replace historical
offer facts, generate candidate reviews or count an AI audit as a human pass.

An explicitly named configuration can also be reconciled during review when
the exact manufacturer SKU matches, the reviewer confirms the existing record
and documents the resolution, and no known hardware contradicts it. This
supports completing missing fields and matching equivalent display wording;
it does not allow model-family matches, changed RAM/GPU/display, or invented
variants. Nonempty canonical hardware stays unchanged.

### Review on another laptop without Python

Run `python -m scripts.portable_review export staging/portable-review` to export
only candidates currently marked `pending`. Copy `START_REVIEW.html` from that
folder to the other laptop and open it in Chrome or Edge. The file embeds the
extracted fields and evidence; retailer links need internet. Edit fields and
record decisions, then use **Download results** regularly and before closing.
Use **Load saved results** to resume from the downloaded JSON in another browser.
Browser autosave is a convenience, not the transfer file.

For unresolved saved reviews, add `--state needs_review` to the export command.
The exported form restores saved factual confirmations, notes and current
revision numbers. Returning approvals retain the hashed condition document from
the trusted export manifest when its evidence URL is unchanged.

Return the downloaded `laptop-review-results-*.json` together with the original
batch identity. Keep the exported `manifest.json` on the home PC. With the
Streamlit reviewer stopped, preflight the returned decisions using
`python -m scripts.portable_review check RESULTS.json --manifest staging/portable-review/manifest.json`.
Use the same command with `apply` instead of `check` to import. Preflight replays
the whole batch in a temporary copy before any live review writes. Import uses
the normal evidence, duplicate, revision, schema, transaction and audit checks.
Identical reimports return the existing receipts; changed or stale reviews are
refused. Unfinished drafts are retained for browser resumption and are not
applied as decisions. The export does not include existing `needs_review` items
or mark pending observations as verified.

SQLite staging holds original extraction payloads, reviewed edits, states and revision numbers. Original evidence is never executed in the UI; displayed content is escaped. Saved raw evidence is hashed, and approval refuses evidence that has changed or disappeared. New condition can have its own checked evidence reference when its URL differs from the product page. Second manual checks remain pending; approval does not claim the proposal's second-pass requirement has been met.

All canonical writes are serialized with a cross-platform file lock, schema-validated in a temporary copy, and applied with per-file atomic replacement plus a durable transaction intent. The transaction retains before/after bytes and the review event under `staging/transactions/`. Startup completes an interrupted transaction exactly once. Recovery refuses to overwrite an unrelated external CSV change. If that happens, stop the app, back up `data/` and `staging/`, resolve the specific outside edit against the journal and restart. Do not delete a pending journal to hide an incomplete write.

Repeated identical approval submissions return the same receipt. Stale tabs and competing sessions are refused using candidate revisions. Canonical CSVs and SQLite cannot be atomically replaced as one operating-system object; the journal provides recovery. Use the app's lock-aware reader and stop the reviewer before running independent CSV tools or making manual edits. Keep staging and data on the same local machine, not a network filesystem, for the documented locking guarantees.

## Verification commands

```bash
python -m unittest discover -s tests -v
python scripts/validate_data.py
python scripts/check_validator.py
```

Collection tests use handwritten product HTML fixtures and temporary workspaces. Pilot tests use explicitly artificial judgments in temporary test folders; they never add research rows. The suite covers parsers, prices/units/unknowns, manufacturer versus shop IDs, hardware conflicts, review gates, historical offers, transaction recovery, access-policy failures, offline batches, Streamlit forms and grouped evaluation. Passing fixture tests does not prove that a retailer is currently accessible.

Review the source access audit before expanding collection. The current catalog has 51 verified configurations and 60 dated offers. See the [project overview](../README.md) and [pilot results](../reports/pilot_integration/RESULTS.md) for the completed pilot analysis and its remaining data limitations. Dated readiness reports retain their historical gates; they are not current-price or study-approval certificates.
