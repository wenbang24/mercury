#!/usr/bin/python3
"""Regression checks for antenna/underside clearances and direct netlist wiring."""

import copy
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

import pcbnew

from check_layout import assert_keepouts
from check_netlist import check
from check_xiao_footprint import check as check_footprint, parse


ROOT = Path(__file__).resolve().parent.parent


class FootprintTests(unittest.TestCase):
    def test_parser(self):
        self.assertEqual(parse('(footprint "quoted ()" (pad "1"))'),
                         ['footprint', '"quoted ()"', ['pad', '"1"']])

    def test_empty(self):
        with self.assertRaises(AssertionError):
            parse('')

    def test_unbalanced(self):
        with self.assertRaises(AssertionError):
            parse('(footprint "name"')

    def test_pad_change_rejected(self):
        derivative = parse((ROOT / 'mercury.pretty/XIAO-nRF52840-Plus-SMD_SilkFix.kicad_mod').read_text())
        official = copy.deepcopy(derivative)
        official[1] = '"XIAO-nRF52840-Plus-SMD"'
        official.extend([['fp_line', ['layer', '"F.SilkS"'], ['uuid', str(i)]] for i in range(4)])
        check_footprint(official, derivative)
        next(item for item in derivative if item[0] == 'pad')[1] = '"999"'
        with self.assertRaisesRegex(AssertionError, 'Non-silkscreen geometry changed'):
            check_footprint(official, derivative)


class KeepoutTests(unittest.TestCase):
    def setUp(self):
        self.board = pcbnew.LoadBoard(str(ROOT / 'mercury.kicad_pcb'))
        self.controller = next(fp for fp in self.board.GetFootprints() if fp.GetReference() == 'U1')

    def test_routed_board(self):
        assert_keepouts(self.board, self.controller)

    def test_missing_keepout(self):
        for zone in list(self.board.Zones()):
            self.board.Remove(zone)
        with self.assertRaises(AssertionError):
            assert_keepouts(self.board, self.controller)

    def test_antenna_track_rejected(self):
        zone = next(zone for zone in self.board.Zones() if zone.GetZoneName() == 'XIAO antenna')
        box = zone.Outline().BBox()
        centre = box.GetCenter()
        track = pcbnew.PCB_TRACK(self.board)
        track.SetStart(centre)
        track.SetEnd(centre + pcbnew.VECTOR2I(pcbnew.FromMM(1), 0))
        track.SetWidth(pcbnew.FromMM(.25))
        track.SetLayer(pcbnew.B_Cu)
        self.board.Add(track)
        with self.assertRaisesRegex(AssertionError, 'Copper inside XIAO antenna'):
            assert_keepouts(self.board, self.controller)

    def test_underside_via_rejected(self):
        pad = next(pad for pad in self.controller.Pads() if pad.GetNumber() == '28')
        via = pcbnew.PCB_VIA(self.board)
        via.SetPosition(pad.GetPosition())
        via.SetWidth(pcbnew.FromMM(.6))
        via.SetDrill(pcbnew.FromMM(.3))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        self.board.Add(via)
        with self.assertRaisesRegex(AssertionError, 'Copper inside XIAO underside 28'):
            assert_keepouts(self.board, self.controller)


class NetlistTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'netlist.xml'
            subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml',
                            '--output', str(path), str(ROOT / 'mercury.kicad_sch')], check=True)
            cls.netlist = ET.parse(path).getroot()

    def test_schematic(self):
        check(self.netlist)

    def test_empty_netlist(self):
        with self.assertRaises(AssertionError):
            check(ET.Element('export'))

    def test_incorrect_gpio(self):
        root = copy.deepcopy(self.netlist)
        node = root.find("./nets/net[@name='/D0']/node[@ref='U1']")
        node.set('pin', '2')
        with self.assertRaises(AssertionError):
            check(root)

    def test_diode_rejected(self):
        root = copy.deepcopy(self.netlist)
        ET.SubElement(root.find('components'), 'comp', ref='D1')
        with self.assertRaisesRegex(AssertionError, 'Unexpected diode'):
            check(root)


if __name__ == '__main__':
    unittest.main()
