# Returned review audit — 28 October 2026

Ro supplied forty portable reviews plus three store-message screenshots and authorized the evidence audit and supported approvals. The original JSON is retained unchanged under `staging/review-return-2026-10-28`, together with the received images, SHA-256 input manifest, pre-import CSV/database backup, audit plan and transaction receipts. Local staging remains ignored by Git.

## Applied outcome

| Scope | Approved observations | Still Needs Review |
|---|---:|---:|
| Returned forty | 22 | 18 |
| Earlier twenty-three | 17 | 6 |
| Whole queue | 39 | 24 |

These observations support **34 verified configuration records and 39 verified dated offers**. Five original configuration records remain draft/quarantined, giving 39 total hardware rows and 47 total offers. Forty reviewed observations are not forty distinct verified configurations. Six additional verified distinct configurations are needed for the working pilot target.

## Condition evidence

- **PTC:** explicit confirmation that its website laptops are brand new. Applied within that website-listing scope.
- **Gold One:** affirmative response to the question about new condition for website laptops. Applied within that scope. The screenshot's relative reply date is retained without inventing an absolute date.
- **Beckie:** the Khmer replies mention both new and second-hand units and then new units for all models. This does not identify whether the exact advertised prices/SKUs refer to new units. Ro confirmed that no further exact-offer evidence is available. All 21 Beckie observations, representing 18 listing URLs, remain Needs Review.

The JPG bytes are retained under `staging/evidence/store_messages_2026-10-28/`. Every audited decision links a separate source row to the corresponding screenshot; each approved offer's `condition_evidence_id` points to its retained condition document. Source rows retain the JPEG path/hash and scope. Retailer homepage URLs provide website context, not fabricated private-message URLs. Screenshot received date is 2026-10-28; product observation dates remain 2026-10-15 or 2026-10-19. No current stock guarantee is asserted.

## Corrections and unresolved identity

- Restored explicit OS lines omitted by extraction and trimmed an OS field that included weight/colour/warranty text. The Dell Inspiron 3530 title says Ubuntu while its detailed specification says DOS: delivered OS was left blank. An OS-dependent hard constraint must fail until clarified.
- The Gold One parser had retained only the first graphics line on two AMD/NVIDIA gaming laptops. Both listed GPUs are now recorded, with the documented NVIDIA VRAM. On the Intel Predator, an incompatible AMD integrated-graphics line was discarded; only the NVIDIA GPU stated in both title and specification was retained, with the integrated GPU unspecified.
- The Beckie Galaxy Book5 Pro card pairs Ultra 7 256V with Iris Plus G7. Its GPU was left unknown pending exact-offer clarification. [Samsung's primary Book5 Pro specification](https://www.samsung.com/hk/business/computers/galaxy-book/galaxy-book5-pro-14-inch-ultra-7-16gb-1tb-np940xha-kg2hk/) identifies Arc 140V for that processor; a different regional SKU was not copied into the delivered record.
- PCIe interface wording alone was not treated as explicit confirmation of storage medium on incomplete Beckie cards. Raw capacity typos such as 512 B remain in original evidence; 512 GB in the same listing title can identify capacity without proving medium. Unknown fields remain blank.
- Ryzen 5 40 was retained: [ASUS's primary product page](https://in.store.asus.com/asus-vivobook-go-15-e1504fa-bq2112ws-amd-ryzen-student-laptop.html) confirms the processor designation. That corroborates the name, not all specifications of a different regional SKU. N355's incorrect i3 branding was corrected to Core 3 using [Intel's primary N-series datasheet](https://edc.intel.com/content/www/us/en/design/products/platforms/processor-and-core-i3-n-series-datasheet-volume-1-of-2/002/).
- The previously supplied [Acer NX.JK7AA.002 manufacturer page](https://www.acer.com/us-en/laptops/aspire/aspire-14-ai-intel/pdp/NX.JK7AA.002) was checked and matches the cited CPU, RAM, capacity and display. It was not used to infer extra delivered options on other models.

Exactly three Gold One listings are held as potential cross-retailer duplicates, rather than being counted as additional configurations:

| Gold One family | Overlapping PTC listing | Needed |
|---|---|---|
| Aspire Lite AL14-32P, N355 / 8 GB / 512 GB / 14-inch WUXGA | AL14-32P-30ZL | Exact part and delivered RAM/display identity |
| Aspire Lite AL15-54P, Ultra 5 115U / 16 GB / 512 GB / 15.6-inch FHD | AL15-54P-58BE | Exact part and delivered RAM/display identity |
| Aspire Lite AL15, N4500 / 8 GB / 512 GB / 15.6-inch FHD | AL15-32P-C5CE | Exact part and delivered display identity |

Different prices, shop codes or marketing titles do not prove a distinct configuration. No uncertain merge, invented hardware variant, or eligibility-rule relaxation was used. Original draft promotion for LAP0001 and LAP0002 is explicit and audited; historical offers and source records remain unchanged.

## Pilot preparation started

[Readiness packet](pilot_2026-10-28/READINESS.md), [questionnaire draft](../docs/PILOT_QUESTIONNAIRE_DRAFT.md) and [protocol/decision draft](../docs/PILOT_PROTOCOL_DRAFT.md) are prepared. An eight-configuration second-check queue covers the two retained retailers and lower/middle/upper catalogue price coverage. Those descriptive price thirds are not participant budget bands. Zero second human checks are marked passed: seven are required at the present 34 records and at least eight at forty.

Availability/offer-age rules, task/OS vocabulary, active preferences with unknown targets, instrument/consent approval and study approvals remain open. There is no survey freeze, recruitment, assignment generation or model training. Student, rating and assignment files remain empty and byte-identical. The AI desk audit was not counted as a second manual human check.

## Validation and recovery

All 51 collection/review tests and nine validator integrity checks pass. Structural validation passes with no errors. Meaningful warnings remain for the incomplete forty-configuration catalogue and later manual/protocol gates. Original review receipts, old offer/source/issue rows, all 63 extraction hashes and the absence of an unfinished transaction were checked. Tests that previously assumed zero real approvals or next ID LAP0008 now compare against the actual baseline.

[Full decision log](REVIEW_DECISIONS_2026-10-28.csv) · [Unresolved observations](UNRESOLVED_REVIEWS_2026-10-28.csv) · [Validation report](validation_report.json).

## Returned forty — per-record result

| Candidate | Product | Result | Configuration / offer |
|---|---|---|
| CANcfecf41848e2114517700e93 | Asus ExpertBook B1 B1402CVA-EB0466 ( i5 1335U / 8GB / SSD 512GB PCIE / 14"FHD ) | approved | LAP0021 / OFF0026 |
| CANe3b655ab2ef30885bdd2e2b4 | Asus ExpertBook B1 B1403CVA-S64967 ( i5 13420H / 8GB / SSD 512GB PCIE / 14"FHD ) | approved | LAP0002 / OFF0027 |
| CAN143e42979019f983c5d88852 | Asus ExpertBook B1 B1503CVA ( Core™ 5 120U / 8GB / SSD 512GB PCIE / 15.6"FHD ) | approved | LAP0022 / OFF0028 |
| CAN691d1b425d5cd1038c6bbac7 | Asus ExpertBook B1 B1503CVA ( Core™ 7 150U / 16GB / SSD 512GB PCIE / 15.6"FHD ) | approved | LAP0023 / OFF0029 |
| CAN66a6a8454d842f37820daf6a | ASUS Vivobook S14 M3407KA-SF025W AMD AI R5-330-16G (ON BD)-1TB G4-14"OLED WUXGA-W11H-MS-BAG-Gray-2Y | approved | LAP0024 / OFF0030 |
| CAN2bdb31ec1ffb421446ae545d | Acer Aspire Lite AL15-54P-58BE-Core Ultra 5-115U-16GB-512G-15.6-NoODD-UMA-HD Cam-Light Silver-2Y | approved | LAP0025 / OFF0031 |
| CAN4f80ffa6203a19caa3f5f5d2 | MSI Modern 15 F1MG-1073KH Core 5 processor 120U-8GB 512GB-UMA-15.6"FHD-Win11H-BAG-Urban Silver-2Y | approved | LAP0026 / OFF0032 |
| CAN3a0d97598cbbe681c1ec46c7 | Lenovo ThinkPad E16 Gen3 Black Core 7 240H-16GB-512GB SSD-16" WUXGA-UMA-DOS-BL+FP-WLAN-1Y | approved | LAP0027 / OFF0033 |
| CAN8d8d71f2516a090a20c54e59 | Lenovo ThinkPad T14 Gen6 Ultra5 236V vPro 16GB 1TB SSD M.2 14" WUXGA DOS 3Y | approved | LAP0028 / OFF0034 |
| CAN76972a81a243a2d3404c3e5a | ASUS Vivobook Go15 E1504FA-BQ4298W-AMD Ryzen 5 40-16G OB-512G-UMA-15.6"FHD-W11H-BP-BLK-MixBlack-2Y | approved | LAP0029 / OFF0035 |
| CAN2a6b5d0e7f20b8f6dc6ce6fe | ASUS Vivobook S14 S3407CA-LY071W-Core 7 255H -16GB-1TB-14"WUXGA-W11-UMA-MatteGray-BL-MS+BAG-2Y | approved | LAP0012 / OFF0036 |
| CAN0f47265261a4c11e6b22d550 | Acer Aspire Lite AL14-32P-30ZL-C3-N355-8GB-512GB-14"-No ODD-DOS-UMA-FHD Camera-Silver-2Y | approved | LAP0013 / OFF0037 |
| CANd78a4ebfa71c2804f6083bc4 | MSI Modern 14 F13MG-638XKH Core i5-1334U-8GB-512GB-UHD-14"FHD-DOS-Sleeve Bag-Urban Silver-2Y | approved | LAP0030 / OFF0038 |
| CAN0df2e953135777cfd49f5aae | Lenovo ThinkPad E16 Gen3 Core 5 210H-16GB-512 SSD-16" WUXGA-UMA-WLAN-FP-DOS-1Y | approved | LAP0031 / OFF0039 |
| CAN4c6c3f51bdc8578a6bbb214c | ASUS Vivobook14 E1404TA-EB045W-Celeron N150-8G OB-256UFS-UMA-14"FHD IPs-W11H-BP-BLK-MixBlack-2Y TA | approved | LAP0032 / OFF0040 |
| CAN42c6a2aac075595ab59e0bd5 | Lenovo Ideapad slim 3 15AMN8 AMD Ryzen™ 5 40-16GB-512GB SSD-UMA-15.6"FHD-Win11-Arctic Grey (2Y) | approved | LAP0033 / OFF0041 |
| CANad84bfb3d9612b1d6109d89b | ASUS Vivobook Go 15 E1504TA-BQ070W-Celeron N150-8G OB-256UFS-UMA-15"FHD-W11H-BP-BLK-MixBlack-2Y | approved | LAP0034 / OFF0042 |
| CANe7db639e88d9a76ad4a202ae | Acer Aspire Lite AL15-32P-C5CE-N4500-8GB-512GB-15.6"-No ODD-UHD Graphics-HD Camera-Silver2Y | approved | LAP0035 / OFF0043 |
| CAN3cb7f1314cb8bec4e3410a4d | Dell Inspiron 3530 Silver Core i3-1305U 8GB-512GB- UHD 15.6"FHD-Wifi 6-3Cell- Ubuntu- (1Y) | approved | LAP0036 / OFF0044 |
| CANf9772ccbda344c671a223c9b | ASUS Vivobook S16 S3607QA-PL017W GRAY- Snapdragon X X1 26 100-LPDDR5X 16G-1T-16" WQXGA-BP-Win11H-2Y | approved | LAP0037 / OFF0045 |
| CANc48a1aff85d1f548daf89969 | ASUS Vivobook 16 X1607QA-MB068W BLUE-Snapdragon X X126100-16G OB-512GB-16"WUXGA-W11H-BP-BLK-2Y | approved | LAP0038 / OFF0046 |
| CAN3e138e87fb6d82e844eb1411 | ASUS Vivobook Go 15 E1504FA-BQ5090W-AMD Ryzen 5 40-8GB OB-512G-UMA-15.6"FHD-W11H-BP-BLK-MixBlack-2Y | approved | LAP0039 / OFF0047 |
| CAN5edf927429ec270f481fa314 | Alienware 16X Aurora OLED (U9/16GB/1TB) RTX 5070 | needs_review |  /  |
| CANa20d3e0ce270855140011585 | Alienware 16 Aurora (U7 v2/32GB/1TB) RTX 5060 Blue | needs_review |  /  |
| CAN1a2c0ab65064ab9e579ff78c | ASUS Vivobook Go 15 E1504FA-BQ5090W Mixed Black | needs_review |  /  |
| CANebe2b7690e43ed00979a8958 | ASUS Vivobook 14 X1404VA-EB2275W Cool Silver | needs_review |  /  |
| CANe161976298c6bbafdb2289b1 | ASUS VIVOBOOK Go 14 E1404FA-EB138W 1K-MIXED BLACK | needs_review |  /  |
| CAN496e925c4b58229e8e0b24ea | ASUS Vivobook Go 15 E1504TA-BQ177W COOL SILVER | needs_review |  /  |
| CAN926289a3f147af9d9a5b6bab | ASUS Vivobook Go 14 E1404TA-EB078W COOL SILVER | needs_review |  /  |
| CAN7ef32928224f7230206fe801 | Samsung Galaxy Book6 Pro Copilot+ PC 14" (U7/16GB/512GB) | needs_review |  /  |
| CANe3cfed3264a5d86d4dbd0da6 | Samsung Galaxy Book6 Copilot+ PC 16" (U7/16GB/512GB) | needs_review |  /  |
| CANc456297b14a57dc24e2f1661 | Samsung Galaxy Book5 Pro 360 Copilot+ PC Business Laptop | needs_review |  /  |
| CANa8a6d69c881e0d3ecbbd6700 | Samsung Galaxy Book5 Pro Copilot+ PC 14" (U7/16GB/512GB) | needs_review |  /  |
| CANec730a2ade4a40b48972b375 | MSI Cyborg15 B13WFKG-620KH​ Translucent Black | needs_review |  /  |
| CAN130fcd8ac1ac51549f947fbf | MSI Cyborg 15 B13WEKG-621KHNN Translucent Black | needs_review |  /  |
| CAN7671181fb9bccb1bd5ee8d13 | MSI Cyborg A15 AI B2HWGKG-207XKH | needs_review |  /  |
| CAN78cfbbfd4dde07c289301ad5 | MSI Katana 15 HX B14WFK-819XKH | needs_review |  /  |
| CAN26977fe5543e3f09a57d60de | MSI Cyborg 15 Max C13WF-035KH | needs_review |  /  |
| CAN26dcaf8360941f2bf72aae7f | MSI Cyborg 15 Black Edition A13VE-2442KH-Black | needs_review |  /  |
| CAN6fa684b2e22c60c6996044a7 | MSI ​Cyborg15 A13VEK-2252KH Translucent Black | needs_review |  /  |

## Later clarification — current status

Ro subsequently clarified in this chat that all reviewed Beckie listings belong to the website's new-laptop category, with second-hand stock in a separate category. That scoped human statement is retained verbatim and hashed at `staging/evidence/store_messages_2026-10-28/beckie_category_clarification.json`, alongside the original store screenshot. All 21 reviewed Beckie observations now have condition new and saved condition confirmations. This supersedes the earlier condition hold above; earlier review events and this report's original outcome remain historical.

Ten more complete observations were approved. Current totals are **44 verified configurations, 49 verified dated offers, and 14 observations awaiting hardware/identity checks** (11 Beckie and 3 Gold One). The working forty-configuration count is reached. The Samsung Book5 Pro 360 and MSI Katana matching drafts were explicitly promoted after equivalent display wording was normalized; exact pixel dimensions absent from those listings remain unknown. No variant was invented.

The current manual second-check queue has **nine** configurations across all three retained retailers. No second check is marked passed. See [the collection workflow](../docs/COLLECTION_WORKFLOW.md) for the review desk, fresh fourteen-item portable export, second-check CSV, and protocol drafts. Current decision/unresolved CSVs reflect the latest saved events.

Final validation: 54 collection/review tests and 9 validator integrity checks pass; structural validation has no errors. Bounded Windows sharing-lock retries preserve atomic replacement, the original target on persistent denial, and transaction-journal recovery.

## Fourteen-item return and manual checklist — current status

The subsequent returned fourteen-item file has been reconciled and all nine actual manual checks incorporated. Eleven approvals accepted, three identities retained. Current catalogue: 51 verified configurations, 60 verified dated offers. Nine manual checks passed; two additional checks are needed for twenty percent of the expanded catalogue. See the [latest returned-file audit](RETURNED_REVIEWS_AND_RECHECKS_2026-10-28.md) and [readiness packet](pilot_2026-10-28/READINESS.md). Earlier totals above are historical.

## Two additional checks received — manual coverage complete

Both returned rows (LAP0051/OFF0065 and LAP0007/OFF0067) match their original configuration, offer, source evidence and queue fields. Ro marked both passed with actual timestamp 2026-10-28T22:44:00+07:00, before import. The submitted findings and original file are retained unchanged under `staging/two-additional-rechecks-2026-10-28`, with input hashes, original queue, pre-import data/database backup and the separate catalogue audit receipt.

All **11 manual checks are now recorded as passed**: 11/51 = **21.6%**, covering the three retained retailers and lower/middle/upper catalogue price coverage. No additional checks are requested for this unchanged catalogue. The full checklist retains all original findings; the additional-check queue is empty. Hardware, offers, candidate states and participant templates are unchanged by this metadata import. Structural validation passes.

The catalogue remains at 51 verified configurations and 60 verified dated offers. The three unresolved Gold One identities remain excluded. Availability wording such as Check Stock is retained as observed and is not converted to in-stock eligibility. Remaining work is the protocol/availability/offer-age and instrument decisions, consent/study approvals and immutable survey freeze. See [current readiness](pilot_2026-10-28/READINESS.md) and [current project guide](../README.md).
