# E0001 fader driver board, rev B: fabrication package

Source: `E0001_fader_driver.kicad_pcb` at git `10de656` (both layout QC rounds applied), sha256 prefix `0c8766c92d749d41`, KiCad 10.0.6.
Exported 2026-10-10 by Router. Rev A (`archive/revA/`) is not touched.

## Pre-export checks
- DRC (`--schematic-parity --severity-all`, JLC 4-layer `E0001_fader_driver.kicad_dru`): **0 violations, 0 unconnected, 0 parity issues.**
- ERC: 0 violations.
- Router QC:
  - Sliver check (`slots.py`): 0 same-net slots.
  - Corner check: 0 acute joins. The only 90° joins are perpendicular T-branches into trunks.
- I²C: ≥ 1.85 mm from the fader touch pad (RV1 "T"), with no parallel run (round-2 fix verified).

## Board
- 4 layers: F.Cu / In1.Cu (GND) / In2.Cu (+5V) / B.Cu. 107 × 17 mm. Thickness as for rev B: standard **1.6 mm** unless specified otherwise.
- Drills: 58 plated holes (48 × 0.30 vias, 2 × 0.40, 6 × 1.50 and 2 × 2.00 fader pins/tabs), 3 non-plated (0.99 mm TC2030 locating holes).

## Files
| Path | Content |
|---|---|
| `E0001_revB_gerbers_JLC.zip` | Upload this to JLC: 11 Gerbers, PTH and NPTH Excellon drills, and the job file |
| `gerbers/` | The same files, unzipped |
| `assembly/E0001_revB_CPL_JLC.csv` | Placement file for fitted parts (29). It includes RV1 (THT fader) and J1; leave those out if JLC assembles |
| `assembly/E0001_revB_pos_front.csv`, `_pos_back.csv`, `_pos_all.csv` | KiCad position files |
| `assembly/E0001_revB_assembly_top.pdf`, `_bottom.pdf` | Assembly drawings, with DNP crossed out (C14) |
| `E0001_revB_BOM.csv` | BOM (from Parts), including the fader and the JST connector, with owner-stock flags |
| `docs/E0001_revB_schematic.pdf` | Schematic |
| `3d/E0001_revB.step` | Board STEP with components |
| `reports/` | DRC, ERC, drill maps, gerber render check |

## Gerber render check
Rendered with pygerber (`reports/E0001_revB_gerber_render.png`):
- Copper: all 4 layers clean, with solid In1/In2 planes.
- Mask and paste: every pad opening present (checked on a macro-free export; pygerber doesn't draw RoundRect macros). Vias are tented. Bottom paste is empty, which is correct: the bottom side only has the solder jumpers and the TC2030 pads.
- Silk: readable, and the bottom silk is mirrored as it should be.

## Open before ordering PCBs
- **Fader hole pattern and pin orientation:** these come from the ALPS RSA0N11M9A0J drawing and must be **verified on a sample of the clone fader** (Amazon B0H45B29YK) before ordering. See `lib/ALPS_RSA0N11M9A0J_notes.md`. The PCB holes (6 × 1.50 and 2 × 2.00 plated) must match the clone.
