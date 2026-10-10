# Laptop data collection guide

Use the supplied proposal, especially sections 4.3–4.8, to decide what belongs in the catalogue. This guide turns those choices into collection steps. The first collection target is 40 verified configurations for the pilot; the main target remains 150–250.

## Collect one configuration and its offers

1. Start with the proposal's sources: [Gold One Computer](https://www.goldonecomputer.com/), [PTC Computer](https://ptc-computer.com.kh/) and [Beckie Khmer](https://beckie-khmer.com/). Inspect the exact product page where possible. Category cards are leads when important information is missing.
2. Identify the manufacturer's complete SKU and the delivered CPU, GPU, RAM, storage and display. Record a shop's inventory code separately. A broad model family such as IdeaPad Slim 3 does not establish an exact configuration.
3. Search `laptops.csv` before adding a configuration. The same SKU with the same delivered hardware uses the same `configuration_id` across retailers. An actual RAM/storage/display upgrade can require a separate configuration, supported by evidence. Do not manufacture different configurations from price changes or duplicate listing URLs.
4. Add or update the draft hardware row. Keep unknown fields blank. Save the source and short factual observations in `source_checks.csv`. Use a stable evidence ID and put it in the hardware and offer records.
5. Add one offer row for each observed shop price. Record full USD purchase price, raw price notation, date, availability wording, delivered OS, source and collection version. A sale price is usable only when it refers to the exact delivered configuration and applicable outright purchase terms. Preserve its conditions. Do not use a monthly payment as the purchase price.
6. Verify that the product is new and complete. Record the supporting evidence ID. Do not mark condition `new` just because no used label was seen. Used/refurbished, ambiguous and installment-only listings are outside the approved scope. A zero price or price-on-request listing is not a positive verified purchase price.
7. Resolve conflicting specifications with exact-SKU evidence, using manufacturer documentation where suitable. Record the discrepancy and resolution. Keep unresolved records `quarantined`; do not average conflicting numbers or fill them from a similar model.
8. Perform the manual source check and record reviewer code/time. Only set `record_status` or `offer_status` to `verified` when the evidence supports it. Obtain a second manual check for at least 20 percent of retained records across sources and price bands before freezing. Keep the second-check record separate from the initial check.
9. Run the validator after each batch. Correct structural errors. A warning can identify real unfinished work even when validation passes.

## Record facts consistently

| Attribute | Rule |
|---|---|
| RAM | Delivered capacity in GB; the maximum supported upgrade is a different fact |
| Storage | Advertised internal capacity in GB; use 1 TB = 1000 advertised GB consistently and preserve original notation |
| Storage medium | Separate SSD, HDD, UFS and eMMC; never silently turn UFS into NVMe |
| Display | Diagonal in inches; exact resolution, refresh and panel/touch details only when verified |
| Weight | Configuration weight in kg, with its evidence class; starting-at, shipping and boxed weights do not establish exact laptop weight |
| GPU | Keep actual model text; dedicated means a discrete GPU exists; unknown VRAM is blank, not zero |
| CPU | Keep exact model as nominal text; no hand-invented performance scores |
| Delivered OS | Record what comes with the offer; DOS is not Windows; no licensing or software compatibility assumptions |
| Unknown values | Blank in CSV, shown as unknown in the eventual interface; a mandatory requirement cannot pass on an unknown |
| Battery | Not collected in this first core batch. Any later battery field must preserve claimed versus measured evidence; no comparable battery ranking is authorized |

An empty preferred target can mean not sure or not supplied. The questionnaire pilot must define its exact response handling. A zero importance weight is an explicit inactive preference, not missing data. Do not infer technical requirements from major or software names.

## The first batch needs these checks

| Record | What to resolve |
|---|---|
| LAP0001 / OFF0001 | New condition and current exact configuration; GPU type; stock wording if available |
| LAP0002 / OFF0002 | New condition and exact GPU type; retain the sourced DOS offer |
| LAP0003 / OFF0003 | New condition and exact SKU specifications, including RAM type; confirm the sale applies to the listed configuration |
| LAP0004 / OFF0004 | Product detail URL, new condition, delivered OS, exact display resolution and weight where available |
| LAP0005 / OFF0005 | Product detail URL, new condition, display pixels and weight where available; preserve advertised 1 TB capacity |
| LAP0006 / OFF0006 | Indexed PTC page failed direct retrieval. Find a current exact-SKU listing and verify its price; do not reuse indexed price as current |
| LAP0007 / OFF0007 and OFF0008 | Same-SKU memory/storage descriptions conflict between Gold One and Beckie; verify hardware before final merge or inclusion |
| SRC0009 | Excluded zero-price, out-of-stock lead; do not add a zero-price offer |

Optional fields such as weight need not all be present for catalogue inclusion. They must remain visibly unknown and fail any user hard constraint that depends on them. The core delivered configuration must be identifiable. Catalogue completeness and individual profile eligibility are separate decisions.

## Before showing cards to students

After protocol approval, copy the verified dataset into a named immutable survey snapshot. Record file hashes, neutral-card version and the exact selected offer for each configuration. Keep `collection_2026-09-28_v0` as collection work, not the final survey version.

Use the lowest verified eligible offer among the collected sources, resolving equal prices by a fixed retailer-name order. Filter all mandatory profile conditions before assignment. The treatment of preorder, check-stock and stale offers must be settled with Ro before freezing the protocol; no new availability rule has been imposed here.

For each participant, select up to 15 eligible configurations across the proposal's price-to-budget bands: at most 0.60, above 0.60 through 0.80, and above 0.80 through 1.00. Initially seek five per band; redistribute unused places without duplicates, prioritize less-exposed configurations and use seeded random selection. Log assignments, exposure counts, selection seeds and randomized display order. These bands are relative to each student's budget; do not replace them with fixed dollar bins for the survey.

Neutral cards must use the same fields and show source/date and unknown values, without predicted scores. Record the actual rating, skip or unable-to-judge response. Never generate suitability labels from price, specifications, baseline scores, AI judgments or hypothetical students.

## Versioning and corrections

During draft collection, corrections may update a draft row if the previous observation and reason are retained in the audit log. Once a snapshot has been shown to participants, preserve its configuration, offer and profile data exactly. A later price needs a new offer ID and snapshot; a material hardware correction requires a versioned mapping and an explicit decision about affected judgments. Never silently change what a historical participant appears to have seen.

Pilot and main rows carry separate study-phase and protocol fields. After an instrument change, pilot ratings must not enter final evaluation. Before main-model work, create and freeze participant split and feature manifests as specified by the proposal.

## Collection exit checks

- Reach the agreed pilot catalogue size with identifiable new configurations and verified USD offers.
- Resolve or exclude all ambiguous core specifications; keep the exclusion reasons.
- Ensure unique configuration IDs and valid offer/evidence links, with no duplicate configurations counted as extra laptops.
- Complete and log at least the required 20 percent second manual checks, spread across source and price coverage.
- Review retailer and budget coverage; report gaps without claiming national representation.
- Discuss unresolved instrument and availability policies with Ro, then obtain the required study approvals before recruiting.

The validator checks a subset of these mechanically. Human verification, institutional approval and permission to automate or publish remain separate factual gates from the proposal.
