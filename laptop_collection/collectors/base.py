import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from ..models import clean
from ..normalize import plain, price, specs


def soup(html):
    return BeautifulSoup(html, 'html.parser')


def laptop_title(title):
    if re.search(r'\b(?:adapter|monitor|mouse|charger|stand|hub|backpack|battery|case|keyboard)\b', title, re.I):
        return False
    return bool(re.search(r'laptop|notebook|vivobook|zenbook|expertbook|ideapad|yoga|thinkpad|legion|nitro|aspire|extensa|swift|predator|tuf|rog|macbook|victus|inspiron|latitude|xps|alienware|katana|cyborg|modern\s*\d|galaxy\s*book|surface\s*laptop|dynabook|loq|probook|elitebook|pavilion|omnibook|prestige|stealth|raider|gram\s*\d', title, re.I))


def result(title, description, price_node, availability='', shop_sku='', manufacturer_sku=''):
    f, flags = specs(title, description)
    amount, raw, price_flags = price(price_node)
    f.update(price_usd=amount, price_text=raw, currency='USD' if re.search(r'\$|\bUSD\b',raw) else '',
             availability_text=clean(availability), retailer_sku=clean(shop_sku),
             purchase_type='outright' if amount else 'unknown')
    if manufacturer_sku:
        # Product codes without a precise suffix may identify only a model family.
        if f.get('brand') not in ('Acer','HP','Lenovo') and re.fullmatch(r'[A-Z0-9]{4,}-[A-Z0-9]{3,}', manufacturer_sku, re.I):
            f['manufacturer_sku'] = manufacturer_sku
            f['manufacturer_sku_evidence'] = 'Retailer Product Code: ' + manufacturer_sku
        else:
            flags.append('product_code_may_be_model_family')
    if not f.get('manufacturer_sku'):
        flags.append('missing_manufacturer_sku')
    if re.search('pre.?order|coming soon|check stock|out of stock', availability, re.I):
        flags.append('availability_requires_manual_decision')
    return dict(fields=f, flags=list(dict.fromkeys(flags + price_flags)))


class Collector:
    detail_required = True

    def next_pages(self, html, url):
        return list(dict.fromkeys(urljoin(url, a['href']) for a in soup(html).select('.pagination a[href]')))

    def links(self, html, url):
        raise NotImplementedError

    def extract(self, html, url):
        raise NotImplementedError
