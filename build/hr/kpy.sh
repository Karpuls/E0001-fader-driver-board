#!/bin/bash
# Python 3.12 (snap core24, glibc 2.39) with KiCad 10.0.6 pcbnew bindings
ulimit -v 4500000
K=/home/karpulis/.backplane-bend/kicad/10.0.6; C=/snap/core24/2124/usr
export PYTHONPATH=$K/lib/python3/dist-packages PYTHONHOME=$C
export KICAD_KIFACE_HOME=$K/bin KICAD_STOCK_DATA_HOME=$K/share/kicad
exec $K/lib/ld-linux-x86-64.so.2 --library-path $K/lib:$C/lib/x86_64-linux-gnu $C/bin/python3.12 "$@"
