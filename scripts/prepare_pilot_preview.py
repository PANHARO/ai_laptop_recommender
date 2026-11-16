"""Export an offline instrument/card preview; never creates research responses."""
import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from laptop_collection.batch import ROOT
from laptop_collection.store import Store
from scripts.pilot_policy import assess_offer
from scripts.validate_data import validate


def build_packet(root):
    root = Path(root)
    store = Store(root)
    with store.lock:
        validation = validate(root)
        if validation['errors']:
            raise ValueError(validation['errors'])
        tables = store.canonical()
        with store.connect() as db:
            events = [json.loads(row[0]) for row in db.execute('SELECT payload FROM audit_events ORDER BY rowid')]
        hashes = {name: hashlib.sha256((root/'data'/f'{name}.csv').read_bytes()).hexdigest()
                  for name in ('laptops', 'offers', 'source_checks')}
    policy = json.loads((root/'config/pilot_policy.json').read_text(encoding='utf-8'))
    attestation = None
    if policy.get('check_date_attestation_file'):
        attestation_path = root / policy['check_date_attestation_file']
        if attestation_path.is_file():
            attestation = json.loads(attestation_path.read_text(encoding='utf-8'))
    now = datetime.now(timezone(timedelta(hours=7)))
    rechecks = [row for event in events if event.get('action')=='manual_second_checks' for row in event.get('rows', [])]
    laptops = {r['configuration_id']: r for r in tables['laptops'] if r['record_status']=='verified'}
    cards = []
    for cid, laptop in sorted(laptops.items()):
        offers = [o for o in tables['offers'] if o['configuration_id']==cid and o['offer_status']=='verified'
                  and o['condition']=='new' and o['purchase_type']=='outright']
        if not offers:
            continue
        # Illustrative catalogue browsing only. No freshness approval, participant
        # assignment or survey-offer choice is implied by these panels.
        choices = []
        for offer in sorted(offers, key=lambda o: (Decimal(o['price_usd']), o['retailer'], o['offer_id'])):
            freshness = assess_offer(offer, rechecks, policy, now.date().isoformat(), attestation)
            choices.append({k:offer[k] for k in ('offer_id','retailer','retailer_sku','price_usd','price_text',
                'source_url','observed_date','availability_text','condition','condition_evidence_id','delivered_os','evidence_id')}
                | freshness)
        cards.append({k:laptop[k] for k in ('configuration_id','brand','model','manufacturer_sku','cpu_model',
            'gpu_model','gpu_type','gpu_vram_gb','ram_gb','ram_type','storage_gb','storage_type','screen_inches',
            'display_text','display_resolution','refresh_hz','weight_kg','weight_evidence_type')}
            | dict(offers=choices))
    return dict(preview_version='pilot_preview_2026-10-29_v1', created_at=now.isoformat(),
                mode='design_preview_not_research_collection', policy=policy, source_hashes=hashes,
                cards=cards, survey_snapshot_created=False)


def export(root, output):
    packet = build_packet(root)
    payload = json.dumps(packet, ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003c')
    template = Path(__file__).with_name('pilot_preview.html').read_text(encoding='utf-8')
    rendered = template.replace('/*PACKET*/null', payload)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output/'START_PILOT_PREVIEW.html').write_bytes(rendered.encode('utf-8'))
    manifest = {k:v for k,v in packet.items() if k!='cards'} | dict(configuration_count=len(packet['cards']),
        offer_count=sum(len(c['offers']) for c in packet['cards']),
        html_sha256=hashlib.sha256(rendered.encode('utf-8')).hexdigest())
    (output/'preview_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export(args.root, args.output), indent=2))


if __name__=='__main__':
    main()
