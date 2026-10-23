# Rev C layout re-done with TraceMaker (experiment, not for fab)

On this branch, `E0001_fader_driver.kicad_pcb` starts from the rev C fab board (`43d01a5`). Everything was redone with TraceMaker: all 411 tracks and vias were stripped, then the board was **placed with `tracemaker-place`** and **routed with `tm_route.sh`**. Design-intent problems were fixed by hand afterwards.

Unchanged from rev C:
- the outline (107 × 17 mm);
- RV1 and its touch pad T, at the same position and rotation;
- J1 and J2;
- the zones (F/B GND, In1 GND, In2 VM_P);
- the net classes, `.kicad_pro`, `.kicad_dru` and schematic.

RV1 now carries `(locked yes)`. Master `43d01a5` is still the fab board.

**Round 2 (§6) supersedes the round 1 figures below for the current board.** Round 2 adds 45°-only tracks, a GND via per cap, C9/C19 back at U1 and the I²C rule in the project dru.

Scripts, logs and backups are in `build/tracemaker/` and `build/backup/` (gitignored).

## 1. Placement

### Commands and times

All runs used `ulimit -v 4800000` and `--seed 1`. Peak RSS stayed under 0.5 GB.

```
P=~/tools/TraceMaker/build/cpu-only/src/place/tracemaker-place
C="--route-check 3000000 --route-threads 2 --threads 2 --seed 1"
$P E0001_fader_driver.kicad_pcb -o placed_routable.kicad_pcb --mode routable $C --loop-time 900 --json routable.json   # 169.9 s  <- used
$P E0001_fader_driver.kicad_pcb -o placed_auto.kicad_pcb     --mode auto     $C                --json auto.json       #  21.8 s
$P E0001_fader_driver.kicad_pcb -o placed_scratch.kicad_pcb  --mode routable --scratch $C --loop-time 900 --json scratch.json  # 122.2 s
```

Three rounds were needed before a placement was usable:

1. **On the stripped board as it is** (`routable` 240.6 s, `auto` 60.7 s): **0 parts moved.**
   - The placer models a courtyard as the convex hull of all of a footprint's courtyard graphics. RV1 has two courtyard rectangles, one for the motor block and one for the terminal block. Their hull spans x 27–166, so all 43 top-side parts counted as overlapping RV1.
   - The route check (no `--soft-zones` in the placer) also saw the filled F/B GND pours as solid copper.
2. **On a placer-only proxy** (`make_proxy.py`) (`routable` 180.6 s, `auto` 21.7 s): all 50 movable parts moved. The proxy was made like this:
   - RV1's two courtyard rectangles became board-level keep-outs that block footprints only.
   - RV1's courtyard lines were removed.
   - The F.Cu/B.Cu GND pours were removed; In1 and In2 were kept.

   This round broke the design intent:
   - U3 went about 45 mm from the motor pins, to x≈118–126 beside U1. The placer weights power-like nets (the motor nets) at 0.1 against 1 for its three logic inputs.
   - In `routable`, U4 went to x≈100, far from J1.
3. **The proxy with U3 and U4 also locked at their rev C spots** (the closest legal positions to RV1's motor pins and to J1's PBUS pin). Everything else was free.

   | Candidate (round 3) | HPWL | Route check (proxy, of 111) |
   |---|---|---|
   | rev C input | 820.0 mm | 56 |
   | `auto` (refine) | 715.2 mm | 58 |
   | `routable --scratch` | 818.6 mm | 60 |
   | **`routable`** (winner: round-3 re-place) | **750.6 mm** | **60** |

   I used the `routable` winner, since `--scratch` was no better. `transfer.py` copied its footprints onto the real board. RV1, the zones and everything else were left as they were.

The route-check counts are relative only. Without the pours, even rev C (which routes fully) scores 56 of 111.

### Hand fixes after the placer (`moves.py`)

1. **Decoupling and filter caps the placer pulled away** were moved back beside their pins:
   - C13 (U3 VM) was 15.1 mm from U3.1, now 1.5 mm.
   - C6 (NRST) was 23.6 mm from U1.6, now 1.5 mm.
   - C7 (FADER_POS filter) is now 1.5 mm from U1.10.
   - R6 moved up 0.5 mm and C5 down 0.15 mm to make room.
2. **The eFuse support network was restored to its rev C arrangement round U4:** R11–R16, C15–C18 and C1, with R7 moved to its rev C spot to make room. Before this, C1 was 36.6 mm from U4's output.
   - In routing pass 1, the placer's packing round U4 left its 0.3 mm bar pads no escape.
   - Pass 1 ended with 3 starved GND thermals, 7 acute PBUS_IN joins and 2 same-net slots in that corner.
   - Rev C and the Freerouting re-route both route this arrangement cleanly.
3. **Silkscreen:** the placer packs parts with 0 mm courtyard clearance, so 27 `silk_overlap` warnings appeared. These were cleared by 0.25–0.6 mm nudges of D4, D5, D6 and C3, plus text moves:
   - "UART boot 3.3 V" moved to 124.6, 99.3, between U1 and U2.
   - "J1: 1=PBUS …" moved 6.5 mm west, clear of U2.
   - A0/A1/A2 moved beside JP1/JP2/JP3 at their new spots under U1, on B.Silkscreen.
   - "addr 0x30–0x37, open = 1" moved to 146, 97.6 (B.Silkscreen).
   - "E0001 rev C", "PBUS 6–9 V" and J2's pin labels stayed where they were, because their parts did not move.

### Before and after

Rev C placement: parts in two clusters, the motor loop (U3, C10–C14, C20, D1) at x 74–89 and the logic/eFuse block at x 121–153.

TraceMaker placement:
- **Motor loop:** unchanged in principle. U3 is locked; C13, C14 and C10 hug it; the VM bulk caps C20/C11/D1 sit at x 78–88, with C12 out at x 105.6.
- **LDO block:** U2, C2, C3, R2 and D7 moved about 12–19 mm west, into the free space under the fader body (x 107–116).
- **U1:** moved 2 mm south.
- **VSENSE divider:** R8, R9 and C9 moved to x 119–124, above J2.
- **ADDR jumpers:** JP1–JP3 turned 90° and went under U1 on B.Cu.
- **Touch parts:** R5 stays at x≈146 and D2 moved to x≈153, between U4's group and the touch pad.
- **J1 side:** the I²C parts (R19, R20, D4, D5) moved by less than 2 mm.
- **Unchanged (17):** C1, C15–C18, J1, J2, RV1, R7, R11–R16, U3 and U4.
- **Moved (36), as rev C → TraceMaker, displacement in mm:**

| Part | rev C (x, y / rot) | TraceMaker | Δ |
|---|---|---|---|
| C2 | 123.40, 95.00 / 90° | 112.57, 100.42 / 90° | 12.1 |
| C3 | 124.40, 97.80 / 0° | 107.70, 103.48 / −90° | 17.6 |
| C4 | 142.60, 101.00 / 0° | 140.95, 103.40 / −90° | 2.9 |
| C5 | 145.20, 102.30 / 0° | 142.15, 103.85 / −90° | 3.4 |
| C6 | 142.60, 99.67 / 0° | 141.45, 101.88 / 0° | 2.5 |
| C7 | 142.60, 97.08 / 0° | 141.00, 98.30 / 90° | 2.0 |
| C9 | 132.30, 96.00 / 0° | 122.87, 96.76 / 180° | 9.5 |
| C10 | 81.40, 98.20 / 90° | 80.43, 98.18 / 0° | 1.0 |
| C11 | 83.40, 94.40 / 90° | 86.86, 94.54 / 90° | 3.5 |
| C12 | 86.00, 94.40 / 90° | 105.61, 95.97 / 90° | 19.7 |
| C13 | 76.60, 98.30 / 180° | 77.40, 98.20 / 0° | 0.8 |
| C14 | 74.00, 100.00 / 90° | 74.29, 99.90 / 90° | 0.3 |
| C19 | 142.60, 98.38 / 0° | 139.49, 94.89 / 90° | 4.7 |
| C20 | 88.60, 94.40 / 90° | 79.47, 96.73 / 180° | 9.4 |
| D1 | 84.60, 105.40 / 180° | 79.70, 94.56 / 180° | 11.9 |
| D2 | 148.60, 100.95 / 90° | 153.02, 102.16 / −90° | 4.6 |
| D3 | 123.40, 99.20 / 0° | 133.77, 95.09 / −90° | 11.2 |
| D4 | 169.45, 107.65 / 0° | 168.55, 106.68 / −90° | 1.3 |
| D5 | 168.40, 105.60 / 0° | 170.36, 105.34 / 0° | 2.0 |
| D6 | 143.60, 104.30 / 180° | 116.20, 99.60 / 0° | 27.8 |
| D7 | 128.60, 98.70 / 0° | 114.91, 103.80 / 180° | 14.6 |
| JP1 (B) | 136.00, 106.60 / 0° | 133.77, 104.23 / −90° | 3.3 |
| JP2 (B) | 139.40, 106.60 / 0° | 139.49, 102.60 / 90° | 4.0 |
| JP3 (B) | 142.80, 106.60 / 0° | 139.49, 105.91 / −90° | 3.4 |
| R2 | 121.00, 93.00 / 0° | 110.94, 100.07 / −90° | 12.3 |
| R5 | 146.60, 100.40 / 180° | 146.15, 101.35 / 180° | 1.1 |
| R6 | 145.25, 98.70 / 0° | 140.96, 100.34 / −90° | 4.6 |
| R8 | 131.00, 93.30 / 90° | 119.48, 95.68 / 0° | 11.8 |
| R9 | 132.30, 94.90 / 0° | 119.59, 96.77 / 180° | 12.8 |
| R10 | 125.90, 99.20 / 180° | 133.77, 97.51 / 90° | 8.0 |
| R17 | 133.00, 101.55 / 90° | 134.67, 106.99 / 0° | 5.7 |
| R18 | 132.90, 98.00 / 90° | 133.25, 106.35 / −90° | 8.4 |
| R19 | 167.60, 107.75 / 180° | 166.73, 106.59 / −90° | 1.4 |
| R20 | 166.85, 105.80 / −90° | 168.04, 105.15 / 180° | 1.4 |
| U1 | 137.50, 100.00 / 180° | 136.63, 101.95 / 180° | 2.1 |
| U2 | 127.00, 94.60 / 180° | 110.94, 104.95 / −90° | 19.1 |

### Design intent: result

| Intent | Result |
|---|---|
| J2 at the south edge, pins out past the edge | Unchanged from rev C. The placer treats edge connectors as fixed. |
| J1 at an edge, reachable | Unchanged (east edge). |
| Decoupling next to IC pins | Cap pad to IC supply pin: C4 1.46, C5 2.66, C10 1.07, C13 1.54, C3 1.74, C2 2.50 (LDO in), C17 3.10, C18 4.42, C1 4.35, C15 1.06, C16 1.16 mm |
| U3 and its loop compact, near M+/M− | U3 is 8.5 mm from M+/M− (as rev C). C14 (snubber) is 3.8 mm from U3. The motor tracks are 8.4–9.2 mm per net. |
| eFuse U4 near J1's PBUS input | U4.5 is 21.3 mm from J1.1, as rev C. RV1's terminal block lies between them. |
| TOUCH_* away from motor and I²C | The touch nets are ≥ 61 mm from the motor nets and ≥ 3.0 mm from the I²C nets. |
| Silkscreen readable, not on pads | DRC: 0 `silk_overlap`, 0 `silk_over_copper` |

## 2. Routing

### Routing-only rules

`tm_route.sh` reads the `.kicad_dru` beside the board, and this experiment may only change the `.kicad_pcb`. So routing ran from a staging folder, `build/tracemaker/stage/`. It holds symlinks to the project files and a copy of the dru with two rules added:

```
(rule "I2C vs TOUCH_ELEC" (condition "(A.NetName == '/I2C_*' || A.NetName == '/J1_S*') && B.NetName == '/TOUCH_ELEC'") (constraint clearance (min 1.85mm)))
(rule "I2C vs TOUCH_SNS/DRV" (condition "(A.NetName == '/I2C_*' || A.NetName == '/J1_S*') && (B.NetName == '/TOUCH_SNS' || B.NetName == '/TOUCH_DRV')") (constraint clearance (min 0.5mm)))
```

The final DRC below uses the project's own, unmodified dru.

### Command and time

```
cd build/tracemaker/stage && ulimit -v 4800000 && TM_THREADS=1 TM_TIME=300 ~/tools/tm_route.sh E0001_fader_driver.kicad_pcb --fast-bends
```

| Pass | Placement | TraceMaker | Whole pipeline | Peak RSS | Result |
|---|---|---|---|---|---|
| 1 | placer + caps fix | 73/73 routed, 300.8 s | 660 s | 1.41 GB | 3 errors (starved thermals), 6 unconnected, 7 acute, 3 right angles, 2 slots, all at U4 |
| 2 | + eFuse group at its rev C spots | 73/73 routed, 263.0 s | 308 s | 1.37 GB | 0 errors, 5 unconnected, 1 `hole_to_hole` warning, 2 acute, 5 right angles, 0 slots |

The pass 2 output is committed as `6d2c1da` (routed). It has 211 tracks and 32 vias before the hand fixes.

No keep-outs were needed:
- `--no-tracks-on In1.Cu,In2.Cu` kept the planes whole. In1 GND and In2 VM_P each fill in one piece.
- B.Cu GND fills in one piece.
- The I²C rule kept I²C off the touch pad.

### Hand fixes after pass 2 (`hand.py`)

The fixes, all on F.Cu:

1. **U4 split pads:** pins 1, 4, 7 and 10 each have two pads. They are joined with 0.2 mm links, as in rev C. This closed 4 unconnected items.
2. **VM_P out of U4:**
   - TraceMaker used a 0.3 mm stub to a 0.5/0.3 mm via, east of the bar.
   - Now VM_P leaves the west end of bar 6 with a 0.25 mm neck inside the pin field, then runs 0.5 mm to C1's 0.8/0.4 mm In2 via.
3. **PBUS_IN into U4:**
   - TraceMaker used 0.15–0.17 mm for 2.9 mm.
   - Now it has a 0.25 mm neck only between U4's pins, then 0.5 mm to R13.1.
4. **Motor loop:**
   - TraceMaker ran MOTOR_P/N at 0.25 mm all the way from U3's pins to C14 (3.6 mm).
   - Now they neck only inside U3's 0.5 mm pin field, fan out at 45° and run 0.5 mm to C14.
5. **U3.1 VM:** TraceMaker used 0.25 mm to a 0.5/0.3 mm via. Now U3.1 goes direct to C13.1 (0.5 mm after a 0.25 mm neck) and on to C13's 0.8/0.4 mm In2 via.
6. **GND vias:** `tm_planevia` had placed two vias 0.3 mm apart (`hole_to_hole`). One was removed, and C17.2 now uses C16's via.
7. **Floating GND pocket:** the pocket south of U4 held only R14.2. It is tied to In1 with one 0.6/0.3 mm via at 149.44, 97.55.
   - `tm_islands` had tried 149.996, 97.940 and reverted it, because that spot is over a +3V3 B.Cu track.
   - The new spot keeps 0.18 mm from B.Cu copper and 0.4 mm from every pad.
8. **Corners:**
   - **EF_EN's acute join at R11.2** was re-routed: the last leg now enters R12.1 at 45°.
   - **The other joins** (LDO_IN at R2 (acute), +3V3 at U3.8, J1_SDA at R20.1, EF_OVLO at R13.2, PBUS_IN at R11.1 and C18.1) now end at separate points inside the pad. This is the same method the Freerouting re-route used.
   - **A redundant PBUS_IN stub at C18.1** was deleted.

### Final copper

- **Tracks:** 222 segments (198 F.Cu, 24 B.Cu, 0 inner, 0 arcs), 633.9 mm in total.
- **Vias:** 35. VM_P (8) and PBUS_IN (2) use 0.8/0.4 mm vias. The 18 signal vias and 6 of the 7 GND vias are 0.6/0.3 mm; one GND via is 0.5/0.3 mm.
- **Test points:** none.

## 3. Checks (verbatim, final board)

- `/home/karpulis/.backplane-bend/kicad/10.0.6/bin/kicad-cli pcb drc --schematic-parity --severity-all --refill-zones E0001_fader_driver.kicad_pcb`, in the worktree with the project's own dru:
  - `Found 1 violations`, `Found 0 unconnected items`, `Found 0 schematic parity issues`.
  - The one item is `[lib_footprint_mismatch]: Footprint 'PinHeader_1x06_P2.54mm_Horizontal' does not match copy in library 'Connector_PinHeader_2.54mm'`, a warning on J2. This is the known warning, and it is the same on master.
  - That includes 0 `courtyards_overlap`, 0 clearance and 0 silkscreen items.
- Router's QC, run on a copy in `build/qc/copy/` with `/home/karpulis/.cache/e0002venv/bin/python -I` and the scripts in `/home/karpulis/.backplane-bend/bots/b1791384657-1165/qc/`:
  - `tm_viapad.py`: `vias on/under pads: 0 (gap < 0.15 mm, pads < 2.0 mm)`.
  - `slots.py`: nothing after `--- after removing slots filled by same-net pours:`.
  - `corners.py`: `Counter()`, so 0 acute and 0 right-angle joins.

### I²C to touch pad T (copper gap, mm)

| Net | TraceMaker | rev C | Freerouting |
|---|---|---|---|
| J1_SCL | **1.92** | 3.76 | 3.76 |
| J1_SDA | 4.20 | 1.90 | 2.25 |
| I2C_SCL | 3.98 | 4.58 | 4.32 |
| I2C_SDA | 3.78 | 4.17 | 3.54 |

### Power widths (mm of track per width)

| Net | Widths |
|---|---|
| PBUS_IN | 0.5 mm for 24.3 mm; 0.25 mm for 1.45 mm |
| VM_P | 0.5 mm for 11.3 mm; 0.25 mm for 2.48 mm |
| MOTOR_P | 0.5 mm for 8.45 mm; 0.25 mm for 0.73 mm |
| MOTOR_N | 0.5 mm for 8.12 mm; 0.25 mm for 0.96 mm |

Every 0.25 mm segment is a neck in a fine-pitch pin field:
- **PBUS_IN and VM_P at U4:** most of those segments' length lies on U4's 2.4 mm bar pads, where they start. The exposed necks are about 0.25 mm (PBUS_IN) and 0.4 mm (VM_P).
- **VM_P, MOTOR_P and MOTOR_N at U3:** necks of up to 1 mm through the 0.5 mm-pitch WSON pins.

The eFuse limit is 0.54–0.73 A.

## 4. Comparison

All three boards were measured the same way:
- `stats.py` (copied from the Freerouting branch's `build/hr/stats.py`): straight segments, copper-to-copper gaps.
- `qc.sh` (Router's scripts on a copy).
- KiCad 10.0.6 DRC with `--schematic-parity --severity-all --refill-zones`.

| | **TraceMaker (this branch)** | Shipped rev C (`43d01a5`) | Freerouting re-route (`cd74685`) |
|---|---|---|---|
| Placement | tracemaker-place `routable` + hand fixes (36 parts moved) | hand | rev C (unchanged) |
| Routing | TraceMaker via tm_route.sh + hand fixes | hand | own pre-route + Freerouting 2.5.0 + cleanup |
| Machine time | placer 170 s (final round; about 14 min in all rounds), router 308 s (pass 2; 660 s for pass 1) | n/a | Freerouting 8.4 s, about 10 min in all |
| Tracks (segments) | **222** (198 F.Cu, 24 B.Cu) | 305 (236 F.Cu, 69 B.Cu) | 341 (252 F.Cu, 89 B.Cu) |
| Vias | **35** (8 VM_P, 7 GND, 2 PBUS_IN, 18 signal) | 106 (12 VM_P, 52 GND, 4 PBUS_IN, 38 signal) | 77 (8 VM_P, 36 GND, 2 PBUS_IN, 31 signal) |
| Total track length | **633.9 mm** | 731.2 mm | 716.4 mm |
| DRC (parity, all, refill) | 0 errors / 0 unconnected / 0 parity; 1 warning (J2 lib) | same | same |
| tm_viapad | 0 | 0 | 0 |
| slots (after same-net pours) | 0 | 0 | 0 |
| corners.py | 0 acute, 0 right | 0 acute, 17 right | 0 acute, 0 right |
| I²C to touch pad T, closest | 1.92 mm (J1_SCL) | 1.90 mm (J1_SDA) | 2.25 mm (J1_SDA) |
| Touch nets to I²C | ELEC 3.02, SNS 3.70, DRV 4.35 mm | ELEC 3.00, SNS 3.13, DRV 3.73 mm | ELEC 3.32, SNS 3.43, DRV 3.97 mm |
| Touch nets to motor nets | ≥ 61.2 mm | ≥ 60.7 mm | ≥ 60.6 mm |
| PBUS_IN width | 0.5 mm (24.3 mm); 0.25 mm neck for 1.45 mm, mostly on U4's bar | 0.5 mm (40.0 mm), plus 2.7 mm at 0.3–0.4 mm | 0.5 mm (37.0 mm); 0.25 mm neck for 0.6 mm |
| VM_P width | 0.5 mm (11.3 mm); 0.25 mm necks for 2.48 mm at U4's bar and U3.1 | 0.5 mm 2.9 mm, 0.4 mm 9.4 mm, 0.3 mm 2.5 mm | 0.5 mm (12.1 mm); 0.25 mm necks for 0.9 mm |
| MOTOR_P / MOTOR_N | 0.5 mm 8.45 / 8.12 mm; 0.25 mm necks for 0.73 / 0.96 mm | 0.5 mm 8.2 mm; 0.25–0.3 mm for 0.95 mm | 0.5 mm 8.1 mm; 0.25 mm neck for 1.05 mm |
| Placement HPWL (placer's measure) | 750.6 mm before hand fixes | 820.0 mm | 820.0 mm |

TraceMaker's counts are lower mainly for two reasons:
- **The F/B GND pours.** Its `--soft-zones` routing lets them serve the SMD GND pads directly, where rev C and the Freerouting re-route give almost every GND pad its own In1 via. GND vias: 7 against 52 and 36.
- **The tighter placement.** The 0.25 mm VM_P/MOTOR necks are slightly longer than the Freerouting re-route's, because U3's 0.5 mm-pitch pins need a longer fan-out before two 0.5 mm tracks fit side by side.

## 5. What I couldn't meet, or interpreted

- **The placer couldn't run on the real board.**
  - Because of RV1's two-rectangle courtyard (see §1), it could not move anything. It ran on a proxy in which RV1's courtyards are footprint keep-outs.
  - The proxy can't see the F/B pours, so its route check is only relative.
- **The placer alone did not keep the design intent.** U3 and U4 had to be locked at their rev C spots. Several decoupling caps, and then the whole eFuse support network, were put back by hand. So the eFuse corner and the motor driver are effectively rev C's placement; the TraceMaker placement is the rest of the board.
- **Two ADC filter caps stay farther from their pins than in rev C.** C9 (VSENSE, 100 nF) is 10.7 mm from U1.11 (rev C 3.0 mm) and C19 (ILM_ADC, 1 nF) is 4.3 mm from U1.9 (rev C 1.9 mm). They are RC filter caps rather than supply decoupling, so I left them where the placer put them. Both are on short Default-class tracks.
- **I²C to touch pad.** J1_SCL is at 1.92 mm, just above the 1.85 mm rule; this is the tightest margin on the board. The clearance rule lived only in the routing dru, so a later edit with the project's dru won't enforce it.
- **Same pad, separate points.** Six joins avoid T-junctions or right angles by ending two tracks at separate points inside one pad: LDO_IN at R2.2, +3V3 at U3.8, J1_SDA at R20.1, EF_OVLO at R13.2, and PBUS_IN at R11.1 and C18.1. corners.py and DRC accept this, but a reviewer may read them as junctions at the pad. The Freerouting re-route does the same.
- **DRC warning.** One warning remains: J2's footprint differs from the stock library copy. Master has the same warning. Clearing it would mean changing J2's footprint.
- **RV1 lock.** RV1 is now `(locked yes)` in the board file; it was unlocked on rev C. Its position and rotation are unchanged.

## 6. Round 2: 45° tracks, GND vias, filter caps, I²C rule in the dru

This round follows the owner's review of round 1 (`284df5d`). The round 1 placement was kept, then all tracks and vias were stripped and the board was routed again with `tm_route.sh`. The pipeline now runs Router's 45° fix-up, `qc/tm_octil.py` (`TM_OCTIL=1`); TraceMaker itself is unchanged.

### Changes before routing

1. **Filter caps back at U1** (`moves2.py`):
   - C9 (VSENSE) is at 132.2, 98.4 / 270°, 1.92 mm from U1.11 (round 1: 10.66 mm).
   - The VSENSE divider sits beside it: R9 at 131.1, 98.4 and R8 at 131.1, 96.5, both 270°.
   - C19 (ILM_ADC) is at 141.55, 99.85, 1.59 mm from U1.9 (round 1: 4.31 mm).
   - C7 (FADER_POS) moved beside C19, to 141.55, 98.85, 1.59 mm from U1.10.
   - R6 moved 2.5 mm east, to 143.5, 100.6, so that U1.9 has a way out.
   - "UART boot 3.3 V" moved 0.7 mm west.
   - VSENSE track length is now **3.86 mm**. It was about 21 mm in round 1 and is 6.75 mm on rev C, measured the same way. It is shorter than rev C because the divider now sits right at U1.11.
2. **GND return** (`gndfan.py`): every capacitor's GND pad (18 caps) got its own locked 0.6/0.3 mm via to In1 before routing, so TraceMaker routed round them. Each via:
   - sits on a 0.3 mm stub at a multiple of 45°;
   - keeps at least 0.15 mm from every pad, at least 0.75 mm from other vias, and the 0.3 mm edge clearance.

   The search took the shortest such site, preferring the side away from the cap's other pad. C19's via was forced east, to keep the U1.7/U1.8 → R6 corridor free.

   | Cap | Via | Stub |
   |---|---|---|
   | C1 | 141.20, 94.50 | 0.95 mm |
   | C2 | 112.57, 98.70 | 0.95 mm |
   | C3 | 107.70, 104.71 | 0.75 mm |
   | C4 | 140.95, 104.63 | 0.75 mm |
   | C5 | 142.15, 105.53 | 0.90 mm |
   | C6 | 142.68, 101.88 | 0.75 mm |
   | C7 | 142.78, 98.85 | 0.75 mm |
   | C9 | 132.20, 99.63 | 0.75 mm |
   | C10 | 81.66, 98.18 | 0.75 mm |
   | C11 | 86.86, 92.59 | 1.00 mm |
   | C12 | 105.61, 94.07 | 0.95 mm |
   | C13 | 78.63, 98.20 | 0.75 mm |
   | C15 | 144.78, 93.06 | 0.90 mm |
   | C16 | 151.22, 92.52 | 0.80 mm |
   | C17 | 152.76, 92.21 | 1.85 mm |
   | C18 | 151.99, 92.31 | 1.15 mm |
   | C19 | 143.43, 99.85 | 1.40 mm |
   | C20 | 77.57, 96.73 | 0.95 mm |

3. **I²C rule in the project dru.** `E0001_fader_driver.kicad_dru` now contains:
   ```
   (rule "I2C vs TOUCH_ELEC" (condition "(A.NetName == '/I2C_*' || A.NetName == '/J1_S*') && B.NetName == '/TOUCH_ELEC'") (constraint clearance (min 1.85mm)))
   (rule "I2C vs TOUCH_SNS/DRV" (condition "(A.NetName == '/I2C_*' || A.NetName == '/J1_S*') && (B.NetName == '/TOUCH_SNS' || B.NetName == '/TOUCH_DRV')") (constraint clearance (min 0.5mm)))
   ```
   - **KiCad applies it.** Raised to 2.0 mm on a scratch copy of the round 1 board, it reports `Clearance violation (rule 'I2C vs TOUCH_ELEC' clearance 2.0000 mm; actual 1.9153 mm)` between pad T and J1_SCL.
   - **Routing aimed higher.** The router ran from `build/tracemaker/stage2/`, whose copy of the dru asks for 2.1 mm, to get margin over the 1.85 mm rule.

### Route

```
cd build/tracemaker/stage2 && ulimit -v 4800000 && TM_THREADS=1 TM_TIME=300 ~/tools/tm_route.sh E0001_fader_driver.kicad_pcb --fast-bends
```

- **TraceMaker:** routed 76/76 connections in 187.4 s; the whole pipeline took 224 s and peaked at 1.41 GB.
- **`tm_octil`:** `243 tracks, 34 off-angle (> 0.05 deg), 9 sharp joints (< 90.5 deg) before` and `fixed 43 (30 dog-leg, 1 drop, 9 pad-centre split, 3 slide), left 0`.
- **`tm_planevia`:** added 1 GND via (D4.2). No `hole_to_hole` warnings this time.
- **Still open after the pipeline:** 4 unconnected items (U4's split pads), 1 acute join (ILM_ADC at U1.9), and power necks to fix. This state is committed as `13f96c5`.

### Hand fixes (`hand2.py`)

All fixes are at multiples of 45°.

1. **U4 split pads.** Pins 1, 4, 7 and 10 each have two pads. Each pair is joined by one horizontal 0.2 mm link from the small pad's centre into the tall neighbouring pad, at 0°.
2. **VM_P out of U4.** As in round 1, VM_P leaves the west end of bar 6 with a 0.25 mm neck in the pin field, then runs 0.5 mm to C1's 0.8/0.4 mm In2 via. TraceMaker's 0.3 mm stub and its 0.5/0.3 mm via were removed.
3. **PBUS_IN out of U4.** A 0.25 mm neck runs to x 149.85, then 0.5 mm at 45° to R13.1. This replaces 1.26 mm at 0.28 mm and 1.25 mm at 0.3 mm. It keeps 0.16 mm from the GND via at 150.72, 94.92.
4. **Motor loop.** As in round 1, MOTOR_P/N neck only in U3's pin field, then run 0.5 mm to C14. This replaces 0.25 mm all the way, 3.6 mm per net.
5. **U3.1 VM.** As in round 1, U3.1 goes direct to C13.1 (0.25 mm neck, then 0.5 mm), with the 0.5/0.3 mm via removed.
6. **ILM_ADC at U1.9.** Duplicate overlapping segments there made an acute T. They became one entry and one exit, ending at separate points in the pad.
7. **C13.1.** The new VM_P leg ends inside the pad, 0.1 mm off the existing leg's end, so there is no right angle.

`tm_octil.py` ran again on the result, under the project name: `281 tracks, 0 off-angle (> 0.05 deg), 0 sharp joints (< 90.5 deg) before`, and it changed nothing.

### Angles

The check is Python over every `(segment` start/end, skipping zero-length segments, flagging anything more than 0.5° off a multiple of 45° (`build/tracemaker/scripts/angles.py`).

| Board | Segments | Off-angle | Off-angle length |
|---|---|---|---|
| Round 1 (`284df5d`) | 222 | **37** | 18.20 mm |
| **Round 2 (this commit)** | 281 | **0** | 0 mm |
| rev C (`43d01a5`) | 305 | 42 | 30.26 mm |
| Freerouting (`cd74685`) | 341 | 1 | 1.02 mm |

### Results, round 2

| | Round 2 | Round 1 |
|---|---|---|
| Tracks / vias / length | **281 / 48 / 626.9 mm** (256 F.Cu, 25 B.Cu, 0 inner) | 222 / 35 / 633.9 mm |
| GND vias | **22** (18 cap fan-out, 4 from the router) | 7 |
| Vias by net | VM_P 8, GND 22, PBUS_IN 2, signal 16 | VM_P 8, GND 7, PBUS_IN 2, signal 18 |
| C9 / C19 to their U1 pin | **1.92 / 1.59 mm** | 10.66 / 4.31 mm |
| VSENSE track | 3.86 mm | about 21 mm |
| I²C to touch pad T (J1_SCL / J1_SDA / I2C_SCL / I2C_SDA) | **2.15** / 4.20 / 3.98 / 3.78 mm | 1.92 / 4.20 / 3.98 / 3.78 mm |
| Touch nets to I²C | ELEC 3.25, SNS 3.57, DRV 4.29 mm | ELEC 3.02, SNS 3.70, DRV 4.35 mm |
| Touch nets to motor | ≥ 61.2 mm | ≥ 61.2 mm |
| PBUS_IN | 0.5 mm × 25.4 mm; 0.25 mm × 1.45 mm (neck, mostly on U4's bar) | 0.5 mm × 24.3 mm; 0.25 mm × 1.45 mm |
| VM_P | 0.5 mm × 11.7 mm; 0.25 mm × 2.48 mm (necks at U4's bar and U3.1) | 0.5 mm × 11.3 mm; 0.25 mm × 2.48 mm |
| MOTOR_P / N | 0.5 mm × 8.45 / 8.12 mm; 0.25 mm × 0.73 / 0.96 mm (U3 pin field) | same |
| Off-angle segments | **0** | 37 (18.2 mm) |

Every 0.25 mm power segment is a neck in a fine-pitch pin field (U4's 0.3 mm bars, U3's 0.5 mm-pitch WSON pins). Pours: In1 GND, In2 VM_P and B.Cu GND each fill in one piece. F.Cu GND has the main pour plus four small pockets, all connected (0 unconnected). No test points.

### Checks, verbatim (round 2 final board)

- `/home/karpulis/.backplane-bend/kicad/10.0.6/bin/kicad-cli pcb drc --schematic-parity --severity-all --refill-zones E0001_fader_driver.kicad_pcb`, in the worktree, with the project dru now including the I²C rules:
  - `Found 1 violations`, `Found 0 unconnected items`, `Found 0 schematic parity issues`.
  - The one item is `[lib_footprint_mismatch]: Footprint 'PinHeader_1x06_P2.54mm_Horizontal' does not match copy in library 'Connector_PinHeader_2.54mm'`, the known J2 warning.
  - That includes no courtyard overlaps, clearance or silkscreen items.
- Router's QC on a copy, with `/home/karpulis/.cache/e0002venv/bin/python -I`:
  - `tm_viapad.py`: `vias on/under pads: 0 (gap < 0.15 mm, pads < 2.0 mm)`.
  - `slots.py`: nothing after `--- after removing slots filled by same-net pours:`.
  - `corners.py`: `Counter()`.
- `angles.py`: `segments 281, off-angle 0, length 0.00 mm`.

### Comparison (all measured the same way)

| | **TraceMaker round 2** | TraceMaker round 1 | rev C `43d01a5` | Freerouting `cd74685` |
|---|---|---|---|---|
| Tracks | 281 | 222 | 305 | 341 |
| Vias (GND) | 48 (22) | 35 (7) | 106 (52) | 77 (36) |
| Length | 626.9 mm | 633.9 mm | 731.2 mm | 716.4 mm |
| Off-angle segments | **0** | 37 | 42 | 1 |
| corners.py | 0 | 0 | 17 right | 0 |
| Closest I²C to pad T | 2.15 mm | 1.92 mm | 1.90 mm | 2.25 mm |
| DRC | 0/0/0, J2 warning | same | same | same |

### Still open, or interpreted (round 2)

- **VSENSE is shorter than asked.** The review asked for about the rev C length (7–8 mm). It is 3.86 mm, because R8/R9 now sit right at U1.11. Shorter is better for this filter node, so I left it.
- **Same pad, separate points.** As in round 1, some joins end two tracks at separate points inside one pad instead of meeting at a corner: ILM_ADC at U1.9, VM_P at C13.1, and U4's EF_EN and FLT links. `tm_octil` also split 9 sharp joints at pad centres. corners.py and DRC accept all of these.
- **The ILM_ADC route** from U1.9 runs west under U1's body, between the pin ends and the package, then north-east to R16. This is legal: 0.22 mm from U1.10's pad, all at 45°. A hand route might prefer the east side.
- **The routing dru** in `build/tracemaker/stage2/` used 2.1 mm for the I²C rule. The project dru enforces 1.85 mm, and the board meets it with 0.30 mm to spare.
