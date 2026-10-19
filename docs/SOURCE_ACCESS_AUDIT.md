# Retailer access audit

Inspected 15 October 2026 UTC using identified public HTTP GET requests before the live collector smoke run. This records the pages inspected, not affirmative legal permission or a permanent access guarantee. No authentication, CAPTCHA solving, hidden APIs, checkout or access-control bypass was used. Recheck restrictions on each run and review any new applicable terms before continuing collection.

| Source | Robots result | Public terms or policy page inspected | Bounded retrieval decision |
|---|---|---|---|
| Gold One Computer | 200; wildcard disallows search, tag, manufacturer, sort/order, limit and filter queries; ordinary product/category paths allowed | [Footer-linked About Us](https://www.goldonecomputer.com/index.php?route=information/information&information_id=4); [robots](https://www.goldonecomputer.com/robots.txt) | Public category/product HTML with preserved query checks. No separate access-terms link was discovered in the inspected footer; no automation prohibition found on the inspected pages. |
| PTC Computer | 404 at robots.txt | [Terms and Conditions](https://ptc-computer.com.kh/terms); [robots endpoint](https://ptc-computer.com.kh/robots.txt) | Public category/product HTML only. The inspected terms concern online purchases, returns, warranty and site-information limitations; no automation prohibition found. A missing robots file does not grant permission. |
| Beckie Khmer | 200; empty Disallow | [Footer-linked About Us and warranty terms](https://www.beckie-khmer.com/about-us?u); [robots](https://www.beckie-khmer.com/robots.txt) | Public catalogue cards, with exact card locators and individual product links for human checking. No automation prohibition found on the inspected pages; no separate access-terms link was discovered. |

These decisions allow the small identified public-HTML smoke test under the inspected rules. They do not authorize copying protected data, bypassing later restrictions or publishing full retailer pages. Raw fetched pages and the SQLite queue are ignored by Git. The committed parser fixtures are handwritten test examples, not scraped catalogues.

The implementation checks the configured public policy pages before product requests, records response/text hashes and stops on known restriction/challenge signals or inaccessible policy pages. It cannot discover or interpret every future policy change automatically. Add newly discovered terms URLs to the source configuration, review them, and set a source to `manual_urls` whenever automation is prohibited or permission is unresolved. The manual URL importer makes zero network requests; an authorized-export importer records the permission reference.

## Observed limitations

Beckie detail routes were sampled during initial inspection and could return catalogue content not uniquely identifying the clicked product. The collector therefore extracts the actual public listing card with its shop SKU and flags catalogue-only evidence; it does not borrow an unrelated detail page's specs. Humans can open both the individual link and the listing evidence. A Coming soon listing/detail message is not silently converted into a live-stock claim.

PTC mixes product prices with finance terms and can omit manufacturer part numbers. Only a scoped price block is parsed. Shop inventory IDs remain separate. Gold One Product Code can be a model family; Acer/HP/Lenovo title families are conservatively left without an asserted manufacturer SKU until supported evidence is entered.

All candidates begin pending. No product or offer becomes verified because robots allowed a request or the collector successfully parsed it. Full new-condition evidence and the existing canonical completeness rules still require human review. Retain missing data and discrepancies and respect the proposal's separate second manual verification pass.
