# Review audit: 19 October 2026

The nine saved human reviews contain eight Needs Review decisions and one Skip. No observation was approved or rejected. Existing decisions and canonical hardware/offer records were preserved during this audit.

The skipped observation is Gold One's Acer Extensa 15 EX215-35 (Core 3 N355 / 8 GB / 512 GB / 15.6-inch FHD), candidate `CAN8d2aa81a05984fae7b61a86e`. It remains available through **Find skipped** and the default queue.

The latest saved events contain hardware and price confirmations for eight of the nine observations, including the skipped Extensa. The Aspire 14 AI's latest saved event has all factual confirmations unchecked. All nine have condition `unknown` and no recorded new-condition evidence. Six have no manufacturer SKU; the other three still have their latest manufacturer-SKU confirmation unchecked. The Aspire 7 event checks the SKU confirmation despite leaving the actual field blank, which does not satisfy approval.

Beckie's ASUS Vivobook Go 15 E1504FA-BQ5090W also lacks storage medium and contains ambiguous source text: CPU `AMD Ryzen 5 40` and storage `512B PCIe`. Correct these only with evidence from the exact listing or documented retailer clarification. The Alienware 16X observation retains `Coming Soon`; this is not an in-stock claim.

Structural validation passes with seven existing canonical laptop rows, eight offers, zero verified configurations and zero verified offers. Passing this validator does not establish factual eligibility or complete the 40-configuration pilot goal.

The current rules require an exact manufacturer SKU and supported new condition. Warranty duration and placement outside a second-hand section are contextual evidence, not explicit condition confirmation. A retailer statement covering a clearly defined set of listings could establish condition for that set. Manufacturer SKU is an identity rule of this implementation, not an intrinsic requirement of recommendation algorithms. Making it optional needs an explicit replacement identity/deduplication policy and consistent changes to the schema, validator and reviewer; no such policy change was made in this audit.

The dashboard now keeps save receipts and approval errors in a fixed corner alert, includes skipped observations by default, provides a **Find skipped** shortcut, shows decisions in candidate labels, and restores saved factual confirmations and notes. All 38 automated tests pass, including skipped-item recovery and restoration of saved review facts. Browser rendering was not visually inspected.

Additional public-HTML observations are collected into staging for human review, with policy checks and source evidence retained under `staging/runs`. Fresh observations of previously reviewed listings retain separate dates and do not inherit old approvals. Collection counts are observations, not verified or necessarily distinct hardware configurations.

Completed run `2026-10-19T160139.2467660000_00e413` staged 54 fresh observations: 18 from each retailer, with no extraction failures. The queue now contains 63 observations (54 pending, eight Needs Review, one skipped), representing 55 distinct listing URLs. Hardware deduplication and eligibility verification are still required before counting configurations toward 40.
