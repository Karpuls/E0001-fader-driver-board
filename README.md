# E0001 – Motorized fader driver board

Controller board for an ALPS **RSA0N11M9A0J**-compatible motorized, touch-sensitive 100 mm fader
(Amazon.de B0H45B29YK clone). The board mounts under the fader, soldered to its pins.

- **Rev B (current):** STM32C051F6P6, DRV8210P H-bridge (motor from 5 V), MCP1703A 3.3 V LDO,
  capacitive touch on the fader lever, position from the 10k linear track, 4-layer, 107 × 17 mm.
- **Interface:** JST GH 4-pin horizontal, Pixhawk/Dronecode I2C pinout (1 = +5 V, 2 = SCL, 3 = SDA, 4 = GND).
  I2C pull-ups belong on the host. Address via 3 solder jumpers (bottom side), SWD via Tag-Connect TC2030-NL pads (bottom).
- Rev A (2-layer, STM32G031) is kept in `archive/revA/`.

## Layout
| Path | Content |
|---|---|
| `E0001_fader_driver.kicad_pro/.kicad_sch/.kicad_pcb` | KiCad 10 project |
| `lib/` | Fader symbol/footprint/3D model + notes, STM32C051F6Px symbol |
| `bom/E0001_revB_digikey_bom.csv` | BOM (DigiKey LV part numbers, excl. fader and JST connector) |
| `mech/` | Board + fader assembly STEP and renders |
| `build/scripts/` | Generators: schematic, placement, pre-routes, Freerouting pipeline, refs, BOM (`run_all.sh`) |

## Open points
Verify the clone fader's hole pattern and pin orientation on a sample before ordering PCBs (see `lib/ALPS_RSA0N11M9A0J_notes.md`).
The ALPS 3D model in `lib/3dmodels` is ALPS CAD data; check ALPS terms before making this repository public.
