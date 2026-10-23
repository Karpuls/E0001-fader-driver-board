"""Dump pad copper polygons, courtyards and rule areas to JSON (run with kpy.sh)."""
import pcbnew, sys, json
b = pcbnew.LoadBoard(sys.argv[1]); T = pcbnew.ToMM
CU = {pcbnew.F_Cu: "F.Cu", pcbnew.B_Cu: "B.Cu", pcbnew.In1_Cu: "In1.Cu", pcbnew.In2_Cu: "In2.Cu"}
def polys(sps):
    out = []
    for i in range(sps.OutlineCount()):
        o = sps.Outline(i)
        out.append([(T(o.CPoint(j).x), T(o.CPoint(j).y)) for j in range(o.PointCount())])
    return out
res = {"pads": [], "fps": [], "keepouts": []}
for fp in b.GetFootprints():
    cy = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
    bb = fp.GetBoundingBox(False)
    res["fps"].append(dict(ref=fp.GetReference(), x=T(fp.GetX()), y=T(fp.GetY()), side="B" if fp.IsFlipped() else "F",
                           court=polys(cy), bbox=[T(bb.GetLeft()), T(bb.GetTop()), T(bb.GetRight()), T(bb.GetBottom())]))
    for z in fp.Zones():
        res["keepouts"].append(dict(ref=fp.GetReference(), layers=[b.GetLayerName(l) for l in z.GetLayerSet().Seq()],
                                    vias=z.GetDoNotAllowVias(), tracks=z.GetDoNotAllowTracks(), poly=polys(z.Outline())))
    for p in fp.Pads():
        layers = [CU[l] for l in CU if p.IsOnLayer(l)]
        attr = {pcbnew.PAD_ATTRIB_PTH: "pth", pcbnew.PAD_ATTRIB_NPTH: "npth", pcbnew.PAD_ATTRIB_SMD: "smd", pcbnew.PAD_ATTRIB_CONN: "conn"}[p.GetAttribute()]
        shp = {}
        for lid, l in CU.items():
            if not p.IsOnLayer(lid): continue
            sp = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(sp, lid, 0, 2000)
            shp[l] = polys(sp)
        res["pads"].append(dict(ref=fp.GetReference(), num=p.GetNumber(), net=p.GetNetname(), attr=attr, x=T(p.GetX()), y=T(p.GetY()),
                                layers=layers, poly=shp, drill=T(p.GetDrillSizeX()) if attr in ("pth", "npth") else 0,
                                minor=min(T(p.GetBoundingBox().GetWidth()), T(p.GetBoundingBox().GetHeight()))))
json.dump(res, open(sys.argv[2], "w"))
print(len(res["pads"]), "pads", len(res["keepouts"]), "keepouts")
