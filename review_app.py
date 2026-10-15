"""Local-only human verification dashboard. Launch: python -m laptop_collection review."""
from collections import Counter
import html
import os
from pathlib import Path

import streamlit as st

from laptop_collection.batch import ROOT, manual_url
from laptop_collection.mapping import Reviewer, ReviewError
from laptop_collection.models import canonical_url
from laptop_collection.store import Store

st.set_page_config(page_title='Laptop Collection Desk', page_icon='💻', layout='wide')
st.markdown('''<style>
.block-container{max-width:1120px;padding-top:2.3rem;padding-bottom:3rem}
[data-testid="stMetric"]{background:#17191d;border:1px solid #2b2e34;border-radius:12px;padding:14px 18px}
[data-testid="stMetricLabel"]{color:#a5a9b2}
[data-testid="stSidebar"]{border-right:1px solid #282b30}
.review-card{border:1px solid #30343a;border-radius:18px;padding:25px 28px;background:#101214;margin:14px 0}
.card-top{display:flex;justify-content:space-between;gap:20px;align-items:center;flex-wrap:wrap}
.eyebrow{color:#9ca3af;font-size:12px;letter-spacing:.1em;text-transform:uppercase}
.badge{color:#ff9b61;background:#382318;border:1px solid #6d3b20;padding:5px 12px;border-radius:25px;font-size:12px}
.product-title{font-size:24px;font-weight:650;line-height:1.3;margin:17px 0 6px}
.price{font-size:32px;font-weight:650;color:#edf5ff;margin:8px 0}
.meta{color:#a9afb8;font-size:13px;line-height:1.8}
.spec-row{display:grid;grid-template-columns:180px 1fr;border-bottom:1px solid #25282c;padding:11px 0;font-size:14px;gap:18px}
.spec-label{color:#9ea5b0}.unknown{color:#faab6d}.review-note{font-size:12px;color:#99a1ad;margin-top:18px;line-height:1.6}
[data-testid="stBaseButton-secondary"],[data-testid="stBaseButton-primary"]{border-radius:30px!important}
@media(max-width:650px){.review-card{padding:18px}.product-title{font-size:20px}.spec-row{grid-template-columns:110px 1fr}.block-container{padding-top:1rem}}
</style>''', unsafe_allow_html=True)

root = Path(os.environ.get('LAPTOP_RECOMMENDER_ROOT', str(ROOT))).resolve()
try:
    store = Store(root)
    service = Reviewer(store)
except Exception as exc:
    st.error('Could not open the review workspace: ' + str(exc))
    st.stop()

if st.session_state.get('flash'):
    message = st.session_state.pop('flash')
    st.success(message)

st.caption('ITM-360  /  COLLECTION DESK')
st.title('Build a catalogue you can verify')
st.write('Open the source, check the delivered configuration, then save your decision. Every candidate starts unverified.')
all_candidates = store.list()
counts = Counter(c['state'] for c in all_candidates)
canonical = store.canonical()
columns = st.columns(4)
for col, label, value in zip(columns, ['Awaiting review','Approved observations','Needs review','Verified configurations / 40'],
        [counts['pending'], counts['approved'], counts['needs_review'], str(sum(r['record_status']=='verified' for r in canonical['laptops'])) + ' / 40']):
    col.metric(label, value)

with st.sidebar:
    st.subheader('Review queue')
    reviewer = st.text_input('Reviewer code', value='Ro')
    retailer = st.selectbox('Retailer', ['All retailers','Gold One Computer','PTC Computer','Beckie Khmer'])
    states = st.multiselect('Show decisions', ['pending','needs_review','skipped','approved','rejected'], default=['pending','needs_review'])
    search = st.text_input('Find a name or SKU')
    st.caption('No network requests run when this page opens. Source buttons open the retailer in your browser.')
    with st.expander('Add a URL manually'):
        with st.form('manual_url'):
            manual_site = st.selectbox('Source site', ['goldone','ptc','beckie'])
            url = st.text_input('Product URL')
            title = st.text_input('Product name (optional)')
            add = st.form_submit_button('Add to queue')
        if add:
            try:
                _, inserted = manual_url(store, manual_site, url, title)
                st.session_state['flash'] = 'URL queued for manual entry.' if inserted else 'This URL observation is already queued.'
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    if st.button('Refresh queue'):
        st.rerun()

queue = [c for c in all_candidates if c['state'] in states
         and (retailer == 'All retailers' or c['fields']['retailer'] == retailer)
         and (not search or search.casefold() in (' '.join(str(v) for v in c['fields'].values()) + c['candidate_id']).casefold())]
if not queue:
    st.info('No candidates match this queue. Collect a smoke batch, queue existing observations, or add a URL in the sidebar.')
    st.code('python -m laptop_collection collect --site all --limit 3\npython -m laptop_collection seed-existing')
    st.stop()

lookup = {c['candidate_id']:c for c in queue}
selected = st.selectbox('Candidate', list(lookup), format_func=lambda i: (lookup[i]['fields'].get('full_name') or lookup[i]['fields'].get('retailer_sku') or i) + ' · ' + lookup[i]['fields']['retailer'] + ' · ' + lookup[i]['observed_date'])
candidate = lookup[selected]
f = candidate['fields']
esc = lambda v: html.escape(str(v or 'Unknown'))
amount = '$' + f['price_usd'] if f['price_usd'] else 'Price unknown'
rows = [('Processor',f['cpu_model']),('Graphics',f['gpu_model']),
        ('RAM', (f['ram_gb']+' GB '+f['ram_type']) if f['ram_gb'] else ''),
        ('Storage',(f['storage_gb']+' GB '+f['storage_type']) if f['storage_gb'] else ''),
        ('Display',f['display_text']),('Weight',f['weight_kg']+' kg' if f['weight_kg'] else ''),
        ('Delivered OS',f['delivered_os']),('Listed availability',f['availability_text']),('Condition',f['condition'])]
body = ''.join('<div class="spec-row"><span class="spec-label">'+esc(label)+'</span><span>'+esc(value)+'</span></div>' for label,value in rows)
st.markdown('<section class="review-card"><div class="card-top"><span class="eyebrow">Laptop review queue</span><span class="badge">'+esc(candidate['state'].replace('_',' ').title())+'</span></div>'
    '<div class="product-title">'+esc(f['full_name'] or f['model'])+'</div><div class="price">'+esc(amount)+'</div>'
    '<div class="meta">'+esc(f['retailer'])+' · Observed '+esc(candidate['observed_date'])+'<br>Manufacturer SKU: '+esc(f['manufacturer_sku'])+' · Shop SKU: '+esc(f['retailer_sku'])+'</div>'+body+
    '<div class="review-note">Unknown values remain unknown. Approval confirms recorded facts; it does not guarantee stock or software performance.</div></section>', unsafe_allow_html=True)
left, right = st.columns(2)
try:
    left.link_button('↗ Open laptop source', canonical_url(f['source_url']), use_container_width=True)
    evidence_url = candidate.get('listing_url') or candidate.get('evidence_url')
    if evidence_url:
        right.link_button('↗ Open catalogue evidence', canonical_url(evidence_url), use_container_width=True)
except ValueError:
    st.warning('The source URL needs correction before it can be opened.')

duplicate = service.preview(candidate)
if duplicate['kind'] in ('exact','conflict'):
    st.warning('Existing configuration: ' + duplicate['kind'] + ' · ' + ', '.join(r['configuration_id'] for r in duplicate['matches']))
if candidate.get('origin') == 'existing_canonical':
    st.warning('Historical CSV observation. For a current price, collect or manually import a fresh dated observation; do not assume the old price is current.')
with st.expander('Evidence and uncertainty', expanded=True):
    if candidate.get('flags'):
        st.write('Original extraction flags: ' + ' · '.join(flag.replace('_',' ') for flag in candidate['flags']))
    st.caption('Raw listed price: ' + (f['price_text'] or 'Unknown'))
    st.text(f.get('specification_evidence') or 'No extracted specification evidence. Open the source and record the facts below.')
    st.caption('Candidate ' + selected + ' · revision ' + str(candidate['revision']))

if candidate['state'] in ('approved','rejected'):
    st.info('Completed review. A new price or changed product needs a new observation.')
    st.json(store.reviews(selected))
    st.stop()

with st.form('review_' + selected + '_' + str(candidate['revision'])):
    edits = {}
    with st.expander('Edit product fields', expanded=False):
        columns = st.columns(2)
        for i, key in enumerate(['full_name','brand','model','manufacturer_sku','retailer_sku','cpu_model','gpu_model','gpu_vram_gb','ram_gb','ram_type','storage_gb','screen_inches','display_resolution','display_text','refresh_hz','weight_kg','delivered_os','price_usd','price_text','availability_text','source_url']):
            edits[key] = columns[i%2].text_input(key.replace('_',' ').title(), value=f.get(key,''))
        options = {
            'storage_type':['','ssd','hdd','ufs','emmc','mixed'],
            'gpu_type':['','integrated','dedicated'],
            'weight_evidence_type':['','retailer_claim','manufacturer_spec','measured'],
            'condition':['unknown','new','used','refurbished'],
            'purchase_type':['unknown','outright','installment_only'],
            'currency':['','USD']}
        for i,(key, values) in enumerate(options.items()):
            value = f.get(key,'')
            edits[key] = columns[i%2].selectbox(key.replace('_',' ').title(),values,index=values.index(value) if value in values else 0)
    with st.expander('Evidence required for approval', expanded=True):
        edits['manufacturer_sku_evidence'] = st.text_area('Manufacturer SKU evidence',value=f.get('manufacturer_sku_evidence',''),help='Record where the manufacturer part number is supported. BECKIE/LLS shop codes are separate.')
        edits['specification_evidence'] = st.text_area('Delivered specification evidence',value=f.get('specification_evidence',''))
        edits['condition_evidence'] = st.text_area('Evidence that this exact product is new',value=f.get('condition_evidence',''),help='Quote the condition statement or record a documented retailer confirmation. No used label is insufficient.')
        edits['condition_evidence_url'] = st.text_input('New condition evidence URL',value=f.get('condition_evidence_url') or f['source_url'])
        confirmations = {
            'new_condition':st.checkbox('I verified explicit new condition evidence'),
            'manufacturer_sku':st.checkbox('I verified the actual manufacturer SKU, separate from shop SKU'),
            'specifications':st.checkbox('I checked the exact delivered CPU, GPU, RAM, storage and display'),
            'price':st.checkbox('I verified the full outright USD purchase price')}
    with st.expander('Resolve duplicates or a documented hardware variant'):
        edits['resolution_notes'] = st.text_area('Resolution notes',value=f.get('resolution_notes',''))
        confirmations['confirm_existing_draft'] = st.checkbox('I explicitly confirm the matching draft and resolved its issues')
        confirmations['documented_variant'] = st.checkbox('This is a separately documented delivered hardware variant')
        edits['variant_evidence'] = st.text_area('Variant evidence (required for a separate hardware variant)',value=f.get('variant_evidence',''))
    notes = st.text_area('Review notes',help='Record missing information, reason for rejection, or what needs another check.')
    actions = st.columns(4)
    approve = actions[0].form_submit_button('✓ Approve',use_container_width=True)
    reject = actions[1].form_submit_button('✕ Reject',use_container_width=True)
    needs = actions[2].form_submit_button('Needs Review',type='primary',use_container_width=True)
    skip = actions[3].form_submit_button('Skip →',use_container_width=True)

if approve or reject or needs or skip:
    action = 'approve' if approve else 'reject' if reject else 'needs_review' if needs else 'skip'
    try:
        event = service.review(selected,action,edits,reviewer,notes,confirmations,expected_revision=candidate['revision'])
        st.session_state['flash'] = 'Saved: ' + event['state'].replace('_',' ') + '. ' + ' '.join(event['notices'])
        st.rerun()
    except (ValueError, OSError, RuntimeError) as exc:
        st.error(str(exc))
with st.expander('Review history'):
    st.json(store.reviews(selected))
