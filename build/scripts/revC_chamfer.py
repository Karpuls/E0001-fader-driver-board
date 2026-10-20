#!/usr/bin/env python3
"""Chamfer right-angle corners on free track.  Usage: revC_chamfer.py <in> <out> net:layer:x:y[:c] ..."""
import gc
import math
import sys
import pcbnew
gc.disable()
b = pcbnew.LoadBoard(sys.argv[1])
MM = pcbnew.FromMM
for spec in sys.argv[3:]:
    f = spec.split(':')
    net, layer, x, y = f[0], f[1], float(f[2]), float(f[3])
    c = float(f[4]) if len(f) > 4 else 0.4
    P = pcbnew.VECTOR2I(MM(x), MM(y))
    segs = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == net and t.GetLayerName() == layer
            and (abs(t.GetStart().x - P.x) < 2000 and abs(t.GetStart().y - P.y) < 2000 or abs(t.GetEnd().x - P.x) < 2000 and abs(t.GetEnd().y - P.y) < 2000)]
    assert len(segs) == 2, (spec, len(segs))
    pts = []
    for t in segs:
        far = t.GetEnd() if abs(t.GetStart().x - P.x) < 2000 and abs(t.GetStart().y - P.y) < 2000 else t.GetStart()
        dx, dy = far.x - P.x, far.y - P.y
        L = math.hypot(dx, dy)
        q = pcbnew.VECTOR2I(int(P.x + dx / L * MM(c)), int(P.y + dy / L * MM(c)))
        if abs(t.GetStart().x - P.x) < 2000 and abs(t.GetStart().y - P.y) < 2000:
            t.SetStart(q)
        else:
            t.SetEnd(q)
        pts.append(q)
    n = pcbnew.PCB_TRACK(b); n.SetStart(pts[0]); n.SetEnd(pts[1]); n.SetWidth(segs[0].GetWidth()); n.SetLayer(segs[0].GetLayer())
    n.SetNet(segs[0].GetNet()); n.SetLocked(True); b.Add(n)
pcbnew.SaveBoard(sys.argv[2], b)
print('chamfered', len(sys.argv) - 3)
