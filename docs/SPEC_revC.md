# E0001 rev C — Motorized fader driver board: Hardware Requirements Spec

| | |
|---|---|
| Status | **v1.1 — FROZEN for hardware** (owner, 2026-10-18: all recommendations accepted; v1.1 Manager edit 2026-10-19). §14 lists the decisions Q1–Q14; there are no open questions. Changes need an owner decision and a version bump. §12 lists the checks for schematic capture. No KiCad files are changed by this document. |
| Date | 2026-10-18 (v0.1, v1.0); 2026-10-19 (v1.1) |
| Scope | **PCB only.** Enclosure and firmware are out of scope. §10 lists only the firmware rules that the hardware depends on. |
| Input requirement | **E0003 SPEC §6 "Peripheral bus spec (v2)"**, frozen with E0003 v1.0 (`../E0003 - ESP32 control box mainboard/docs/SPEC.md`). Host = E0003, 4 × E0001 rev C per box on mux channels 0–3. |
| Baseline | **Rev B** (git `10de656`, `fab/E0001_revB/`): STM32C051F6P6, DRV8210P, MCP1703A, 5 V input, JST-GH 4-pin, Tag-Connect SWD, 4-layer, 107 × 17 mm. **Rev B is obsolete: it will not be used or produced** (E0003 §6.1). |
| Rule | **Keep everything from rev B unless the new supply or an owner requirement forces a change.** Every change is listed in §1. |
| Build | 4-layer, DigiKey BOM, hand assembly with a stencil. **No test points** (owner rule 2026-10-16, all boards). |
| Parts policy | Cross-project common parts (`../E0003 - ESP32 control box mainboard/bom/common_parts_across_projects.md`) are the defaults. **Full BOM; owner stock is only a flag** (§11). |

### Revision history
| Rev | Change |
|---|---|
| v0.1 | First draft from the owner requirements of 2026-10-18 (PBUS v2 input, supply marking, UART bootloader header instead of Tag-Connect, no test points, R5/J1 sourcing, BOM policy) |
| **v1.0** | **Frozen (2026-10-18).** The owner accepted every recommendation ("go with recommendations"). Q1–Q14 are moved to §14 "Decided by the owner". "Proposed" markers are removed, and the BOM lists STM32C051F8P6 as the approved alternate for U1. The AN2606 STM32C051 bootloader-pin check stays in §12 as a schematic-capture item. |
| **v1.1** | Manager edit:<br>(1) **J2 pin 2 "3V3" now feeds through the BAT54W into the MCP1703A input (net LDO_IN, after R2), not into +3V3.** MCP1703A pins must stay ≤ V_IN + 0.3 V, so +3V3 must not be back-fed. With only a programmer attached the board runs at ≈ 2.9 V (§4.1, §4.5, §6.3, Q5).<br>(2) **The C051 bootloader pins are confirmed from ST pin data** (`STM32C051F6Px.xml`): pin 16 = PA9 (bonded with PA11), pin 17 = PA10 (bonded with PA12), pin 19 = PA14-BOOT0.<br>(3) **Still to confirm by someone with st.com access:** the STM32C051xx table in AN2606 Rev 70 and the RM0490 factory default of nBOOT_SEL (§6.1, §12). |

---

## 1. Changes from rev B (summary)

| # | Area | Rev B | Rev C | Why |
|---|---|---|---|---|
| C1 | Supply input | +5 V on J1 pin 1 | **PBUS 6.0–8.8 V** (operate 5.5–9.0 V, survive 11 V) on the same pin | Owner req. 1, E0003 §6 |
| C2 | Input protection | AO3401A P-FET (V_GS ±12 V) + R1, SMF5.0A on +5 V | **TPS259470ARPWR eFuse** (U4): reverse polarity to −15 V, OVLO, 0.54–0.73 A current limit, reverse-current blocking, dVdt. **SMF9.0A** on the protected rail. Q1, R1 and SMF5.0A removed. | Owner req. 1; E0003 §6.3/§6.4; common parts |
| C3 | Motor supply | DRV8210 VM from +5 V | **VM from the protected PBUS rail (VM_P)**; firmware PWM duty limit + measured current keep the board ≤ 0.6 A | DRV8210 VM ≤ 11 V; §6.3 0.6 A cap |
| C4 | DRV8210 logic supply | VCC from +5 V | **VCC from +3V3** | VCC abs max 5.75 V; PBUS would destroy it |
| C5 | 3V3 regulator | MCP1703A SOT-23 from +5 V | MCP1703A from VM_P (16 V input); **SOT-89 package** (Q7) | §6.4: input ≥ 16 V, SOT-89 preferred |
| C6 | PBUS sense divider | 100 k / 100 k (0–6.6 V) | **100 k / 30.1 k** (0–14.3 V full scale, 2.55 V at 11 V) | §6.3: ADC sized for 0–11 V |
| C7 | Bulk capacitance | 10 µF 10 V + 2 × 22 µF 16 V | **4 × 10 µF 25 V (TMK212BBJ106MG-T)** on VM_P; 4.7 µF 25 V + 100 nF on PBUS_IN | Voltage rating; common parts; ≤ 220 µF |
| C8 | Programming | Tag-Connect TC2030-NL (J2, SWD) + 3 NPTH holes | **1 × 6 2.54 mm right-angle header J2: GND, 3V3, RX, TX, BOOT0, NRST** (STM32 ROM UART bootloader, USART1) | Owner req. 3 |
| C9 | MCU pin map | ADDR0/1 on PA9/PA10, SWD on PA13/PA14 | PA9/PA10 → **USART1 TX/RX**, PA14 → **BOOT0**, ADDR0 → PA13, ADDR1 → PC15, PA2 → **eFuse ILM (motor current)**, POT_HI → +3V3 | AN2606 bootloader pins; pins freed by SWD removal |
| C10 | I²C | direct to MCU, no ESD | **0 Ω series footprints + PESD5V0L1UL** on SCL and SDA at J1 | §6.5; common parts |
| C11 | Silkscreen | "+5V" pinout | **"PBUS 6–9 V"** at J1, "E0001 rev C", header pin names | Owner req. 2, E0003 §6.7 |
| C12 | Test points | none (TC2030 pads only) | **none** | Owner rule |
| C13 | R5 | Yageo RC0402FR-074K7L (no stock) | **KOA RK73H1ETTP4701F** | Owner req. 5 |
| C14 | J1 sourcing | DigiKey only (stock 0) | DigiKey 455-1566-1-ND, **second source RS 1755704** | Owner req. 5 |
| C15 | 100 nF / 10 µF / 22 µF MPNs | CL05B104JO5NNNC (16 V), CL21A106KPCLQNC (10 V), CL21A226MOQNNNE | **GRM155R71H104KE14D** (50 V), **TMK212BBJ106MG-T** (25 V); 22 µF dropped | PBUS up to 11 V; common parts |

**Unchanged from rev B:** MCU STM32C051F6P6 (TSSOP-20), DRV8210PDSGR (PWM interface, WSON-8), fader RV1 footprint and position, capacitive touch circuit (R5, R6, D2), wiper filter (R7, C7), status LED (D3, R10), 3 address solder jumpers on the bottom, JST-GH SM04B-GHS-TB on the east end, 4-layer stack-up, 107 × 17 mm outline, I²C at 3.3 V with no pull-ups on this board.

---

## 2. Requirements

### 2.1 Functional (owner)
| # | Requirement |
|---|---|
| F1 | Power from **PBUS v2** on J1 pin 1 (E0003 §6). Full operation at **5.5–9.0 V** at the connector; **no damage at 11 V continuous**; clean brown-out below 5.5 V. |
| F2 | **Silkscreen the supply voltage at the connector: "PBUS 6–9 V".** |
| F3 | Programming via the **STM32 ROM UART bootloader** on a **2.54 mm right-angle 1 × 6 header: GND, 3V3, RX, TX, BOOT0, NRST**, so a USB-UART adapter with DTR/RTS can enter the bootloader automatically. **No Tag-Connect / SWD connector.** |
| F4 | **No test points** anywhere (schematic or layout). |
| F5 | R5 = **KOA RK73H1ETTP4701F**. J1 SM04B-GHS-TB with **second source RS 1755704**. |
| F6 | **Full BOM**; owner stock is a flag only. |
| F7 | Keep the rev B functions: closed-loop motor drive of the ALPS RSA0N11M9A0J-compatible fader, position from the 10 k linear track, capacitive touch on the lever, I²C target, 3-bit address, status LED. |

### 2.2 Derived from E0003 §6 (host interface)
| # | Requirement | Where met |
|---|---|---|
| D1 | Pinout JST-GH 4-pin SM04B-GHS-TB: **1 PBUS, 2 SCL, 3 SDA, 4 GND**; MP pads = GND | §7 |
| D2 | **≤ 0.6 A continuous and peak, including motor stall**; own limit is primary, host eFuse (0.74–1.00 A) is backup | §4.4, §4.5 |
| D3 | Input capacitance **≤ 220 µF** | §4.3 (≈ 45 µF nominal) |
| D4 | Motor disabled until PBUS ≥ 5.5 V **and** the host enables it over I²C | §4.2, §10 |
| D5 | Measure PBUS with an ADC sized for 0–11 V; report it and any current-limit event over I²C | §4.6, §10 |
| D6 | Must not source current into PBUS (back-EMF stays local) | §4.2 (eFuse reverse blocking) |
| D7 | Tolerate unannounced power loss (motor coasts, no damage) | §4.2, §10 |
| D8 | I²C **3.3 V**, **no pull-ups** (DNP bench footprints allowed), 5 V-tolerant (FT) pins, **no back-powering** through SCL/SDA, ≤ 15 pF per line, series R 0 Ω (≤ 100 Ω allowed) | §7 |
| D9 | Address **0x30–0x37**, 3 solder jumpers, default all open = **0x37**; no interrupt line | §7 |
| D10 | Silkscreen **"PBUS 6–9 V"** at the connector and the revision letter in the board text | §9.3 |

---

## 3. Block diagram

```
J1 pin1 PBUS ──► PBUS_IN ──[U4 TPS259470ARPWR eFuse]──► VM_P (protected PBUS, 5.5–9.0 V)
   (6.0–8.8 V)     │  C 4.7 µF + 100 nF        │ EN/UVLO 1M/330k (4.84 V rise)   ├── D1 SMF9.0A
                   │                           │ OVLO    1M/137k (9.96 V rise)   ├── 4 × 10 µF 25 V + 100 nF
                   │                           │ ILM 5.23k → 0.64 A ──R 10k──► PA2 (ADC: motor/board current)
                   │                           │ ITIMER 4.7 nF, dVdt 1.8 nF      ├── U3 DRV8210P VM ──► fader motor M+/M−
                   │                                                             ├── R 100k/30.1k ──► PA4 (ADC: PBUS)
                   │                                                             └── R2 10 Ω ─► U2 MCP1703A ─► +3V3
J1 pin2/3 SCL/SDA ─┴─ PESD5V0L1UL ×2 ── 0 Ω ── PB6/PB7 (I2C1, FT)                           │
J1 pin4 GND                                                                       U1 STM32C051, DRV8210 VCC, pot top, LED
J2 1×6 R/A header: GND · 3V3 (→BAT54W→LDO_IN, after R2) · RX (PA10) · TX (PA9) · BOOT0 (PA14, 1k / 10k PD) · NRST (via BAT54W)
```

---

## 4. Power

### 4.1 Rails
| Net | Source | Voltage | Feeds |
|---|---|---|---|
| **PBUS_IN** | J1 pin 1 | 6.0–8.8 V normal (host guarantee); 5.5–9.0 V operating; 11 V survive; −15 V survive | U4 IN, UVLO/OVLO dividers, C_IN |
| **VM_P** | U4 OUT | PBUS_IN − ≤ 0.03 V | DRV8210 VM, bulk caps, SMF9.0A, PBUS sense divider, LDO (via R2) |
| **LDO_IN** | VM_P via R2 10 Ω; or J2 pin 2 via BAT54W (programmer only) | VM_P − ≤ 0.15 V; ≈ 3.0 V from a programmer | U2 MCP1703A V_IN, C2 |
| **+3V3** | U2 MCP1703A | 3.3 V (≈ 2.9 V when powered from J2 only), ≈ 10–15 mA | STM32C051, DRV8210 VCC, fader track top (POT_HI), LED |

No +5 V net on rev C. The In2.Cu plane (rev B: +5V) becomes **VM_P**.

### 4.2 Input protection and current limit — U4 **TPS259470ARPWR** [decided, Q1/Q2]
The TPS25947 family is rated 2.7–23 V operating, **28 V absolute maximum, withstands −15 V on IN**, has back-to-back FETs with **true reverse-current blocking**, adjustable **OVLO** (1.2 µs) and active current limit (0.5–6 A), R_ON 28 mΩ, 2 × 2 mm QFN (datasheet SLVSFC9C). It is the same family as E0003's port eFuses; the **A (auto-retry, 110 ms)** variant is used here so the fader recovers from a local fault without a host power cycle (E0003 keeps the latch-off L variant).

| Function | Setting | Result (datasheet thresholds incl. tolerance) | Check |
|---|---|---|---|
| **EN/UVLO** | **1 MΩ / 330 kΩ 1 %** from PBUS_IN | **4.84 V rising** (4.77–4.93 V), **4.40 V falling** | Below the 5.5 V operating minimum; the motor's 5.5 V gate is in firmware (§10). Top resistor ≥ 350 kΩ as the datasheet asks for reverse-polarity inputs. |
| **OVLO** | **1 MΩ / 137 kΩ 1 %** (same as E0003) | **9.96 V rising** (9.8–10.2 V incl. ±1 % R), 9.05 V falling; off in 1.2 µs | Above 9.0 V operating max; below DRV8210 VM 11 V operating max and 12 V abs max. At 11 V input the output is off, so **11 V continuous is survived** (only U4, the dividers and C_IN see it). OVLO pin 0.66–1.33 V over 5.5–11 V (allowed 0.5–1.5 V). |
| **Current limit** | **R_ILM 5.23 kΩ 1 %** (I_LIM = 3334 / R_ILM) | **0.64 A typ, ≈ 0.54–0.73 A** (interpolated from the 0.5 A and 1.0 A test points, ±15 %) | Max (0.73 A) is below the host eFuse minimum (0.74 A), so the local limit acts first (§6.6 rule 3). Margin is small: see Q1. |
| **ITIMER** | **4.7 nF** | ≈ 3.9 ms (2.4–6.8 ms) of transient blanking; peaks up to 2 × I_LIM pass within it | Shorter than the host blanking (11–32 ms), so a held overload is handled locally first. |
| **dVdt** | **1.8 nF** (C_dVdt[pF] = 2000 / SR[V/ms]) | ≈ 1.1 V/ms → ≈ 50 mA inrush into 45 µF | Applies on local restarts (auto-retry, OVLO recovery); the host also ramps at 1 V/ms. |
| **FLT** | not connected (open drain) | — | No free MCU pin; faults are visible on ILM / VM_P (§10). |
| **ILM** (current monitor) | to **PA2** (ADC1_IN2) via **10 kΩ**, **1 nF** at the MCU pin | 182 µA/A × 5.23 kΩ = **0.95 V/A** (±10 %): 0.6 A → 0.57 V | Gives the firmware a measured board current for the 0.6 A rule. Keep the ILM node short; the 10 k isolates the ADC sample capacitor from the limit loop. |

**Reverse polarity / back-feed:** U4 blocks −15 V on PBUS_IN and blocks VM_P → PBUS current (D6). The rev B AO3401A P-FET (V_GS ±12 V, only 1 V margin at 11 V) and its gate resistor R1 are removed.

### 4.3 TVS and capacitors
| Ref | Part | Net | Why |
|---|---|---|---|
| D1 | **SMF9.0A** (Littelfuse, SOD-123F) | VM_P → GND, next to U3/bulk | 9.0 V stand-off ≥ 8.8 V; clamps motor back-EMF and residual spikes on the protected side. **Not on PBUS_IN** (see Q3): a 9 V TVS directly on the connector would conduct heavily at the required 11 V continuous (V_BR 10.0 V min). |
| C_IN (2 parts) | **GRM188R61E475KE11D** 4.7 µF 25 V 0603 + **GRM155R71H104KE14D** 100 nF 50 V | PBUS_IN | eFuse input decoupling; 25/50 V rating covers 11 V |
| C_BULK (4 parts) | **TMK212BBJ106MG-T** 10 µF 25 V X5R 0805 | VM_P | 40 µF nominal (≈ 20 µF at 8 V DC bias). PWM ripple at 0.6 A, 25 kHz, D = 0.5: ≈ 0.3 V. Replaces rev B C1 (10 V part) and C11/C12 (22 µF). |
| C13 | GRM155R71H104KE14D 100 nF | DRV8210 VM pin | as rev B |
| C14 | GRM155R71H103KA88D 10 nF, **DNP** | across the motor | as rev B |

**Total input capacitance ≈ 45 µF nominal ≤ 220 µF (D3).**

### 4.4 Motor drive — U3 **DRV8210PDSGR** (kept)
DRV8210 (DSG): VM 0–11 V operating, **12 V abs max**; VCC 1.65–5.5 V (**5.75 V abs max**); R_DS(on) HS + LS ≈ 1.05 Ω; I_OCP 1.76 A; TSD 153 °C min; autosleep in coast.

- **VM = VM_P** (≤ 9.0 V operating, ≤ 10.1 V before OVLO cuts). Inside the 11 V rating.
- **VCC = +3V3** (rev B had +5 V; on rev C PBUS would exceed 5.75 V).
- IN1/IN2 = PA6/PA7 (TIM3_CH1/CH2), nSLEEP = PA8: unchanged.
- **Motor rating vs PBUS:** the ALPS motor is rated **10 V DC, ≤ 800 mA at 10 V** (≈ 12.5 Ω, effectively the stall figure; `lib/ALPS_RSA0N11M9A0J_notes.md`). The average motor voltage is D × PBUS ≤ 9.0 V < 10 V, so **no voltage derating is needed; the binding limit is the 0.6 A current cap**. No local motor regulator is needed.
- **Stall current and duty limit** (R_motor 12.5 Ω + 1.05 Ω bridge; board logic ≈ 15 mA reserved → motor budget 0.585 A):

| PBUS | Stall current at 100 % duty | Max duty for ≤ 0.585 A | Note |
|---|---|---|---|
| 5.5 V | 0.41 A | 100 % | |
| 6.0 V | 0.44 A | 100 % | |
| 7.4 V (nominal) | 0.55 A | 100 % | |
| 8.4 V | 0.62 A | 94 % | |
| 8.8 V | 0.65 A | **90 %** | |
| 9.0 V | 0.66 A | **88 %** | |

  Firmware rule: `D_max = min(1, 0.585 A × (R_motor + 1.05 Ω) / V_PBUS)`, with R_motor **measured at start-up** (short low-duty pulse, ILM current) because the clone motor may differ from ALPS (Q12), plus a closed-loop clamp on the ILM reading. The eFuse (0.54–0.73 A) is the hardware backstop.
- **Speed scaling:** rev B ran the motor at 5 V. Rev C sees 6–9 V, so firmware scales duty by 5 V / V_PBUS (or its own target) to keep the rev B motion profile.
- **Decay mode:** PWM in **slow decay (brake: IN1 = IN2 = 1 between pulses)** so motor current recirculates in the low-side FETs and does not pump VM_P. With U4 blocking reverse current, any regenerated energy stays on VM_P (absorbed by the 40 µF bulk and D1).
- **Thermal:** stall at 0.585 A → 0.36 W in the DRV8210 (R_θJA 99.6 °C/W → +36 °C). Firmware limits stall time (§10).
- PWM frequency ≥ 20 kHz (inaudible; ≤ 100 kHz allowed).

### 4.5 3V3 regulator — U2 **MCP1703A** (kept, SOT-89 per Q7)
- Input from **VM_P via R2 10 Ω** + C2 4.7 µF 25 V (as rev B). MCP1703A V_IN ≤ 16 V ✓ (E0003 §6.4 asks for ≥ 16 V).
- Load ≈ 10–15 mA (MCU 48 MHz, DRV8210 VCC 0.2 mA, pot 0.33 mA, LED 1.3 mA, U4 I_Q is on PBUS). Dissipation at 9.0 V × 15 mA ≈ 0.09 W: SOT-23A (≈ 336 °C/W) +29 °C; **SOT-89 (MCP1703AT-3302E/MB)** ≈ +14 °C.
- Output C5 4.7 µF, C3 1 µF, C4 100 nF at the MCU (as rev B).
- Fed after U4, so the LDO is behind the reverse/over-voltage protection and turns on with the eFuse (≥ 4.84 V). MCU brown-out handles the rest.
- **Programmer power (v1.1):** J2 pin 2 → BAT54W (anode at J2) → **LDO_IN**. Nothing external connects to +3V3, so the MCP1703A pins never exceed V_IN + 0.3 V. From a 3.3 V adapter: LDO_IN ≈ 3.0 V → +3V3 ≈ 2.9 V (LDO in dropout); the STM32C051 runs from 2.0 V. With PBUS present, LDO_IN ≈ 8 V reverse-biases the BAT54W (30 V), so no current flows into the adapter.
- Side effect: through R2, LDO_IN also pulls VM_P to ≈ 3 V. Loads there are small: the PBUS divider (≈ 23 µA), the DRV8210 VM sleep current and U4 OUT leakage (U4 blocks reverse current into PBUS). The motor stays off because firmware sees V_PBUS < 5.5 V (§10 rule 1).

### 4.6 PBUS measurement
- **R8 100 kΩ / R9 30.1 kΩ** from VM_P to PA4 (ADC1_IN4), C9 100 nF (as rev B). 11 V → 2.55 V; full scale 14.3 V; 3.5 mV/LSB.
- VM_P = PBUS − ≤ 0.03 V. It reads ≈ 0 V when U4 is off (OVLO or fault), which is how firmware sees a local eFuse trip.

### 4.7 Power budget (board, at the connector)
| State | Current | Note |
|---|---|---|
| Idle (motor asleep) | ≈ 15 mA | logic + U4 I_Q 0.43 mA |
| Moving | 0.15–0.35 A | E0003 §5.1 estimate |
| Stall / hold, worst | **≤ 0.6 A** | firmware duty limit + ILM loop; eFuse 0.54–0.73 A backstop |

---

## 5. MCU — STM32C051F6P6 (TSSOP-20) pin map

Signals checked against ST open pin data `STM32C051F6Px.xml`. Pins 16, 17, 19 and 20 each bond two GPIOs; the unused one stays an input/analog.

| Pin | GPIO | Rev B | **Rev C** | Notes |
|---|---|---|---|---|
| 1 | PB7 (/PB8) | I2C_SDA | **I2C1_SDA** | FT; also the bootloader's I2C1 SDA |
| 2 | PC14 | ADDR2 | **ADDR2** | internal pull-up, jumper to GND |
| 3 | PC15 | NC | **ADDR1** | moved from PA10 |
| 4 | VDD/VDDA | +3V3 | +3V3 | C4 100 nF, C3 1 µF |
| 5 | VSS | GND | GND | |
| 6 | PF2-NRST | NRST (TC2030) | **NRST** → J2 pin 6 via BAT54W | C6 100 nF kept |
| 7 | PA0 | TOUCH_SNS | TOUCH_SNS | unchanged |
| 8 | PA1 | TOUCH_DRV | TOUCH_DRV | unchanged |
| 9 | PA2 | POT_HI (drives track top) | **ILM** (ADC1_IN2, eFuse current) | track top moves to +3V3 (Q4) |
| 10 | PA3 | FADER_POS | FADER_POS | ADC1_IN3, unchanged |
| 11 | PA4 | VSENSE | **VSENSE (PBUS)** | divider 100 k / 30.1 k |
| 12 | PA5 | LED | LED | unchanged |
| 13 | PA6 | MOT_IN1 | MOT_IN1 | TIM3_CH1 |
| 14 | PA7 | MOT_IN2 | MOT_IN2 | TIM3_CH2 |
| 15 | PA8 | MOT_nSLEEP | MOT_nSLEEP | unchanged |
| 16 | PA9 [PA11] | ADDR0 | **USART1_TX** → J2 pin 4 "TX" | bootloader TX |
| 17 | PA10 [PA12] | ADDR1 | **USART1_RX** ← J2 pin 3 "RX" | bootloader RX (pull-up in bootloader) |
| 18 | PA13 | SWDIO (TC2030) | **ADDR0** | SWD is no longer used |
| 19 | PA14-BOOT0 (/PA15) | SWCLK (TC2030) | **BOOT0** ← J2 pin 5 via 1 kΩ, **10 kΩ pull-down** | sampled at reset (§6.2) |
| 20 | PB6 (/PB3/PB4/PB5) | I2C_SCL | **I2C1_SCL** | FT; also the bootloader's I2C1 SCL |

Address: 7-bit address = **0x30 | ADDR[2:0]**, with ADDRn = 1 when its jumper is **open** (internal pull-up), so all open = **0x37**, all closed = 0x30 (D9). Jumpers JP1–JP3 stay on the bottom side, labelled A0/A1/A2.

---

## 6. Programming — STM32 ROM UART bootloader on J2

### 6.1 Bootloader resources (AN2606)
- AN2606 (Rev 61, STM32C031xx section, same C0 bootloader and TSSOP-20 bonding) lists for the C0 bootloader: **USART1, PA10 = RX (input pull-up), PA9 = TX; 8 data bits, even parity, 1 stop bit**, plus **I2C1 on PB6 (SCL) / PB7 (SDA), 7-bit slave address 0x63** (0b1100011x). Note there: *"On TSSOP20 … USART1 PA9/PA10 IOs are remapped on PA11/PA12"*, i.e. the bootloader UART is on **pins 16 and 17**, which ST pin data confirms carry PA9 (USART1_TX) and PA10 (USART1_RX) on the STM32C051F6Px.
- **Activation (Pattern 11):** BOOT0 pin = 1 with option bits **nBOOT_SEL = 0, nBOOT1 = 1, BOOT_LOCK = 0**; or main flash empty (a blank part always starts the bootloader).
- **Pin availability:** in rev B pins 16/17 were the ADDR0/ADDR1 jumpers and pin 19 was SWCLK. Rev C moves ADDR0/1 to PA13/PC15 (freed by removing SWD), so **pins 16, 17 and 19 are free for the bootloader**. PB6/PB7 are already the I²C pins.
- **Pins confirmed from ST pin data** (`STM32C051F6Px.xml`, STM32_open_pin_data): **pin 16 = PA9 (USART1_TX), bonded with PA11; pin 17 = PA10 (USART1_RX), bonded with PA12; pin 19 = PA14-BOOT0** (bonded with PA15); pin 20 = PB6 (I2C1_SCL); pin 1 = PB7 (I2C1_SDA).
- **Still to confirm by someone with st.com access** (ST's server did not deliver these PDFs during this review): (a) the **STM32C051xx table in AN2606 Rev 70** (Feb 2026; the C051 uses bootloader V11.x), which should show the same USART1/I2C1 pins and address as the C031 table above; (b) the **RM0490 factory default of nBOOT_SEL** (§6.2). Both are §12 check 1.

### 6.2 BOOT0 option-byte rule
The BOOT0 pin is only honoured when **nBOOT_SEL = 0**. The first flash of a blank part (empty-flash entry) must also program **nBOOT_SEL = 0, nBOOT1 = 1, BOOT_LOCK = 0** (stm32flash / STM32CubeProgrammer option-byte write), otherwise the header's BOOT0 has no effect afterwards. This goes into the production programming procedure (§10).

### 6.3 Header J2
**Würth 61300611021** (WR-PHD 2.54 mm, 1 × 6, right-angle THT; DigiKey 732-5339-ND). Pin order (owner):

| J2 pin | Silk | Board net | Circuit | Adapter connection |
|---|---|---|---|---|
| 1 | GND | GND | — | GND |
| 2 | 3V3 | **LDO_IN** (MCP1703A input, after R2) via **BAT54W** (anode at header) | The adapter powers the board through the LDO for programming: LDO_IN ≈ 3.0 V → +3V3 ≈ 2.9 V. +3V3 is never back-fed (MCP1703A pins ≤ V_IN + 0.3 V). The diode blocks the board from feeding the adapter (Q5) | 3V3 out (optional) |
| 3 | RX | PA10 USART1_RX | direct (FT pin) | adapter **TXD** |
| 4 | TX | PA9 USART1_TX | direct | adapter **RXD** |
| 5 | B0 | PA14-BOOT0 | **1 kΩ series**, **10 kΩ to GND** on the board side | adapter **RTS#** |
| 6 | RST | PF2-NRST | **BAT54W, cathode at the header** (adapter can only pull NRST low; C6 100 nF kept) | adapter **DTR#** |

- **3.3 V-logic adapter required** (CP2102 / FT232R set to 3.3 V I/O).
- **Auto-entry sequence (line levels):** BOOT0 line high (RTS# de-asserted) → NRST low (DTR# asserted) ≥ 1 ms → NRST high → wait ≈ 10 ms → bootloader running; BOOT0 back low (RTS# asserted). Run the application: BOOT0 low, pulse NRST. For stm32flash this is an `-i` GPIO sequence (exact string set by firmware tooling, §10).
- Side effect: many adapters idle with RTS#/DTR# high when the port is closed, so a **power-up with the adapter still plugged in starts the bootloader**. Unplug the adapter for normal use.
- With only the adapter attached, the board runs at ≈ 2.9 V and VM_P sits at ≈ 3 V through R2. Firmware keeps the motor off below 5.5 V, so programming-only power from the adapter is safe (§4.5).
- Adapter levels at VDD ≈ 2.9 V: RX (PA10) is driven to 3.3 V, which is fine on an FT pin. BOOT0 is driven through 1 kΩ, which limits any injection current (FT status in §12 check 2).
- After boot, the application may use **USART1 on the same pins as a debug console**.
- **No SWD.** There is no debugger access in rev C (owner decision, Q13).

---

## 7. Host interface J1 and I²C

| J1 pin | Signal | Board circuit |
|---|---|---|
| 1 | **PBUS** | → PBUS_IN (U4 IN, C_IN) |
| 2 | SCL | **PESD5V0L1UL** to GND at the connector → **0 Ω** (RC0402JR-070RL) → PB6 |
| 3 | SDA | **PESD5V0L1UL** to GND at the connector → **0 Ω** → PB7 |
| 4 | GND | GND; MP pads = GND |

- **Connector:** JST **SM04B-GHS-TB(LF)(SN)**, DigiKey 455-1566-1-ND (stock 0 on 2026-10-18), **second source RS 1755704**, (E0003 uses LCSC C189895 for the same part). Position as rev B (east end, cable exits east).
- **No pull-ups** on this board (host 4.7 kΩ per port). Optional DNP 4.7 kΩ bench pull-up footprints are allowed by §6.5 but are **not added** (fewer parts; a bench host provides its own).
- **No back-powering:** STM32 FT pins have no clamp to VDD; the PESD diodes clamp to GND only. With PBUS off, SCL/SDA cannot power +3V3.
- **Load per line:** MCU pin ≈ 5 pF + PESD5V0L1UL (check C_d against the datasheet; §6.5 allows 1–5 pF) + short traces ≤ 15 pF.
- **Series R:** 0 Ω fitted (§6.5 default). The footprint allows up to 100 Ω if a damaged-cable PBUS-to-SCL short ever needs more current limiting (Q9).
- **Keep the rev B I²C routing rule:** ≥ 1.85 mm from the fader touch pad (RV1 "T"), no parallel run.
- The bootloader's I²C1 (address 0x63) sits on the same pins, so the host could in future update E0001 firmware over the cable after a software jump to the bootloader. This is a firmware option only; no hardware is added.

---

## 8. Unchanged circuits (rev B)
| Function | Parts | Note |
|---|---|---|
| Fader position | RV1 wiper → R7 1 kΩ → PA3, C7 100 nF; track bottom (pin 1) = GND | **Track top (pin 3) → +3V3** instead of PA2 (Q4); 0.33 mA |
| Touch | RV1 T → D2 PESD5V0L1UL, R5 **4.7 kΩ RK73H1ETTP4701F** → PA0 (SNS); R6 1 MΩ → PA1 (DRV) | unchanged circuit, new R5 MPN |
| LED | D3 LTST-C191KGKT green, R10 1 kΩ, PA5 | unchanged |
| Fader frame | RV1 FG lugs → GND | unchanged |

---

## 9. Mechanical, layout and silkscreen (PCB only)

### 9.1 Board
- **4 layers**, 1.6 mm: F.Cu / In1.Cu GND / **In2.Cu VM_P** (was +5V) / B.Cu.
- **Outline 107 × 17 mm, unchanged**; fader footprint, position and courtyards unchanged (motor zone at the west end, terminal block at the east end).
- **Removed:** TC2030 pads and its 3 NPTH locating holes (bottom), Q1, R1.
- **Added:** U4 + 8 passives (place where Q1/R1 were, between the terminal block and the MCU, close to the J1 power path), J2, BAT54W ×2, BOOT0 R ×2, ILM R/C, 2 × PESD + 2 × 0 Ω at J1, 2 extra 0805 bulk caps near U3.
- All SMD parts stay on the **top** side (bottom keeps only JP1–JP3, no bottom paste), as rev B.

### 9.2 J2 placement [decided, Q6]
- **Top side, south long edge, in the MCU zone (between the fader motor zone and the terminal-block courtyard)**, pins pointing outward past the board edge, pin 1 (GND) to the west.
- Free height under the fader channel is ≥ 17.8 mm; a right-angle header + Dupont housing is ≈ 2.5–3 mm high, so it fits under the fader.
- The THT tails on the bottom (≈ 2–3 mm) are shorter than the fader pins that already stick out ≈ 2.2 mm.
- 15.2 mm header length fits in the free stretch of the edge; keep it clear of the I²C/touch keep-out.

### 9.3 Silkscreen
| Where | Text |
|---|---|
| Next to J1 (top) | **"PBUS 6–9 V"** (≥ 1.0 mm text) and the pin-1 mark; pin names "PBUS SCL SDA GND" if space allows |
| Board name (top) | **"E0001 rev C"** (revision letter required by §6.7) |
| J2 (top, at each pin) | **GND 3V3 RX TX B0 RST**; plus "UART boot 3.3 V" |
| JP1–JP3 (bottom) | A0 A1 A2, "addr 0x30–0x37, open = 1" |

### 9.4 Layout rules
- **No test points** and no probe pads. Bring-up probing uses component pads and J2.
- U4: R_ILM right at the ILM pin (an open ILM pin means ≈ 0 A limit); thermal pad and GND vias per the TI layout; C_IN at IN.
- VM_P → U3 VM loop with C13 + bulk tight; D1 next to U3.
- I²C ≥ 1.85 mm from the touch pad, no parallel run (rev B rule).
- DRC with `E0001_fader_driver.kicad_dru` (JLC 4-layer), schematic parity, 0 violations, as rev B.

---

## 10. Firmware constraints the hardware relies on
1. **Motor enable gate:** motor stays off until **V_PBUS ≥ 5.5 V** (PA4) **and** the host has enabled it over I²C. Below 5.5 V: motor off, report brown-out.
2. **Current cap:** `D_max = min(1, 0.585 A × (R_motor + 1.05 Ω) / V_PBUS)`; R_motor measured at start-up; closed-loop clamp on the ILM reading (PA2, 0.95 V/A) so board current ≤ 0.6 A including stall. Report a limit event in the register map.
3. **Stall time limit** (e.g. ≤ 1 s at the cap, then hold at a lower duty or coast) for DRV8210 thermal margin.
4. **Slow-decay (brake) PWM**, ≥ 20 kHz; speed scaled to V_PBUS.
5. **U4 trip detection:** V_PBUS (VM_P) reads ≈ 0 or ILM saturates → report fault; U4 auto-retries every 110 ms.
6. **Option bytes at first programming: nBOOT_SEL = 0, nBOOT1 = 1, BOOT_LOCK = 0** (§6.2). Keep PA14 as input (BOOT0 pull-down) in the application.
7. Address from PA13/PC15/PC14 with internal pull-ups: 0x30 | ADDR.
8. PA11 and PA12 (bonded with PA9/PA10) and PA15, PB3/PB4/PB5, PB8 (bonded pins) stay inputs/analog.
9. Register map reports V_PBUS and current/fault events (E0003 §6.6 rule 2).

---

## 11. BOM (full; DigiKey LV, stock/price checked by API 2026-10-18; no orders)

Ref designators are provisional; final refs come from schematic capture. **Owner stock** is a flag only and does not reduce the quantity.

| Refs | Qty | Value | Footprint | MPN | Manufacturer | Supplier PN | Stock | EUR @1 | Owner stock | Status vs rev B |
|---|---|---|---|---|---|---|---|---|---|---|
| U1 | 1 | STM32C051F6P6 | TSSOP-20 | STM32C051F6P6 | ST | 497-STM32C051F6P6-ND | **47** | 1.28 | no | kept; **approved alternate STM32C051F8P6** (497-STM32C051F8P6-ND, 1178 pcs, same pinout, 64 KB), buy whichever is in stock (Q8) |
| U2 | 1 | 3.3 V LDO | **SOT-89-3** | **MCP1703AT-3302E/MB** | Microchip | MCP1703AT-3302E/MBCT-ND | 9366 | 0.66 | no | package change to SOT-89 (Q7) |
| U3 | 1 | H-bridge | WSON-8 2×2 | DRV8210PDSGR | TI | 296-DRV8210PDSGRCT-ND | 3849 | 0.76 | no | kept, VCC → 3V3 |
| U4 | 1 | eFuse | VQFN-HR-10 2×2 (RPW) | **TPS259470ARPWR** | TI | 296-TPS259470ARPWRCT-ND | 78910 | 1.81 | no | **new** |
| J1 | 1 | JST-GH 4p | SM04B-GHS-TB horizontal | SM04B-GHS-TB(LF)(SN) | JST | 455-1566-1-ND; **2nd source RS 1755704** | **0** (DigiKey) | 0.34 | unknown | kept, 2nd source |
| J2 | 1 | 1×6 2.54 R/A | PinHeader_1x06_P2.54mm_Horizontal | **61300611021** | Würth | 732-5339-ND | 6816 | 0.47 | no | **new** (replaces TC2030 J2, which had no BOM part) |
| RV1 | 1 | Motor fader 10 k lin | ALPS_RSA0N11M9A0J | RSA0N11M9A0J B10K clone | Fastigeaty (Amazon.de B0H45B29YK) | ASIN B0H45B29YK | — | — | unknown | kept |
| D1 | 1 | SMF9.0A | D_SOD-123F (SMF) | SMF9.0A | Littelfuse | F5755CT-ND | 2437 | 0.47 | no | **changed** (was SMF5.0A) |
| D2, D4, D5 | 3 | ESD | D_SOD-882 | PESD5V0L1UL,315 | Nexperia | 1727-4193-1-ND | 18740 | 0.22 | no | D2 kept; D4/D5 **new** (I²C) |
| D3 | 1 | LED green | 0603 | LTST-C191KGKT | Lite-On | 160-1446-1-ND | 2.8 M | 0.13 | no | kept |
| D6, D7 | 2 | Schottky | SOT-323 | BAT54W,135 | Nexperia | 1727-1869-1-ND | 26776 | 0.17 | no | **new** (NRST; J2 3V3 → LDO_IN) |
| C_BULK ×4 (C1, C11, C12, C20) | 4 | 10 µF 25 V X5R | 0805 | TMK212BBJ106MG-T | Taiyo Yuden | 587-6025-1-ND | 237658 | 0.18 | no | **changed** |
| C2, C5, C18 | 3 | 4.7 µF 25 V | 0603 | GRM188R61E475KE11D | Murata | 490-7203-1-ND | 713624 | 0.21 | no | C2/C5 kept; C18 **new** (PBUS_IN) |
| C3 | 1 | 1 µF 10 V | 0402 | CL05A105KP5NNNC | Samsung | 1276-1076-1-ND | 911254 | 0.09 | no | kept (3V3 only) |
| C4, C6, C7, C9, C10, C13, C17 | 7 | 100 nF 50 V X7R | 0402 | **GRM155R71H104KE14D** | Murata | 490-10700-1-ND | 1.4 M | 0.09 | no | MPN changed; C17 **new** |
| C14 | 1 | 10 nF 50 V | 0402 | GRM155R71H103KA88D | Murata | 490-4516-1-ND | 4.1 M | 0.09 | no | kept, **DNP** |
| C15 | 1 | 4.7 nF 50 V (ITIMER) | 0402 | GRM155R71H472KA01J | Murata | 490-8259-1-ND | 143253 | 0.09 | no | **new** |
| C16 | 1 | 1.8 nF 50 V (dVdt) | 0402 | C0402C182K5RACTU | KEMET | 399-C0402C182K5RACTUCT-ND | 9731 | 0.44 | no | **new** |
| C19 | 1 | 1 nF 50 V (ILM ADC) | 0402 | GRM155R71H102KA01D | Murata | 490-1303-1-ND | 4.2 M | 0.10 | no | **new** |
| R2 | 1 | 10 Ω | 0603 | RC0603FR-0710RL | Yageo | 311-10.0HRCT-ND | 264276 | 0.10 | no | kept |
| R5 | 1 | 4.7 kΩ | 0402 | **RK73H1ETTP4701F** | KOA | 2019-RK73H1ETTP4701FCT-ND | 2.9 M | 0.09 | no | **MPN changed** |
| R6, R11, R13 | 3 | 1 MΩ 1 % | 0402 | RC0402FR-071ML | Yageo | 311-1.00MLRCT-ND | 961162 | 0.09 | no | R6 kept; R11/R13 **new** (UVLO/OVLO top) |
| R7, R10, R18 | 3 | 1 kΩ | 0402 | RC0402FR-071KL | Yageo | 311-1.00KLRCT-ND | 3.6 M | 0.09 | no | R18 **new** (BOOT0 series) |
| R8 | 1 | 100 kΩ | 0402 | RC0402FR-07100KL | Yageo | 311-100KLRCT-ND | 6.1 M | 0.09 | no | kept |
| R9 | 1 | 30.1 kΩ 1 % | 0402 | RC0402FR-0730K1L | Yageo | 311-30.1KLRCT-ND | 12740 | 0.09 | no | **value changed** (was 100 k) |
| R12 | 1 | 330 kΩ 1 % | 0402 | RC0402FR-07330KL | Yageo | 311-330KLRCT-ND | 902151 | 0.09 | no | **new** (UVLO bottom; only non-common value) |
| R14 | 1 | 137 kΩ 1 % | 0402 | RC0402FR-07137KL | Yageo | YAG2972CT-ND | 126860 | 0.09 | no | **new** (OVLO bottom) |
| R15 | 1 | 5.23 kΩ 1 % | 0402 | RC0402FR-075K23L | Yageo | YAG3195CT-ND | 39950 | 0.09 | no | **new** (R_ILM) |
| R16, R17 | 2 | 10 kΩ | 0402 | RC0402FR-0710KL | Yageo | 311-10.0KLRCT-ND | 10.9 M | 0.09 | no | **new** (ILM series, BOOT0 pull-down) |
| R19, R20 | 2 | 0 Ω | 0402 | RC0402JR-070RL | Yageo | 311-0.0JRCT-ND | 1.0 M | 0.09 | no | **new** (I²C series) |
| JP1–JP3 | 3 | solder jumper | SolderJumper-2 open | — | — | — | — | — | — | kept (PCB only) |

**Removed from rev B:** Q1 AO3401A, R1 10 kΩ, SMF5.0A, the TC2030 J2 footprint and its NPTH holes. **MPNs replaced:** C1 (CL21A106KPCLQNC 10 V) and C11/C12 (CL21A226MOQNNNE 22 µF) become TMK212BBJ106MG-T; 100 nF CL05B104JO5NNNC becomes GRM155R71H104KE14D.
All non-connector parts except R12 (330 k) are on the cross-project common list. The refs fill the gaps left by rev B (R3/R4, C8 are unused).

---

## 12. Schematic-capture checks
1. **Needs st.com access:** (a) the STM32C051xx section of AN2606 Rev 70: bootloader USART1 = PA9/PA10, I2C1 address, activation pattern (§6.1); the package pins themselves (16/17/19) are already confirmed from ST pin data; (b) RM0490: factory default of nBOOT_SEL (plus nBOOT1, BOOT_LOCK).
2. RM0490 / datasheet: FT status of NRST, PA9, PA10, PA14, PB6, PB7.
3. MCP1703A: SOT-89 pinout (it differs from SOT-23A). J2 pin 2 goes to LDO_IN through the BAT54W, never to +3V3 (v1.1); check the dropout at ≈ 3.0 V in and 15 mA (≈ 2.9 V out expected).
4. TPS25947: ILM pin load (10 kΩ + 1 nF) vs. the current-limit loop; RPW footprint and thermal vias (reuse E0003's footprint `TI_RPW0010A_VQFN-HR-10_2x2mm_P0.475mm`).
5. PESD5V0L1UL capacitance vs the 15 pF I²C budget.
6. SMF9.0A footprint: E0003 uses D_SOD-123F; rev B used D_SMF. Use one footprint for the same MPN.
7. ERC 0, DRC 0 with schematic parity, no TP symbols.

---

## 13. Risks
| Risk | Mitigation |
|---|---|
| Local eFuse max (0.73 A) only 0.01 A under the host eFuse min (0.74 A) | Firmware cap at 0.6 A is primary; local ITIMER (≤ 6.8 ms) is shorter than the host's (≥ 11 ms); R_ILM 5.23 kΩ decided (Q1); 5.62 kΩ is the fallback if the prototype shows host trips |
| Clone motor resistance differs from ALPS (12.5 Ω) | R_motor measured at start-up + ILM loop; sample measurement before the PCB order (Q12) |
| STM32C051F6P6 stock 47 at DigiKey | STM32C051F8P6 (same pinout, 64 KB) 1178 in stock approved alternate (Q8) |
| JST SM04B-GHS-TB stock 0 at DigiKey | RS 1755704 second source; LCSC C189895 (used by E0003) |
| BOOT0 has no effect if nBOOT_SEL stays 1 | First-programming procedure sets it (§6.2); a blank part still enters the bootloader on its own |
| Adapter left plugged in boots the bootloader at power-up | Unplug for normal use; documented |
| No SWD debugging | UART console on J2; owner decision |
| Bootloader peripheral/pins taken from the C031 table of AN2606 Rev 61 (the C051 table in Rev 70 is not yet read; package pins confirmed from ST pin data) | §12 check 1, by someone with st.com access, before capture |
| An old 5 V board on PBUS | Not produced (E0003 §6.1); "PBUS 6–9 V" silkscreen |

---

## 14. Decided by the owner (2026-10-18)

The owner accepted every recommendation of v0.1. **There are no open questions.**

| # | Question | Decision |
|---|---|---|
| **Q1** | Local eFuse instead of the AO3401A P-FET with a firmware-only current limit; value of R_ILM | **Fit U4 TPS259470ARPWR, with R_ILM 5.23 kΩ** (0.54–0.73 A, common part). This handles reverse polarity, the 11 V requirement and back-EMF blocking, and gives a measured current. |
| **Q2** | Auto-retry (A) or latch-off (L) | **A (auto-retry, 110 ms).** The host's L eFuse remains the hard stop. |
| **Q3** | TVS position | **SMF9.0A on VM_P, after the eFuse; no TVS on PBUS_IN** (U4 IN is rated 28 V / −15 V; C_IN absorbs ESD). |
| **Q4** | Fader track top | **Tied to +3V3**, which frees PA2 for the eFuse current monitor (ILM). |
| **Q5** | J2 pin 2 "3V3" | **Through a BAT54W into the MCP1703A input (LDO_IN, after R2)**, never into +3V3 (v1.1, Manager: MCP1703A pins ≤ V_IN + 0.3 V). Power flows only into the board; ≈ 2.9 V on +3V3 when powered from the programmer. |
| **Q6** | J2 position | **Top side, south long edge in the MCU zone, pins pointing out of the edge, pin 1 = GND to the west.** |
| **Q7** | LDO package | **SOT-89: MCP1703AT-3302E/MB.** |
| **Q8** | MCU stock (STM32C051F6P6: 47 pcs) | **STM32C051F8P6 is the approved alternate** (same TSSOP-20 pinout, 64 KB). Buy whichever is in stock at order time. |
| **Q9** | I²C protection at J1 | **PESD5V0L1UL on SCL and SDA + 0 Ω series.** Change to 100 Ω only if a damaged-cable test shows MCU damage. |
| **Q10** | Option bytes | **Set nBOOT_SEL = 0, nBOOT1 = 1, BOOT_LOCK = 0 at first flash**; this is part of the programming procedure (§6.2, §10). |
| **Q11** | Bulk capacitance and PWM | **4 × 10 µF 25 V 0805 (≈ 45 µF total input); PWM ≥ 20 kHz in slow decay.** Add a 5th 10 µF only if the prototype shows VM_P ripple > 0.3 V. |
| **Q12** | Clone motor data | **Measure on a sample before the PCB order:** winding resistance, stall current at 7.4 V and 9 V, running current, direction. Do this together with the hole-pattern check left open from rev B. |
| **Q13** | No SWD | **Accepted.** Debug output goes to the USART1 console on J2. |
| **Q14** | Firmware update from E0003 over I²C | **Future firmware option only** (ROM bootloader on I2C1, address 0x63, entered by a software jump); no hardware change. |
