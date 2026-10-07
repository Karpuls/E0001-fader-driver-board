import sys, subprocess
from PIL import Image
# usage: crop_pcb.py pdf out_prefix dpi x0 x1 [mirror]
pdf, pref, dpi = sys.argv[1], sys.argv[2], int(sys.argv[3])
x0, x1 = float(sys.argv[4]), float(sys.argv[5])
mirror = len(sys.argv) > 6
subprocess.run(['pdftoppm', '-r', str(dpi), '-png', '-singlefile', pdf, '/tmp/fbr_pcbpage'], check=True)
im = Image.open('/tmp/fbr_pcbpage.png').convert('RGB')
s = dpi / 25.4
if mirror:   # mirrored print: page x -> 297 - x
    x0, x1 = 297 - (100 + x1), 297 - (100 + x0)
else:
    x0, x1 = 100 + x0, 100 + x1
y0, y1 = 100 - 9.5, 100 + 9.5
im.crop((int(x0 * s), int(y0 * s), int(x1 * s), int(y1 * s))).save(pref + '.png')
print(pref + '.png', im.size)
