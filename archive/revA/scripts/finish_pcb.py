#!/usr/bin/env python3
"""Phase 3: import Freerouting session, add GND pours on F.Cu and B.Cu, fill, save."""
import sys, os
import pcbnew

PROJ = '/home/karpulis/KiCad/E0001 - fader driver board'
PCB = os.path.join(PROJ, 'E0001_fader_driver.kicad_pcb')
SES = os.path.join(PROJ, 'build/route/board.ses')
MM = pcbnew.FromMM
OX, OY = 100.0, 100.0
OUTLINE = [(-33.5, -8.4), (57.9, -8.4), (57.9, -7.8), (73.5, -7.8), (73.5, 7.8), (57.9, 7.8), (57.9, 8.4), (-33.5, 8.4)]

board = pcbnew.LoadBoard(PCB)
if len(sys.argv) < 2 or sys.argv[1] != '--no-ses':
    ok = pcbnew.ImportSpecctraSES(board, SES)
    print('ses import', ok)

# re-add GND vias/stubs if the session import dropped them
import json
gnd = board.FindNet('GND')
have = [(pcbnew.ToMM(t.GetPosition().x), pcbnew.ToMM(t.GetPosition().y))
        for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
have_gnd_tracks = any(t.Type() == pcbnew.PCB_TRACE_T and t.GetNetCode() == gnd.GetNetCode() for t in board.GetTracks())
added = 0
for it in json.load(open(os.path.join(PROJ, 'build/route/gnd_items.json'))):
    if it[0] == 'via':
        if any(abs(it[1] - hx) < 0.05 and abs(it[2] - hy) < 0.05 for hx, hy in have):
            continue
        v = pcbnew.PCB_VIA(board); v.SetPosition(pcbnew.VECTOR2I(MM(it[1]), MM(it[2])))
        v.SetWidth(MM(it[3])); v.SetDrill(MM(it[4])); v.SetNet(gnd); board.Add(v); added += 1
    elif added or not have_gnd_tracks:
        t = pcbnew.PCB_TRACK(board); t.SetStart(pcbnew.VECTOR2I(MM(it[1]), MM(it[2]))); t.SetEnd(pcbnew.VECTOR2I(MM(it[3]), MM(it[4])))
        t.SetWidth(MM(it[5])); t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd); board.Add(t)
print('gnd vias re-added', added)

# min width fix: Freerouting sometimes necks down to 0.1 mm at pads
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_TRACE_T and t.GetWidth() < MM(0.15):
        t.SetWidth(MM(0.15))

# co-located duplicate vias
seen = []
for v in [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]:
    p = v.GetPosition()
    if any(abs(p.x - q.x) < 1000 and abs(p.y - q.y) < 1000 for q in seen):
        board.Remove(v)
        continue
    seen.append(p)

# redundant vias: all attached tracks on one layer and no pad there
gndc = board.FindNet('GND').GetNetCode()
for v in [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]:
    if v.GetNetCode() == gndc:
        continue
    p = v.GetPosition()
    layers = set()
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetCode() == v.GetNetCode():
            for e in (t.GetStart(), t.GetEnd()):
                if abs(e.x - p.x) < 1000 and abs(e.y - p.y) < 1000:
                    layers.add(t.GetLayer())
    if len(layers) == 1:
        board.Remove(v)
        print('removed redundant via', pcbnew.ToMM(p.x) - OX, pcbnew.ToMM(p.y) - OY)

# remove old zones
for z in list(board.Zones()):
    board.Remove(z)

gnd = board.FindNet('GND')
for layer, prio in ((pcbnew.F_Cu, 0), (pcbnew.B_Cu, 0)):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(gnd)
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(MM(0.2))
    z.SetMinThickness(MM(0.2))
    z.SetThermalReliefGap(MM(0.25))
    z.SetThermalReliefSpokeWidth(MM(0.35))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in OUTLINE:
        ol.Append(MM(OX + x), MM(OY + y))
    board.Add(z)

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
pcbnew.SaveBoard(PCB, board)
import subprocess
subprocess.run([sys.executable, os.path.join(PROJ, 'build/scripts/patch_pro.py')])
print('saved with', len(list(board.Zones())), 'zones,', len(board.GetTracks()), 'tracks/vias')
