"""Explicit feature allowlist and training-fold-only fitting."""
import json
import numpy as np
from sklearn.feature_extraction import DictVectorizer

from .ranking import PREFERENCES, matches, number

STUDENT_NUMERIC = (
    "budget_usd", "min_ram_gb", "min_storage_gb", "max_weight_kg", "desired_ram_gb",
    "desired_storage_gb", "desired_max_weight_kg", "preferred_screen_inches",
) + tuple("importance_" + pref for pref in PREFERENCES)
HARDWARE_NUMERIC = ("ram_gb", "storage_gb", "screen_inches", "weight_kg", "gpu_vram_gb", "refresh_hz")
TASKS = ("Documents/presentations", "Web/research", "Online classes", "Coding", "Data analysis",
         "Graphic design/photo editing", "3D modelling/rendering", "Video editing", "Engineering/CAD", "Games")


def features(row):
    p, h, o = row["profile"], row["card"]["hardware"], row["card"]["offer"]
    numeric = {"student_" + key: number(p.get(key)) for key in STUDENT_NUMERIC}
    numeric.update({"hardware_" + key: number(h.get(key)) for key in HARDWARE_NUMERIC})
    price, budget = number(o["price_usd"]), number(p["budget_usd"])
    numeric.update(price=price, price_budget_ratio=price / budget, budget_remaining=budget - price)
    for attr, target in (("ram_gb", "desired_ram_gb"), ("storage_gb", "desired_storage_gb"),
                         ("weight_kg", "desired_max_weight_kg")):
        actual, desired = number(h.get(attr)), number(p.get(target))
        numeric["ratio_" + attr] = actual / desired if actual is not None and desired else None
    actual, desired = number(h.get("screen_inches")), number(p.get("preferred_screen_inches"))
    numeric["screen_difference"] = abs(actual - desired) if actual is not None and desired else None
    numeric.update({"match_" + key: value for key, value in matches(p, row["card"]).items()})
    nominal = {"cpu_model": h.get("cpu_model") or "unknown", "gpu_model": h.get("gpu_model") or "unknown",
               "gpu_type": h.get("gpu_type") or "unknown", "storage_type": h.get("storage_type") or "unknown",
               "required_gpu_type": p.get("required_gpu_type") or "unknown",
               "preferred_gpu_type": p.get("preferred_gpu_type") or "unknown"}
    tasks = json.loads(p["tasks_json"]) if p.get("tasks_json") else []
    binary = {"task_" + task: float(task in tasks) for task in TASKS}
    binary["tasks_unavailable"] = float(not p.get("tasks_json"))
    binary["task_other"] = float(any(task not in TASKS for task in tasks))
    for key in ("mandatory_budget_not_sure", "mandatory_ram_not_sure", "mandatory_storage_not_sure",
                "mandatory_weight_not_sure", "mandatory_gpu_not_sure"):
        binary[key] = float(p.get(key) == "1")
    return numeric, nominal, binary


class FoldPreprocessor:
    """Median fallback 0 for all-missing columns; binaries remain unscaled."""
    def __init__(self, scale=False):
        self.scale = scale

    def fit(self, rows):
        extracted = [features(row) for row in rows]
        self.numeric_keys = sorted(extracted[0][0])
        matrix = np.array([[value[0][key] if value[0][key] is not None else np.nan
                            for key in self.numeric_keys] for value in extracted], dtype=float)
        self.medians = np.array([np.median(column[np.isfinite(column)]) if np.isfinite(column).any() else 0.0
                                 for column in matrix.T])
        imputed = np.where(np.isnan(matrix), self.medians, matrix)
        self.means = imputed.mean(axis=0) if self.scale else np.zeros(matrix.shape[1])
        self.scales = imputed.std(axis=0) if self.scale else np.ones(matrix.shape[1])
        self.scales[self.scales == 0] = 1.0
        self.encoder = DictVectorizer(sparse=False)
        self.encoder.fit([nominal | binary for _, nominal, binary in extracted])
        self.feature_names = (self.numeric_keys + ["missing_" + key for key in self.numeric_keys]
                              + self.encoder.get_feature_names_out().tolist())
        return self

    def transform(self, rows):
        extracted = [features(row) for row in rows]
        matrix = np.array([[value[0][key] if value[0][key] is not None else np.nan
                            for key in self.numeric_keys] for value in extracted], dtype=float)
        missing = np.isnan(matrix)
        imputed = np.where(missing, self.medians, matrix)
        encoded = self.encoder.transform([nominal | binary for _, nominal, binary in extracted])
        return np.hstack(((imputed - self.means) / self.scales, missing.astype(float), encoded)).astype(np.float32)
