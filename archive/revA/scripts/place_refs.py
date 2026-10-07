#!/usr/bin/env python3
"""Place silkscreen reference designators in free spots (or hide them when there is no room)."""
import os, sys, subprocess
import pcbnew

PROJ = '/home/karpulis/KiCad/E0001 - fader driver board'
PCB = os.path.join(PROJ, 'E0001_fader_driver.kicad_pcb')
MM, TO = pcbnew.FromMM, pcbnew.ToMM
OX, OY = 100.0, 100.0
OUTLINE = [(-33.5, -8.4), (57.9, -8.4), (57.9, -7.8), (73.5, -7.8), (73.5, 7.8), (57.9, 7.8), (57.9, 8.4), (-33.5, 8.4)]
H, TH = 0.7, 0.12          # text height / stroke
GAP = 0.12                 # clearance from silk text to pads / other silk

board = pcbnew.LoadBoard(PCB)

def bb(item):
    b = item.GetBoundingBox()
    return [TO(b.GetLeft()), TO(b.GetTop()), TO(b.GetRight()), TO(b.GetBottom())]

def inside(r):
    # rectangle fully inside the outline with a 0.2 mm margin (outline is a union of 2 rectangles)
    x0, y0, x1, y1 = r[0] - OX, r[1] - OY, r[2] - OX, r[3] - OY
    m = 0.2
    in_main = x0 >= -33.5 + m and x1 <= 57.9 - m and y0 >= -8.4 + m and y1 <= 8.4 - m
    in_end = x0 >= 57.9 - 1 and x1 <= 73.5 - m and y0 >= -7.8 + m and y1 <= 7.8 - m
    in_both = x0 >= -33.5 + m and x1 <= 73.5 - m and y0 >= -7.8 + m and y1 <= 7.8 - m
    return in_main or in_end or in_both

def hit(r, rects, g=GAP):
    for q in rects:
        if r[0] < q[2] + g and r[2] > q[0] - g and r[1] < q[3] + g and r[3] > q[1] - g:
            return True
    return False

sides = {pcbnew.F_Cu: (pcbnew.F_SilkS, pcbnew.F_Mask), pcbnew.B_Cu: (pcbnew.B_SilkS, pcbnew.B_Mask)}
placed = {pcbnew.F_SilkS: [], pcbnew.B_SilkS: []}
obst = {pcbnew.F_SilkS: [], pcbnew.B_SilkS: []}
for fp in board.GetFootprints():
    for pad in fp.Pads():
        for cu, (silk, _) in sides.items():
            if pad.IsOnLayer(cu) or pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                obst[silk].append(bb(pad))
    for g in fp.GraphicalItems():
        if g.GetLayer() in placed and g.Type() != pcbnew.PCB_FIELD_T and g.Type() != pcbnew.PCB_TEXT_T:
            obst[g.GetLayer()].append(bb(g))
# vias: keep text off via pads too (cleaner look)
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        for silk in placed:
            obst[silk].append(bb(t))

LABELS = (('E0001 FADER DRIVER rev A', 2.0, 4.6, pcbnew.F_SilkS),
          ('J1: 1=+5V 2=SCL 3=SDA 4=GND', 2.0, 6.3, pcbnew.F_SilkS),
          ('ADDR: bridge=0', 50.3, 6.9, pcbnew.B_SilkS),
          ('SWD (TC2030)', 24.5, 3.6, pcbnew.B_SilkS))
for txt, x, y, layer in LABELS:
    sz = 0.7 if layer == pcbnew.B_SilkS else 0.9
    w = len(txt) * sz * 0.8
    placed[layer].append([OX + x - w / 2, OY + y - sz / 2, OX + x + w / 2, OY + y + sz / 2])

hidden = []
order = sorted(board.GetFootprints(), key=lambda f: (TO(f.GetBoundingBox(False).GetWidth()) * TO(f.GetBoundingBox(False).GetHeight())))
for fp in order:
    ref = fp.Reference()
    if fp.GetReference() == 'RV1':
        # fader: label sits in the free stretch under the channel
        ref.SetTextSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0))); ref.SetTextThickness(MM(0.15))
        ref.SetTextAngleDegrees(0)
        ref.SetPosition(pcbnew.VECTOR2I(MM(OX - 3.0), MM(OY - 6.0)))
        placed[pcbnew.F_SilkS].append(bb(ref))
        continue
    silk = pcbnew.B_SilkS if fp.GetLayer() == pcbnew.B_Cu else pcbnew.F_SilkS
    ref.SetLayer(silk)
    ref.SetTextSize(pcbnew.VECTOR2I(MM(H), MM(H))); ref.SetTextThickness(MM(TH))
    ref.SetVisible(True)
    fb = fp.GetBoundingBox(False)          # without text
    cx, cy = TO(fb.GetCenter().x), TO(fb.GetCenter().y)
    hw, hh = TO(fb.GetWidth()) / 2, TO(fb.GetHeight()) / 2
    best = None
    for d in (0.15, 0.4, 0.8, 1.3):
        for ang in (0, 90):
            ref.SetTextAngleDegrees(ang)
            cands = [(cx, cy - hh - d - H / 2), (cx, cy + hh + d + H / 2),
                     (cx - hw - d - H, cy), (cx + hw + d + H, cy),
                     (cx - hw - d, cy - hh - d), (cx + hw + d, cy - hh - d),
                     (cx - hw - d, cy + hh + d), (cx + hw + d, cy + hh + d)]
            for (x, y) in cands:
                ref.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
                r = bb(ref)
                if inside(r) and not hit(r, obst[silk]) and not hit(r, placed[silk], 0.15):
                    best = (x, y, ang)
                    break
            if best:
                break
        if best:
            break
    if best:
        ref.SetTextAngleDegrees(best[2])
        ref.SetPosition(pcbnew.VECTOR2I(MM(best[0]), MM(best[1])))
        placed[silk].append(bb(ref))
    else:
        ref.SetVisible(False)
        hidden.append(fp.GetReference())

for d in list(board.GetDrawings()):
    if d.Type() == pcbnew.PCB_TEXT_T:
        board.Remove(d)
for txt, x, y, layer in LABELS:
    sz = 0.7 if layer == pcbnew.B_SilkS else 0.9
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt); t.SetLayer(layer)
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    t.SetTextSize(pcbnew.VECTOR2I(MM(sz), MM(sz))); t.SetTextThickness(MM(0.15))
    t.SetPosition(pcbnew.VECTOR2I(MM(OX + x), MM(OY + y)))
    board.Add(t)
pcbnew.SaveBoard(PCB, board)
subprocess.run([sys.executable, os.path.join(PROJ, 'build/scripts/patch_pro.py')], capture_output=True)
print('hidden refs:', hidden)
