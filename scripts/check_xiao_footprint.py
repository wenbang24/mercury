#!/usr/bin/python3
"""Prove the SilkFix derivative retains the pinned official manufacturing geometry."""

import argparse
from pathlib import Path
import re
import subprocess


REVISION = '3be8215d3db652e2f62269913cb1fddd5e737d38'
SOURCE = 'Seeed Studio XIAO Series Library/XIAO-nRF52840-Plus-SMD.kicad_mod'


def parse(text):
    stack = [[]]
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text):
        if token == '(':
            node = []
            stack[-1].append(node)
            stack.append(node)
        elif token == ')':
            assert len(stack) > 1, 'Unbalanced footprint'
            stack.pop()
        else:
            stack[-1].append(token)
    assert len(stack) == 1 and len(stack[0]) == 1, 'Malformed footprint'
    return stack[0][0]


def check(official, derivative):
    assert official[:2] == ['footprint', '"XIAO-nRF52840-Plus-SMD"']
    assert derivative[:2] == ['footprint', '"XIAO-nRF52840-Plus-SMD_SilkFix"']

    def silk(item):
        return item[0].startswith('fp_') and ['layer', '"F.SilkS"'] in item

    original = official[2:]
    modified = derivative[2:]
    assert [item for item in original if not silk(item)] == [
        item for item in modified if not silk(item)], 'Non-silkscreen geometry changed'
    pads = [item for item in modified if item[0] == 'pad']
    assert len(pads) == 29
    assert all(set(next(item for item in pad if item[0] == 'layers')[1:]) ==
               {'"F.Cu"', '"F.Paste"', '"F.Mask"'} for pad in pads)
    removed = [item for item in original if item not in modified]
    assert len(removed) == 4 and all(silk(item) for item in removed)
    assert all(item in original for item in modified), 'Unexpected footprint addition'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('official_clone', type=Path, help='Local OPL_Kicad_Library clone')
    args = parser.parse_args()
    official = subprocess.check_output(['git', '-C', str(args.official_clone),
                                        'show', f'{REVISION}:{SOURCE}'], text=True)
    path = Path(__file__).resolve().parent.parent / 'mercury.pretty/XIAO-nRF52840-Plus-SMD_SilkFix.kicad_mod'
    check(parse(official), parse(path.read_text()))
    print('PASS: SilkFix vs official OPL 3be8215: all 29 pads, copper/paste/mask, courtyards and other non-silk geometry identical; only four F.SilkS graphics removed')


if __name__ == '__main__':
    main()
