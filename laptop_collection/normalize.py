"""Conservative text normalization. Unknown/ambiguous data stays blank."""
import re
from bs4 import BeautifulSoup
from .models import clean, decimal_string

BRANDS = ('ASUS', 'Acer', 'Lenovo', 'MSI', 'HP', 'Dell', 'Apple', 'Samsung', 'Microsoft', 'Gigabyte', 'LG', 'Huawei', 'Dynabook')
LABELS = r'CPU(?:\s*/\s*Processor)?|Processor|RAM(?:\s*/\s*Memory)?|Memory|Storage|SSD|HDD|Graphic(?:s)?(?:\s*[12])?|VGA|GPU|RTX|Display|Screen|Weight|OS|Operating System|Battery|Keyboard|Warranty|Color|(?:Standard )?Ports?|Optical Drive|Wi-Fi|WLAN(?:\s*\+\s*Bluetooth)?|Camera|(?:Bundled )?Office|AI PC Category|NPU|Network|Ethernet Port|Speakers|Fingerprint(?: Reader)?|Case (?:Material|Color)|Power Adapter'


def plain(element):
    node = BeautifulSoup(str(element), 'html.parser')
    for tag in node(['script', 'style']):
        tag.decompose()
    for tag in node.find_all('br'):
        tag.replace_with('\n')
    for tag in node.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'p', 'li', 'div']):
        tag.insert_before('\n')
    return '\n'.join(clean(line) for line in node.get_text(' ', strip=False).replace('\xa0', ' ').splitlines() if clean(line))


def price(element):
    if element is None:
        return '', '', ['missing_price']
    node = BeautifulSoup(str(element), 'html.parser')
    raw = clean(node.get_text(' ', strip=True))
    if re.search(r'/\s*(?:mo|month)|per\s+month|monthly|installment.only|ក្នុងមួយខែ', raw, re.I):
        return '', raw, ['installment_price_only']
    selected = node.select_one('.price-new, .special-price, [data-price-type="finalPrice"]')
    if selected:
        text = selected.get_text(' ', strip=True)
    else:
        for tag in node.select('del, s, strike, .price-old, .old-price, .line-through'):
            tag.decompose()
        for tag in node.find_all(style=re.compile('line-through', re.I)):
            tag.decompose()
        text = node.get_text(' ', strip=True)
    values = re.findall(r'(?:US\$|USD\s*|\$)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)', text, re.I)
    unique = list(dict.fromkeys(decimal_string(x.replace(',', '')) for x in values))
    if len(unique) != 1:
        return '', raw, ['ambiguous_price' if unique else 'missing_price']
    if float(unique[0]) <= 0:
        return '', raw, ['zero_price_placeholder']
    return unique[0], raw, []


def labelled(text, label):
    # Labels may be split across nested spans; whitespace is retained until after matching.
    pattern = r'(?:^|\n)\s*[-•]?\s*(?:' + label + r')\s*:\s*(.*?)(?=\n\s*[-•]\s*\S|\n\s*(?:' + LABELS + r')\s*:|$)'
    match = re.search(pattern, text, re.I | re.S)
    return clean(match.group(1)) if match else ''


def capacity(text):
    m = re.search(r'(\d+(?:\.\d+)?)\s*(TB|GB)\b', text, re.I)
    if not m:
        return ''
    return decimal_string(float(m[1]) * (1000 if m[2].upper() == 'TB' else 1))


def specs(title, text):
    f, flags = {'full_name': clean(title), 'model': clean(title)}, []
    for brand in BRANDS:
        if re.search(r'\b' + brand + r'\b', title, re.I):
            f['brand'] = brand
            break
    if not f.get('brand') and re.search('MacBook', title, re.I):
        f['brand'] = 'Apple'
    if not f.get('brand') and re.search('Alienware', title, re.I):
        f['brand'] = 'Dell'
    sku = re.search(r'\b([A-Z0-9]{4,}-[A-Z0-9]{3,})\b', title, re.I)
    if sku and f.get('brand') not in ('Acer','HP','Lenovo') and re.search(r'\d', sku[1]) and not re.match(r'(?:BECKIE|LL[SY]|LUX)', sku[1], re.I):
        f['manufacturer_sku'] = sku[1]
        f['manufacturer_sku_evidence'] = 'Part-number-shaped token in full product title: ' + sku[1]
        flags.append('title_sku_requires_human_confirmation')
    f['cpu_model'] = labelled(text, r'CPU(?:\s*/\s*Processor)?|Processor')[:300]
    f['gpu_model'] = labelled(text, r'Graphic(?:s)?(?:\s*1)?|VGA|GPU|RTX')[:300]
    other = labelled(text, r'Graphic(?:s)?\s*2')
    if other:
        f['gpu_model'] += ' + ' + other
    if re.search(r'RTX\s*\d|GTX\s*\d|dedicated|discrete', f['gpu_model'], re.I):
        f['gpu_type'] = 'dedicated'
        vr = re.search(r'(\d+)\s*GB', f['gpu_model'], re.I)
        if vr:
            f['gpu_vram_gb'] = vr[1]
    elif re.search(r'\bintegrated\b', f['gpu_model'], re.I):
        f['gpu_type'] = 'integrated'
    ram = labelled(text, r'RAM(?:\s*/\s*Memory)?|Memory')
    f['ram_gb'] = capacity(ram)
    typ = re.search(r'LPDDR\d[Xx]?|DDR\d', ram, re.I)
    if typ:
        f['ram_type'] = typ[0].upper()
    storage = labelled(text, r'Storage|SSD|HDD')
    f['storage_gb'] = capacity(storage)
    types = [x for x in ['ssd', 'hdd', 'ufs', 'emmc'] if re.search(r'\b' + x + r'\b', storage, re.I)]
    if len(types) == 1:
        f['storage_type'] = types[0]
    elif len(types) > 1:
        if re.search(r'\bSSD\b.*\+.*\bHDD\b|\bHDD\b.*\+.*\bSSD\b', storage, re.I):
            f['storage_type'] = 'mixed'
            flags.append('mixed_storage_total_needs_check')
            # The first number is not necessarily the delivered total.
            f['storage_gb'] = ''
        else:
            flags.append('conflicting_storage_media')
    display = labelled(text, r'Display|Screen')
    if not display:
        line = re.search(r'(?:^|\n)\s*[-•]?\s*(\d{2}(?:\.\d+)?\s*["″].*)', text)
        display = clean(line[1]) if line else ''
    f['display_text'] = display[:400]
    d = re.search(r'(\d{2}(?:\.\d+)?)\s*(?:["″”“]|\x27\x27|-?\s*inch)', display, re.I)
    if d:
        f['screen_inches'] = d[1]
    resolution = re.search(r'(\d{3,4})\s*[x×]\s*(\d{3,4})', display)
    if resolution:
        f['display_resolution'] = resolution[1] + 'x' + resolution[2]
    refresh = re.search(r'(\d{2,3})\s*Hz', display, re.I)
    if refresh:
        f['refresh_hz'] = refresh[1]
    weight = labelled(text, r'Weight')
    if re.search('starting|from|shipping|boxed|up to|approx', weight, re.I):
        flags.append('weight_not_exact')
    else:
        w = re.search(r'(\d+(?:\.\d+)?)\s*kg', weight, re.I)
        if w:
            f.update(weight_kg=w[1], weight_evidence_type='retailer_claim')
    f['delivered_os'] = labelled(text, r'OS|Operating System')[:180]
    condition = re.search(r'Condition\s*:\s*(new|used|refurbished)', text, re.I)
    if condition:
        f['condition'] = condition[1].lower()
        f['condition_evidence'] = condition[0]
    elif re.search(r'\b(?:second.hand|refurbished|pre.owned)\b|^used\b', title, re.I):
        f['condition'] = 'refurbished' if re.search('refurbished', title, re.I) else 'used'
    else:
        f['condition'] = 'unknown'
        flags.append('new_condition_needs_evidence')
    f['specification_evidence'] = text[:6000]
    return f, flags
