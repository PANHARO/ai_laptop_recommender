from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

HARDWARE_FIELDS = (
    'brand', 'model', 'manufacturer_sku', 'cpu_model', 'gpu_model', 'gpu_type',
    'gpu_vram_gb', 'ram_gb', 'ram_type', 'storage_gb', 'storage_type',
    'screen_inches', 'display_resolution', 'display_text', 'refresh_hz',
    'weight_kg', 'weight_evidence_type',
)
OFFER_FIELDS = ('retailer_sku', 'price_usd', 'price_text', 'currency',
                'availability_text', 'condition', 'purchase_type', 'delivered_os')
EDIT_FIELDS = HARDWARE_FIELDS + OFFER_FIELDS + ('full_name', 'source_url',
    'manufacturer_sku_evidence', 'specification_evidence', 'condition_evidence',
    'condition_evidence_url', 'resolution_notes', 'variant_evidence')
CORE_FIELDS = ('brand', 'model', 'manufacturer_sku', 'cpu_model', 'gpu_model',
               'ram_gb', 'storage_gb', 'storage_type', 'screen_inches', 'display_text')
NUMERIC_FIELDS = ('ram_gb', 'storage_gb', 'screen_inches', 'gpu_vram_gb',
                  'refresh_hz', 'weight_kg', 'price_usd')


def now():
    return datetime.now(timezone.utc).isoformat()


def clean(value):
    return re.sub(r'\s+', ' ', '' if value is None else str(value)).strip()


def decimal_string(value):
    if value is None or clean(value) == '':
        return ''
    try:
        n = Decimal(str(value))
        if not n.is_finite():
            return ''
        return format(n.normalize(), 'f')
    except InvalidOperation:
        return ''


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def canonical_url(url):
    p = urlsplit(clean(url))
    if p.scheme != 'https' or not p.hostname or p.username or p.password or p.port not in (None, 443):
        raise ValueError('Use a public HTTPS URL without credentials or a custom port.')
    # Query parameters are preserved: removing them could change the listing or bypass robots rules.
    return urlunsplit(('https', p.netloc.lower(), p.path or '/', p.query, ''))


def allowed_url(url, source):
    url = canonical_url(url)
    if urlsplit(url).hostname not in source['hosts']:
        raise ValueError('URL is outside this retailer; no network request made.')
    return url


def make_candidate(site, retailer, url, fields=None, **metadata):
    fields = fields or {}
    data = {k: clean(fields.get(k)) for k in EDIT_FIELDS}
    data.update(retailer=retailer, source_url=canonical_url(url))
    data['currency'] = data.get('currency') or ''
    data['condition'] = data.get('condition') or 'unknown'
    data['purchase_type'] = data.get('purchase_type') or 'unknown'
    for k in NUMERIC_FIELDS:
        data[k] = decimal_string(fields.get(k))
    observed_at = metadata.pop('observed_at', None) or now()
    identity = dict(site=site, url=data['source_url'], date=observed_at[:10], fields=data)
    flags = metadata.pop('flags', [])
    flags = list(dict.fromkeys(flags + ['missing_' + k for k in CORE_FIELDS if not data.get(k)]))
    return dict(candidate_id='CAN' + digest(identity)[:24], site=site,
                observed_at=observed_at, observed_date=observed_at[:10],
                fields=data, flags=flags,
                origin=metadata.pop('origin', 'public_html'), **metadata)


def hardware_key(fields):
    keys = ('manufacturer_sku', 'brand', 'cpu_model', 'gpu_model', 'ram_gb',
            'storage_gb', 'storage_type', 'screen_inches', 'display_text')
    return tuple(identity_value(k, fields.get(k), fields) for k in keys)


def identity_value(key, value, fields=None):
    if key in NUMERIC_FIELDS:
        return decimal_string(value)
    text = clean(value).casefold().replace('®','').replace('™','')
    if key == 'cpu_model':
        chip = re.search(r'\bi[3579][- ]\d{4,5}[a-z]{0,3}\b',text)
        if chip:
            return 'intel core ' + chip[0].replace(' ','-')
        text = re.sub(r'\b(?:mobile )?processor\b','',text)
        text = re.split(r'\(|\d+(?:\.\d+)?\s*ghz',text)[0].strip()
    if key == 'gpu_model':
        text = re.sub(r'\b(?:nvidia|geforce|graphics)\b','',text)
        text = re.sub(r'\d+\s*gb\s*(?:gddr\d[x]?)?','',text)
    if key == 'display_text' and fields and fields.get('display_resolution'):
        # Explicit pixels, diagonal and documented panel/touch/refresh attributes identify
        # the display; reordered prose and repeated diagonal text are not new hardware.
        panel = next((x for x in ('oled','ips','tn','va') if re.search(r'\b'+x+r'\b',text)), '')
        touch = 'non-touch' if re.search(r'non[ -]?touch',text) else 'touch' if re.search(r'\btouch\b',text) else ''
        return '|'.join([clean(fields['display_resolution']).lower().replace(' ',''),panel,touch,decimal_string(fields.get('refresh_hz'))])
    return clean(text)


def classify_duplicate(fields, laptops):
    sku = clean(fields.get('manufacturer_sku')).casefold()
    if not sku:
        return dict(kind='missing_sku', matches=[])
    same = [r for r in laptops if clean(r['manufacturer_sku']).casefold() == sku]
    exact = [r for r in same if hardware_key(r) == hardware_key(fields)]
    if len(exact) == 1:
        # Optional known attributes must not be silently overwritten or contradicted.
        old = exact[0]
        conflicts = [k for k in HARDWARE_FIELDS if k != 'model' and old.get(k) and fields.get(k)
                     and identity_value(k,old[k],old) != identity_value(k,fields[k],fields)]
        return dict(kind='conflict' if conflicts else 'exact', matches=exact, fields=conflicts)
    return dict(kind='conflict' if same else 'new', matches=same,
                fields=['manufacturer_sku identifies existing hardware with different or incomplete specifications'] if same else [])
