"""Artificial fixtures only. Never write synthetic rows to the research data."""
import copy
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

try:
    import numpy as np
    from sklearn.metrics import ndcg_score
except ImportError:
    raise unittest.SkipTest("Install requirements-pilot.txt to run the optional ML integration tests")

from laptop_pilot.catalogue import load_catalogue
from laptop_pilot.evaluation import frozen_split, score_rows
from laptop_pilot.features import FoldPreprocessor, features
from laptop_pilot.importer import checked_bundle, import_bundle, load_rows, private_path
from laptop_pilot.privacy import blocked_blob
from laptop_pilot.ranking import content_score, eligibility, ndcg, profile_errors, rank, student_weights

ROOT = Path(__file__).resolve().parents[1]


def profile():
    return dict(participant_id="ARTIFICIAL_TEST_ONLY", budget_usd="1000", min_ram_gb="8",
                min_storage_gb="256", max_weight_kg="", required_gpu_type="",
                desired_ram_gb="16", desired_storage_gb="512", desired_max_weight_kg="2",
                preferred_screen_inches="14", preferred_gpu_type="integrated",
                **{"importance_" + key: "1" for key in ("savings", "ram", "storage", "weight", "screen", "gpu")})


def card():
    return dict(configuration_id="LAP_TEST", link_status="verified_exact_export_and_display_reference",
                hardware=dict(configuration_id="LAP_TEST", record_status="verified", cpu_model="TEST_CPU",
                              gpu_model="TEST_GPU", gpu_type="integrated", ram_gb="16", storage_gb="512",
                              storage_type="ssd", screen_inches="14", weight_kg="", gpu_vram_gb="", refresh_hz=""),
                offer=dict(offer_id="OFF_TEST", configuration_id="LAP_TEST", offer_status="verified",
                           price_usd="500", currency="USD", condition="new", purchase_type="outright"))


def row(pid="ARTIFICIAL_TEST_ONLY", rating=3):
    return dict(participant_id=pid, configuration_id="LAP_TEST", profile=profile(), card=card(),
                suitability_rating=rating)


class RankingTests(unittest.TestCase):
    def test_budget_and_hardware_boundaries_and_unknown_required_property(self):
        p, c = profile(), card()
        p.update(budget_usd="500", min_ram_gb="16", min_storage_gb="512")
        self.assertEqual(eligibility(p, c), [])
        p["budget_usd"] = "499.99"
        self.assertIn("over_budget", eligibility(p, c))
        p.update(budget_usd="1000", max_weight_kg="2")
        self.assertIn("fails_max_weight_kg", eligibility(p, c))
        p.update(max_weight_kg="", required_gpu_type="dedicated")
        self.assertIn("fails_required_gpu_type", eligibility(p, c))

    def test_stock_and_delivered_os_do_not_filter_pilot(self):
        c = card()
        c["offer"].update(availability_text="Out of Stock", delivered_os="DOS")
        self.assertEqual(eligibility(profile(), c), [])

    def test_content_keeps_missing_attribute_weight_in_denominator(self):
        self.assertAlmostEqual(content_score(profile(), card()), (0.5 + 1 + 1 + 0 + 1 + 1) / 6)
        p = profile()
        p.update({"importance_" + pref: "0" for pref in ("savings", "ram", "storage", "weight", "screen", "gpu")})
        self.assertEqual(content_score(p, card()), 0)
        self.assertEqual(rank([row(), dict(row(), configuration_id="LAP_A")], [0, 0]), [1, 0])

    def test_active_missing_target_is_flagged_without_imputation(self):
        p = profile()
        p["desired_ram_gb"] = ""
        self.assertIn("missing_active_target_ram", profile_errors(p))
        p["importance_ram"] = "0"
        self.assertEqual(profile_errors(p), [])

    def test_linear_ndcg_matches_sklearn_after_deterministic_ties(self):
        ratings = np.array([5, 2, 1, 4, 3, 5])
        order = [3, 5, 0, 4, 2, 1]
        scores = np.zeros(len(order))
        for position, index in enumerate(order):
            scores[index] = len(order) - position
        self.assertAlmostEqual(ndcg(ratings, order), ndcg_score([ratings - 1], [scores], k=5, ignore_ties=True))
        self.assertEqual(ndcg([1, 1], [0, 1]), 0)

    def test_balanced_weights_and_student_macro_averaging(self):
        rows = [row("TEST_A", 5), row("TEST_A", 1), row("TEST_B", 5)]
        weights = student_weights(rows)
        self.assertAlmostEqual(sum(weights[:2]), weights[2])
        self.assertAlmostEqual(sum(weights) / len(weights), 1)
        metrics = score_rows(rows, [2, 1, 0])
        self.assertEqual(set(metrics), {"TEST_A", "TEST_B"})
        self.assertIsNone(metrics["TEST_B"]["precision_at_5"])


class LeakageTests(unittest.TestCase):
    def test_fold_local_imputation_scaling_unknown_categories_and_no_identifiers(self):
        training = [row(), row()]
        training[1]["card"]["offer"]["price_usd"] = "700"
        pre = FoldPreprocessor(scale=True).fit(training)
        test = row("HELD_OUT_TEST_ONLY")
        test["card"]["offer"]["price_usd"] = "9000"
        test["card"]["hardware"].update(cpu_model="UNSEEN_CPU", weight_kg="99")
        result = pre.transform([test])
        self.assertEqual(pre.medians[pre.numeric_keys.index("price")], 600)
        self.assertEqual(pre.medians[pre.numeric_keys.index("hardware_weight_kg")], 0)
        self.assertTrue(np.isfinite(result).all())
        self.assertFalse(any("participant_id" in key or "offer_id" in key or "retailer" in key for key in pre.feature_names))
        before = features(training[0])
        changed = copy.deepcopy(training[0])
        changed.update(participant_id="NEW_ID", configuration_id="NEW_ID", suitability_rating=1)
        changed["card"]["offer"].update(offer_id="NEW_ID", retailer="NEW_SHOP", source_url="https://example.invalid")
        self.assertEqual(before, features(changed))

    def test_student_held_out_and_grouped_folds(self):
        rows = [row(f"ARTIFICIAL_{pid}") for pid in range(10) for _ in range(3)]
        dev, test, folds, manifest = frozen_split(rows)
        self.assertFalse(set(manifest["development_students"]) & set(manifest["test_students"]))
        self.assertEqual(len(folds), 5)
        self.assertEqual(len(dev) + len(test), len(rows))
        for fold in manifest["folds"]:
            self.assertFalse(set(fold["training_students"]) & set(fold["validation_students"]))


class ImportPrivacyTests(unittest.TestCase):
    def make_bundle(self, root, offer="", price="500", extra_card=False):
        root = Path(root)
        mapping = dict(students_member="profiles.csv", ratings_member="judgments.csv", cards_member="cards.csv",
                       students_columns={}, ratings_columns={}, study_phase="pilot", instrument_version="TEST_ONLY",
                       consent_attestation="Artificial fixture, never a research response",
                       rating_status_values={"rated": "rated", "skipped": "skipped"})
        catalogue = dict(version="TEST_ONLY", core=["LAP_TEST"], groups={}, cards=[card()])
        (root / "map.json").write_text(json.dumps(mapping), encoding="utf-8")
        (root / "catalogue.json").write_text(json.dumps(catalogue), encoding="utf-8")
        def csv_text(rows):
            stream = io.StringIO(newline="")
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
            return stream.getvalue()
        with zipfile.ZipFile(root / "fixture.zip", "w") as bundle:
            bundle.writestr("README.md", "ARTIFICIAL SOFTWARE TEST ONLY")
            bundle.writestr("profiles.csv", csv_text([profile()]))
            bundle.writestr("judgments.csv", csv_text([dict(participant_id="ARTIFICIAL_TEST_ONLY", configuration_id="LAP_TEST",
                offer_id=offer, rating_status="rated", suitability_rating="4")]))
            bundle.writestr("cards.csv", csv_text([dict(card_id="MISSING_TEST" if extra_card else "LAP_TEST", displayed_price_usd=price)]))
        return root / "fixture.zip", root / "map.json", root / "catalogue.json"

    def test_exact_import_tampering_and_unresolved_links(self):
        for offer, price, missing, expected in (("", "500", False, "ready"), ("WRONG_OFFER", "500", False, "needs_review"),
                                                ("", "501", False, "needs_review"), ("", "500", True, "needs_review")):
            with self.subTest(offer=offer, price=price, missing=missing), tempfile.TemporaryDirectory() as tmp:
                args = self.make_bundle(tmp, offer, price, missing)
                with patch("laptop_pilot.importer.ROOT", Path(tmp)):
                    destination, report = import_bundle(*args)
                    self.assertEqual(report["status"], expected)
                    if expected == "ready":
                        self.assertEqual(len(load_rows(destination)), 1)
                        (destination / "ratings.json").write_text("[]", encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_rows(destination)

    def test_unsafe_archive_and_nonprivate_output_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "unsafe.zip"
            with zipfile.ZipFile(path, "w") as bundle:
                bundle.writestr("../escape.csv", "ARTIFICIAL")
            with self.assertRaises(ValueError):
                checked_bundle(path)
            with self.assertRaises(ValueError):
                private_path(Path(tmp) / "human-data.json")

    def test_force_added_human_data_is_blocked_but_header_only_templates_are_allowed(self):
        for path, content in (("data/students.csv", b"participant_id,budget_usd\nTEST,500\n"),
                              ("private/any.json", b"{}"), ("ITM360_Laptop_Pilot.zip", b"zip"),
                              ("renamed_export.csv", b"participant_id,status\nTEST,rated\n")):
            self.assertTrue(blocked_blob(path, content))
        self.assertFalse(blocked_blob("data/students.csv", b"participant_id,budget_usd\n"))
        self.assertFalse(blocked_blob("config/pilot_import.json", b"{}"))

    def test_recovered_catalogue_has_only_verified_exact_links(self):
        packet, cards = load_catalogue(ROOT / "data/pilot_catalogue.json")
        self.assertEqual(len(cards), 51)
        self.assertNotIn("LAP0003", cards)
        self.assertNotIn("LAP0006", cards)
        self.assertEqual(set(packet["core"] + sum(packet["groups"].values(), [])), set(cards))


if __name__ == "__main__":
    unittest.main()
