#!/usr/bin/env python3
"""Pull RV1's silkscreen inside the 107 x 17 mm board (board instance and Fader library together,
so DRC sees no library mismatch). Footprint-local coordinates; RV1 sits at (100, 100), rotation 0.

Usage: qc_rv1_silk.py <board.kicad_pcb> <ALPS_RSA0N11M9A0J.kicad_mod>
"""
import re
import sys

# motor box: only its right edge lies on the board; the rest overhangs and can never be printed
DROP = [((-72.68, -9.12), (-27.19, -9.12)), ((-72.68, 9.12), (-72.68, -9.12)), ((-27.19, 9.12), (-72.68, 9.12))]
MOVE = {((-27.19, -9.12), (-27.19, 9.12)): ((-27.19, -7.9), (-27.19, 7.9)),
        # body-end corner marks: the body overhangs the board edge, mark it 0.7 mm inside instead
        ((74.12, -8.02), (72.12, -8.02)): ((72.8, -7.8), (70.8, -7.8)),
        ((74.12, -8.02), (74.12, -6.02)): ((72.8, -7.8), (72.8, -5.8)),
        ((74.12, 8.02), (72.12, 8.02)): ((72.8, 7.8), (70.8, 7.8)),
        ((74.12, 8.02), (74.12, 6.02)): ((72.8, 7.8), (72.8, 5.8))}
TRI_OLD = '(xy 63.65 7.82) (xy 63.05 8.62) (xy 64.25 8.62)'
TRI_NEW = '(xy 63.65 7.05) (xy 63.05 7.85) (xy 64.25 7.85)'

LINE = re.compile(r'\t*\(fp_line\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)'
                  r'\s*\(stroke\s*\(width [\d.]+\)\s*\(type \w+\)\s*\)\s*\(layer "F\.SilkS"\)\s*\(uuid "[^"]*"\)\s*\)\n')


def fix(block):
    def sub(m):
        key = ((float(m.group(1)), float(m.group(2))), (float(m.group(3)), float(m.group(4))))
        if key in DROP:
            return ''
        if key in MOVE:
            (a, b), (c, d) = MOVE[key]
            return (m.group(0).replace(f'(start {m.group(1)} {m.group(2)})', f'(start {a} {b})')
                              .replace(f'(end {m.group(3)} {m.group(4)})', f'(end {c} {d})'))
        return m.group(0)
    out, n = LINE.subn(sub, block)
    out2 = re.sub(r'\(xy 63\.65 7\.82\)\s*\(xy 63\.05 8\.62\)\s*\(xy 64\.25 8\.62\)', TRI_NEW, out)
    assert out2 != out or TRI_NEW in out, 'pin-1 marker not found'
    return out2


pcb, mod = sys.argv[1], sys.argv[2]
s = open(mod).read()
open(mod, 'w').write(fix(s))

t = open(pcb).read()
i = t.index('(footprint "Fader:ALPS_RSA0N11M9A0J"')
depth, j = 0, i
while True:                      # find the end of the RV1 footprint s-expression
    c = t[j]
    depth += c == '('
    depth -= c == ')'
    j += 1
    if depth == 0:
        break
open(pcb, 'w').write(t[:i] + fix(t[i:j]) + t[j:])
print('RV1 silk trimmed')
