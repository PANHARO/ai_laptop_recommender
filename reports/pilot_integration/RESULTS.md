# ITM360 laptop pilot integration — 16 November 2026

The ZIP's price baseline was reproduced exactly, and all **51 survey cards**
were linked to their original verified, dated offers. The main comparison
cannot be estimated: after profile validation and the complete shared hardware
eligibility filter, **zero students have ten eligible judgments**.

A separate exploratory comparison was completed with seven students who have
at least two eligible judgments. It uses five development students and two
held-out students, with five student-grouped development folds. These results
cannot establish that a learned model improves recommendation quality.

## Original benchmark reproduced

The bundle README and original `price_baseline.py` were inspected. The original
script ran locally, and an independent implementation matched every field in
`price_baseline_results.json`, including the full-precision scores below.

| Budget-only cohort | Students scored | Mean student NDCG@5 |
|---|---:|---:|
| At least 10 within-budget numeric judgments | 10 | 0.5972316214492109 |
| At least 2 within-budget numeric judgments | 19 | 0.7139838141762228 |

There are 25 cleaned profiles, 250 numeric ratings, 187 within-budget ratings,
63 over-budget ratings, 23 students with numeric ratings, and 51 rated cards.
Twenty students meet the secondary threshold; its original script excludes one
zero-ideal-gain student, leaving nineteen scored. Those exact original rules
are preserved solely for reproduction. The proposal comparison includes
zero-ideal-gain students with NDCG zero.

The baseline in the ZIP checks budget only. Its cohort and scores must not be
compared directly with the full-eligibility model scores below.

## Original catalog and exact links recovered

The earlier project work contained `form_v2_catalogue.json` and its independent
`form_v2_display.json` from 3 November. The source survey app's `lib/catalogue.json`
also survives from 2 November. Its three stored source hashes exactly match
the current `data/laptops.csv`, `data/offers.csv` and `data/source_checks.csv`.
The original proposal's SHA-256 also matches `config/proposal_lock.json`.

Recovery required exact hardware, offer ID, displayed price, observation date,
source URL, checked offer/condition evidence and displayed card references.
The ZIP's entire 51-card inventory and all printed prices agree with this
retained card-generation export. Shared and A/B/C/D card inventories are saved.
No title-only or same-price guess was promoted to a confirmed link.

| Link audit | Result |
|---|---:|
| Verified survey card/configuration/offer links | 51 |
| Unresolved survey links | 0 |
| LAP0003 | Draft, absent from survey |
| LAP0006 | Quarantined, absent from survey |

See [all card-to-offer links](card_offer_links.csv) and the participant-free
`config/pilot/recovered_catalogue.json`. Offer snapshot identifiers are retained
exactly as stored; the later instrument version is recorded separately. This
recovery does not assert that an immutable pre-recruitment freeze occurred, or
that an October price remains current. No additional catalog file is needed.

## Full eligibility and data limitations

All four methods use the same candidate sets after verified new/positive/USD/
outright offer checks, budget, RAM/storage minima, maximum weight and required
GPU type. Unknown required attributes fail. All stock statuses remain included;
the confirmed pilot has no OS hard filter. Historical rated offers are never
replaced by later or cheaper offers.

Nine profiles lack at least one target whose importance is above zero and are
excluded from every method, without guessing targets or changing their weights.
The counts overlap: missing RAM targets 5, storage 5, weight 6, screen 7 and GPU 1.
Local `validation.json` retains the exact affected participant IDs and fields.
The ZIP contains no tasks, response timestamps or original response codes;
these were not reconstructed. The README supplies cohort-level adult/student/
consent provenance, rather than fabricated individual administrative fields.

Across all profiles, budget plus hardware requirements retain 47 numeric
judgments. After the profile exclusions, **26 eligible judgments remain across
8 students**. Seven students have at least two, supplying 25 judgments to the
exploratory cohort. One additional student has only one. None reaches ten.
Skips (49), unable-to-judge (18), and self-reported ineligibility (41) stay
distinct missing-feedback statuses, not numerical labels.

## Exploratory four-method comparison

Seed 42 reserves two of the seven cohort students before model fitting. The
other five undergo five-fold `GroupKFold` development validation; no student's
rows cross groups. There are 18 development ratings and 7 held-out ratings.
Each method ranks precisely the same eligible, genuinely rated cards per
student. Scores use linear `rating - 1` gain and equal student weight.

| Method | Development NDCG@5 used for selection | Held-out NDCG@5 | Held-out rating MAE |
|---|---:|---:|---:|
| Ascending price | 0.918662 | 1.000000 | — |
| Weighted content matching | 0.960004 | 0.991446 | — |
| Random Forest | 0.994682 | 0.837021 | 0.883337 |
| Small MLP | 0.978653 | 0.837021 | 3.396214 |

Development results are selection scores, not an independent final estimate.
The forest was selected as the learned default using development data only.
Its 310-tree search selected depth 4, minimum leaf size 3 and maximum features
1.0 from the proposal's eighteen settings. Student-balanced sample weights and
fold-local preprocessing were used for both models.

The Keras MLP used the specified 33/16 ReLU layers, dropout 0.20, linear output,
AdamW, batch size 16 and validation-MSE early stopping. Its five best epochs
were 13, 60, 26, 42 and 1; the final refit used their median of 26 epochs.
Predictions are unrounded and unclipped, so MAE can exceed the rating scale's
width. The MLP's poor MAE shows unstable rating prediction on this tiny sample;
the results were not used to retune the architecture or held-out split.

The held-out RF-minus-content NDCG difference is -0.154425. Its exploratory
2,000-resample paired student bootstrap interval is [-0.222253, -0.086598].
With only **two** held-out students this interval is not evidence of a reliable
population effect. Price's perfect score is also a result on tiny judged sets,
not proof of general superiority. Only one held-out student has five candidates;
ordinary Precision@5 is therefore reported for that one student, while the
two-student shorter-list precision is kept separate in the aggregate JSON.

No full-catalogue recall, current purchasing availability, main-study result,
production model quality, or recommendation-runtime claim is made. The missing
task answers are an explicit feature limitation of this cleaned export.

## Validation and privacy

The integration's twelve focused tests pass, including NDCG agreement with
scikit-learn, hard-constraint boundaries, missing-target handling, exact-link
conflicts, fold-local imputation, student-grouped splits, tamper detection and
staged participant-data rejection. The complete existing suite passes **79
tests**, and the existing validator's **12 integrity checks** pass.
Saved forest/Keras models and their preprocessors reproduce every stored
held-out prediction after loading. `pip check` passes in the ML environment.

All participant rows, the original ZIP and original reproduction files,
validation identifiers, split manifests, histories, predictions and fitted
models remain in ignored `private/itm360_pilot/`. The commit contains only code,
participant-free catalog/provenance, dependencies and aggregate findings.
The local Git pre-commit hook guards participant CSVs and local artifacts,
including force-added files. The tracked participant CSV templates stay empty.
Existing uncommitted collection/review work is preserved separately.

## What is needed next

No catalog or offer-link file is missing. The primary cohort needs genuine
additional eligible judgments, under an approved administration procedure,
until enough students have at least ten. Missing active preference targets
need genuine participant clarification or documented exclusion; do not
manufacture them. If restoring the task predictors is desired, supply an
authorized, pseudonymous profile export with `participant_id` and the original
`tasks_json` answers, aligned to this cleaned export. Keep that export local.

For running/import details, see [PILOT_README.md](../../PILOT_README.md).
