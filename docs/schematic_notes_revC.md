# E0001 rev C schematic capture notes (Schematics, 2026-10-19)

**Spec:** `docs/SPEC_revC.md` **v1.0**.

**Schematic:** `E0001_fader_driver.kicad_sch` (canonical), a single 450 × 350 mm sheet with **53 parts**.

**Generator:** `build/scripts/gen_sch.py`. **Edit the generator, not the .kicad_sch.** It uses the same UUID namespace as rev B, so unchanged parts (U1, U3, RV1, J1, R5–R10 …) keep their UUIDs and stay linked to the board.

**Rev B archive:** `archive/revB/` holds the sch, pcb, pro, dru, E0001.kicad_sym, generator scripts and a README. Rev B fab outputs stay in `fab/E0001_revB/`.

**Checks**, re-run after every change:
- `build/scripts/render_check.sh`: **ERC (`--severity-all`) is 0 errors, 0 warnings.**
  - The connectivity report lists unlabelled or single-pin nets. Only the deliberate R10 → LED wire (`Net-(D3-A)`) is left.
  - No-connect flags: U4 ~FLT and AUXOFF, the NC pins of D6/D7.
- `build/scripts/check_fp.py`: **all 53 footprints exist, and pin numbers match pad numbers for all 17 symbol/footprint pairs.**
- **Net-by-net netlist audit done.**
- **BOM:** the MPN, supplier PN and DNP fields come from Parts' `bom/E0001_revC_bom.csv`, with the spec §11 table as fallback.
  - All 53 BOM references match it with 0 mismatches, and no supplier PN is blank. DNP: C14 only.
  - JP1–JP3 are in Parts' BOM as PCB-only lines (bare pads), and `in_bom = no` in the schematic.
- **No test points** (owner rule).

## Circuit as captured (per SPEC_revC)
- **J1:** 1 PBUS_IN, 2 SCL, 3 SDA, 4 GND, MP GND.
  - SCL/SDA: PESD5V0L1UL (D4/D5) at J1, then 0 Ω (R19/R20) to PB6/PB7.
  - No pull-ups.
- **U4 TPS259470ARPWR** (auto-retry):
  - IN = PBUS_IN with C18 4.7 µF 25 V + C17 100 nF.
  - EN/UVLO: R11 1 M / R12 330 k (4.84 V rising). OVLO: R13 1 M / R14 137 k (9.96 V).
  - DVDT C16 1.8 nF, ITIMER C15 4.7 nF, ILM R15 5.23 k.
  - ILM monitor: R16 10 k + C19 1 nF → PA2.
  - FLT and AUXOFF unconnected. OUT = **VM_P**.
- **VM_P:**
  - Bulk 4 × 10 µF 25 V (C1/C11/C12/C20), D1 SMF9.0A (D_SOD-123F, same footprint as E0003).
  - DRV8210 VM with C13. PBUS sense R8 100 k / R9 30.1 k + C9 → PA4.
  - R2 10 Ω → LDO_IN (C2 4.7 µF) → **U2 MCP1703AT-3302E/MB (SOT-89)** → +3V3 (C5 4.7 µF, C3 1 µF).
- **U3 DRV8210:** VM = VM_P, **VCC = +3V3** (C10). IN1/IN2/nSLEEP on PA6/PA7/PA8. OUT1/OUT2 → MOTOR_N/P, as rev B. C14 10 nF DNP.
- **RV1:** track top (pin 3) → **+3V3**; bottom and frame → GND. Wiper R7 1 k / C7 → PA3. Touch: D2, R5 4.7 k (RK73H1ETTP4701F) → PA0, R6 1 M from PA1.
- **U1 pin map** (SPEC §5):
  - Pins 1/20 PB7/PB6 = I2C1, 2 PC14 = ADDR2, 3 PC15 = ADDR1, 6 NRST (C6).
  - 7 PA0 TOUCH_SNS, 8 PA1 TOUCH_DRV, 9 PA2 ILM, 10 PA3 FADER_POS, 11 PA4 VSENSE, 12 PA5 LED.
  - 13–15 PA6/PA7/PA8 motor, **16 PA9 UART_TX, 17 PA10 UART_RX**, 18 PA13 ADDR0, **19 PA14-BOOT0** (R17 10 k pull-down).
  - JP1–JP3 (ADDR0–2 → GND, bottom).
- **J2 (Würth 61300611021, 1 × 6 2.54 mm R/A):** 1 GND, 2 3V3, 3 RX (PA10), 4 TX (PA9), 5 B0, 6 RST.
  - Pin 5: R18 1 k → BOOT0.
  - Pin 6: D6 BAT54W, anode at NRST and cathode at the header, so the adapter can only pull NRST low.
  - **Pin 2 → D7 BAT54W → LDO_IN** (see the change below).

## Change vs. SPEC Q5 (approved by Manager 2026-10-19)
**J2 pin 2 feeds the LDO input, not +3V3.**
- **Why:** the MCP1703A abs max (DS20005122B) is "all inputs and outputs (VSS − 0.3 V) to (VIN + 0.3 V)". With the adapter on +3V3 and no PBUS, VOUT ≈ 3.0 V and VIN ≈ 0 V, so reverse current would flow through the LDO.
- **Now:** adapter 3.3 V → D7 → LDO_IN (≈ 3.0 V) → +3V3 ≈ 2.9 V (STM32C051 runs from 2.0 V), so VOUT < VIN always.
- **With PBUS present:** LDO_IN ≈ VM_P > 3.3 V and D7 blocks.
- **Back-feed:** the adapter supply also reaches VM_P through R2 (≈ 3 V). U4 blocks it towards PBUS_IN (reverse blocking), and the DRV8210 stays asleep (nSLEEP low from the MCU / pull-down).

## SPEC §12 checks
| # | Result |
|---|---|
| 1 | **Pins confirmed from ST open pin data `STM32C051F6Px.xml`:** pin 16 = PA9 (USART1_TX) / PA11, pin 17 = PA10 (USART1_RX) / PA12, pin 19 = PA14-BOOT0 / PA15, pins 20/1 = PB6/PB7 I2C1. Even if the C0 bootloader uses the "remapped PA11/PA12" option, it lands on the same physical pins 16/17. **AN2606 Rev 70 itself couldn't be read:** st.com is unreachable from this machine. Activation pattern and the I2C address 0x63 are **unverified** and on the pre-order checklist (Manager). |
| 2 | RM0490 factory nBOOT_SEL: **unverified** (same reason); pre-order checklist. NRST and PA9/PA10/PB6/PB7 FT status: the I/O type in the pin data is plain "I/O"; FT is per the spec author's read. |
| 3 | **MCP1703A SOT-89 pinout:** 1 GND, 2 + tab VIN, 3 VOUT (datasheet Table 3-1). It matches the KiCad `MCP1703Ax-330xxMB` symbol and `SOT-89-3` footprint. V_OUT > V_IN is not allowed, which led to the J2 pin 2 change above. |
| 4 | RPW footprint and symbol reused from E0003 (`lib/E0001.pretty/TI_RPW0010A_VQFN-HR-10_2x2mm_P0.475mm`, `E0001:TPS259470L`). ILM loading (10 k + 1 nF) as in the spec. |
| 5 | PESD5V0L1UL capacitance vs the I²C budget: not re-checked (part kept from rev B/E0003). |
| 6 | SMF9.0A uses **D_SOD-123F**, the same as E0003. |
| 7 | ERC 0, footprint parity OK, no TP symbols. **Board parity:** the rev B `.kicad_pcb` still sits in the canonical place, so DRC parity fails until Router does the rev C layout. |

## Notes for Router
- **Removed vs. rev B:** Q1, R1, the old SMF5.0A D1 footprint (D1 is now the SMF9.0A on D_SOD-123F), the TC2030 J2 footprint and its NPTH holes, C8 (unused).
- **Added:** U4 + 8 passives, J2 1 × 6 R/A header (`PinHeader_1x06_P2.54mm_Horizontal`), D4–D7, R11–R20, C15–C20.
- **Nets:** the In2 plane changes from +5V to **VM_P**. **+5V no longer exists.**
- **I²C:** keep the rev B rule, ≥ 1.85 mm from the touch pad and no parallel run.
- **U4:** keep R15 (ILM) right at the pin.
- **Silkscreen:** "PBUS 6–9 V" at J1, "E0001 rev C", J2 pin names (GND 3V3 RX TX B0 RST), A0/A1/A2 at JP1–JP3.
