#!/usr/bin/python3
"""Assert direct wiring, RF clearances and mirrored single-face placement."""

import math
from pathlib import Path

import pcbnew


SWITCHES = [
    (137, 45, 0), (120, 33, 0), (103, 27, 0), (86, 33.62, 0), (69, 36, 0),
    (137, 62, 0), (120, 50, 0), (103, 44, 0), (86, 50.62, 0), (69, 53, 0),
    (137, 79, 0), (120, 67, 0), (103, 61, 0), (86, 67.625, 0), (69, 70, 0),
    (91.5722, 87.59, -180), (72.6361, 90.18, -165), (53.1806, 93.39, 120),
]


def rectangle(fp, width, height):
    x, y = pcbnew.ToMM(fp.GetPosition())
    a = math.radians(fp.GetOrientationDegrees())
    return [(x + u * math.cos(a) + v * math.sin(a),
             y - u * math.sin(a) + v * math.cos(a))
            for u, v in [(-width/2, -height/2), (width/2, -height/2),
                         (width/2, height/2), (-width/2, height/2)]]


def assert_keepouts(board, controller):
    zones = {zone.GetZoneName(): zone for zone in board.Zones()}
    assert set(zones) == {'XIAO antenna', *[f'XIAO underside {i}' for i in range(24, 30)]}
    for name, zone in zones.items():
        assert zone.GetIsRuleArea() and zone.GetDoNotAllowVias()
        assert zone.GetLayerSet().Contains(pcbnew.F_Cu) and zone.GetLayerSet().Contains(pcbnew.B_Cu)
        assert zone.GetDoNotAllowTracks() == (name == 'XIAO antenna')
        assert zone.GetDoNotAllowCopperPour() == (name == 'XIAO antenna')
        if name == 'XIAO antenna':
            box = zone.Outline().BBox()
            assert pcbnew.ToMM(box.GetSize()) == (13.6, 2.5)
            x, y = pcbnew.ToMM(controller.GetPosition())
            assert math.dist(pcbnew.ToMM(box.GetPosition()), (x - 6.8, y + 7.9)) < .00015
            items = [*board.GetTracks(), *[pad for fp in board.GetFootprints() for pad in fp.Pads()]]
        else:
            pad = next(pad for pad in controller.Pads() if pad.GetNumber() == name.split()[-1])
            assert zone.Outline().Contains(pad.GetPosition())
            items = [track for track in board.GetTracks() if isinstance(track, pcbnew.PCB_VIA)]
        for item in items:
            for layer in [pcbnew.F_Cu, pcbnew.B_Cu]:
                if not item.GetLayerSet().Contains(layer):
                    continue
                copper = pcbnew.SHAPE_POLY_SET()
                item.TransformShapeToPolygon(copper, layer, 0, pcbnew.FromMM(.001), pcbnew.ERROR_OUTSIDE)
                copper.BooleanIntersection(zone.Outline())
                assert copper.OutlineCount() == 0, f'Copper inside {name}: {item.GetNetname()}'


def angle_difference(a, b):
    return abs((a - b + 180) % 360 - 180)


def assert_contained(board, footprints):
    outline = pcbnew.SHAPE_POLY_SET()
    assert board.GetBoardPolygonOutlines(outline)
    # Allow polygon approximation and the nominally flush USB edge 5 micrometres.
    outline.Inflate(pcbnew.FromMM(.005), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,
                    pcbnew.FromMM(.001))
    for fp in footprints:
        geometry = pcbnew.SHAPE_POLY_SET()
        for pad in fp.Pads():
            pad.TransformShapeToPolygon(geometry, pcbnew.F_Cu, 0, pcbnew.FromMM(.001),
                                        pcbnew.ERROR_OUTSIDE)
        for item in fp.GraphicalItems():
            if isinstance(item, pcbnew.PCB_SHAPE) and item.GetLayer() in [pcbnew.F_CrtYd, pcbnew.F_Fab]:
                item.TransformShapeToPolygon(geometry, item.GetLayer(), 0,
                                             pcbnew.FromMM(.001), pcbnew.ERROR_OUTSIDE, True)
        geometry.BooleanSubtract(outline)
        assert geometry.OutlineCount() == 0, f'{fp.GetReference()} protrudes beyond Edge.Cuts'
        ref = fp.GetReference()
        if ref.startswith('SW') and int(ref[2:]) <= 18:
            cap = pcbnew.SHAPE_POLY_SET()
            cap.NewOutline()
            for x, y in rectangle(fp, 16.05, 16.25):
                cap.Append(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
            cap.BooleanSubtract(outline)
            assert cap.OutlineCount() == 0, f'{ref} keycap extends beyond Edge.Cuts'


def usb_offset(board, fp):
    rectangles = [item for item in fp.GraphicalItems()
                  if isinstance(item, pcbnew.PCB_SHAPE) and item.GetLayer() == pcbnew.User_1
                  and item.GetShape() == pcbnew.SHAPE_T_RECT]
    assert rectangles
    usb = min(rectangles, key=lambda item: min(item.GetStart().y, item.GetEnd().y))
    x1, x2 = sorted([usb.GetStart().x, usb.GetEnd().x])
    tip = min(usb.GetStart().y, usb.GetEnd().y)
    edges = [item for item in board.GetDrawings() if item.GetLayer() == pcbnew.Edge_Cuts
             and item.GetShape() == pcbnew.SHAPE_T_SEGMENT
             and item.GetStart().y == item.GetEnd().y
             and min(item.GetStart().x, item.GetEnd().x) <= x1
             and max(item.GetStart().x, item.GetEnd().x) >= x2]
    assert edges
    return pcbnew.ToMM(min(item.GetStart().y for item in edges) - tip)


def main():
    root = Path(__file__).resolve().parent.parent
    boards = [pcbnew.LoadBoard(str(root / name))
              for name in ['mercury.kicad_pcb', 'mercury-left.kicad_pcb']]
    footprints = [{fp.GetReference(): fp for fp in board.GetFootprints()} for board in boards]
    bounds = boards[0].GetBoardEdgesBoundingBox()
    axis = bounds.GetCenter().x
    usb_offsets = []
    for board, fps in zip(boards, footprints):
        assert len(fps) == 22
        assert not any(ref.startswith('D') for ref in fps)
        assert all(fp.GetLayer() == pcbnew.F_Cu and not fp.IsFlipped() for fp in fps.values())
        assert_contained(board, fps.values())
        offset = usb_offset(board, fps['U1'])
        assert 0 <= offset <= .3, f'USB overhang {offset:.6f} mm is not within 0..0.3 mm'
        usb_offsets.append(offset)
        assert fps['U1'].GetFPID().GetLibNickname() == 'mercury'
        assert fps['U1'].GetFPID().GetLibItemName() == 'XIAO-nRF52840-Plus-SMD_SilkFix'
        assert angle_difference(fps['U1'].GetOrientationDegrees(), 90) < .001
        assert_keepouts(board, fps['U1'])
        pads = {pad.GetNumber(): pad.GetNetname() for pad in fps['U1'].Pads()}
        for i, pin in enumerate([*range(1, 12), 15, 16, 17, 18, 21, 22, 23], 1):
            switch = {pad.GetNumber(): pad.GetNetname() for pad in fps[f'SW{i}'].Pads()}
            assert switch['1'] == pads[str(pin)] and switch['2'] == '/GND'
        assert pads['13'] == pads['27'] == pads['29'] == '/GND'
        assert pads['28'] == '/BAT_SW' and pads['26'] == '/RST'
        for track in board.GetTracks():
            if not isinstance(track, pcbnew.PCB_VIA):
                net = track.GetNetname()
                width = .4 if net.startswith('/BAT') or net == '/GND' else .25
                assert track.GetWidth() == pcbnew.FromMM(width)
    for i, (x, y, angle) in enumerate(SWITCHES, 1):
        fp = footprints[0][f'SW{i}']
        assert math.dist(pcbnew.ToMM(fp.GetPosition()), (x, y)) < .01
        assert angle_difference(fp.GetOrientationDegrees(), angle) < .001
    assert pcbnew.ToMM(footprints[0]['U1'].GetPosition()) == (49.54, 40.39)
    assert angle_difference(footprints[0]['U1'].GetOrientationDegrees(), 90) < .001
    for ref, right in footprints[0].items():
        left = footprints[1][ref]
        a, b = right.GetPosition(), left.GetPosition()
        assert abs(b.x - (2 * axis - a.x)) < 150 and b.y == a.y
        expected_angle = 90 if ref == 'U1' else -right.GetOrientationDegrees()
        assert angle_difference(left.GetOrientationDegrees(), expected_angle) < .001
        assert sorted((p.GetNumber(), p.GetNetname()) for p in right.Pads()) == sorted(
            (p.GetNumber(), p.GetNetname()) for p in left.Pads())
        assert not left.Reference().IsMirrored() and not left.Value().IsMirrored()
    assert (footprints[0]['U1'].GetPosition().x - axis) * (footprints[1]['U1'].GetPosition().x - axis) < 0
    edges = [[d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
             for board in boards]
    assert len(edges[0]) == len(edges[1])
    for right in edges[0]:
        reflected = [(2 * axis - q.x, q.y) for q in [right.GetStart(), right.GetEnd()]]
        assert any(left.GetShape() == right.GetShape() and all(
            any(math.dist(q, (v.x, v.y)) < 150 for v in [left.GetStart(), left.GetEnd()])
            for q in reflected) for left in edges[1])
    print('PASS: no diodes; all 18 switches connect to their intended GPIO and GND on both boards')
    print('PASS: both boards: full rotated 16.05 x 16.25 mm keycap areas inside Edge.Cuts')
    print('PASS: USB tip overhang (positive = beyond PCB edge): right {:.6f} mm; left {:.6f} mm'.format(*usb_offsets))
    print('PASS: all footprints inside Edge.Cuts (pads, body and courtyards; 5 micrometre tolerance)')
    print('PASS: official Plus footprint at +90 degrees both boards; 13.6 x 2.5 mm two-layer antenna keepout has no copper; six underside pads have no vias')
    print('PASS: 22 F.Cu footprints each, none flipped; switch coordinates/rotations and U1 centre unchanged; mirrored placement/outline and pad nets; readable labels; signal 0.25 mm / BAT-GND 0.4 mm; no copper pours')
    print('Board size excluding Edge.Cuts stroke: {:.3f} x {:.3f} mm'.format(
        *(value - .05 for value in pcbnew.ToMM(bounds.GetSize()))))


if __name__ == '__main__':
    main()
