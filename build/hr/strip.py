#!/usr/bin/env python3
"""Remove every top-level segment/arc/via from a .kicad_pcb (s-expression level)."""
import re, sys
def spans(s, head, indent="\n\t"):
    for m in re.finditer(re.escape(indent) + r"\(" + head + r"\b", s):
        d, j = 0, m.start() + len(indent)
        while True:
            c = s[j]
            if c == "(": d += 1
            elif c == ")":
                d -= 1
                if d == 0: break
            j += 1
        yield m.start(), j + 1
src = sys.argv[1]; dst = sys.argv[2] if len(sys.argv) > 2 else src
s = open(src).read()
cut = sorted(sp for h in ("segment", "arc", "via") for sp in spans(s, h))
out, i = [], 0
for a, b in cut:
    out.append(s[i:a]); i = b
out.append(s[i:])
open(dst, "w").write("".join(out))
print("removed", len(cut))
