import re, sys
s = open(sys.argv[1]).read()
nets = sys.argv[2:]
for m in re.finditer(r'\n\t\(segment\s.*?\n\t\)', s, re.S):
    b = m.group(0)
    n = re.search(r'\(net "([^"]*)"', b).group(1)
    if nets and n not in nets: continue
    st = re.search(r'\(start ([^)]*)\)', b).group(1); en = re.search(r'\(end ([^)]*)\)', b).group(1)
    print(n, re.search(r'\(layer "([^"]*)"', b).group(1), st, '->', en, 'w', re.search(r'\(width ([^)]*)\)', b).group(1))
for m in re.finditer(r'\n\t\(via\s.*?\n\t\)', s, re.S):
    b = m.group(0); n = re.search(r'\(net "([^"]*)"', b).group(1)
    if nets and n not in nets: continue
    print(n, 'VIA', re.search(r'\(at ([^)]*)\)', b).group(1), re.search(r'\(size ([^)]*)\)', b).group(1))
