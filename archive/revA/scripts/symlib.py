"""Load + flatten KiCad library symbols (KiCad 10 .kicad_symdir or .kicad_sym)."""
import os, copy
from sexp import parse, find, findall, Sym

KSYM = '/home/karpulis/.backplane-bend/kicad/10.0.6/share/kicad/symbols'
PROJ = '/home/karpulis/KiCad/E0001 - fader driver board'
LIBS = {'Fader': os.path.join(PROJ, 'lib/Fader.kicad_sym')}

def _load_raw(lib, name):
    if lib in LIBS:
        root = parse(open(LIBS[lib]).read())
    else:
        p = os.path.join(KSYM, lib + '.kicad_symdir', name + '.kicad_sym')
        root = parse(open(p).read())
    for s in findall(root, 'symbol'):
        if s[1] == name:
            return s
    raise KeyError(lib + ':' + name)

def load(lib, name):
    """Return flattened symbol with name 'lib:name' suitable for schematic lib_symbols."""
    s = copy.deepcopy(_load_raw(lib, name))
    ext = find(s, 'extends')
    if ext:
        parent = load(lib, ext[1])  # already flattened, named lib:parent
        pname = ext[1]
        child_props = {p[1]: p for p in findall(s, 'property')}
        out = [Sym('symbol'), lib + ':' + name]
        for x in parent[2:]:
            if isinstance(x, list) and x and x[0] == 'property':
                out.append(child_props.pop(x[1], x))
            elif isinstance(x, list) and x and x[0] == 'symbol':
                y = copy.deepcopy(x)
                y[1] = y[1].replace(pname + '_', name + '_', 1)
                out.append(y)
            else:
                out.append(x)
        # extra child properties
        idx = max(i for i, x in enumerate(out) if isinstance(x, list) and x and x[0] == 'property')
        for p in child_props.values():
            idx += 1
            out.insert(idx, p)
        return out
    s[1] = lib + ':' + name
    return s

def pins(sym):
    """List of dicts: number, name, x, y, angle, length, type, unit."""
    res = []
    base = sym[1].split(':', 1)[-1]
    for u in findall(sym, 'symbol'):
        parts = u[1][len(base) + 1:].split('_') if u[1].startswith(base + '_') else ['0', '0']
        unit = int(parts[0]) if parts[0].isdigit() else 0
        for p in findall(u, 'pin'):
            at = find(p, 'at')
            res.append(dict(number=find(p, 'number')[1], name=find(p, 'name')[1],
                            x=float(at[1]), y=float(at[2]), angle=float(at[3]) if len(at) > 3 else 0.0,
                            length=float(find(p, 'length')[1]), type=str(p[1]), unit=unit))
    return res
