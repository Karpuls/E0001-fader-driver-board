#!/usr/bin/env python3
"""Rev C, step 1: turn the rev B board into the rev C board (netlist, footprints, placement, text).

Starts from the rev B board (build/backup/revB_before_revC_*.kicad_pcb), keeps the outline, the four
zones and RV1 exactly, drops all rev B copper, re-creates every other footprint from the library
with the rev C netlist fields, and places them.  Coordinates are absolute (page) mm.

Usage: revC_strip.py <revB board> <stripped> RV1; revC_place.py <stripped> <out board>
"""
import gc
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
from sexp import parse, find, findall

gc.disable()
PROJ = '/home/karpulis/KiCad/E0001 - fader driver board'
NAME = 'E0001_fader_driver'
FPLIB = '/home/karpulis/.backplane-bend/kicad/10.0.6/share/kicad/footprints'
MM = pcbnew.FromMM
SRC, OUT = sys.argv[1], sys.argv[2]

def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))

# ------------------------------------------------------------------ netlist
net = parse(open(os.path.join(PROJ, 'build/revC/netlist.net')).read())
comps = {}
for c in findall(find(net, 'components'), 'comp'):
    ref = find(c, 'ref')[1]
    fields = [(find(f, 'name')[1], (f[2] if len(f) > 2 else '')) for f in findall(find(c, 'fields'), 'field')]
    props = {find(p, 'name')[1] for p in findall(c, 'property')}
    comps[ref] = dict(value=find(c, 'value')[1], fp=find(c, 'footprint')[1], fields=fields,
                      uuid=find(c, 'tstamps')[1], dnp='dnp' in props, nobom='exclude_from_bom' in props)
padnet, netnames = {}, []
for n in findall(find(net, 'nets'), 'net'):
    nm = find(n, 'name')[1]
    netnames.append(nm)
    for nd in findall(n, 'node'):
        padnet[(find(nd, 'ref')[1], find(nd, 'pin')[1])] = nm

# ------------------------------------------------------------------ placement: ref -> (x, y, rot, side)
PLACE = {
    # --- J1 + I2C protection (south of J1, outside the terminal block)
    'J1': (170.4, 100.0, 90, 'F'),
    'R20': (166.85, 105.8, 270, 'F'),     # SDA 0R
    'R19': (167.6, 107.75, 180, 'F'),     # SCL 0R
    'D5': (168.4, 105.6, 0, 'F'),         # SDA ESD
    'D4': (169.45, 107.65, 0, 'F'),        # SCL ESD
    # --- eFuse cluster: north band between MCU and terminal block (where Q1/R1 were)
    'U4': (148.4, 94.8, 90, 'F'),         # IN bar south (exit east), OUT bar north (exit west)
    'R15': (148.685, 92.75, 0, 'F'),      # ILM -> GND, pad 1 straight above pin 9
    'R16': (146.7, 92.6, 180, 'F'),      # ILM -> ILM_ADC
    'C15': (145.9, 93.7, 180, 'F'),       # ITIMER
    'C16': (150.42, 93.0, 90, 'F'),         # DVDT
    'C17': (151.45, 94.0, 90, 'F'),        # IN 100n, pad 1 on the PBUS trunk
    'C18': (152.8, 93.9, 90, 'F'),        # IN 4.7u 0603
    'R13': (151.0, 96.45, 270, 'F'),       # PBUS -> OVLO
    'R11': (152.3, 96.45, 270, 'F'),       # PBUS -> EN
    'R14': (151.0, 98.45, 270, 'F'),       # OVLO -> GND
    'R12': (152.3, 98.45, 270, 'F'),       # EN -> GND
    'C1': (143.1, 94.5, 180, 'F'),        # VM_P bulk at U4 OUT
    # --- MCU
    'U1': (137.5, 100.0, 180, 'F'),
    'C7': (142.6, 97.075, 0, 'F'),        # FADER_POS, pin 10
    'R7': (145.25, 97.4, 0, 'F'),         # wiper 1k
    'C19': (142.6, 98.375, 0, 'F'),       # ILM_ADC, pin 9 (via track between)
    'R6': (145.25, 98.7, 0, 'F'),         # TOUCH_DRV -> TOUCH_SNS
    'C6': (142.6, 99.675, 0, 'F'),      # NRST
    'C4': (142.6, 101.0, 0, 'F'),       # +3V3 pin 4 / GND pin 5
    'R5': (146.6, 100.4, 180, 'F'),       # TOUCH_ELEC -> TOUCH_SNS
    'D2': (148.6, 100.95, 90, 'F'),       # touch ESD
    'C5': (145.2, 102.3, 0, 'F'),         # +3V3 4.7u
    'D6': (143.6, 104.3, 180, 'F'),      # NRST -> J2 pin 6 (BAT54W)
    'R17': (133.0, 101.55, 90, 'F'),       # BOOT0 pull-down
    'R18': (132.9, 98.0, 90, 'F'),        # J2 B0 -> BOOT0 1k
    # address jumpers, bottom, south-east of U1
    'JP1': (136.0, 106.6, 0, 'B'),
    'JP2': (139.4, 106.6, 0, 'B'),
    'JP3': (142.8, 106.6, 0, 'B'),
    # --- J2 UART header: top, south edge, pins out of the edge
    'J2': (131.0, 104.45, 270, 'F'),
    # --- VSENSE, LED
    'R8': (131.0, 93.3, 90, 'F'),
    'R9': (132.3, 94.9, 0, 'F'),
    'C9': (132.3, 96.0, 0, 'F'),
    'R10': (125.9, 99.2, 180, 'F'),
    'D3': (123.4, 99.2, 0, 'F'),
    # --- LDO
    'D7': (128.6, 98.7, 0, 'F'),
    'R2': (121.0, 93.0, 0, 'F'),
    'C2': (123.4, 95.0, 90, 'F'),
    'U2': (127.0, 94.6, 180, 'F'),
    'C3': (124.4, 97.8, 0, 'F'),
    # --- motor driver
    'U3': (79.0, 100.0, 0, 'F'),
    'C13': (76.6, 98.3, 180, 'F'),
    'C10': (81.4, 98.2, 90, 'F'),
    'C14': (74.0, 100.0, 90, 'F'),
    'C11': (83.4, 94.4, 90, 'F'),
    'C12': (86.0, 94.4, 90, 'F'),
    'C20': (88.6, 94.4, 90, 'F'),
    'D1': (84.6, 105.4, 180, 'F'),
}
missing = [r for r in comps if r not in PLACE and r != 'RV1']
assert not missing, missing

b = pcbnew.LoadBoard(SRC)

# (rev B copper, parts and texts are already stripped by revC_strip.py)
# nets
nets = {}
for nm in netnames:
    ni = b.FindNet(nm)
    if ni is None:
        ni = pcbnew.NETINFO_ITEM(b, nm)
        b.Add(ni)
    nets[nm] = ni

# zones: In2 becomes VM_P, others stay GND (fills are stale: unfill, DRC refills)
for z in b.Zones():
    z.UnFill()
    if z.GetLayer() == pcbnew.In2_Cu:
        z.SetNet(nets['VM_P'])
    else:
        z.SetNet(nets['GND'])

def load_fp(fpid):
    lib, name = fpid.split(':', 1)
    path = os.path.join(PROJ, 'lib', lib + '.pretty') if lib in ('Fader', 'E0001') else os.path.join(FPLIB, lib + '.pretty')
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError('footprint not found ' + fpid)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp

def set_fields(fp, c, back):
    fp.SetValue(c['value'])
    for k, v in c['fields']:
        if k == 'Footprint':
            continue
        fp.SetField(k, v)
        f = fp.GetField(k)
        f.SetVisible(False)
        f.SetLayer(pcbnew.B_Fab if back else pcbnew.F_Fab)
    fp.SetDNP(c['dnp'])
    if c['nobom']:
        fp.SetExcludedFromBOM(True)
        fp.SetExcludedFromPosFiles(True)

for ref, c in sorted(comps.items()):
    if ref == 'RV1':
        fp = b.FindFootprintByReference('RV1')
        set_fields(fp, c, False)
    else:
        fp = load_fp(c['fp'])
        fp.SetReference(ref)
        fp.SetPath(pcbnew.KIID_PATH('/' + c['uuid']))
        fp.SetSheetname('/')
        fp.SetSheetfile(NAME + '.kicad_sch')
        x, y, rot, side = PLACE[ref]
        set_fields(fp, c, side == 'B')
        if ref == 'U3':   # library lacks the DSG-named model; same body as the generic WSON-8 2x2
            fp.Models()[0].m_Filename = '${KICAD10_3DMODEL_DIR}/Package_SON.3dshapes/WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm.step'
        b.Add(fp)
        if side == 'B':
            fp.SetLayerAndFlip(pcbnew.B_Cu)
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(V(x, y))
        # reference designators: fab only (no room for silk refs under the fader)
        fp.Reference().SetLayer(pcbnew.B_Fab if side == 'B' else pcbnew.F_Fab)
        fp.Reference().SetTextSize(V(0.5, 0.5))
        fp.Reference().SetTextThickness(MM(0.08))
        fp.Reference().SetPosition(fp.GetPosition())
        fp.Value().SetVisible(False)
    for pad in fp.Pads():
        k = (ref, pad.GetNumber())
        pad.SetNet(nets[padnet[k]] if k in padnet else b.FindNet(''))

# ------------------------------------------------------------------ silkscreen text
def text(s, x, y, layer, rot=0, h=1.0, t=0.15, just=0):
    tx = pcbnew.PCB_TEXT(b)
    tx.SetText(s)
    tx.SetLayer(layer)
    tx.SetTextSize(V(h, h))
    tx.SetTextThickness(MM(t))
    tx.SetTextAngleDegrees(rot)
    if layer == pcbnew.B_SilkS:
        tx.SetMirrored(True)
    if just:
        tx.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT if just < 0 else pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    tx.SetPosition(V(x, y))
    b.Add(tx)

F, B = pcbnew.F_SilkS, pcbnew.B_SilkS
text('PBUS 6–9 V', 166.72, 99.9, F, rot=90)
text('E0001 rev C', 100.0, 104.4, F)
text('J1: 1=PBUS 2=SCL 3=SDA 4=GND', 100.0, 106.4, F)
text('UART boot 3.3 V', 110.0, 102.4, F)
j2 = b.FindFootprintByReference('J2')
for pad, lab in zip(sorted(j2.Pads(), key=lambda p: int(p.GetNumber())), ['GND', '3V3', 'RX', 'TX', 'B0', 'RST']):
    text(lab, pad.GetPosition().x / 1e6, 101.45, F, rot=90)
for r, lab in (('JP1', 'A0'), ('JP2', 'A1'), ('JP3', 'A2')):
    p = b.FindFootprintByReference(r).GetPosition()
    text(lab, p.x / 1e6, 104.85, B)
text('addr 0x30–0x37, open = 1', 146.0, 103.2, B)

pcbnew.SaveBoard(OUT, b)
print('saved', OUT)
