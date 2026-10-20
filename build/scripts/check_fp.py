#!/usr/bin/env python3
"""Check that every footprint exists and that symbol pin numbers match footprint pad numbers."""
import os, re, sys, glob
sys.path.insert(0, os.path.dirname(__file__))
from sexp import parse, find, findall
import symlib
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
F = '/home/karpulis/.backplane-bend/kicad/10.0.6/share/kicad/footprints'
LOCAL = {'E0001': 'lib/E0001.pretty', 'Fader': 'lib/Fader.pretty'}
bad, seen, n = [], set(), 0
for f in glob.glob(os.path.join(PROJ, '*.kicad_sch')):
    root = parse(open(f).read())
    libs = {s[1]: s for s in findall(find(root, 'lib_symbols') or [], 'symbol')}
    for s in findall(root, 'symbol'):
        lid = find(s, 'lib_id')[1]
        if lid.startswith('power:'):
            continue
        pr = {p[1]: p[2] for p in findall(s, 'property')}
        fp = pr.get('Footprint', '')
        n += 1
        if not fp:
            bad.append((pr['Reference'], 'no footprint'))
            continue
        lib, name = fp.split(':')
        path = os.path.join(PROJ, LOCAL[lib], name + '.kicad_mod') if lib in LOCAL else os.path.join(F, lib + '.pretty', name + '.kicad_mod')
        if not os.path.exists(path):
            bad.append((pr['Reference'], 'missing ' + fp))
            continue
        if (lid, fp) in seen:
            continue
        seen.add((lid, fp))
        pads = set(re.findall(r'\(pad "([^"]+)"', open(path).read())) - {''}
        pins = set(p['number'] for p in symlib.pins(libs[lid]))
        if pins - pads or pads - pins:
            bad.append((lid, fp, 'pins w/o pad', sorted(pins - pads), 'pads w/o pin', sorted(pads - pins)))
print(n, 'symbols,', len(seen), 'symbol/footprint pairs')
for b in bad:
    print('  ', b)
