#!/usr/bin/env python3
"""Generate E0001_fader_driver.kicad_sch, rev C (single A3 sheet). Spec: docs/SPEC_revC.md v1.0.

Rev B generator is archived in archive/revB/scripts. Same UUID namespace as rev B, so unchanged
parts keep their UUIDs and stay linked to the PCB.
Most connections are short pin stubs ending in a net label or power symbol; grid = 2.54 mm.
"""
import sys, os, uuid, math
sys.path.insert(0, os.path.dirname(__file__))
from sexp import Sym, dump, find, findall
import symlib

PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
NAME = 'E0001_fader_driver'
NS = uuid.UUID('6f0a3c1e-2b7d-4f7e-9a51-0e0001fade00')
G = 2.54

def U(*parts):
    return str(uuid.uuid5(NS, '/'.join(str(p) for p in parts)))

ROOT_UUID = U('root')
S = Sym

def font(size=1.27, bold=False, color=None):
    f = [S('font'), [S('size'), size, size]]
    if bold:
        f.append([S('thickness'), round(size * 0.2, 3)])
        f.append([S('bold'), S('yes')])
    if color:
        f.append([S('color'), color[0], color[1], color[2], 1])
    return f

def effects(size=1.27, justify=None, hide=False, bold=False, color=None):
    e = [S('effects'), font(size, bold, color)]
    if justify:
        e.append([S('justify')] + [S(j) for j in justify.split()])
    if hide:
        e.append([S('hide'), S('yes')])
    return e

# ---------------------------------------------------------------- colours
C_I2C = (0, 84, 200)
C_MOTCTL = (205, 100, 0)
C_MOTOUT = (200, 0, 0)
C_ANA = (0, 135, 60)
C_ENC = (140, 0, 180)
C_SWD = (0, 125, 135)
C_MISC = (110, 80, 40)
C_PWR = (190, 0, 90)

NET_COLOR = {}
for n in ('I2C_SCL', 'I2C_SDA', 'J1_SCL', 'J1_SDA'):
    NET_COLOR[n] = C_I2C
for n in ('MOT_IN1', 'MOT_IN2', 'MOT_nSLEEP'):
    NET_COLOR[n] = C_MOTCTL
for n in ('MOTOR_P', 'MOTOR_N'):
    NET_COLOR[n] = C_MOTOUT
for n in ('FADER_POS', 'FADER_WIPER', 'TOUCH_SNS', 'TOUCH_DRV', 'TOUCH_ELEC'):
    NET_COLOR[n] = C_ANA
for n in ('UART_TX', 'UART_RX', 'NRST', 'BOOT0', 'J2_BOOT0', 'J2_NRST', 'J2_3V3'):
    NET_COLOR[n] = C_SWD
for n in ('ADDR0', 'ADDR1', 'ADDR2', 'LED', 'LED_A'):
    NET_COLOR[n] = C_MISC
for n in ('PBUS_IN', 'LDO_IN', 'EF_EN', 'EF_OVLO', 'EF_DVDT', 'EF_ITIMER', 'EF_ILM', 'ILM_ADC', 'VSENSE'):
    NET_COLOR[n] = C_PWR

POWER_NETS = {'GND', 'VM_P', '+3V3'}

# ---------------------------------------------------------------- state
lib_cache = {}
symbols = []
items = []
inst = {}
pwr_count = [0]

def libsym(lib_id):
    if lib_id not in lib_cache:
        lib, name = lib_id.split(':', 1)
        lib_cache[lib_id] = symlib.load(lib, name)
    return lib_cache[lib_id]

def xform(px, py, x, y, rot, mirror):
    if mirror == 'y':
        px = -px
    elif mirror == 'x':
        py = -py
    a = math.radians(rot)
    xr = px * math.cos(a) - py * math.sin(a)
    yr = px * math.sin(a) + py * math.cos(a)
    return (round(x + xr, 4), round(y - yr, 4))

def _pin(ref, num):
    d = inst[ref]
    for p in symlib.pins(d['sym']):
        if p['number'] == num:
            return p, d
    raise KeyError(ref + '.' + num)

def pin(ref, num):
    p, d = _pin(ref, num)
    return xform(p['x'], p['y'], d['x'], d['y'], d['rot'], d['mirror'])

def outward(ref, num):
    """Unit vector (schematic coords) pointing away from the symbol body at this pin."""
    p, d = _pin(ref, num)
    a = math.radians(p['angle'])
    inner = xform(p['x'] + math.cos(a), p['y'] + math.sin(a), d['x'], d['y'], d['rot'], d['mirror'])
    outer = xform(p['x'], p['y'], d['x'], d['y'], d['rot'], d['mirror'])
    return (round(outer[0] - inner[0]), round(outer[1] - inner[1]))

def prop(name, value, x, y, rot=0, hide=False, justify=None, size=1.27):
    return [S('property'), name, value, [S('at'), x, y, rot], effects(size, justify, hide)]

def place(lib_id, ref, value, x, y, rot=0, mirror=None, fp='', ds='~', desc='',
          refpos=None, valpos=None, extra=None, dnp=False, in_bom=True, on_board=True, unit=1,
          hide_value=False, alts=None, in_pos=True):
    sym = libsym(lib_id)
    pr = {p[1]: p for p in findall(sym, 'property')}
    if not fp and 'Footprint' in pr:
        fp = pr['Footprint'][2]
    if ds == '~' and 'Datasheet' in pr:
        ds = pr['Datasheet'][2]
    if not desc and 'Description' in pr:
        desc = pr['Description'][2]
    ispower = ref.startswith('#')
    e = [S('symbol'), [S('lib_id'), lib_id], [S('at'), x, y, rot]]
    if mirror:
        e.append([S('mirror'), S(mirror)])
    e += [[S('unit'), unit], [S('exclude_from_sim'), S('no')], [S('in_bom'), S('yes' if in_bom else 'no')],
          [S('on_board'), S('yes' if on_board else 'no')], [S('in_pos_files'), S('yes' if in_pos else 'no')],
          [S('dnp'), S('yes' if dnp else 'no')],
          [S('uuid'), U('sym', ref)]]
    rx, ry, rr, rj = refpos if refpos else (x, y - 5, 0, None)
    vx, vy, vr, vj = valpos if valpos else (x, y + 5, 0, None)
    if rot in (90, 180, 270):
        rj = vj = None
    fa = 90 if rot in (90, 270) else 0
    e.append(prop('Reference', ref, rx, ry, fa, hide=ispower, justify=rj))
    e.append(prop('Value', value, vx, vy, fa, hide=hide_value, justify=vj))
    e.append(prop('Footprint', fp, x, y, 0, hide=True))
    e.append(prop('Datasheet', ds, x, y, 0, hide=True))
    e.append(prop('Description', desc, x, y, 0, hide=True))
    for k, v in (extra or {}).items():
        e.append(prop(k, v, x, y, 0, hide=True))
    for p in symlib.pins(sym):
        pe = [S('pin'), p['number'], [S('uuid'), U('pin', ref, p['number'])]]
        if alts and p['number'] in alts:
            pe.append([S('alternate'), alts[p['number']]])
        e.append(pe)
    e.append([S('instances'), [S('project'), NAME, [S('path'), '/' + ROOT_UUID,
                                                    [S('reference'), ref], [S('unit'), unit]]]])
    symbols.append(e)
    inst[ref] = dict(x=x, y=y, rot=rot, mirror=mirror, sym=sym)
    return e

def wire(*pts, net=None):
    color = NET_COLOR.get(net)
    for a, b in zip(pts[:-1], pts[1:]):
        st = [S('stroke'), [S('width'), 0], [S('type'), S('default')]]
        if color:
            st.append([S('color'), color[0], color[1], color[2], 1])
        items.append([S('wire'), [S('pts'), [S('xy'), a[0], a[1]], [S('xy'), b[0], b[1]]], st,
                      [S('uuid'), U('wire', a, b)]])

def label(name, p, side='right'):
    rot = {'right': 0, 'up': 90, 'left': 180, 'down': 270}[side]
    just = {'right': 'left bottom', 'left': 'right bottom', 'up': 'left bottom', 'down': 'right bottom'}[side]
    items.append([S('label'), name, [S('at'), p[0], p[1], rot],
                  effects(1.27, just, color=NET_COLOR.get(name)),
                  [S('uuid'), U('label', name, p)]])

def junction(p):
    items.append([S('junction'), [S('at'), p[0], p[1]], [S('diameter'), 0], [S('color'), 0, 0, 0, 0],
                  [S('uuid'), U('junc', p)]])

def noconnect(p):
    items.append([S('no_connect'), [S('at'), p[0], p[1]], [S('uuid'), U('nc', p)]])

def power(net, p, flip=False):
    """Power symbol for a rail at point p. GND-type symbols point down, supplies point up."""
    pwr_count[0] += 1
    ref = '#PWR%03d' % pwr_count[0]
    if net in ('GND', 'GNDA'):
        place('power:' + net, ref, net, p[0], p[1], 0, valpos=(p[0], p[1] + 3.81, 0, None))
    else:
        place('power:VDD', ref, net, p[0], p[1], 180 if flip else 0,
              valpos=(p[0], p[1] + (3.556 if flip else -3.556), 0, None))

def flag(net, p):
    """PWR_FLAG at p, joined by a short wire down to a power symbol / label."""
    pwr_count[0] += 1
    place('power:PWR_FLAG', '#FLG%03d' % pwr_count[0], 'PWR_FLAG', p[0], p[1], 0,
          valpos=(p[0], p[1] - 3.81, 0, None))
    q = (p[0], p[1] + G)
    wire(p, q, net=net)
    if net in ('GND', 'GNDA'):
        power(net, q)
    elif net in POWER_NETS:
        power(net, q, flip=True)
    else:
        label(net, q, 'down')

SIDE = {(1, 0): 'right', (-1, 0): 'left', (0, -1): 'up', (0, 1): 'down'}

def net(ref, num, name, L=G):
    """Short stub from a pin, ending in a label or power symbol."""
    p = pin(ref, num)
    d = outward(ref, num)
    q = (round(p[0] + d[0] * L, 4), round(p[1] + d[1] * L, 4))
    wire(p, q, net=name)
    if name in ('GND', 'GNDA'):
        power(name, q)
    elif name in POWER_NETS:
        power(name, q, flip=(d == (0, 1)))
    else:
        label(name, q, SIDE[d])
    return q

def nc(ref, num):
    noconnect(pin(ref, num))

def rect(x1, y1, x2, y2, color, title):
    items.append([S('rectangle'), [S('start'), x1, y1], [S('end'), x2, y2],
                  [S('stroke'), [S('width'), 0.3], [S('type'), S('dash')], [S('color'), color[0], color[1], color[2], 1]],
                  [S('fill'), [S('type'), S('color')], [S('color'), color[0], color[1], color[2], 0.06]],
                  [S('uuid'), U('rect', title)]])
    text(title, x1 + 2.54, y1 + 4.5, size=2.2, bold=True, color=color)

def text(s, x, y, size=1.27, bold=False, color=None):
    items.append([S('text'), s, [S('exclude_from_sim'), S('no')], [S('at'), x, y, 0],
                  effects(size, 'left bottom', bold=bold, color=color), [S('uuid'), U('text', s, x, y)]])

def notes(lines, x, y, color=None, size=1.27):
    for i, s in enumerate(lines):
        text(s, x, y + i * 2.54, size, color=color)

# ---------------------------------------------------------------- 2-pin parts
R_FP = 'Resistor_SMD:R_0402_1005Metric'
C_FP = 'Capacitor_SMD:C_0402_1005Metric'
FP0603C = 'Capacitor_SMD:C_0603_1608Metric'
FP0805C = 'Capacitor_SMD:C_0805_2012Metric'

def two(lib_id, ref, val, x, y, n1, n2, fp, horiz=False, dnp=False, extra=None):
    """Two-pin part at grid (x, y); vertical: pin 1 top, horizontal: pin 1 left. Stubs to n1/n2."""
    X, Y = x * G, y * G
    if horiz:
        place(lib_id, ref, val, X, Y, 90, fp=fp, dnp=dnp, extra=extra,
              refpos=(X, Y - 2.54, 0, None), valpos=(X, Y + 2.794, 0, None))
    else:
        place(lib_id, ref, val, X, Y, 0, fp=fp, dnp=dnp, extra=extra,
              refpos=(X + 1.778, Y - 0.635, 0, 'left'), valpos=(X + 1.778, Y + 1.905, 0, 'left'))
    if n1:
        net(ref, '1', n1)
    if n2:
        net(ref, '2', n2)

def R(ref, val, x, y, n1, n2, fp=R_FP, **kw):
    two('Device:R_Small_US', ref, val, x, y, n1, n2, fp, **kw)

def C(ref, val, x, y, n1, n2, fp=C_FP, **kw):
    two('Device:C_Small', ref, val, x, y, n1, n2, fp, **kw)

V25 = {'Voltage': '25V'}
V50 = {'Voltage': '50V'}

def divider(rt, rb, vt, vb, x, y, ntop, nmid, nbot, side='right', L=2):
    """Vertical divider: top R at y, bottom R at y+5 (grid), mid node wired to a label."""
    R(rt, vt, x, y, ntop, None)
    R(rb, vb, x, y + 5, None, nbot)
    wire(pin(rt, '2'), pin(rb, '1'), net=nmid)
    m = (x * G, (y + 2.5) * G)
    junction(m)
    q = ((x + (L if side == 'right' else -L)) * G, m[1])
    wire(m, q, net=nmid)
    label(nmid, q, side)

def bat54w(ref, x, y, nA, nK, rot=180):
    """BAT54W, horizontal (rot 180: anode left, cathode right)."""
    place('Diode:BAT54W', ref, 'BAT54W', x * G, y * G, rot, fp='Package_TO_SOT_SMD:SOT-323_SC-70',
          refpos=(x * G, (y - 1.6) * G, 0, None), valpos=(x * G, (y + 1.6) * G, 0, None))
    net(ref, '1', nA)
    net(ref, '3', nK)
    nc(ref, '2')

def pesd(ref, x, y, nk, desc):
    place('Diode:PESD5V0L1UL', ref, 'PESD5V0L1UL', x * G, y * G, 270,
          refpos=((x + 1.5) * G, (y - 0.5) * G, 0, 'left'), valpos=((x + 1.5) * G, (y + 0.5) * G, 0, 'left'), desc=desc)
    net(ref, '1', nk)
    net(ref, '2', 'GND')

# =========================================================================
# A. Host connector J1, I2C ESD, eFuse U4
# =========================================================================
rect(1 * G, 2 * G, 76 * G, 46 * G, C_PWR, 'HOST J1 (PBUS v2 + I2C), eFUSE U4 TPS259470A')
place('Connector_Generic_MountingPin:Conn_01x04_MountingPin', 'J1', 'SM04B-GHS-TB', 7 * G, 16 * G, 0, mirror='y',
      fp='Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal',
      ds='https://www.jst-mfg.com/product/pdf/eng/eGH.pdf',
      desc='Host: PBUS v2 + I2C, JST GH 4-pin horizontal (1 PBUS, 2 SCL, 3 SDA, 4 GND)',
      refpos=(7 * G, 11 * G, 0, None), valpos=(7 * G, 12 * G, 0, None))
net('J1', '1', 'PBUS_IN', L=2 * G)
net('J1', '2', 'J1_SCL', L=2 * G)
net('J1', '3', 'J1_SDA', L=2 * G)
net('J1', '4', 'GND', L=8 * G)
net('J1', 'MP', 'GND')
pesd('D4', 18, 26, 'J1_SCL', 'I2C ESD at J1 (SCL)')
pesd('D5', 24, 26, 'J1_SDA', 'I2C ESD at J1 (SDA)')
R('R19', '0R', 31, 24, 'J1_SCL', 'I2C_SCL', horiz=True)
R('R20', '0R', 31, 28, 'J1_SDA', 'I2C_SDA', horiz=True)
notes(['J1: 1 PBUS 2 SCL 3 SDA 4 GND, MP = GND. Silk "PBUS 6-9 V".',
       'No I2C pull-ups here (host 4.7k). R19/R20 0R (<= 100R allowed).'], 2 * G, 40 * G, C_PWR)
C('C18', '4.7uF', 35, 10, 'PBUS_IN', 'GND', fp=FP0603C, extra=V25)
C('C17', '100nF', 39, 10, 'PBUS_IN', 'GND', extra=V50)
place('E0001:TPS259470L', 'U4', 'TPS259470ARPW', 56 * G, 14 * G, 0,
      refpos=(49 * G, 7.5 * G, 0, 'left'), valpos=(49 * G, 8.5 * G, 0, 'left'))
for n, nn in (('5', 'PBUS_IN'), ('1', 'EF_EN'), ('2', 'EF_OVLO'), ('7', 'EF_DVDT'), ('6', 'VM_P'), ('9', 'EF_ILM'),
              ('10', 'EF_ITIMER'), ('8', 'GND')):
    net('U4', n, nn, L=2 * G if n != '8' else G)
nc('U4', '3')
nc('U4', '4')
divider('R11', 'R12', '1M 1%', '330k 1%', 40, 20, 'PBUS_IN', 'EF_EN', 'GND')
divider('R13', 'R14', '1M 1%', '137k 1%', 46, 20, 'PBUS_IN', 'EF_OVLO', 'GND')
C('C16', '1.8nF', 52, 31, 'EF_DVDT', 'GND', extra=V50)
C('C15', '4.7nF', 56, 31, 'EF_ITIMER', 'GND', extra=V50)
R('R15', '5.23k 1%', 61, 31, 'EF_ILM', 'GND')
R('R16', '10k', 67, 28, 'EF_ILM', 'ILM_ADC', horiz=True)
C('C19', '1nF', 71, 32, 'ILM_ADC', 'GND', extra=V50)
flag('PBUS_IN', (24 * G, 10 * G))
notes(['U4 TPS259470A (auto-retry): UVLO 4.84/4.40 V, OVLO 9.96/9.05 V, I_LIM 3334/5.23k = 0.64 A (0.54-0.73 A),',
       'ITIMER 4.7 nF ~3.9 ms, dVdt 1.8 nF ~1.1 V/ms. Reverse blocking to -15 V, survives 11 V (OVLO off).',
       'ILM monitor 0.95 V/A -> R16 10k + C19 1 nF -> PA2. FLT and AUXOFF unused.'], 30 * G, 40 * G, C_PWR)

# =========================================================================
# B. VM_P bulk, TVS, PBUS sense, 3V3 LDO
# =========================================================================
rect(78 * G, 2 * G, 153 * G, 46 * G, C_PWR, 'VM_P (protected PBUS), PBUS SENSE, 3V3 LDO')
for i, ref in enumerate(('C1', 'C11', 'C12', 'C20')):
    C(ref, '10uF', 82 + 4 * i, 10, 'VM_P', 'GND', fp=FP0805C, extra=V25)
place('Diode:SMF9V0A', 'D1', 'SMF9.0A', 100 * G, 10 * G, 270, fp='Diode_SMD:D_SOD-123F',
      refpos=(101.5 * G, 9.5 * G, 0, 'left'), valpos=(101.5 * G, 10.5 * G, 0, 'left'),
      desc='TVS 9.0 V stand-off on VM_P (after the eFuse, not on PBUS_IN)')
net('D1', '1', 'VM_P')
net('D1', '2', 'GND')
divider('R8', 'R9', '100k', '30.1k 1%', 108, 8, 'VM_P', 'VSENSE', 'GND')
C('C9', '100nF', 114, 15, 'VSENSE', 'GND', extra=V50)
R('R2', '10R', 122, 10, 'VM_P', 'LDO_IN', fp='Resistor_SMD:R_0603_1608Metric')
C('C2', '4.7uF', 126, 16, 'LDO_IN', 'GND', fp=FP0603C, extra=V25)
place('Regulator_Linear:MCP1703Ax-330xxMB', 'U2', 'MCP1703AT-3302E/MB', 138 * G, 14 * G, 0,
      refpos=(138 * G, 9.5 * G, 0, None), valpos=(138 * G, 10.5 * G, 0, None))
net('U2', '2', 'LDO_IN', L=2 * G)
net('U2', '3', '+3V3', L=2 * G)
net('U2', '1', 'GND')
C('C5', '4.7uF', 146, 16, '+3V3', 'GND', fp=FP0603C, extra=V25)
C('C3', '1uF', 150, 16, '+3V3', 'GND')
flag('LDO_IN', (132 * G, 26 * G))
flag('GND', (146 * G, 26 * G))
notes(['VM_P bulk 4 x 10 uF 25 V (~45 uF total input incl. C18). D1 SMF9.0A clamps back-EMF on VM_P.',
       'VSENSE = VM_P x 30.1/130.1 -> PA4 (11 V -> 2.55 V). U2 MCP1703A SOT-89 from VM_P via R2 10R.',
       'J2 pin 2 (3V3) feeds LDO_IN through D7 BAT54W, so VOUT never exceeds VIN (MCP1703A abs max).'], 80 * G, 40 * G, C_PWR)

# =========================================================================
# C. MCU STM32C051F6P6
# =========================================================================
rect(1 * G, 48 * G, 76 * G, 113 * G, C_I2C, 'MCU STM32C051F6P6 (TSSOP-20)')
XU, YU = 34 * G, 80 * G
place('E0001:STM32C051F6Px', 'U1', 'STM32C051F6P6', XU, YU, 0,
      refpos=(XU + 9 * G, YU - 11 * G, 0, 'left'), valpos=(XU + 9 * G, YU - 10 * G, 0, 'left'))
for n, nn in {'1': 'I2C_SDA', '2': 'ADDR2', '3': 'ADDR1', '6': 'NRST', '20': 'I2C_SCL'}.items():
    net('U1', n, nn, L=2 * G)
for n, nn in {'7': 'TOUCH_SNS', '8': 'TOUCH_DRV', '9': 'ILM_ADC', '10': 'FADER_POS', '11': 'VSENSE', '12': 'LED',
              '13': 'MOT_IN1', '14': 'MOT_IN2', '15': 'MOT_nSLEEP', '16': 'UART_TX', '17': 'UART_RX',
              '18': 'ADDR0', '19': 'BOOT0'}.items():
    net('U1', n, nn, L=2 * G)
net('U1', '4', '+3V3')
net('U1', '5', 'GND')
C('C4', '100nF', 22, 54, '+3V3', 'GND', extra=V50)
C('C6', '100nF', 10, 72, 'NRST', 'GND', extra=V50)
R('R17', '10k', 62, 104, 'BOOT0', 'GND')
notes(['C4 at VDD (C3/C5 at the LDO). C6: NRST filter.',
       'Pins 16/17 = PA9/PA10 USART1 (ROM bootloader TX/RX),',
       'pin 19 = PA14-BOOT0 (R17 10k pull-down). Address 0x30 | ADDR,',
       'ADDRn = 1 when its jumper is open (internal pull-up).',
       'PA11/PA12/PA15/PB3-5/PB8 (bonded) stay inputs.'], 2 * G, 100 * G, C_I2C)
text('I2C address jumpers (bottom): open = 1', 2 * G, 86 * G, color=C_MISC)
for i, (ref, nn) in enumerate((('JP1', 'ADDR0'), ('JP2', 'ADDR1'), ('JP3', 'ADDR2'))):
    y = (89 + 3 * i) * G
    place('Jumper:SolderJumper_2_Open', ref, nn, 9 * G, y, 0, fp='Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm',
          refpos=(9 * G, y - 2.032, 0, None), valpos=(9 * G, y + 2.54, 0, None), in_bom=False, hide_value=True)
    net(ref, '1', nn, L=2 * G)
    net(ref, '2', 'GND')
# status LED
R('R10', '1k', 62, 54, 'LED', None, horiz=True)
place('Device:LED_Small', 'D3', 'green', 67 * G, 54 * G, 180, fp='LED_SMD:LED_0603_1608Metric',
      refpos=(67 * G, 52.5 * G, 0, None), valpos=(67 * G, 55.6 * G, 0, None))
wire(pin('R10', '2'), pin('D3', '2'), net='LED_A')
net('D3', '1', 'GND')

# =========================================================================
# D. Programming header J2 (STM32 ROM UART bootloader)
# =========================================================================
rect(78 * G, 48 * G, 120 * G, 113 * G, C_SWD, 'J2 UART BOOTLOADER HEADER (1x6 2.54 R/A)')
place('Connector_Generic:Conn_01x06', 'J2', '61300611021', 84 * G, 66 * G, 0, mirror='y',
      fp='Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Horizontal',
      desc='1x6 2.54 mm right-angle header: 1 GND, 2 3V3, 3 RX, 4 TX, 5 BOOT0, 6 NRST (3.3 V USB-UART adapter)',
      refpos=(84 * G, 58 * G, 0, None), valpos=(84 * G, 59 * G, 0, None))
net('J2', '1', 'GND', L=8 * G)
net('J2', '2', 'J2_3V3', L=2 * G)
net('J2', '3', 'UART_RX', L=2 * G)
net('J2', '4', 'UART_TX', L=2 * G)
net('J2', '5', 'J2_BOOT0', L=2 * G)
net('J2', '6', 'J2_NRST', L=2 * G)
bat54w('D7', 104, 76, 'J2_3V3', 'LDO_IN')
bat54w('D6', 104, 84, 'NRST', 'J2_NRST')
R('R18', '1k', 104, 92, 'J2_BOOT0', 'BOOT0', horiz=True)
notes(['Silk: GND 3V3 RX TX B0 RST, "UART boot 3.3 V".',
       'Pin 2: adapter 3V3 -> D7 -> LDO_IN (board ~2.9 V).',
       'Pin 6: D6 lets the adapter only pull NRST low.',
       'Pin 5: R18 1k series, R17 10k pull-down at PA14.',
       'Auto-boot: B0 high, pulse RST low, release.',
       'Option bytes at first flash: nBOOT_SEL=0,',
       'nBOOT1=1, BOOT_LOCK=0. No SWD, no test points.'], 79 * G, 99 * G, C_SWD)

# =========================================================================
# E. Motor driver + fader
# =========================================================================
rect(122 * G, 48 * G, 153 * G, 80 * G, C_MOTOUT, 'MOTOR DRIVER DRV8210P')
XD, YD = 136 * G, 63 * G
place('Driver_Motor:DRV8837', 'U3', 'DRV8210PDSGR', XD, YD, 0,
      refpos=(XD - 4 * G, YD + 4 * G, 0, 'right'), valpos=(XD - 4 * G, YD + 5 * G, 0, 'right'))
for n, nn in (('6', 'MOT_IN1'), ('5', 'MOT_IN2'), ('7', 'MOT_nSLEEP')):
    net('U3', n, nn, L=2 * G)
net('U3', '1', 'VM_P', L=5 * G)
net('U3', '8', '+3V3', L=2 * G)
net('U3', '4', 'GND')
net('U3', '2', 'MOTOR_N', L=2 * G)
net('U3', '3', 'MOTOR_P', L=2 * G)
C('C13', '100nF', 125, 53, 'VM_P', 'GND', extra=V50)
C('C10', '100nF', 149, 53, '+3V3', 'GND', extra=V50)
C('C14', '10nF', 149, 72, 'MOTOR_P', 'MOTOR_N', extra=V50, dnp=True)
notes(['VM = VM_P (<= 9 V), VCC = +3V3. C14 DNP.'], 123 * G, 78 * G, C_MOTOUT)

rect(122 * G, 82 * G, 153 * G, 113 * G, C_ANA, 'FADER RV1: TRACK, TOUCH, MOTOR')
XF, YF = 132 * G, 95 * G
place('Fader:ALPS_RSA0N11M9A0J', 'RV1', 'RSA0N11M9A0J B10K', XF, YF, 0,
      refpos=(XF - 3 * G, YF - 5 * G, 0, 'right'), valpos=(XF - 3 * G, YF - 4 * G, 0, 'right'),
      desc='Motorized touch-sensitive fader, 100 mm, 10k linear, 10 V motor (clone of ALPS RSA0N11M9A0J)')
net('RV1', '3', '+3V3')
net('RV1', '1', 'GND')
net('RV1', 'FG', 'GND')
net('RV1', 'M+', 'MOTOR_P', L=2 * G)
net('RV1', 'M-', 'MOTOR_N', L=2 * G)
net('RV1', '2', 'FADER_WIPER', L=2 * G)
net('RV1', 'T', 'TOUCH_ELEC', L=2 * G)
R('R7', '1k', 143, 104, 'FADER_WIPER', 'FADER_POS', horiz=True)
C('C7', '100nF', 149, 108, 'FADER_POS', 'GND', extra=V50)
pesd('D2', 143, 88, 'TOUCH_ELEC', 'Low-capacitance ESD diode on the touch line (knob is user-accessible)')
R('R5', '4.7k', 148, 86, 'TOUCH_ELEC', 'TOUCH_SNS', horiz=True)
R('R6', '1M', 149, 96, 'TOUCH_DRV', 'TOUCH_SNS')
notes(['Track top -> +3V3 (rev C), wiper R7/C7 -> PA3.', 'Touch: T -> D2, R5 -> PA0; R6 1M from PA1.'], 123 * G, 111 * G, C_ANA)

# =========================================================================
# purchasing data (SPEC_revC §11; Parts' BOM overrides when present)
# =========================================================================
import csv
BOM_BY_REF = {
    'U1': ('STM32C051F6P6', 'STMicroelectronics', '497-STM32C051F6P6-ND'),
    'U2': ('MCP1703AT-3302E/MB', 'Microchip', 'MCP1703AT-3302E/MBCT-ND'),
    'U3': ('DRV8210PDSGR', 'Texas Instruments', '296-DRV8210PDSGRCT-ND'),
    'U4': ('TPS259470ARPWR', 'Texas Instruments', '296-TPS259470ARPWRCT-ND'),
    'J1': ('SM04B-GHS-TB(LF)(SN)', 'JST', '455-1566-1-ND'),
    'J2': ('61300611021', 'Wurth Elektronik', '732-5339-ND'),
    'RV1': ('RSA0N11M9A0J B10K clone', 'Fastigeaty', 'ASIN B0H45B29YK'),
    'D1': ('SMF9.0A', 'Littelfuse', 'F5755CT-ND'),
    'D3': ('LTST-C191KGKT', 'Lite-On', '160-1446-1-ND'),
    'R2': ('RC0603FR-0710RL', 'Yageo', '311-10.0HRCT-ND'),
}
BOM_BY_VALUE = {
    'PESD5V0L1UL': ('PESD5V0L1UL,315', 'Nexperia', '1727-4193-1-ND'),
    'BAT54W': ('BAT54W,135', 'Nexperia', '1727-1869-1-ND'),
    '10uF': ('TMK212BBJ106MG-T', 'Taiyo Yuden', '587-6025-1-ND'),
    '4.7uF': ('GRM188R61E475KE11D', 'Murata', '490-7203-1-ND'),
    '1uF': ('CL05A105KP5NNNC', 'Samsung', '1276-1076-1-ND'),
    '100nF': ('GRM155R71H104KE14D', 'Murata', '490-10700-1-ND'),
    '10nF': ('GRM155R71H103KA88D', 'Murata', '490-4516-1-ND'),
    '4.7nF': ('GRM155R71H472KA01J', 'Murata', '490-8259-1-ND'),
    '1.8nF': ('C0402C182K5RACTU', 'KEMET', '399-C0402C182K5RACTUCT-ND'),
    '1nF': ('GRM155R71H102KA01D', 'Murata', '490-1303-1-ND'),
    '4.7k': ('RK73H1ETTP4701F', 'KOA', '2019-RK73H1ETTP4701FCT-ND'),
    '1M': ('RC0402FR-071ML', 'Yageo', '311-1.00MLRCT-ND'),
    '1M 1%': ('RC0402FR-071ML', 'Yageo', '311-1.00MLRCT-ND'),
    '1k': ('RC0402FR-071KL', 'Yageo', '311-1.00KLRCT-ND'),
    '100k': ('RC0402FR-07100KL', 'Yageo', '311-100KLRCT-ND'),
    '30.1k 1%': ('RC0402FR-0730K1L', 'Yageo', '311-30.1KLRCT-ND'),
    '330k 1%': ('RC0402FR-07330KL', 'Yageo', '311-330KLRCT-ND'),
    '137k 1%': ('RC0402FR-07137KL', 'Yageo', 'YAG2972CT-ND'),
    '5.23k 1%': ('RC0402FR-075K23L', 'Yageo', 'YAG3195CT-ND'),
    '10k': ('RC0402FR-0710KL', 'Yageo', '311-10.0KLRCT-ND'),
    '0R': ('RC0402JR-070RL', 'Yageo', '311-0.0JRCT-ND'),
}
PARTS = {}   # Parts' BOM (bom/E0001_revC_bom.csv) wins, per reference
_bp = os.path.join(PROJ, 'bom', 'E0001_revC_bom.csv')
if os.path.exists(_bp):
    import re as _re
    for r in csv.DictReader(open(_bp)):
        for rf in _re.split(r'[ ,;]+', r['References'].strip()):
            if rf and r.get('MPN'):
                PARTS[rf] = (r['MPN'], r['Manufacturer'], r['SupplierPN'], r['Supplier'])
report = []
for sym in symbols:
    props = {p[1]: p for p in sym if isinstance(p, list) and p and p[0] == 'property'}
    ref, val = props['Reference'][2], props['Value'][2]
    inbom = [x for x in sym if isinstance(x, list) and x and x[0] == 'in_bom'][0][1]
    if ref.startswith('#') or inbom == 'no':
        continue
    key = BOM_BY_REF.get(ref) or BOM_BY_VALUE.get(val)
    if ref in PARTS:
        if key and key[0] != PARTS[ref][0]:
            report.append('%s: spec %s -> Parts %s' % (ref, key[0], PARTS[ref][0]))
        key = PARTS[ref]
    if not key:
        report.append(ref + ' ' + val)
        continue
    at = [p for p in sym if isinstance(p, list) and p and p[0] == 'at'][0]
    idx = max(i for i, p in enumerate(sym) if isinstance(p, list) and p and p[0] == 'property')
    sup = key[3] if len(key) > 3 else ('DigiKey' if key[2].endswith('-ND') else 'other')
    for k, v in reversed((('MPN', key[0]), ('Manufacturer', key[1]), ('Supplier', sup), ('Supplier PN', key[2]))):
        sym.insert(idx + 1, prop(k, v, at[1], at[2], 0, hide=True))
for r_ in report:
    print('  BOM:', r_)

# =========================================================================
# write (shift inside the A3 frame)
# =========================================================================
OX, OY = 4 * G, 4 * G

def shift(e):
    if isinstance(e, list) and e:
        if e[0] in ('at', 'xy', 'start', 'end') and len(e) >= 3 and isinstance(e[1], (int, float)):
            e[1] = round(e[1] + OX, 4)
            e[2] = round(e[2] + OY, 4)
        else:
            for x in e[1:]:
                shift(x)

for e in items + symbols:
    shift(e)
lib_symbols = [S('lib_symbols')] + [lib_cache[k] for k in sorted(lib_cache)]
sch = [S('kicad_sch'), [S('version'), 20250114], [S('generator'), 'eeschema'], [S('generator_version'), '10.0'],
       [S('uuid'), ROOT_UUID], [S('paper'), 'User', 450, 350],
       [S('title_block'), [S('title'), 'E0001 Motorized fader driver board'], [S('date'), '2026-10-19'],
        [S('rev'), 'C'], [S('company'), ''],
        [S('comment'), 1, 'PBUS v2 (6-9 V) + I2C on JST GH 4p; eFuse TPS259470A; UART bootloader header J2'],
        [S('comment'), 2, 'Spec docs/SPEC_revC.md v1.0; generated by build/scripts/gen_sch.py']],
       lib_symbols] + items + symbols + [
       [S('sheet_instances'), [S('path'), '/', [S('page'), '1']]],
       [S('embedded_fonts'), S('no')]]
out = os.path.join(PROJ, NAME + '.kicad_sch')
open(out, 'w').write(dump(sch) + '\n')
print('wrote', out, len([s for s in symbols if not find(s, 'lib_id')[1].startswith('power:')]), 'parts')
