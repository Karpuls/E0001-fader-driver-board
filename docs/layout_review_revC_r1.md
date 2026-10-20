# E0001 rev C layout review, round 1 (Router, 2026-10-20)

Board: `E0001_fader_driver.kicad_pcb`, saved 2026-10-19 19:04 by the layout thread (sha256 prefix `4b738d3985be2c1d`). Reviewed on an independent copy (`qc/E0001-revC-r1`, in Router's home folder), zones refilled.
Spec: `docs/SPEC_revC.md` v1.1. Renders: `docs/review_revC_r1/`.

## Verdict: PASS (ready for fab outputs once the owner approves)

## Results
| Check | Result |
|---|---|
| `kicad-cli pcb drc --schematic-parity --severity-all --refill-zones`, JLC dru | **0 errors, 0 unconnected, 0 parity issues**; 1 warning (J2 `lib_footprint_mismatch`, waiver W1) |
| Same-net slivers (`slots.py`) | **0** |
| Vias on or under pads (`tm_viapad.py`, owner rule; rule also in the dru) | **0** |
| Test points (owner rule) | **0** |
| Outline / RV1 / layers | **Unchanged from rev B**: Edge.Cuts 66.5–173.5 × 91.5–108.5 (107 × 17 mm), RV1 at (100, 100); 4 layers with In1 GND and **In2 VM_P** (a single 1629 mm² pour) |
| J2 (1×6 R/A header) | Top side at y 104.45, pins pointing out past the **south edge**, in the MCU zone. Pin 1 (GND) is at the east end, accepted by Manager as option (a); every pin is labelled on the silk |
| Power paths (spec D2: ≤ 0.6 A including stall; eFuse limit 0.54–0.73 A) | **PBUS_IN** 0.5 mm on B.Cu and F.Cu with 4 vias, necking to 0.3–0.4 mm only at pads. **VM_P**: U4 OUT goes to the In2 plane through 12 vias in total, with 0.3–0.5 mm tracks. **MOTOR_P/N** 0.5 mm, necking to 0.25–0.3 mm at the WSON pads. All fine for 0.73 A |
| R15 (ILM) at U4 | 1.15 mm from U4's ILM pin, centre to centre |
| I²C vs the fader touch pad (RV1 "T") | I2C_SCL 4.58 mm, I2C_SDA 3.70 mm, J1_SCL 3.60 mm, **J1_SDA 1.90 mm** (rule ≥ 1.85 mm, see N1) |
| Touch nets vs I²C and motor | TOUCH_ELEC/SNS ≥ 3.13 mm from I²C, ≥ 60 mm from MOTOR_P/N |
| Geometry (`corners.py`) | **0 acute joins**; 1 right-angle T-join on free signal track (J1_SCL at 168.6, 107.75); the remaining right angles are at pads |
| Closest gaps, fine-pitch parts (`gaps.py`) | U1 0.112 mm (MOT_IN1 track to the R18 pad); U4 0.162 mm; U3 0.19 mm; U2 0.207 mm. All within the JLC rules |
| Silkscreen | "PBUS 6–9 V", "E0001 rev C", "J1: 1=PBUS 2=SCL 3=SDA 4=GND", J2 pin names (GND 3V3 RX TX B0 RST), "UART boot 3.3 V", A0/A1/A2 and "addr 0x30–0x37, open = 1" |

## Minor (no action needed)
- **N1:** J1_SDA passes 1.90 mm from the touch pad over about 6 mm as it leaves J1 pin 3. J1 is fixed next to the pad, so this exit run can't be avoided. It meets the ≥ 1.85 mm rule.
- **N2:** one right-angle T-join on J1_SCL. Cosmetic.
- **N3:** the custom JLC 0.09 mm clearance rule overrides the 0.15 mm net class, as on E0003. The tightest gap is 0.112 mm, which is legal for JLC.

## Waivers
- **W1:** J2 `PinHeader_1x06_P2.54mm_Horizontal` differs from the library copy because its silk outline was removed: the header body and pins overhang the south edge. The pins are labelled on the board silk instead.

## Next
Fab outputs are made only after the owner approves (Manager relays).
