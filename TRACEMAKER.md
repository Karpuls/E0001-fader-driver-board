# TraceMaker routing experiment (not for fab)

On this branch, `E0001_fader_driver.kicad_pcb` is the rev B board (master `10de656`) with **all tracks and vias stripped and routed again from scratch** by TraceMaker (github.com/DingoOz/TraceMaker). Placement, zones and footprints are unchanged. Compare it against `master` to judge the autorouter. Rev B on master is still the board for fab.

Command (Router's pipeline): `TM_TIME=180 ~/tools/tm_route.sh E0001_fader_driver.kicad_pcb`
- TraceMaker options: `--reroute --soft-zones --stitch-vias planes --keep-vias-off-pads --vias-off-pads-below 2 --widen-power --no-tracks-on In1.Cu,In2.Cu`
- Rule: no vias on or under pads (≥ 0.15 mm copper gap to any pad under 2 mm; exposed-pad thermal vias are exempt), checked by `tm_viapad.py`.
- The first version of this branch (2da4aa1) had 16 vias on pads and one GND via 0.02 mm from C6. This version has 0, and no fix-up vias were needed.

Result:
- 51/51 connections routed, 144 tracks, 30 vias, TraceMaker exit 0. The routing itself took about 16 s.
- KiCad DRC with the JLC dru and schematic parity: 0 violations, 0 unconnected, 0 parity issues.
- slots.py: 0 same-net slivers. tm_viapad.py: 0 vias on or under pads.
- corners.py: 2 acute joins (+3V3 T-join on B.Cu at 130.32, 101.56; VSENSE into C9) and 2 right angles into pads (TOUCH_ELEC at D2, TOUCH_SNS at R6). These would be fixed by hand.
- MOTOR_P/N and +5V are at their 0.5 mm Power class width, necked to 0.15–0.25 mm at a few pads.

Not reviewed: I2C distance from the touch pad, and the motor-loop and touch-sense layout that master's QC rounds fixed. TraceMaker marks all its tracks as locked.
