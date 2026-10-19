import re
from urllib.parse import urljoin
from .base import Collector, soup, laptop_title, result
from ..normalize import plain


class GoldOneCollector(Collector):
    def links(self, html, url):
        rows = []
        for card in soup(html).select('#content .product-layout'):
            a = card.select_one('h4 a[href*="product_id="]')
            if a and laptop_title(a.get_text(' ', strip=True)):
                rows.append(dict(url=urljoin(url, a['href'].strip()), title=a.get_text(' ', strip=True)))
        return rows

    def extract(self, html, url):
        doc = soup(html)
        title = doc.select_one('#content .product-title')
        description = doc.select_one('#tab-description')
        right = doc.select_one('#content .product-right')
        if not title or not description or not right:
            raise ValueError('Gold One product selectors not found; possible HTML change or non-product page.')
        text = plain(description)
        header = plain(right)
        code = re.search(r'Product Code:\s*([^\n]+)', header, re.I)
        code = code[1].strip() if code else ''
        availability = re.search(r'Availability:\s*(Out Of Stock|In Stock|Pre.?Order|Check Stock)', header, re.I)
        return result(title.get_text(' ', strip=True), text, right.select_one('.price'),
                      availability[1] if availability else '', shop_sku=code, manufacturer_sku=code)
