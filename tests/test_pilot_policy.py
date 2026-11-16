import unittest
from pathlib import Path
import shutil
import tempfile

from scripts.pilot_policy import assess_offer


class OfferFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.policy = dict(intended_freeze_date='2026-10-28', maximum_offer_age_days=7)
        self.offer = dict(offer_id='TEST_OFFER', evidence_id='TEST_SOURCE', observed_date='2026-10-19')
        self.check = dict(offer_id='TEST_OFFER', evidence_id='TEST_SOURCE',
                          second_check_status='passed', second_checked_by='TEST_ONLY',
                          second_checked_at='2026-10-28T22:44:00+07:00', findings='TEST ONLY')

    def test_seven_day_boundary_and_original_date_preserved(self):
        for day, expected in [('21', 'within_window'), ('20', 'needs_fresh_source_check')]:
            with self.subTest(day=day):
                offer = dict(self.offer, observed_date='2026-10-' + day)
                self.assertEqual(assess_offer(offer, [], self.policy)['freshness_status'], expected)
                self.assertEqual(offer['observed_date'], '2026-10-' + day)

    def test_exact_human_recheck_refreshes_without_redating_observation(self):
        result = assess_offer(self.offer, [self.check], self.policy)
        self.assertEqual(result['confirmed_date'], '2026-10-28')
        self.assertEqual(result['freshness_status'], 'within_window')
        self.assertEqual(self.offer['observed_date'], '2026-10-19')

    def test_unrelated_failed_or_future_checks_do_not_refresh(self):
        for change in [dict(offer_id='OTHER'), dict(evidence_id='OTHER'),
                       dict(second_check_status='failed'), dict(findings=''),
                       dict(second_checked_at='2026-10-29T01:00:00+07:00')]:
            with self.subTest(change=change):
                result = assess_offer(self.offer, [dict(self.check, **change)], self.policy)
                self.assertEqual(result['freshness_status'], 'needs_fresh_source_check')

    def test_confirmation_uses_bangkok_calendar_day(self):
        check = dict(self.check, second_checked_at='2026-10-28T18:00:00+00:00')
        self.assertEqual(assess_offer(self.offer, [check], self.policy)['confirmed_date'], '2026-10-19')

    def test_offer_observed_after_freeze_is_not_backdated(self):
        offer = dict(self.offer, observed_date='2026-10-29')
        self.assertEqual(assess_offer(offer, [], self.policy)['freshness_status'], 'after_reference_date')

    def test_moving_freeze_reassesses_window_without_redating_checks(self):
        self.assertEqual(assess_offer(self.offer, [self.check], self.policy, '2026-10-29')['age_days'], 1)
        self.assertEqual(assess_offer(self.offer, [self.check], self.policy, '2026-11-05')['freshness_status'], 'needs_fresh_source_check')

    def test_reported_range_overlapping_cutoff_is_uncertain_not_stale(self):
        attestation = dict(offer_ids=['TEST_OFFER'], earliest_check_date='2026-10-20', latest_check_date='2026-10-28')
        result = assess_offer(self.offer, [], self.policy, '2026-10-29', attestation)
        self.assertEqual(result['freshness_status'], 'check_date_uncertain')
        self.assertEqual(result['confirmed_date'], '')
        self.assertEqual(assess_offer(self.offer, [self.check], self.policy, '2026-10-29', attestation)['confirmed_date'], '2026-10-28')

    def test_reported_range_is_scoped_and_must_fit_window_to_pass(self):
        attestation = dict(offer_ids=['TEST_OFFER'], earliest_check_date='2026-10-22', latest_check_date='2026-10-28')
        self.assertEqual(assess_offer(self.offer, [], self.policy, '2026-10-29', attestation)['freshness_status'], 'within_window')
        attestation['offer_ids'] = ['ANOTHER_OFFER']
        self.assertEqual(assess_offer(self.offer, [], self.policy, '2026-10-29', attestation)['freshness_status'], 'needs_fresh_source_check')

    def test_readiness_and_preview_work_without_private_evidence_on_a_new_clone(self):
        from scripts.prepare_pilot import prepare
        from scripts.prepare_pilot_preview import build_packet
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            clean = Path(temporary)
            for name in ('data', 'config'):
                shutil.copytree(root / name, clean / name)
            before = {p.name: p.read_bytes() for p in (clean / 'data').glob('*.csv')}
            packet = build_packet(clean)
            self.assertEqual(len(packet['cards']), 51)
            report = prepare(clean, clean / 'readiness', '2026-11-16')
            self.assertIsNone(report['user_reported_check_window'])
            self.assertEqual(report['freshness_assessment']['configurations_with_fresh_offers'], 0)
            self.assertEqual(before, {p.name: p.read_bytes() for p in (clean / 'data').glob('*.csv')})


if __name__ == '__main__':
    unittest.main()
