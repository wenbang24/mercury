#!/usr/bin/python3
"""Regenerate mercury-left.kicad_pcb by flipping the right board left-to-right."""

from pathlib import Path

import pcbnew


def main():
    root = Path(__file__).resolve().parent.parent
    board = pcbnew.LoadBoard(str(root / "mercury.kicad_pcb"))
    bounds = board.GetBoardEdgesBoundingBox()
    axis = pcbnew.VECTOR2I(bounds.GetCenter().x, 0)
    items = [*board.GetFootprints(), *board.GetTracks(),
             *board.GetDrawings(), *board.Zones()]
    for item in items:
        item.Flip(axis, pcbnew.FLIP_DIRECTION_LEFT_RIGHT)

    settings = board.GetDesignSettings()
    origin = settings.GetAuxOrigin()
    settings.SetAuxOrigin(pcbnew.VECTOR2I(2 * axis.x - origin.x, origin.y))
    assert len(list(board.GetFootprints())) == 40
    assert all(fp.GetLayer() == pcbnew.B_Cu for fp in board.GetFootprints())
    destination = root / "mercury-left.kicad_pcb"
    pcbnew.SaveBoard(str(destination), board)
    print(f"Generated {destination.name}: 40 footprints on B.Cu, 0 on F.Cu")


if __name__ == "__main__":
    main()
