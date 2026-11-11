#!/usr/bin/python3
"""Export edge-constrained Specctra DSN or import SES at the keyboard widths."""

import argparse
import math
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
            start = pcbnew.ToMM(edge.GetStart())
            end = pcbnew.ToMM(edge.GetEnd())
            points = [start, end]
            if edge.GetShape() == pcbnew.SHAPE_T_ARC:
                cx, cy = pcbnew.ToMM(edge.GetCenter())
                mid = pcbnew.ToMM(edge.GetArcMid())
                angles = [math.atan2(y - cy, x - cx) for x, y in [start, mid, end]]
                sweep = (angles[2] - angles[0]) % math.tau
                if (angles[1] - angles[0]) % math.tau > sweep:
                    sweep -= math.tau
                radius = math.hypot(start[0] - cx, start[1] - cy)
                steps = max(1, math.ceil(abs(sweep) * radius / .1))
                points = [(cx + radius * math.cos(angles[0] + sweep * i / steps),
                           cy + radius * math.sin(angles[0] + sweep * i / steps))
                          for i in range(steps + 1)]
                points[0], points[-1] = start, end
            else:
                assert edge.GetShape() == pcbnew.SHAPE_T_SEGMENT
            # DSN edge keepouts compensate for Freerouting's board-edge handling.
            for layer in ['F.Cu', 'B.Cu']:
                coords = ' '.join(f'{round(x * 1000)} {round(-y * 1000)}'
                                  for x, y in points)
                keepouts.append(f'    (keepout "edge-{layer}-{index}" '
                                f'(path {layer} 1100 {coords}))\n')
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
