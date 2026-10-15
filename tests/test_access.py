import copy
import unittest
from unittest.mock import Mock
import requests

from laptop_collection.access import AccessBlocked, PublicClient, RetrievalError, robot_delay
from laptop_collection.batch import ROOT, settings


class Response:
    def __init__(self,status=200,text='',headers=None):
        self.status_code=status;self.text=text;self.headers=headers or {};self.encoding='utf-8'
    def iter_content(self,size):yield self.text.encode()
    def close(self):pass


class AccessTests(unittest.TestCase):
    def client(self,responses):
        config=settings(ROOT)
        session=Mock();session.headers={};session.get.side_effect=responses
        return PublicClient(config['sources']['goldone'],config,session=session,sleep=lambda _:None),session

    def test_terms_prohibition_prevents_products(self):
        for terms in ['Automated collection is not permitted.','No scraping or crawling.','You agree not to use automated means to retrieve this website.']:
            with self.subTest(terms=terms):
                client,session=self.client([Response(text='User-agent: *\nDisallow:\n'),Response(text='<main>'+terms+'</main>')])
                with self.assertRaises(AccessBlocked):client.check_policy()
                with self.assertRaises(AccessBlocked):client.get('https://www.goldonecomputer.com/product')
                self.assertEqual(session.get.call_count,2)

    def test_missing_robots_and_allowed_terms_logged(self):
        client,session=self.client([Response(404),Response(text='<main>Public purchase terms.</main>'),Response(text='<h1>Public product</h1>')])
        client.check_policy();self.assertEqual(client.get('https://www.goldonecomputer.com/product')['status'],200)
        self.assertTrue(any(x['event']=='robots_missing' for x in client.audit))

    def test_forbidden_and_captcha_stop_without_retry(self):
        for response in [Response(403),Response(429),Response(text='<title>Just a moment</title>Verify you are human'),Response(text='<h1>Please complete the CAPTCHA</h1>')]:
            with self.subTest(status=response.status_code):
                client,session=self.client([response]);client.checked=True
                with self.assertRaises(AccessBlocked):client.get('https://www.goldonecomputer.com/product')
                with self.assertRaises(AccessBlocked):client.get('https://www.goldonecomputer.com/other')
                self.assertEqual(session.get.call_count,1)

    def test_disallowed_path_has_no_network_side_effect(self):
        client,session=self.client([]);client.checked=True;client.robots='User-agent: *\nDisallow: /*search='
        with self.assertRaises(AccessBlocked):client.get('https://www.goldonecomputer.com/?search=secret')
        self.assertEqual(session.get.call_count,0)

    def test_redirect_cannot_escape_retailer(self):
        client,session=self.client([Response(302,headers={'Location':'https://attacker.example/'})]);client.checked=True
        with self.assertRaises(ValueError):client.get('https://www.goldonecomputer.com/product')
        self.assertEqual(session.get.call_count,1)

    def test_retries_are_bounded_and_recover_transient_failure(self):
        client,session=self.client([Response(503),Response(text='<h1>Product</h1>')]);client.checked=True
        self.assertEqual(client.get('https://www.goldonecomputer.com/product')['status'],200)
        self.assertEqual(session.get.call_count,2)
        client,session=self.client([requests.Timeout('TEST timeout')]*3);client.checked=True
        with self.assertRaises(RetrievalError):client.get('https://www.goldonecomputer.com/product')
        self.assertEqual(session.get.call_count,3)

    def test_manual_only_source_cannot_be_collected(self):
        client,session=self.client([]);client.source=dict(client.source,mode='manual_urls')
        with self.assertRaises(AccessBlocked):client.check_policy()
        self.assertEqual(session.get.call_count,0)

    def test_stream_timeout_retries_and_eventually_logs_failure(self):
        broken=Response();broken.iter_content=Mock(side_effect=requests.Timeout('TEST stream timeout'))
        client,session=self.client([broken,Response(text='<h1>Product</h1>')]);client.checked=True
        self.assertEqual(client.get('https://www.goldonecomputer.com/product')['status'],200)
        self.assertTrue(any(x['event']=='stream_error' for x in client.audit))
        client,session=self.client([broken]*3);client.checked=True
        with self.assertRaises(RetrievalError):client.get('https://www.goldonecomputer.com/product')
        self.assertEqual(session.get.call_count,3)

    def test_crawl_delay_with_multiple_agent_lines(self):
        policy='User-agent: ITM360-LaptopResearch\nUser-agent: OtherBot\nCrawl-delay: 12\nUser-agent: *\nCrawl-delay: 5\n'
        self.assertEqual(robot_delay(policy,'ITM360-LaptopResearch'),12)

    def test_normal_review_captcha_on_public_product_is_not_challenge_wall(self):
        client,session=self.client([Response(text='<h1>ASUS laptop</h1><p>Public product specifications</p><footer>Review CAPTCHA</footer>')]);client.checked=True
        self.assertEqual(client.get('https://www.goldonecomputer.com/product')['status'],200)


if __name__=='__main__':unittest.main()
