"""Recover survey links from exact historical exports, never from model names."""
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def unique_index(rows, field):
    result = {}
    for row in rows:
        value = row.get(field, "")
        if not value or value in result:
            raise ValueError(f"Missing or duplicate {field}")
        result[value] = row
    return result


def recover(source, display, data_dir, output):
    """Require independently retained card descriptions and canonical evidence."""
    source, display, data_dir, output = map(Path, (source, display, data_dir, output))
    packet = json.loads(source.read_text(encoding="utf-8-sig"))
    displayed = unique_index(json.loads(display.read_text(encoding="utf-8-sig")), "id")
    laptops = unique_index(read_csv(data_dir / "laptops.csv"), "configuration_id")
    offers = unique_index(read_csv(data_dir / "offers.csv"), "offer_id")
    evidence = unique_index(read_csv(data_dir / "source_checks.csv"), "evidence_id")
    cards = unique_index(packet["cards"], "configuration_id")
    if set(cards) != set(displayed):
        raise ValueError("Catalog and displayed card inventories differ")
    recovered = []
    for cid, card in sorted(cards.items()):
        if cid not in laptops or laptops[cid]["record_status"] != "verified":
            raise ValueError(f"Unverified configuration: {cid}")
        # No fuzzy, name-only, price-only, or nearest-SKU matching.
        for key, value in card.items():
            if key in laptops[cid] and str(value) != laptops[cid][key]:
                raise ValueError(f"Historical hardware conflict: {cid}/{key}")
        if len(card["offers"]) != 1:
            raise ValueError(f"The displayed offer is ambiguous: {cid}")
        shown = card["offers"][0]
        oid = shown["offer_id"]
        offer = offers.get(oid, {})
        if offer.get("configuration_id") != cid or offer.get("offer_status") != "verified":
            raise ValueError(f"Unverified exact offer: {cid}/{oid}")
        for key, value in shown.items():
            if key in offer and str(value) != offer[key]:
                raise ValueError(f"Historical offer conflict: {cid}/{oid}/{key}")
        if (offer.get("condition") != "new" or offer.get("currency") != "USD"
                or offer.get("purchase_type") != "outright" or Decimal(offer["price_usd"]) <= 0):
            raise ValueError(f"Out-of-scope purchase offer: {oid}")
        for eid in (offer["evidence_id"], offer["condition_evidence_id"]):
            if evidence.get(eid, {}).get("source_check_status") != "checked":
                raise ValueError(f"Missing checked source evidence: {oid}/{eid}")
        description = displayed[cid]["description"]
        reference = re.search(r"Reference:\s*(LAP\d{4})\s*/\s*(OFF\d{4})", description)
        if not reference or reference.groups() != (cid, oid):
            raise ValueError(f"Displayed reference conflict: {cid}")
        displayed_price = Decimal(displayed[cid]["price"].replace("US$", "").replace(",", ""))
        if displayed_price != Decimal(offer["price_usd"]):
            raise ValueError(f"Displayed price conflict: {cid}")
        if f"Price observed: {offer['observed_date']}" not in description or offer["source_url"] not in description:
            raise ValueError(f"Displayed source/date conflict: {cid}")
        recovered.append(dict(configuration_id=cid, hardware=laptops[cid], offer=offer,
                              link_status="verified_exact_export_and_display_reference"))
    assigned = packet["core"] + sum(packet["groups"].values(), [])
    if len(assigned) != len(set(assigned)) or set(assigned) != set(cards):
        raise ValueError("Invalid shared/group card inventory")
    result = dict(version=packet["version"], historical_offers=True,
                  freshness_claim=False, source_catalogue_sha256=sha256(source),
                  displayed_cards_sha256=sha256(display),
                  canonical_sha256={name: sha256(data_dir / f"{name}.csv")
                                    for name in ("laptops", "offers", "source_checks")},
                  core=packet["core"], groups=packet["groups"], cards=recovered)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def load_catalogue(path):
    packet = json.loads(Path(path).read_text(encoding="utf-8"))
    cards = unique_index(packet["cards"], "configuration_id")
    for cid, card in cards.items():
        h, o = card["hardware"], card["offer"]
        if (card["link_status"] != "verified_exact_export_and_display_reference"
                or h["record_status"] != "verified" or o["offer_status"] != "verified"
                or h["configuration_id"] != cid or o["configuration_id"] != cid
                or o["condition"] != "new" or o["purchase_type"] != "outright"
                or o["currency"] != "USD" or Decimal(o["price_usd"]) <= 0):
            raise ValueError(f"Invalid verified link: {cid}")
    return packet, cards
