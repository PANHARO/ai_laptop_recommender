# Student laptop recommender

ITM 360 project for Cambodian university students. The project includes a local
laptop collection/review desk and a private pilot-analysis pipeline comparing
ascending price, weighted content matching, Random Forest and a small MLP.

The catalog contains **51 verified configurations and 60 verified dated offers**.
The pilot ZIP's original budget-only price baseline is reproduced exactly:
**NDCG@5 0.597232** for ten students. All 51 survey cards have verified links to
the offers actually displayed.

After the full eligibility rules and incomplete-profile exclusions, no students
have ten eligible judgments. The separate exploratory comparison has seven
students and only two held out; it does not establish a model advantage.
Read [the results](reports/pilot_integration/RESULTS.md).

## Setup and review

Use Python 3.11 or newer for collection. On Windows:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m laptop_collection review
```

Open the localhost address printed by Streamlit, or double-click
`START_REVIEW.cmd` after setup. The review queue and retained evidence live in
ignored `staging/`; a fresh clone starts with an empty queue. Verified catalog
CSVs are shared, but raw evidence and the local review database are not.

To collect a small batch or inspect the queue:

```powershell
.\.venv\Scripts\python -m laptop_collection collect --site all --limit 3
.\.venv\Scripts\python -m laptop_collection status
```

The collector checks configured source-access rules. Approval requires human
verification of the exact hardware, outright price and new condition. Unknowns
stay unknown; a changed price becomes a new dated offer. See the
[collection workflow](docs/COLLECTION_WORKFLOW.md) for review, manual imports,
portable review files, evidence and recovery.

## Pilot analysis

Use a separate Python 3.12 environment for TensorFlow:

```powershell
py -3.12 -m venv .venv-pilot
.\.venv-pilot\Scripts\python -m pip install -r requirements-pilot.txt
.\.venv-pilot\Scripts\python -m laptop_pilot reproduce-price C:\Users\Pc\Downloads\ITM360_Laptop_Pilot.zip
.\.venv-pilot\Scripts\python -m laptop_pilot import C:\Users\Pc\Downloads\ITM360_Laptop_Pilot.zip
```

Use the printed dataset directory with `python -m laptop_pilot compare` in the
pilot venv. The [pilot guide](docs/PILOT.md) covers the primary and exploratory
runs, validation, historical source recovery and offline design preview.

## Project files

| Location | Purpose |
|---|---|
| `laptop_collection/` and `review_app.py` | Collection, verification and local review UI |
| `laptop_pilot/` | Import, shared eligibility, rankers and student-grouped evaluation |
| `data/` | Catalog CSVs, participant-free historical pilot snapshot and empty participant templates |
| `config/` | Schema, source access, proposal settings and pilot import/policy |
| `scripts/` | Validation, offline review exports and preview generation |
| `tests/` | Artificial fixtures and regression tests |
| `docs/` and `reports/` | Guides, dated audits and aggregate findings |
| `staging/` and `private/` | Ignored local evidence, participant data and model outputs |

The exact hardware configuration and dated offer are separate records.
Historical ratings must retain their original offer; never substitute today's
lowest price. IDs, retailer names, URLs and comments are not model features.
The [data dictionary](docs/DATA_DICTIONARY.md) defines columns and units.
Dated protocol drafts and readiness reports describe their historical stage;
the pilot results above describe the current analysis.

## Checks

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -v
.\.venv\Scripts\python scripts/validate_data.py
.\.venv\Scripts\python scripts/check_validator.py
.\.venv-pilot\Scripts\python -m unittest discover -s tests -p test_pilot_integration.py -v
```

Pilot tests are skipped when the optional ML dependencies are absent. A
structural validator PASS does not certify current prices, stock, research
approval or model quality.

## Keep participant data local

The ZIP, participant rows, splits, training histories, predictions and fitted
models belong under ignored `private/`. The `data/students.csv`, `ratings.csv`
and `assignments.csv` files remain header-only templates. Consent/contact
administration stays outside the model repository.

Enable the included staged-data check on a new clone:

```powershell
git config --local core.hooksPath .githooks
python -m laptop_pilot guard-index
```
