#!/usr/bin/python3
"""Assert diode/keycap clearance and mirrored, single-face keyboard placement."""

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


def intersects(a, b):
    assert a and b
    for polygon in [a, b]:
        for start, end in zip(polygon, polygon[1:] + polygon[:1]):
            nx, ny = start[1] - end[1], end[0] - start[0]
            projections = [[x * nx + y * ny for x, y in points] for points in [a, b]]
            if max(projections[0]) < min(projections[1]) or max(projections[1]) < min(projections[0]):
                return False
    return True


def courtyard(fp):
    assert abs(fp.GetOrientationDegrees()) < .001
    points = []
    for item in fp.GraphicalItems():
        if isinstance(item, pcbnew.PCB_SHAPE) and item.GetLayer() == pcbnew.F_CrtYd:
            assert item.GetShape() in [pcbnew.SHAPE_T_SEGMENT, pcbnew.SHAPE_T_RECT]
            points.extend([pcbnew.ToMM(item.GetStart()), pcbnew.ToMM(item.GetEnd())])
    assert points
    x1, x2 = min(x for x, y in points), max(x for x, y in points)
    y1, y2 = min(y for x, y in points), max(y for x, y in points)
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


def angle_difference(a, b):
    return abs((a - b + 180) % 360 - 180)


def main():
    root = Path(__file__).resolve().parent.parent
    boards = [pcbnew.LoadBoard(str(root / name))
              for name in ['mercury.kicad_pcb', 'mercury-left.kicad_pcb']]
    footprints = [{fp.GetReference(): fp for fp in board.GetFootprints()} for board in boards]
    bounds = boards[0].GetBoardEdgesBoundingBox()
    axis = bounds.GetCenter().x
    for board, fps in zip(boards, footprints):
        assert len(fps) == 40
        assert all(fp.GetLayer() == pcbnew.F_Cu and not fp.IsFlipped() for fp in fps.values())
        caps = [rectangle(fps[f'SW{i}'], 16.05 + 1, 16.25 + 1) for i in range(1, 19)]
        diodes = [courtyard(fps[f'D{i}']) for i in range(1, 19)]
        for i, diode in enumerate(diodes, 1):
            for j, cap in enumerate(caps, 1):
                assert not intersects(diode, cap), f'D{i} courtyard intersects SW{j} keycap + 0.5 mm'
        assert not list(board.Zones())
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
    assert angle_difference(footprints[0]['U1'].GetOrientationDegrees(), 0) < .001
    for ref, right in footprints[0].items():
        left = footprints[1][ref]
        a, b = right.GetPosition(), left.GetPosition()
        assert abs(b.x - (2 * axis - a.x)) < 150 and b.y == a.y
        assert angle_difference(left.GetOrientationDegrees(), -right.GetOrientationDegrees()) < .001
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
    print('PASS: both boards: all 18 diode courtyards outside every rotated 16.05 x 16.25 mm keycap + 0.5 mm margin (648 pair checks)')
    print('PASS: 40 F.Cu footprints each, none flipped; switch coordinates/rotations and U1 unchanged; left mirrors right placement/outline, rotations and pad nets; readable labels; signal 0.25 mm / BAT-GND 0.4 mm; no zones')
    print('Board size excluding Edge.Cuts stroke: {:.3f} x {:.3f} mm'.format(
        *(value - .05 for value in pcbnew.ToMM(bounds.GetSize()))))


if __name__ == '__main__':
    main()
