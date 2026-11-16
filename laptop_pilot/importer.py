"""Read bundles without executing their scripts or publishing human records."""
from collections import Counter
import csv
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import zipfile

from .catalogue import load_catalogue, sha256, unique_index
from .ranking import eligibility, number, profile_errors

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOGUE = ROOT / "config/pilot/recovered_catalogue.json"


def private_path(path):
    path = Path(path).resolve()
    root = (ROOT / "private").resolve()
    # Also reject an existing private/ symlink pointing outside the checkout.
    if not root.is_relative_to(ROOT.resolve()) or not path.is_relative_to(root):
        raise ValueError("Human data and evaluation outputs must stay under this repository's ignored private/ directory")
    return path


def checked_bundle(path):
    bundle = zipfile.ZipFile(path)
    total = 0
    seen = set()
    try:
        for info in bundle.infolist():
            name = info.filename.replace("\\", "/")
            parts = PurePosixPath(name)
            if parts.is_absolute() or ".." in parts.parts or ":" in name or name in seen:
                raise ValueError("Unsafe or duplicate ZIP member")
            if stat.S_ISLNK(info.external_attr >> 16) or info.flag_bits & 1:
                raise ValueError("Symlink/encrypted ZIP members are unsupported")
            seen.add(name)
            total += info.file_size
            if total > 100_000_000 or info.file_size > 25_000_000:
                raise ValueError("Pilot ZIP exceeds local import size limits")
        return bundle
    except Exception:
        bundle.close()
        raise


def inspect_bundle(path):
    with checked_bundle(path) as bundle:
        names = bundle.namelist()
        readmes = [name for name in names if PurePosixPath(name).name.lower().startswith("readme")
                   and not name.endswith("/")]
        if not readmes:
            raise ValueError("ZIP has no README; supply the complete original bundle")
        return dict(sha256=sha256(path), members=names,
                    readmes={name: bundle.read(name).decode("utf-8-sig") for name in readmes})


def csv_member(bundle, member, columns):
    reader = csv.DictReader(io.StringIO(bundle.read(member).decode("utf-8-sig"), newline=""))
    if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("Missing or duplicate CSV headers")
    unknown = set(columns.values()) - set(reader.fieldnames)
    if unknown:
        raise ValueError("Column map references missing CSV headers")
    result = []
    for raw in reader:
        if None in raw or any(value is None for value in raw.values()):
            raise ValueError("Malformed CSV row")
        row = {key: value.strip() for key, value in raw.items()}
        for target, source in columns.items():
            if target in row and target != source and row[target] != row[source]:
                raise ValueError("Column map would overwrite a different value")
            row[target] = row[source]
        result.append(row)
    return result


def import_bundle(path, mapping_path, catalogue_path=DEFAULT_CATALOGUE):
    path, mapping_path, catalogue_path = map(Path, (path, mapping_path, catalogue_path))
    inspection = inspect_bundle(path)
    mapping = json.loads(mapping_path.read_text(encoding="utf-8-sig"))
    packet, cards = load_catalogue(catalogue_path)
    if mapping["study_phase"] != "pilot" or mapping["instrument_version"] != packet["version"]:
        raise ValueError("Import must identify this pilot's exact instrument, separately from main data")
    fingerprint = inspection["sha256"]
    mapping_hash = sha256(mapping_path)
    destination = private_path(ROOT / "private/itm360_pilot/imports" / (fingerprint[:16] + "_" + mapping_hash[:8]))
    if destination.exists():
        raise ValueError("This bundle/map import already exists; preserve it and use its validation report")
    # Parse before creating output; no extractall and no execution of ZIP code.
    with checked_bundle(path) as bundle:
        students = csv_member(bundle, mapping["students_member"], mapping.get("students_columns", {}))
        ratings = csv_member(bundle, mapping["ratings_member"], mapping.get("ratings_columns", {}))
        survey_cards = csv_member(bundle, mapping["cards_member"], {}) if mapping.get("cards_member") else []
    destination.mkdir(parents=True)
    shutil.copyfile(path, destination / "original_bundle.zip")
    shutil.copyfile(mapping_path, destination / "import_map.json")
    shutil.copyfile(catalogue_path, destination / "catalogue.json")
    (destination / "readmes.json").write_text(json.dumps(inspection["readmes"], indent=2), encoding="utf-8")
    errors, unresolved, linked, excluded_profiles = [], [], [], []
    if survey_cards:
        unique_index(survey_cards, "card_id")
    for shown in survey_cards:
        cid = shown["card_id"]
        if cid not in cards:
            unresolved.append(dict(configuration_id=cid, reason="no_verified_displayed_card_to_offer_link"))
        elif number(shown["displayed_price_usd"]) != number(cards[cid]["offer"]["price_usd"]):
            unresolved.append(dict(configuration_id=cid, reason="survey_heading_price_conflict"))
    try:
        profiles = unique_index(students, "participant_id")
    except ValueError as exc:
        profiles = {}
        errors.append(dict(reason=str(exc)))
    for pid, profile in profiles.items():
        for reason in profile_errors(profile):
            excluded_profiles.append(dict(participant_id=pid, reason=reason))
        if profile.get("study_phase", "pilot") != "pilot":
            errors.append(dict(participant_id=pid, reason="mixed_study_phase"))
        attested = bool(mapping.get("consent_attestation"))
        if ((profile.get("consent_status") and profile["consent_status"] != "consented")
                or (profile.get("adult_confirmed") and profile["adult_confirmed"] != "1")
                or (not attested and (profile.get("consent_status") != "consented"
                                     or profile.get("adult_confirmed") != "1"))):
            errors.append(dict(participant_id=pid, reason="consent_or_adult_eligibility_unconfirmed"))
        if profile.get("tasks_json"):
            try:
                tasks = json.loads(profile["tasks_json"])
                if not isinstance(tasks, list) or any(not isinstance(task, str) or not task.strip() for task in tasks):
                    raise ValueError
            except (ValueError, TypeError):
                errors.append(dict(participant_id=pid, reason="invalid_tasks_json"))
        for key, value in profile.items():
            if key.startswith("mandatory_") and key.endswith("_not_sure") and value not in ("0", "1"):
                errors.append(dict(participant_id=pid, reason=f"invalid_{key}"))
        if profile.get("survey_group") and profile["survey_group"] not in packet["groups"]:
            errors.append(dict(participant_id=pid, reason="unknown_survey_group"))
    seen = set()
    status_counts, exclusions = Counter(), Counter()
    for index, raw in enumerate(ratings, start=2):
        row = dict(raw)
        pid = row.get("participant_id", "")
        cid = row.get("configuration_id", "")
        location = dict(csv_line=index, participant_id=pid, configuration_id=cid)
        if (pid, cid) in seen:
            errors.append(location | dict(reason="duplicate_participant_card_requires_review"))
        seen.add((pid, cid))
        profile = profiles.get(pid)
        if profile is None:
            errors.append(location | dict(reason="unknown_participant"))
        card = cards.get(cid)
        if card is None:
            unresolved.append(location | dict(reason="no_verified_displayed_card_to_offer_link"))
            continue
        oid = card["offer"]["offer_id"]
        if row.get("offer_id") and row["offer_id"] != oid:
            unresolved.append(location | dict(reason="explicit_offer_conflicts_with_historical_card", offer_id=row["offer_id"]))
            continue
        if row.get("price_usd"):
            try:
                if number(row["price_usd"]) != number(card["offer"]["price_usd"]):
                    raise ValueError
            except ValueError:
                unresolved.append(location | dict(reason="rated_price_conflicts_with_historical_card"))
                continue
        status = mapping["rating_status_values"].get(row.get("rating_status"))
        if status not in ("rated", "skipped", "unable_to_judge", "not_eligible", "unanswered"):
            errors.append(location | dict(reason="unmapped_rating_status"))
            continue
        status_counts[status] += 1
        value = row.get("suitability_rating", "")
        if status == "rated":
            try:
                value = number(value)
                if value is None or not value.is_integer() or not 1 <= value <= 5:
                    raise ValueError
            except ValueError:
                errors.append(location | dict(reason="invalid_genuine_rating"))
                continue
        elif value not in (None, ""):
            errors.append(location | dict(reason="nonrating_status_has_numeric_label"))
            continue
        if profile and profile.get("survey_group") in packet["groups"]:
            allowed = packet["core"] + packet["groups"][profile["survey_group"]]
            if cid not in allowed:
                errors.append(location | dict(reason="card_not_in_assigned_group"))
        reasons = []
        if profile and not profile_errors(profile):
            reasons = eligibility(profile, card)
        if status == "rated":
            exclusions.update(reasons)
        linked.append(dict(participant_id=pid, configuration_id=cid, offer_id=oid,
                           rating_status=status, suitability_rating=value,
                           eligibility_exclusions=reasons,
                           link_basis=card["link_status"]))
    report = dict(status="ready" if not errors and not unresolved and linked else "needs_review",
                  bundle_sha256=fingerprint, mapping_sha256=mapping_hash,
                  catalogue_sha256=sha256(catalogue_path), instrument_version=packet["version"],
                  study_phase="pilot", student_rows=len(students), rating_rows=len(ratings),
                  linked_rows=len(linked), status_counts=dict(status_counts),
                  eligibility_exclusions=dict(exclusions), errors=errors, unresolved_links=unresolved,
                  excluded_profiles=excluded_profiles,
                  consent_basis=mapping.get("consent_attestation", "Explicit consent/adult fields"),
                  unavailable_predictors=["tasks"] if not any(p.get("tasks_json") for p in students) else [],
                  assignment_scope="exact judged cards only; no invented seeds, exposures, timestamps, or assignments",
                  baseline_reproduced=False)
    for name, value in (("students.json", students), ("ratings.json", linked)):
        (destination / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["normalized_sha256"] = {name: sha256(destination / name) for name in ("students.json", "ratings.json")}
    (destination / "validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return destination, report


def load_rows(dataset):
    dataset = private_path(dataset)
    report = json.loads((dataset / "validation.json").read_text(encoding="utf-8"))
    if report["status"] != "ready":
        raise ValueError("Resolve local validation errors and card links before evaluating")
    if sha256(dataset / "catalogue.json") != report["catalogue_sha256"]:
        raise ValueError("Imported catalog was modified")
    for name, digest in report["normalized_sha256"].items():
        if sha256(dataset / name) != digest:
            raise ValueError("Imported participant data was modified; make an audited new import")
    _, cards = load_catalogue(dataset / "catalogue.json")
    profiles = unique_index(json.loads((dataset / "students.json").read_text(encoding="utf-8")), "participant_id")
    rows = []
    excluded = {row["participant_id"] for row in report["excluded_profiles"]}
    for rating in json.loads((dataset / "ratings.json").read_text(encoding="utf-8")):
        profile, card = profiles[rating["participant_id"]], cards[rating["configuration_id"]]
        if (rating["participant_id"] not in excluded and rating["rating_status"] == "rated"
                and not eligibility(profile, card)):
            rows.append(rating | dict(profile=profile, card=card))
    return rows
