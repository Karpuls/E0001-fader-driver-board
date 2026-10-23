# Rev C hand-route experiment (not for fab)

On this branch, `E0001_fader_driver.kicad_pcb` is the rev C board (master `43d01a5`). All of its tracks and vias (411 items) were stripped and the board was routed again **without TraceMaker**, to compare against the shipped rev C routing. Placement, footprints, zones (In1 GND, In2 VM_P, F/B GND pours), outline, net classes, `.kicad_pro` and the JLC `.kicad_dru` are unchanged. Master `43d01a5` is still the board for fab.

## Method

These are the same scripts as the rev B run, copied to `build/hr/` and adapted to rev C.

1. `strip.py` removes all segments, arcs and vias at the s-expression level.
2. `preroute_c.py` is my own geometry code. It writes tracks into the board file:
   - **Motor loop:** U3 pins 2/3 neck out at 0.25 mm, then run 0.5 mm to C14 (4 mm from U3) and on to M+/M−.
   - **U3 supply:** VM (pin 1) goes to C13 and then a VM_P plane via. VCC (pin 8) goes to C10.
   - **U3 GND:** pin 4 runs into the exposed pad, which has two thermal vias.
   - **eFuse U4 power:**
     - PBUS_IN leaves the east end of bar 5 and runs to C17 and C18, then to the feed via.
     - VM_P leaves the west end of bar 6 and runs to C1, then to the plane via.
     - Both neck to 0.25 mm only between U4's pins, where the bars are 0.3 mm wide and 0.2 mm apart.
   - **PBUS_IN feed:** from J1 pin 1, a via, then B.Cu up the east edge and along the north edge to the U4 feed via, 0.5 mm all the way.
   - **Touch nets:**
     - TOUCH_ELEC runs from pad T to D2 and R5.
     - TOUCH_SNS runs from U1.7 through the C19/C6 gap to R6 and R5.
     - TOUCH_DRV runs from U1.8 to a via under U1, along B.Cu, to a via, then R6.
   - **Plane fan-out:** every SMD GND pad gets an In1 via (0.6/0.3). Every VM_P pad gets an In2 via (0.8/0.4), placed by the same clearance-checked search as before. U4.8, R15.2 and C17.2 in the crowded eFuse corner are tied by short tracks to C16.2's GND via.
3. pcbnew 10.0.6 exports a DSN, edited as before:
   - In1/In2 stay `power` layers, so no tracks go on the inner layers.
   - The F/B GND pours are removed from the DSN; KiCad refills them afterwards.
   - A 6.4 mm keepout circle around touch pad T enforces the I²C gap.
   - `via_at_smd off`, and +0.01 mm clearance margin.

   Freerouting 2.5.0 routed the remaining 69 nets in 8.4 s (`build/hr/fr/`).
4. `cleanup.py` is my 45° chain rebuilder plus right-angle chamfer. It now recomputes the chains after every rebuild; in the rev B version, stale segment indices could break a net. It rebuilt 44 chains.
5. `fixes_c.py` holds the hand edits, run through `fixes.py`. Each is clearance-checked by the script and then by KiCad DRC.
   - Where two tracks meet at a pad, they end at separate points inside the pad, so no T-join or right angle forms. This applies to PBUS_IN/VM_P at the eFuse and at C13.
   - +3V3, LDO_IN, J1_SDA, I2C_SDA, FADER_POS and EF_OVLO joins are redrawn at 45°.
   - LDO_IN ends on the U2 tab's anchor, because corners.py only treats a custom pad's anchor as the pad.

**Time:** about 10 minutes wall-clock from strip to DRC-clean (13:14 to 13:24), reusing the rev B scripts, plus writing this file. Freerouting took 8.4 s, cleanup about 5 s, and each DRC about 10 s.

## Result

| | Hand-route (this branch) | Shipped rev C (master `43d01a5`) |
|---|---|---|
| Method | own pre-route/fan-out + Freerouting 2.5.0 + own cleanup + hand fixes | as shipped |
| Tracks (segments) | 341 (252 F.Cu, 89 B.Cu, 0 inner) | 305 (236 F.Cu, 69 B.Cu) |
| Vias | 77 (36 GND, 8 VM_P, 2 PBUS_IN, 31 signal) | 106 (52 GND, 12 VM_P, 4 PBUS_IN, 38 signal) |
| Total track length | 716.4 mm | 731.2 mm |
| DRC (parity, all severities, refill) | 0 errors, 0 unconnected, 0 parity; 1 warning (J2 lib mismatch) | the same: 0 errors, 0 unconnected, 0 parity, the same 1 warning |
| tm_viapad | 0 | 0 |
| slots (after same-net pours) | 0 | 0 |
| corners.py | 0 acute, 0 right angle | 0 acute, 17 right angle |
| I²C to touch pad T (copper gap) | J1_SDA 2.25, J1_SCL 3.76, I2C_SDA 3.54, I2C_SCL 4.32 mm | J1_SDA 1.90, J1_SCL 3.76, I2C_SDA 4.17, I2C_SCL 4.58 mm |
| Touch nets to I²C | ELEC 3.32, SNS 3.43, DRV 3.97 mm | ELEC 3.00, SNS 3.13, DRV 3.73 mm |
| Touch nets to motor nets | ≥ 60.6 mm | ≥ 60.7 mm |
| PBUS_IN width | 0.5 mm (37.0 mm); 0.25 mm neck for 0.6 mm at U4's bar | 0.5 mm (40.0 mm), plus 2.7 mm at 0.3–0.4 mm |
| VM_P width | 0.5 mm (12.1 mm); 0.25 mm necks for 0.9 mm in total, at U4's bar and U3 pin 1 | 0.5 mm 2.9 mm, 0.4 mm 9.4 mm, 0.3 mm 2.5 mm |
| MOTOR_P/N | 0.5 mm (8.1 mm each); 0.25 mm neck for 1.05 mm at U3's pins | 0.5 mm 8.2 mm; 0.25–0.3 mm for 0.95 mm |

Both boards were measured with the same script, `build/hr/stats.py`. It counts straight segments (neither board has arcs) and gives copper-to-copper gaps.

The QC scripts ran with `/home/karpulis/.cache/e0002venv/bin/python -I` on copies in `build/qc/` (`qc.sh`). The master figures come from `git show 43d01a5:E0001_fader_driver.kicad_pcb`, checked in a copy with the same project files.

### Checks, verbatim (this branch)

- `kicad-cli pcb drc --schematic-parity --severity-all --refill-zones` (KiCad 10.0.6, in the worktree):
  - `Found 1 violations`, `Found 0 unconnected items`, `Found 0 schematic parity issues`.
  - The one item is `[lib_footprint_mismatch]: Footprint 'PinHeader_1x06_P2.54mm_Horizontal' does not match copy in library 'Connector_PinHeader_2.54mm'`, a warning on J2.
- `tm_viapad.py`: `vias on/under pads: 0 (gap < 0.15 mm, pads < 2.0 mm)`.
- `slots.py`: nothing after `--- after removing slots filled by same-net pours:`.
- `corners.py`: `Counter()`.

### Power and current

The eFuse limit is 0.54–0.73 A.
- Power tracks are 0.5 mm on 1 oz outer copper.
- The PBUS_IN feed uses two 0.8/0.4 vias.
- VM_P reaches the In2 plane through one 0.8/0.4 via at C1, right beside U4's output, plus one such via at every other VM_P pad: C11, C12, C20, C13, D1, R2, R8.
- That margin is ample for 0.73 A.
- The only narrow power copper is the 0.25 mm necks inside U4's and U3's pin fields, at most 1.05 mm long.

## What I couldn't meet, or interpreted

- **DRC 0/0/0:** errors, unconnected items and parity are all 0. One warning remains: J2's footprint differs from the stock library copy. The shipped master has exactly the same warning. Clearing it would mean changing J2's footprint, which the brief rules out, so I left it.
- **Necks:** "necking only at pads" is read as necks inside a fine-pitch pin field.
  - U4's bars are 0.3 mm wide and 0.2 mm apart, between pins 1 and 10 and pins 4 and 7, so a 0.5 mm track can't reach them.
  - U3's pins are 0.25 mm wide at 0.5 mm pitch.
- **Thin signal stubs:** Freerouting used 0.15 mm on a few signal stubs into U1/U4 pins. These are not Power class and are above the JLC 0.09 mm minimum.
- **Pads with two tracks:** a few pads take two tracks that end at separate points inside the pad: C17.1, C18.1, R11.1, R13.1, R13.2/R14.1, C1.1, C13.1, C5.1, C7.1, R6.2/R5.2 and D5/R20. This is what avoids T-joins on a 45° grid. corners.py and DRC accept it, but a reviewer may still read it as a junction at the pad.
- No test points were added. No tracks are on In1/In2.
