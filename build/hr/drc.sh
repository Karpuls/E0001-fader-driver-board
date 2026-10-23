#!/bin/bash
# drc.sh board.kicad_pcb -> DRC in a scratch copy with the project's pro/dru/sch
W=/home/karpulis/.cache/e0001c-handroute-wt; D=$W/build/qc/drc; mkdir -p $D
cp $W/E0001_fader_driver.kicad_pro $W/E0001_fader_driver.kicad_dru $W/E0001_fader_driver.kicad_sch $W/sym-lib-table $W/fp-lib-table $D/
cp "$1" $D/E0001_fader_driver.kicad_pcb
ulimit -v 4500000
/home/karpulis/.backplane-bend/kicad/10.0.6/bin/kicad-cli pcb drc --schematic-parity --severity-all --refill-zones --save-board --format json -o $D/drc.json $D/E0001_fader_driver.kicad_pcb >/dev/null 2>&1
python3 - $D/drc.json <<'PY'
import json,sys,collections
d=json.load(open(sys.argv[1]))
v=d.get('violations',[]);u=d.get('unconnected_items',[]);p=d.get('schematic_parity',[])
print('violations',len(v),'unconnected',len(u),'parity',len(p))
print(collections.Counter((x['type'],x['severity']) for x in v))
for x in (v+u+p)[:60]:
    print(' ',x['type'],x['severity'],x['description'][:60],' | '.join('%s @%.2f,%.2f'%(i['description'][:50],i['pos']['x'],i['pos']['y']) for i in x['items']))
PY
