#!/usr/bin/env python3
"""E0001 rev C BOM: parse the SPEC_revC.md BOM table, verify every DigiKey line via the API, write the CSV. usage: e0001c_bom.py out.csv"""
import csv, json, os, re, sys, urllib.request, urllib.parse
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
rows = json.load(open('/tmp/e1c_rows.json'))
out = []; issues = []
for c in rows:
    refs, qty, val, fp, mpn = c[0], int(c[1]), c[2].replace('**', ''), c[3], c[4].replace('**', '')
    refs = re.sub(r'C_BULK ×4 \((.*)\)', r'\1', refs).replace(',', '').replace('–', '-')
    if refs.startswith('JP1'):
        refs = 'JP1 JP2 JP3'
    base = dict(Qty=qty, QtyBasis='spec', References=refs, Value=val, Footprint=fp, MPN=mpn, DNP='DNP' if c[1] and 'DNP' in c[10] else '', OwnerStock='no', Notes='')
    if mpn in ('—', '-'):
        base.update(Supplier='PCB', Manufacturer='-', SupplierPN='-', Stock='-', Lifecycle='-', UnitEUR='0', LeadWeeks='', Notes='Open solder jumper (PCB feature, no part)'); out.append(base); continue
    if mpn.startswith('RSA0N11'):
        base.update(Supplier='Amazon.de', Manufacturer='Fastigeaty (seller Fadianshop)', SupplierPN='ASIN B0H45B29YK', Stock='not checked (Amazon page blocked)', Lifecycle='-', UnitEUR='', LeadWeeks='', OwnerStock='unknown', Notes='ALPS RSA0N11M9A0J-compatible clone, 100 mm motor fader'); out.append(base); continue
    p, v = look('SM04B-GHS-TB' if mpn.startswith('SM04B') else mpn)
    if not p: issues.append(mpn); base.update(Supplier='?', SupplierPN='NOT FOUND'); out.append(base); continue
    base.update(Supplier='DigiKey', Manufacturer=p['Manufacturer']['Name'], SupplierPN=v['DigiKeyProductNumber'], Stock=v.get('QuantityAvailableforPackageType') or 0, Lifecycle=p['ProductStatus']['Status'], UnitEUR=p.get('UnitPrice'), LeadWeeks=p.get('ManufacturerLeadWeeks'))
    if mpn.startswith('SM04B'):
        base.update(Supplier='LCSC', SupplierPN='LCSC C189895 (SM04B-GHS-TB(LF)(SN))', Stock='1900 (LCSC, 2026-10-19)', UnitEUR='0.31 USD @5 (LCSC)', OwnerStock='unknown',
                    Notes=f"DigiKey {v['DigiKeyProductNumber']} stock {base['Stock']} (16 w). Second sources: RS Online 1755704 / 7521797 (regional stock), LCSC C189895 (min order 5). E0003 uses the same LCSC part.")
    if mpn == 'STM32C051F6P6':
        q, w = look('STM32C051F8P6')
        base['Notes'] = 'Approved alternate STM32C051F8P6 (same TSSOP-20 pinout, 64 KB): ' + (f"{w['DigiKeyProductNumber']}, stock {w.get('QuantityAvailableforPackageType')}, EUR {q.get('UnitPrice')}" if q else 'not found') + '. Buy whichever is in stock.'
    out.append(base)
f = ['Supplier','Qty','QtyBasis','References','Value','Footprint','MPN','Manufacturer','SupplierPN','Stock','Lifecycle','UnitEUR','LeadWeeks','DNP','OwnerStock','Notes']
w = csv.DictWriter(open(sys.argv[1], 'w', newline=''), fieldnames=f); w.writeheader(); w.writerows(out)
print(len(out), 'lines;', sum(r['Qty'] for r in out), 'parts; issues:', issues)
for r in out:
    st = r.get('Stock', '')
    if r['Supplier'] == 'DigiKey' and str(st).isdigit() and (int(st) < 20 * int(r['Qty']) or r['Lifecycle'] != 'Active'): print('LOW/NOT-ACTIVE:', r['MPN'], st, r['Lifecycle'], 'need', r['Qty'])
