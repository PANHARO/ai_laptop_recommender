"""Shared hard constraints, locked proposal matching values, and linear NDCG."""
from collections import Counter
import math

PREFERENCES = {
    "savings": "budget_usd", "ram": "desired_ram_gb", "storage": "desired_storage_gb",
    "weight": "desired_max_weight_kg", "screen": "preferred_screen_inches",
    "gpu": "preferred_gpu_type",
}


def number(value):
    if value in (None, ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError("Expected a finite number") from None
    if not math.isfinite(result):
        raise ValueError("Expected a finite number")
    return result


def profile_errors(profile):
    errors = []
    for key in ("budget_usd", "min_ram_gb", "min_storage_gb", "max_weight_kg",
                "desired_ram_gb", "desired_storage_gb", "desired_max_weight_kg", "preferred_screen_inches"):
        try:
            value = number(profile.get(key))
            if (key == "budget_usd" and value is None) or (value is not None and value <= 0):
                errors.append(f"invalid_{key}")
        except ValueError:
            errors.append(f"invalid_{key}")
    for key in ("required_gpu_type", "preferred_gpu_type"):
        if profile.get(key, "") not in ("", "integrated", "dedicated"):
            errors.append(f"invalid_{key}")
    for pref, target in PREFERENCES.items():
        try:
            weight = number(profile.get(f"importance_{pref}"))
            if weight is None or not 0 <= weight <= 5 or not weight.is_integer():
                errors.append(f"invalid_importance_{pref}")
            elif weight > 0 and profile.get(target) in (None, ""):
                errors.append(f"missing_active_target_{pref}")
        except ValueError:
            errors.append(f"invalid_importance_{pref}")
    if profile.get("required_os"):
        errors.append("required_os_conflicts_with_pilot_no_os_filter")
    return errors


def eligibility(profile, card):
    """Unknown required values fail. Stock and OS do not filter the pilot."""
    h, o = card["hardware"], card["offer"]
    reasons = []
    if number(o["price_usd"]) > number(profile["budget_usd"]):
        reasons.append("over_budget")
    for requirement, attr, minimum in (("min_ram_gb", "ram_gb", True),
                                        ("min_storage_gb", "storage_gb", True),
                                        ("max_weight_kg", "weight_kg", False)):
        target = number(profile.get(requirement))
        actual = number(h.get(attr))
        if target is not None and (actual is None or (actual < target if minimum else actual > target)):
            reasons.append(f"fails_{requirement}")
    target = profile.get("required_gpu_type")
    if target and target != h.get("gpu_type"):
        reasons.append("fails_required_gpu_type")
    return reasons


def matches(profile, card):
    h, o = card["hardware"], card["offer"]
    values = dict(savings=max(0.0, 1 - number(o["price_usd"]) / number(profile["budget_usd"])))
    for pref, attr in (("ram", "ram_gb"), ("storage", "storage_gb"), ("weight", "weight_kg")):
        actual, target = number(h.get(attr)), number(profile.get(PREFERENCES[pref]))
        values[pref] = (min(1.0, target / actual if pref == "weight" else actual / target)
                        if actual and target else 0.0)
    actual, target = number(h.get("screen_inches")), number(profile.get("preferred_screen_inches"))
    values["screen"] = max(0.0, 1 - abs(actual - target) / 3) if actual and target else 0.0
    target = profile.get("preferred_gpu_type")
    values["gpu"] = float(bool(target) and target == h.get("gpu_type"))
    return values


def content_score(profile, card):
    values = matches(profile, card)
    weights = {key: number(profile[f"importance_{key}"]) for key in PREFERENCES}
    total = sum(weights.values())
    return sum(weights[key] * values[key] for key in weights) / total if total else 0.0


def rank(rows, scores):
    """All methods use exactly the same deterministic price/ID tiebreak."""
    return sorted(range(len(rows)), key=lambda i: (-float(scores[i]),
                  number(rows[i]["card"]["offer"]["price_usd"]), rows[i]["configuration_id"]))


def ndcg(ratings, order, k=5):
    gains = [float(value) - 1 for value in ratings]
    if any(not 0 <= gain <= 4 for gain in gains):
        raise ValueError("NDCG expects suitability ratings in 1..5")
    def dcg(values):
        return sum(gain / math.log2(position + 2) for position, gain in enumerate(values[:k]))
    ideal = dcg(sorted(gains, reverse=True))
    return dcg([gains[i] for i in order]) / ideal if ideal else 0.0


def student_weights(rows):
    counts = Counter(row["participant_id"] for row in rows)
    return [len(rows) / (len(counts) * counts[row["participant_id"]]) for row in rows]
