#!/usr/bin/env python3
"""Rev B layout QC, round 2: acid-trap junctions, I2C reroute around the fader touch pad,
right-angle chamfers.

Usage: qc_round2.py <board.kicad_pcb>   (edits in place; restore the .kicad_pro afterwards,
pcbnew.SaveBoard rewrites it)
"""
import gc
import sys
import pcbnew

gc.disable()   # SWIG wrappers of removed items segfault when collected

PCB = sys.argv[1]
b = pcbnew.LoadBoard(PCB)
MM, T = pcbnew.FromMM, pcbnew.ToMM
L = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu}
_removed = []


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


def pt(t, i):
    p = t.GetStart() if i == 0 else t.GetEnd()
    return (T(p.x), T(p.y))


def near(a, c, tol=0.002):
    return abs(a[0] - c[0]) < tol and abs(a[1] - c[1]) < tol


def delete(t):
    t.SetLocked(False)
    b.Remove(t)
    _removed.append(t)


def delseg(netname, p0, p1):
    hit = [t for t in tracks(netname, 'seg')
           if (near(pt(t, 0), p0) and near(pt(t, 1), p1)) or (near(pt(t, 0), p1) and near(pt(t, 1), p0))]
    assert len(hit) == 1, (netname, p0, p1, len(hit))
    w = T(hit[0].GetWidth())
    delete(hit[0])
    return w


def delvia(netname, p):
    hit = [t for t in tracks(netname, 'via') if near((T(t.GetPosition().x), T(t.GetPosition().y)), p)]
    assert len(hit) == 1, (netname, p, len(hit))
    delete(hit[0])


def delnet(netname):
    for t in tracks(netname):
        delete(t)


def path(netname, layer, pts, w=0.2):
    n = b.FindNet(netname)
    for a, c in zip(pts, pts[1:]):
        s = pcbnew.PCB_TRACK(b)
        s.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
        s.SetEnd(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])))
        s.SetWidth(MM(w)); s.SetLayer(L[layer]); s.SetNet(n)
        b.Add(s)


def via(netname, p, d=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(MM(p[0]), MM(p[1])))
    v.SetWidth(MM(d)); v.SetDrill(MM(drill)); v.SetNet(b.FindNet(netname))
    b.Add(v)


def replace(netname, layer, old_pts, new_pts):
    """Swap the polyline old_pts (consecutive segments) for new_pts at the same width."""
    w = None
    for a, c in zip(old_pts, old_pts[1:]):
        w = delseg(netname, a, c)
    path(netname, layer, new_pts, w)


# ---- A1. +3V3 trunk through C3 pad 1 centre (y 93.62), chamfered down to U1 pin 4 and C4 ------
replace('+3V3', 'F', [(125.737, 93.45), (142.9, 93.45), (142.9, 96.4), (143.2, 96.7), (143.2, 100.975),
                      (146.863, 100.975), (148.8, 100.975), (148.8, 101.13), (149.395, 101.725)],
        [(125.737, 93.62), (142.0, 93.62), (143.2, 94.82), (143.2, 100.475), (143.7, 100.975),
         (148.645, 100.975), (148.8, 101.13), (149.395, 101.725)])
delseg('+3V3', (127.6, 93.62), (127.43, 93.45))
replace('+3V3', 'F', [(129.0, 93.45), (129.0, 95.6)], [(129.0, 93.62), (129.0, 95.6)])

# ---- A2. NRST (B.Cu): C6 branch meets the J2 diagonal at 90 deg instead of a 45 deg wedge -------
delseg('/NRST', (135.525, 99.675), (133.6, 101.6))
delseg('/NRST', (133.6, 101.6), (133.0, 102.2))
delseg('/NRST', (133.6, 101.6), (129.9, 101.6))
path('/NRST', 'B', [(135.525, 99.675), (133.3, 101.9), (133.0, 102.2)])
path('/NRST', 'B', [(129.9, 101.6), (133.0, 101.6), (133.3, 101.9)])

# ---- A3. VSENSE: R8 joins the U1 track at a 90 deg T, not into the R9 pad at 45 deg ------------
delseg('/VSENSE', (139.0523, 96.5327), (138.51, 97.075))
delseg('/VSENSE', (138.51, 97.075), (141.1375, 97.075))
path('/VSENSE', 'F', [(139.0523, 96.5327), (139.0523, 97.075)])
path('/VSENSE', 'F', [(138.51, 97.075), (139.0523, 97.075), (141.137, 97.075)])

# ---- B. I2C: straight parallel pair from U1, down between FG and RV1 pad 1, under pad 1 (GND),
#         up into J1 at x >= 166.8, well clear of the touch pad T ---------------------------------
# ADDR2 via moves up under the U1 body so SCL can run straight at y 103.6
delnet('/ADDR2')
path('/ADDR2', 'F', [(146.863, 102.275), (144.2, 102.275)])
via('/ADDR2', (144.2, 102.275))
path('/ADDR2', 'B', [(144.2, 102.275), (143.55, 102.925), (143.55, 106.9)])

delnet('/I2C_SCL')
delnet('/I2C_SDA')
path('/I2C_SCL', 'F', [(141.137, 102.925), (141.812, 103.6), (157.5, 103.6), (161.55, 107.65),
                       (166.8, 107.65), (167.25, 107.2), (167.25, 101.075), (167.7, 100.625),
                       (168.55, 100.625)])
path('/I2C_SDA', 'F', [(146.863, 102.925), (157.475, 102.925), (161.75, 107.2), (166.35, 107.2),
                       (166.8, 106.75), (166.8, 99.825), (167.25, 99.375), (168.55, 99.375)])

# ---- C9. right-angle chamfers ------------------------------------------------------------------
replace('/VIN', 'B', [(165.5, 100.0), (154.4, 100.0), (154.4, 93.15)],
        [(165.5, 100.0), (155.4, 100.0), (154.4, 99.0), (154.4, 93.15)])
replace('+5V', 'F', [(87.4, 96.0), (77.72, 96.0), (77.72, 97.7)],
        [(87.4, 96.0), (78.32, 96.0), (77.72, 96.6), (77.72, 97.7)])
replace('/LDO_IN', 'F', [(120.575, 93.4), (122.0, 93.4), (122.0, 93.625), (123.087, 93.625)],
        [(120.575, 93.4), (121.775, 93.4), (122.0, 93.625), (123.087, 93.625)])
# TOUCH_ELEC enters D2 pad 1 at 45 deg from R5 instead of a vertical-in / horizontal-out corner
replace('/TOUCH_ELEC', 'F', [(153.01, 99.025), (153.45, 99.465), (153.45, 100.55)],
        [(153.01, 99.025), (153.01, 100.11), (153.45, 100.55)])

# ---- C10. SWDIO on U1 pin 18's centre line ---------------------------------------------------
replace('/SWDIO', 'F', [(141.1375, 101.625), (141.0158, 101.5033), (135.0565, 101.5033), (131.73, 104.8298)],
        [(141.137, 101.625), (134.934, 101.625), (131.73, 104.8298)])

pcbnew.SaveBoard(PCB, b)
print('saved', PCB)
