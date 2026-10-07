#!/usr/bin/env python3
"""Hand-planned routes for power, motor, analog/touch, I2C and 3V3 (locked), plus helpers."""
import os, sys, math, json
import pcbnew

PROJ = '/home/karpulis/KiCad/E0001 - fader driver board'
PCB = os.path.join(PROJ, 'E0001_fader_driver.kicad_pcb')
MM, TO = pcbnew.FromMM, pcbnew.ToMM
OX, OY = 100.0, 100.0
F, B = pcbnew.F_Cu, pcbnew.B_Cu

# (net, layer, width, [points in board coords])
ROUTES = [
    # ---- VIN: J1 pin 1 -> via -> bottom through the fader gap -> via -> top edge -> Q1 drain
    ('/VIN', F, 0.6, [(68.55, 1.875), (68.55, 3.05)]),
    ('/VIN', B, 0.6, [(68.55, 3.05), (65.5, 0.0), (54.4, 0.0), (54.4, -6.85)]),
    ('/VIN', F, 0.6, [(54.4, -6.85), (53.5, -7.75), (11.8, -7.75), (11.8, -7.237)]),
    # ---- +5V trunk to the driver and branches
    ('+5V', F, 0.6, [(12.75, -5.362), (12.75, -4.0), (-22.28, -4.0), (-22.28, -2.3)]),
    ('+5V', F, 0.5, [(-19.48, -4.0), (-19.48, -2.3)]),
    ('+5V', F, 0.3, [(-22.28, -2.3), (-22.28, -1.08), (-21.95, -0.75)]),
    ('+5V', F, 0.3, [(-19.48, -2.3), (-19.48, -1.32), (-20.05, -0.75)]),
    ('+5V', F, 0.6, [(12.75, -4.0), (18.35, -4.0), (18.925, -4.575), (18.925, -6.6)]),
    ('+5V', F, 0.6, [(14.45, -4.0), (14.45, -5.4)]),
    ('+5V', F, 0.6, [(15.05, -4.0), (15.05, -2.4)]),
    ('+5V', F, 0.25, [(18.925, -4.575), (19.9, -3.6), (38.4, -3.6), (38.4, -4.19)]),
    # ---- gate
    ('Net-(Q1-G)', F, 0.3, [(10.85, -5.362), (9.51, -5.36)]),
    # ---- LDO in / out and 3V3 to the MCU (under the TSSOP body)
    ('/LDO_IN', F, 0.4, [(20.575, -6.6), (22.0, -6.6), (22.0, -6.375), (23.087, -6.375), (23.862, -5.6)]),
    ('+3V3', F, 0.3, [(25.737, -6.55), (42.9, -6.55), (42.9, -3.6), (43.2, -3.3), (43.2, 0.975), (46.863, 0.975),
                      (48.8, 0.975), (48.8, 1.13)]),
    ('+3V3', F, 0.3, [(48.8, 1.13), (49.395, 1.725), (50.4, 1.725)]),
    # ---- motor outputs
    ('/MOTOR_N', F, 0.3, [(-21.95, -0.25), (-22.7, -0.25), (-22.93, -0.48)]),
    ('/MOTOR_N', F, 0.5, [(-22.93, -0.48), (-26.0, -0.48), (-29.0, -3.48), (-29.55, -4.0)]),
    ('/MOTOR_P', F, 0.3, [(-21.95, 0.25), (-22.7, 0.25), (-22.93, 0.48)]),
    ('/MOTOR_P', F, 0.5, [(-22.93, 0.48), (-26.0, 0.48), (-29.0, 3.48), (-29.55, 4.0)]),
    # ---- fader position / pot supply / touch
    ('/POT_HI', F, 0.25, [(46.863, -2.275), (53.5, -2.275), (53.9, -1.875), (63.65, -1.875)]),
    ('/FADER_POS', F, 0.2, [(46.863, -2.925), (51.1, -2.925), (51.49, -3.3)]),
    ('/FADER_POS', F, 0.2, [(49.12, -2.925), (49.12, -3.75)]),
    ('/FADER_WIPER', F, 0.25, [(52.51, -3.3), (59.0, -3.3), (61.325, -5.625), (63.65, -5.625)]),
    ('/TOUCH_DRV', F, 0.2, [(46.863, -1.625), (49.69, -1.625)]),
    ('/TOUCH_SNS', F, 0.2, [(46.863, -0.975), (51.99, -0.975)]),
    ('/TOUCH_SNS', F, 0.2, [(50.71, -1.625), (50.71, -0.975)]),
    ('/TOUCH_ELEC', F, 0.25, [(53.01, -0.975), (53.45, -0.535), (53.45, 0.55), (54.0, 0.55), (55.325, 1.875), (63.65, 1.875)]),
    # ---- I2C through the gap between fader pins T and 1, then up to J1
    ('/I2C_SDA', F, 0.2, [(46.863, 2.925), (58.4, 2.925), (58.925, 3.45), (65.6, 3.45), (65.6, -0.625), (68.55, -0.625)]),
    ('/I2C_SCL', F, 0.2, [(41.137, 2.925), (40.1, 2.925), (40.1, 3.95), (54.6, 3.95), (54.9, 3.65), (58.4, 3.65),
                          (58.8, 4.05), (66.4, 4.05), (66.4, 0.625), (68.55, 0.625)]),
]
ROUTES += [
    # ---- NRST: under-body via, bottom layer to the SWD pads, on to C6
    ('/NRST', F, 0.2, [(46.863, -0.325), (45.2, -0.325)]),
    ('/NRST', B, 0.2, [(45.2, -0.325), (43.275, 1.6), (33.6, 1.6), (33.0, 2.2), (33.0, 2.965)]),
    ('/NRST', B, 0.2, [(33.6, 1.6), (29.9, 1.6), (29.3, 1.0)]),
    ('/NRST', F, 0.2, [(29.3, 1.0), (28.48, 1.0)]),
]
VIAS = [('/VIN', (68.55, 3.05), 0.8, 0.4), ('/VIN', (54.4, -6.85), 0.8, 0.4),
        ('/NRST', (45.2, -0.325), 0.6, 0.3), ('/NRST', (29.3, 1.0), 0.6, 0.3)]

def apply(board):
    nets = {n: board.FindNet(n) for n in set(r[0] for r in ROUTES) | set(v[0] for v in VIAS)}
    for n, ni in nets.items():
        if ni is None:
            raise RuntimeError('net missing ' + n)
    for net, layer, w, pts in ROUTES:
        for a, b in zip(pts[:-1], pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(MM(OX + a[0]), MM(OY + a[1])))
            t.SetEnd(pcbnew.VECTOR2I(MM(OX + b[0]), MM(OY + b[1])))
            t.SetWidth(MM(w)); t.SetLayer(layer); t.SetNet(nets[net]); t.SetLocked(True)
            board.Add(t)
    for net, (x, y), d, dr in VIAS:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(MM(OX + x), MM(OY + y)))
        v.SetWidth(MM(d)); v.SetDrill(MM(dr)); v.SetNet(nets[net]); v.SetLocked(True)
        board.Add(v)

if __name__ == '__main__':
    board = pcbnew.LoadBoard(PCB)
    for t in list(board.GetTracks()):
        board.Remove(t)
    apply(board)
    pcbnew.SaveBoard(PCB, board)
    print('prerouted', len(board.GetTracks()))
