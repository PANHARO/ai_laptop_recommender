# Pilot import and evaluation

Run commands from the repository root. Use Python 3.12 for TensorFlow;
the collector's Python 3.14 environment can remain separate.

```powershell
py -3.12 -m venv .venv-pilot
.\.venv-pilot\Scripts\python -m pip install -r requirements-pilot.txt
.\.venv-pilot\Scripts\python -m laptop_pilot inspect C:\Users\Pc\Downloads\ITM360_Laptop_Pilot.zip
.\.venv-pilot\Scripts\python -m laptop_pilot reproduce-price C:\Users\Pc\Downloads\ITM360_Laptop_Pilot.zip
.\.venv-pilot\Scripts\python -m laptop_pilot import C:\Users\Pc\Downloads\ITM360_Laptop_Pilot.zip
```

`import` prints the private dataset directory. Use that path for comparison:

```powershell
.\.venv-pilot\Scripts\python -m laptop_pilot compare <private-dataset-directory>
.\.venv-pilot\Scripts\python -m laptop_pilot compare <private-dataset-directory> --exploratory
```

Imports and completed evaluations are preserved rather than overwritten.
If a command says the import already exists, use the dataset under
`private/itm360_pilot/imports/`. A corrected source bundle or reviewed mapping
creates a separate import. All original files, participant rows, validation
identifiers, split IDs, histories, predictions and models stay in ignored
`private/itm360_pilot/`. Do not copy them into `data/` or Git.

The import fields are defined in `config/pilot_import.json`. The original
51-card hardware/offer snapshot is `data/pilot_catalogue.json`; it stays
separate from the live collection CSVs so later prices cannot alter a rating.
All cards are linked, including exact displayed prices, dates and offer IDs.
`LAP0003` and `LAP0006` were not survey cards. See
[the link audit](../reports/pilot_integration/card_offer_links.csv) and
[source hashes](../reports/pilot_integration/recovery_provenance.json).

The original source exports can be checked again with:

```powershell
python -m laptop_pilot recover-catalogue <form_v2_catalogue.json> <form_v2_display.json>
```

All methods share the same budget/RAM/storage/weight/GPU eligibility rules;
unknown required properties fail. All stock states are included and the pilot
has no OS hard filter. Active preferences require genuine targets. Skips,
unable-to-judge and self-reported ineligibility are missing feedback, not labels.
The cleaned ZIP lacks tasks; none are invented. Historical offers do not claim
current freshness or a newly completed survey freeze.

Evaluation reserves about 20% of students, then uses five grouped development
folds with training-only preprocessing. Both models use student-balanced
weights. The forest uses 310 trees and the proposal's 18-setting search. The
MLP uses 33/16 ReLU units, dropout 0.20, AdamW and validation-MSE early stopping;
its final fit uses the median best epoch from development. Ties use historical
price and configuration ID. NDCG@5 uses linear `rating - 1` gain, including
zero ideal gain as zero. The ZIP reproduction preserves its original separate
zero-gain exclusion rule. Model selection never uses test scores.

The primary threshold of ten eligible judgments currently yields no students.
That command returns status 2 and saves the reason. `--exploratory` explicitly
uses two judgments instead; seven students qualify, with only two held out.
Read [the results and limitations](../reports/pilot_integration/RESULTS.md).

Verify the analysis with:

```powershell
.\.venv-pilot\Scripts\python -m unittest discover -s tests -p test_pilot_integration.py -v
git config --local core.hooksPath .githooks
python -m laptop_pilot guard-index
```

For the historical, offline design preview, open `START_PILOT_PREVIEW.cmd`.
It creates no research records. Rebuild it, if needed, with the collection venv:

```powershell
.\.venv\Scripts\python -m scripts.prepare_pilot_preview --output reports/pilot_2026-10-29/preview
```
