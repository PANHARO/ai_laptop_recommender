#!/usr/bin/env python3
"""Focused integrity checks. All artificial human records exist only in temp dirs."""
import csv
from pathlib import Path
import shutil
import tempfile
import unittest

from validate_data import ROOT, validate


def read(root, name):
    with (root / 'data' / f'{name}.csv').open(encoding='utf-8', newline='') as f:
        r = csv.DictReader(f)
        return r.fieldnames, list(r)


def write(root, name, rows):
    headers, _ = read(root, name)
    with (root / 'data' / f'{name}.csv').open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        w.writerows(rows)


class IntegrityChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / 'data', self.root / 'data')
        shutil.copytree(ROOT / 'config', self.root / 'config')

    def tearDown(self):
        self.temp.cleanup()

    def errors(self):
        return '\n'.join(validate(self.root)['errors'])

    def synthetic_response(self):
        """Make one structurally valid artificial response, never saved to project data."""
        _, rows = read(self.root, 'source_checks')
        rows[0].update(source_check_status='checked', checked_by='SYNTHETIC_TEST', checked_at='2026-09-28T10:00:00+07:00', facts_observed='SYNTHETIC TEST ONLY: new condition and hardware verified')
        write(self.root, 'source_checks', rows)
        _, rows = read(self.root, 'laptops')
        rows[0]['record_status'] = 'verified'
        write(self.root, 'laptops', rows)
        _, rows = read(self.root, 'offers')
        rows[0].update(offer_status='verified', condition='new', condition_evidence_id='SRC0001')
        write(self.root, 'offers', rows)
        s = dict(participant_id='SYNTHETIC_ONLY', study_phase='pilot', protocol_version='fixture_v1', consent_status='consented', adult_confirmed='1', profile_recorded_at='2026-09-28T10:00:00+07:00', budget_usd='1000', tasks_json='["synthetic_fixture"]')
        for name in ['savings','ram','storage','weight','screen','gpu']:
            s['importance_' + name] = '0'
        write(self.root, 'students', [s])
        a = dict(assignment_id='SYNTHETIC_ASSIGNMENT', participant_id='SYNTHETIC_ONLY', configuration_id='LAP0001', offer_id='OFF0001', snapshot_version='collection_2026-09-28_v0', protocol_version='fixture_v1', price_budget_band='gt_0.60_le_0.80', selection_seed='42', exposure_count_before='0', display_order='1', assigned_at='2026-09-28T10:01:00+07:00', card_version='synthetic_fixture')
        write(self.root, 'assignments', [a])
        r = {k:a[k] for k in ['assignment_id','participant_id','configuration_id','offer_id','snapshot_version','display_order']}
        r.update(rating_id='SYNTHETIC_RESPONSE', rating_status='rated', suitability_rating='3', rated_at='2026-09-28T10:02:00+07:00', comment='SYNTHETIC TEST ONLY')
        write(self.root, 'ratings', [r])
        self.assertEqual(self.errors(), '')

    def test_starter_structure(self):
        result = validate(self.root)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['verified_configurations'], 0)
        self.assertEqual(result['counts']['ratings'], 0)

    def test_zero_and_nonfinite_prices(self):
        _, rows = read(self.root, 'offers')
        for bad in ('0', 'NaN', 'Infinity'):
            with self.subTest(price=bad):
                rows[0]['price_usd'] = bad
                write(self.root, 'offers', rows)
                self.assertIn('invalid price_usd', self.errors())

    def test_duplicate_configuration_different_id(self):
        _, rows = read(self.root, 'laptops')
        duplicate = dict(rows[0], configuration_id='LAP9999')
        write(self.root, 'laptops', rows + [duplicate])
        self.assertIn('duplicate configuration signature', self.errors())

    def test_rating_offer_mismatch(self):
        self.synthetic_response()
        _, rows = read(self.root, 'ratings')
        rows[0]['configuration_id'] = 'LAP0002'
        write(self.root, 'ratings', rows)
        self.assertIn('rated configuration differs from its offer', self.errors())

    def test_unable_to_judge_is_missing(self):
        self.synthetic_response()
        _, rows = read(self.root, 'ratings')
        rows[0]['rating_status'] = 'unable_to_judge'
        write(self.root, 'ratings', rows)
        self.assertIn('missing feedback must not receive a numerical rating', self.errors())
        rows[0]['suitability_rating'] = ''
        write(self.root, 'ratings', rows)
        self.assertEqual(self.errors(), '')

    def test_consent_required_for_assignment(self):
        self.synthetic_response()
        _, rows = read(self.root, 'students')
        rows[0]['consent_status'] = 'declined'
        write(self.root, 'students', rows)
        self.assertIn('requires consented adult participant', self.errors())

    def test_unknown_mandatory_value_fails(self):
        self.synthetic_response()
        _, rows = read(self.root, 'students')
        rows[0]['max_weight_kg'] = '2'
        write(self.root, 'students', rows)
        _, rows = read(self.root, 'laptops')
        rows[0]['weight_kg'] = ''
        write(self.root, 'laptops', rows)
        self.assertIn('missing or failing mandatory max_weight_kg', self.errors())


if __name__ == '__main__':
    unittest.main(verbosity=2)
