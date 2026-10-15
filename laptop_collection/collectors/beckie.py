import re
from urllib.parse import urljoin
from .base import Collector, soup, laptop_title, result
from ..normalize import plain


class BeckieCollector(Collector):
    # Public catalogue cards carry independent product identity. Some detail routes return
    # unrelated catalogue content. Do not silently attach that content to the clicked SKU.
    detail_required = False

    def links(self, html, url):
        rows = []
        for card in soup(html).select('.product-wrapper'):
            a = card.select_one('.product-info h2 a[href]')
            description = card.select_one('.product-short-text')
            if not a or not description or not laptop_title(a.get_text(' ', strip=True)):
                continue
            title = a.get_text(' ', strip=True)
            info = card.select_one('.product-info')
            text = plain(info)
            sku = re.search(r'\bSKU\s*(BECKIE\d+)\b', text, re.I)
            status = re.search(r'Available In Stock!?|Out of Stock|Check Stock|Coming Soon|Pre.?Order|restock soon', text, re.I)
            extracted = result(title, plain(description), info.select_one('.price'),
                               status[0] if status else '', shop_sku=sku[1] if sku else '')
            extracted['flags'].append('catalogue_card_only_confirm_detail_link_or_exact_locator')
            rows.append(dict(url=urljoin(url, a['href']), title=title,
                             extracted=extracted, listing_url=url))
        return rows

    def extract(self, html, url):
        # Only a uniquely identified card whose actual URL matches can be used.
        matches = [r for r in self.links(html, url) if r['url'] == url]
        if len(matches) != 1:
            raise ValueError('Beckie detail identity is missing/ambiguous; import the exact catalogue card or review manually.')
        return matches[0]['extracted']
