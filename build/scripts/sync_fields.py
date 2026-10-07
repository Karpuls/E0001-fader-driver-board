#!/usr/bin/env python3
"""Copy symbol fields (value, MPN, Manufacturer, Farnell, ...) from the netlist onto the existing PCB footprints (no re-route)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
from sexp import parse, find, findall
PROJ = '/home/karpulis/KiCad/E0001 - fader driver board'
PCB = os.path.join(PROJ, 'E0001_fader_driver.kicad_pcb')
net = parse(open(os.path.join(PROJ, 'build/out/netlist.net')).read())
board = pcbnew.LoadBoard(PCB)
for c in findall(find(net, 'components'), 'comp'):
    ref = find(c, 'ref')[1]
    fp = board.FindFootprintByReference(ref)
    if fp is None:
        print('missing footprint', ref); continue
    fp.SetValue(find(c, 'value')[1])
    fields = {find(f, 'name')[1]: (f[2] if len(f) > 2 else '') for f in findall(find(c, 'fields'), 'field')}
    for k in ('MPN', 'Manufacturer', 'DigiKey', 'Voltage', 'Dielectric', 'Datasheet', 'Description'):
        v = fields.get(k)
        if v:
            new = not fp.HasField(k)
            fp.SetField(k, v)
            f = fp.GetField(k); f.SetVisible(False)
            if new and k not in ('Datasheet', 'Description'):
                f.SetLayer(pcbnew.F_Fab if fp.GetLayer() == pcbnew.F_Cu else pcbnew.B_Fab)
pcbnew.SaveBoard(PCB, board)
