"""Assess recorded offer freshness without changing historical observations."""
from datetime import date, datetime, timedelta, timezone


def assess_offer(offer, rechecks, policy, reference_date=None, attestation=None):
    freeze = date.fromisoformat(reference_date or policy.get('actual_freeze_date') or policy['intended_freeze_date'])
    maximum = policy['maximum_offer_age_days']
    observed = date.fromisoformat(offer['observed_date'])
    confirmations = [(observed, 'original_observation')]
    # Only an actual passed human source recheck of this exact offer confirms
    # its price again. Approval/import times and manufacturer pages do not.
    for row in rechecks:
        if (row.get('offer_id') == offer['offer_id']
                and row.get('evidence_id') == offer['evidence_id']
                and row.get('second_check_status') == 'passed'
                and row.get('second_checked_by') and row.get('findings')):
            stamp = datetime.fromisoformat(row['second_checked_at'].replace('Z', '+00:00'))
            if stamp.utcoffset() is None:
                raise ValueError('Source recheck needs a timezone-aware timestamp')
            checked = stamp.astimezone(timezone(timedelta(hours=7))).date()
            if checked >= observed:
                confirmations.append((checked, 'passed_manual_source_recheck'))
    usable = [(day, basis) for day, basis in confirmations if day <= freeze]
    if not usable:
        return dict(freshness_status='after_reference_date', confirmed_date='',
                    confirmation_basis='', age_days='')
    day, basis = max(usable)
    age = (freeze - day).days
    result = dict(freshness_status='within_window' if age <= maximum else 'needs_fresh_source_check',
                  confirmed_date=day.isoformat(), confirmation_basis=basis, age_days=age)
    if age <= maximum or not attestation or offer['offer_id'] not in attestation.get('offer_ids', []):
        return result
    first = date.fromisoformat(attestation['earliest_check_date'])
    last = date.fromisoformat(attestation['latest_check_date'])
    if first > last or first < observed or last > freeze:
        return result
    if last <= day:
        return result
    oldest_age, youngest_age = (freeze-first).days, (freeze-last).days
    if oldest_age <= maximum:
        status = 'within_window'
    elif youngest_age <= maximum:
        status = 'check_date_uncertain'
    else:
        status = 'needs_fresh_source_check'
    return dict(freshness_status=status, confirmed_date='',
                confirmation_basis=f'user_reported_check_range:{first.isoformat()}/{last.isoformat()}', age_days='')
