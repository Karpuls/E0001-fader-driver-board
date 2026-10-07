#!/usr/bin/env python3
"""Phase 2: GND vias, Freerouting (GND excluded), import, GND pours on both layers."""
import sys, os, re, subprocess, math, json
import pcbnew

PROJ = '/home/karpulis/KiCad/E0001 - fader driver board'
PCB = os.path.join(PROJ, 'E0001_fader_driver.kicad_pcb')
WORK = os.path.join(PROJ, 'build/route')
os.makedirs(WORK, exist_ok=True)
FR = ['/tmp/fbr_jre/jdk-25.0.4.1+1-jre/bin/java', '-Xmx1200m', '-Djava.awt.headless=true', '-jar', '/tmp/fbr_frjar/freerouting.jar']
MM, TO = pcbnew.FromMM, pcbnew.ToMM
OX, OY = 100.0, 100.0
OUTLINE = [(-33.5, -8.5), (73.5, -8.5), (73.5, 8.5), (-33.5, 8.5)]

def P(x, y):
    return pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))

board = pcbnew.LoadBoard(PCB)
gnd = board.FindNet('GND')
for t in list(board.GetTracks()):
    if t.GetNetCode() == gnd.GetNetCode():
        board.Remove(t)

# ---------------------------------------------------------- geometry helpers for free-spot search
def obstacles(exclude_net):
    obs = []   # (x0,y0,x1,y1) in mm, page coords, on F.Cu or through
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetCode() == exclude_net and exclude_net != 0:
                continue
            if not (pad.IsOnLayer(pcbnew.F_Cu) or pad.IsOnLayer(pcbnew.B_Cu)):
                if pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                    continue
            bb = pad.GetBoundingBox()
            obs.append((TO(bb.GetLeft()), TO(bb.GetTop()), TO(bb.GetRight()), TO(bb.GetBottom())))
    for t in board.GetTracks():
        if t.GetNetCode() == exclude_net:
            continue
        bb = t.GetBoundingBox()
        obs.append((TO(bb.GetLeft()), TO(bb.GetTop()), TO(bb.GetRight()), TO(bb.GetBottom())))
    return obs

def inside_board(x, y, margin):
    # point-in-polygon with margin test against outline edges (board coords)
    bx, by = x - OX, y - OY
    poly = OUTLINE
    inside = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > by) != (y2 > by):
            xi = x1 + (by - y1) * (x2 - x1) / (y2 - y1)
            if bx < xi:
                inside = not inside
    if not inside:
        return False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        dx, dy = x2 - x1, y2 - y1
        L = dx * dx + dy * dy
        t = max(0, min(1, ((bx - x1) * dx + (by - y1) * dy) / L))
        if math.hypot(bx - (x1 + t * dx), by - (y1 + t * dy)) < margin:
            return False
    return True

def free(x, y, r, obs):
    for (x0, y0, x1, y1) in obs:
        cx, cy = min(max(x, x0), x1), min(max(y, y0), y1)
        if math.hypot(x - cx, y - cy) < r:
            return False
    return True

VIA_D, VIA_DRILL = 0.6, 0.3
def add_via(x, y, net, d=VIA_D, drill=VIA_DRILL):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(d)); v.SetDrill(MM(drill))
    v.SetNet(net)
    board.Add(v)
    return v

def add_track(p0, p1, net, w, layer=pcbnew.F_Cu, locked=False):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(p0[0]), MM(p0[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(p1[0]), MM(p1[1])))
    t.SetWidth(MM(w)); t.SetLayer(layer); t.SetNet(net)
    if locked:
        t.SetLocked(True)
    board.Add(t)
    return t

# ---------------------------------------------------------- GND vias next to every top SMD GND pad
CLR = 0.22
done = []
gnd_items = []
# hand-placed: MCU VSS -> C4 -> via -> C5
for a, b_ in (((46.863, 0.325), (48.2, 0.325)), ((48.2, 0.325), (48.355, 0.17)), ((48.355, 0.17), (50.4, 0.175))):
    add_track((OX + a[0], OY + a[1]), (OX + b_[0], OY + b_[1]), gnd, 0.3)
    gnd_items.append(['trk', OX + a[0], OY + a[1], OX + b_[0], OY + b_[1], 0.3])
add_via(OX + 49.6, OY + 0.17, gnd); gnd_items.append(['via', OX + 49.6, OY + 0.17, 0.6, 0.3])
done.append((OX + 49.6, OY + 0.17))
SKIP = {('U1', '5'), ('C4', '2'), ('C5', '2')}
for fp in board.GetFootprints():
    if fp.GetLayer() != pcbnew.F_Cu:
        continue
    for pad in fp.Pads():
        if pad.GetNetCode() != gnd.GetNetCode() or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            continue
        if not pad.IsOnLayer(pcbnew.F_Cu):
            continue
        c = pad.GetPosition(); cx, cy = TO(c.x), TO(c.y)
        ref = fp.GetReference()
        if (ref, pad.GetNumber()) in SKIP:
            continue
        if ref == 'U3' and pad.GetNumber() in ('9', ''):
            continue   # exposed pad handled separately
        obs = obstacles(gnd.GetNetCode())
        # skip if an existing GND via is already very close
        if any(math.hypot(cx - vx, cy - vy) < 1.0 for vx, vy in done):
            continue
        bb = pad.GetBoundingBox()
        hw, hh = TO(bb.GetWidth()) / 2, TO(bb.GetHeight()) / 2
        best = None
        for dist in (0.0, 0.25, 0.5, 0.75, 1.0, 1.3):
            for ang in range(0, 360, 30):
                a = math.radians(ang)
                ex = hw + VIA_D / 2 + 0.05 + dist
                ey = hh + VIA_D / 2 + 0.05 + dist
                vx, vy = cx + ex * math.cos(a), cy + ey * math.sin(a)
                if not inside_board(vx, vy, 0.6):
                    continue
                if free(vx, vy, VIA_D / 2 + CLR, obs):
                    best = (vx, vy)
                    break
            if best:
                break
        if not best:
            print('no via spot for', ref, pad.GetNumber())
            continue
        add_via(best[0], best[1], gnd)
        add_track((cx, cy), best, gnd, 0.3)
        done.append(best)
        gnd_items.append(['via', best[0], best[1], 0.6, 0.3]); gnd_items.append(['trk', cx, cy, best[0], best[1], 0.3])
# DRV8837 exposed pad: two thermal vias inside the pad
u3 = board.FindFootprintByReference('U3')
c = u3.GetPosition()
for dy in (-0.45, 0.45):
    add_via(TO(c.x), TO(c.y) + dy, gnd, 0.5, 0.3)
    gnd_items.append(['via', TO(c.x), TO(c.y) + dy, 0.5, 0.3])
print('GND vias:', len(done) + 2)

json.dump(gnd_items, open(os.path.join(WORK, 'gnd_items.json'), 'w'))
pcbnew.SaveBoard(PCB, board)
subprocess.run([sys.executable, os.path.join(PROJ, 'build/scripts/patch_pro.py')])

# ---------------------------------------------------------- Specctra export, drop GND, route
dsn = os.path.join(WORK, 'board.dsn'); ses = os.path.join(WORK, 'board.ses')
board = pcbnew.LoadBoard(PCB)
ok = pcbnew.ExportSpecctraDSN(board, dsn)
print('dsn export', ok)
txt = open(dsn).read()
# remove the GND net from the network section and from class lists
for _n in ('GND', r'\+5V'):
    txt = re.sub(r'\(net "?' + _n + r'"?\s*\(pins[^)]*\)\s*\)', '', txt)
txt = re.sub(r'(\(class [^\n]*?)\s+GND(\s)', r'\1\2', txt)
txt = re.sub(r'(\(class [^\n]*?)\s+\+5V(\s)', r'\1\2', txt)
txt = txt.replace('(clearance 160)', '(clearance 205)').replace('(clearance 200)', '(clearance 215)')
AUTO = ('    (autoroute_settings (fanout off) (autoroute on) (postroute on) (vias on) (via_costs 80) (plane_via_costs 5)'
        ' (start_ripup_costs 100) (start_pass_no 1)'
        ' (layer_rule F.Cu (active on) (preferred_direction horizontal) (preferred_direction_trace_costs 1.0) (against_preferred_direction_trace_costs 1.6))'
        ' (layer_rule In1.Cu (active off)) (layer_rule In2.Cu (active off))'
        ' (layer_rule B.Cu (active on) (preferred_direction vertical) (preferred_direction_trace_costs 6.0) (against_preferred_direction_trace_costs 8.0)))\n')
i = txt.index('(structure')
j = txt.index('(placement')
k = txt.rindex(')', i, j)
txt = txt[:k] + AUTO + txt[k:]
open(dsn, 'w').write(txt)
if os.path.exists(ses):
    os.remove(ses)
r = subprocess.run(FR + ['-de', dsn, '-do', ses, '-mp', sys.argv[1] if len(sys.argv) > 1 else '30', '-mt', '3'],
                   cwd=WORK, capture_output=True, text=True, timeout=1800)
open(os.path.join(WORK, 'freerouting.log'), 'w').write(r.stdout + r.stderr)
print('freerouting rc', r.returncode, 'ses exists', os.path.exists(ses))
