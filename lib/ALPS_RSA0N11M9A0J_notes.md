# ALPS RSA0N11M9A0J motorized fader: library notes

Part used: Amazon.de ASIN B0H45B29YK, "Motorized Electric Fader for DM1000 M7CL LS9 ... Interchangeable with
RSA0N11M9A0J B10K 100mm" (brand Fastigeaty, seller Fadianshop). The listing has no drawings, so this library is
built from the **genuine ALPS RSA0N11M9A0J** data (ALPS catalogue drawing No. 4 and ALPS's official STEP model).
See "Uncertainties" for the clone.

| File | Content |
|---|---|
| `lib/Fader.kicad_sym` : `ALPS_RSA0N11M9A0J` | symbol, ref `RV`, footprint `Fader:ALPS_RSA0N11M9A0J` |
| `lib/Fader.pretty/ALPS_RSA0N11M9A0J.kicad_mod` | footprint |
| `lib/3dmodels/ALPS_RSA0N11M9A0J.step` | ALPS's own STEP model, rotated 180° about Z and moved up 26 mm so it sits on the footprint origin with no offset or rotation in KiCad (`${KIPRJMOD}/lib/3dmodels/ALPS_RSA0N11M9A0J.step`) |

## Ratings (ALPS)

| Item | Value |
|---|---|
| Type | Motor N fader, single unit, 100 mm travel, 9-T (T-bar) lever, lever length 8.2 mm |
| Track | 10 kΩ ±20 %, taper 1B (linear), rated power 0.5 W |
| Max operating voltage (track) | 10 V DC / 500 V AC (100 mm travel) |
| Insulation / voltage proof | 100 MΩ min at 250 V DC; 250 V AC for 1 min |
| Motor | brushed DC, **rated 10 V DC**, **max current 800 mA or less at 10 V DC** (ALPS gives only this maximum, which is effectively the stall/peak figure; no running or no-load current is published) |
| Touch sense track | yes (terminal T, connected to the lever) |
| Operating force | 0.8 ±0.5 N (0.3 to 1.3 N) |
| Stopper strength / lever push-pull | 100 N / 50 N |
| Life | 30,000 cycles |
| Operating temperature | −10 °C to +60 °C |
| Soldering | manual 350 °C max, 3 s; dip 260 °C max, 5 s |
| Status at ALPS | "Not recommended for new designs" (still produced for existing customers) |

### Circuit and motor polarity (ALPS circuit diagram, catalogue p.380)
- Terminal **3 = 100 %**, terminal **1 = 0 %**, terminal **2 = wiper**, **T** = touch track/lever.
- Motor: **A positive (B negative) moves the lever and contacts toward terminal 3 (100 %)**; B positive moves toward 1 (0 %).
  So **A = `M+`, B = `M-`**: M+ positive with respect to M- drives the knob toward the TOP/max end. This is ALPS's data;
  check it on the clone (see below).
- "3T side" in the drawing = the end of the frame where the 1/T/3/2 terminal block sits = **TOP (max) of travel**.
  "1T side" = the motor end = **BOTTOM (min)**. ALPS draws the lever at the 1T end, the normal fully-down position.

## Pin mapping

| ALPS terminal | Function | Our pad / symbol pin number | Symbol pin name |
|---|---|---|---|
| 1 | track end, 0 % (bottom, motor end) | `1` | `END_BOT` |
| 2 | wiper | `2` | `WIPER` |
| 3 | track end, 100 % (top, terminal-block end) | `3` | `END_TOP` |
| T | touch sense (lever) | `T` | `TOUCH` |
| A | motor (+ to move to top) | `M+` | `M+` |
| B | motor | `M-` | `M-` |
| L (×2) | lug terminals (metal, part of the frame/bracket; mechanical retention, solder them) | `FG` (both pads) | `FRAME` |

All symbol pins are passive. Pin names are hidden on the symbol; pin numbers are shown.

## Footprint coordinate system
Viewed from the PCB top side (the fader sits on top, terminals go down into the board). X = travel axis, **+X = TOP
of travel (pad 3 end)**, origin = middle of the 100 mm travel on the fader centreline. KiCad Y points down the screen.
Travel ends: x = −50 (min, bottom) to x = +50 (max, top).

### Pads (all plated through holes)

| Pad | x (mm) | y (mm) | Drill | Pad | Terminal cross-section (from ALPS STEP) |
|---|---|---|---|---|---|
| 1 | +63.65 | +5.625 | 1.5 | 2.4 square (pin 1) | 0.5 × 1.0 mm blade (diagonal 1.12) |
| T | +63.65 | +1.875 | 1.5 | 2.4 round | 0.5 × 1.0 |
| 3 | +63.65 | −1.875 | 1.5 | 2.4 round | 0.5 × 1.0 |
| 2 | +63.65 | −5.625 | 1.5 | 2.4 round | 0.5 × 1.0 |
| FG | +56.65 | +5.625 | 2.0 | 3.2 round | 1.175 × 0.4 lug, twisted/bent at the tip |
| FG | +56.65 | −5.625 | 2.0 | 3.2 round | 1.175 × 0.4 lug |
| M+ (A) | −29.55 | +4.0 | 1.5 | 2.4 round | 0.4 × 1.0 blade (diagonal 1.08) |
| M- (B) | −29.55 | −4.0 | 1.5 | 2.4 round | 0.4 × 1.0 |

- The hole positions and diameters are ALPS's recommended "PC board mounting hole dimensions": 6× ø1.5 and 2× ø2, terminal
  column 63.65 mm from the travel centre at 3.75 mm pitch (11.25 mm overall), lugs 56.65 mm from centre in line with
  pins 1 and 2, motor pins 29.55 mm from centre on the motor side, 8 mm apart.
- ALPS's hole drawing is "viewed from mounting side". Their side view labels the panel face of the frame "Mounting surface",
  and the hole drawing has the same left/right orientation as the top view, so I read it as a view from the lever (component)
  side. Rotating that view 180° to our +X = top convention gives the y signs above: pin 1 and A on +y.
  This is the one interpretation step in the pinout (see Uncertainties).
- Courtyard (F.CrtYd) covers only the parts that come down to PCB level, each with a 0.5 mm margin:
  - terminal block: x 54.15 … 66.25, y ±7.95 (body x 54.65 … 65.75, ±7.45)
  - motor + gearbox + motor bracket: x −73.06 … −26.81, y ±9.5 (body x −72.56 … −27.31, ±9.0)
- F.SilkS: outlines of those two zones, corner marks at the far frame end (x = +74), and a pin-1 triangle next to pad 1.
- F.Fab: full projected body (146.56 × 18 mm, with the frame end narrowing to ±7.9), the travel axis with MIN/MAX marks,
  the two panel M3 screw positions, and the terminal-block outline.

## Body dimensions (ALPS drawing No. 4 + STEP)

| Item | Value |
|---|---|
| Overall length | 146.5 mm: 74.0 from the travel centre to the 3T (top) frame end, 72.5 (STEP 72.56) to the motor end |
| Footprint X extent | −72.56 (motor end) … +74.0 (terminal-block end) |
| Width | 18 mm max (motor bracket ±9.0; channel side rails ±8.5; frame ±7.9; end plates ±7.5) |
| Above the panel mounting surface | lever top 8.2 mm (T-bar 18.5 wide, knob holes 2× ø2 at 14.5 mm, lever 1.5 thick at the top (blade 1.2 thick)) |
| Panel mounting surface to PCB seating plane | **26 mm** |
| Terminal length below seating plane | 2.5 to 3.8 mm (lugs reach 3.8 mm); on a 1.6 mm PCB about 2.2 mm sticks out the bottom |
| Panel fixing | **2× M3 tapped holes in the frame**, on the centreline at x = ±60 mm (120 mm apart), screwed from the front panel side. **No PCB holes needed.** Only shown on F.Fab |
| Panel slot | ≥ 100 mm travel + lever width; the lever is 1.5 mm thick where it passes the panel (size the slot to your knob) |

### Free height under the channel (from the STEP, PCB top = 0)
- Channel underside: 6.5 mm below the panel face, so **≈19.5 mm** above the PCB.
- Five small snap tabs on the channel underside (STEP x ≈ ±40, −47, at y ≈ ±7.2) reach 8.15 mm below the panel face,
  so **≥17.8 mm** guaranteed free height over the whole channel between the two courtyard zones.
- Motor/gearbox body bottom: about 19 to 21 mm below the panel face, so **≈5 to 7 mm** above the PCB over footprint x −72.6 … −27.3.
  Only the motor bracket feet (footprint x −30.65 … −28.85, y ±8.0 … ±9.0) and the motor pins actually reach the PCB.
  The courtyard covers the whole motor zone anyway.
- Terminal block: reaches the PCB (standoffs at footprint x 59.75 … 65.75, y ±6.9 … ±7.45, and a centre rib).
- A gearbox/pulley part from footprint x −27.3 to −23.95 hangs ≈15 mm above the PCB (outside the courtyard; keep tall parts away).

## 3D model
`lib/3dmodels/ALPS_RSA0N11M9A0J.step` is ALPS's STEP model (`product_3dcad_rsa0n11m9a0j_en_*.zip` from the ALPS product
page), re-exported with colours from FreeCAD. ALPS's model origin is the travel centre on the panel mounting surface, with
the 3T end at −X. It was rotated 180° about Z and raised 26 mm, but the exported file has its height along Y (Y-up), so KiCad needs
model rotation X = −90° and offset Z = +26 mm (set in the footprint; checked against the board in a STEP export:
leads 2.2 mm through a 1.6 mm board, panel surface 26 mm above the PCB).
Resulting extents: x −72.56 … +74.0, y ±9, z −3.80 … +34.2. ALPS CAD data: fine for this design, but check ALPS's terms
before redistributing the file publicly.

## Sources
- ALPS product page (specs, STEP download): https://tech.alpsalpine.com/e/products/detail/RSA0N11M9A0J/
- ALPS catalogue pages, Motor-driven Master Type RS□□N1□M (pp.378 to 380: product line, dimensions No. 4 for RSA0N11M9A0J,
  PCB hole pattern, circuit diagram with motor direction):
  https://static.chipdip.ru/lib/596/DOC016596272.pdf (another copy: https://static.chipdip.ru/lib/060/DOC035060887.pdf)
- ALPS basic-information page for the 60 mm sibling RS60N11M9A0F (same specification format):
  https://media.onlinecomponents.com/productfiles/mf-ale/rs60n11m9a0f.pdf
- Conrad listing (0.5 W, 10 k linear): https://www.conrad.com/en/p/alps-rsaon11m9-motorised-fader-10-k-0-5-w-linear-1-pc-s-442081.html
- RSA0N11M9A0K (lead-wire terminals, drawing No. 3) has the same body; only the terminal style differs.

## Uncertainties / to verify
1. **Clone vs genuine.** The Fastigeaty/Fadianshop part is sold as "interchangeable", which should mean the same hole
   pattern, but no clone drawing exists. Before ordering PCBs, measure a sample with calipers: terminal column to motor pins
   distance (should be 63.65 + 29.55 = 93.2 mm), the 3.75 mm terminal pitch, the 8 mm motor pin pitch, the lug positions,
   the 26 mm height and the 146.5 mm length. Clones often use a different motor, so measure the clone's stall current at 10 V
   (ALPS: ≤800 mA) and its running current, and check its motor direction (A/B may not be marked).
2. **Y-orientation of the terminal column (1/T/3/2 vs 2/3/T/1).** It rests on reading "viewed from mounting side" as a view
   from the component side (reasons above). The STEP is symmetric in Y, so it cannot settle this. On a sample: with the fader
   fully down, measure which outer pin of the 4-pin column reads ~0 Ω to the wiper. That pin is 1 and should sit on the same
   side as motor terminal A (+y in this footprint). If it is the other way, swap the y signs of pads 1↔2, T↔3 and M+↔M-.
3. **Small datasheet/STEP differences.** ALPS's STEP puts the terminal centres 0.1 mm (pot pins, x 63.75) and 0.2 mm (motor
   pins, x 29.75; lugs y ±5.825) away from the hole drawing. The footprint follows the hole drawing; worst-case clearance is
   still positive (blade corner at ≈0.64 mm radius in a 0.75 mm radius hole; lug corner at ≈0.71 mm in a 1.0 mm radius hole).
4. **FG lugs.** I take the lugs to be metal from the frame/bracket (they are metal in the STEP); ALPS does not state whether
   they are connected to the frame or the motor can. Connect them to chassis/GND as a mechanical solder anchor.
5. **Touch sense.** T is a separate contact track that touches the metal lever. It only works with a conductive knob (metal or
   conductive-plastic cap). The 9-T lever takes the knob on its 18.5 mm T-bar (2× ø2 holes, 14.5 mm apart). ALPS gives no
   capacitance figure for this electrode.
6. **Motor current figures.** ALPS publishes only "maximum current of motor 800 mA or less at 10 V DC"; it gives no running
   current or separate stall figure. Size the driver for ≥800 mA continuous at 10 V.
7. Yamaha service part numbers / service-manual drawings (DM1000, LS9, M7CL) were not used. ALPS's own drawing and STEP
   were enough.
