#!/usr/bin/env python3
"""Drop top-level board items by kind at the s-expression level (pcbnew Remove() crashes the SWIG
wrappers on this build).  Usage: revC_strip.py <in> <out> [keep_ref ...]
Removes: segment, arc, via, gr_text, and every footprint whose Reference is not in keep_ref."""
import re
import sys

src, out, keep = sys.argv[1], sys.argv[2], set(sys.argv[3:])
s = open(src).read()

def blocks(s):
    """yield (start, end) of each top-level child of (kicad_pcb ...)"""
    depth, i, start, n = 0, 0, None, len(s)
    instr = False
    while i < n:
        ch = s[i]
        if instr:
            if ch == '\\':
                i += 2
                continue
            if ch == '"':
                instr = False
        elif ch == '"':
            instr = True
        elif ch == '(':
            depth += 1
            if depth == 2:
                start = i
        elif ch == ')':
            if depth == 2:
                yield start, i + 1
            depth -= 1
        i += 1

drop = []
for a, e in blocks(s):
    head = re.match(r'\((\w+)', s[a:a + 40]).group(1)
    if head in ('segment', 'arc', 'via', 'gr_text'):
        drop.append((a, e))
    elif head == 'footprint':
        ref = re.search(r'\(property "Reference" "([^"]*)"', s[a:e]).group(1)
        if ref not in keep:
            drop.append((a, e))
outs, last = [], 0
for a, e in drop:
    outs.append(s[last:a])
    last = e
    while last < len(s) and s[last] in ' \t\r\n':
        last += 1
outs.append(s[last:])
open(out, 'w').write(''.join(outs))
print('dropped', len(drop), 'items')
