#!/usr/bin/env python3
"""Own post-route cleanup: rebuild every free track chain as a clean 45-degree path.

A chain runs between terminals (pads, vias, branch points). Each chain is
replaced by the shortest octilinear path (straight, or two/three segments
with 135-degree bends) that keeps the net-class clearance to every other
net's copper, the board edge, and the I2C-to-touch-pad gap. Joins at a
terminal are kept >= 90.5 degrees apart. Remaining right-angle bends are
chamfered. Chains that cannot be improved are left as they are.

usage: cleanup.py geom.json in.kicad_pcb out.kicad_pcb
"""
import json, math, re, sys, uuid, itertools
from collections import defaultdict
from shapely.geometry import Point, Polygon, LineString, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

G = json.load(open(sys.argv[1]))
src = open(sys.argv[2]).read()
EDGE_IN = box(66.475, 91.475, 173.525, 108.525).buffer(-0.31, join_style=2)
POWER = {"+5V", "/VIN", "/MOTOR_P", "/MOTOR_N"}
I2C = {"/I2C_SDA", "/I2C_SCL"}
TPAD = Point(163.65, 101.875).buffer(1.2, 64)
I2C_GAP = 1.9
TOUCH = {"/TOUCH_ELEC", "/TOUCH_SNS", "/TOUCH_DRV"}


def clr(a, b):
    c = 0.21 if (a in POWER or b in POWER) else 0.17
    if (a in TOUCH and b in I2C) or (a in I2C and b in TOUCH):
        c = 0.6
    return c

# ---------------------------------------------------------------- items
pads = []
for p in G["pads"]:
    for L, pl in p["poly"].items():
        if L in ("F.Cu", "B.Cu"):
            g = unary_union([Polygon(r) for r in pl if len(r) >= 3])
            pads.append((p["net"], L, g, p))
    if p["attr"] == "npth":
        for L in ("F.Cu", "B.Cu"):
            pads.append(("", L, Point(p["x"], p["y"]).buffer(p["drill"] / 2, 32), p))

SEG = re.compile(r'\n\t\(segment\s.*?\n\t\)', re.S)
VIA = re.compile(r'\n\t\(via\s.*?\n\t\)', re.S)
f = lambda b, k: re.search(r'\(' + k + r' ([^)]*)\)', b).group(1)
segs = []
for m in SEG.finditer(src):
    b = m.group(0)
    a = tuple(map(float, f(b, "start").split())); e = tuple(map(float, f(b, "end").split()))
    segs.append(dict(a=a, b=e, w=float(f(b, "width")), L=f(b, "layer").strip('"'), n=f(b, "net").strip('"')))
vias = []
for m in VIA.finditer(src):
    b = m.group(0)
    vias.append(dict(at=tuple(map(float, f(b, "at").split()[:2])), d=float(f(b, "size")), n=f(b, "net").strip('"')))
base = VIA.sub("", SEG.sub("", src))

K = lambda p: (round(p[0], 3), round(p[1], 3))


def split_tjoins(segs):
    """split a segment where another same-net/layer segment ends on its interior"""
    for s in segs:
        s["a"], s["b"] = K(s["a"]), K(s["b"])
    segs = [s for s in segs if s["a"] != s["b"]]
    changed = True
    while changed:
        changed = False
        ends = defaultdict(set)
        for s in segs:
            ends[(s["n"], s["L"])].update([K(s["a"]), K(s["b"])])
        for s in list(segs):
            ls = LineString([s["a"], s["b"]])
            for p in ends[(s["n"], s["L"])]:
                if p in (K(s["a"]), K(s["b"])):
                    continue
                if ls.distance(Point(p)) < 0.003 and min(math.dist(p, s["a"]), math.dist(p, s["b"])) > 0.002:
                    segs.remove(s)
                    segs.append(dict(s, b=p)); segs.append(dict(s, a=p))
                    changed = True
                    break
            if changed:
                break
    return [s for s in segs if K(s["a"]) != K(s["b"])]


segs = split_tjoins(segs)


def is_term(n, L, p):
    for v in vias:
        if v["n"] == n and math.dist(v["at"], p) < 0.02:
            return "via"
    for pn, pl, g, pp in pads:
        if pn == n and pl == L and g.distance(Point(p)) < 0.005 and math.dist((pp["x"], pp["y"]), p) < 0.02:
            return "pad"
    return None


def chains():
    by = defaultdict(list)
    for i, s in enumerate(segs):
        by[(s["n"], s["L"])].append(i)
    out = []
    for (n, L), idx in by.items():
        adj = defaultdict(list)
        for i in idx:
            adj[K(segs[i]["a"])].append(i); adj[K(segs[i]["b"])].append(i)
        term = {p for p in adj if len(adj[p]) != 2 or is_term(n, L, p)}
        seen = set()
        for t in term:
            for i in adj[t]:
                if i in seen:
                    continue
                path, ids, cur, j = [t], [], t, i
                while True:
                    seen.add(j); ids.append(j)
                    s = segs[j]
                    nxt = K(s["b"]) if K(s["a"]) == cur else K(s["a"])
                    path.append(nxt); cur = nxt
                    if cur in term:
                        break
                    j = [k for k in adj[cur] if k != j][0]
                    if j in seen:
                        break
                out.append((n, L, path, ids))
    return out


def obstacles(n, L, skip):
    obs = []
    for pn, pl, g, pp in pads:
        if pl == L and pn != n:
            obs.append((g, clr(n, pn)))
    for i, s in enumerate(segs):
        if s["L"] == L and s["n"] != n and i not in skip:
            obs.append((LineString([s["a"], s["b"]]).buffer(s["w"] / 2, 8), clr(n, s["n"])))
    for v in vias:
        if v["n"] != n:
            obs.append((Point(v["at"]).buffer(v["d"] / 2, 16), clr(n, v["n"])))
    return obs


def ok_path(n, L, pts, w, obs):
    g = LineString(pts).buffer(w / 2, 8)
    if not EDGE_IN.contains(g):
        return False
    if n in I2C and g.distance(TPAD) < I2C_GAP:
        return False
    for o, c in obs:
        if o.distance(g) < c:
            return False
    return True


def rays_at(n, L, p, skip):
    r = []
    for i, s in enumerate(segs):
        if i in skip or s["n"] != n or s["L"] != L:
            continue
        if K(s["a"]) == p:
            r.append(math.atan2(s["b"][1] - p[1], s["b"][0] - p[0]))
        elif K(s["b"]) == p:
            r.append(math.atan2(s["a"][1] - p[1], s["a"][0] - p[0]))
    return r


def angdiff(a, b):
    d = abs(math.degrees(a - b)) % 360
    return min(d, 360 - d)


def candidates(A, B):
    dx, dy = B[0] - A[0], B[1] - A[1]
    adx, ady = abs(dx), abs(dy)
    sx, sy = math.copysign(1, dx), math.copysign(1, dy)
    if adx < 1e-4 or ady < 1e-4 or abs(adx - ady) < 1e-4:
        yield [A, B]
    d = min(adx, ady)
    if adx > ady:
        straight = (adx - d) * sx, 0
    else:
        straight = 0, (ady - d) * sy
    diag = d * sx, d * sy
    # diagonal first / straight first
    yield [A, (A[0] + diag[0], A[1] + diag[1]), B]
    yield [A, (A[0] + straight[0], A[1] + straight[1]), B]
    # straight split around a diagonal
    for fr in (0.5, 0.25, 0.75, 0.1, 0.9):
        p1 = (A[0] + straight[0] * fr, A[1] + straight[1] * fr)
        p2 = (p1[0] + diag[0], p1[1] + diag[1])
        yield [A, p1, p2, B]
    # diagonal split around a straight
    for fr in (0.5, 0.25, 0.75):
        p1 = (A[0] + diag[0] * fr, A[1] + diag[1] * fr)
        p2 = (p1[0] + straight[0], p1[1] + straight[1])
        yield [A, p1, p2, B]


def clean(pts):
    out = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, out[-1]) > 1e-4:
            out.append(p)
    i = 1
    while i < len(out) - 1:
        a, b, c = out[i - 1], out[i], out[i + 1]
        if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) < 1e-6:
            out.pop(i)
        else:
            i += 1
    return out


def min_join(n, L, pts, skip):
    """smallest angle the new path makes with other copper at its two ends"""
    m = 180
    for end, nxt in ((pts[0], pts[1]), (pts[-1], pts[-2])):
        r0 = math.atan2(nxt[1] - end[1], nxt[0] - end[0])
        for r in rays_at(n, L, K(end), skip):
            m = min(m, angdiff(r0, r))
    return m


def bends_ok(pts):
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        r1 = math.atan2(a[1] - b[1], a[0] - b[0]); r2 = math.atan2(c[1] - b[1], c[0] - b[0])
        if angdiff(r1, r2) < 134:
            return False
    return True


def length(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def bad_bends(pts):
    return sum(1 for a, b, c in zip(pts, pts[1:], pts[2:])
               if angdiff(math.atan2(a[1] - b[1], a[0] - b[0]), math.atan2(c[1] - b[1], c[0] - b[0])) < 134)


import time; T0 = time.time()
changed = 0
for it in range(3):
    print("iter", it, len(segs), "segs %.1fs" % (time.time() - T0), flush=True)
    for n, L, path, ids in chains():
        if not all(i < len(segs) for i in ids):
            continue
        ws = [segs[i]["w"] for i in ids]
        if n in POWER and min(ws) < max(ws):
            continue          # keep pad neck-downs on power as drawn
        w = max(ws)
        if n in POWER:
            w = max(w, 0.5) if min(ws) >= 0.5 else w
        skip = set(ids)
        obs = obstacles(n, L, skip)
        A, B = path[0], path[-1]
        old = clean(path)
        old_score = (bad_bends(old) + (0 if min_join(n, L, old, skip) >= 90.5 else 1), len(old), length(old))
        best = None
        for cand in candidates(A, B):
            cand = clean(cand)
            if not bends_ok(cand):
                continue
            mj = min_join(n, L, cand, skip)
            if mj < 90.5:
                continue
            for ww in sorted({w, min(ws)}, reverse=True):
                if ok_path(n, L, cand, ww, obs):
                    sc = (0, len(cand), length(cand))
                    if best is None or sc < best[0]:
                        best = (sc, cand, ww)
                    break
        if best and best[0] < old_score and not (best[1] == old and best[2] == w):
            for i in sorted(ids, reverse=True):
                segs[i] = None
            for a, b in zip(best[1], best[1][1:]):
                segs.append(dict(a=a, b=b, w=best[2], L=L, n=n))
            segs[:] = [s for s in segs if s]
            changed += 1
    segs = split_tjoins(segs)
print("chains rebuilt:", changed)

# chamfer leftover right-angle bends at free nodes
nchamf = 0
for n, L, path, ids in chains():
    pts = path
    for k in range(1, len(pts) - 1):
        a, b, c = pts[k - 1], pts[k], pts[k + 1]
        ang = angdiff(math.atan2(a[1] - b[1], a[0] - b[0]), math.atan2(c[1] - b[1], c[0] - b[0]))
        if 89 < ang < 91:
            i1 = [i for i in ids if K(segs[i]["a"]) in (K(a), K(b)) and K(segs[i]["b"]) in (K(a), K(b))]
            i2 = [i for i in ids if K(segs[i]["a"]) in (K(b), K(c)) and K(segs[i]["b"]) in (K(b), K(c))]
            if not i1 or not i2:
                continue
            w = segs[i1[0]]["w"]
            obs = obstacles(n, L, set(ids))
            for cut in (0.5, 0.35, 0.25, 0.15, 0.08):
                cut = min(cut, math.dist(a, b) * 0.45, math.dist(b, c) * 0.45)
                pa = (b[0] + (a[0] - b[0]) * cut / math.dist(a, b), b[1] + (a[1] - b[1]) * cut / math.dist(a, b))
                pc = (b[0] + (c[0] - b[0]) * cut / math.dist(b, c), b[1] + (c[1] - b[1]) * cut / math.dist(b, c))
                if ok_path(n, L, [pa, pc], w, obs):
                    s1, s2 = segs[i1[0]], segs[i2[0]]
                    for s in (s1, s2):
                        if K(s["a"]) == K(b): s["a"] = pa if s is s1 else pc
                        if K(s["b"]) == K(b): s["b"] = pa if s is s1 else pc
                    segs.append(dict(a=pa, b=pc, w=w, L=L, n=n))
                    nchamf += 1
                    break
            break   # path changed; next chain
print("chamfers:", nchamf)

items = []
for s in segs:
    items.append('\t(segment\n\t\t(start %.4f %.4f)\n\t\t(end %.4f %.4f)\n\t\t(width %.3f)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)'
                 % (s["a"][0], s["a"][1], s["b"][0], s["b"][1], s["w"], s["L"], s["n"], uuid.uuid4()))
vb = [m.group(0).lstrip("\n") for m in VIA.finditer(src)]
out = base.rstrip()
assert out.endswith(")")
out = out[:-1].rstrip() + "\n" + "\n".join(items + vb) + "\n)\n"
open(sys.argv[3], "w").write(out)
print("segments", len(segs), "vias", len(vb))
