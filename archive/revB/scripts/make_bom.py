#!/usr/bin/env python3
"""DigiKey BOM (CSV) from the schematic netlist. Excludes J1 (JST), RV1 (fader), DNP and not-in-BOM items."""
import sys, os, csv, re
sys.path.insert(0, os.path.dirname(__file__))
from sexp import parse, find, findall
PROJ = '/home/karpulis/KiCad/E0001 - fader driver board'
EXCLUDE = {'J1', 'RV1'}
net = parse(open(os.path.join(PROJ, 'build/out/netlist.net')).read())
groups, skipped = {}, []
for c in findall(find(net, 'components'), 'comp'):
    ref = find(c, 'ref')[1]
    props = {find(p, 'name')[1] for p in findall(c, 'property')}
    if ref in EXCLUDE or 'dnp' in props or 'exclude_from_bom' in props:
        skipped.append(ref); continue
    f = {find(x, 'name')[1]: (x[2] if len(x) > 2 else '') for x in findall(find(c, 'fields'), 'field')}
    fp = find(c, 'footprint')[1].split(':')[-1]
    key = (f.get('MPN', ''), f.get('Manufacturer', ''))
    g = groups.setdefault(key, dict(refs=[], value=find(c, 'value')[1], fp=fp, farnell=f.get('DigiKey', ''),
                                     desc=f.get('Description', '')))
    g['refs'].append(ref)
def nat(r):
    m = re.match(r'([A-Z]+)(\d+)', r); return (m.group(1), int(m.group(2)))
rows = sorted(groups.items(), key=lambda kv: nat(sorted(kv[1]['refs'], key=nat)[0]))
out = os.path.join(PROJ, 'bom', 'E0001_revB_digikey_bom.csv')
with open(out, 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['Quantity', 'Manufacturer Part Number', 'Manufacturer', 'DigiKey Part Number', 'Value', 'Package', 'Designators', 'Description'])
    total = 0
    for (mpn, mfr), g in rows:
        refs = sorted(g['refs'], key=nat)
        total += len(refs)
        w.writerow([len(refs), mpn, mfr, g['farnell'], g['value'], g['fp'], ' '.join(refs), g['desc']])
print('wrote', out, len(rows), 'lines,', total, 'parts; excluded:', ' '.join(sorted(skipped, key=nat)))
