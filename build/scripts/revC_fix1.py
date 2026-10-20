#!/usr/bin/env python3
"""Rev C, step 3 (after TraceMaker pass 1): U4 split-pin joins, clean ADDR1 / ILM_ADC routes.
Usage: revC_fix1.py <in> <out>"""
import gc
import sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import pcbnew
gc.disable()
MM = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
LAY = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu}
def V(x, y): return pcbnew.VECTOR2I(MM(x), MM(y))
def path(net, layer, pts, w=0.2):
    n = b.FindNet(net); assert n is not None, net
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(*a)); t.SetEnd(V(*c)); t.SetWidth(MM(w)); t.SetLayer(LAY[layer]); t.SetNet(n); t.SetLocked(True); b.Add(t)

# U4 (RPW) split corner pins: join main pad and corner tab of pins 1, 4, 7, 10
u4 = b.FindFootprintByReference('U4')
by = {}
for p in u4.Pads():
    by.setdefault(p.GetNumber(), []).append(p)
for num in ('1', '4', '7', '10'):
    a, c = by[num]
    path(a.GetNetname(), 'F', [(a.GetPosition().x / 1e6, a.GetPosition().y / 1e6), (c.GetPosition().x / 1e6, c.GetPosition().y / 1e6)], 0.2)

# ADDR1: U1 pin 3 -> via -> straight down on B.Cu into JP2 pad 1
path('/ADDR1', 'F', [(140.363, 101.625), (139.68, 101.76), (138.42, 101.76)])
path('/ADDR1', 'B', [(138.42, 101.76), (138.42, 106.27), (138.75, 106.6)])
# ILM_ADC: R16 -> around the U1 north end -> pin 9 -> C19 at the pin
path('/ILM_ADC', 'F', [(146.19, 92.6), (142.18, 92.6), (139.32, 95.46), (139.32, 97.38), (139.665, 97.725)])
path('/ILM_ADC', 'F', [(140.363, 97.725), (141.45, 97.725), (142.09, 98.365)])
pcbnew.SaveBoard(sys.argv[2], b)
print('saved', sys.argv[2])
