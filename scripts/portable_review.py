"""Export pending candidates to an offline browser form; safely replay returned reviews.

Run from the project root with: python -m scripts.portable_review --help
"""
import argparse
from collections import Counter
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile

from laptop_collection.batch import ROOT
from laptop_collection.mapping import Reviewer
from laptop_collection.models import EDIT_FIELDS, digest, now
from laptop_collection.store import Store, atomic_bytes, json_bytes


FORMAT = 'laptop-portable-review-v1'


def export_pending(root, output, states=('pending',)):
    store = Store(root)
    with store.lock:
        all_candidates = store.list()
        candidates = [c for c in all_candidates if c['state'] in states]
        if not candidates:
            raise ValueError('No pending candidates to export for the selected states.')
        service = Reviewer(store)
        for candidate in candidates:
            history = store.reviews(candidate['candidate_id'])
            if history:
                candidate['saved_review'] = history[-1]
            preview = service.preview(candidate)
            candidate['duplicate_hint'] = {
                'kind': preview['kind'],
                'matches': [r['configuration_id'] for r in preview['matches']],
            }
        manifest = dict(format=FORMAT, created_at=now(), candidates=candidates,
                        edit_fields=list(EDIT_FIELDS))
        manifest['batch_id'] = digest(candidates)
        template = Path(__file__).with_suffix('.html').read_text(encoding='utf-8')
        # JSON is data, never executable HTML, including retailer-supplied strings.
        embedded = json.dumps(manifest, ensure_ascii=False).replace('<', '\\u003c').replace('&', '\\u0026')
        output = Path(output)
        output.mkdir(parents=True, exist_ok=False)
        atomic_bytes(output/'manifest.json', json_bytes(manifest))
        atomic_bytes(output/'START_REVIEW.html', template.replace('__BATCH_DATA__', embedded).encode('utf-8'))
        counts = dict(Counter(c['site'] for c in candidates))
        readme = f'''PORTABLE LAPTOP REVIEW — {len(candidates)} candidates awaiting review

1. Copy START_REVIEW.html to your laptop (USB, your own cloud drive, or email to yourself).
   If using the ZIP, extract it first. Double-click START_REVIEW.html and open in Chrome or Edge.
2. No Python, venv, installation, or home-PC connection is needed.
   The extracted product information works offline. Retailer links need internet.
3. Edit the fields, record evidence, and select a decision for each item.
   Download results regularly and before closing the browser. Browser autosave is only a convenience.
4. Send the downloaded laptop-review-results-*.json back in this chat.
   If continuing on another browser/computer, open the HTML and use Load saved results.

Only the {len(candidates)} items in the selected states ({', '.join(states)}) are included: {counts}.
Saved confirmations and notes are restored. Other queue states are not included.
Decisions are applied to the home-PC project only when the returned JSON is imported.
Approval still passes the existing evidence, duplicate, revision and schema checks.
Manufacturer SKU is optional; shop SKU is separate. Unknown facts should remain blank.
Original observation dates are preserved. Record any later source-check date in notes.
Raw retailer pages are retained on the home PC; extracted evidence is embedded here.

Batch: {manifest['batch_id']}
Exported: {manifest['created_at']}

HOME-PC IMPORT (from project root; stop the Streamlit reviewer first):
  .\\.venv\\Scripts\\python.exe -m scripts.portable_review check RESULTS.json --manifest PATH_TO_manifest.json
  .\\.venv\\Scripts\\python.exe -m scripts.portable_review apply RESULTS.json --manifest PATH_TO_manifest.json

Check replays the whole batch in a temporary copy and makes no review/data changes here.
Apply repeats this preflight under the review lock, then uses the normal audited reviewer.
Stale/conflicting decisions are refused; repeated identical imports are idempotent.
'''
        atomic_bytes(output/'READ_ME.txt', readme.encode('utf-8'))
    return manifest


def load_reviews(results_path, manifest_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8-sig'))
    results = json.loads(Path(results_path).read_text(encoding='utf-8-sig'))
    if manifest.get('format') != FORMAT or results.get('format') != FORMAT:
        raise ValueError('Unrecognized portable review format.')
    if digest(manifest['candidates']) != manifest['batch_id'] or results.get('batch_id') != manifest['batch_id']:
        raise ValueError('Results do not match this original export manifest.')
    originals = {c['candidate_id']: c for c in manifest['candidates']}
    reviews = results.get('reviews')
    if not isinstance(reviews, list):
        raise ValueError('Results must contain a review list.')
    seen = set()
    for review in reviews:
        cid = review.get('candidate_id')
        if cid not in originals or cid in seen:
            raise ValueError('Unknown or repeated candidate in results.')
        seen.add(cid)
        if review.get('expected_revision') != originals[cid]['revision']:
            raise ValueError('Original revision does not match.')
        if review.get('action') not in ('approve', 'reject', 'needs_review', 'skip'):
            raise ValueError('Invalid decision.')
        if not isinstance(review.get('edits'), dict) or any(k not in EDIT_FIELDS for k in review['edits']):
            raise ValueError('Invalid editable fields.')
        if any(not isinstance(v, str) for v in review['edits'].values()):
            raise ValueError('Edited values must be text.')
        if not isinstance(review.get('confirmations'), dict) or any(type(v) is not bool for v in review['confirmations'].values()):
            raise ValueError('Invalid confirmations.')
        if not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip():
            raise ValueError('A reviewer code is required.')
        if not isinstance(review.get('notes'), str) or not isinstance(review.get('saved_at'), str):
            raise ValueError('Review notes and save time must be text.')
    return manifest, reviews


def replay(store, manifest, reviews):
    service = Reviewer(store)
    receipts = []
    originals = {c['candidate_id']: c for c in manifest['candidates']}
    for review in reviews:
        cid = review['candidate_id']
        current = store.get(cid)
        original = originals[cid]
        # Guard against importing a batch into an unrelated or modified workspace.
        if current['original_fields'] != original['original_fields']:
            raise ValueError(f'{cid}: original extraction changed.')
        request_id = 'portable-' + digest(dict(batch_id=manifest['batch_id'], review=review))
        document = original.get('saved_review', {}).get('condition_document')
        if document and document['source_url'] != review['edits'].get('condition_evidence_url', original['fields'].get('condition_evidence_url')):
            document = None
        receipt = service.review(
            cid, review['action'], review['edits'], review['reviewer'],
            review['notes'] + '\nPortable review saved at ' + review['saved_at'] +
            '; batch ' + manifest['batch_id'], review['confirmations'],
            expected_revision=review['expected_revision'], request_id=request_id,
            condition_document=document)
        receipts.append(dict(candidate_id=cid, state=receipt['state'], notices=receipt['notices']))
    return receipts


def import_reviews(root, results_path, manifest_path, apply=False):
    manifest, reviews = load_reviews(results_path, manifest_path)
    store = Store(root)
    with store.lock:
        store.recover()
        with tempfile.TemporaryDirectory(prefix='portable-review-check-') as tmp:
            target = Path(tmp)
            for name in ('config', 'data'):
                shutil.copytree(store.root/name, target/name)
            (target/'staging').mkdir()
            with store.connect() as source, closing(sqlite3.connect(target/'staging/collection.sqlite3')) as dest:
                source.backup(dest)
            if (store.staging/'evidence').exists():
                shutil.copytree(store.staging/'evidence', target/'staging/evidence')
            receipts = replay(Store(target), manifest, reviews)
        if apply:
            receipts = replay(store, manifest, reviews)
    return dict(applied=apply, decisions=len(receipts), receipts=receipts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    sub = parser.add_subparsers(dest='command', required=True)
    export = sub.add_parser('export')
    export.add_argument('output', type=Path)
    export.add_argument('--state', action='append', choices=['pending', 'needs_review', 'skipped'],
                        help='Queue state to include; repeat to include more than one. Default: pending.')
    for command in ('check', 'apply'):
        imp = sub.add_parser(command)
        imp.add_argument('results', type=Path)
        imp.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'export':
        manifest = export_pending(args.root, args.output, args.state or ('pending',))
        print(json.dumps(dict(output=str(args.output.resolve()), count=len(manifest['candidates']), batch_id=manifest['batch_id'])))
    else:
        print(json.dumps(import_reviews(args.root, args.results, args.manifest, args.command == 'apply'), indent=2))


if __name__ == '__main__':
    main()
