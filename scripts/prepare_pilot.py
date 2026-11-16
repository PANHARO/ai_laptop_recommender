"""Generate a draft readiness report and uncompleted second-check queue.

This does not freeze a survey, select participant assignments or change data.
"""
import argparse
from collections import Counter, defaultdict
import csv
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path

from laptop_collection.batch import ROOT
from laptop_collection.store import Store
from scripts.validate_data import validate
from scripts.pilot_policy import assess_offer


def write_csv(path, rows, columns):
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def prepare(root, output, date):
    root, output = Path(root), Path(output)
    validation = validate(root)
    if validation['errors']:
        raise ValueError(validation['errors'])
    store = Store(root)
    with store.lock:
        tables = store.canonical()
        candidates = store.list()
        with store.connect() as db:
            audit_events = [json.loads(row[0]) for row in db.execute('SELECT payload FROM audit_events ORDER BY rowid')]
    findings = {}
    rechecks = []
    for event in audit_events:
        if event.get('action') == 'manual_second_checks':
            rechecks.extend(event.get('rows', []))
            for row in event.get('rows', []):
                findings[row['evidence_id']] = row.get('findings', '')
    policy_path = root / 'config/pilot_policy.json'
    policy = json.loads(policy_path.read_text(encoding='utf-8')) if policy_path.exists() else None
    attestation = None
    if policy and policy.get('check_date_attestation_file'):
        attestation_path = root / policy['check_date_attestation_file']
        if attestation_path.is_file():
            attestation = json.loads(attestation_path.read_text(encoding='utf-8'))
    sources = {r['evidence_id']: r for r in tables['source_checks']}
    laptops = {r['configuration_id']: r for r in tables['laptops'] if r['record_status'] == 'verified'}
    offers = defaultdict(list)
    for offer in tables['offers']:
        if offer['offer_status'] == 'verified' and offer['configuration_id'] in laptops:
            offers[offer['configuration_id']].append(offer)
    representatives = []
    passed = set()
    for cid, choices in offers.items():
        # A representative for catalogue QA only, not survey-offer selection.
        checked_choices = [o for o in choices if sources[o['evidence_id']]['second_check_status']=='passed'
            and sources[o['evidence_id']].get('second_checked_by') and sources[o['evidence_id']].get('second_checked_at')]
        if checked_choices:
            passed.add(cid)
        offer = min(checked_choices or choices, key=lambda o: (Decimal(o['price_usd']), o['retailer'], o['offer_id']))
        representatives.append((cid, offer))
    representatives.sort(key=lambda pair: (Decimal(pair[1]['price_usd']), pair[0]))
    strata = defaultdict(list)
    for index, (cid, offer) in enumerate(representatives):
        tier = min(2, index * 3 // max(1, len(representatives)))
        strata[(offer['retailer'], tier)].append((cid, offer))
    for values in strata.values():
        values.sort(key=lambda pair: hashlib.sha256(('42:' + pair[0]).encode()).hexdigest())
    count = min(len(representatives), max(8, len(passed), math.ceil(len(representatives) * 0.2)))
    selected = []
    covered = Counter()
    for key, values in strata.items():
        already = [pair for pair in values if pair[0] in passed]
        selected.extend((cid, offer, key[1]) for cid, offer in already)
        covered[key] += len(already)
        strata[key] = [pair for pair in values if pair[0] not in passed]
    while len(selected) < count:
        available = [key for key in strata if strata[key]]
        key = min(available, key=lambda key: (covered[key], key))
        cid, offer = strata[key].pop(0)
        selected.append((cid, offer, key[1]))
        covered[key] += 1
    queue = []
    for cid, offer, tier in selected:
        laptop = laptops[cid]
        evidence = sources[offer['evidence_id']]
        condition = sources[offer['condition_evidence_id']]
        queue.append(dict(configuration_id=cid, offer_id=offer['offer_id'],
            manufacturer_sku=laptop['manufacturer_sku'], model=laptop['model'],
            retailer=offer['retailer'], source_url=offer['source_url'],
            observed_date=offer['observed_date'], price_usd=offer['price_usd'],
            evidence_id=offer['evidence_id'], condition_evidence_id=offer['condition_evidence_id'],
            condition_evidence_file=condition['evidence_file'],
            qa_price_coverage=['lower catalogue third','middle catalogue third','upper catalogue third'][tier],
            second_check_status=evidence['second_check_status'],
            second_checked_by=evidence.get('second_checked_by',''),
            second_checked_at=evidence.get('second_checked_at',''), findings=findings.get(offer['evidence_id'],'')))
    inventory = []
    for cid, offer in representatives:
        laptop = laptops[cid]
        inventory.append({k:laptop[k] for k in ('configuration_id','brand','model','manufacturer_sku','cpu_model','gpu_model','ram_gb','storage_gb','storage_type','screen_inches','display_text')}
                         | {k:offer[k] for k in ('offer_id','retailer','price_usd','observed_date','availability_text','delivered_os','source_url')})
    participant_counts = {}
    for name in ('students','ratings','assignments'):
        with (root/'data'/f'{name}.csv').open(encoding='utf-8-sig', newline='') as stream:
            participant_counts[name] = sum(1 for _ in csv.DictReader(stream))
    freshness = []
    freshness_date = (policy.get('actual_freeze_date') or date) if policy and policy.get('freeze_date_rule') else (policy['intended_freeze_date'] if policy else None)
    if policy:
        for choices in offers.values():
            for offer in choices:
                freshness.append({k: offer[k] for k in ('configuration_id','offer_id','retailer','source_url','observed_date','price_usd','availability_text')}
                    | assess_offer(offer, rechecks, policy, reference_date=freshness_date, attestation=attestation))
    fresh_ids = {r['configuration_id'] for r in freshness if r['freshness_status']=='within_window'}
    uncertain_ids = {r['configuration_id'] for r in freshness if r['freshness_status']=='check_date_uncertain'} - fresh_ids
    report = dict(date=date, status='DRAFT_NOT_READY_FOR_PARTICIPANTS',
        target_verified_configurations=40, verified_configurations_with_offers=len(offers),
        configurations_still_needed=max(0,40-len(offers)),
        verified_offers=sum(len(v) for v in offers.values()),
        queue_states=dict(Counter(c['state'] for c in candidates)),
        verified_offers_by_retailer=dict(Counter(o['retailer'] for rows in offers.values() for o in rows)),
        second_checks=dict(passed_configurations=len(passed), required_for_current_catalogue=math.ceil(len(offers)*0.2),
            required_at_target=8, proposed_queue_count=len(queue), status='pending' if len(passed)<math.ceil(len(offers)*0.2) else 'count_satisfied_review_coverage'),
        unresolved_gates=(['40 distinct verified configurations'] if len(offers)<40 else [])
            + (['required manual second checks'] if len(passed)<math.ceil(len(offers)*0.2) else [])
            + (['resolve offer check-date uncertainty or freshness before actual freeze; see offer_freshness.csv'] if policy and len(fresh_ids)<40 else [])
            + [
            *([] if policy else ['availability and offer-age policies', 'task/OS vocabulary and unknown-target handling']),
            'final instrument wording/translation, participant storage and withdrawal details, and study approvals', 'immutable survey snapshot'],
        confirmed_policy=policy,
        user_reported_check_window=attestation,
        freshness_assessment=dict(configurations_with_fresh_offers=len(fresh_ids),
            reference_date=freshness_date, provisional=not bool(policy.get('actual_freeze_date')),
            configurations_without_confirmed_fresh_offers=len(offers)-len(fresh_ids),
            configurations_with_uncertain_check_dates=len(uncertain_ids),
            offer_status_counts=dict(Counter(r['freshness_status'] for r in freshness))) if policy else None,
        research_rows=participant_counts,
        survey_snapshot_created=False, recruitment_started=False, models_trained=False,
        notes=['QA price thirds are descriptive coverage strata, not the proposal\'s participant budget-relative assignment bands.',
            'Representative offers are for QA only; freshness assessment is retrospective, not a completed or backdated survey freeze.',
            'AI desk review has not been counted as a second manual human check.'])
    output.mkdir(parents=True, exist_ok=True)
    (output/'readiness.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if freshness:
        write_csv(output/'offer_freshness.csv',freshness,list(freshness[0]))
    columns=['configuration_id','offer_id','manufacturer_sku','model','retailer','source_url','observed_date','price_usd','evidence_id','condition_evidence_id','condition_evidence_file','qa_price_coverage','second_check_status','second_checked_by','second_checked_at','findings']
    write_csv(output/'second_check_queue.csv',queue,columns)
    additional = [r for r in queue if r['second_check_status'] != 'passed']
    write_csv(output/'additional_second_check_queue.csv',additional,columns)
    if inventory:
        write_csv(output/'catalogue_inventory.csv',inventory,list(inventory[0]))
    text = f'''# Pilot readiness — {date}

Preparation has started; the pilot is not ready for participants or freeze.

| Gate | Actual status |
|---|---|
| Verified configurations with verified offers | {len(offers)} / 40; {max(0,40-len(offers))} more needed |
| Verified dated offers | {report['verified_offers']} |
| Separate manual second checks | {len(passed)} passed; {report['second_checks']['required_for_current_catalogue']} required now, at least 8 at forty |
| Second-check queue | {len(queue)} configurations including {len(passed)} already passed; {len(additional)} additional checks proposed |
| Task/OS, missing target, availability and offer-age policies | {'User-confirmed; see config/pilot_policy.json' if policy else 'Open decisions in the protocol draft'} |
| Freshness as of {freshness_date or date} (provisional) | {str(len(fresh_ids)) + ' configurations confirmed within window; ' + str(len(uncertain_ids)) + ' have uncertain check dates; see offer_freshness.csv' if policy else 'Policy pending'} |
| Questionnaire, consent and study approval | Draft/pending; no recruitment |
| Survey snapshot | Not frozen |
| Students / ratings / assignments | {participant_counts['students']} / {participant_counts['ratings']} / {participant_counts['assignments']} |
| Model training | Not started |

[Questionnaire draft](../../docs/PILOT_QUESTIONNAIRE_DRAFT.md) ·
[Protocol and decisions](../../docs/PILOT_PROTOCOL_DRAFT.md) ·
[Second-check queue](second_check_queue.csv) ·
[Additional checks only](additional_second_check_queue.csv) ·
[Catalogue QA inventory](catalogue_inventory.csv) · [Machine-readable status](readiness.json).

The original intended freeze date is {policy['intended_freeze_date'] if policy else 'undecided'};
the maximum offer age is {policy['maximum_offer_age_days'] if policy else 'undecided'} days.
Ro authorized a later actual freeze after freshness checks on 29 October.
The actual date remains pending. This report assesses the window provisionally
as of {freshness_date or date}; recompute it at the actual freeze.
Ro reports that all catalogue checks were completed within 20–28 October,
but only knows the overall date range. Retain this range without inventing
exact per-offer dates. An interval overlapping the seven-day cutoff is uncertain,
not proof that the offer needs another review or that it is within the window.
Original observation dates are never rewritten. A passed human check of an
exact offer may confirm it again on the actual check date. Later checks cannot
be backdated into an earlier freeze. All stock statuses are allowed under the
confirmed policy and must remain visible; unknown stock is not in-stock.

The inventory is a working QA reference, not a survey snapshot or a list of
offers approved for student presentation. Original offer dates and unknown
attributes are retained. Price thirds in this QA sample are not the survey's
budget-relative 0.60/0.80/1.00 assignment bands. Passed checks are imported actual
human checks, with reviewer/time retained. No person, rating or successful check
has been invented.
'''
    (output/'READINESS.md').write_text(text,encoding='utf-8')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--date',required=True)
    args=parser.parse_args()
    print(json.dumps(prepare(args.root,args.output,args.date),indent=2))


if __name__=='__main__':
    main()
