#!/usr/bin/python3
"""Generate unrouted left placement, keeping component footprints unmirrored."""

from pathlib import Path

import pcbnew


def main():
    root = Path(__file__).resolve().parent.parent
    board = pcbnew.LoadBoard(str(root / "mercury.kicad_pcb"))
    bounds = board.GetBoardEdgesBoundingBox()
    axis = bounds.GetCenter().x
    footprints = list(board.GetFootprints())
    assert len(footprints) == 22
    assert all(fp.GetLayer() == pcbnew.F_Cu and not fp.IsFlipped()
               for fp in footprints)
    assert all(zone.GetIsRuleArea() for zone in board.Zones())
    controller = next(fp for fp in footprints if fp.GetReference() == 'U1')
    offset = pcbnew.VECTOR2I(2 * (axis - controller.GetPosition().x), 0)
    for zone in board.Zones():
        assert zone.GetZoneName().startswith('XIAO ')
        zone.Move(offset)
    for item in list(board.GetTracks()):
        board.Remove(item)
    for fp in footprints:
        pads = [(pad, pad.GetFPRelativePosition()) for pad in fp.Pads()]
        labels = [(text, text.GetPosition(), text.GetTextAngle().AsDegrees())
                  for text in [fp.Reference(), fp.Value()]]
        position = fp.GetPosition()
        fp.SetPosition(pcbnew.VECTOR2I(2 * axis - position.x, position.y))
        fp.SetOrientationDegrees(90 if fp.GetReference() == 'U1'
                                 else -fp.GetOrientationDegrees())
        for pad, local_position in pads:
            pad.SetFPRelativePosition(local_position)
        for text, position, angle in labels:
            text.SetPosition(pcbnew.VECTOR2I(2 * axis - position.x, position.y))
            text.SetTextAngle(pcbnew.EDA_ANGLE(-angle, pcbnew.DEGREES_T))
            text.SetMirrored(False)
    for item in board.GetDrawings():
        layer = item.GetLayer()
        item.Flip(pcbnew.VECTOR2I(axis, 0), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        item.SetLayer(layer)
        if isinstance(item, pcbnew.PCB_TEXT):
            item.SetMirrored(False)

    settings = board.GetDesignSettings()
    origin = settings.GetAuxOrigin()
    settings.SetAuxOrigin(pcbnew.VECTOR2I(2 * axis - origin.x, origin.y))
    assert all(fp.GetLayer() == pcbnew.F_Cu and not fp.IsFlipped()
               for fp in footprints)
    assert not list(board.GetTracks())
    destination = root / "mercury-left.kicad_pcb"
    pcbnew.SaveBoard(str(destination), board)
    print(f"Generated {destination.name}: unrouted, 22 unflipped footprints on F.Cu; U1 +90 degrees; keepouts retained")


if __name__ == "__main__":
    main()
