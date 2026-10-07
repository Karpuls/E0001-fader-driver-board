"""Minimal S-expression parser/serializer for KiCad files."""
import re

class Sym(str):
    """Bare (unquoted) atom."""
    pass

_tok = re.compile(r'\s*(\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+)', re.S)

def parse(text):
    stack = [[]]
    pos = 0
    n = len(text)
    while pos < n:
        m = _tok.match(text, pos)
        if not m:
            if text[pos:].strip() == '':
                break
            raise ValueError('parse error at %d' % pos)
        t = m.group(1)
        pos = m.end()
        if t == '(':
            stack.append([])
        elif t == ')':
            lst = stack.pop()
            stack[-1].append(lst)
        elif t.startswith('"'):
            s = t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
            stack[-1].append(s)
        else:
            stack[-1].append(Sym(t))
    return stack[0][0] if len(stack[0]) == 1 else stack[0]

def q(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'

def dump(e, indent=0):
    if isinstance(e, list):
        if not e:
            return '()'
        head = e[0]
        simple = all(not isinstance(x, list) for x in e)
        if simple and len(e) <= 8:
            return '(' + ' '.join(dump(x) for x in e) + ')'
        out = '(' + dump(head)
        for x in e[1:]:
            if isinstance(x, list):
                out += '\n' + '\t' * (indent + 1) + dump(x, indent + 1)
            else:
                out += ' ' + dump(x)
        out += '\n' + '\t' * indent + ')'
        return out
    if isinstance(e, Sym):
        return str(e)
    if isinstance(e, bool):
        return 'yes' if e else 'no'
    if isinstance(e, (int,)):
        return str(e)
    if isinstance(e, float):
        s = ('%.4f' % e).rstrip('0').rstrip('.')
        return s if s not in ('-0', '') else '0'
    return q(e)

def find(e, key):
    for x in e:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return None

def findall(e, key):
    return [x for x in e if isinstance(x, list) and x and x[0] == key]
