import json
from pathlib import Path
import shutil
import tempfile
import unittest

from laptop_collection.batch import ROOT
from laptop_collection.mapping import Reviewer, ReviewError
from laptop_collection.models import make_candidate
from laptop_collection.store import Store
from scripts.portable_review import FORMAT, export_pending, import_reviews


class PortableReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for name in ('data', 'config'):
            shutil.copytree(ROOT/name, self.root/name)
        self.store = Store(self.root)
        self.candidate = make_candidate('goldone', 'Gold One Computer',
            'https://www.goldonecomputer.com/index.php?route=product/product&product_id=portable-test',
            {'full_name': 'FICTIONAL </script> portable test', 'price_usd': '399'})
        self.store.add(self.candidate)
        self.output = self.root/'portable'
        self.manifest = export_pending(self.root, self.output)
        self.review = dict(candidate_id=self.candidate['candidate_id'], expected_revision=0,
            action='needs_review', reviewer='TEST', notes='FICTIONAL test review',
            saved_at='2026-10-26T12:00:00Z', edits={}, confirmations={})
        self.results = self.root/'results.json'

    def tearDown(self):
        self.temp.cleanup()

    def write_results(self, reviews=None):
        self.results.write_text(json.dumps(dict(format=FORMAT, batch_id=self.manifest['batch_id'],
            reviews=reviews if reviews is not None else [self.review])), encoding='utf-8')

    def run_import(self, apply=False):
        return import_reviews(self.root, self.results, self.output/'manifest.json', apply)

    def snapshot(self):
        return {str(p.relative_to(self.root)):p.read_bytes() for p in (self.root/'data').glob('*.csv')}

    def test_export_excludes_saved_reviews_and_escapes_retailer_html(self):
        Reviewer(self.store).review(self.candidate['candidate_id'], 'skip', {}, 'TEST')
        with self.assertRaisesRegex(ValueError, 'No pending'):
            export_pending(self.root, self.root/'second')
        html = (self.output/'START_REVIEW.html').read_text(encoding='utf-8')
        self.assertIn('FICTIONAL \\u003c/script>', html)
        self.assertNotIn('FICTIONAL </script>', html)

    def test_check_preserves_live_data_and_apply_is_idempotent(self):
        self.write_results()
        before = self.snapshot()
        self.assertEqual(self.run_import()['decisions'], 1)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.store.get(self.candidate['candidate_id'])['revision'], 0)
        self.run_import(True)
        self.assertEqual(self.store.get(self.candidate['candidate_id'])['state'], 'needs_review')
        after = self.snapshot()
        self.run_import(True)
        self.assertEqual(after, self.snapshot())
        self.assertEqual(len(self.store.reviews(self.candidate['candidate_id'])), 1)

    def test_preflight_refuses_unconfirmed_approval_without_changes(self):
        self.review['action'] = 'approve'
        self.write_results()
        before = self.snapshot()
        with self.assertRaises(ReviewError):
            self.run_import(True)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.store.get(self.candidate['candidate_id'])['state'], 'pending')

    def test_stale_and_unknown_reviews_are_refused(self):
        self.write_results()
        Reviewer(self.store).review(self.candidate['candidate_id'], 'skip', {}, 'TEST')
        with self.assertRaisesRegex(ReviewError, 'changed in another session'):
            self.run_import(True)
        self.review['candidate_id'] = 'CAN-unknown'
        self.write_results()
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            self.run_import()

    def test_needs_review_export_restores_saved_confirmations_and_revision(self):
        Reviewer(self.store).review(self.candidate['candidate_id'], 'needs_review',
            {'condition':'new'}, 'TEST', 'Check storage next', {'new_condition': True})
        exported = export_pending(self.root, self.root/'remaining', states=('needs_review',))
        candidate = exported['candidates'][0]
        self.assertEqual(candidate['revision'], 1)
        self.assertEqual(candidate['fields']['condition'], 'new')
        self.assertTrue(candidate['saved_review']['confirmations']['new_condition'])
        self.assertEqual(candidate['saved_review']['notes'], 'Check storage next')


if __name__ == '__main__':
    unittest.main()
