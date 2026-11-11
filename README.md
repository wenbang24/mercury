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
global tables for other standard parts.

- XIAO nRF52840 **Plus**: official Seeed footprint
  `mercury:XIAO-nRF52840-Plus-SMD_SilkFix` in `mercury.pretty`,
  and symbol `mercury:XIAO-nRF52840_Plus_SMD` in `mercury.kicad_sym`.
  Source: [Seeed Studio OPL](https://github.com/Seeed-Studio/OPL_Kicad_Library/tree/3be8215d3db652e2f62269913cb1fddd5e737d38/Seeed%20Studio%20XIAO%20Series%20Library),
  revision `3be8215d3db652e2f62269913cb1fddd5e737d38` (KiCad 9).
  Copyright/attribution: Seeed Studio and OPL contributors, **CC BY-SA 4.0**;
  see [retained licence](SEEED-LICENSE.txt). The footprint derivative removes
  only two F.SilkS side-outline lines overlapping the castellated lands and
  two USB corner arcs crossing the flush board edge. Copper, paste, mask,
  courtyards and all other geometry are unchanged. Symbol changes: battery pin numbers
  32/33 corrected to **28/29**, pin 26 named **RST**, and the footprint property
  points to the project library. The schematic adds MPN `102010672`, manufacturer
  Seeed Studio and LCSC **C48405120** for JLCPCB's bare-module SMD assembly.
- PG1316S switch footprint: `marbastlib-xp-choc:SW_PG1316S`
  (`libs/marbastlib/footprints/marbastlib-xp-choc.pretty`).
- Common keyboard footprints in `marbastlib-various`:
  - Reset pushbutton: `marbastlib-various:SW_SPST_SKQG_WithStem`.
  - Power slide switch: `marbastlib-various:SW_MSK12C02-HB`.
  - JST ACH two-pin battery connector: `marbastlib-various:CON_JST_ACH_BM02B`.

The bundled 3D model references use `${KICAD8_3RD_PARTY}` and only resolve
if marbastlib is also installed through KiCad's Plugin and Content Manager.
The git submodule alone provides symbols and footprints, not resolved 3D models.

## Keyboard schematic

One half has 18 keys: three rows of five and three thumb keys. Both halves use
the same electrical design, with separate mirrored PCBs. Switches SW1–SW15 run
row-major from outer/pinky to inner/index; SW16–SW18 are the thumbs.
Each switch connects one dedicated GPIO to GND; **there are no diodes**.

| Switch | XIAO GPIO | nRF52840 GPIO | U1 pad |
| --- | --- | --- | --- |
| SW1 | D0 | P0.02 | 1 |
| SW2 | D1 | P0.03 | 2 |
| SW3 | D2 | P0.28 | 3 |
| SW4 | D3 | P0.29 | 4 |
| SW5 | D4 | P0.04 | 5 |
| SW6 | D5 | P0.05 | 6 |
| SW7 | D6 | P1.11 | 7 |
| SW8 | D7 | P1.12 | 8 |
| SW9 | D8 | P1.13 | 9 |
| SW10 | D9 | P1.14 | 10 |
| SW11 | D10 | P1.15 | 11 |
| SW12 | D11 | P0.15 | 15 |
| SW13 | D12 | P0.19 | 16 |
| SW14 | D13 | P1.01 | 17 |
| SW15 | D14 / NFC1 | P0.09 | 18 |
| SW16 | D17 | P1.03 | 21 |
| SW17 | D18 | P1.05 | 22 |
| SW18 | D19 | P1.07 | 23 |

ZMK requires **direct kscan**, pull-ups and active-low inputs, not a matrix
scanner. Configure `&uicr { nfct-pins-as-gpios; };` to use NFC1 as GPIO;
this disables NFC. D15/P0.10 and D16/P0.31 are not key inputs. D16 remains
reserved for the module's battery divider: its edge label BAT is **not BAT+**.
Unused D15, D16, 3V3, VBUS, SWDIO and SWCLK have no-connect flags.
All three GND pads (13, 27 and 29) connect to GND.

J1 pin 1 is battery positive, through SW19 common pin 2 to throw pin 1,
then U1 BAT+ (28). J1 pin 2 connects to BAT- (29) and GND.
SW19 throw pin 3 is unused. SW20 connects RST (26) to GND.
Power flags on switched battery positive and GND supply ERC's power-input checks.
SW19 disconnects the battery, including its charging path: charge with the switch
on. USB can still power the keyboard with the battery switch off. Use a suitable
protected single-cell Li-ion/LiPo battery; the XIAO contains its charger.

## PCBs

`mercury.kicad_pcb` is the routed right half, with all 22 components on F.Cu.
`mercury-left.kicad_pcb` has mirrored placement and outline, but its footprints
are not mirrored: all 22 components remain on F.Cu, with readable front
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
locally for XIAO/power parts. No source mounting holes are copied.

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

The former diode-cluster area remains empty. Run
`/usr/bin/python3 scripts/check_layout.py` to verify direct GPIO assignments,
unchanged switch/U1-centre placement, mirrored left placement, widths,
footprint/keycap containment, USB overhang and antenna/underside-pad keepouts.
The stepped column and thumb edges are straight between rounded corners, with
the small Chocofi-derived perimeter tabs removed. U1 is at
**(49.54, 40.39) mm, +90°**, USB pointing up and nominally flush with the local
controller-wing edge (0.08 mm tip overhang). A rounded diagonal transition
to the column edge preserves keycap coverage without tabs. J1 (49.54, 73.4), reset SW20 (50.5, 79.6) and power
SW19 (43.3, 83.5; 90°) occupy the lower controller wing; SW19's actuator faces its outer
edge. The left board mirrors these positions without mirroring the footprints.

Regenerate left placement after right-board edits: `/usr/bin/python3 scripts/make_left.py`.
**This discards all left routing.** Nets and pad assignments are retained from
the right board; footprint X coordinates are reflected about the outline's
vertical centre and rotations are negated without flipping the footprints,
except U1 which remains +90° so USB points up. Its rule areas translate with
the unmirrored controller rather than mirroring the underside pad pattern.

### Antenna and underside-pad keepouts

Both copper layers have a **13.6 × 2.5 mm** antenna rule area: relative to U1's
centre with USB up, X **−6.8..+6.8 mm**, Y **+7.9..+10.4 mm**. This forbids
tracks, vias, pads and copper pours in the central non-castellated tail at the
end opposite USB. It is derived from ANT1 (`ANTENNA-AN3216`) and the tail outline
in [Seeed's Plus v1.1 hardware project](https://files.seeedstudio.com/wiki/XIAO-BLE/Seeed_Studio_XIAO_nRF52840_Plus.zip),
not a published guaranteed RF clearance specification. Keep batteries/metal
away from this region; RF performance still requires physical testing.
Each exposed underside pad (24–29) also has a both-layer **via-only keepout**,
covering its land's bounding rectangle plus 0.2 mm on every side. Matching
official host lands and paste apertures remain present for reflow assembly.
The DSN exporter retains these rule areas as copper/via keepouts.

### Checks

```sh
kicad-cli sch erc --severity-all mercury.kicad_sch
kicad-cli pcb drc --severity-all --schematic-parity mercury.kicad_pcb
kicad-cli pcb drc --severity-all mercury-left.kicad_pcb
/usr/bin/python3 scripts/check_layout.py
mkdir -p fab
kicad-cli sch export netlist --format kicadxml --output fab/direct.xml mercury.kicad_sch
/usr/bin/python3 scripts/check_netlist.py fab/direct.xml
/usr/bin/python3 scripts/test_layout.py
/usr/bin/python3 scripts/check_xiao_footprint.py /home/ubuntu/analysis/xiao-plus/OPL_Kicad_Library
```

The last check reads the official footprint directly from commit `3be8215` in
the supplied OPL clone (its checkout branch does not matter). It asserts exact
equality of all 29 pads, including copper/paste/mask layers and attributes,
and all other non-silkscreen geometry. Only the four removed F.SilkS graphics
and the footprint identifier may differ. The unused unmodified copy is not
included in this project.

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
