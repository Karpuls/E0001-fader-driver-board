"""stats.py board -> track/via counts, length, power widths, I2C/touch distances"""
import re, sys, math, collections, json
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
s = open(sys.argv[1]).read()
f = lambda b, k: re.search(r'\(' + k + r' ([^)]*)\)', b).group(1)
segs = []
for m in re.finditer(r'\n\t\(segment\s.*?\n\t\)', s, re.S):
    b = m.group(0)
    segs.append(dict(a=tuple(map(float, f(b, "start").split())), b=tuple(map(float, f(b, "end").split())),
                     w=float(f(b, "width")), L=f(b, "layer").strip('"'), n=f(b, "net").strip('"')))
arcs = len(re.findall(r'\n\t\(arc\s', s))
vias = []
for m in re.finditer(r'\n\t\(via\s.*?\n\t\)', s, re.S):
    b = m.group(0); vias.append(dict(at=tuple(map(float, f(b, "at").split()[:2])), d=float(f(b, "size")), n=f(b, "net").strip('"')))
L = sum(math.dist(x["a"], x["b"]) for x in segs)
print("tracks %d (arcs %d)  vias %d  length %.1f mm" % (len(segs), arcs, len(vias), L))
print("by layer", dict(collections.Counter(x["L"] for x in segs)))
print("vias by net", dict(collections.Counter(v["n"] for v in vias)))
for n in ("/VIN", "+5V", "/MOTOR_P", "/MOTOR_N"):
    ws = collections.defaultdict(float)
    for x in segs:
        if x["n"] == n: ws[x["w"]] += math.dist(x["a"], x["b"])
    print("  %-9s" % n, {k: round(v, 2) for k, v in sorted(ws.items())})
geo = lambda nets: unary_union([LineString([x["a"], x["b"]]).buffer(x["w"] / 2, 16) for x in segs if x["n"] in nets] +
                               [Point(v["at"]).buffer(v["d"] / 2, 16) for v in vias if v["n"] in nets])
T = Point(163.65, 101.875).buffer(1.2, 64)
for n in ("/I2C_SDA", "/I2C_SCL"):
    print("  %s track/via copper to touch pad T: %.2f mm" % (n, geo({n}).distance(T)))
I2C = geo({"/I2C_SDA", "/I2C_SCL"}); MOT = geo({"/MOTOR_P", "/MOTOR_N"})
for n in ("/TOUCH_ELEC", "/TOUCH_SNS", "/TOUCH_DRV"):
    g = geo({n}); print("  %s to I2C %.2f mm, to motor %.1f mm" % (n, g.distance(I2C), g.distance(MOT)))
