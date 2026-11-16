import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from laptop_collection.batch import ROOT
from laptop_collection.rechecks import apply_rechecks
from laptop_collection.store import Store


class RecheckTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        for name in ('data','config'):shutil.copytree(ROOT/name,self.root/name)
        self.store=Store(self.root)
        offer=next(r for r in self.store.canonical()['offers'] if r['offer_status']=='verified')
        source=next(r for r in self.store.canonical()['source_checks'] if r['evidence_id']==offer['evidence_id'])
        self.row={k:offer[k] for k in ('configuration_id','offer_id','evidence_id','condition_evidence_id','source_url','observed_date','price_usd','retailer')}
        self.row.update(second_check_status=source['second_check_status'],second_checked_by='',second_checked_at='',findings='')
        self.original=self.root/'queue.csv';self.returned=self.root/'returned.csv'
        self.write(self.original,self.row)
        self.submitted=dict(self.row,second_check_status='passed',second_checked_by='FICTIONAL_TEST',
            second_checked_at=(datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat(),
            findings='FICTIONAL TEST ONLY: source matches')
        self.write(self.returned,self.submitted)

    def tearDown(self):self.temp.cleanup()

    def write(self,path,row):
        with path.open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(row));writer.writeheader();writer.writerow(row)

    def test_recheck_is_audited_idempotent_and_preserves_offers_and_candidates(self):
        before=self.store.canonical()
        first=apply_rechecks(self.store,self.returned,self.original)
        after=self.store.canonical()
        second=apply_rechecks(self.store,self.returned,self.original)
        self.assertEqual(first,second)
        self.assertEqual(after,self.store.canonical())
        self.assertEqual(before['laptops'],after['laptops'])
        self.assertEqual(before['offers'],after['offers'])
        self.assertEqual(self.store.list(),[])
        source=next(r for r in after['source_checks'] if r['evidence_id']==self.row['evidence_id'])
        self.assertEqual(source['second_check_status'],'passed')
        self.assertEqual(source['second_checked_by'],'FICTIONAL_TEST')
        self.assertEqual(self.store.audit_receipt(first['event_id']),first)

    def test_wrong_identity_or_future_timestamp_cannot_write(self):
        before=self.store.canonical()
        for changed in [dict(self.submitted,offer_id='OFF_UNKNOWN'),
                        dict(self.submitted,second_checked_at=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat())]:
            self.write(self.returned,changed)
            with self.assertRaises(ValueError):apply_rechecks(self.store,self.returned,self.original)
        self.assertEqual(before,self.store.canonical())

    def test_interrupted_second_check_recovers_once_without_candidate_review(self):
        from laptop_collection.store import atomic_bytes
        before=len(self.store.canonical()['issues'])
        def interrupted(path,data):
            if Path(path).name=='issues.csv':
                raise OSError('FICTIONAL interrupted metadata import')
            atomic_bytes(path,data)
        with patch('laptop_collection.store.atomic_bytes',side_effect=interrupted):
            with self.assertRaises(OSError):apply_rechecks(self.store,self.returned,self.original)
        self.assertTrue((self.root/'staging/pending_transaction.json').exists())
        recovered=Store(self.root)
        event=apply_rechecks(recovered,self.returned,self.original)
        self.assertEqual(recovered.audit_receipt(event['event_id']),event)
        self.assertEqual(len(recovered.canonical()['issues']),before+1)
        self.assertEqual(recovered.list(),[])
        self.assertFalse((self.root/'staging/pending_transaction.json').exists())


if __name__=='__main__':unittest.main()
