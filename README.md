# mercury — KiCad keyboard PCB

Clone with submodules:

```sh
git clone --recursive https://github.com/wenbang24/mercury.git
```

Open `mercury.kicad_pro` in KiCad 9. The schematic describes one keyboard half.

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
- 1N4148W diode footprint: `mercury:D_SOD-123_NoSilk` in the project-local
  `mercury.pretty` library. It copies KiCad's stock `Diode_SMD:D_SOD-123`,
  removing only the F.SilkS outline graphics while retaining reference text,
  pads, fabrication/courtyard drawings and the stock 3D model.

The bundled 3D model references use `${KICAD8_3RD_PARTY}` and only resolve
if marbastlib is also installed through KiCad's Plugin and Content Manager.
The git submodule alone provides symbols and footprints, not resolved 3D models.

## Keyboard schematic

One half has 18 keys: three rows of five and three thumb keys. Both halves use
this same schematic and PCB. ROW3 uses COL2, COL3, COL4; **COL4 is innermost**.
Switches SW1–SW15 run row-major; SW16–SW18 are the thumbs.

| XIAO GPIO | nRF52840 GPIO | U1 pin | Matrix net |
| --- | --- | --- | --- |
| D0 | P0.02 | 1 | COL0 |
| D1 | P0.03 | 2 | COL1 |
| D2 | P0.28 | 3 | COL2 |
| D3 | P0.29 | 4 | COL3 |
| D4 | P0.04 | 5 | COL4 |
| D5 | P0.05 | 6 | ROW0 |
| D6 | P1.11 | 7 | ROW1 |
| D7 | P1.12 | 14 | ROW2 |
| D8 | P1.13 | 13 | ROW3 |

The matrix is **COL2ROW**: column → switch → diode anode (pin 2) →
diode cathode (pin 1) → row. D1–D18 are 1N4148W in SOD-123.
XIAO D9/D10 (U1 pins 12/11), 5V, 3V3, SWDIO, SWCLK, NFC pins, and
the unused second GND pad (22) have no-connect flags.

J1 pin 1 is battery positive, through SW19 common pin 2 to throw pin 1,
then U1 BAT+ (16). J1 pin 2 connects to BAT- (15) and GND (9).
SW19 throw pin 3 is unused. SW20 connects RST (21) to GND.
The library marks both GND pads as power outputs; only pad 9 is used,
avoiding a power-output conflict without modifying the library.
A PWR_FLAG on switched battery positive supplies ERC's BAT+ power-input check.

## PCBs

`mercury.kicad_pcb` is the routed right half, with all 40 components on F.Cu.
`mercury-left.kicad_pcb` has mirrored placement and outline, but its footprints
are not mirrored: all 40 components remain on F.Cu, with readable front
silkscreen. U1's USB points up on both halves; SW19's actuator faces the
respective board edge. Both boards have components on one face only;
traces and vias may use both copper layers.
Signal tracks are 0.25 mm; BAT and GND tracks are 0.4 mm. There is no ground pour.

### Layout geometry

Placement and contour are adapted from [Chocofi by pashutk](https://github.com/pashutk/chocofi),
source revision `273676d11b06785fb5a1a94860a39fc36c38baba`, licensed under the
**CERN Open Hardware Licence v2 – Permissive (CERN-OHL-P)**; see
[the retained licence](CHOCOfi-LICENSE.txt). Only geometry is copied: Mercury's
schematic, electronics, footprints and routing are independent of Chocofi.
Modified 2026-11-07: reflected the source half for the right hand, scaled X by
17/18 (Y unchanged), refitted circular outline fillets and extended the contour
locally for external diodes and XIAO/power parts. No source mounting holes are copied.

PG1316S pitch is **17 × 17 mm**, versus Chocofi's 18 × 17 mm. From outer/pinky
COL0 to inner/index COL4, top-row Y stagger is **0, −12, −18, −11.38, −9 mm**.
Finger rows are 17 mm apart (the source's COL3 bottom row retains its 0.005 mm
offset). On the right, column X positions are **137, 120, 103, 86, 69 mm**,
and SW1 is anchored at **(137, 45) mm**. Thumb placements/rotations are:

| Switch | Position X, Y (mm) | Rotation | Thumb |
| --- | --- | --- | --- |
| SW16 | 91.5722, 87.59 | −180° | Outer, COL2 |
| SW17 | 72.6361, 90.18 | −165° | Middle, COL3 |
| SW18 | 53.1806, 93.39 | 120° | Inner, COL4 |

Diodes D1–D18 form one **3-column × 6-row cluster**, all at 0°, directly below
the XIAO inside the original-width controller wing: column X positions
**43.3, 48.5, 53.7 mm**, row Y positions
**54.7, 57.5, 60.3, 63.1, 65.9, 68.7 mm**, numbered row-major. Courtyard spacing is
0.5 mm horizontally and vertically. All diode courtyards are outside every
rotated **16.05 × 16.25 mm keycap envelope plus 0.5 mm margin on each side**.
Run `/usr/bin/python3 scripts/check_layout.py` to verify this on both boards,
along with unchanged switch/U1 placement, mirrored left placement, widths,
footprint containment and absence of diode silkscreen graphics. Reference text
is retained in the local footprint but hidden on the assembled boards.
The stepped column and thumb edges are straight between rounded corners, with
the small Chocofi-derived perimeter tabs removed. U1 is at
**(49.54, 40.39) mm, 0°**, USB pointing up, with its tip approximately 0.6 mm
inside the straightened controller-wing top. J1 (49.54, 73.4), reset SW20 (50.5, 79.6) and power
SW19 (43.3, 83.5; 90°) occupy the space below the diodes; SW19's actuator faces its outer
edge. The left board mirrors these positions without mirroring the footprints.

Regenerate left placement after right-board edits: `/usr/bin/python3 scripts/make_left.py`.
**This discards all left routing.** Nets and pad assignments are retained from
the right board; footprint X coordinates are reflected about the outline's
vertical centre and rotations are negated without flipping the footprints.

From the repository root, regenerate and route using the installed Temurin
JDK 25 and official Freerouting 2.5.0 release jar:

```sh
/usr/bin/python3 scripts/make_left.py
cp mercury.kicad_pro mercury-left.kicad_pro
mkdir -p fab/left-routing
/usr/bin/python3 scripts/route_board.py export mercury-left.kicad_pcb fab/left-routing/left.dsn
/home/ubuntu/tools/freerouting/jdk-25.0.5+8/bin/java -Djava.awt.headless=true \
  -jar /home/ubuntu/tools/freerouting/freerouting-2.5.0.jar \
  -de fab/left-routing/left.dsn -do fab/left-routing/left.ses \
  --gui.enabled=false -da --router.autorouter.max_passes=50 --router.optimizer.max_threads=1
/usr/bin/python3 scripts/route_board.py import mercury-left.kicad_pcb fab/left-routing/left.ses
kicad-cli pcb drc --severity-all mercury-left.kicad_pcb
```

To route an unrouted right board, use the same export / Java / import commands
with `mercury.kicad_pcb` and right-specific DSN/SES filenames, then run
`kicad-cli pcb drc --severity-all --schematic-parity mercury.kicad_pcb`.
SES import does not rip up existing copper: remove existing tracks/vias before
exporting when replacing a route.

The ignored local `mercury-left.kicad_pro` copy supplies identical net classes
and DRC settings. The export adds 0.55 mm edge keepouts to the DSN only; it
supports straight and circular-arc edges (arcs are sampled every ≤0.1 mm for
DSN keepouts; the board retains true arcs). Import enforces the track
widths above, including any Freerouting neckdowns. Always check DRC after
import: edits to placement may require manual escape/clearance repairs before
the board is fabrication-ready. No DRC rules are relaxed by these scripts.
