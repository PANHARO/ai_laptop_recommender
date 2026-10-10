# Dataset dictionary

Schema version 0.1. Proposal sections 4.3 to 4.8 and Table 4 are the authority. These columns implement those requirements; they do not freeze the pilot questionnaire or choose new model features.

CSV format: UTF-8, comma delimiter, header row, quoted text when needed. Blank means unknown or not supplied; never use zero for missing data. Booleans are 1 or 0. Dates use YYYY-MM-DD; event timestamps include a UTC offset. IDs are stable and excluded from model features. Required means required for a stored row, with stricter checks for verified records.

## laptops.csv

Primary key: `configuration_id`.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `configuration_id` | text | Yes | Stable project ID such as LAP0001; never a predictor. |
| `brand` | text | Yes | Manufacturer name. |
| `model` | text | Yes | Readable model name; not enough alone to identify a configuration. |
| `manufacturer_sku` | text | No | Exact manufacturer part number including suffix; retailer inventory code belongs in offers. |
| `cpu_model` | text | No | Exact delivered CPU as sourced; nominal, never an invented performance tier. |
| `gpu_model` | text | No | Delivered graphics description; preserve both GPUs if listed. |
| `gpu_type` | enum:integrated,dedicated | No | Dedicated means a discrete GPU is present, even if integrated graphics also exist; blank if unverified. |
| `gpu_vram_gb` | number:nonnegative | No | Verified dedicated VRAM in GB; shared system memory is not dedicated VRAM. |
| `ram_gb` | number:positive | No | Delivered RAM in GB, not the supported maximum. |
| `ram_type` | text | No | Delivered memory technology as sourced. |
| `storage_gb` | number:positive | No | Advertised total internal capacity; use 1000 GB per advertised TB and keep raw text in evidence. |
| `storage_type` | enum:ssd,hdd,ufs,emmc,mixed | No | Verified delivered medium; do not equate UFS with an NVMe SSD. |
| `screen_inches` | number:positive | No | Display diagonal in inches. |
| `display_resolution` | text | No | Verified pixel dimensions such as 1920x1080; preserve unresolved labels in display_text. |
| `display_text` | text | No | Display identity including sourced panel type, resolution label, refresh and touch when known. |
| `refresh_hz` | number:positive | No | Verified refresh rate; blank does not mean 60 Hz. |
| `weight_kg` | number:positive | No | Verified configuration weight in kg; do not use a starting-at or shipping weight as exact. |
| `weight_evidence_type` | enum:retailer_claim,manufacturer_spec,measured | No | Evidence class for weight; no equivalence to independent measurement is implied. |
| `evidence_ids` | ids | Yes | Semicolon-separated source evidence IDs supporting these attributes. |
| `record_status` | enum:draft,verified,quarantined,excluded | Yes | Only verified records may enter a frozen survey catalogue. |
| `review_notes` | text | No | Unresolved fields and corrections; not a predictor. |

## offers.csv

Primary key: `offer_id`.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `offer_id` | text | Yes | Immutable observation ID such as OFF0001; a later price needs a new row and ID. |
| `configuration_id` | text | Yes | Foreign key to laptops.configuration_id. |
| `retailer` | text | Yes | Canonical name: Gold One Computer, PTC Computer, or Beckie Khmer for this batch. |
| `retailer_sku` | text | No | Shop inventory code; never substitute for a manufacturer SKU. |
| `price_usd` | number:positive | Yes | Observed full purchase price in USD; no installments or zero-price placeholders. |
| `currency` | enum:USD | Yes | USD only in the approved catalogue. |
| `price_text` | text | Yes | Short original price notation preserving sale and list-price distinction. |
| `source_url` | url | Yes | Product URL where available; catalogue URL plus exact SKU anchor otherwise. |
| `observed_date` | date | Yes | Date this evidence was retrieved; does not assert that an indexed page was refreshed that day. |
| `availability_text` | text | No | Original stock wording; blank means no explicit stock statement. |
| `condition` | enum:new,used,refurbished,unknown | Yes | New condition needs evidence; a normal retail listing alone is not explicit confirmation. |
| `condition_evidence_id` | text | No | Evidence ID supporting a new-condition decision; required for verified offers. |
| `purchase_type` | enum:outright,installment_only,unknown | Yes | Full-price purchase basis; retain installment-only leads in the issue log, not eligible offers. |
| `delivered_os` | text | No | Verified delivered OS for this particular offer; OS can differ between shops for the same hardware. |
| `snapshot_version` | text | Yes | Collection version, initially collection_2026-09-28_v0; this is not yet a frozen survey snapshot. |
| `evidence_id` | text | Yes | Foreign key to source_checks.evidence_id. |
| `offer_status` | enum:draft,verified,quarantined,excluded | Yes | Only verified eligible offers may be selected for a survey. |
| `review_notes` | text | No | Unresolved offer issues; not a predictor. |

## students.csv

Primary key: `participant_id`.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `participant_id` | text | Yes | Anonymous participant code; no name, email, phone or university ID. |
| `study_phase` | enum:pilot,main | Yes | Keep pilot and main analysis separate. |
| `protocol_version` | text | Yes | Instrument and consent protocol version in force at collection. |
| `consent_status` | enum:consented,withdrawn,declined | Yes | Administrative status; only consented records can provide usable feedback. |
| `adult_confirmed` | boolean | Yes | 1 when adult participation criterion is confirmed; 0 otherwise. |
| `profile_recorded_at` | datetime | Yes | ISO 8601 timestamp with timezone; freeze profile before assignment. |
| `budget_usd` | number:positive | Yes | Mandatory maximum USD budget. |
| `tasks_json` | json_array | Yes | Student-selected or stated tasks as a JSON array of strings; questionnaire vocabulary awaits pilot. |
| `software_names` | text | No | Optional stated software; advisory only and not automatic compatibility requirements. |
| `major` | text | No | Optional descriptive major; excluded from hardware rules and current model feature plan. |
| `min_ram_gb` | number:positive | No | Explicit mandatory RAM minimum; blank means not specified. |
| `min_storage_gb` | number:positive | No | Explicit mandatory storage minimum; blank means not specified. |
| `max_weight_kg` | number:positive | No | Explicit mandatory weight ceiling; blank means not specified. |
| `required_gpu_type` | enum:integrated,dedicated | No | Explicit mandatory GPU type; blank means not specified. |
| `required_os` | text | No | Explicit delivered-OS requirement; no automatic OS compatibility inference. |
| `desired_ram_gb` | number:positive | No | Soft desired RAM target, separate from min_ram_gb. |
| `desired_storage_gb` | number:positive | No | Soft desired storage target, separate from min_storage_gb. |
| `desired_max_weight_kg` | number:positive | No | Soft preferred maximum weight, separate from max_weight_kg. |
| `preferred_screen_inches` | number:positive | No | Soft preferred display diagonal. |
| `preferred_gpu_type` | enum:integrated,dedicated | No | Soft desired GPU type; blank means unknown or unspecified. |
| `importance_savings` | integer:0:5 | Yes | Preference importance; zero is inactive. |
| `importance_ram` | integer:0:5 | Yes | RAM preference importance; zero is inactive. |
| `importance_storage` | integer:0:5 | Yes | Storage preference importance; zero is inactive. |
| `importance_weight` | integer:0:5 | Yes | Portability preference importance; zero is inactive. |
| `importance_screen` | integer:0:5 | Yes | Screen preference importance; zero is inactive. |
| `importance_gpu` | integer:0:5 | Yes | GPU preference importance; zero is inactive. |

## ratings.csv

Primary key: `rating_id`.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `rating_id` | text | Yes | Unique observation ID. |
| `assignment_id` | text | Yes | Foreign key to the exact neutral card assignment. |
| `participant_id` | text | Yes | Foreign key to students; must match the assignment. |
| `configuration_id` | text | Yes | Exact configuration judged; must match both offer and assignment. |
| `offer_id` | text | Yes | Exact dated offer shown, never a subsequently refreshed price. |
| `snapshot_version` | text | Yes | Must match the assignment and offer snapshot. |
| `rating_status` | enum:rated,skipped,unable_to_judge | Yes | Skips and unable-to-judge responses are missing feedback. |
| `suitability_rating` | integer:1:5 | No | Required only for rated responses; blank otherwise; no rule-generated labels. |
| `display_order` | integer:1:15 | Yes | Shown position, copied from assignment. |
| `rated_at` | datetime | Yes | ISO 8601 timestamp with timezone. |
| `comment` | text | No | Optional participant comment; never a predictive feature. |

## assignments.csv

Primary key: `assignment_id`.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `assignment_id` | text | Yes | Unique neutral-card assignment ID. |
| `participant_id` | text | Yes | Foreign key to students. |
| `configuration_id` | text | Yes | Foreign key to laptops; no duplicate configurations per participant. |
| `offer_id` | text | Yes | Frozen selected offer; lowest verified eligible offer for that configuration under the protocol. |
| `snapshot_version` | text | Yes | Frozen snapshot identifier. |
| `protocol_version` | text | Yes | Assignment protocol version. |
| `price_budget_band` | enum:le_0.60,gt_0.60_le_0.80,gt_0.80_le_1.00 | Yes | Band computed from observed offer price divided by participant budget. |
| `selection_seed` | integer:0:2147483647 | Yes | Recorded selection seed; no seed chosen by looking at ratings. |
| `exposure_count_before` | integer:0:2147483647 | Yes | Configuration assignment count immediately before this selection. |
| `display_order` | integer:1:15 | Yes | Seeded randomized presentation order. |
| `assigned_at` | datetime | Yes | ISO 8601 timestamp with timezone. |
| `card_version` | text | Yes | Version of the identical neutral card fields and wording used. |

## source_checks.csv

Primary key: `evidence_id`.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `evidence_id` | text | Yes | Unique reference used by laptop and offer rows. |
| `source_url` | url | Yes | Public page inspected; product-specific URL preferred. |
| `page_locator` | text | Yes | Product name, manufacturer SKU or shop code locating the facts. |
| `retrieved_date` | date | Yes | Date inspected through the retrieval service. |
| `access_mode` | enum:retrieved_product_page,retrieved_catalogue,indexed_search_only,manual_page,manufacturer_page | Yes | Distinguishes indexed evidence and live manual review; retrieval is not a stock confirmation. |
| `facts_observed` | text | Yes | Compact factual transcription, not a copy of the full webpage. |
| `source_check_status` | enum:pending,checked,conflict | Yes | Human verification status; automated transcription is pending. |
| `checked_by` | text | No | Collector/reviewer code, not a participant identity. |
| `checked_at` | datetime | No | Timezone-aware timestamp of actual manual check. |
| `second_check_status` | enum:pending,passed,failed,not_selected | Yes | Manual second pass; at least 20 percent of retained records across sources and price bands before freeze. |
| `second_checked_by` | text | No | Code of person carrying out the second manual pass; may be the solo researcher. |
| `second_checked_at` | datetime | No | Timestamp of that second pass; do not pre-fill. |
| `evidence_file` | text | No | Relative path to permitted screenshot or other retained evidence, if actually saved. |
| `notes` | text | No | Missing fields, discrepancies, retrieval limitations and verification actions. |

## issues.csv

Primary key: `issue_id`.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `issue_id` | text | Yes | Unique audit event ID; retain history when resolving. |
| `entity_type` | enum:configuration,offer,source,protocol | Yes | What is affected. |
| `entity_id` | text | Yes | Configuration ID, offer ID, evidence ID or protocol section. |
| `source_url` | url | No | Source supporting the issue, where applicable. |
| `logged_date` | date | Yes | Date recorded. |
| `issue_type` | text | Yes | Short reason such as storage_conflict or invalid_price. |
| `decision` | enum:pending,quarantined,excluded,resolved | Yes | Current inclusion decision; resolution must describe evidence. |
| `details` | text | Yes | Observed conflict or reason for exclusion. |
| `resolution` | text | No | Evidence-backed resolution, blank while unresolved. |
