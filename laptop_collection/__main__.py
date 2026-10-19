import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from .batch import ROOT, collect, import_export, manual_url, seed_existing
from .store import Store


def main():
    parser = argparse.ArgumentParser(description='Local laptop collection and human verification; canonical data is never written by a collector.')
    parser.add_argument('--root', type=Path, default=ROOT)
    commands = parser.add_subparsers(dest='command', required=True)
    fetch = commands.add_parser('collect', help='Check policies and stage public HTML candidates.')
    fetch.add_argument('--site', choices=['all','goldone','ptc','beckie'], default='all')
    fetch.add_argument('--limit', type=int, default=3, help='Maximum extracted observations per retailer, including already-staged observations.')
    fetch.add_argument('--max-pages', type=int, default=None)
    commands.add_parser('seed-existing', help='Queue existing dated observations without network access or canonical changes.')
    imp = commands.add_parser('import-urls', help='Queue URLs without retrieving them; works when automation is disallowed.')
    imp.add_argument('--site', choices=['goldone','ptc','beckie'], required=True)
    imp.add_argument('--file', type=Path, required=True, help='UTF-8 text file with one HTTPS product URL per line.')
    exp = commands.add_parser('import-export', help='Import a retailer-authorized JSON product export without network access.')
    exp.add_argument('--site', choices=['goldone','ptc','beckie'], required=True)
    exp.add_argument('--file', type=Path, required=True)
    exp.add_argument('--authorization', required=True)
    commands.add_parser('status', help='Print local queue counts.')
    commands.add_parser('review', help='Launch Streamlit bound only to localhost.')
    args = parser.parse_args()
    root = args.root.resolve()
    if not (root/'config/schema.json').is_file():
        parser.error('Root must contain config/schema.json and the canonical data files.')
    if args.command == 'collect':
        if args.max_pages is not None and not 1 <= args.max_pages <= 50:
            parser.error('--max-pages must be 1 to 50.')
        result = collect(root, ['goldone','ptc','beckie'] if args.site=='all' else [args.site], args.limit, args.max_pages)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if any(x['extracted'] for x in result['per_site'].values()) else 2
    if args.command == 'seed-existing':
        print(json.dumps({'staged_new':seed_existing(root), 'network_requests':0}))
    elif args.command == 'import-urls':
        lines = [x.strip() for x in args.file.read_text(encoding='utf-8-sig').splitlines() if x.strip() and not x.startswith('#')]
        store=Store(root)
        from .batch import settings
        from .models import allowed_url
        for url in lines:
            allowed_url(url, settings(root)['sources'][args.site])
        print(json.dumps({'staged_new':sum(manual_url(store,args.site,url)[1] for url in lines), 'network_requests':0}))
    elif args.command == 'import-export':
        print(json.dumps({'staged_new':import_export(root,args.site,args.file,args.authorization), 'network_requests':0}))
    elif args.command == 'status':
        from collections import Counter
        print(json.dumps(dict(Counter(x['state'] for x in Store(root).list())),indent=2))
    elif args.command == 'review':
        env=dict(os.environ, LAPTOP_RECOMMENDER_ROOT=str(root))
        return subprocess.call([sys.executable,'-m','streamlit','run',str(ROOT/'review_app.py'),'--server.address','127.0.0.1'],env=env)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as exc:
        print('Collection stopped: ' + str(exc), file=sys.stderr)
        raise SystemExit(2)
