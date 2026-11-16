# Pilot questionnaire — revised working draft, 29 October 2026

For review and wording/translation testing. Not approved for distribution.
Use with [PILOT_PROTOCOL_DRAFT.md](PILOT_PROTOCOL_DRAFT.md). No participant records
or responses have been generated. Map approved responses to the existing CSV
schema; do not add identifying details to the model data.

The [offline instrument/card preview](../reports/pilot_2026-10-29/preview/START_PILOT_PREVIEW.html)
implements this draft for Ro's wording/interaction review. Practice answers are
temporary; its download contains design feedback only. The proposed age-group
wording is under 18, 18–20, 21–24, 25–29 and 30 or above, with adult eligibility
enforced. No participant administration schema or study approval is implied.

## Participant information and eligibility

This study is part of an ITM 360 final project for the course taught by
Prof. Kuntha Pin. We ask about your age or age group, university year, budget
and laptop needs. We do not collect your name, phone number or email address.
Responses use an anonymous participant code. Do not enter identifying details
in free-text answers. Laptop cards may show out-of-stock, check-stock or
coming-soon listings; please judge suitability using the stated information,
not an assurance that the laptop is available to buy immediately.

Before use, insert the approved researcher/instructor contact, storage/retention
period, withdrawal procedure and cutoff. Explain that this study concerns laptop
suitability for university work; participation is voluntary; questions/cards
may be skipped; laptop information is a dated retailer claim rather than a
purchase, stock or software-performance guarantee. Explain the approved data use
and any sharing before requesting consent. Do not promise anonymity after
publication or withdrawal after linkage is destroyed without an approved rule.

- Are you at least eighteen years old? Yes / No. Stop if No.
- Are you currently a university student in the study's approved population?
  Yes / No. Apply the approved eligibility rule.
- Having read the approved information, do you agree to participate?
  Agree / Decline. Stop if Decline. Record the actual consent status.
- Age or age group: finalize the response format before distribution; do not
  request a date of birth. Confirm adult eligibility separately.
- What university year are you in? Year 1 / Year 2 / Year 3 / Year 4 /
  Year 5 or above / Postgraduate / Other university stage.

The current model-data schema has no age/year columns. Keep these descriptive
answers in the approved separate pilot administration record until its storage
format is finalized; do not put them in comments or add predictive features.

Assign an anonymous participant code. Keep any signed consent or contact
administration separate from this dataset. Record `study_phase=pilot`, the
approved `protocol_version` and the actual timezone-aware profile timestamp.

## Your budget and activities

1. What is the maximum total laptop purchase price you can pay in USD?
   Enter a positive number. This is a mandatory maximum, not a monthly payment.
   Maps to `budget_usd`.
2. What activities do you expect to use it for? Confirmed choices:
   documents/presentations; web/research; online classes; coding; data analysis;
   graphic design/photo editing; 3D modelling/rendering; video editing;
   engineering/CAD; games; another stated task.
   Allow multiple choices and clarification. Maps to `tasks_json`.
3. Which software do you expect to use, if any? Optional free text.
   Maps to `software_names`; it does not generate automatic hardware rules.
The optional legacy `major` field stays blank in this pilot; no university name,
student ID or contact details are requested.

## Requirements the laptop must meet

Explain: a requirement excludes a laptop that does not meet it. Leave it blank
when there is no requirement or you do not know; record which reason was given
in the approved instrument rather than guessing a technical value.

| Question | Response | Existing field |
|---|---|---|
| Minimum RAM you must have? | Positive GB value / no requirement / not sure | `min_ram_gb` |
| Minimum internal storage you must have? | Positive GB value / no requirement / not sure | `min_storage_gb` |
| Maximum laptop weight you can accept? | Positive kg value / no requirement / not sure | `max_weight_kg` |
| Must it have integrated or dedicated graphics? | Integrated / dedicated / no requirement / not sure | `required_gpu_type` |

No OS requirement question or OS eligibility filter is used in this pilot.
Leave legacy `required_os` blank. Cards still show the offer's recorded OS,
including DOS/no OS or Not stated where applicable. Never assume Windows.

Do not infer these answers from budget, major, software, task choices or what
the facilitator thinks the student needs. Unknown laptop attributes cannot
satisfy an active mandatory constraint.

## Preferences, separate from requirements

For each row, ask the desired target and how important that preference is from
0 to 5: 0 = inactive, 1 = very low, 2 = low, 3 = moderate, 4 = high,
5 = very high. These draft anchors need wording approval.

| Preference | Target question/field | Importance field |
|---|---|---|
| Save money below your maximum budget | No separate target; budget already recorded | `importance_savings` |
| More RAM | Desired RAM in GB: `desired_ram_gb` | `importance_ram` |
| More storage | Desired capacity in GB: `desired_storage_gb` | `importance_storage` |
| Portability | Preferred maximum kg: `desired_max_weight_kg` | `importance_weight` |
| Screen size | Preferred diagonal in inches: `preferred_screen_inches` | `importance_screen` |
| Graphics type | Integrated or dedicated: `preferred_gpu_type` | `importance_gpu` |

Whenever importance is above zero, its target is required before profile
submission or assignment. Ask for clarification; the participant can supply a
target or explicitly choose importance zero. Do not invent a target or silently
change importance. Savings uses the already-required budget as its reference.

## Rate each assigned laptop card

Each neutral card is a consistent information panel with delivered hardware,
price in USD, retailer/source, observation or actual confirmation date, condition,
stock status and OS. Show unknown values explicitly. A verified matching product
photo may accompany it, without shop advertising, promotional badges or scores.
A photo does not prove a model's RAM, storage or other delivered specifications.

Prompt: “Considering your stated budget, activities, requirements and
preferences, how suitable is this exact laptop and offer for you?”

1. Very unsuitable
2. Unsuitable
3. Neither suitable nor unsuitable
4. Suitable
5. Very suitable

Also provide **Skip** and **Unable to judge from this information** as separate
options. An optional comment can explain the response. A skip/unable response
has a blank numerical rating; it is never zero or a generated replacement.

Save the genuine response against the exact `assignment_id`, `participant_id`,
`configuration_id`, `offer_id`, `snapshot_version`, displayed order and actual
response timestamp. Show at most fifteen eligible configurations per student.
Do not display predicted scores, performance tiers or claims that software will
run well. Never generate suitability labels from specifications or AI judgments.

## Short exit discussion

- Which questions or laptop terms were unclear?
- Was it easy to distinguish requirements from preferences?
- Was any information missing when you judged a card?
- Why did you skip a card or select unable to judge, if applicable?
- Was the session length acceptable, and what would you change?

Record actual feedback and timing in the approved pilot log. Review the
instrument after the pilot; pilot data must not enter main evaluation after
instrument changes. No model training begins from an empty or invented dataset.
