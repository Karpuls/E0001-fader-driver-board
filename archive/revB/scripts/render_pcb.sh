#!/bin/bash
# usage: render_pcb.sh <tag>  -> build/out/pcb_<tag>_top.png / _bot.png (board area, high res)
K=/home/karpulis/.backplane-bend/kicad/10.0.6/bin/kicad-cli
cd "/home/karpulis/KiCad/E0001 - fader driver board"
T=${1:-v}
"$K" pcb export pdf --layers "F.Cu,F.Fab,F.Courtyard,Edge.Cuts,F.Silkscreen" --mode-single --include-border-title -o build/out/pcb_top.pdf E0001_fader_driver.kicad_pcb >/dev/null 2>&1 || "$K" pcb export pdf --layers "F.Cu,F.Fab,F.Courtyard,Edge.Cuts,F.Silkscreen" -o build/out/pcb_top.pdf E0001_fader_driver.kicad_pcb
"$K" pcb export pdf --layers "B.Cu,B.Fab,B.Courtyard,Edge.Cuts,B.Silkscreen" --mirror -o build/out/pcb_bot.pdf E0001_fader_driver.kicad_pcb >/dev/null 2>&1 || "$K" pcb export pdf --layers "B.Cu,B.Fab,B.Courtyard,Edge.Cuts,B.Silkscreen" -o build/out/pcb_bot.pdf E0001_fader_driver.kicad_pcb
ls -la build/out/pcb_top.pdf build/out/pcb_bot.pdf
