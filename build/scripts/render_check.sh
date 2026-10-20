#!/bin/bash
# ERC + netlist + PDF + connectivity report for the E0003 schematic
set -e
cd "$(dirname "$0")/../.."
K=/home/karpulis/.backplane-bend/kicad/10.0.6/bin/kicad-cli
mkdir -p build/out
"$K" sch erc --severity-all -o build/out/erc.rpt E0001_fader_driver.kicad_sch | tail -1
grep -E "ERC messages" build/out/erc.rpt
"$K" sch export netlist --format kicadsexpr -o build/out/E0001.net E0001_fader_driver.kicad_sch >/dev/null
"$K" sch export pdf -o build/out/E0001_sch.pdf E0001_fader_driver.kicad_sch >/dev/null
python3 - <<'PY'
import sys
sys.path.insert(0, 'build/scripts')
from sexp import parse, find, findall
n = parse(open('build/out/E0001.net').read())
for net in findall(find(n, 'nets'), 'net'):
    nm = find(net, 'name')[1]
    nodes = ['%s.%s' % (find(x, 'ref')[1], find(x, 'pin')[1]) for x in findall(net, 'node')]
    if (nm.startswith('Net-(') or len(nodes) < 2) and not nm.startswith('unconnected-'):
        print('  check net:', nm, nodes)
PY
