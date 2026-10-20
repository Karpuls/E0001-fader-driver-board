#!/usr/bin/env python3
"""Rev B layout QC fixes, part 1: reroutes, width cleanup, tiny segments, acute corners.

Usage: qc_route_fixes.py <board.kicad_pcb>   (edits in place; restore the .kicad_pro afterwards,
pcbnew.SaveBoard rewrites it)
"""
import gc
import sys
import pcbnew

gc.disable()

PCB = sys.argv[1]
b = pcbnew.LoadBoard(PCB)
MM, T = pcbnew.FromMM, pcbnew.ToMM
L = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu}


def net(name):
    n = b.FindNet(name)
    assert n is not None, name
    return n


def tracks(netname, kind=None):
    out = []
    for t in b.GetTracks():
        if t.GetNetname() != netname:
            continue
        isvia = t.Type() == pcbnew.PCB_VIA_T
        if kind == 'via' and not isvia or kind == 'seg' and isvia:
            continue
        out.append(t)
    return out


def pt(t, which):
    p = t.GetStart() if which == 0 else t.GetEnd()
    return (T(p.x), T(p.y))


def near(a, b_, tol=0.002):
    return abs(a[0] - b_[0]) < tol and abs(a[1] - b_[1]) < tol


_removed = []   # keep SWIG wrappers of removed items alive: letting them be collected segfaults


def delete(t):
    t.SetLocked(False)
    b.Remove(t)
    _removed.append(t)


def delseg(netname, p0, p1, tol=0.002):
    """Delete the segment with endpoints p0/p1 (either order)."""
    hit = [t for t in tracks(netname, 'seg')
           if (near(pt(t, 0), p0, tol) and near(pt(t, 1), p1, tol)) or
              (near(pt(t, 0), p1, tol) and near(pt(t, 1), p0, tol))]
    assert len(hit) == 1, (netname, p0, p1, len(hit))
    delete(hit[0])


def delvia(netname, p, tol=0.002):
    hit = [t for t in tracks(netname, 'via') if near((T(t.GetPosition().x), T(t.GetPosition().y)), p, tol)]
    assert len(hit) == 1, (netname, p, len(hit))
    delete(hit[0])


def delnet(netname, layer=None, keep=lambda t: False):
    for t in tracks(netname):
        if layer and (t.Type() == pcbnew.PCB_VIA_T or t.GetLayer() != L[layer]):
            continue
        if not keep(t):
            delete(t)


def path(netname, layer, pts, w=0.2):
    n = net(netname)
    for a, c in zip(pts, pts[1:]):
        s = pcbnew.PCB_TRACK(b)
        s.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
        s.SetEnd(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])))
        s.SetWidth(MM(w))
        s.SetLayer(L[layer])
        s.SetNet(n)
        b.Add(s)


def via(netname, p, d=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(MM(p[0]), MM(p[1])))
    v.SetWidth(MM(d))
    v.SetDrill(MM(drill))
    v.SetNet(net(netname))
    b.Add(v)


def setw(netname, p0, p1, w):
    hit = [t for t in tracks(netname, 'seg')
           if (near(pt(t, 0), p0) and near(pt(t, 1), p1)) or (near(pt(t, 0), p1) and near(pt(t, 1), p0))]
    assert len(hit) == 1, (netname, p0, p1)
    hit[0].SetLocked(False)
    hit[0].SetWidth(MM(w))


def move_end(netname, old, new):
    """Move whichever end of a segment sits at `old` to `new`."""
    hit = 0
    for t in tracks(netname, 'seg'):
        for i in (0, 1):
            if near(pt(t, i), old):
                t.SetLocked(False)
                v = pcbnew.VECTOR2I(MM(new[0]), MM(new[1]))
                t.SetStart(v) if i == 0 else t.SetEnd(v)
                hit += 1
    assert hit == 1, (netname, old, hit)


# ---- 1. ADDR0 / ADDR1: via under the U1 body, straight B.Cu run to JP1 / JP2 ----------------
delnet('/ADDR0')
delnet('/ADDR1')
path('/ADDR0', 'F', [(141.137, 100.325), (142.5, 100.325)])
via('/ADDR0', (142.5, 100.325))
path('/ADDR0', 'B', [(142.5, 100.325), (136.75, 106.075), (136.75, 106.9)])
path('/ADDR1', 'F', [(141.137, 100.975), (142.175, 100.975), (142.5, 101.3)])
via('/ADDR1', (142.5, 101.3))
path('/ADDR1', 'B', [(142.5, 101.3), (140.15, 103.65), (140.15, 106.9)])

# NRST B.Cu used to cross the ADDR column at y 101.6; move it up to y 99.675 above the ADDR vias
delseg('/NRST', (145.2, 99.675), (143.275, 101.6))
delseg('/NRST', (143.275, 101.6), (133.6, 101.6))
path('/NRST', 'B', [(145.2, 99.675), (135.525, 99.675), (133.6, 101.6)])

# ADDR2: drop the 0.15 dog-leg and the snapping stub
delnet('/ADDR2', 'F')
path('/ADDR2', 'F', [(146.863, 102.275), (144.169, 102.275), (143.1356, 103.3081)])

# SWCLK: remove the hairpin around J2, via right next to J2 pad 4
delnet('/SWCLK')
path('/SWCLK', 'F', [(141.137, 102.275), (139.369, 102.275), (135.976, 105.668), (133.47, 105.668), (133.0, 105.198)])
via('/SWCLK', (133.0, 105.198))
path('/SWCLK', 'B', [(133.0, 105.198), (133.0, 104.235)])

# ---- 4/6. motor-control bundle: IN1 / IN2 / nSLEEP all 0.2 mm, nSLEEP runs under IN2 ----------
# U1 end
for p0, p1 in [((140.9931, 98.5194), (141.1375, 98.375)), ((139.0391, 98.5194), (140.9931, 98.5194)),
               ((139.0391, 98.5194), (139.0371, 98.5194)), ((139.0371, 98.5194), (138.0449, 99.5116))]:
    delseg('/MOT_IN1', p0, p1)
path('/MOT_IN1', 'F', [(141.137, 98.375), (139.182, 98.375), (138.045, 99.512)])
for p0, p1 in [((138.9622, 99.1694), (140.9931, 99.1694)), ((140.9931, 99.1694), (141.1375, 99.025)),
               ((138.9622, 99.1694), (138.2133, 99.9183))]:
    delseg('/MOT_IN2', p0, p1)
path('/MOT_IN2', 'F', [(141.137, 99.025), (139.106, 99.025), (138.213, 99.918)])
# U3 end
for p0, p1 in [((80.2705, 100.25), (80.391, 100.1295)), ((81.1733, 99.5116), (80.5554, 100.1295)),
               ((80.391, 100.1295), (80.5554, 100.1295)), ((79.95, 100.25), (80.2705, 100.25))]:
    delseg('/MOT_IN1', p0, p1)
delseg('/MOT_IN1', (138.0449, 99.5116), (81.1733, 99.5116))
path('/MOT_IN1', 'F', [(138.045, 99.512), (82.4, 99.512), (81.662, 100.25), (79.95, 100.25)])
for p0, p1 in [((88.0195, 100.8208), (80.2727, 100.8208)), ((88.922, 99.9183), (88.0195, 100.8208)),
               ((80.2019, 100.75), (80.2727, 100.8208)), ((79.95, 100.75), (80.2019, 100.75))]:
    delseg('/MOT_IN2', p0, p1)
delseg('/MOT_IN2', (138.2133, 99.9183), (88.922, 99.9183))
path('/MOT_IN2', 'F', [(138.213, 99.918), (82.582, 99.918), (81.75, 100.75), (79.95, 100.75)])

delnet('/MOT_nSLEEP')
path('/MOT_nSLEEP', 'F', [(141.137, 99.675), (139.6, 99.675), (138.951, 100.324), (84.226, 100.324), (83.6, 100.95)])
via('/MOT_nSLEEP', (83.6, 100.95))
path('/MOT_nSLEEP', 'B', [(83.6, 100.95), (81.5, 98.85)])
via('/MOT_nSLEEP', (81.5, 98.85))
path('/MOT_nSLEEP', 'F', [(81.5, 98.85), (80.6, 99.75), (79.95, 99.75)])

# LED: no acute kink, 0.2 mm
delnet('/LED', keep=lambda t: near(pt(t, 0), (131.71, 97.7)) or near(pt(t, 1), (131.71, 97.7)) or
       (near(pt(t, 0), (132.859, 98.849), 0.01) and near(pt(t, 1), (137.972, 98.849), 0.01)))
move_end('/LED', (137.972, 98.849), (138.101, 98.849))
path('/LED', 'F', [(141.137, 97.725), (139.225, 97.725), (138.101, 98.849)])

# ---- 5. +3V3: remove the '>' kink at C3, plain branch to the J2 via -----------------------------
delseg('+3V3', (127.43, 93.45), (125.7375, 93.45))          # duplicate of the 0.3 trunk
for p0, p1 in [((127.6, 93.62), (128.189, 93.62)), ((128.189, 93.62), (129.1325, 94.5635)),
               ((129.1325, 94.5635), (128.6517, 95.0443)), ((128.6517, 95.0443), (128.6517, 95.2073)),
               ((128.6517, 95.2073), (127.9652, 95.2073)), ((127.9652, 95.2073), (127.6823, 95.4902)),
               ((127.5562, 95.6163), (127.6823, 95.4902)), ((127.5562, 100.1645), (127.5562, 95.6163))]:
    delseg('+3V3', p0, p1)
delvia('+3V3', (127.6823, 95.4902))
path('+3V3', 'F', [(129.0, 93.45), (129.0, 95.6)])
via('+3V3', (129.0, 95.6))
path('+3V3', 'B', [(129.0, 95.6), (127.5562, 97.0438), (127.5562, 100.1645)])

# TOUCH_SNS: overlapping back-tracking segment made an acute corner at R5
delseg('/TOUCH_SNS', (151.99, 99.025), (150.71, 99.025))

# ---- 3. remaining sub-0.1 mm snapping stubs (endpoints already sit inside the pads) -------------
removed = 0
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_TRACE_T and T(t.GetLength()) < 0.1:
        delete(t)
        removed += 1
print('stubs removed', removed)

# ---- 4. +5V widths: 0.6 mm feeds, 0.3 mm only at the U3 pins, 0.4 mm via stub at R8 ------------
setw('+5V', (80.52, 96.0), (80.52, 97.7), 0.6)
setw('+5V', (152.75, 94.0), (152.75, 94.9), 0.6)
delseg('+5V', (137.5, 96.0), (138.4, 95.81))
delvia('+5V', (137.5, 96.0))
via('+5V', (137.5, 95.81))
path('+5V', 'F', [(137.5, 95.81), (138.4, 95.81)], 0.4)

pcbnew.SaveBoard(PCB, b)
print('saved', PCB)
