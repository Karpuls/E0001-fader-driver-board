import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1]); T=pcbnew.ToMM
for z in b.Zones():
    bb=z.GetBoundingBox()
    print(z.GetNetname(), [b.GetLayerName(l) for l in z.GetLayerSet().Seq()], "keepout" if z.GetIsRuleArea() else "", "prio",z.GetAssignedPriority(), "bbox",T(bb.GetLeft()),T(bb.GetTop()),T(bb.GetRight()),T(bb.GetBottom()), "clr", T(z.GetLocalClearance() or 0), "pts", z.Outline().FullPointCount(), "thermal", T(z.GetThermalReliefGap()), T(z.GetThermalReliefSpokeWidth()), "padconn", z.GetPadConnection())
ds=b.GetDesignSettings()
print("min via", T(ds.m_ViasMinSize), "clr", T(ds.m_MinClearance))
