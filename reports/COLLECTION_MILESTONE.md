# Collection and human verification milestone

Implemented on `feat/laptop-collection-review`, based on master `0087b937fbc1891d14adf64ec77a62d6b59c4e32`. The proposal lock, canonical schema, all seven original CSVs, data dictionary and existing validator scripts remain byte-for-byte unchanged. No participant data, ratings, assignments, synthetic research labels or survey was created. See [the recorded results and hashes](collection_milestone_report.json).

## Verified results

| Check | Result |
|---|---|
| New offline tests | 37 passed |
| Existing validator checks | 7 passed |
| Canonical CSV validation | PASS: 7 configurations, 8 historical offers, 9 source references, 5 issues; 0 verified |
| Live three-per-retailer smoke | Gold One 3, PTC 3, Beckie 3; no failed/blocked sources |
| Final one-per-retailer transport smoke | 1 each, all recognized as existing observations; no overwritten reviews |
| Offline larger batch | 40 candidates staged, canonical files unchanged |
| Local reviewer | CLI startup and HTTP health passed; Streamlit form actions passed in temporary fixture workspaces |

Live collection occurred on 15 October 2026 UTC after robots and configured public policy pages were checked. PTC's robots endpoint returned 404, which is recorded separately from a retrieval failure. No automation prohibition was found on the inspected pages; this is not affirmative retailer permission. The [source access audit](../docs/SOURCE_ACCESS_AUDIT.md) records the inspected URLs and limits.

No live 40-configuration collection or human verification is claimed. The development queue and saved public HTML are ignored by Git; a checkout needs its own fresh batch. The remote browser could not reach the container's loopback address, so browser visual inspection was unavailable. The dark card layout follows the supplied reference; functional form testing and server startup passed.

## Review the first batch

Follow [README Start here](../README.md#start-here) to create the Python environment, run `python -m laptop_collection collect --site all --limit 3 --max-pages 1`, then `python -m laptop_collection review`. Open the printed localhost URL and use **Open laptop source** and **Open catalogue evidence**. Correct the fields, record evidence and choose Approve, Reject, Needs Review or Skip. Approval requires all four explicit factual confirmations and the existing verified-record completeness checks.

Use `python -m laptop_collection seed-existing` to also queue historical offers and source-only leads such as SRC0009 without any network request. This preserves their original dates and never changes an old price. Import or collect a fresh observation for a current price.

## Remaining work

- Confirm exact manufacturer SKUs, actual new condition and delivered hardware; missing facts remain blank.
- Check Beckie's catalogue locators carefully when detail links return a generic page or Coming soon. Retain Needs Review if identity cannot be established.
- Resolve conflicting SKU/hardware evidence explicitly. A price update creates a new offer ID; it never replaces an old offer.
- Expand configurable batches to around 40 distinct verified configurations and record the proposal's second manual check of at least 20 percent.
- Complete the existing protocol/instrument and study-approval gates before any later participant collection. This milestone does not start them.

The [workflow guide](../docs/COLLECTION_WORKFLOW.md) covers manual URL/authorized export inputs, safe writes, recovery, testing commands and larger batches.
