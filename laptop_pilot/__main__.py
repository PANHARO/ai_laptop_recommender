import argparse
import json
import sys
from pathlib import Path

from .importer import DEFAULT_CATALOGUE, ROOT


def main():
    parser = argparse.ArgumentParser(description="Local ITM360 pilot import and evaluation")
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="Read ZIP README and inventory without printing participant records")
    inspect.add_argument("bundle", type=Path)
    recover = commands.add_parser("recover-catalogue", help="Validate original source export against displayed cards and canonical tables")
    recover.add_argument("source", type=Path)
    recover.add_argument("display", type=Path)
    recover.add_argument("--data", type=Path, default=ROOT / "data")
    recover.add_argument("--output", type=Path, default=DEFAULT_CATALOGUE)
    ingest = commands.add_parser("import", help="Keep raw/normalized data and validation under ignored private/")
    ingest.add_argument("bundle", type=Path)
    ingest.add_argument("--mapping", type=Path, default=ROOT / "config/pilot_import.json")
    ingest.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    baseline = commands.add_parser("reproduce-price", help="Reproduce the budget-only ZIP result exactly")
    baseline.add_argument("bundle", type=Path)
    baseline.add_argument("--output", type=Path, default=ROOT / "private/itm360_pilot/price_baseline_reproduced.json")
    compare = commands.add_parser("compare", help="Locked primary comparison; --exploratory explicitly permits the small secondary cohort")
    compare.add_argument("dataset", type=Path)
    compare.add_argument("--exploratory", action="store_true")
    commands.add_parser("guard-index", help="Reject staged participant records and local artifacts")
    args = parser.parse_args()
    if args.command == "inspect":
        from .importer import inspect_bundle
        print(json.dumps(inspect_bundle(args.bundle), indent=2, ensure_ascii=True))
    elif args.command == "recover-catalogue":
        from .catalogue import recover
        result = recover(args.source, args.display, args.data, args.output)
        print(f"Recovered {len(result['cards'])} verified exact historical card-to-offer links")
    elif args.command == "import":
        from .importer import import_bundle
        path, report = import_bundle(args.bundle, args.mapping, args.catalogue)
        print(json.dumps(dict(dataset=str(path), status=report["status"], linked_rows=report["linked_rows"],
                              unresolved_links=len(report["unresolved_links"]), structural_errors=len(report["errors"]),
                              excluded_profiles=len({r["participant_id"] for r in report["excluded_profiles"]})), indent=2))
        return 0 if report["status"] == "ready" else 2
    elif args.command == "reproduce-price":
        from .baseline import reproduce
        print(json.dumps(reproduce(args.bundle, args.output), indent=2))
    elif args.command == "compare":
        from .evaluation import evaluate
        report = evaluate(args.dataset, minimum=2 if args.exploratory else 10)
        # Aggregate report only. Splits, histories and predictions remain private.
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "complete" else 2
    else:
        from .privacy import guard_index
        guard_index()
        print("Staged-file privacy check passed")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, FileNotFoundError, KeyError) as exc:
        print(f"Pilot operation stopped: {exc}", file=sys.stderr)
        sys.exit(2)
