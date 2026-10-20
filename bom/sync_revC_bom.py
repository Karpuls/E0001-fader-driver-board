#!/usr/bin/env python3
"""E0001 rev C final BOM from a fresh kicad-cli flat export. usage: e0001c_final.py flat.csv planning_bom.csv out.csv"""
import csv, json, os, re, sys, urllib.request, urllib.parse, collections
env = {k: v.strip().strip('"\'') for k, v in (l.strip().split('=', 1) for l in open(os.path.expanduser('~/.backplane-bend/secrets/api.env')) if '=' in l)}
cid, sec = env['DIGIKEY_CLIENT_ID'], env['DIGIKEY_CLIENT_SECRET']
tok = json.load(urllib.request.urlopen(urllib.request.Request('https://api.digikey.com/v1/oauth2/token',
    urllib.parse.urlencode({'client_id': cid, 'client_secret': sec, 'grant_type': 'client_credentials'}).encode())))['access_token']
H = {'Authorization': 'Bearer ' + tok, 'X-DIGIKEY-Client-Id': cid, 'Content-Type': 'application/json',
     'X-DIGIKEY-Locale-Site': 'LV', 'X-DIGIKEY-Locale-Currency': 'EUR', 'X-DIGIKEY-Locale-Language': 'en'}
def look(mpn):
    d = json.load(urllib.request.urlopen(urllib.request.Request('https://api.digikey.com/products/v4/search/keyword',
        json.dumps({'Keywords': mpn, 'Limit': 8, 'FilterOptionsRequest': {'MarketPlaceFilter': 'ExcludeMarketPlace'}}).encode(), H)))
    for p in d.get('Products', []):
        if p['ManufacturerProductNumber'].upper() == mpn.upper():
            vs = p['ProductVariations']; ct = [v for v in vs if 'Cut Tape' in v['PackageType']['Name']] or vs
            return p, ct[0]
    return None, None
flat, planp, outp = sys.argv[1:4]
plan = {}
for r in csv.DictReader(open(planp)): plan.setdefault(r['MPN'], r)
groups = collections.OrderedDict()
for r in csv.DictReader(open(flat)):
    if r['EXCL'] and r['EXCL'] != '0': continue
    k = (r['Value'] if not r['MPN'].startswith('RC0402FR-071ML') else '1M 1%', r['Footprint'].split(':')[-1], r['MPN'], bool(r['DNP'] and r['DNP'] != '0'))
    groups.setdefault(k, []).append(r['Ref'])
def key(ref): return (re.sub(r'\d', '', ref), int(re.sub(r'\D', '', ref) or 0))
rows, issues = [], []
for (val, fp, mpn, dnp), refs in groups.items():
    refs.sort(key=key); o = plan.get(mpn, {})
    base = dict(Qty=len(refs), QtyBasis='schematic', References=' '.join(refs), Value=val, Footprint=fp, MPN=mpn, DNP='DNP' if dnp else '', OwnerStock=o.get('OwnerStock', 'no'), Notes=o.get('Notes', ''))
    if mpn.startswith('RSA0N11'):
        base.update({k: o.get(k, '') for k in ('Supplier', 'Manufacturer', 'SupplierPN', 'Stock', 'Lifecycle', 'UnitEUR', 'LeadWeeks')}); rows.append(base); continue
    p, v = look('SM04B-GHS-TB' if mpn.startswith('SM04B') else mpn)
    if not p: issues.append(mpn); base.update(Supplier='?', SupplierPN='NOT FOUND'); rows.append(base); continue
    base.update(Supplier='DigiKey', Manufacturer=p['Manufacturer']['Name'], SupplierPN=v['DigiKeyProductNumber'], Stock=v.get('QuantityAvailableforPackageType') or 0, Lifecycle=p['ProductStatus']['Status'], UnitEUR=p.get('UnitPrice'), LeadWeeks=p.get('ManufacturerLeadWeeks'))
    if mpn.startswith('SM04B'):
        base.update(Supplier='LCSC', SupplierPN='LCSC C189895 (SM04B-GHS-TB(LF)(SN))', Stock=o.get('Stock', ''), UnitEUR='0.31 USD @5 (LCSC)', Notes=f"DigiKey {v['DigiKeyProductNumber']} stock {v.get('QuantityAvailableforPackageType') or 0}. Second sources: RS Online 1755704 / 7521797; LCSC C189895 (min order 5).")
    rows.append(base)
rows.append(dict(Supplier='PCB', Qty=3, QtyBasis='spec', References='JP1 JP2 JP3', Value='solder jumper', Footprint='SolderJumper-2 open', MPN='-', Manufacturer='-', SupplierPN='-', Stock='-', Lifecycle='-', UnitEUR='0', LeadWeeks='', DNP='', OwnerStock='no', Notes='Open solder jumpers on the PCB (not in the schematic BOM, no part)'))
f = ['Supplier','Qty','QtyBasis','References','Value','Footprint','MPN','Manufacturer','SupplierPN','Stock','Lifecycle','UnitEUR','LeadWeeks','DNP','OwnerStock','Notes']
w = csv.DictWriter(open(outp, 'w', newline=''), fieldnames=f); w.writeheader(); w.writerows(rows)
print(len(rows), 'lines;', sum(int(r['Qty']) for r in rows), 'parts; issues:', issues)
for r in rows:
    st = str(r.get('Stock', ''))
    if r['Supplier'] == 'DigiKey' and st.isdigit() and (int(st) < 20 * int(r['Qty']) or r['Lifecycle'] != 'Active'): print('LOW/NOT-ACTIVE:', r['MPN'], st, r['Lifecycle'], 'need', r['Qty'])
