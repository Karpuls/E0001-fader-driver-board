#!/usr/bin/env python3
"""Clip J2 (R/A header, pins out past the south edge) silkscreen to the board: drop silk beyond
the edge and cut the body outline back to local x <= XMAX.  Usage: revC_j2silk.py <in> <out>"""
import re
import sys
import uuid
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from revC_strip_lib import blocks
XMAX = 3.8          # local +X points out of the board; edge is at local x 4.05
s = open(sys.argv[1]).read()
for a, e in blocks(s):
    if s[a:a + 12].startswith('(footprint') and '(property "Reference" "J2"' in s[a:e]:
        break
fp = s[a:e]
pat = re.compile(r'\t\t\((fp_line|fp_rect)\s*\n\t\t\t\(start ([-\d.]+) ([-\d.]+)\)\s*\n\t\t\t\(end ([-\d.]+) ([-\d.]+)\)(.*?)\n\t\t\)\n', re.S)
tmpl = None
def sub(m):
    global tmpl
    kind, x1, y1, x2, y2, rest = m.group(1), *map(float, m.group(2, 3, 4, 5)), m.group(6)
    if '"F.SilkS"' not in rest:
        return m.group(0)
    if min(x1, x2) >= XMAX:
        return ''
    if kind == 'fp_rect':     # body outline -> three lines inside the board
        r = re.sub(r'\(fill [^)]*\)\s*', '', rest)
        out = ''
        for (p, q) in (((x1, y1), (x1, y2)), ((x1, y1), (XMAX, y1)), ((x1, y2), (XMAX, y2))):
            rr = re.sub(r'\(uuid "[^"]*"\)', '(uuid "%s")' % uuid.uuid4(), r)
            out += '\t\t(fp_line\n\t\t\t(start %g %g)\n\t\t\t(end %g %g)%s\n\t\t)\n' % (p[0], p[1], q[0], q[1], rr)
        return out
    x1, x2 = min(x1, XMAX), min(x2, XMAX)
    return '\t\t(%s\n\t\t\t(start %g %g)\n\t\t\t(end %g %g)%s\n\t\t)\n' % (kind, x1, y1, x2, y2, rest)
nfp = pat.sub(sub, fp)
open(sys.argv[2], 'w').write(s[:a] + nfp + s[e:])
print('J2 silk clipped')
