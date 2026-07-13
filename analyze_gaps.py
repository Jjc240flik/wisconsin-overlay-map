#!/usr/bin/env python3
"""Analyze off-market parcels for acreage gaps."""
import json

off = json.load(open('/root/wisconsin-overlay-map/checkpoints/off_market_results.json'))
fs = json.load(open('/root/wisconsin-overlay-map/checkpoints/for_sale_results.json'))

fips_names = {'55087':'Outagamie','55009':'Brown','55025':'Dane',
              '55133':'Waukesha','55089':'Ozaukee','55105':'Rock',
              '55139':'Winnebago','55015':'Calumet'}

print("=== OFF-MARKET ===")
print(f"Total: {len(off)}")

off_with = sum(1 for p in off if p.get('lot_size_acres') is not None)
off_wo = sum(1 for p in off if p.get('lot_size_acres') is None)
print(f"With lot_size_acres: {off_with}")
print(f"Without lot_size_acres: {off_wo}")

by_county = {}
for p in off:
    fips = str(p.get('fips', p.get('_query_fips', '?')))
    by_county.setdefault(fips, {'total':0, 'missing':0})
    by_county[fips]['total'] += 1
    if p.get('lot_size_acres') is None:
        by_county[fips]['missing'] += 1

print()
for fips in sorted(by_county):
    c = by_county[fips]
    name = fips_names.get(fips, fips)
    print(f"  {name} ({fips}): {c['total']} total, {c['missing']} missing acres")

# For-sale
print(f"\n=== FOR-SALE ===")
print(f"Total: {len(fs)}")
fs_with = sum(1 for p in fs if p.get('lot_size_acres') is not None)
fs_wo = sum(1 for p in fs if p.get('lot_size_acres') is None)
print(f"With lot_size_acres: {fs_with}")
print(f"Without lot_size_acres: {fs_wo}")

# Fields available
print(f"\n=== SAMPLE FIELDS (off-market) ===")
keys = sorted(off[0].keys()) if off else []
print(keys)

# Total unique property IDs
off_ids = set(p['property_id'] for p in off)
fs_ids = set(p['property_id'] for p in fs)
print(f"\nUnique off-market property_ids: {len(off_ids)}")
print(f"Unique for-sale property_ids: {len(fs_ids)}")
print(f"Overlap: {len(off_ids & fs_ids)}")

# Priority for detail extraction: off-market parcels missing acres
wo_acres_ids = [p['property_id'] for p in off if p.get('lot_size_acres') is None]
print(f"\nOff-market needing detail (missing acres): {len(wo_acres_ids)}")
print("Sample property_ids needing detail:")
for pid in wo_acres_ids[:10]:
    print(f"  {pid}")
