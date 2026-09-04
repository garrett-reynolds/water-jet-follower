# HB-Laser 3D HydroMatrix HD Single Module — what it needs and exposes

Research for GitHub issue #2. Researched 2026-09-04 from HB-Laser's own PDFs and pages only.
No user manual as such is online; the primary source is the 4-page **Module Datasheet** PDF hosted
on HB-Laser's own product site 3d-hydromatrix.com (its imprint points to hb-laser.com). Its drawing
is dated 22.05.2017, so the figures are 2017-drawing-era; the catalogs are 2024 and 2025.

## Summary

- One HD single module (500 x 50 x 100 mm, 10 nozzles, 10 RGBW pixels) uses **50 DMX channels: 5 per pixel-fountain, in order red, green, blue, white, fountain height**. Only this one mode is documented.
- Power: **24 VDC, 3.2 A max per module**; power passes module-to-module; a new power feed-in is required every **5 HD modules**. DMX passes through too: **max 10 HD modules (500 ch) per universe**.
- Water: **each nozzle has its own integrated brushless DC pump** (no external pump). Required water level is stated as **8 mm** in the tech-facts section and **at least 8 cm** in the FAQ of the same site — conflict, unresolved.
- RDM is for **recalibration of fountain height**. Auto addressing needs an **optional programming connector plus separate software** per the datasheet (German version: "gesondert erhältlich" = sold separately), even though the catalog says "DMX RDM incl. auto addressing".
- Not found online: DMX connector/cable type at the feed-in cable's free end, whether a PSU ships with a module, basin mounting, ch-5 value mapping, address assignment across chained modules, the calibration/auto-addressing software manual.

## Naming caution

The datasheet calls the 500 x 50 x 100 mm unit the "HD module" and gives it 50 channels. The 2024/2025
catalogs call that same unit the "HD | Single Module" (10 pixels, 10 fountains) and use "3D HydroMatrix
HD" for a different 250 x 500 x 100 mm block with 50 fountains. The drawing (datasheet p.4, titled
"10er Modul") ties 50 channels to 10 nozzles: "50 DMX chanals, (5 chanal per nozzle) per Module 24V DC,
3,2A max. (10 nozzle)". So 50 channels is per 10-nozzle single module, not per 50-fountain block.

## Findings

| Item | Finding | Source |
|---|---|---|
| Channels per module | 50 (HD module). SD module: 25. | Datasheet p.1 [DS]; drawing p.4 [DS] |
| Channels per pixel-fountain | 5: "1: red, 2: green, 3: blue, 4: white, 5: fountain height" | Datasheet p.1 [DS] |
| DMX modes | Only the 5-ch-per-pixel / 50-ch mode is documented. Other modes: **not found**. | [DS] |
| Value mapping on ch 5 (e.g. 0 = jet off), curve | **Not found** | — |
| Address layout across chained modules | **Not found** (datasheet only gives per-universe maximum) | — |
| Max modules per DMX universe | 10 HD modules (= 500 ch) or 20 SD modules | Datasheet p.1 [DS] |
| Two modules on one DMX line | Yes: connectors pass "signal and electricity longitudinal or cross to the next module" (Function 1); up to 10 HD per universe | Datasheet p.1, p.3 [DS] |
| RDM | "DMX RDM for recalibration"; drawing: "DMX RDM calibration of fountain hight, data storage inside the module for independent Software use" | Datasheet p.1, p.4 [DS] |
| Auto addressing | "Auto addressing with optional available programming connector and additional software". After replacing a dot, "Auto addressing has to be done for the universe in which the replacement has taken place. For this, the optional programming connector and additional software is necessary. See separate manual: Software for calibration and auto addressing". German datasheet: "Autoadressierung über Programieradapter und Zusatzsoftware. (gesondert erhältlich)". Catalogs and product page instead say "DMX RDM incl. auto addressing". **Conflict; check what shipped with the units.** | Datasheet p.1, p.2 [DS]; German datasheet p.1 [DS-DE]; Catalog 2024 p.72 [CAT24]; Catalog 2025 p.72 [CAT25]; product page [PP] |
| "Software for calibration and auto addressing" manual | Referenced by the datasheet; **not found online** | Datasheet p.2 [DS] |
| Inter-module connection | Sealed pin-header blocks at each end labelled "Data & Power in" / "Data & Power out" (drawing). Longitudinal and cross connection connectors screw onto the busboard with 4 stainless screws (threadlock), silicone flat seal greased with silicone grease. A flexible longitudinal connector with 70 cm connection cable (or custom lengths) is offered for geometric layouts. | Datasheet p.3, p.4 [DS] |
| DMX/power feed-in | Feed-in variant of the longitudinal/cross connector "has 2 input cables for signal (DMX) and supply voltage" (Function 2); power-only feed-in variant has one cable (Function 3). | Datasheet p.3 [DS] |
| DMX connector and cable type at the free end of the feed-in cable (XLR? bare?) | **Not found** | — |
| Supply voltage / current | HD module: 24 VDC / 3.2 A (drawing: "3,2A max. (10 nozzle)"). SD: 24 VDC / 1.6 A. | Datasheet p.1, p.4 [DS] |
| Modules per power feed-in | New electricity feed-in every 5 HD modules (or 10 SD) | Datasheet p.1, p.3 [DS] |
| PSU included? | **Unresolved.** Catalog says "3D HydroMatrix includes all components necessary for operation" and, separately, lists "Accessoires: Powersupply, Cableset, Connectors" (2025: "Power supply, cable set, connectors"). Neither says what ships with one single module. | Catalog 2024 p.71-72 [CAT24]; Catalog 2025 p.72 [CAT25] |
| Pump | "brushless DC Pump, ceramic bearings, livetime 50.000h" per nozzle, integrated in the dot; "Each nozzel has its own integrated pump" (DryDECK page); "Each pump and thus each individual LED can be controlled individually" | Datasheet p.4 [DS]; Catalog 2025 p.74 [CAT25]; [HM] |
| Water level / depth | Tech-facts: "Only a water level of 8mm is required". FAQ on the same page: "You only need a water depth of at least 8 cm, nothing more." **Conflict; unresolved.** A "Water level sensor M3" is on the drawing. | [HM]; Datasheet p.4 [DS] |
| Water quality | pH 7.2-7.6; hardness 1-8.4 dH; free chlorine max 0.3 mg/l; chloride max 250 mg/l; total dry residue max 50 mg/l; 5-35 C; max particle 50 micron. Site: PVC/stainless, salt or fresh water; filtration via filter mats. | Datasheet p.1 [DS]; [HM] |
| Fountain height | 1 cm-1.5 m (catalogs, product page); 5 cm-1.5 m (datasheet); 5 cm-2 m (3d-hydromatrix.com). **Three values; unresolved.** | [CAT24] [CAT25] [PP]; [DS]; [HM] |
| Dimensions | Nominal 500 x 50 x 100 mm (L x W x H). Drawing labels: 499.80 (length), 51.30 and 91.40 (side view; an unlabelled 49.00 also appears). | Datasheet p.1, p.4 [DS]; [CAT24] [CAT25] [PP] |
| Pitch / pixels | 50 mm pitch; 10 RGBW LED pixels (90 LEDs); 10 fountains | [CAT24] [CAT25] [PP] |
| Mounting | Only documented: dots screwed to the busboard with 2 stainless screws; connectors with 4. Mounting of the module into a basin: **not found**. | Datasheet p.2, p.3 [DS] |
| Control software | HB-Laser uses MADRIX; any DMX-512 controller works | [HM] |
| Prices | No prices found on any source. | — |
| Contact | info@hb-laser.com; +49 (0)7171 104 6920; HB Laser components GmbH, Heldenbergstr. 26, 73529 Schwäbisch Gmünd, Germany; https://hb-laser.com/contact-2/ ; enquiry form https://3d-hydromatrix.com/formular/ | [CONTACT] [HM] |

## Open gaps

1. DMX connector and cable type on the free end of the feed-in cable — not found. Photograph the cable ends that shipped.
2. Whether a 24 V PSU (and which one) ships with a single module — not found. Check the shipped kit and label.
3. Value mapping for the fountain-height channel and any other DMX modes — not found; must be measured on the bench.
4. Address assignment across chained modules (does module 2 follow at ch 51?) — not found; the datasheet only gives 10 modules per universe.
5. Whether auto addressing works out of the box or needs the "optional programming connector and additional software" — sources conflict. The referenced "Software for calibration and auto addressing" manual is not online; ask info@hb-laser.com.
6. Minimum water depth: 8 mm vs 8 cm on the same site — unresolved.
7. Basin mounting method — not found.
8. Fountain height range: 1 cm or 5 cm lower bound; 1.5 m or 2 m upper bound — sources disagree.

## Sources

- [DS] Module Datasheet (EN, 4 pages, drawing dated 22.05.2017, uploaded 2023-01): https://3d-hydromatrix.com/wp-content/uploads/2023/01/Module-Datasheet.pdf
- [DS-DE] Modul-Datenblatt (DE): https://3d-hydromatrix.com/wp-content/uploads/2023/01/Modul-Datenblatt.pdf
- [PP] Product page HB-Hydro 2025 (single module: 10 pixels, 10 fountains, 50 mm pitch, 1 cm-1.5 m, "DMX RDM incl. auto addressing", 24 V): https://hb-laser.com/hb-hydro-2025/
- [CAT24] HB catalog 2024, pages 70-73 (single module p.72): https://hb-laser.com/wp-content/uploads/2024/03/20240304_HB_Katalog_ONLINE.pdf
- [CAT25] HB Magazin 2025, pages 70-75 (single module p.72, DryDECK / "each nozzle has its own integrated pump" p.74): https://hb-laser.com/wp-content/uploads/2025/02/HB_Magazin_Mailing.pdf
- [HM] 3d-hydromatrix.com (HB-Laser's product site; imprint links to hb-laser.com): https://3d-hydromatrix.com/
- [CONTACT] https://hb-laser.com/contact-2/ (also https://hb-laser.com/contact/)
- Older brochure link found in search but dead (HTTP 404): https://www.hb-laser.com/images/jsn_is_thumbs/images/pdfdownloads/3D-HydroMatrix-2018-web.pdf
