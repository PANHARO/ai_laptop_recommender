#!/usr/bin/env python3
"""Validate the milestone CSV scaffold using Python's standard library.

This checks data integrity, not truth of retailer claims or approval of a study.
No files are changed unless --write-report is supplied.
"""
import argparse
import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def number(value):
    try:
        x = Decimal(value)
        return x if x.is_finite() else None
    except (InvalidOperation, TypeError, ValueError):
        return None


def check_type(value, kind):
    if kind.startswith('number:'):
        n = number(value)
        return n is not None and (n > 0 if kind.endswith('positive') else n >= 0)
    if kind.startswith('integer:'):
        _, lo, hi = kind.split(':')
        n = number(value)
        return n is not None and n == n.to_integral_value() and int(lo) <= n <= int(hi)
    if kind.startswith('enum:'):
        return value in kind[5:].split(',')
    if kind == 'boolean':
        return value in ('0', '1')
    if kind == 'date':
        try:
            return date.fromisoformat(value).isoformat() == value
        except ValueError:
            return False
    if kind == 'datetime':
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00')).utcoffset() is not None
        except ValueError:
            return False
    if kind == 'url':
        u = urlparse(value)
        return u.scheme in ('http', 'https') and bool(u.netloc)
    if kind == 'json_array':
        try:
            x = json.loads(value)
            return isinstance(x, list) and all(isinstance(v, str) for v in x)
        except (ValueError, TypeError):
            return False
    return True


def normalized(value):
    return ' '.join(value.casefold().split())


def validate(root):
    schema = json.loads((root / 'config/schema.json').read_text(encoding='utf-8'))
    errors, warnings, tables, by_id = [], [], {}, {}
    for name, spec in schema.items():
        path = root / 'data' / (name + '.csv')
        if not path.is_file():
            errors.append(f'Missing {path.name}')
            tables[name], by_id[name] = [], {}
            continue
        with path.open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            expected = [x['name'] for x in spec['fields']]
            if reader.fieldnames != expected:
                errors.append(f'{path.name}: headers differ from schema (including order)')
            rows = list(reader)
        tables[name], by_id[name] = rows, {}
        for line, row in enumerate(rows, 2):
            if None in row or any(v is None for v in row.values()):
                errors.append(f'{name}:{line}: malformed CSV row')
            for field in spec['fields']:
                v = row.get(field['name']) or ''
                if field['required'] and not v:
                    errors.append(f"{name}:{line}: missing {field['name']}")
                elif v and not check_type(v, field['type']):
                    errors.append(f"{name}:{line}: invalid {field['name']} ({field['type']})")
            key = row.get(spec['primary_key'], '')
            if key in by_id[name]:
                errors.append(f'{name}:{line}: duplicate primary key {key}')
            by_id[name][key] = row

    def ref(name, key, where):
        value = by_id[name].get(key)
        if value is None:
            errors.append(f'{where}: unknown {name} reference {key!r}')
        return value

    seen = {}
    for row in tables['laptops']:
        rid = row.get('configuration_id', '')
        fields = ['manufacturer_sku', 'cpu_model', 'gpu_model', 'ram_gb', 'storage_gb', 'storage_type', 'screen_inches', 'display_text']
        signature = tuple(normalized(row.get(k) or '') for k in fields)
        if all(signature):
            if signature in seen:
                errors.append(f'{rid}: duplicate configuration signature with {seen[signature]}')
            seen[signature] = rid
        for eid in (row.get('evidence_ids') or '').split(';'):
            ev = ref('source_checks', eid, rid)
            if row.get('record_status') == 'verified' and ev and ev.get('source_check_status') != 'checked':
                errors.append(f'{rid}: verified configuration has unchecked or conflicting evidence {eid}')
        if row.get('record_status') == 'verified':
            for k in fields:
                if not row.get(k):
                    errors.append(f'{rid}: verified configuration missing {k}')
        if row.get('weight_kg') and not row.get('weight_evidence_type'):
            errors.append(f'{rid}: weight has no evidence class')

    for row in tables['source_checks']:
        rid = row.get('evidence_id', '')
        if row.get('source_check_status') == 'checked':
            for k in ('checked_by', 'checked_at'):
                if not row.get(k):
                    errors.append(f'{rid}: checked evidence missing {k}')
        if row.get('second_check_status') in ('passed', 'failed'):
            for k in ('second_checked_by', 'second_checked_at'):
                if not row.get(k):
                    errors.append(f'{rid}: second check missing {k}')

    offer_keys = set()
    for row in tables['offers']:
        rid = row.get('offer_id', '')
        laptop = ref('laptops', row.get('configuration_id'), rid)
        ev = ref('source_checks', row.get('evidence_id'), rid)
        identity = tuple(row.get(k) for k in ('configuration_id', 'retailer', 'source_url', 'observed_date', 'snapshot_version'))
        if identity in offer_keys:
            errors.append(f'{rid}: repeated offer observation; review before assigning a new ID')
        offer_keys.add(identity)
        if row.get('condition_evidence_id'):
            ref('source_checks', row['condition_evidence_id'], rid)
        if row.get('offer_status') == 'verified':
            if row.get('condition') != 'new' or row.get('purchase_type') != 'outright':
                errors.append(f'{rid}: verified offers require new condition and outright purchase')
            condition_ev = by_id['source_checks'].get(row.get('condition_evidence_id'))
            if not condition_ev or condition_ev.get('source_check_status') != 'checked':
                errors.append(f'{rid}: verified offer lacks checked new-condition evidence')
            if not laptop or laptop.get('record_status') != 'verified':
                errors.append(f'{rid}: verified offer requires a verified configuration')
            if not ev or ev.get('source_check_status') != 'checked':
                errors.append(f'{rid}: verified offer requires checked source evidence')

    for row in tables['students']:
        rid = row.get('participant_id', '')
        for weight, target in [('ram', 'desired_ram_gb'), ('storage', 'desired_storage_gb'), ('weight', 'desired_max_weight_kg'), ('screen', 'preferred_screen_inches'), ('gpu', 'preferred_gpu_type')]:
            n = number(row.get('importance_' + weight))
            if n is not None and n > 0 and not row.get(target):
                warnings.append(f'{rid}: active {weight} importance has an unknown target; resolve in the questionnaire pilot, do not invent a value')

    assignment_configs, assignment_orders = set(), set()
    for row in tables['assignments']:
        rid = row.get('assignment_id', '')
        student = ref('students', row.get('participant_id'), rid)
        offer = ref('offers', row.get('offer_id'), rid)
        laptop = ref('laptops', row.get('configuration_id'), rid)
        config_key = (row.get('participant_id'), row.get('configuration_id'))
        order_key = (row.get('participant_id'), row.get('display_order'))
        if config_key in assignment_configs or order_key in assignment_orders:
            errors.append(f'{rid}: repeated participant configuration or display position')
        assignment_configs.add(config_key)
        assignment_orders.add(order_key)
        if student:
            if student.get('consent_status') != 'consented' or student.get('adult_confirmed') != '1':
                errors.append(f'{rid}: assignment requires consented adult participant')
            if row.get('protocol_version') != student.get('protocol_version'):
                errors.append(f'{rid}: protocol version differs from profile')
        if offer:
            for k in ('configuration_id', 'snapshot_version'):
                if row.get(k) != offer.get(k):
                    errors.append(f'{rid}: {k} differs from offer')
            if offer.get('offer_status') != 'verified':
                errors.append(f'{rid}: assignment uses an unverified offer')
        if student and offer:
            price, budget = number(offer.get('price_usd')), number(student.get('budget_usd'))
            if price is not None and budget is not None and price > 0 and budget > 0:
                ratio = price / budget
                if ratio > 1:
                    errors.append(f'{rid}: assigned price exceeds budget')
                expected = 'le_0.60' if ratio <= Decimal('0.60') else 'gt_0.60_le_0.80' if ratio <= Decimal('0.80') else 'gt_0.80_le_1.00'
                if row.get('price_budget_band') != expected:
                    errors.append(f'{rid}: incorrect price-to-budget band')
        if student and laptop:
            for requirement, attribute, minimum in [('min_ram_gb', 'ram_gb', True), ('min_storage_gb', 'storage_gb', True), ('max_weight_kg', 'weight_kg', False)]:
                bound = number(student.get(requirement))
                actual = number(laptop.get(attribute))
                if bound is not None and (actual is None or (actual < bound if minimum else actual > bound)):
                    errors.append(f'{rid}: missing or failing mandatory {requirement}')
            required_gpu = student.get('required_gpu_type')
            if required_gpu and laptop.get('gpu_type') != required_gpu:
                errors.append(f'{rid}: mandatory GPU type is unverified or not matched')
            # Conservative exact normalized OS match only. Compatibility aliases await protocol work.
            required_os = student.get('required_os')
            if required_os and (not offer or normalized(offer.get('delivered_os') or '') != normalized(required_os)):
                errors.append(f'{rid}: mandatory delivered OS needs an exact verified match')

    rated_assignments = set()
    for row in tables['ratings']:
        rid = row.get('rating_id', '')
        assignment = ref('assignments', row.get('assignment_id'), rid)
        ref('students', row.get('participant_id'), rid)
        offer = ref('offers', row.get('offer_id'), rid)
        ref('laptops', row.get('configuration_id'), rid)
        if row.get('assignment_id') in rated_assignments:
            errors.append(f'{rid}: duplicate response for an assignment')
        rated_assignments.add(row.get('assignment_id'))
        if assignment:
            for k in ('participant_id', 'configuration_id', 'offer_id', 'snapshot_version', 'display_order'):
                if row.get(k) != assignment.get(k):
                    errors.append(f'{rid}: {k} differs from the displayed assignment')
        if offer and row.get('configuration_id') != offer.get('configuration_id'):
            errors.append(f'{rid}: rated configuration differs from its offer')
        if row.get('rating_status') == 'rated' and not row.get('suitability_rating'):
            errors.append(f'{rid}: rated response has no rating')
        if row.get('rating_status') != 'rated' and row.get('suitability_rating'):
            errors.append(f'{rid}: missing feedback must not receive a numerical rating')

    verified_laptops = sum(x.get('record_status') == 'verified' for x in tables['laptops'])
    verified_offers = sum(x.get('offer_status') == 'verified' for x in tables['offers'])
    if verified_laptops < len(tables['laptops']) or verified_offers < len(tables['offers']):
        warnings.append('Draft/quarantined rows are collection work only; exclude them from survey assignments and model data.')
    if verified_laptops < 40:
        warnings.append(f'Working pilot catalogue target: 40 verified configurations; currently {verified_laptops}.')
    warnings.append('Manual review must confirm truth of specs, new condition, source permissions, price validity and second-check coverage; this validator cannot certify those facts.')
    warnings.append('Candidate balancing, exposure priority, lowest eligible offer selection, frozen snapshot integrity and study approval are later gates, not certified by this scaffold validator.')
    return dict(
        schema_version='0.1', checked_at=datetime.now().astimezone().isoformat(),
        structural_validation='PASS' if not errors else 'FAIL',
        counts={k: len(v) for k, v in tables.items()},
        verified_configurations=verified_laptops, verified_offers=verified_offers,
        errors=errors, warnings=warnings,
        sha256={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'data').glob('*.csv'))}
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=ROOT)
    ap.add_argument('--write-report', action='store_true')
    args = ap.parse_args()
    result = validate(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.write_report:
        (args.root / 'reports').mkdir(exist_ok=True)
        (args.root / 'reports/validation_report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    raise SystemExit(1 if result['errors'] else 0)


if __name__ == '__main__':
    main()
