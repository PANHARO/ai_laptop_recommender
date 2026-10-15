"""Map explicit human reviews to the unmodified canonical CSV schema."""
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile

from scripts.validate_data import check_type, validate
from .models import (CORE_FIELDS, EDIT_FIELDS, HARDWARE_FIELDS, NUMERIC_FIELDS,
                     allowed_url, canonical_url, classify_duplicate, clean,
                     decimal_string, digest, now)


class ReviewError(ValueError):
    pass


def allocate(rows, key, prefix):
    values = [int(r[key][len(prefix):]) for r in rows if re.fullmatch(prefix + r'\d+', r[key])]
    return prefix + str(max(values or [0]) + 1).zfill(4)


def assert_complete(fields, confirmations, source):
    placeholders = {'','unknown','n/a','na','not sure','tbd','none','?','-','not provided','not listed'}
    missing = [k for k in CORE_FIELDS if clean(fields.get(k)).casefold() in placeholders]
    missing += [k for k in ('full_name', 'price_text', 'manufacturer_sku_evidence', 'specification_evidence', 'condition_evidence', 'condition_evidence_url') if not clean(fields.get(k))]
    if missing:
        raise ReviewError('Complete these fields with source evidence: ' + ', '.join(missing))
    if fields.get('condition') != 'new' or fields.get('purchase_type') != 'outright' or fields.get('currency') != 'USD':
        raise ReviewError('Approval requires verified new condition, an outright purchase price and USD currency.')
    if not all(confirmations.get(k) is True for k in ('new_condition', 'specifications', 'manufacturer_sku', 'price')):
        raise ReviewError('Explicitly confirm new condition, delivered specifications, manufacturer SKU and full purchase price.')
    if re.match(r'(?:BECKIE\d+|LL[A-Z]-|LU[A-Z]+-)', fields['manufacturer_sku'], re.I):
        raise ReviewError('The manufacturer SKU appears to be a shop inventory ID. Keep it in shop SKU instead.')
    allowed_url(fields['source_url'], source)
    canonical_url(fields['condition_evidence_url'])
    schema_types = {'price_usd':'number:positive', 'ram_gb':'number:positive', 'storage_gb':'number:positive', 'screen_inches':'number:positive'}
    for k, typ in schema_types.items():
        if not check_type(fields.get(k, ''), typ):
            raise ReviewError('Invalid ' + k + ': use a finite positive value in the documented unit.')


def validate_proposal_tables(root, tables):
    import csv
    with tempfile.TemporaryDirectory(prefix='laptop-proposed-') as tmp:
        target = Path(tmp)
        shutil.copytree(root/'config', target/'config')
        shutil.copytree(root/'data', target/'data')
        schema = json.loads((root/'config/schema.json').read_text())
        for name, rows in tables.items():
            with (target/'data'/f'{name}.csv').open('w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[x['name'] for x in schema[name]['fields']])
                writer.writeheader(); writer.writerows(rows)
        errors = validate(target)['errors']
        if errors:
            raise ReviewError('Canonical validation refused the write: ' + '; '.join(errors))


class Reviewer:
    def __init__(self, store):
        self.store, self.root = store, store.root
        self.config = json.loads((self.root/'config/collection_sources.json').read_text())

    def preview(self, candidate, edits=None):
        return classify_duplicate(edits or candidate['fields'], self.store.canonical()['laptops'])

    def review(self, candidate_id, action, edits, reviewer, notes='', confirmations=None,
               expected_revision=0, request_id=None):
        if action not in ('approve', 'reject', 'needs_review', 'skip'):
            raise ReviewError('Unknown review action.')
        if not clean(reviewer):
            raise ReviewError('Enter a reviewer code/name before saving a decision.')
        confirmations = confirmations or {}
        key = request_id or digest(dict(candidate_id=candidate_id, revision=expected_revision,
            action=action, edits=edits, reviewer=reviewer, notes=notes, confirmations=confirmations))
        with self.store.lock:
            self.store.recover()
            old_event = self.store.receipt(key)
            if old_event:
                if old_event['candidate_id'] != candidate_id or old_event['action'] != action:
                    raise ReviewError('Idempotency key belongs to a different review.')
                return old_event
            candidate = self.store.get(candidate_id)
            if candidate['revision'] != expected_revision:
                raise ReviewError('This candidate changed in another session. Refresh before reviewing.')
            if candidate['state'] in ('approved', 'rejected'):
                raise ReviewError('This is a completed review. Collect a new observation rather than changing history.')
            fields = {k: clean(candidate['fields'].get(k)) for k in EDIT_FIELDS}
            fields.update({k: clean(v) for k, v in edits.items() if k in EDIT_FIELDS})
            for k in NUMERIC_FIELDS:
                if fields[k] and not decimal_string(fields[k]):
                    raise ReviewError('Invalid numeric value: ' + k)
                fields[k] = decimal_string(fields[k])
            fields['retailer'] = self.config['sources'][candidate['site']]['retailer']
            fields['source_url'] = allowed_url(fields['source_url'], self.config['sources'][candidate['site']])
            tables = self.store.canonical()
            duplicate = classify_duplicate(fields, tables['laptops'])
            at = now()
            state = {'approve':'approved', 'reject':'rejected', 'needs_review':'needs_review', 'skip':'skipped'}[action]
            event = dict(event_id=key, candidate_id=candidate_id, action=action,
                state=state, reviewed_by=clean(reviewer), reviewed_at=at,
                notes=clean(notes), fields=fields, confirmations=confirmations,
                before_revision=expected_revision, canonical_result={}, notices=[])
            if action == 'approve':
                assert_complete(fields, confirmations, self.config['sources'][candidate['site']])
                if candidate.get('evidence_file'):
                    evidence_path=(self.root/candidate['evidence_file']).resolve()
                    permitted=(self.root/'staging/evidence').resolve()
                    if not evidence_path.is_relative_to(permitted) or not evidence_path.is_file() or hashlib.sha256(evidence_path.read_bytes()).hexdigest()!=candidate.get('evidence_sha256'):
                        raise ReviewError('Saved extraction evidence is missing or changed. Recollect or import a fresh manual observation before approval.')
                variant = confirmations.get('documented_variant') is True and fields['variant_evidence'] and fields['resolution_notes']
                if duplicate['kind'] == 'conflict' and not variant:
                    state = event['state'] = 'needs_review'
                    event['notices'].append('Existing manufacturer SKU has conflicting or incomplete hardware. No laptop or offer was merged. Supply documented variant evidence, or resolve the conflicting record separately.')
                elif duplicate['kind'] == 'exact' and duplicate['matches'][0]['record_status'] != 'verified':
                    old = duplicate['matches'][0]
                    if confirmations.get('confirm_existing_draft') is not True or not fields['resolution_notes']:
                        raise ReviewError('A matching draft/quarantined configuration exists. Confirm that draft explicitly and record how its issues were resolved before promotion.')
                    import csv
                    for name in ('ratings', 'assignments'):
                        with (self.root/'data'/f'{name}.csv').open(newline='', encoding='utf-8-sig') as f:
                            if any(r['configuration_id'] == old['configuration_id'] for r in csv.DictReader(f)):
                                raise ReviewError('Existing configuration is referenced by research history; it cannot be promoted/edited here. Use a documented correction workflow.')
                elif duplicate['kind'] == 'missing_sku':
                    raise ReviewError('Manufacturer SKU is required for a verified configuration.')

            # Skip is a staging-only action. Rejection/needs-review add an evidence record and
            # issue but never a verified laptop/offer. All decisions remain in the audit database.
            if action != 'skip':
                eid = allocate(tables['source_checks'], 'evidence_id', 'SRC')
                checked = state == 'approved'
                evidence = dict(evidence_id=eid, source_url=fields['source_url'],
                    page_locator=fields['manufacturer_sku'] or fields['retailer_sku'] or fields['full_name'] or candidate_id,
                    retrieved_date=candidate['observed_date'],
                    access_mode='retrieved_catalogue' if candidate.get('access_mode') == 'retrieved_catalogue' else 'manual_page',
                    facts_observed=json.dumps({k: fields[k] for k in HARDWARE_FIELDS + ('price_usd','price_text','condition','availability_text','delivered_os') if fields.get(k)}, ensure_ascii=False) or 'No verified product facts.',
                    source_check_status='checked' if checked else 'conflict' if state == 'needs_review' else 'pending',
                    checked_by=clean(reviewer), checked_at=at if checked else '',
                    second_check_status='pending',
                    evidence_file=candidate.get('evidence_file', ''),
                    notes=f"Candidate {candidate_id}; review event {key}. Original retrieved URL: {candidate['original_fields']['source_url']}. {notes}. Specification evidence: {fields['specification_evidence']}. New-condition evidence: {fields['condition_evidence']}")
                tables['source_checks'].append(evidence)
                event['canonical_result']['evidence_id'] = eid
                if state == 'approved':
                    condition_eid = eid
                    if fields['condition_evidence_url'] != fields['source_url']:
                        condition_eid = allocate(tables['source_checks'], 'evidence_id', 'SRC')
                        tables['source_checks'].append(dict(evidence, evidence_id=condition_eid,
                            source_url=fields['condition_evidence_url'], facts_observed=fields['condition_evidence'], evidence_file=''))
                    if duplicate['kind'] == 'exact':
                        laptop = duplicate['matches'][0]
                        lid = laptop['configuration_id']
                        if laptop['record_status'] != 'verified':
                            # No nonempty hardware value is overwritten. The previous evidence rows
                            # remain immutable; current verification gets its own evidence reference.
                            previous_evidence = laptop['evidence_ids']
                            for k in HARDWARE_FIELDS:
                                if not laptop.get(k) and fields.get(k):
                                    laptop[k] = fields[k]
                            laptop.update(record_status='verified', evidence_ids=eid,
                                review_notes=laptop['review_notes'] + f' Explicit draft promotion {at}; prior evidence {previous_evidence} retained in source log. {fields["resolution_notes"]}')
                        else:
                            event['notices'].append('Existing verified hardware retained without changes; a new offer observation was added.')
                    else:
                        lid = allocate(tables['laptops'], 'configuration_id', 'LAP')
                        laptop = {k:fields[k] for k in HARDWARE_FIELDS}
                        laptop.update(configuration_id=lid, evidence_ids=eid, record_status='verified', review_notes=clean(notes) + (' Documented variant: ' + fields['variant_evidence'] if variant else ''))
                        tables['laptops'].append(laptop)
                    oid = allocate(tables['offers'], 'offer_id', 'OFF')
                    tables['offers'].append(dict(offer_id=oid, configuration_id=lid, retailer=fields['retailer'],
                        retailer_sku=fields['retailer_sku'], price_usd=fields['price_usd'], currency='USD', price_text=fields['price_text'],
                        source_url=fields['source_url'], observed_date=candidate['observed_date'], availability_text=fields['availability_text'],
                        condition='new', condition_evidence_id=condition_eid, purchase_type='outright', delivered_os=fields['delivered_os'],
                        snapshot_version='collection_' + candidate['observed_date'] + '_' + candidate_id,
                        evidence_id=eid, offer_status='verified', review_notes=clean(notes) + ' Human review ' + at))
                    event['canonical_result'].update(configuration_id=lid, offer_id=oid)
                iid = allocate(tables['issues'], 'issue_id', 'ISS')
                tables['issues'].append(dict(issue_id=iid, entity_type='offer' if state == 'approved' else 'source',
                    entity_id=event['canonical_result'].get('offer_id', eid), source_url=fields['source_url'],
                    logged_date=at[:10], issue_type='human_' + action,
                    decision='resolved' if state == 'approved' else 'excluded' if state == 'rejected' else 'quarantined',
                    details=f'Candidate {candidate_id}; {action}; {clean(notes)}; ' + '; '.join(event['notices']),
                    resolution=f'Explicit human approval by {clean(reviewer)} at {at}. {fields["resolution_notes"]}' if state == 'approved' else ''))
            if action != 'skip':
                validate_proposal_tables(self.root, tables)
            self.store.commit(event, tables if action != 'skip' else None)
            return event
