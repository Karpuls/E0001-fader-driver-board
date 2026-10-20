# E0001 fader driver board, rev C: fabrication package

Source: `E0001_fader_driver.kicad_pcb`, sha256 prefix `4b738d3985be2c1d`, KiCad 10.0.6. Exported 2026-10-20 by Router.
Layout review: `docs/layout_review_revC_r1.md` (**PASS**). The owner approved fab outputs (via Manager, 2026-10-20).
Spec: `docs/SPEC_revC.md` v1.1. Rev B is obsolete (spec §1) and is kept in `fab/E0001_revB/` for reference only.

## Board
- **4 layers, 1.6 mm finished.**
  - F.Cu: parts and signals.
  - In1.Cu: solid GND.
  - In2.Cu: **VM_P** plane (protected PBUS).
  - B.Cu: signals and PBUS feed.
- **No custom stackup** (no impedance-controlled nets). Use JLC's default 4-layer stackup: 1 oz outer, 0.5 oz inner.
- 107 × 17 mm, same outline and fader position as rev B.
- **Vias are tented** (covered by solder mask on both sides).
- Minimum track 0.2 mm (0.15 mm only at fine-pitch pad necks). Tightest copper gap 0.112 mm (JLC rules: 0.09 mm).
- Vias 0.6/0.3 mm. **No vias on or under pads** (owner rule; there is a DRC rule for it).
- Drills, plated only (120): 101 × 0.30 (vias), 5 × 0.40, 6 × 1.00 (J2 header), 6 × 1.50 and 2 × 2.00 (fader pins and tabs). **No non-plated holes**; the Tag-Connect holes are gone.
- Board checks: DRC 0 errors, 0 unconnected, 0 parity issues. ERC 0. The one DRC warning is J2 `lib_footprint_mismatch`: the stock header's silk outline was removed because the header overhangs the south edge (waiver W1).

## Files
| Path | Content |
|---|---|
| `E0001_revC_gerbers_JLC.zip` | **Upload this to JLC.** It holds 11 Gerbers (F/In1/In2/B Cu, F/B Mask, F/B Paste, F/B Silk, Edge.Cuts), the PTH Excellon drill, an empty NPTH drill file (the board has no non-plated holes) and the job file |
| `gerbers/` | The same files, unzipped |
| `assembly/E0001_revC_CPL_JLC.csv` | Placement file in JLC column format: 49 fitted parts, with DNP parts excluded. It includes RV1 (THT fader), J1 and J2. Leave those out if JLC assembles |
| `assembly/E0001_revC_pos_front.csv`, `_pos_back.csv`, `_pos_all.csv` | KiCad position files, including DNP parts |
| `assembly/E0001_revC_assembly_top.pdf`, `_bottom.pdf` | Assembly drawings. The bottom view is mirrored and DNP parts are crossed out |
| `assembly/E0001_revC_DNP.txt` | DNP list: **C14** |
| `docs/E0001_revC_schematic.pdf` | Schematic (rev C) |
| `3d/E0001_revC.step` | Board STEP with components |
| `reports/` | DRC (`.rpt` and `.json`), ERC, drill map, the Gerber render check (`E0001_revC_gerber_render.png`) and the mask and paste render (`E0001_revC_mask_paste_render.png`) |
| `E0001_revC_BOM.csv` | BOM, owned by Parts (not generated here) |

## JLC order settings
- 4 layers; **1.6 mm**; default stackup; 1 oz outer, 0.5 oz inner.
- Via covering: **tented**. Any mask colour.
- Remove the order number, or specify its location.
- **J2** (1×6 2.54 mm right-angle header) sits on the top side with its pins pointing out past the south edge. Pin 1 (GND) is at the **east** end (owner-approved); every pin is labelled on the silk (GND 3V3 RX TX B0 RST).
- The bottom side has only the JP1–JP3 address solder jumpers and the THT pins, so there's no bottom paste.

## Gerber render check
Rendered with pygerber 2.4.3:
- **Copper:** all 4 layers render. In1 is solid GND and In2 is the VM_P plane.
- **Mask and paste:** these were rendered from a macro-free export, because pygerber doesn't draw RoundRect macros. Every pad opening is present, and the vias are tented.
- **Silk:** the top silk has "PBUS 6–9 V", "E0001 rev C", the J1 pinout and the J2 pin names. The bottom silk has the A0–A2 jumper notes and is mirrored.

## Open before ordering
- **Bootloader:** someone with st.com access must confirm the STM32C051 bootloader details. That means the STM32C051xx table in AN2606 Rev 70 and the RM0490 factory default of nBOOT_SEL (spec §6.1/§12). J2's UART bootloader access depends on them.
