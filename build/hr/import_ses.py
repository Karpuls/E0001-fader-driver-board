import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1])
print("import", pcbnew.ImportSpecctraSES(b, sys.argv[2]))
b.Save(sys.argv[3])
