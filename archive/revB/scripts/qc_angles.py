#!/usr/bin/env python3
"""Rev B layout QC fixes, part 3: put the remaining off-angle segments on 45 deg multiples.

Usage: qc_angles.py <board.kicad_pcb>   (edits in place; restore the .kicad_pro afterwards)
"""
import gc
import sys
import pcbnew

gc.disable()   # SWIG wrappers of removed items segfault when collected
PCB = sys.argv[1]
b = pcbnew.LoadBoard(PCB)
MM, T = pcbnew.FromMM, pcbnew.ToMM
_removed = []


def near(p, q, tol=0.002):
    return abs(T(p.x) - q[0]) < tol and abs(T(p.y) - q[1]) < tol


def V(p):
    return pcbnew.VECTOR2I(MM(p[0]), MM(p[1]))


def move_point(netname, old, new, vias=True):
    """Move every track end (and via) of `netname` sitting at `old` to `new`."""
    n = 0
    for t in b.GetTracks():
        if t.GetNetname() != netname:
            continue
        t.SetLocked(False)
        if t.Type() == pcbnew.PCB_VIA_T:
            if vias and near(t.GetPosition(), old):
                t.SetPosition(V(new)); n += 1
            continue
        if near(t.GetStart(), old):
            t.SetStart(V(new)); n += 1
        if near(t.GetEnd(), old):
            t.SetEnd(V(new)); n += 1
    assert n, (netname, old)


# GND pad-to-via stubs: slide the via onto a 45 deg line from the pad
for old, new in [((128.2063, 98.4145), (128.3125, 98.2)),     # D3
                 ((172.6, 104.4611), (172.486, 104.461)),     # J1 shield
                 ((172.6, 97.0111), (172.486, 97.011)),       # J1 shield
                 ((116.484, 95.125), (116.825, 95.125)),      # D1
                 ((150.6256, 95.92), (150.41, 95.92)),        # C7
                 ((78.6129, 100.9875), (78.2875, 100.9875)),  # U3 pin 4
                 ((153.1, 101.7263), (153.1, 101.6))]:        # D2
    move_point('GND', old, new)

# FADER_POS into R7: move the bend so the last leg is 45 deg
move_point('/FADER_POS', (151.1, 97.075), (151.115, 97.075))

# MOTOR_P/N into the fader motor pads: one straight 45 deg leg instead of a kinked pair
for netname, mid, end, new_end in [('/MOTOR_P', (71.0, 103.48), (70.45, 104.0), (70.45, 104.03)),
                                   ('/MOTOR_N', (71.0, 96.52), (70.45, 96.0), (70.45, 95.97))]:
    for t in list(b.GetTracks()):
        if t.GetNetname() == netname and t.Type() == pcbnew.PCB_TRACE_T and \
                {(round(T(t.GetStart().x), 3), round(T(t.GetStart().y), 3)),
                 (round(T(t.GetEnd().x), 3), round(T(t.GetEnd().y), 3))} == {mid, end}:
            t.SetLocked(False); b.Remove(t); _removed.append(t)
    move_point(netname, mid, new_end, vias=False)

pcbnew.SaveBoard(PCB, b)
print('saved', PCB)
