#!/usr/bin/env python3
"""Delete top-level segments/arcs (and optionally vias) by net, at the s-expression level.
Usage: revC_sexp_del.py <in> <out> [--unlocked-only] [--vias] NET [NET ...]"""
import re
import sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from revC_strip_lib import blocks

args = sys.argv[1:]
src, out = args[0], args[1]
unl = '--unlocked-only' in args
vias = '--vias' in args
nets = {a for a in args[2:] if not a.startswith('--')}
s = open(src).read()
drop = []
for a, e in blocks(s):
    head = re.match(r'\((\w+)', s[a:a + 40]).group(1)
    if head in ('segment', 'arc') or (vias and head == 'via'):
        blk = s[a:e]
        net = re.search(r'\(net "([^"]*)"\)', blk).group(1)
        if net in nets and not (unl and '(locked yes)' in blk):
            drop.append((a, e))
outs, last = [], 0
for a, e in drop:
    outs.append(s[last:a]); last = e
    while last < len(s) and s[last] in ' \t\r\n':
        last += 1
outs.append(s[last:])
open(out, 'w').write(''.join(outs))
print('deleted', len(drop))
