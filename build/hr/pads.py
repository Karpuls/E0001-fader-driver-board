import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1])
T = pcbnew.ToMM
bb = b.GetBoardEdgesBoundingBox(); print("edge", T(bb.GetLeft()), T(bb.GetTop()), T(bb.GetRight()), T(bb.GetBottom()))
for fp in b.GetFootprints():
    print("FP", fp.GetReference(), fp.GetFPID().GetLibItemName(), T(fp.GetX()), T(fp.GetY()), fp.GetOrientationDegrees(), "B" if fp.IsFlipped() else "F")
    for p in fp.Pads():
        s = p.GetSize(pcbnew.F_Cu) if hasattr(p,'GetSize') else None
        print("  ", p.GetNumber(), p.GetNetname(), round(T(p.GetX()),3), round(T(p.GetY()),3), round(T(p.GetBoundingBox().GetWidth()),2), round(T(p.GetBoundingBox().GetHeight()),2), "TH" if p.GetAttribute()==pcbnew.PAD_ATTRIB_PTH else ("NP" if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH else "SMD"))
