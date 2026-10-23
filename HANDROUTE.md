# Hand-route experiment (not for fab)

On this branch, `E0001_fader_driver.kicad_pcb` is the rev B board (master `10de656`). All of its tracks and vias were stripped and the board was routed again **without TraceMaker**, to compare against `origin/backplane/e0001-tracemaker`. Placement, footprints, zones, outline, net classes, the `.kicad_pro` and the JLC `.kicad_dru` are unchanged. Rev B on master is still the board for fab.

## Method

Own scripts plus Freerouting 2.5.0. All scripts are in `build/hr/`.

1. `strip.py` removes every segment, arc and via at the s-expression level (215 items).
2. `preroute.py` is my own geometry code (shapely). It writes tracks straight into the board file:
   - **Motor loop by hand:** U3 pins 2/3 neck out at 0.25 mm, then run 0.5 mm to C14 (4 mm from the driver) and on to the motor pads M+/M−.
   - **U3 supply:** U3 pins 1 and 8 go to C10 and C13, then to +5V plane vias.
   - **U3 GND:** pin 4 runs into the exposed pad, which has two thermal vias.
   - **TOUCH_ELEC by hand:** from the fader touch pad T to D2 and R5.
   - **Plane fan-out:** every SMD GND pad gets its own In1 via (0.6/0.3). Every +5V pad gets its own In2 via (0.8/0.4, Power class). A search picks each via spot so it keeps ≥ 0.2 mm copper gap to every pad, stays off the J2 via keepout, the edge and the NPTH holes, and doesn't sit under its own part.
3. pcbnew (KiCad 10.0.6 Python) exports a Specctra DSN. I edited the DSN:
   - In1/In2 stay `power` layers, so no tracks go on the inner layers.
   - The F/B GND pours are removed from the DSN; KiCad refills them afterwards.
   - A 6.4 mm keepout circle on F/B around touch pad T enforces the I²C gap.
   - `via_at_smd off`.
   - Net-class clearances get +0.01 mm of margin.

   Freerouting then routed the remaining 39 nets in 4.3 s (`build/hr/fr/`). A second run with its optimizer was worse (3 unrouted), so I kept the first run.
4. `cleanup.py` is my own post-processor. It rebuilds each track chain between terminals as the shortest 45° path that keeps net-class clearance (+0.01 mm), stays 1.9 mm from T for I²C, and makes every join at a terminal at least 90.5°. It then chamfers any right-angle bends left over.
5. `fixes.py` and `fixes2.py` are explicit hand edits, each checked for clearance by the script and then by KiCad DRC:
   - On a 45° grid a T-join always contains a 90° angle. So +3V3, NRST, TOUCH_SNS, VSENSE and FADER_POS are daisy-chained through pads, or meet at a via on different layers, instead of T-joining.
   - VIN is redrawn at 0.5 mm all the way. Freerouting had necked it to 0.375 mm on free track.
   - The I²C runs near J1 are straightened, and the SDA via moved to remove a same-net slot.
   - TOUCH_ELEC moved up to y = 100.55, 2.7 mm from the I²C via.

Board edits happened in the file. KiCad was used for the DSN export, the SES import and the zone refill/DRC (`drc.sh`, `qc.sh`, `stats.py`).

**Time:** about 55 minutes wall-clock from stripping to DRC-clean (12:15 to 13:10), including writing the scripts. Freerouting itself took 4.3 s. Each cleanup pass takes under 1 s, and each DRC about 10 s.

## Result

| | Hand-route (this branch) | TraceMaker (`origin/backplane/e0001-tracemaker`, `1e285fc`) |
|---|---|---|
| Method | own pre-route/fan-out + Freerouting 2.5.0 + own cleanup + hand fixes | TraceMaker `--reroute …` (Router's pipeline) |
| Tracks (segments) | 216 (159 F.Cu, 57 B.Cu, 0 inner) | 144 (120 F.Cu, 24 B.Cu) |
| Vias | 60 (28 GND, 9 +5V, 23 signal) | 30 (8 GND, 11 +5V, 11 signal) |
| Total track length | 544.7 mm | 477.6 mm |
| DRC (parity, all severities, refill) | 0 / 0 unconnected / 0 parity | 0 / 0 / 0 |
| tm_viapad (vias on/under pads) | 0 | 0 |
| slots (after same-net pours) | 0 | 0 |
| corners.py | 0 acute, 0 right angle | 2 acute, 2 right angle |
| I²C copper to touch pad T | SDA 3.96 mm, SCL 2.17 mm | SDA 0.20 mm, SCL 0.92 mm |
| TOUCH_ELEC to I²C | 2.66 mm | 1.31 mm |
| GND via per GND pad | yes: 26 SMD GND pads with their own via, U3 pin 4 through the 2 EP thermal vias (RV1 TH GND pads go straight to In1) | 8 GND vias |
| VIN width | 0.5 mm, 28.4 mm, no necks | 0.5 mm |
| MOTOR_P/N | 0.5 mm; 0.25 mm neck for 1.05 mm per net at U3's 0.25 mm pins | 0.5 mm; 3.8 mm per net at 0.15–0.25 mm |

All lengths and counts come from `build/hr/stats.py`, run the same way on both boards (straight segments, no arcs on either).

### Checks, verbatim

- `kicad-cli pcb drc --schematic-parity --severity-all --refill-zones` (KiCad 10.0.6): `Found 0 violations`, `Found 0 unconnected items`, `Found 0 schematic parity issues`.
- `tm_viapad.py`: `vias on/under pads: 0 (gap < 0.15 mm, pads < 2.0 mm)`.
- `slots.py`: nothing listed after `--- after removing slots filled by same-net pours:`.
- `corners.py`: `Counter()` (no acute, right-angle or dangling entries).

The QC scripts ran with `/home/karpulis/.cache/e0002venv/bin/python -I` on a copy in `build/qc/copy/`.

### Power widths

- **/VIN:** 0.5 mm everywhere (28.4 mm).
- **+5V:** 0.5 mm (12.7 mm). The only exception is a 0.25 mm neck of 0.3 mm length at each of U3's two 0.25 mm VM pins. Every other +5V pad goes to the In2 plane through its own 0.8/0.4 via.
- **MOTOR_P/N:** 0.5 mm (8.4 mm each), with a 0.25 mm fan-out neck for the first 1.05 mm out of U3's 0.25 mm pins at 0.5 mm pitch.
- GND stubs to the fan-out vias are 0.3 mm. GND is not in the Power class.

### I²C and touch

- I²C copper (tracks and vias) to the copper of RV1 pad T: SDA 3.96 mm, SCL 2.17 mm. Both meet the 1.85 mm minimum.
- Both I²C lines leave J1 on vias and run on B.Cu along the bottom edge, below the fader pads.
- Touch nets to I²C: TOUCH_ELEC 2.66 mm, TOUCH_SNS 3.53 mm, TOUCH_DRV 4.35 mm.
- Touch nets to the motor nets: ≥ 68 mm. The motor nets stay at the far end, at U3, C14 and M±.

## What I couldn't meet, or interpreted

- **Net names:** rev B has no PBUS or VM_P nets. Its input is `/VIN`, and In2.Cu is the **+5V** plane, which feeds the driver's VM. The zones were kept exactly as they are, so "In2 = VM_P plane" here means In2 = +5V.
- **Necks:** "necking only at pads" is read as necking in the fan-out within about 1 mm of a fine-pitch pad. That covers U3's 0.25 mm pins, where 0.5 mm can't fit.
- **Freerouting widths:** Freerouting used 0.15 mm on a few signal stubs into U1's TSSOP pins. These are signal nets, not Power class, and above the JLC 0.09 mm minimum. I left them.
- **Via count:** higher than TraceMaker's, because of one plane via per GND/+5V pad as required, and because Freerouting changes layer more often.
- **Length:** longer than TraceMaker's. VSENSE takes a 6 mm loop over R8/C9 to avoid a T-join. The I²C pair runs along the bottom edge to keep its distance from the touch pad.
- **Optimizer:** Freerouting's own optimizer did not run, because it counted two of my pre-routed connections as unrouted. `cleanup.py` does the clean-up instead.
- No test points were added. No tracks are on In1/In2.
