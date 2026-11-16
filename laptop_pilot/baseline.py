"""Reproduce the ZIP's budget-only benchmark, including its zero-gain policy."""
from collections import defaultdict
import json
from pathlib import Path
from statistics import mean

from .importer import checked_bundle, csv_member, private_path
from .catalogue import unique_index
from .ranking import ndcg


def reproduce(bundle_path, output):
    output = private_path(output)
    with checked_bundle(bundle_path) as bundle:
        profiles = unique_index(csv_member(bundle, "pilot_profiles.csv", {}), "participant_id")
        cards = unique_index(csv_member(bundle, "pilot_cards.csv", {}), "card_id")
        judgments = csv_member(bundle, "pilot_judgments.csv", {})
        expected = json.loads(bundle.read("price_baseline_results.json"))
    rated, affordable, seen = defaultdict(list), defaultdict(list), set()
    for row in judgments:
        pid, cid = row["participant_id"], row["card_id"]
        if (pid, cid) in seen:
            raise ValueError("Duplicate participant-card judgment")
        seen.add((pid, cid))
        if row["status"] != "rated":
            continue
        rating = int(row["suitability_rating"])
        price, budget = float(cards[cid]["displayed_price_usd"]), float(profiles[pid]["budget_usd"])
        item = price, cid, rating
        rated[pid].append(item)
        if price <= budget:
            affordable[pid].append(item)
    cohorts = {}
    for threshold in (2, 10):
        scores, zero, eligible = [], 0, 0
        for candidates in affordable.values():
            if len(candidates) < threshold:
                continue
            eligible += 1
            values = [item[2] for item in sorted(candidates)]
            if max(values) == 1:
                zero += 1
            else:
                scores.append(ndcg(values, list(range(len(values)))))
        cohorts[str(threshold)] = dict(students_meeting_threshold=eligible,
                                      students_scored=len(scores), students_with_zero_ideal_gain=zero,
                                      mean_student_ndcg_at_5=mean(scores) if scores else None)
    total, within = sum(map(len, rated.values())), sum(map(len, affordable.values()))
    actual = dict(scope="Exploratory ascending price on judged cards, with the budget constraint only",
                  participants_after_deduplication=len(profiles), participants_with_numeric_ratings=len(rated),
                  cards_with_numeric_ratings=len({item[1] for rows in rated.values() for item in rows}),
                  numeric_ratings=total, within_budget_numeric_ratings=within,
                  over_budget_numeric_ratings=total - within, students_with_within_budget_ratings=len(affordable),
                  cohorts_by_minimum_judgment_count=cohorts)
    if actual != expected:
        raise ValueError("Reproduced baseline differs from the ZIP's expected aggregate output")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(matches_original=True, result=actual), indent=2) + "\n", encoding="utf-8")
    return actual
