import re
from urllib.parse import urljoin
from .base import Collector, soup, laptop_title, result
from ..normalize import plain


class PTCCollector(Collector):
    def links(self, html, url):
        rows = []
        for card in soup(html).select('.product-card, .aiz-card-box'):
            a = card.select_one('h3 a[href*="/product/"]')
            if a and laptop_title(a.get_text(' ', strip=True)):
                rows.append(dict(url=urljoin(url, a['href']), title=a.get_text(' ', strip=True)))
        return rows

    def extract(self, html, url):
        doc = soup(html)
        title = doc.select_one('h1.fs-24, h1.product-title, main h1')
        if not title:
            raise ValueError('PTC product heading not found; possible redirect or HTML change.')
        scope = title.find_parent(class_='text-left') or title.parent.parent
        description = doc.select_one('#tab_default_1') or scope
        # Prefer the detailed delivered specs, preserving starting-at weight as unknown.
        text = plain(description)
        header = plain(scope)
        code = re.search(r'SKU:\s*([A-Z][A-Z0-9-]+)', header)
        availability = re.search(r'\b(?:in stock|out of stock|pre.?order|check stock)\b', header, re.I)
        price_node = scope.select_one('.product-price, .price')
        discount_label = scope.find(string=re.compile(r'^\s*Discount Price:\s*$', re.I))
        list_label = scope.find(string=re.compile(r'^\s*Price:\s*$', re.I))
        if discount_label and list_label:
            # Keep both displayed observations while selecting the explicitly labelled sale.
            prices = soup('<div></div>')
            old = prices.new_tag('div', attrs={'class': 'price-old'})
            old.string = plain(list_label.parent.parent.parent)
            sale = prices.new_tag('div', attrs={'class': 'price-new'})
            sale.string = plain(discount_label.parent.parent.parent)
            prices.div.extend([old, sale])
            price_node = prices.div
        # A price label may have a separate amount column; do not scan related products or installments.
        if not price_node or '$' not in plain(price_node):
            label = discount_label or list_label
            price_node = label.parent.parent.parent if label else price_node
        return result(title.get_text(' ', strip=True), text, price_node,
                      availability[0] if availability else '', shop_sku=code[1] if code else '')
