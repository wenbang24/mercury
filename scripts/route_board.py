#!/usr/bin/python3
"""Export edge-constrained Specctra DSN or import SES at the keyboard widths."""

import argparse
from pathlib import Path

import pcbnew


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['export', 'import'])
    parser.add_argument('board', type=Path)
    parser.add_argument('specctra', type=Path)
    args = parser.parse_args()
    board = pcbnew.LoadBoard(str(args.board.resolve()))
    if args.operation == 'export':
        assert pcbnew.ExportSpecctraDSN(board, str(args.specctra.resolve()))
        keepouts = []
        for index, edge in enumerate(board.GetDrawings()):
            if edge.GetLayer() != pcbnew.Edge_Cuts:
                continue
            assert edge.GetShape() == pcbnew.SHAPE_T_SEGMENT
            start, end = edge.GetStart(), edge.GetEnd()
            assert start.x == end.x or start.y == end.y
            x1, y1 = pcbnew.ToMM(start)
            x2, y2 = pcbnew.ToMM(end)
            # DSN edge keepouts compensate for Freerouting's board-edge handling.
            for layer in ['F.Cu', 'B.Cu']:
                coords = [min(x1, x2) - .55, min(-y1, -y2) - .55,
                          max(x1, x2) + .55, max(-y1, -y2) + .55]
                rect = ' '.join(str(round(value * 1000)) for value in coords)
                keepouts.append(f'    (keepout "edge-{layer}-{index}" (rect {layer} {rect}))\n')
        dsn = args.specctra.read_text()
        assert '    (rule\n' in dsn
        dsn = dsn.replace('    (rule\n', ''.join(keepouts) + '    (rule\n', 1)
        args.specctra.write_text(dsn)
        print(f'Exported {args.specctra} with copper-edge keepouts')
    else:
        assert pcbnew.ImportSpecctraSES(board, str(args.specctra.resolve()))
        for track in board.GetTracks():
            if not isinstance(track, pcbnew.PCB_VIA):
                net = track.GetNetname()
                width = .4 if net.startswith('/BAT') or net == '/GND' else .25
                track.SetWidth(pcbnew.FromMM(width))
        pcbnew.SaveBoard(str(args.board.resolve()), board)
        print(f'Imported {args.specctra}; signal 0.25 mm, BAT/GND 0.4 mm; run DRC')


if __name__ == '__main__':
    main()
