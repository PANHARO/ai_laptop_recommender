import copy
import csv
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from laptop_collection.access import AccessBlocked, PublicClient, robots_allowed
from laptop_collection.batch import ROOT, import_export, manual_url, seed_existing, settings
from laptop_collection.collectors import COLLECTORS
from laptop_collection.mapping import Reviewer, ReviewError
from laptop_collection.models import classify_duplicate, hardware_key, make_candidate, canonical_url
from laptop_collection.normalize import capacity, price
from laptop_collection.store import Store, atomic_bytes
from scripts.validate_data import validate

FIXTURES = Path(__file__).parent/'fixtures'
URL = 'https://www.goldonecomputer.com/index.php?route=product/product&product_id=fixture-not-real'
CONFIRMED = dict(new_condition=True, manufacturer_sku=True, specifications=True, price=True)


def fields():
    return dict(full_name='ASUS FixtureBook F1400-TESTW', brand='ASUS', model='FixtureBook',
        manufacturer_sku='F1400-TESTW', retailer_sku='TEST-SHOP-123', cpu_model='Intel N150',
        gpu_model='Intel UHD Graphics', gpu_type='integrated',ram_gb='8',ram_type='DDR5',storage_gb='512',
        storage_type='ssd',screen_inches='14',display_text='14 inch FHD; non-touch',price_usd='399',
        price_text='$399',currency='USD',condition='new',purchase_type='outright',source_url=URL,
        manufacturer_sku_evidence='FICTIONAL TEST: manufacturer part number in fixture',
        specification_evidence='FICTIONAL TEST: delivered specifications confirmed',
        condition_evidence='FICTIONAL TEST: Condition: New',condition_evidence_url=URL)


class ParserTests(unittest.TestCase):
    def test_goldone_scopes_price_and_does_not_use_hdmi_refresh(self):
        r=COLLECTORS['goldone']().extract((FIXTURES/'goldone_product.html').read_text(),URL)
        f=r['fields']
        self.assertEqual(f['price_usd'],'399')
        self.assertIn('499',f['price_text'])
        self.assertEqual(f['manufacturer_sku'],'F1400-TESTW')
        self.assertEqual(f['ram_gb'],'8')
        self.assertEqual(f['cpu_model'],'Intel N150')
        self.assertNotIn('refresh_hz',f)
        self.assertNotIn('HDMI',f['display_text'])

    def test_ptc_inventory_is_not_manufacturer_and_weight_unknown(self):
        f=COLLECTORS['ptc']().extract((FIXTURES/'ptc_product.html').read_text(),URL)['fields']
        self.assertEqual(f['retailer_sku'],'LLS-9999')
        self.assertFalse(f.get('manufacturer_sku'))
        self.assertEqual(f['price_usd'],'799')
        self.assertEqual(f['storage_gb'],'1000')
        self.assertFalse(f.get('weight_kg'))
        self.assertEqual(f['ram_gb'],'16')
        self.assertEqual(f['availability_text'],'Pre Order')

    def test_beckie_card_conflicting_media_and_detail_identity(self):
        html=(FIXTURES/'beckie_listing.html').read_text()
        collector=COLLECTORS['beckie']()
        rows=collector.links(html,'https://www.beckie-khmer.com/?cat=laptop')
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['extracted']['fields']['retailer_sku'],'BECKIE9999')
        self.assertFalse(rows[0]['extracted']['fields'].get('storage_type'))
        self.assertIn('conflicting_storage_media',rows[0]['extracted']['flags'])
        with self.assertRaises(ValueError):
            collector.extract(html,'https://www.beckie-khmer.com/products/detail?q=wrong-product')

    def test_ptc_preserves_explicit_list_and_discount_prices(self):
        html=(FIXTURES/'ptc_product.html').read_text().replace('<div>Installments',
            '<div class="row"><div><div>Discount Price:</div></div><div>$749 /Pc</div></div><div>Installments')
        f=COLLECTORS['ptc']().extract(html,URL)['fields']
        self.assertEqual(f['price_usd'],'749')
        self.assertIn('799',f['price_text']);self.assertIn('749',f['price_text'])

    def test_missing_changed_html_does_not_invent_specs(self):
        with self.assertRaises(ValueError):
            COLLECTORS['goldone']().extract('<h1>Coming soon</h1>',URL)
        self.assertEqual(COLLECTORS['ptc']().links('<html>Changed</html>',URL),[])

    def test_price_ambiguity_monthly_and_zero(self):
        for text in ['$0.00','$399 $499','$29 per month']:
            self.assertEqual(price(BeautifulSoup('<p>'+text+'</p>','html.parser'))[0],'')
        self.assertEqual(capacity('1TB SSD'),'1000')
        self.assertEqual(capacity('Unknown'),'')

    def test_duplicate_uses_exact_hardware_and_numeric_units(self):
        old=fields(); old.update(configuration_id='LAP9999',record_status='verified')
        new=fields();new['ram_gb']='8.0'
        self.assertEqual(classify_duplicate(new,[old])['kind'],'exact')
        new['ram_gb']='16'
        self.assertEqual(classify_duplicate(new,[old])['kind'],'conflict')
        new['manufacturer_sku']=''
        self.assertEqual(classify_duplicate(new,[old])['kind'],'missing_sku')

    def test_identity_keeps_actual_cpu_model_and_ignores_trademark_prose(self):
        old=fields();old['cpu_model']='Intel Core Ultra 7 255H'
        new=dict(old,cpu_model='Intel® Core™ Ultra 7 Processor 255H (24MB Cache, 2.0 GHz)')
        self.assertEqual(hardware_key(old),hardware_key(new))
        new['cpu_model']='Intel Core Ultra 7 Processor 285H (24MB Cache)'
        self.assertNotEqual(hardware_key(old),hardware_key(new))

    def test_acer_family_code_is_not_invented_manufacturer_sku(self):
        from laptop_collection.normalize import specs
        f,flags=specs('Acer Aspire A715-59G','-CPU: Intel Core i5-12450H')
        self.assertFalse(f.get('manufacturer_sku'))

    def test_hyphenated_screen_and_class_marked_sale(self):
        from laptop_collection.normalize import specs
        f,_=specs('ASUS test laptop','-Display: 14.0-inch WUXGA (1920x1200) 60Hz')
        self.assertEqual(f['screen_inches'],'14.0')
        amount,raw,_=price(BeautifulSoup('<span><b class="line-through">$709</b> $559</span>','html.parser'))
        self.assertEqual(amount,'559');self.assertIn('709',raw)

    def test_robots_wildcards_specific_agents_and_allow_tie(self):
        text='User-agent: *\nDisallow: /*search=\nDisallow: /private\nAllow: /private/public\n'
        self.assertFalse(robots_allowed(text,URL+'&search=foo','ITM360-LaptopResearch'))
        self.assertTrue(robots_allowed(text,'https://example.com/private/public','ITM360-LaptopResearch'))
        self.assertTrue(robots_allowed('User-agent: OtherBot\nDisallow: /',URL,'ITM360-LaptopResearch'))
        self.assertTrue(robots_allowed('User-agent: *\nDisallow: /\nAllow: /',URL,'ITM360-LaptopResearch'))

    def test_access_requires_policy_and_rejects_external_urls(self):
        config=settings(ROOT);client=PublicClient(config['sources']['goldone'],config,sleep=lambda _:None)
        with self.assertRaises(AccessBlocked):client.get(URL)
        with self.assertRaises(ValueError):canonical_url('http://127.0.0.1/secrets')


class WorkspaceCase(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        shutil.copytree(ROOT/'data',self.root/'data')
        shutil.copytree(ROOT/'config',self.root/'config')
        self.store=Store(self.root);self.reviewer=Reviewer(self.store)
        self.initial={p.name:p.read_bytes() for p in (self.root/'data').glob('*.csv')}

    def tearDown(self):self.temp.cleanup()

    def candidate(self, edits=None, day='2026-10-15'):
        f=fields();f.update(edits or {})
        c=make_candidate('goldone','Gold One Computer',URL,f,observed_at=day+'T12:00:00+00:00')
        self.store.add(c);return c

    def approve(self,c,**kwargs):
        return self.reviewer.review(c['candidate_id'],'approve',{},'TEST_REVIEWER',confirmations=CONFIRMED,**kwargs)


class ReviewTests(WorkspaceCase):
    def test_no_collection_or_unconfirmed_review_verifies(self):
        c=self.candidate()
        for confirmation in ['new_condition','manufacturer_sku','specifications','price']:
            f=dict(CONFIRMED);f[confirmation]=False
            with self.assertRaises(ReviewError):self.reviewer.review(c['candidate_id'],'approve',{},'TEST',confirmations=f)
        self.assertEqual(self.store.get(c['candidate_id'])['state'],'pending')
        for p in (self.root/'data').glob('*.csv'):self.assertEqual(p.read_bytes(),self.initial[p.name])

    def test_missing_information_and_shop_sku_block_approval(self):
        for key in ['manufacturer_sku','cpu_model','storage_type','condition_evidence']:
            with self.subTest(key=key):
                c=self.candidate({key:''})
                with self.assertRaises(ReviewError):self.approve(c)
        c=self.candidate({'manufacturer_sku':'BECKIE12345'})
        with self.assertRaises(ReviewError):self.approve(c)

    def test_unknown_literal_and_invalid_optional_values_are_not_verified(self):
        c=self.candidate({'cpu_model':'Unknown'})
        with self.assertRaises(ReviewError):self.approve(c)
        c=self.candidate({'gpu_type':'super-fast'})
        with self.assertRaises(ReviewError):self.approve(c)
        self.assertEqual(sum(r['record_status']=='verified' for r in self.store.canonical()['laptops']),0)

    def test_documented_variant_requires_an_explicit_separate_review(self):
        first=self.approve(self.candidate());second=self.candidate({'ram_gb':'16','variant_evidence':'FIXTURE retailer documents delivered 16 GB upgrade','resolution_notes':'Distinct delivered memory option documented in fixture'})
        confirmations=dict(CONFIRMED,documented_variant=True)
        result=self.reviewer.review(second['candidate_id'],'approve',{},'TEST',confirmations=confirmations)
        self.assertEqual(result['state'],'approved')
        self.assertNotEqual(first['canonical_result']['configuration_id'],result['canonical_result']['configuration_id'])

    def test_recovery_refuses_an_unrelated_manual_csv_change(self):
        c=self.candidate();original=atomic_bytes
        def crash(path,data):
            if Path(path).parent.name=='data' and Path(path).name=='offers.csv':raise OSError('TEST interrupted')
            original(path,data)
        with patch('laptop_collection.store.atomic_bytes',side_effect=crash):
            with self.assertRaises(OSError):self.approve(c)
        path=self.root/'data/offers.csv';path.write_bytes(path.read_bytes()+b'\n# TEST external edit\n')
        with self.assertRaises(RuntimeError):Store(self.root)

    def test_40_candidate_batch_leaves_all_canonical_data_untouched(self):
        from laptop_collection.batch import collect
        import hashlib
        product=(FIXTURES/'goldone_product.html').read_text()
        listing='<div id="content">'+''.join('<div class="product-layout"><h4><a href="'+URL+'&n='+str(i)+'">ASUS Fixture Laptop F1400-TESTW</a></h4></div>' for i in range(40))+'</div>'
        class OfflineClient:
            blocked=False
            def __init__(self,*a,**k):pass
            def check_policy(self):return []
            def get(self,url):
                raw=listing if 'category' in url else product
                return dict(url=url,text=raw,sha256=hashlib.sha256(raw.encode()).hexdigest())
            def log(self,**entry):pass
        with patch('laptop_collection.batch.PublicClient',OfflineClient):report=collect(self.root,['goldone'],40,1)
        self.assertEqual(report['per_site']['goldone']['staged_new'],40)
        self.assertEqual(len(self.store.list()),40)
        for p in (self.root/'data').glob('*.csv'):self.assertEqual(p.read_bytes(),self.initial[p.name])

    def test_approval_idempotency_and_old_snapshots(self):
        old=self.store.canonical();c=self.candidate()
        first=self.approve(c);second=self.approve(c)
        self.assertEqual(first,second)
        current=self.store.canonical()
        self.assertEqual(current['offers'][:len(old['offers'])],old['offers'])
        self.assertEqual(len(current['offers']),len(old['offers'])+1)
        self.assertEqual(validate(self.root)['errors'],[])
        for name in ['students.csv','ratings.csv','assignments.csv']:
            self.assertEqual((self.root/'data'/name).read_bytes(),self.initial[name])

    def test_new_price_gets_new_offer_but_same_configuration(self):
        first=self.approve(self.candidate())
        second=self.approve(self.candidate({'price_usd':'429','price_text':'$429'},day='2026-10-16'))
        self.assertEqual(first['canonical_result']['configuration_id'],second['canonical_result']['configuration_id'])
        self.assertNotEqual(first['canonical_result']['offer_id'],second['canonical_result']['offer_id'])

    def test_conflict_is_quarantined_without_merging(self):
        self.approve(self.candidate())
        old=self.store.canonical();second=self.approve(self.candidate({'ram_gb':'16'}))
        self.assertEqual(second['state'],'needs_review')
        current=self.store.canonical()
        self.assertEqual(current['offers'],old['offers'])
        self.assertEqual(current['laptops'],old['laptops'])
        self.assertTrue(second['notices'])

    def test_review_transitions_skip_and_stale_session(self):
        c=self.candidate();event=self.reviewer.review(c['candidate_id'],'skip',{},'TEST')
        self.assertEqual(event['state'],'skipped')
        for p in (self.root/'data').glob('*.csv'):self.assertEqual(p.read_bytes(),self.initial[p.name])
        with self.assertRaises(ReviewError):self.approve(c)
        event=self.reviewer.review(c['candidate_id'],'needs_review',{},'TEST','Check SKU',expected_revision=1)
        self.assertEqual(event['state'],'needs_review')
        event=self.reviewer.review(c['candidate_id'],'reject',{},'TEST','Wrong condition',expected_revision=2)
        self.assertEqual(event['state'],'rejected')
        with self.assertRaises(ReviewError):self.reviewer.review(c['candidate_id'],'skip',{},'TEST',expected_revision=3)

    def test_crash_recovery_finishes_once(self):
        c=self.candidate()
        original=atomic_bytes
        tripped=False
        def crash(path,data):
            nonlocal tripped
            if Path(path).parent.name=='data' and Path(path).name=='offers.csv' and not tripped:
                tripped=True;raise OSError('TEST simulated interruption')
            original(path,data)
        with patch('laptop_collection.store.atomic_bytes',side_effect=crash):
            with self.assertRaises(OSError):self.approve(c)
        self.assertTrue((self.root/'staging/pending_transaction.json').exists())
        recovered=Store(self.root)
        self.assertEqual(recovered.get(c['candidate_id'])['state'],'approved')
        self.assertEqual(validate(self.root)['errors'],[])
        self.assertEqual(len(recovered.reviews(c['candidate_id'])),1)
        self.assertFalse((self.root/'staging/pending_transaction.json').exists())

    def test_manual_import_does_not_fetch_and_seed_is_idempotent(self):
        with patch('requests.Session.get',side_effect=AssertionError('Network forbidden')):
            c,added=manual_url(self.store,'goldone',URL,'Manual fixture')
            self.assertTrue(added)
            self.assertFalse(manual_url(self.store,'goldone',URL,'Manual fixture')[1])
            count=seed_existing(self.root)
            self.assertGreater(count,0)
            self.assertEqual(seed_existing(self.root),0)
            self.assertTrue(any(c.get('existing_evidence_id')=='SRC0009' for c in self.store.list()))
        for p in (self.root/'data').glob('*.csv'):self.assertEqual(p.read_bytes(),self.initial[p.name])

    def test_authorized_export_requires_reference_date_and_human_review(self):
        export=self.root/'authorized.json'
        export.write_text(json.dumps([dict(fields(),observed_date='2026-10-14')]))
        with patch('requests.Session.get',side_effect=AssertionError('Network forbidden')):
            with self.assertRaises(ValueError):import_export(self.root,'goldone',export,'')
            self.assertEqual(import_export(self.root,'goldone',export,'FICTIONAL TEST export authorization'),1)
            self.assertEqual(import_export(self.root,'goldone',export,'FICTIONAL TEST export authorization'),0)
        c=self.store.list()[0]
        self.assertEqual(c['state'],'pending');self.assertEqual(c['observed_date'],'2026-10-14')
        export.write_text(json.dumps([fields()]))
        with self.assertRaises(ValueError):import_export(self.root,'goldone',export,'FICTIONAL TEST authorization')
        for p in (self.root/'data').glob('*.csv'):self.assertEqual(p.read_bytes(),self.initial[p.name])


class DashboardTests(WorkspaceCase):
    def test_dashboard_needs_review_button_and_source_links(self):
        from streamlit.testing.v1 import AppTest
        c=self.candidate()
        with patch.dict(os.environ,{'LAPTOP_RECOMMENDER_ROOT':str(self.root)}):
            at=AppTest.from_file(str(ROOT/'review_app.py')).run(timeout=30)
            self.assertEqual(len(at.exception),0)
            next(w for w in at.text_area if w.label=='Review notes').input('Needs an exact source check')
            next(w for w in at.button if w.label=='Needs Review').click().run(timeout=30)
            self.assertEqual(len(at.exception),0)
            self.assertEqual(self.store.get(c['candidate_id'])['state'],'needs_review')

    def test_dashboard_approval_requires_checkboxes_and_then_commits(self):
        from streamlit.testing.v1 import AppTest
        c=self.candidate()
        with patch.dict(os.environ,{'LAPTOP_RECOMMENDER_ROOT':str(self.root)}):
            at=AppTest.from_file(str(ROOT/'review_app.py')).run(timeout=30)
            next(w for w in at.button if w.label=='✓ Approve').click().run(timeout=30)
            self.assertGreater(len(at.error),0)
            self.assertEqual(self.store.get(c['candidate_id'])['state'],'pending')
            for checkbox in at.checkbox:
                if checkbox.label in ['I verified explicit new condition evidence','I verified the actual manufacturer SKU, separate from shop SKU','I checked the exact delivered CPU, GPU, RAM, storage and display','I verified the full outright USD purchase price']:
                    checkbox.check()
            next(w for w in at.button if w.label=='✓ Approve').click().run(timeout=30)
            self.assertEqual(len(at.exception),0)
            self.assertEqual(self.store.get(c['candidate_id'])['state'],'approved')


if __name__=='__main__':unittest.main(verbosity=2)
