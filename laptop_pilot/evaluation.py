"""Student-held-out comparison. No participant identifiers leave private/."""
from collections import defaultdict
from itertools import product
import json
import os
from pathlib import Path
import platform
from statistics import mean, median
import sys

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
import sklearn

from .catalogue import sha256
from .features import FoldPreprocessor
from .importer import load_rows, private_path
from .ranking import content_score, ndcg, number, rank, student_weights

SEED = 42
METHODS = ("ascending_price", "weighted_content", "random_forest", "small_mlp")


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def by_student(rows):
    result = defaultdict(list)
    for row in rows:
        result[row["participant_id"]].append(row)
    return result


def score_rows(rows, scores, predicted_ratings=False):
    groups = defaultdict(list)
    for i, row in enumerate(rows):
        groups[row["participant_id"]].append(i)
    result = {}
    for pid, indices in groups.items():
        selected = [rows[i] for i in indices]
        prediction = [float(scores[i]) for i in indices]
        if not all(np.isfinite(prediction)):
            raise ValueError("Ranker produced a nonfinite score")
        order = rank(selected, prediction)
        ratings = [float(row["suitability_rating"]) for row in selected]
        k = min(5, len(order))
        result[pid] = dict(ndcg_at_5=ndcg(ratings, order), candidate_count=len(order),
                           precision_at_available_k=sum(ratings[i] >= 4 for i in order[:k]) / k,
                           precision_at_5=(sum(ratings[i] >= 4 for i in order[:5]) / 5 if len(order) >= 5 else None),
                           mae=(mean(abs(a - b) for a, b in zip(ratings, prediction)) if predicted_ratings else None))
    return result


def summarize(metrics):
    result = dict(students=len(metrics))
    for key in ("ndcg_at_5", "precision_at_5", "precision_at_available_k", "mae"):
        values = [row[key] for row in metrics.values() if row[key] is not None]
        result[key] = mean(values) if values else None
        result[key + "_students"] = len(values)
    return result


def deterministic_scores(rows, method):
    if method == "ascending_price":
        return [-number(row["card"]["offer"]["price_usd"]) for row in rows]
    return [content_score(row["profile"], row["card"]) for row in rows]


def frozen_split(rows):
    groups = np.array([row["participant_id"] for row in rows])
    if len(set(groups)) < 7:
        raise ValueError("At least seven cohort students are required for 20% holdout and five development folds")
    dev, test = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED).split(rows, groups=groups))
    if len(set(groups[dev])) < 5:
        raise ValueError("Fewer than five development students")
    folds = list(GroupKFold(n_splits=5).split(dev, groups=groups[dev]))
    manifest = dict(seed=SEED, test_fraction=0.2, development_students=sorted(set(groups[dev])),
                    test_students=sorted(set(groups[test])), folds=[])
    for train, valid in folds:
        train_ids, valid_ids = set(groups[dev][train]), set(groups[dev][valid])
        assert not train_ids & valid_ids and not (train_ids | valid_ids) & set(groups[test])
        manifest["folds"].append(dict(training_students=sorted(train_ids), validation_students=sorted(valid_ids)))
    return dev, test, folds, manifest


def forest_model(params):
    return RandomForestRegressor(n_estimators=310, criterion="squared_error", bootstrap=True,
                                 random_state=SEED, n_jobs=1, **params)


def train_forest(dev_rows, folds, output):
    cache = []
    for train, valid in folds:
        training = [dev_rows[i] for i in train]
        validation = [dev_rows[i] for i in valid]
        pre = FoldPreprocessor().fit(training)
        cache.append((training, validation, pre.transform(training), pre.transform(validation)))
    trials = []
    for depth, leaf, maximum in product((4, 8, None), (3, 5, 10), (0.5, 1.0)):
        params = dict(max_depth=depth, min_samples_leaf=leaf, max_features=maximum)
        metrics = {}
        for training, validation, x_train, x_valid in cache:
            model = forest_model(params)
            model.fit(x_train, [r["suitability_rating"] for r in training], sample_weight=student_weights(training))
            metrics.update(score_rows(validation, model.predict(x_valid), True))
        trials.append(dict(parameters=params, summary=summarize(metrics), student_metrics=metrics))
    best = min(trials, key=lambda trial: (-trial["summary"]["ndcg_at_5"],
               trial["parameters"]["max_depth"] or float("inf"),
               -trial["parameters"]["min_samples_leaf"], trial["parameters"]["max_features"]))
    dump(output / "forest_search.json", trials)
    pre = FoldPreprocessor().fit(dev_rows)
    model = forest_model(best["parameters"])
    model.fit(pre.transform(dev_rows), [r["suitability_rating"] for r in dev_rows], sample_weight=student_weights(dev_rows))
    joblib.dump(dict(preprocessor=pre, model=model), output / "forest.joblib")
    return pre, model, best


def tensorflow():
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
    import tensorflow as tf
    tf.config.threading.set_intra_op_parallelism_threads(1)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.experimental.enable_op_determinism()
    return tf


def make_mlp(tf, width):
    tf.keras.backend.clear_session()
    tf.keras.utils.set_random_seed(SEED)
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(width,)), tf.keras.layers.Dense(33, activation="relu"),
        tf.keras.layers.Dropout(0.2), tf.keras.layers.Dense(16, activation="relu"), tf.keras.layers.Dense(1),
    ])
    model.compile(optimizer=tf.keras.optimizers.AdamW(learning_rate=0.001, weight_decay=0.0001), loss="mse")
    return model


def regression_metrics(model, x, y, weights):
    # Direct inference disables dropout for comparable fit-gap histories.
    predicted = model(x, training=False).numpy().reshape(-1)
    return dict(mse=float(np.average((predicted - y) ** 2, weights=weights)),
                mae=float(np.average(np.abs(predicted - y), weights=weights)))


def fit_mlp(tf, training, validation=None, epochs=150):
    pre = FoldPreprocessor(scale=True).fit(training)
    x = pre.transform(training)
    y = np.array([r["suitability_rating"] for r in training], dtype=np.float32)
    weights = np.array(student_weights(training), dtype=np.float32)
    if validation:
        vx = pre.transform(validation)
        vy = np.array([r["suitability_rating"] for r in validation], dtype=np.float32)
        vw = np.array(student_weights(validation), dtype=np.float32)
    model = make_mlp(tf, x.shape[1])
    rng = np.random.default_rng(SEED)
    best_loss, best_epoch, best_weights, stale, history = float("inf"), 0, None, 0, []
    for epoch in range(1, epochs + 1):
        order = rng.permutation(len(training))
        for start in range(0, len(order), 16):
            indices = order[start:start + 16]
            model.train_on_batch(x[indices], y[indices], sample_weight=weights[indices])
        record = dict(epoch=epoch, training=regression_metrics(model, x, y, weights))
        if validation:
            record["validation"] = regression_metrics(model, vx, vy, vw)
            loss = record["validation"]["mse"]
            if loss < best_loss:
                best_loss, best_epoch, best_weights, stale = loss, epoch, model.get_weights(), 0
            else:
                stale += 1
        history.append(record)
        if validation and stale >= 10:
            break
    if validation:
        model.set_weights(best_weights)
    else:
        best_epoch = epochs
    return pre, model, history, best_epoch


def train_mlp(tf, dev_rows, folds, output):
    metrics, best_epochs = {}, []
    for index, (train, valid) in enumerate(folds, start=1):
        training, validation = [dev_rows[i] for i in train], [dev_rows[i] for i in valid]
        pre, model, history, best_epoch = fit_mlp(tf, training, validation)
        scores = model(pre.transform(validation), training=False).numpy().reshape(-1)
        metrics.update(score_rows(validation, scores, True))
        best_epochs.append(best_epoch)
        dump(output / f"mlp_fold_{index}_history.json", dict(best_epoch=best_epoch, epochs=history))
    epochs = int(median(best_epochs))
    pre, model, history, _ = fit_mlp(tf, dev_rows, epochs=epochs)
    model.save(output / "mlp.keras")
    joblib.dump(pre, output / "mlp_preprocessor.joblib")
    dump(output / "mlp_refit_history.json", dict(epochs=epochs, history=history))
    return pre, model, dict(summary=summarize(metrics), student_metrics=metrics,
                            fold_best_epochs=best_epochs, refit_epochs=epochs)


def paired_intervals(metrics):
    rng = np.random.default_rng(SEED)
    students = sorted(metrics["ascending_price"])
    result = {}
    for left, right in (("random_forest", "weighted_content"), ("small_mlp", "weighted_content"),
                        ("small_mlp", "random_forest")):
        delta = np.array([metrics[left][pid]["ndcg_at_5"] - metrics[right][pid]["ndcg_at_5"] for pid in students])
        samples = rng.choice(delta, size=(2000, len(delta)), replace=True).mean(axis=1)
        result[left + "_minus_" + right] = dict(mean_delta=float(delta.mean()),
            exploratory_95_percent_interval=np.quantile(samples, [0.025, 0.975]).tolist(), student_resamples=2000)
    return result


def evaluate(dataset, minimum=10):
    if minimum not in (2, 10):
        raise ValueError("Use the locked primary threshold 10 or the explicitly exploratory threshold 2")
    dataset = private_path(dataset)
    rows = sorted(load_rows(dataset), key=lambda row: (row["participant_id"], row["configuration_id"]))
    grouped = by_student(rows)
    cohort = {pid for pid, values in grouped.items() if len(values) >= minimum}
    selected = [row for row in rows if row["participant_id"] in cohort]
    output = dataset / f"evaluation_min{minimum}"
    if output.exists():
        raise ValueError("Evaluation output already exists; preserve the locked result")
    output.mkdir()
    validation = json.loads((dataset / "validation.json").read_text(encoding="utf-8"))
    report = dict(status="unavailable", scope="primary" if minimum == 10 else "exploratory_small_judged_sets",
                  minimum_eligible_judgments=minimum, cohort_students=len(cohort), cohort_ratings=len(selected),
                  eligible_numeric_judgments=len(rows), valid_profiles_with_eligible_ratings=len(grouped),
                  excluded_profiles=len({r["participant_id"] for r in validation["excluded_profiles"]}),
                  primary_cohort_students=sum(len(values) >= 10 for values in grouped.values()),
                  zero_ideal_gain_policy="NDCG is zero, included in mean (locked proposal); ZIP reproduction preserves its separate exclusion policy",
                  unavailable_predictors=validation["unavailable_predictors"],
                  seed=SEED, models_trained=False,
                  input_sha256={name: sha256(dataset / name) for name in ("students.json", "ratings.json", "catalogue.json", "validation.json")},
                  module_sha256={p.name: sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))})
    dump(output / "candidate_counts.json", {pid: len(values) for pid, values in grouped.items()})
    if len(cohort) < 7:
        report["reason"] = "No sufficient cohort for 20% student holdout plus five-fold grouped development validation"
        dump(output / "report.json", report)
        return report
    dev, test, folds, manifest = frozen_split(selected)
    dump(output / "split_manifest.json", manifest)
    # Split is saved before any fit or held-out label inspection.
    dev_rows, test_rows = [selected[i] for i in dev], [selected[i] for i in test]
    tf = tensorflow()
    forest_pre, forest, forest_best = train_forest(dev_rows, folds, output)
    mlp_pre, mlp, mlp_development = train_mlp(tf, dev_rows, folds, output)
    development = {method: score_rows(dev_rows, deterministic_scores(dev_rows, method)) for method in METHODS[:2]}
    development["random_forest"] = forest_best["student_metrics"]
    development["small_mlp"] = mlp_development["student_metrics"]
    default = ("random_forest" if forest_best["summary"]["ndcg_at_5"] >= mlp_development["summary"]["ndcg_at_5"] else "small_mlp")
    dump(output / "development_selection.json", dict(default_learned_ranker=default,
         forest_parameters=forest_best["parameters"], mlp_refit_epochs=mlp_development["refit_epochs"]))
    # The held-out group is scored only after model/settings selection.
    predictions = {method: deterministic_scores(test_rows, method) for method in METHODS[:2]}
    predictions["random_forest"] = forest.predict(forest_pre.transform(test_rows))
    predictions["small_mlp"] = mlp(mlp_pre.transform(test_rows), training=False).numpy().reshape(-1)
    metrics = {method: score_rows(test_rows, predictions[method], method in METHODS[2:]) for method in METHODS}
    dump(output / "student_metrics.json", dict(development=development, held_out=metrics))
    dump(output / "held_out_predictions.json", [dict(participant_id=row["participant_id"],
         configuration_id=row["configuration_id"], offer_id=row["offer_id"], rating=row["suitability_rating"],
         scores={method: float(predictions[method][i]) for method in METHODS}) for i, row in enumerate(test_rows)])
    report.update(status="complete", models_trained=True, development_students=len(manifest["development_students"]),
                  held_out_students=len(manifest["test_students"]), development_ratings=len(dev_rows), held_out_ratings=len(test_rows),
                  development_selection_scores={method: summarize(value) for method, value in development.items()},
                  held_out_scores={method: summarize(value) for method, value in metrics.items()},
                  paired_ndcg_differences=paired_intervals(metrics), default_learned_ranker=default,
                  forest_selected_parameters=forest_best["parameters"], mlp_fold_best_epochs=mlp_development["fold_best_epochs"],
                  mlp_refit_epochs=mlp_development["refit_epochs"],
                  python=sys.version, platform=platform.platform(), numpy=np.__version__, sklearn=sklearn.__version__, tensorflow=tf.__version__,
                  limitations=["Pilot only; no claim of main-study performance or a usable production model.",
                              "Development scores are used for selection, not an independent estimate.",
                              "Evaluates only genuinely rated eligible historical cards, not unrated catalogue items.",
                              "The exported profiles omit task answers; no task labels were reconstructed.",
                              "Very small held-out sample; paired intervals are exploratory.",
                              "No primary result exists unless students have at least ten eligible judgments."])
    dump(output / "report.json", report)
    return report
