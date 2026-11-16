"""Import genuine second-check metadata without changing offers or review states."""
import copy
import csv
from datetime import datetime, timezone
import hashlib
from pathlib import Path

from .mapping import allocate, validate_proposal_tables
from .models import digest, now


EDITABLE = {'second_check_status', 'second_checked_by', 'second_checked_at', 'findings'}


def read_rows(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def apply_rechecks(store, submitted, original_queue, audit_notes=None):
    rows, expected = read_rows(submitted), read_rows(original_queue)
    key = 'second-check-' + digest(dict(
        input_sha256=hashlib.sha256(Path(submitted).read_bytes()).hexdigest(),
        queue_sha256=hashlib.sha256(Path(original_queue).read_bytes()).hexdigest(), audit_notes=audit_notes or {}))
    with store.lock:
        store.recover()
        previous = store.audit_receipt(key)
        if previous:
            return previous
        baseline = {(r['configuration_id'], r['offer_id']): r for r in expected}
        if not rows or len(baseline) != len(expected) or len(rows) != len(expected):
            raise ValueError('Return exactly the original second-check queue rows.')
        tables = store.canonical()
        sources = {r['evidence_id']: r for r in tables['source_checks']}
        offers = {r['offer_id']: r for r in tables['offers']}
        laptops = {r['configuration_id']: r for r in tables['laptops']}
        seen = set()
        accepted = []
        at = now()
        for row in rows:
            identity = (row['configuration_id'], row['offer_id'])
            if identity not in baseline or identity in seen:
                raise ValueError('Unknown or repeated configuration/offer in checklist.')
            seen.add(identity)
            expected_row = baseline[identity]
            if set(row) != set(expected_row) or any(row[k] != v for k,v in expected_row.items() if k not in EDITABLE):
                raise ValueError('Checklist identity/source fields changed: ' + row['configuration_id'])
            status, reviewer, timestamp = (row[k].strip() for k in ('second_check_status','second_checked_by','second_checked_at'))
            if status not in ('passed','failed') or not reviewer or not row['findings'].strip():
                raise ValueError('Complete status, reviewer and factual findings for each check.')
            checked = datetime.fromisoformat(timestamp)
            if checked.tzinfo is None or checked.utcoffset() is None or checked > datetime.now(timezone.utc):
                raise ValueError('Record an actual check timestamp with timezone, not a future timestamp.')
            offer = offers.get(row['offer_id'])
            laptop = laptops.get(row['configuration_id'])
            if not offer or not laptop or offer['configuration_id'] != row['configuration_id']:
                raise ValueError('Checklist no longer identifies the same configuration and offer.')
            for name in ('evidence_id','condition_evidence_id','source_url','observed_date','price_usd','retailer'):
                if row[name] != offer[name]:
                    raise ValueError('Offer changed since the queue was prepared: ' + name)
            for eid in dict.fromkeys([row['evidence_id'], row['condition_evidence_id']]):
                evidence = sources[eid]
                if evidence['second_check_status'] not in (expected_row['second_check_status'],'pending','not_selected'):
                    raise ValueError('This source already has a different second check; preserve its history.')
                evidence.update(second_check_status=status, second_checked_by=reviewer, second_checked_at=timestamp)
                evidence['notes'] += '\nSecond manual check returned by ' + reviewer + ': ' + row['findings']
                extra = (audit_notes or {}).get(row['configuration_id'], '')
                if extra:
                    evidence['notes'] += '\nDesk audit of returned findings: ' + extra
            iid = allocate(tables['issues'],'issue_id','ISS')
            tables['issues'].append(dict(issue_id=iid, entity_type='source',entity_id=row['evidence_id'],
                source_url=row['source_url'],logged_date=checked.date().isoformat(),issue_type='manual_second_check',
                decision='resolved' if status=='passed' else 'quarantined',details=row['findings'],
                resolution=f'Actual manual second check by {reviewer} at {timestamp}; audit event {key}.'))
            accepted.append(copy.deepcopy(row))
        validate_proposal_tables(store.root, tables)
        event = dict(kind='catalogue_audit',event_id=key,action='manual_second_checks',reviewed_at=at,
            submitted_file=str(Path(submitted).resolve()), original_queue=str(Path(original_queue).resolve()),
            rows=accepted,audit_notes=audit_notes or {})
        store.commit(event,tables)
        return event
