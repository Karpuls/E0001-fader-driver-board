#!/usr/bin/env python3
"""Hand pre-route for the E0001 rev B board (own script, no autorouter).

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

# ------------------------------------------------------------------ 1. motor loop + U3 supply
N = "/MOTOR_N"; P = "/MOTOR_P"
add_path(N, "F.Cu", [(78.05, 99.75), (77.6, 99.75), (77.37, 99.52), (77.1, 99.52)], [0.25] * 3)
add_path(N, "F.Cu", [(77.1, 99.52), (74.0, 99.52)], [0.5])
add_path(P, "F.Cu", [(78.05, 100.25), (77.6, 100.25), (77.37, 100.48), (77.1, 100.48)], [0.25] * 3)
add_path(P, "F.Cu", [(77.1, 100.48), (74.0, 100.48)], [0.5])
add_path(N, "F.Cu", [(74.0, 99.52), (73.5, 99.52), (70.45, 96.47), (70.45, 96.0)], [0.5] * 3)
add_path(P, "F.Cu", [(74.0, 100.48), (73.5, 100.48), (70.45, 103.53), (70.45, 104.0)], [0.5] * 3)
V5 = "+5V"
add_path(V5, "F.Cu", [(78.05, 99.25), (78.05, 98.95)], [0.25])
add_path(V5, "F.Cu", [(78.05, 98.95), (77.72, 98.62), (77.72, 97.7)], [0.5, 0.5])
add_path(V5, "F.Cu", [(79.95, 99.25), (79.95, 98.95)], [0.25])
add_path(V5, "F.Cu", [(79.95, 98.95), (80.52, 98.38), (80.52, 97.7)], [0.5, 0.5])
# U3 GND pin 4 into the exposed pad, two thermal vias in the EP
add_path("GND", "F.Cu", [(78.05, 100.75), (78.75, 100.75)], [0.25])
ep = pad("U3", "9"); ep["ep"] = True
add_via("GND", 79.0, 99.62, own=ep)
add_via("GND", 79.0, 100.38, own=ep)

# ------------------------------------------------------------------ 2. TOUCH_ELEC (fader touch pad T -> D2.1 -> R5.1)
TE = "/TOUCH_ELEC"
add_path(TE, "F.Cu", [(163.65, 101.875), (155.4, 101.875), (154.075, 100.55), (153.45, 100.55)], [0.25] * 3)
add_path(TE, "F.Cu", [(153.45, 100.55), (153.45, 99.465), (153.01, 99.025)], [0.25] * 2)

# ------------------------------------------------------------------ 3. plane fan-out
done = {("U3", "4"), ("U3", "9")}
fp_c = {f["ref"]: (f["x"], f["y"]) for f in G["fps"]}
court = {f["ref"]: unary_union([Polygon(r) for r in f["court"] if len(r) >= 3]) for f in G["fps"]}
hull = {f["ref"]: unary_union([s for q in pads if q["ref"] == f["ref"] for s in q["shape"].values()]).convex_hull.buffer(-0.05)
        for f in G["fps"]}
DIRS = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in range(0, 360, 45)]
# fixed via spots for the hand-routed U3 supply
add_path(V5, "F.Cu", [(77.72, 97.7), (77.72, 96.62)], [0.5]); add_via(V5, 77.72, 96.62, 0.8, 0.4)
add_path(V5, "F.Cu", [(80.52, 97.7), (80.52, 96.62)], [0.5]); add_via(V5, 80.52, 96.62, 0.8, 0.4)
done |= {("C10", "1"), ("C13", "1"), ("U3", "1"), ("U3", "8")}


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
            if out < -0.05 and p["ref"] in ("U1", "J1", "U2", "Q1"):
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


todo = [p for p in pads if p["attr"] in ("smd", "conn") and p["net"] in ("GND", "+5V") and p["layers"]
        and (p["ref"], p["num"]) not in done]
for p in todo:
    pw = 0.5 if p["net"] == "+5V" else 0.3
    w = min(pw, p["minor"])
    d, drill = (0.8, 0.4) if p["net"] == "+5V" else (0.6, 0.3)
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
