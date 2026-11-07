# mercury — KiCad keyboard PCB

Clone with submodules:

```sh
git clone --recursive https://github.com/wenbang24/mercury.git
```

Open `mercury.kicad_pro` in KiCad 9. The schematic and PCB are intentionally empty.

## Libraries

[marbastlib](https://github.com/ebastler/marbastlib) (CERN-OHL-P v2) is a
submodule pinned to **2025.08.03** (`b628d38`), the last KiCad 9 compatible
release. Do not update to master: it uses KiCad 10 format.
Project-level library tables register all bundled symbol and footprint libraries
using `${KIPRJMOD}` paths. Stock KiCad libraries remain available through the
global tables for passives, diodes, and other standard parts.

- XIAO nRF52840 symbol: `marbastlib-promicroish:Seeeduino_Xiao_nRF52840`.
  Battery pins are **15 = BAT-**, **16 = BAT+** in this release.
  Footprints: `marbastlib-xp-promicroish:Xiao_nRF52840_ACH`,
  `marbastlib-xp-promicroish:Xiao_nRF52840_AC_Reflow`, and
  `marbastlib-xp-promicroish:Xiao_nRF52840_AH_Pogo`.
- PG1316S switch footprint: `marbastlib-xp-choc:SW_PG1316S`
  (`libs/marbastlib/footprints/marbastlib-xp-choc.pretty`).
- Common keyboard footprints in `marbastlib-various`:
  - Reset pushbutton: `marbastlib-various:SW_SPST_SKQG_WithStem`.
  - Power slide switch: `marbastlib-various:SW_MSK12C02-HB`.
  - JST ACH two-pin battery connector: `marbastlib-various:CON_JST_ACH_BM02B`.
- 1N4148W diode footprint from stock KiCad: `Diode_SMD:D_SOD-123`.

The bundled 3D model references use `${KICAD8_3RD_PARTY}` and only resolve
if marbastlib is also installed through KiCad's Plugin and Content Manager.
The git submodule alone provides symbols and footprints, not resolved 3D models.
