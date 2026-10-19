import csv
import json
from pathlib import Path
from .access import AccessBlocked, PublicClient, RetrievalError
from .collectors import COLLECTORS
from .models import allowed_url, digest, make_candidate, now
from .store import Store, atomic_bytes, json_bytes

ROOT = Path(__file__).resolve().parents[1]


def settings(root):
    return json.loads((root/'config/collection_sources.json').read_text())


def manual_url(store, site, url, title=''):
    config = settings(store.root)
    source = config['sources'][site]
    allowed_url(url, source)
    candidate = make_candidate(site, source['retailer'], url, {'full_name':title},
        origin='manual_url', flags=['manual_url_only_no_network_request','human_entry_required'],
        access_mode='manual_page', evidence_file='')
    return candidate, store.add(candidate)


def collect(root, sites, limit=3, max_pages=None):
    if not 1 <= limit <= 500:
        raise ValueError('Limit must be 1 to 500 observations per site.')
    store, config = Store(root), settings(root)
    run_id = now().replace(':','').replace('+','') + '_' + digest(sites)[:6]
    report = dict(run_id=run_id, started_at=now(), per_site={})
    for site in sites:
        source = config['sources'][site]
        stats = dict(status='not_started', discovered=0, extracted=0, staged_new=0,
                     already_staged=0, failed=[], policy_pages=[], retrieval='public_html')
        report['per_site'][site] = stats
        client = PublicClient(source, config, store.staging/'runs'/run_id/(site+'.jsonl'))
        collector = COLLECTORS[site]()
        try:
            stats['policy_pages'] = client.check_policy()
            queue, visited, products = source['listing_urls'][:], set(), set()
            pages = 0
            while queue and pages < (max_pages or config['max_pages']) and stats['extracted'] < limit:
                url = queue.pop(0)
                if url in visited:
                    continue
                visited.add(url); pages += 1
                listing = client.get(url)
                links = collector.links(listing['text'], listing['url'])
                if not links:
                    stats['failed'].append(dict(url=url, reason='No laptop cards found; inspect source HTML/selectors.'))
                queue.extend(x for x in collector.next_pages(listing['text'], listing['url']) if x not in visited)
                for entry in links:
                    if stats['extracted'] >= limit:
                        break
                    if entry['url'] in products:
                        continue
                    products.add(entry['url']); stats['discovered'] += 1
                    try:
                        allowed_url(entry['url'], source)
                        if collector.detail_required:
                            response = client.get(entry['url'])
                            parsed = collector.extract(response['text'], response['url'])
                            evidence_url, access_mode = response['url'], 'retrieved_product_page'
                        else:
                            # No hidden API or detail-route probing. The labelled public card is
                            # evidence from the allowed listing, not a verified detail-page fetch.
                            response, parsed = listing, entry['extracted']
                            evidence_url, access_mode = listing['url'], 'retrieved_catalogue'
                        relative = 'staging/evidence/' + response['sha256'] + '.html'
                        atomic_bytes(root/relative, response.get('raw', response['text'].encode('utf-8')))
                        candidate = make_candidate(site, source['retailer'], entry['url'], parsed['fields'],
                            flags=parsed['flags'], evidence_file=relative,
                            evidence_url=evidence_url, evidence_sha256=response['sha256'],
                            access_mode=access_mode, listing_url=listing['url'], run_id=run_id)
                        stats['extracted'] += 1
                        if store.add(candidate):
                            stats['staged_new'] += 1
                        else:
                            stats['already_staged'] += 1
                    except AccessBlocked as exc:
                        client.log(event='blocked_product', url=entry['url'], reason=str(exc))
                        if client.blocked:
                            raise
                        stats['failed'].append(dict(url=entry['url'], reason=str(exc)))
                    except (RetrievalError, ValueError) as exc:
                        client.log(event='extraction_failed', url=entry['url'], reason=str(exc))
                        stats['failed'].append(dict(url=entry['url'], reason=str(exc)))
            stats['status'] = 'completed' if stats['extracted'] else 'no_candidates'
        except AccessBlocked as exc:
            stats.update(status='blocked', reason=str(exc), manual_import_available=True)
        except (RetrievalError, ValueError) as exc:
            stats.update(status='failed', reason=str(exc), manual_import_available=True)
        report['finished_at'] = now()
        atomic_bytes(store.staging/'runs'/run_id/'summary.json', json_bytes(report))
    return report


def seed_existing(root):
    """Copy canonical observations into a review queue; do not edit canonical rows."""
    store, config = Store(root), settings(root)
    tables = store.canonical()
    laptops = {r['configuration_id']:r for r in tables['laptops']}
    evidence = {r['evidence_id']:r for r in tables['source_checks']}
    names = {value['retailer']:key for key,value in config['sources'].items()}
    added, represented = 0, set()
    for offer in tables['offers']:
        if offer['retailer'] not in names:
            continue
        laptop = laptops[offer['configuration_id']]
        fields = dict(laptop, **{k:v for k,v in offer.items() if k not in laptop})
        fields['full_name'] = ' '.join([laptop['brand'],laptop['model'],laptop['manufacturer_sku']])
        fields['manufacturer_sku_evidence'] = 'Existing unverified CSV; confirm actual manufacturer part number at the source.'
        fields['specification_evidence'] = evidence.get(offer['evidence_id'],{}).get('facts_observed','')
        candidate = make_candidate(names[offer['retailer']], offer['retailer'], offer['source_url'], fields,
            observed_at=offer['observed_date'], origin='existing_canonical',
            flags=['historical_observation_requires_recheck',offer['review_notes'],laptop['review_notes']],
            evidence_file='', access_mode='manual_page', existing_offer_id=offer['offer_id'])
        added += store.add(candidate)
        represented.add(offer['evidence_id'])
    # Keep source-only leads reviewable too, including the old excluded zero-price lead.
    # Their locator is a label, never an asserted manufacturer part number or offer.
    for reference in tables['source_checks']:
        if reference['evidence_id'] in represented:
            continue
        for site, source in config['sources'].items():
            try:
                allowed_url(reference['source_url'], source)
            except ValueError:
                continue
            candidate = make_candidate(site, source['retailer'], reference['source_url'],
                {'full_name':reference['page_locator'], 'specification_evidence':reference['facts_observed']},
                observed_at=reference['retrieved_date'], origin='existing_canonical',
                existing_evidence_id=reference['evidence_id'],
                flags=['historical_source_only_no_offer', 'historical_observation_requires_recheck', reference['notes']],
                evidence_file='', access_mode='manual_page')
            added += store.add(candidate)
            break
    return added


def import_export(root, site, path, authorization):
    if not authorization.strip():
        raise ValueError('Record who authorized this export and the permission/reference; do not download restricted pages to manufacture an export.')
    store, config = Store(root), settings(root)
    records = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(records, list):
        raise ValueError('Authorized export must be a JSON array of product objects.')
    # Validate the complete batch before inserting anything.
    candidates = []
    for row in records:
        allowed_url(row['source_url'], config['sources'][site])
        if 'observed_date' not in row:
            raise ValueError('Every authorized export row needs its actual observed_date.')
        from datetime import date
        if date.fromisoformat(row['observed_date']).isoformat() != row['observed_date']:
            raise ValueError('observed_date must use YYYY-MM-DD.')
        candidate = make_candidate(site, config['sources'][site]['retailer'], row['source_url'], row,
            observed_at=row['observed_date'], origin='authorized_export',
            authorization=authorization, flags=['authorized_export_requires_human_review'],
            evidence_file='', access_mode='manual_page')
        candidates.append(candidate)
    return sum(store.add(c) for c in candidates)
