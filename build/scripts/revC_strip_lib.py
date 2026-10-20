"""shared s-expression helpers"""

def blocks(s):
    """yield (start, end) of each top-level child of (kicad_pcb ...)"""
    depth, i, start, n = 0, 0, None, len(s)
    instr = False
    while i < n:
        ch = s[i]
        if instr:
            if ch == '\\':
                i += 2
                continue
            if ch == '"':
                instr = False
        elif ch == '"':
            instr = True
        elif ch == '(':
            depth += 1
            if depth == 2:
                start = i
        elif ch == ')':
            if depth == 2:
                yield start, i + 1
            depth -= 1
        i += 1

