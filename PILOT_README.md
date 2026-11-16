# ITM360 pilot integration

Integration completed 16 November 2026. The project now imports the genuine
`ITM360_Laptop_Pilot.zip`, reproduces its price benchmark, validates historical
card-to-offer links, and compares the four proposal methods. Participant records
stay under ignored `private/itm360_pilot/`; the tracked `data/students.csv`,
`data/ratings.csv` and `data/assignments.csv` remain empty templates.

Read [the findings](reports/pilot_integration/RESULTS.md) before interpreting
model scores. The ten-judgment primary cohort is empty after full eligibility
and profile validation. The completed secondary run is exploratory: seven
students, five development students and two held-out students. It does not
establish a model advantage or complete the main study.

## Reproduce locally

Use Python **3.12** for the tested ML environment. The existing collection venv
uses Python 3.14 on this machine; TensorFlow 2.20 cannot run in that venv.
The collection application does not need the ML dependencies.

```powershell
Set-Location D:\AI_laptop_recommender\AI_laptop_recommender
py -3.12 -m venv .venv-pilot
.\.venv-pilot\Scripts\python -m pip install -r requirements-pilot-lock.txt
python -m laptop_pilot inspect C:\Users\Pc\Downloads\ITM360_Laptop_Pilot.zip
python -m laptop_pilot reproduce-price C:\Users\Pc\Downloads\ITM360_Laptop_Pilot.zip
python -m laptop_pilot import C:\Users\Pc\Downloads\ITM360_Laptop_Pilot.zip
```

`import` prints the private dataset directory. Use that directory in:

```powershell
.\.venv-pilot\Scripts\python -m laptop_pilot compare <private-dataset-directory>
.\.venv-pilot\Scripts\python -m laptop_pilot compare <private-dataset-directory> --exploratory
.\.venv-pilot\Scripts\python -m unittest discover -s tests -p test_pilot_integration.py -v
```

Primary comparison returns exit status 2 with a saved aggregate explanation when
the cohort cannot support the locked evaluation. `--exploratory` explicitly
uses the ZIP's secondary threshold of two eligible judgments, including zero
ideal gain as NDCG zero under the proposal. It still uses a student holdout and
five grouped development folds. It never substitutes a row-random split.

Raw imports and evaluation directories are immutable: an existing import or
evaluation is refused, rather than overwritten or used to repeatedly select
against held-out results. The completed local run is already saved. A corrected
source bundle or a reviewed new column map produces a separate hashed import.
Use `requirements-pilot.txt` for compatible dependency ranges on another supported
Python version; the lock file records the exact tested Windows/Python 3.12 environment.

## Historical catalog recovery

The original 51-card generation export was found in the earlier 3 November
project work as `form_v2_catalogue.json`, with its independent displayed-card
export `form_v2_display.json`. Its source was the 2 November survey app's
`lib/catalogue.json`. The app source's SHA-256 references match all three
current canonical catalog files: laptops, offers and source checks.

`config/pilot/recovered_catalogue.json` contains a standalone, participant-free
copy of the exact verified hardware and dated offers used in those cards,
plus export hashes and the shared/A/B/C/D card inventory. Recovery checks
hardware fields, exact offer IDs, prices, dates, URLs, checked condition/source
evidence, and the displayed `LAPxxxx / OFFxxxx` references. It never matches
on product title alone or replaces a judged offer with a newer cheapest offer.

All 51 ZIP card IDs and printed prices match that export. See
[the complete link audit](reports/pilot_integration/card_offer_links.csv).
`LAP0003` is draft and `LAP0006` is quarantined; neither was a survey card.
There are **zero unresolved survey links**, so no additional catalog file is needed.

To repeat recovery from the retained originals:

```powershell
python -m laptop_pilot recover-catalogue <form_v2_catalogue.json> <form_v2_display.json>
```

These are historical offers, not a newly frozen catalog or a current-price
claim. The later form's recorded historical-offer policy explains why the
original seven-day pre-freeze collection gate is not retroactively applied at
today's date. No evidence has been redated or new freeze asserted.

## Import and validation contract

The bundled README was read, and its original baseline script was inspected
and run locally. The importer does not execute code found in arbitrary bundles.
It rejects unsafe ZIP paths, duplicate CSV keys, repeated participant/card
judgments, unexpected columns in a column map, invalid rating/status pairs,
unresolved cards, and conflicting explicit offers or survey prices.

`config/pilot/itm360_import.json` explicitly maps this ZIP's fields. The generic
example shows how to name different members and columns without fuzzy guesses.
It records the README's cohort-level adult/student/consent attestation; no
individual consent answers, assignment seeds, exposure counts, response codes,
or timestamps are fabricated. Original files and the map stay in the private
hashed import. Skips, unable-to-judge and reported-ineligible responses remain
separate missing-feedback statuses. Over-budget ratings remain in the import.

Nine profiles are excluded from every method's comparison because an active
preference lacks its target. The local `validation.json` identifies the affected
participant IDs and fields. Missing targets are not guessed and importance
weights are not silently switched off. The missing-target counts overlap:
RAM 5, storage 5, weight 6, screen 7 and GPU 1. Structural errors and unresolved
links stop evaluation; profile exclusions are reported and shared by all methods.

Tasks are absent from the cleaned ZIP. The models record that absence and use
the available structured predictors; they do not invent task labels or infer
hardware requirements from major, software, or unspecified requirements.
Explicit mandatory `not_sure` answers remain uncertainty indicators.

## Shared ranking and evaluation

All methods use the same genuine, numerically rated, verified cards after
budget, minimum RAM/storage, maximum weight and required GPU checks. Unknown
mandatory attributes fail. Every stock status is retained and no OS hard
filter is applied, following the confirmed pilot policy. Each configuration
appears at most once. Ties use lower historical price and then configuration ID.

Content matching implements the exact functions in the hash-matched original
proposal: savings `1-price/budget`; RAM/storage `min(actual/desired,1)`; weight
`min(desired/actual,1)`; screen `max(0,1-abs(actual-desired)/3)`; and exact GPU
type match. Active importance weights are normalized by their sum; unknown
attributes earn zero without reducing that sum. With no active weights, the
price/ID tie rule gives ascending price order.

Seed 42 reserves about 20% of cohort students before model fitting. Five
`GroupKFold` development folds fit their own encoders and numeric medians;
entirely missing numeric columns fall back to zero plus a missing indicator.
The MLP also standardizes numeric inputs using each training fold and leaves
binary indicators unchanged. CPU/GPU names are nominal, with no performance tier.
IDs, SKU, retailer, URLs, comments, future prices and held-out labels are excluded.
Training weights are inverse student judgment counts, normalized to mean one.

The forest searches the proposal's 18 settings with 310 trees. Selection uses
macro student NDCG@5; ties favor shallower trees, then larger leaves. The Keras
MLP has 33/16 ReLU units, 0.20 dropout, linear output, AdamW 0.001/0.0001,
batch size 16, at most 150 epochs, validation-MSE patience 10 and restored best
weights. Histories recompute weighted training/validation MSE and MAE with dropout
disabled. Final development refit uses the median best epoch across five folds.
The learned default is selected on development scores, before held-out scoring.
Predictions are neither rounded nor clipped.

NDCG@5 uses linear `rating-1` gain, logarithmic discounts and equal student
weight. The ZIP reproduction retains its original exclusion of zero-ideal-gain
students; the four-method comparison follows the proposal's zero score policy.
MAE is reported only for learned rating predictions. Precision@5 applies only
to students with five candidates; shorter-list precision is separate. Paired
intervals use 2,000 student resamples and are exploratory with only two test
students. No main-study inference, full-catalogue recall, or runtime claim is made.

## Privacy and Git

Only code, dependency declarations, participant-free catalog links and aggregate
findings are committed. The ZIP, all participant rows, validation IDs, splits,
predictions, histories and fitted models remain under ignored `private/`.

The local checkout has `core.hooksPath=.githooks`. The pre-commit hook rejects
known human-data files and nonempty participant CSVs even if force-added; it
permits the existing header-only templates. On another clone, enable it with:

```powershell
git config --local core.hooksPath .githooks
python -m laptop_pilot guard-index
```

The substantial collection/review changes that predated this integration remain
uncommitted and were not bundled into its commit. The recovered snapshot lets
this integration run independently of those pending catalog changes.
