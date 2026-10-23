#!/usr/bin/env python3
"""Hand pre-route for the E0001 rev C board (own script, no autorouter).

1. Motor loop at U3 (driver -> C14 -> motor pads), U3 supply pins to C10/C13.
2. TOUCH_ELEC from the fader touch pad to D2/R5.
3. A plane via for every SMD GND pad (In1.Cu) and every +5V pad (In2.Cu),
   each placed by a search that keeps >= 0.2 mm copper gap to every pad.

usage: preroute.py geom.json board.kicad_pcb  (writes the board in place)
"""
import json, math, sys, uuid
from shapely.geometry import Point, Polygon, LineString, box
from shapely.ops import unary_union

G = json.load(open(sys.argv[1]))
BOARD = sys.argv[2]
EDGE = box(66.475, 91.475, 173.525, 108.525)
CU = ("F.Cu", "B.Cu")

# ------------------------------------------------------------------ obstacles
pads = []
for p in G["pads"]:
    shapes = {}
    for L, pl in p["poly"].items():
        shapes[L] = unary_union([Polygon(r) for r in pl if len(r) >= 3])
    if p["attr"] == "npth":
        shapes = {L: Point(p["x"], p["y"]).buffer(p["drill"] / 2, 32) for L in ("F.Cu", "B.Cu", "In1.Cu", "In2.Cu")}
    p["shape"] = shapes
    pads.append(p)
keep_via = [Polygon(k["poly"][0]) for k in G["keepouts"] if k["vias"]]

tracks = []   # (net, layer, geom, width, a, b)
vias = []     # (net, x, y, d, drill)


def track_geom(a, b, w):
    return LineString([a, b]).buffer(w / 2, 16) if a != b else Point(a).buffer(w / 2, 16)


def clear_track(net, L, g, clr=0.2):
    for p in pads:
        s = p["shape"].get(L)
        if s is None or p["net"] == net:
            continue
        if s.distance(g) < clr:
            return "pad %s.%s" % (p["ref"], p["num"])
    for n, l, tg, *_ in tracks:
        if l == L and n != net and tg.distance(g) < clr:
            return "track " + n
    for n, x, y, d, _ in vias:
        if n != net and Point(x, y).buffer(d / 2, 16).distance(g) < clr:
            return "via " + n
    if not EDGE.buffer(-0.3).contains(g):
        return "edge"
    return None


def via_problem(net, x, y, d, drill, own=None, padgap=0.2):
    c = Point(x, y).buffer(d / 2, 24)
    for p in pads:
        if p is own and p.get("ep"):
            continue
        for L, s in p["shape"].items():
            if s.is_empty:
                continue
            if p["attr"] == "npth":
                if Point(p["x"], p["y"]).distance(Point(x, y)) < p["drill"] / 2 + drill / 2 + 0.35:
                    return "npth"
                continue
            gap = padgap
            if p["net"] == net and p["minor"] >= 2.0:
                continue
            if s.distance(c) < gap:
                return "pad %s.%s gap %.3f" % (p["ref"], p["num"], s.distance(c))
    for n, l, tg, *_ in tracks:
        if n != net and tg.distance(c) < 0.2:
            return "track " + n
    for n, vx, vy, vd, vdr in vias:
        dd = math.hypot(vx - x, vy - y)
        if dd < (vd + d) / 2 + 0.2 or dd < (vdr + drill) / 2 + 0.3:
            return "via " + n
    for k in keep_via:
        if k.buffer(0.05).intersects(c):
            return "keepout"
    if not EDGE.buffer(-0.35).contains(c):
        return "edge"
    return None


def add_path(net, L, pts, widths):
    """pts: list of points, widths: one per segment"""
    for (a, b), w in zip(zip(pts, pts[1:]), widths):
        g = track_geom(a, b, w)
        why = clear_track(net, L, g)
        if why:
            print("  WARN %s %s->%s w%.2f: %s" % (net, a, b, w, why))
        tracks.append((net, L, g, w, a, b))


def add_via(net, x, y, d=0.6, drill=0.3, own=None, quiet=False):
    why = via_problem(net, x, y, d, drill, own)
    if why and not quiet:
        print("  WARN via %s @%.2f,%.2f: %s" % (net, x, y, why))
    vias.append((net, x, y, d, drill))


def pad(ref, num):
    return [p for p in pads if p["ref"] == ref and p["num"] == num][0]

# ------------------------------------------------------------------ 1. motor loop + U3 supply (rev C)
N = "/MOTOR_N"; P = "/MOTOR_P"; VM = "VM_P"; PB = "/PBUS_IN"
add_path(N, "F.Cu", [(78.05, 99.75), (77.6, 99.75), (77.37, 99.52), (77.1, 99.52)], [0.25] * 3)
add_path(N, "F.Cu", [(77.1, 99.52), (74.0, 99.52)], [0.5])
add_path(P, "F.Cu", [(78.05, 100.25), (77.6, 100.25), (77.37, 100.48), (77.1, 100.48)], [0.25] * 3)
add_path(P, "F.Cu", [(77.1, 100.48), (74.0, 100.48)], [0.5])
add_path(N, "F.Cu", [(74.0, 99.52), (73.5, 99.52), (70.45, 96.47), (70.45, 96.0)], [0.5] * 3)
add_path(P, "F.Cu", [(74.0, 100.48), (73.5, 100.48), (70.45, 103.53), (70.45, 104.0)], [0.5] * 3)
# VM pin 1 -> C13.1 -> plane via; logic supply pin 8 -> C10.1
add_path(VM, "F.Cu", [(78.05, 99.25), (78.05, 98.95)], [0.25])
add_path(VM, "F.Cu", [(78.05, 98.95), (77.4, 98.3), (77.08, 98.3)], [0.5, 0.5])
add_path(VM, "F.Cu", [(77.08, 98.3), (77.08, 97.3)], [0.5]); add_via(VM, 77.08, 97.3, 0.8, 0.4)
add_path("+3V3", "F.Cu", [(79.95, 99.25), (79.95, 99.0), (80.27, 98.68), (81.4, 98.68)], [0.25] * 3)
# U3 GND pin 4 into the exposed pad, two thermal vias in the EP
add_path("GND", "F.Cu", [(78.05, 100.75), (78.75, 100.75)], [0.25])
ep = pad("U3", "9"); ep["ep"] = True
add_via("GND", 79.0, 99.62, own=ep)
add_via("GND", 79.0, 100.38, own=ep)

# ------------------------------------------------------------------ 2. eFuse U4 power: PBUS_IN in, VM_P out
# VM_P: bar 6 west end -> C1.1 (neck 0.25 between U4 pins 1/10)
add_path(VM, "F.Cu", [(147.3, 94.55), (146.7, 94.55)], [0.25])
add_path(VM, "F.Cu", [(146.7, 94.55), (144.05, 94.55)], [0.5])
# PBUS_IN: bar 5 east end <- C17.1 <- C18.1 <- feed via; C18.1 -> R11.1 -> R13.1
add_path(PB, "F.Cu", [(149.4, 95.05), (150.0, 95.05)], [0.25])
add_path(PB, "F.Cu", [(150.0, 95.05), (151.1, 95.05), (151.45, 94.7)], [0.5, 0.5])
add_path(PB, "F.Cu", [(151.45, 94.55), (152.6, 94.55)], [0.5])
add_path(PB, "F.Cu", [(153.0, 95.05), (154.5, 95.05)], [0.5])
add_path(PB, "F.Cu", [(152.6, 95.0), (152.3, 95.3), (152.3, 95.8)], [0.5, 0.5])
add_path(PB, "F.Cu", [(152.3, 96.05), (151.0, 96.05)], [0.5])
add_via(PB, 154.5, 95.05, 0.8, 0.4)
# feed from J1.1: F.Cu stub east, B.Cu up the east edge and along the north edge
add_path(PB, "F.Cu", [(168.55, 101.875), (168.92, 102.245), (170.749, 102.245)], [0.5, 0.5])
add_via(PB, 170.749, 102.245, 0.8, 0.4)
add_path(PB, "B.Cu", [(170.749, 102.245), (170.749, 93.0), (170.049, 92.3), (155.0, 92.3), (154.5, 92.8), (154.5, 95.05)], [0.5] * 5)

# ------------------------------------------------------------------ 3. touch nets
TE = "/TOUCH_ELEC"; TS = "/TOUCH_SNS"; TD = "/TOUCH_DRV"
add_path(TE, "F.Cu", [(163.65, 101.875), (149.775, 101.875), (149.2, 101.3), (148.6, 101.3)], [0.25] * 3)
add_path(TE, "F.Cu", [(148.6, 101.3), (148.01, 101.3), (147.11, 100.4)], [0.25] * 2)
# TOUCH_SNS: U1.7 through the C19/C6 gap, under R6.1 to R6.2, second entry R6.2 -> R5.2
add_path(TS, "F.Cu", [(140.363, 99.025), (143.4, 99.025), (143.8, 99.425), (145.4, 99.425), (145.76, 99.065), (145.76, 98.7)], [0.2] * 5)
add_path(TS, "F.Cu", [(145.9, 98.55), (146.25, 98.9), (146.25, 100.25)], [0.2] * 2)
# TOUCH_DRV: U1.8 -> via under U1 -> B.Cu -> via -> R6.1
add_path(TD, "F.Cu", [(140.363, 98.375), (139.425, 98.375), (139.1, 98.7)], [0.2] * 2)
add_via(TD, 139.1, 98.7)
add_path(TD, "B.Cu", [(139.1, 98.7), (143.95, 98.7)], [0.2])
add_via(TD, 143.95, 98.7)
add_path(TD, "F.Cu", [(143.95, 98.7), (144.74, 98.7)], [0.2])

# ------------------------------------------------------------------ 3. plane fan-out
done = {("U3", "4"), ("U3", "9")}
fp_c = {f["ref"]: (f["x"], f["y"]) for f in G["fps"]}
court = {f["ref"]: unary_union([Polygon(r) for r in f["court"] if len(r) >= 3]) for f in G["fps"]}
hull = {f["ref"]: unary_union([s for q in pads if q["ref"] == f["ref"] for s in q["shape"].values()]).convex_hull.buffer(-0.05)
        for f in G["fps"]}
DIRS = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in range(0, 360, 45)]
# eFuse corner GND: U4.8 -> R15.2 -> C16.2 (C16.2 gets its own via), C17.2 -> that via
add_path("GND", "F.Cu", [(148.625, 93.9), (148.625, 93.55), (149.15, 93.025)], [0.2, 0.2])
add_path("GND", "F.Cu", [(149.3, 92.6), (150.3, 92.6)], [0.3])
add_path("GND", "F.Cu", [(150.42, 92.52), (151.27, 92.52)], [0.3]); add_via("GND", 151.27, 92.52)
add_path("GND", "F.Cu", [(151.45, 93.52), (151.27, 92.52)], [0.3])
done |= {("U4", "8"), ("R15", "2"), ("C16", "2"), ("C17", "2")}
done |= {("C13", "1"), ("U3", "1"), ("U3", "8"), ("U4", "5"), ("U4", "6")}


def fanout(p, d, drill, w):
    cx, cy = p["x"], p["y"]
    L = p["layers"][0]
    own = p["shape"][L]
    oc = fp_c[p["ref"]]
    best = None
    for dx, dy in DIRS:
        out = (dx * (cx - oc[0]) + dy * (cy - oc[1]))
        for k in range(0, 60):
            t = 0.2 + 0.05 * k
            x, y = round(cx + dx * t, 3), round(cy + dy * t, 3)
            c = Point(x, y).buffer(d / 2, 24)
            if own.distance(c) < 0.2:
                continue
            if via_problem(p["net"], x, y, d, drill):
                continue
            g = track_geom((cx, cy), (x, y), w)
            if clear_track(p["net"], L, g, 0.2):
                break
            score = t
            if out < -0.05 and p["ref"] in ("U1", "J1", "U2", "U4"):
                score += 3       # do not drop vias under the package
            if hull[p["ref"]].intersects(c):
                score += 2       # not between the part's own pads
            for r, cg in court.items():
                if r != p["ref"] and cg.intersects(c):
                    score += 1.5
            # stay off other nets' pads so routing channels stay open
            near = min((s.distance(c) for q in pads if q["net"] != p["net"] for s in q["shape"].values() if not s.is_empty), default=9)
            if near < 0.45:
                score += (0.45 - near) * 4
            if best is None or score < best[0]:
                best = (score, x, y)
            break
    return best


todo = [p for p in pads if p["attr"] in ("smd", "conn") and p["net"] in ("GND", "VM_P") and p["layers"]
        and (p["ref"], p["num"]) not in done]
for p in todo:
    pw = 0.5 if p["net"] == "VM_P" else 0.3
    w = min(pw, p["minor"])
    d, drill = (0.8, 0.4) if p["net"] == "VM_P" else (0.6, 0.3)
    b = fanout(p, d, drill, w)
    if not b:
        d, drill = 0.6, 0.3
        b = fanout(p, d, drill, w)
    if not b:
        print("NO FANOUT", p["ref"], p["num"], p["net"])
        continue
    _, x, y = b
    add_path(p["net"], p["layers"][0], [(p["x"], p["y"]), (x, y)], [w])
    add_via(p["net"], x, y, d, drill)
    print("fanout %s.%s %s -> via %.2f,%.2f d%.1f" % (p["ref"], p["num"], p["net"], x, y, d))

# ------------------------------------------------------------------ write
s = open(BOARD).read().rstrip()
assert s.endswith(")")
items = []
for n, L, g, w, a, b in tracks:
    if a == b:
        continue
    items.append('\t(segment\n\t\t(start %.4f %.4f)\n\t\t(end %.4f %.4f)\n\t\t(width %.3f)\n\t\t(locked yes)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)'
                 % (a[0], a[1], b[0], b[1], w, L, n, uuid.uuid4()))
for n, x, y, d, dr in vias:
    items.append('\t(via\n\t\t(at %.4f %.4f)\n\t\t(size %.2f)\n\t\t(drill %.2f)\n\t\t(locked yes)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)'
                 % (x, y, d, dr, n, uuid.uuid4()))
s = s[:-1].rstrip() + "\n" + "\n".join(items) + "\n)\n"
open(BOARD, "w").write(s)
print("wrote", len(items), "items")
