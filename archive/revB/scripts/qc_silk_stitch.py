#!/usr/bin/env python3
"""Rev B layout QC fixes, part 2: GND stitching vias, JLC-size silkscreen (1.0 mm / 0.15 mm).

Usage: qc_silk_stitch.py <board.kicad_pcb>   (edits in place; restore the .kicad_pro afterwards)
RV1's off-board silk is trimmed separately by qc_rv1_silk.py (board + library together).
"""
import gc
import sys
import pcbnew

gc.disable()   # SWIG wrappers of removed items segfault when collected

PCB = sys.argv[1]
MM, TO = pcbnew.FromMM, pcbnew.ToMM
OX, OY = 100.0, 100.0
H, TH = 1.0, 0.15          # JLC minimum text height / stroke
GAP = 0.15                 # JLC silk-to-pad clearance

board = pcbnew.LoadBoard(PCB)

# ---- 7. GND stitching vias: near U3 and along the motor-control bundle ------------------------
gnd = board.FindNet('GND')
for x, y in [(76.5, 101.6), (82.0, 101.8), (85.0, 98.2), (95.0, 101.2), (110.0, 101.2), (125.0, 101.2)]:
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3)); v.SetNet(gnd)
    board.Add(v)


# ---- 2. silkscreen ----------------------------------------------------------------------------
def bb(item):
    b = item.GetBoundingBox()
    return [TO(b.GetLeft()), TO(b.GetTop()), TO(b.GetRight()), TO(b.GetBottom())]


def inside(r):
    x0, y0, x1, y1 = r[0] - OX, r[1] - OY, r[2] - OX, r[3] - OY
    return x0 >= -33.5 + 0.5 and x1 <= 73.5 - 0.5 and y0 >= -8.5 + 0.3 and y1 <= 8.5 - 0.3


def hit(r, rects, g=GAP):
    return any(r[0] < q[2] + g and r[2] > q[0] - g and r[1] < q[3] + g and r[3] > q[1] - g for q in rects)


sides = {pcbnew.F_Cu: pcbnew.F_SilkS, pcbnew.B_Cu: pcbnew.B_SilkS}
placed = {pcbnew.F_SilkS: [], pcbnew.B_SilkS: []}
obst = {pcbnew.F_SilkS: [], pcbnew.B_SilkS: []}
for fp in board.GetFootprints():
    for pad in fp.Pads():
        for cu, silk in sides.items():
            if pad.IsOnLayer(cu) or pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                obst[silk].append(bb(pad))
    for g in fp.GraphicalItems():
        if g.GetLayer() in placed and g.Type() not in (pcbnew.PCB_FIELD_T, pcbnew.PCB_TEXT_T):
            obst[g.GetLayer()].append(bb(g))

# board labels (x, y relative to the board centre)
LABELS = (('E0001 FADER DRIVER rev B', 2.0, 4.6, pcbnew.F_SilkS),
          ('J1: 1=+5V 2=SCL 3=SDA 4=GND', 2.0, 6.3, pcbnew.F_SilkS),
          ('ADDR: bridge=0', 50.0, 3.0, pcbnew.B_SilkS),
          ('SWD (TC2030)', 24.0, 3.6, pcbnew.B_SilkS))
for d in list(board.GetDrawings()):
    if d.Type() == pcbnew.PCB_TEXT_T:
        board.Remove(d)
for txt, x, y, layer in LABELS:
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt); t.SetLayer(layer)
    t.SetMirrored(layer == pcbnew.B_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(MM(H), MM(H))); t.SetTextThickness(MM(TH))
    t.SetPosition(pcbnew.VECTOR2I(MM(OX + x), MM(OY + y)))
    board.Add(t)
    r = bb(t)
    assert inside(r) and not hit(r, obst[layer]), (txt, r)
    placed[layer].append(r)

# hand placements where the greedy search would hide a ref (x, y, angle)
MANUAL = {'U2': (125.0, 97.4, 90), 'Q1': (153.25, 94.0, 90), 'D3': (128.6, 99.5, 0)}
for r, (x, y, a) in MANUAL.items():
    fp = board.FindFootprintByReference(r)
    ref = fp.Reference()
    ref.SetTextSize(pcbnew.VECTOR2I(MM(H), MM(H))); ref.SetTextThickness(MM(TH))
    ref.SetVisible(True); ref.SetTextAngleDegrees(a)
    ref.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    placed[pcbnew.F_SilkS].append(bb(ref))

hidden = []
order = sorted(board.GetFootprints(),
               key=lambda f: TO(f.GetBoundingBox(False).GetWidth()) * TO(f.GetBoundingBox(False).GetHeight()))
for fp in order:
    ref = fp.Reference()
    ref.SetTextSize(pcbnew.VECTOR2I(MM(H), MM(H))); ref.SetTextThickness(MM(TH))
    if fp.GetReference() in MANUAL:
        continue
    if fp.GetReference() == 'RV1':
        ref.SetTextAngleDegrees(0)
        ref.SetPosition(pcbnew.VECTOR2I(MM(OX - 3.0), MM(OY - 6.0)))
        placed[pcbnew.F_SilkS].append(bb(ref))
        continue
    silk = pcbnew.B_SilkS if fp.GetLayer() == pcbnew.B_Cu else pcbnew.F_SilkS
    ref.SetLayer(silk)
    ref.SetVisible(True)
    fb = fp.GetBoundingBox(False)
    cx, cy = TO(fb.GetCenter().x), TO(fb.GetCenter().y)
    hw, hh = TO(fb.GetWidth()) / 2, TO(fb.GetHeight()) / 2
    best = None
    for d in (0.15, 0.4, 0.8, 1.3, 1.8):
        for ang in (0, 90):
            ref.SetTextAngleDegrees(ang)
            for (x, y) in [(cx, cy - hh - d - H / 2), (cx, cy + hh + d + H / 2),
                           (cx - hw - d - H, cy), (cx + hw + d + H, cy),
                           (cx - hw - d, cy - hh - d), (cx + hw + d, cy - hh - d),
                           (cx - hw - d, cy + hh + d), (cx + hw + d, cy + hh + d)]:
                ref.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
                r = bb(ref)
                if inside(r) and not hit(r, obst[silk]) and not hit(r, placed[silk], 0.2):
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

pcbnew.SaveBoard(PCB, board)
print('hidden refs:', hidden)
