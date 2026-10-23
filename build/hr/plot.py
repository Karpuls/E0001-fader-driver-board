"""plot.py geom.json board x0,x1,y0,y1 out.png [nets...]  - detailed zoom render"""
import json, re, sys, math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP, Circle
G = json.load(open(sys.argv[1])); s = open(sys.argv[2]).read()
x0, x1, y0, y1 = map(float, sys.argv[3].split(","))
hl = set(sys.argv[5:])
fig, ax = plt.subplots(figsize=((x1 - x0) * 0.9, (y1 - y0) * 0.9), dpi=110)
for p in G["pads"]:
    for L, pl in p["poly"].items():
        if L not in ("F.Cu", "B.Cu"): continue
        if p["attr"] in ("smd", "conn") and L == "B.Cu" and "F.Cu" in p["poly"]: continue
        for r in pl:
            ax.add_patch(MP(r, closed=True, fc=("#e8a0a0" if L == "F.Cu" else "#a0b0e8") if p["attr"] in ("smd","conn") else "#c8c8a0", ec="k", lw=0.3, alpha=0.8))
    if x0 < p["x"] < x1 and y0 < p["y"] < y1:
        ax.text(p["x"], p["y"], "%s.%s\n%s" % (p["ref"], p["num"], p["net"].replace("/", "")), fontsize=4.5, ha="center", va="center", clip_on=True)
for m in re.finditer(r'\n\t\(segment\s.*?\n\t\)', s, re.S):
    b = m.group(0); f = lambda k: re.search(r'\(' + k + r' ([^)]*)\)', b).group(1)
    a = list(map(float, f("start").split())); e = list(map(float, f("end").split()))
    L = f("layer").strip('"'); n = f("net").strip('"')
    c = "#c00000" if L == "F.Cu" else "#0030d0"
    lw = float(f("width")) * 72 * 0.9 * 1.0
    ax.plot([a[0], e[0]], [a[1], e[1]], color=c, lw=lw / 1.0 * 0.99, alpha=0.55 if not hl or n in hl else 0.2, solid_capstyle="round")
for m in re.finditer(r'\n\t\(via\s.*?\n\t\)', s, re.S):
    b = m.group(0); at = list(map(float, re.search(r'\(at ([^)]*)\)', b).group(1).split()))
    d = float(re.search(r'\(size ([^)]*)\)', b).group(1)); n = re.search(r'\(net "([^"]*)"', b).group(1)
    ax.add_patch(Circle(at[:2], d / 2, fc="#202020", alpha=0.7)); ax.text(at[0], at[1] - 0.4, n.replace("/", ""), fontsize=4, color="g", ha="center", clip_on=True)
ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect("equal")
ax.set_xticks([x0 + i for i in range(int(x1 - x0) + 1)]); ax.set_yticks([y0 + i for i in range(int(y1 - y0) + 1)])
ax.tick_params(labelsize=5); ax.grid(lw=0.2)
plt.savefig(sys.argv[4])
