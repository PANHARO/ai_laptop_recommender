# Returned fourteen reviews and nine manual checks — 28 October 2026

Eleven requested approvals were accepted. Three Gold One observations remain Needs Review because the return compares them with PTC configurations while still omitting the exact Gold One suffix/panel/RAM evidence needed to establish identity. They were not added as new configurations and were not forcibly merged.

All nine submitted human checks were recorded with reviewer Ro, the actual submitted 2026-10-28T22:14:00+07:00 timestamp, and the original findings. Identity/offer/source fields match the original queue. The timestamp was checked against the actual import time. These are returned human checks, not generated AI checks.

The catalogue now contains **51 verified configuration records and 60 verified dated offers**. Nine configurations have passed second checks; twenty percent of 51 rounds up to eleven. Only **two additional checks** are outstanding for that coverage requirement. The original nine stay recorded.

## Audit findings

- The VTech product_id=5782 citation opens E1504TA-BQ070W, a different laptop, and was rejected as evidence for X1404VA-EB2275W. [ASUS X1404 platform storage specifications](https://www.asus.com/laptops/for-home/vivobook/asus-vivobook-14-x1404/techspec/) support the storage-medium correction alongside the exact Beckie SKU/capacity review. The wrong original citation remains preserved in the unchanged submitted JSON.
- [ASUS Cambodia identifies exact E1504FA-BQ5090W hardware](https://www.asus.com/kh/laptops/for-home/all-series/vivobook-go-15-oled-e1504f/), supporting LPDDR5 and NVMe storage. Its two dated Beckie observations reuse existing LAP0039 with explicit same-part confirmation; no extra configuration is counted.
- The [ASUS Cambodia E1404TA exact-SKU listing](https://www.asus.com/kh/laptops/for-home/vivobook/asus-vivobook-go-14-e1404g/) and its techspec support completing the existing same-part LAP0007 draft with UFS storage and documented missing fields. Nonempty historical hardware was retained; no variant was invented.
- [ASUS E1504TA specifications](https://www.asus.com/kh/laptops/for-home/vivobook/asus-vivobook-go-15-oled-e1504g/techspec/) and the submitted exact BQ177W source support keeping storage as UFS rather than SSD.
- [ASUS Cambodia names E1404FA-EB138W](https://www.asus.com/kh/laptops/for-home/vivobook/vivobook-go-14-e1404f/) and corroborates the proposed SSD correction. The separate Gold One zero-price/out-of-stock offer was not imported.
- [Dell AC16251 internal-slot documentation](https://www.dell.com/support/manuals/en-us/alienware-aurora-ac16251-gaming-laptop/alienware-16x-aurora-ac16251-owners-manual/internal-slots?guid=guid-647a9bd6-0be5-4b27-9df1-31e3c269abed&lang=en-us) and [Dell AC16250 storage documentation](https://www.dell.com/support/manuals/en-us/alienware-aurora-ac16250-gaming-laptop/alienware-16-aurora-ac16250-owners-manual/storage?guid=guid-381dc6f8-242a-41ce-b4b2-fbf5cbd0287c&lang=en-us) corroborate SSD medium. Delivered capacities remain the exact retailer observations, not maximum upgrade capacities.
- The checklist flags PTC S3407CA-LY071W summary LPDDR5X versus description DDR5. [ASUS Cambodia explicitly lists that SKU with 16GB DDR5](https://www.asus.com/kh/laptops/for-home/vivobook/asus-vivobook-s14-s3407/), supporting recorded RAM technology. The original contradictory summary remains visible in the findings; manufacturer marketing display wording was not copied into the delivered configuration.

## Preserved records and remaining work

Original JSON, CSV, original nine-row queue, their hashes and a pre-import data/database backup are retained under `staging/review-return-14-and-rechecks-2026-10-28`. Candidate decisions use the normal review transaction journal. Manual checks use a separate catalogue audit event, leaving candidate revisions and dated offer facts unchanged. Earlier offer and issue rows were checked for preservation. Participant, rating and assignment templates remain byte-identical and empty.

[Two additional manual checks](pilot_2026-10-28/additional_second_check_queue.csv) · [Full check history/queue](pilot_2026-10-28/second_check_queue.csv) · [Current readiness](pilot_2026-10-28/READINESS.md) · [Three unresolved identities](UNRESOLVED_REVIEWS_2026-10-28.csv).

Availability/offer-age decisions, task/OS and unknown-target handling, instrument/consent and study approvals remain open. No survey freeze, recruitment, assignment generation or training is claimed.

## Per-review outcome

| Candidate | Submitted | Applied state | Configuration / offer |
|---|---|---|---|
| CAN559e98dbd00c5cc7a38f34b9 | approve | approved | LAP0048 / OFF0058 |
| CANd7571ed13d72b1630ca11c7c | approve | approved | LAP0049 / OFF0059 |
| CAN351b2d6926544f3f4069e115 | approve | approved | LAP0039 / OFF0060 |
| CAN9687052797e98fb1dfb98001 | approve | needs_review |  /  |
| CANc53a5e003421d69ac697a417 | approve | needs_review |  /  |
| CAN1cc01ef8828a8966fb68721a | approve | needs_review |  /  |
| CAN5edf927429ec270f481fa314 | approve | approved | LAP0048 / OFF0061 |
| CANa20d3e0ce270855140011585 | approve | approved | LAP0049 / OFF0062 |
| CAN1a2c0ab65064ab9e579ff78c | approve | approved | LAP0039 / OFF0063 |
| CANebe2b7690e43ed00979a8958 | approve | approved | LAP0050 / OFF0064 |
| CANe161976298c6bbafdb2289b1 | approve | approved | LAP0051 / OFF0065 |
| CAN496e925c4b58229e8e0b24ea | approve | approved | LAP0052 / OFF0066 |
| CAN926289a3f147af9d9a5b6bab | approve | approved | LAP0007 / OFF0067 |
| CANa8a6d69c881e0d3ecbbd6700 | approve | approved | LAP0053 / OFF0068 |

## Two additional checks received — manual coverage complete

Both returned rows (LAP0051/OFF0065 and LAP0007/OFF0067) match their original configuration, offer, source evidence and queue fields. Ro marked both passed with actual timestamp 2026-10-28T22:44:00+07:00, before import. The submitted findings and original file are retained unchanged under `staging/two-additional-rechecks-2026-10-28`, with input hashes, original queue, pre-import data/database backup and the separate catalogue audit receipt.

All **11 manual checks are now recorded as passed**: 11/51 = **21.6%**, covering the three retained retailers and lower/middle/upper catalogue price coverage. No additional checks are requested for this unchanged catalogue. The full checklist retains all original findings; the additional-check queue is empty. Hardware, offers, candidate states and participant templates are unchanged by this metadata import. Structural validation passes.

The catalogue remains at 51 verified configurations and 60 verified dated offers. The three unresolved Gold One identities remain excluded. Availability wording such as Check Stock is retained as observed and is not converted to in-stock eligibility. Remaining work is the protocol/availability/offer-age and instrument decisions, consent/study approvals and immutable survey freeze. See [current readiness](pilot_2026-10-28/READINESS.md) and [current project guide](../README.md).
