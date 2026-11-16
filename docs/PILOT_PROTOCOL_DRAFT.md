# Pilot protocol — confirmed design decisions, 29 October 2026

Status: prepared for Ro and instructor review. This is not an approved protocol,
a frozen survey catalogue, or permission to recruit. See the generated
`reports/pilot_2026-10-28/READINESS.md` for actual catalogue and check counts.

## Purpose and scope

Test whether adult Cambodian university students can understand the profile
questions, distinguish mandatory requirements from preferences, judge neutral
laptop cards, and complete the instrument. The proposal's working pilot target
is about ten adults and forty verified, distinct configurations. Pilot and main
responses must remain separate, especially after instrument changes.

No performance scores, synthetic suitability labels, new ranking method or
change to the locked model/evaluation plan is introduced here. Model training
waits for genuine responses and the later development/test split freeze.

## Design decisions confirmed by Ro on 29 October 2026

The user-confirmed policy is recorded in `config/pilot_policy.json`. This records
design authorization, not instructor/institutional approval or an actual freeze.

| Topic | Confirmed handling | Remaining preparation |
|---|---|---|
| Availability | Include all stock statuses: In Stock, Out of Stock, Check Stock, Coming Soon/preorder and blank. Apply equally to older and newer models. | Display original wording; blank displays as Availability not stated. Do not infer model age or purchase availability. |
| Offer age | Maximum seven calendar days at the actual freeze, in Asia/Bangkok. Age 0 through 7 days is allowed. Original intended date: 28 October 2026. Ro subsequently authorized moving the actual freeze until freshness checks are complete. | Audit dated observations or genuine passed human rechecks of each exact offer. Retain original dates. Record the real freeze date and recompute the seven-day window then. |
| Task vocabulary | Multi-select: documents/presentations; web/research; online classes; coding; data analysis; graphic design/photo editing; 3D modelling/rendering; video editing; engineering/CAD; games; other stated task. | Final wording/Khmer translation. Tasks/software do not generate hidden hardware requirements. |
| Active preference target | A target is required whenever importance is above zero. No target is required for importance zero. | Ask the participant to supply a target or explicitly choose inactive; block incomplete profile submission/assignment. Never silently change their answer. |
| OS requirement | No OS question or delivered-OS hard filter in this pilot. Retain actual delivered OS on offers/cards; unknown stays unknown. | Keep legacy required_os blank. The methodology adjustment is recorded in proposal_lock.json; no Windows assumption or compatibility inference. |
| Neutral cards | Consistent factual panels showing hardware, exact dated offer, condition, retailer/source/date, stock and unknowns; no scores, recommendation order or promotional claims. | A matching verified product photo is optional. It supplements the information panel; it does not establish the delivered specifications. Final layout/language review remains. |
| Participant information | ITM 360 final project for the course taught by Prof. Kuntha Pin. Collect age/age group, university year, budget and laptop needs with anonymous participant codes; no names, phone numbers or emails. | Finalize age versus age-group wording, approved storage/retention, withdrawal procedure and participant contact information. Instructor/institutional approval remains separate. |

The original requested date is not evidence that a survey was frozen on that
day. Confirmation occurred on 29 October, and Ro authorized a later actual freeze
after freshness checks. An immutable export must record its real creation
timestamp; do not label later evidence as available on 28 October. Until the
actual freeze, readiness assesses freshness provisionally at its report date.
Ro subsequently reported completion of all checks within 20–28 October, with
only the overall range known. Preserve this interval and the eleven exact
second-check dates. A range overlapping the seven-day cutoff is date-uncertain,
not evidence that reviews were never completed. Do not invent exact dates or
request a blanket repeat. Resolve treatment of this uncertainty before freeze;
the seven-day policy is unchanged.
Out-of-stock cards measure suitability of dated offers,
not immediate purchasing availability; explain this when requesting ratings.

## Catalogue preparation

1. Reach forty distinct verified configurations with verified, positive, outright
   USD offers and explicit new-condition evidence. Different URLs, prices,
   retailers or observation dates are not extra configurations.
2. Resolve or exclude overlapping model families and conflicting hardware.
   Keep missing optional properties visibly unknown. A retailer statement about
   new stock establishes only its documented scope. Ro's later 28 October
   clarification identifies the reviewed Beckie catalogue listings as belonging
   to the new-laptop category; combine it with the retained store messages.
   Exclude the separate second-hand category and do not automatically extend
   that clarification to future, unreviewed listings.
3. Complete a separate manual source check of at least twenty percent of retained
   configurations, spread across retailers and price coverage. At forty this is
   at least eight. The generated readiness packet reports the current required
   count and selects additional checks as the catalogue grows. Passed checks
   are recorded only from returned human findings, reviewer and actual time.
   An AI desk audit is not this second human check.
4. Apply the confirmed availability/age policy and assess exact offers before freezing.
   Select the lowest verified eligible offer per configuration, breaking equal
   prices by fixed retailer-name order, as already specified in the collection
   guide. Do not treat the QA queue's representative offers as survey selection.
5. Freeze a named immutable catalogue, profile/card/instrument versions and
   hashes only after the preceding gates pass and study approvals are recorded.

## Session flow after approval

Use the [questionnaire draft](PILOT_QUESTIONNAIRE_DRAFT.md). Explain participation
and obtain consent; confirm adult/student eligibility; record the anonymous
profile and its timestamp before assignment; show up to fifteen eligible cards;
collect genuine ratings, skips or unable-to-judge responses; then ask the exit
questions. Keep contact/consent administration outside the model repository.

Follow the proposal's existing assignment plan: budget-relative price bands
at most 0.60, above 0.60 through 0.80, and above 0.80 through 1.00. Initially aim
for five cards per band; redistribute empty places without duplicates,
prioritize less-exposed configurations, use seeded random selection and
randomize display order. Log the exact offer, catalogue version, participant,
assignment ID, seed and displayed position. No assignments are generated by
this draft or the readiness script.

The same explicit budget and mandatory RAM/storage/weight/GPU constraints
must govern eligibility across methods. An unknown required property fails its
constraint. Do not infer compatibility from major or software names.

## Pilot assessment

Record completion time, unclear questions/terms, missing-target cases, empty
eligible sets, skips/unable-to-judge responses and requested corrections.
Summarize actual observations; do not invent a satisfaction score, participant
count or rating. Log instrument changes and obtain approval for the revised
version before main collection. The main targets and locked evaluation remain
unchanged in `config/proposal_lock.json`.

## Second-check checklist

For each selected row in the generated CSV, reopen the exact listing using its
shop/manufacturer locator. Check delivered CPU/GPU, RAM, storage medium/capacity,
display, full USD purchase terms, offer condition evidence, source identity,
date, stock wording and any OS claim. Compare against the recorded row, including
unknowns. Record passed or failed, actual reviewer code/time and factual notes.
If anything changed, record a new observation/correction; do not overwrite a
historical offer or pre-fill a successful second check. Return the completed
CSV for audited incorporation before freeze.
