# Personalized Laptop Recommendation System for Cambodian University Students

ITM-360 implementation, milestone 1. Prepared 28 September 2026 from the supplied `AI_project_proposal.docx`. The proposal is the source of truth. Its SHA-256 is recorded in `config/proposal_lock.json` so later work can identify the exact version used.

This repository contains the dataset structure, public HTML collectors, a separate staging queue, a local Streamlit verification desk and a runnable validator. The collection milestone supports human review of extracted candidates; it does not complete the pilot catalogue. No research method has been changed, no participants have been recruited, and no model has been trained.

## Start here

Open the repository folder in VS Code. Use Python 3.11 or newer. On Windows PowerShell, create a local environment and run the first batch without activating scripts:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m laptop_collection collect --site all --limit 3
.\.venv\Scripts\python -m laptop_collection review
```

On Linux/macOS, use `python3 -m venv .venv`, then use `.venv/bin/python` for the same commands. Open the localhost URL printed by Streamlit. Click **Open laptop source**, edit the fields and evidence, then choose **Approve**, **Reject**, **Needs Review** or **Skip**. Approval requires your explicit new-condition, exact-SKU, delivered-specification and outright-price checks. Missing information remains visible and cannot be silently completed.

See [the collection and review workflow](docs/COLLECTION_WORKFLOW.md) for larger batches, manual URL imports, authorized exports, duplicate handling and recovery. [The access audit](docs/SOURCE_ACCESS_AUDIT.md) records what was inspected for each retailer. The existing [collection guide](docs/COLLECTION_GUIDE.md) and [data dictionary](docs/DATA_DICTIONARY.md) remain the canonical research rules.

[Milestone verification results](reports/COLLECTION_MILESTONE.md) include actual per-site smoke counts, test results and outstanding manual checks.

To queue the old CSV observations and source-only leads (including SRC0009) for inspection without visiting any website, run `python -m laptop_collection seed-existing`. These remain dated historical observations, not fresh price confirmations. The collected candidates and saved reviews live locally under ignored `staging/`; they are not automatically shared with GitHub.

Run the existing validator after a review batch while the reviewer is stopped. The validator itself still uses only the Python standard library:

```bash
python scripts/validate_data.py --write-report
```

On a system where Python is named `python3`, use `python3` in that same command. It also works in PowerShell without Bash line continuations.

The validator separates a structurally valid dataset from verified research data. A PASS means IDs, types and implemented relationships passed. Read the warnings and verified counts as well.

## Current collection status

| Item | Count | Meaning |
|---|---:|---|
| Provisional configuration records | 7 | Five draft and two quarantined |
| Dated offer observations | 8 | Five draft and three quarantined |
| Source references | 9 | Includes one excluded zero-price lead |
| Verified configurations and offers | 0 | Manual checks and explicit new-condition evidence remain open |
| Students, ratings and assignments | 0 | Empty templates, with no invented research records |

This is a small schema-checking batch, not a representative sample or a completed pilot. It includes direct page retrieval, catalogue cards and one quarantined indexed listing. The retrieval date is not a guarantee of current price or stock. All prices require review before participant use.

## Data organization

| File | One row represents |
|---|---|
| `data/laptops.csv` | One exact hardware configuration |
| `data/offers.csv` | One retailer's dated purchase offer for a configuration |
| `data/students.csv` | One anonymous participant profile in its study phase |
| `data/ratings.csv` | One genuine response to a displayed configuration and offer |
| `data/assignments.csv` | One candidate card selected and ordered for a participant |
| `data/source_checks.csv` | One evidence reference and its manual review history |
| `data/issues.csv` | One inclusion, exclusion, correction or unresolved issue |

`docs/DATA_DICTIONARY.md` describes every column. `config/schema.json` gives the validator the same definitions. Delivered OS is stored on offers because shops may deliver different OS packages for identical hardware. This placement preserves the proposal's verified delivered-OS constraint.

Join offers to laptops on `configuration_id`. Join each rating to its original `offer_id`, participant and assignment. Never join a historical rating to today's lowest price. A shop inventory code is not a manufacturer SKU. Multiple offers are allowed for one configuration; recommendations must still show each configuration once.

## Methodology preserved

The four methods remain ascending price, weighted content matching, Random Forest regression and a small MLP. All apply the same hard eligibility filter. The target remains a real student's suitability rating from 1 to 5. IDs, retailers, source URLs, comments and future prices are excluded from predictors.

The main targets remain 150–250 configurations, about 50 complete students, and 500–1,000 genuine ratings, with up to 15 judged configurations per student. The separate pilot targets about 10 adults and a working catalogue of 40 configurations. Forty fits both pilot ranges appearing in the proposal.

Evaluation remains approximately 20 percent held-out students, five-fold grouped development validation, student-level NDCG@5 with linear gain `rating - 1`, and the proposal's secondary outcomes. Random Forest uses 310 trees; the MLP uses 33 and 16 hidden units. These unusual but explicit values are preserved in the configuration record.

No numerical CPU/GPU tier, comparable battery ranking, synthetic preference label, extra recommender or different split has been added. Changes to sampling, labels, feature semantics, baseline weights, models or evaluation require discussion with Ro before implementation.

## Milestones and completion gates

| Milestone | Completion gate | Status |
|---|---|---|
| 1. Dataset design and initial collection | Linked schema, documented units and provenance, first sourced batch, tested structural validator | Starter implemented; verification and collection continue |
| 2. Pilot catalogue and questionnaire | Around 40 verified configurations; approved consent and instrument; separate pilot with about 10 adults | Next |
| 3. Main collection and freeze | 150–250 configurations where feasible; genuine ratings; documented exclusions and frozen snapshots | Pending |
| 4. Shared constraints and baselines | Same candidates and deterministic ties for price/content methods; boundary checks | Pending |
| 5. Random Forest and MLP | Grouped splits, fold-local preprocessing, student weights, histories and development-only selection | Pending |
| 6. Streamlit and locked evaluation | Shared pipeline, factual explanations, final comparison, usability and reporting | Pending |

The next hands-on batch is to verify the first ten complete configurations, including the resolvable entries here, then expand to the working target of 40. Recheck at least 20 percent of retained records across sources and price bands. This is a second manual pass, not automatically a second researcher.

## Decisions to discuss before the pilot is frozen

The proposal leaves task vocabulary, handling an active preference with an unknown target, availability eligibility (for example check-stock or preorder), and exact OS matching vocabulary to protocol work. This scaffold records the underlying facts but does not choose those policies. The validator flags missing preference targets; it uses conservative exact OS matching only when checking an assignment. No survey assignments are generated here.

Source access conditions must be checked before automating collection. The new optional collectors recheck public robots/terms pages, use bounded public HTML requests and keep every extraction unverified in staging. Human approval remains separate. Instructor approval and any required institutional review must precede recruitment, as specified in the proposal.

## Verification and limits

Run `python scripts/check_validator.py` to repeat the focused integrity checks. The tests use clearly artificial records in temporary folders and never add them to the research dataset.

The included report records current CSV hashes. These identify the supplied data files; they do not prove that a retailer claim is correct and do not constitute the later survey freeze. No independently measured laptop performance, manufacturer corroboration, manual second-pass review or human preference data is claimed.

Keep contact details and consent-administration documents outside the model repository. Public release of any later human records must follow the proposal's consent and disclosure provisions.
