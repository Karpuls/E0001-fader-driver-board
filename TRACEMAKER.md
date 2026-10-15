# TraceMaker routing experiment (not for fab)

On this branch, `E0001_fader_driver.kicad_pcb` is the rev B board (master `10de656`) with **all tracks and vias stripped and routed again from scratch** by TraceMaker (github.com/DingoOz/TraceMaker). Placement, zones and footprints are unchanged. Compare it against `master` to judge the autorouter. Rev B on master is still the board for fab.

Command (Router's pipeline): `TM_TIME=180 ~/tools/tm_route.sh E0001_fader_driver.kicad_pcb`
- TraceMaker options: `--reroute --soft-zones --stitch-vias planes --widen-power --no-tracks-on In1.Cu,In2.Cu`
- Cleanup steps added 3 GND vias: C6 pad 2 and R9 pad 2 were boxed in with starved thermals, and one F.Cu GND pour island was floating.

Result:
- 51/51 connections routed, 145 tracks, 34 vias. The routing itself took about 23 s.
- KiCad DRC with the JLC dru and schematic parity: 0 violations, 0 unconnected, 0 parity issues.
- slots.py: 0 same-net slivers.
- corners.py: 2 acute joins (+3V3 T-join on B.Cu at 130.32, 101.56; GND into R9 pad 2) and 2 right angles into pads (TOUCH_ELEC at D2, TOUCH_SNS at R6). These would be fixed by hand.
- MOTOR_P/N and +5V are at their 0.5 mm Power class width, necked to 0.15–0.25 mm at a few pads.

Not reviewed: I2C distance from the touch pad, and the motor-loop and touch-sense layout that master's QC rounds fixed. TraceMaker marks all its tracks as locked.
