#!/bin/bash
# full PCB rebuild: placement -> pre-routes -> GND vias + Freerouting -> import + pours -> DRC
set -e
cd "/home/karpulis/KiCad/E0001 - fader driver board"
S=build/scripts
python3 $S/gen_pcb.py 2>&1 | grep -v assert | tail -1
python3 $S/patch_pro.py >/dev/null
python3 $S/preroute.py 2>&1 | grep -v assert | tail -1
python3 $S/patch_pro.py >/dev/null
python3 $S/route_pcb.py ${1:-20} 2>&1 | grep -v assert | grep -E "GND vias|freerouting|no via" || true
grep -E "unrouted connection|Net '" build/route/freerouting.log | tail -8 || true
python3 $S/finish_pcb.py 2>&1 | grep -v assert | tail -2
python3 $S/finish_pcb.py --no-ses 2>&1 | grep -E "redundant" || true
python3 $S/place_refs.py 2>&1 | grep -E "hidden" || true
K=/home/karpulis/.backplane-bend/kicad/10.0.6/bin/kicad-cli
"$K" pcb drc --severity-all -o build/out/drc.rpt E0001_fader_driver.kicad_pcb 2>&1 | tail -2
grep -E "^\[" build/out/drc.rpt | sed 's/:.*//' | sort | uniq -c | sort -rn || true
