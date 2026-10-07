#!/usr/bin/env python3
"""Phase 1: build E0001_fader_driver.kicad_pcb from the schematic netlist: footprints, nets, placement, outline."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
from sexp import parse, find, findall

PROJ = '/home/karpulis/KiCad/E0001 - fader driver board'
NAME = 'E0001_fader_driver'
FPLIB = '/home/karpulis/.backplane-bend/kicad/10.0.6/share/kicad/footprints'
OX, OY = 100.0, 100.0          # board coords (fader travel centre) -> page coords
MM = pcbnew.FromMM

def P(x, y):
    return pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))

# ------------------------------------------------------------------ netlist
net = parse(open(os.path.join(PROJ, 'build/out/netlist.net')).read())
comps = {}
for c in findall(find(net, 'components'), 'comp'):
    ref = find(c, 'ref')[1]
    fields = {find(f, 'name')[1]: (f[2] if len(f) > 2 else '') for f in findall(find(c, 'fields'), 'field')}
    props = {find(p, 'name')[1] for p in findall(c, 'property')}
    comps[ref] = dict(value=find(c, 'value')[1], fp=find(c, 'footprint')[1], fields=fields,
                      uuid=find(c, 'tstamps')[1], dnp='dnp' in props, nobom='exclude_from_bom' in props)
padnet = {}
netnames = []
for n in findall(find(net, 'nets'), 'net'):
    nm = find(n, 'name')[1]
    netnames.append(nm)
    for nd in findall(n, 'node'):
        padnet[(find(nd, 'ref')[1], find(nd, 'pin')[1])] = nm

# ------------------------------------------------------------------ placement (x, y, rot, side)
PLACE = {
    'RV1': (0.0, 0.0, 0, 'F'),
    'J1': (70.4, 0.0, 90, 'F'),
    'U1': (44.0, 0.0, 180, 'F'),
    # analog / touch cluster between MCU and fader terminal block
    'C7': (49.6, -3.75, 0, 'F'),
    'R7': (52.0, -3.3, 180, 'F'),
    'R6': (50.2, -1.625, 0, 'F'),
    'R5': (52.5, -0.975, 180, 'F'),
    'D2': (53.45, 0.9, 270, 'F'),
    'C4': (48.8, 0.65, 90, 'F'),
    'C5': (50.4, 0.95, 90, 'F'),
    # supply sense next to PA4
    'R8': (38.4, -4.7, 90, 'F'),
    'R9': (38.0, -2.925, 180, 'F'),
    'C9': (36.6, -4.7, 90, 'F'),
    # status LED
    'R10': (31.2, -2.3, 180, 'F'),
    'D3': (28.6, -2.3, 0, 'F'),
    # power entry + LDO (top band, middle of board)
    'Q1': (11.8, -6.3, 90, 'F'),
    'R1': (9.0, -5.36, 180, 'F'),
    'D1': (15.9, -5.4, 0, 'F'),
    'C1': (16.0, -2.4, 0, 'F'),
    'R2': (19.75, -6.6, 0, 'F'),
    'C2': (22.0, -5.6, 270, 'F'),
    'U2': (24.8, -5.6, 180, 'F'),
    'C3': (27.6, -5.9, 270, 'F'),
    # I2C pull-ups (DNP) and NRST cap, below the MCU
    'C6': (28.0, 1.0, 180, 'F'),
    # motor driver
    'U3': (-21.0, 0.0, 0, 'F'),
    'C10': (-21.8, -2.3, 0, 'F'),
    'C13': (-19.0, -2.3, 0, 'F'),
    'C11': (-16.2, -5.6, 90, 'F'),
    'C12': (-13.6, -5.6, 90, 'F'),
    'C14': (-26.0, 0.0, 90, 'F'),
    # bottom side: SWD pads and address jumpers (reachable with the fader mounted)
    'J2': (33.0, 3.6, 0, 'B'),
    'JP1': (37.4, 6.9, 0, 'B'),
    'JP2': (40.8, 6.9, 0, 'B'),
    'JP3': (44.2, 6.9, 0, 'B'),
}

board = pcbnew.CreateEmptyBoard()
board.SetCopperLayerCount(2)
nets = {}
for nm in netnames:
    ni = pcbnew.NETINFO_ITEM(board, nm)
    board.Add(ni)
    nets[nm] = ni

def side_of(ref):
    return PLACE.get(ref, (0, 0, 0, 'F'))[3]

def load_fp(fpid):
    lib, name = fpid.split(':', 1)
    path = os.path.join(PROJ, 'lib/Fader.pretty') if lib == 'Fader' else os.path.join(FPLIB, lib + '.pretty')
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError('footprint not found ' + fpid)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp

for ref, c in sorted(comps.items()):
    fp = load_fp(c['fp'])
    fp.SetReference(ref)
    fp.SetValue(c['value'])
    fp.SetPath(pcbnew.KIID_PATH('/' + c['uuid']))
    fp.SetSheetname('/')
    fp.SetSheetfile(NAME + '.kicad_sch')
    for k in ('MPN', 'Manufacturer', 'Voltage', 'Dielectric', 'Datasheet', 'Description'):
        v = c['fields'].get(k)
        if v:
            fp.SetField(k, v)
            f = fp.GetField(k)
            f.SetVisible(False)
            if k not in ('Datasheet', 'Description'):
                f.SetLayer(pcbnew.F_Fab if side_of(ref) == 'F' else pcbnew.B_Fab)
    if c['dnp']:
        fp.SetDNP(True)
    if c['nobom']:
        fp.SetExcludedFromBOM(True)
        fp.SetExcludedFromPosFiles(True)
    for pad in fp.Pads():
        k = (ref, pad.GetNumber())
        if k in padnet:
            pad.SetNet(nets[padnet[k]])
        if ref == 'RV1' and pad.GetNumber() in ('1', 'FG'):
            pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    if ref == 'U3':   # library lacks the DSG-named model; same body as the generic WSON-8 2x2
        fp.Models()[0].m_Filename = '${KICAD10_3DMODEL_DIR}/Package_SON.3dshapes/WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm.step'
    board.Add(fp)
    x, y, rot, side = PLACE.get(ref, (0, 20, 0, 'F'))
    if side == 'B':
        fp.SetLayerAndFlip(pcbnew.B_Cu)
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(P(x, y))
    # field text: small silk reference, value on fab
    fp.Reference().SetTextSize(pcbnew.VECTOR2I(MM(0.7), MM(0.7)))
    fp.Reference().SetTextThickness(MM(0.12))
    fp.Value().SetVisible(False) if False else None

missing = [r for r in comps if r not in PLACE]
print('unplaced:', missing)

# ------------------------------------------------------------------ outline (inside the fader projection)
OUT = [(-33.5, -8.4), (57.9, -8.4), (57.9, -7.8), (73.5, -7.8), (73.5, 7.8), (57.9, 7.8), (57.9, 8.4), (-33.5, 8.4)]
for a, b in zip(OUT, OUT[1:] + OUT[:1]):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(P(*a)); s.SetEnd(P(*b))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(MM(0.05))
    board.Add(s)

out = os.path.join(PROJ, NAME + '.kicad_pcb')
board.Save(out) if hasattr(board, 'Save') else pcbnew.SaveBoard(out, board)
print('saved', out)
