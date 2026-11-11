#!/usr/bin/python3
"""Check an exported KiCad XML netlist against the direct-input wiring."""

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


def check(root):
    components = {component.attrib['ref'] for component in root.findall('./components/comp')}
    assert not any(ref.startswith('D') for ref in components), 'Unexpected diode'
    assert {ref for ref in components if ref.startswith('SW')} == {f'SW{i}' for i in range(1, 21)}
    nets = {net.attrib['name']: {(node.attrib['ref'], node.attrib['pin'])
                                for node in net.findall('node')}
            for net in root.findall('./nets/net')}

    def net(ref, pin):
        matches = [name for name, nodes in nets.items() if (ref, str(pin)) in nodes]
        assert len(matches) == 1, (ref, pin, matches)
        return matches[0]

    for i, (pad, gpio) in enumerate(zip([*range(1, 12), 15, 16, 17, 18, 21, 22, 23],
                                      [*range(14), 14, 17, 18, 19]), 1):
        name = net(f'SW{i}', 1)
        assert name == net('U1', pad) == f'/D{gpio}'
        assert nets[name] == {(f'SW{i}', '1'), ('U1', str(pad))}
        assert net(f'SW{i}', 2) == '/GND'
    assert net('J1', 1) == net('SW19', 2) == '/BAT_RAW'
    assert net('SW19', 1) == net('U1', 28) == '/BAT_SW'
    assert net('J1', 2) == net('U1', 13) == net('U1', 27) == net('U1', 29) == '/GND'
    assert net('SW20', 1) == net('U1', 26) == '/RST'
    assert net('SW20', 2) == '/GND'
    for pad in [12, 14, 19, 20, 24, 25]:
        assert nets[net('U1', pad)] == {('U1', str(pad))}
    controller = root.find("./components/comp[@ref='U1']")
    fields = {field.attrib['name']: field.text for field in controller.findall('./fields/field')}
    assert fields['LCSC'] == 'C48405120' and fields['MPN'] == '102010672'
    assert controller.findtext('footprint') == 'mercury:XIAO-nRF52840-Plus-SMD_SilkFix'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('netlist', type=Path)
    args = parser.parse_args()
    check(ET.parse(args.netlist).getroot())
    print('PASS: netlist: all 18 intended GPIO-to-switch-to-GND paths; no diodes; battery/switch/reset/GND paths; unused pins isolated; Plus BOM fields')


if __name__ == '__main__':
    main()
