# E0001 rev C BOM notes (Parts, 2026-10-19, SPEC_revC.md v1.0)
`bom/E0001_revC_bom.csv`: 31 lines, 53 parts. Built from the spec §11 table by `bom/gen_revC_bom.py` (needs the DigiKey API secrets file); **every DigiKey line was checked through the API today** (site LV, EUR): all supplier PNs equal the spec's, all Active. Columns: Supplier, Qty, QtyBasis, References (provisional until schematic capture), Value, Footprint, MPN, Manufacturer, SupplierPN, Stock, Lifecycle, UnitEUR (1 piece), LeadWeeks, DNP, OwnerStock, Notes. Re-sync to the schematic export after capture (same flow as E0002/E0003).
DigiKey parts cost about EUR 10.9 per board at 1-piece prices (plus J1 about USD 0.31 at LCSC, plus the fader).

## Sourcing points
- **U1 STM32C051F6P6:** 47 in stock (EUR 1.28). **Approved alternate STM32C051F8P6** (497-STM32C051F8P6-ND, 1,178 in stock, EUR 1.34, same pinout). Buy whichever is in stock.
- **U2 MCP1703AT-3302E/MB (SOT-89):** MCP1703AT-3302E/MBCT-ND, 9,366 in stock.
- **J1 SM04B-GHS-TB:** DigiKey 455-1566-1-ND has 0 stock (16 w). BOM line = **LCSC C189895** (1,900 in stock, min order 5, USD 0.31); second sources RS Online 1755704 / 7521797. The DigiKey MPN string is "SM04B-GHS-TB"; "(LF)(SN)" is the lead-free tin order code and the same part.
- **J2 Wuerth 61300611021:** 732-5339-ND, 6,816 in stock. Right-angle 1x6 2.54 mm header, THT.
- **RV1 fader:** Amazon.de ASIN B0H45B29YK (clone), not checked (the page is blocked); owner stock unknown.
- **U4 TPS259470ARPWR:** 78,910 in stock (same part as E0003).
- **R12 330 kOhm 1 %** is the only value not already used in E0002/E0003; everything else is on the common-parts list (`E0003/.../bom/common_parts_across_projects.csv`).
- C14 10 nF is DNP (as rev B). JP1-JP3 are PCB solder jumpers (no part).

## Lines that may need a schematic-capture check (spec §12)
SOT-89 pinout and V_OUT > V_IN behaviour of the MCP1703A (U2), RPW footprint (reuse E0003's), SMF9.0A footprint (D_SOD-123F as in E0003), PESD5V0L1UL capacitance vs the 15 pF I2C budget.
