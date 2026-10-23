#!/bin/bash
# qc.sh board -> Router's checks on a scratch copy
W=/home/karpulis/.cache/e0001-handroute-wt; Q=/home/karpulis/.backplane-bend/bots/b1791384657-1165/qc
D=$W/build/qc/copy; mkdir -p $D; cp "$1" $D/b.kicad_pcb; cd $D
ulimit -v 4500000
PY="/home/karpulis/.cache/e0002venv/bin/python -I"
echo "== tm_viapad"; $PY $Q/tm_viapad.py b.kicad_pcb | tail -15
echo "== slots"; $PY $Q/slots.py b.kicad_pcb | sed -n '/after removing/,$p'
echo "== corners"; $PY $Q/corners.py b.kicad_pcb | tail -25
