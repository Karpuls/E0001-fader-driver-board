#!/usr/bin/env python3
"""Hand fixes after the cleanup pass: daisy-chain branch points through pads
(no T-joins), straighten I2C/VIN, 45-degree pad entries. Every added track and
via is checked for clearance against all other copper.

usage: fixes.py geom.json in.kicad_pcb out.kicad_pcb
"""
import json, math, re, sys, uuid
from shapely.geometry import Point, Polygon, LineString, box
from shapely.ops import unary_union

G = json.load(open(sys.argv[1]))
src = open(sys.argv[2]).read()
POWER = {"+5V", "/VIN", "/MOTOR_P", "/MOTOR_N"}
I2C = {"/I2C_SDA", "/I2C_SCL"}
TPAD = Point(163.65, 101.875).buffer(1.2, 64)

# ------------------------------------------------------------------ edits
RM = {   # net: [(layer, a, b)]  ('*' = every segment of the net on that layer)
    "+3V3": [("B.Cu", (128.414, 97.18), (129.155, 97.922)), ("B.Cu", (129.155, 97.922), (142.391, 97.922)),
             ("B.Cu", (129.155, 97.922), (129.155, 100.39)), ("B.Cu", (129.155, 100.39), (131.73, 102.965)),
             ("B.Cu", (128.414, 93.62), (128.414, 97.18)),
             ("F.Cu", (145.624, 101.154), (146.683, 101.154)), ("F.Cu", (146.683, 101.154), (146.863, 100.975))],
    "/NRST": [("B.Cu", (133, 101.965), (131.781, 100.746)),
              ("F.Cu", (128.48, 101), (128.771, 100.709)), ("F.Cu", (128.771, 100.709), (130.592, 100.709)),
              ("F.Cu", (130.592, 100.709), (130.629, 100.746)), ("F.Cu", (130.629, 100.746), (131.781, 100.746))],
    "/TOUCH_SNS": [("F.Cu", "*", None)],
    "/VSENSE": [("F.Cu", "*", None)],
    "/FADER_POS": [("F.Cu", "*", None)],
    "/POT_HI": [("F.Cu", (146.863, 97.724), (146.863, 97.725))],
    "/I2C_SCL": [("B.Cu", (167.12, 99.959), (167.12, 99.946)), ("B.Cu", (166.935, 100.144), (167.12, 99.959)),
                 ("B.Cu", (167.12, 100.329), (166.935, 100.144)), ("B.Cu", (167.12, 104.809), (167.12, 100.329)),
                 ("B.Cu", (166.935, 104.809), (167.12, 104.809)), ("B.Cu", (165.12, 106.624), (166.935, 104.809)),
                 ("B.Cu", (165.12, 106.966), (165.12, 106.624)), ("B.Cu", (164.97, 107.116), (165.12, 106.966))],
    "/I2C_SDA": [("B.Cu", "*", None), ("F.Cu", (169.056, 99.881), (168.55, 99.375)), ("F.Cu", (169.878, 99.881), (169.056, 99.881))],
    "/TOUCH_ELEC": [("F.Cu", (153.45, 100.55), (153.45, 99.465)), ("F.Cu", (153.45, 99.465), (153.01, 99.025))],
    "/VIN": [("F.Cu", "*", None), ("B.Cu", "*", None)],
}
RMVIA = [("/NRST", (131.781, 100.746)), ("/I2C_SDA", (169.878, 99.881)), ("/VIN", (158.304, 92.315))]
ADDVIA = [("/NRST", (133.0, 101.965), 0.6, 0.3), ("/I2C_SDA", (169.95, 99.375), 0.6, 0.3), ("/VIN", (164.0, 92.3), 0.8, 0.4)]
ADD = [  # (net, layer, width, points)
    ("+3V3", "B.Cu", 0.2, [(128.414, 93.62), (128.814, 93.22), (134.0, 93.22), (138.702, 97.922), (142.391, 97.922)]),
    ("+3V3", "B.Cu", 0.2, [(128.414, 93.62), (128.414, 99.649), (131.73, 102.965)]),
    ("+3V3", "F.Cu", 0.2, [(145.624, 101.154), (145.803, 100.975), (146.863, 100.975)]),
    ("/NRST", "F.Cu", 0.2, [(133.0, 101.965), (131.781, 100.746), (128.734, 100.746), (128.48, 101.0)]),
    ("/TOUCH_SNS", "F.Cu", 0.2, [(146.863, 99.025), (147.75, 99.025), (147.995, 98.78), (149.1, 98.78), (149.32, 99.0),
                                 (150.085, 99.0), (150.71, 98.375)]),
    ("/TOUCH_SNS", "F.Cu", 0.2, [(150.71, 98.375), (151.34, 98.375), (151.99, 99.025)]),
    ("/VSENSE", "F.Cu", 0.2, [(141.137, 97.075), (138.51, 97.075)]),
    ("/VSENSE", "F.Cu", 0.2, [(138.51, 97.075), (137.75, 96.315), (137.75, 95.44), (138.4, 94.79)]),
    ("/VSENSE", "F.Cu", 0.2, [(138.4, 94.79), (138.4, 93.8), (138.0, 93.4), (136.0, 93.4), (135.6, 93.8),
                              (135.6, 95.38), (136.0, 95.78), (136.6, 95.78)]),
    ("/FADER_POS", "F.Cu", 0.2, [(146.863, 97.075), (148.295, 97.075), (149.12, 96.25)]),
    ("/FADER_POS", "F.Cu", 0.2, [(149.12, 96.25), (149.12, 95.95), (149.47, 95.6), (151.19, 95.6), (151.49, 95.9), (151.49, 96.7)]),
    ("/I2C_SCL", "B.Cu", 0.2, [(167.12, 99.946), (167.12, 104.966), (164.97, 107.116)]),
    ("/I2C_SDA", "F.Cu", 0.2, [(168.55, 99.375), (169.95, 99.375)]),
    ("/I2C_SDA", "B.Cu", 0.2, [(169.95, 99.375), (169.95, 103.011), (164.898, 108.063), (156.443, 108.063),
                               (151.486, 103.106), (151.486, 102.925)]),
    ("/TOUCH_ELEC", "F.Cu", 0.25, [(153.45, 100.55), (153.01, 100.11), (153.01, 99.025)]),
    ("/VIN", "F.Cu", 0.5, [(150.8, 92.662), (151.162, 92.3), (164.0, 92.3)]),
    ("/VIN", "B.Cu", 0.5, [(164.0, 92.3), (170.749, 99.049), (170.749, 102.245)]),
    ("/VIN", "F.Cu", 0.5, [(168.55, 101.875), (168.92, 102.245), (170.749, 102.245)]),
]
if "--only" in sys.argv:
    sys.argv.remove("--only")
    RM, RMVIA, ADDVIA, ADD = {}, [], [], []
if len(sys.argv) > 4:      # optional extra edit file (python literal: RM, RMVIA, ADDVIA, ADD)
    ex = {}
    exec(open(sys.argv[4]).read(), ex)
    for k, v in ex.get("RM", {}).items(): RM.setdefault(k, []).extend(v)
    RMVIA += ex.get("RMVIA", []); ADDVIA += ex.get("ADDVIA", []); ADD += ex.get("ADD", [])

# ------------------------------------------------------------------ apply
SEG = re.compile(r'\n\t\(segment\s.*?\n\t\)', re.S)
VIA = re.compile(r'\n\t\(via\s.*?\n\t\)', re.S)
f = lambda b, k: re.search(r'\(' + k + r' ([^)]*)\)', b).group(1)
near = lambda p, q, t=0.004: math.dist(p, q) < t


def seg_rm(b):
    n = f(b, "net").strip('"'); L = f(b, "layer").strip('"')
    a = tuple(map(float, f(b, "start").split())); e = tuple(map(float, f(b, "end").split()))
    for rl, ra, rb in RM.get(n, []):
        if rl != L:
            continue
        if ra == "*" or (near(a, ra) and near(e, rb)) or (near(a, rb) and near(e, ra)):
            used.add((n, rl, ra, rb))
            return True
    return False


used = set()
out = SEG.sub(lambda m: "" if seg_rm(m.group(0)) else m.group(0), src)
for n, l in RM.items():
    for r in l:
        if (n,) + r not in used:
            print("NOT FOUND", n, r)


def via_rm(b):
    n = f(b, "net").strip('"'); at = tuple(map(float, f(b, "at").split()[:2]))
    for rn, rp in RMVIA:
        if rn == n and near(at, rp, 0.01):
            return True
    return False


out = VIA.sub(lambda m: "" if via_rm(m.group(0)) else m.group(0), out)
items = []
for n, L, w, pts in ADD:
    for a, b in zip(pts, pts[1:]):
        items.append('\t(segment\n\t\t(start %.4f %.4f)\n\t\t(end %.4f %.4f)\n\t\t(width %.3f)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)'
                     % (a[0], a[1], b[0], b[1], w, L, n, uuid.uuid4()))
for n, p, d, dr in ADDVIA:
    items.append('\t(via\n\t\t(at %.4f %.4f)\n\t\t(size %.2f)\n\t\t(drill %.2f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)'
                 % (p[0], p[1], d, dr, n, uuid.uuid4()))
out = out.rstrip()[:-1].rstrip() + "\n" + "\n".join(items) + "\n)\n"
open(sys.argv[3], "w").write(out)

# ------------------------------------------------------------------ check what was added
copper = []   # (net, layer|'*', geom)
for p in G["pads"]:
    for L, pl in p["poly"].items():
        if L in ("F.Cu", "B.Cu"):
            copper.append((p["net"] or "npth", L, unary_union([Polygon(r) for r in pl if len(r) >= 3]), "pad %s.%s" % (p["ref"], p["num"])))
    if p["attr"] == "npth":
        copper.append(("npth", "*", Point(p["x"], p["y"]).buffer(p["drill"] / 2, 32), "npth"))
for m in SEG.finditer(out):
    b = m.group(0)
    a = tuple(map(float, f(b, "start").split())); e = tuple(map(float, f(b, "end").split()))
    copper.append((f(b, "net").strip('"'), f(b, "layer").strip('"'), LineString([a, e]).buffer(float(f(b, "width")) / 2, 12), "track"))
for m in VIA.finditer(out):
    b = m.group(0)
    at = tuple(map(float, f(b, "at").split()[:2]))
    copper.append((f(b, "net").strip('"'), "*", Point(at).buffer(float(f(b, "size")) / 2, 24), "via@%.2f,%.2f" % at))
EDGE = box(66.475, 91.475, 173.525, 108.525).buffer(-0.3, join_style=2)


def check(n, L, g, what):
    c0 = 0.2 if n in POWER else 0.16
    for cn, cl, cg, cw in copper:
        if cn == n or (cl != "*" and L != "*" and cl != L):
            continue
        c = max(c0, 0.2 if cn in POWER else 0.16)
        d = cg.distance(g)
        if d < c + 0.002:
            print("  CLEARANCE %s %s %s: %.3f to %s %s" % (what, n, L, d, cn, cw))
    if not EDGE.contains(g):
        print("  EDGE", what, n)
    if n in I2C and g.distance(TPAD) < 1.85:
        print("  I2C-TOUCH %.3f" % g.distance(TPAD), what)


for n, L, w, pts in ADD:
    for a, b in zip(pts, pts[1:]):
        check(n, L, LineString([a, b]).buffer(w / 2, 12), "seg %s->%s" % (a, b))
for n, p, d, dr in ADDVIA:
    check(n, "*", Point(p).buffer(d / 2, 24), "via %s" % (p,))
print("fixes applied")
