#!/usr/bin/env python3
"""Generate E0001_fader_driver.kicad_sch (single A3 sheet).

Deterministic UUIDs (uuid5 of names) so the PCB stays linked when re-run.
"""
import sys, os, uuid, math, copy
sys.path.insert(0, os.path.dirname(__file__))
from sexp import Sym, dump, find, findall
import symlib

PROJ = '/home/karpulis/KiCad/E0001 - fader driver board'
NAME = 'E0001_fader_driver'
NS = uuid.UUID('6f0a3c1e-2b7d-4f7e-9a51-0e0001fade00')

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
C_TOUCH = (140, 0, 180)
C_SWD = (0, 125, 135)
C_MISC = (110, 80, 40)
C_PWR = (190, 0, 90)

NET_COLOR = {
    'I2C_SCL': C_I2C, 'I2C_SDA': C_I2C,
    'MOT_IN1': C_MOTCTL, 'MOT_IN2': C_MOTCTL, 'MOT_nSLEEP': C_MOTCTL,
    'MOTOR_P': C_MOTOUT, 'MOTOR_N': C_MOTOUT,
    'FADER_POS': C_ANA, 'FADER_WIPER': C_ANA, 'POT_HI': C_ANA,
    'VSENSE': C_PWR, 'VIN': C_PWR, 'LDO_IN': C_PWR,
    'TOUCH_SNS': C_TOUCH, 'TOUCH_DRV': C_TOUCH, 'TOUCH_ELEC': C_TOUCH,
    'SWDIO': C_SWD, 'SWCLK': C_SWD, 'NRST': C_SWD,
    'ADDR0': C_MISC, 'ADDR1': C_MISC, 'ADDR2': C_MISC, 'LED': C_MISC,
}

# ---------------------------------------------------------------- state
lib_cache = {}
symbols = []      # instance s-exprs
items = []        # wires, labels, junctions, etc.
inst = {}         # ref -> dict(x,y,rot,mirror,sym)
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

def pin(ref, num):
    d = inst[ref]
    for p in symlib.pins(d['sym']):
        if p['number'] == num:
            return xform(p['x'], p['y'], d['x'], d['y'], d['rot'], d['mirror'])
    raise KeyError(ref + '.' + num)

def prop(name, value, x, y, rot=0, hide=False, justify=None, size=1.27):
    return [S('property'), name, value, [S('at'), x, y, rot], effects(size, justify, hide)]

def place(lib_id, ref, value, x, y, rot=0, mirror=None, fp='', ds='~', desc='',
          refpos=None, valpos=None, extra=None, dnp=False, in_bom=True, on_board=True, unit=1,
          fields_hidden=True, hide_value=False):
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
          [S('on_board'), S('yes' if on_board else 'no')], [S('dnp'), S('yes' if dnp else 'no')],
          [S('uuid'), U('sym', ref)]]
    rx, ry, rr, rj = refpos if refpos else (x, y - 5, 0, None)
    vx, vy, vr, vj = valpos if valpos else (x, y + 5, 0, None)
    fa = 90 if rot in (90, 270) else 0
    if rot in (90, 180):
        rj = vj = None   # KiCad flips justification for these; keep centred
    e.append(prop('Reference', ref, rx, ry, fa, hide=ispower, justify=rj))
    e.append(prop('Value', value, vx, vy, fa, hide=hide_value, justify=vj))
    e.append(prop('Footprint', fp, x, y, 0, hide=True))
    e.append(prop('Datasheet', ds, x, y, 0, hide=True))
    e.append(prop('Description', desc, x, y, 0, hide=True))
    for k, v in (extra or {}).items():
        e.append(prop(k, v, x, y, 0, hide=True))
    for p in symlib.pins(sym):
        e.append([S('pin'), p['number'], [S('uuid'), U('pin', ref, p['number'])]])
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
            st = [S('stroke'), [S('width'), 0], [S('type'), S('default')],
                  [S('color'), color[0], color[1], color[2], 1]]
        items.append([S('wire'), [S('pts'), [S('xy'), a[0], a[1]], [S('xy'), b[0], b[1]]], st,
                      [S('uuid'), U('wire', a, b)]])

def label(name, p, side='right'):
    """Local label whose connection point is p. side = direction the text runs."""
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

def power(kind, p, value=None):
    """kind: 'gnd' (points down), 'vdd' (points up, value = net name), 'flag'."""
    pwr_count[0] += 1
    ref = '#PWR%02d' % pwr_count[0] if kind != 'flag' else '#FLG%02d' % pwr_count[0]
    if kind == 'gnd':
        place('power:GND', ref, 'GND', p[0], p[1], 0, valpos=(p[0], p[1] + 3.81, 0, None))
    elif kind == 'vdd':
        place('power:VDD', ref, value, p[0], p[1], 0, valpos=(p[0], p[1] - 3.556, 0, None))
    elif kind == 'flag':
        place('power:PWR_FLAG', ref, 'PWR_FLAG', p[0], p[1], 0, valpos=(p[0], p[1] - 3.81, 0, None))

def rect(x1, y1, x2, y2, color, title):
    items.append([S('rectangle'), [S('start'), x1, y1], [S('end'), x2, y2],
                  [S('stroke'), [S('width'), 0.3], [S('type'), S('dash')], [S('color'), color[0], color[1], color[2], 1]],
                  [S('fill'), [S('type'), S('color')], [S('color'), color[0], color[1], color[2], 0.06]],
                  [S('uuid'), U('rect', title)]])
    text(title, x1 + 2.54, y1 + 4.5, size=2.2, bold=True, color=color)

def text(s, x, y, size=1.27, bold=False, color=None):
    items.append([S('text'), s, [S('exclude_from_sim'), S('no')], [S('at'), x, y, 0],
                  effects(size, 'left bottom', bold=bold, color=color), [S('uuid'), U('text', s, x, y)]])

# convenience for 2-pin passives -------------------------------------------
R_FP = 'Resistor_SMD:R_0402_1005Metric'
C_FP = 'Capacitor_SMD:C_0402_1005Metric'

def R(ref, val, x, y, horiz=False, fp=R_FP, dnp=False, extra=None):
    if horiz:
        return place('Device:R_Small_US', ref, val, x, y, 90, fp=fp, dnp=dnp, extra=extra,
                     refpos=(x, y - 2.54, 0, None), valpos=(x, y + 2.794, 0, None))
    return place('Device:R_Small_US', ref, val, x, y, 0, fp=fp, dnp=dnp, extra=extra,
                 refpos=(x + 1.778, y - 0.635, 0, 'left'), valpos=(x + 1.778, y + 1.905, 0, 'left'))

def C(ref, val, x, y, horiz=False, fp=C_FP, dnp=False, extra=None):
    if horiz:
        return place('Device:C_Small', ref, val, x, y, 90, fp=fp, dnp=dnp, extra=extra,
                     refpos=(x, y - 2.794, 0, None), valpos=(x, y + 3.048, 0, None))
    return place('Device:C_Small', ref, val, x, y, 0, fp=fp, dnp=dnp, extra=extra,
                 refpos=(x + 1.778, y - 0.635, 0, 'left'), valpos=(x + 1.778, y + 1.905, 0, 'left'))

def gnd_under(ref, num='2'):
    p = pin(ref, num)
    power('gnd', p)

# =========================================================================
# A. Power input and protection           (A4 sheet)
# =========================================================================
rect(12.7, 12.7, 116.84, 78.74, C_PWR, 'POWER INPUT, PROTECTION, SUPPLY SENSE')
text('J1: JST GH 1.25 mm, Dronecode/Pixhawk I2C pinout: 1 = +5 V, 2 = SCL, 3 = SDA, 4 = GND', 15.24, 76.2, 1.27)

place('Connector_Generic_MountingPin:Conn_01x04_MountingPin', 'J1', 'JST GH SM04B-GHS-TB',
      25.4, 40.64, 0, mirror='y',
      fp='Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal',
      ds='https://www.jst-mfg.com/product/pdf/eng/eGH.pdf',
      desc='Power + I2C input, JST GH 4-pin horizontal (side entry) SMD',
      refpos=(15.24, 29.21, 0, 'right'), valpos=(15.24, 31.75, 0, 'right'),
      extra={'MPN': 'SM04B-GHS-TB(LF)(SN)', 'Manufacturer': 'JST'})
j1 = {n: pin('J1', n) for n in ['1', '2', '3', '4', 'MP']}
place('Transistor_FET:AO3401A', 'Q1', 'AO3401A', 53.34, 40.64, 90,
      refpos=(53.34, 31.75, 0, None), valpos=(53.34, 34.29, 0, None),
      desc='P-MOSFET, reverse-polarity protection (body diode conducts, channel enhances when VIN is correct)',
      extra={'MPN': 'AO3401A', 'Manufacturer': 'Alpha & Omega'})
qd, qs, qg = pin('Q1', '3'), pin('Q1', '2'), pin('Q1', '1')
wire(j1['1'], qd, net='VIN')
label('VIN', (33.02, j1['1'][1]), 'right')
power('flag', (43.18, j1['1'][1]))
junction((43.18, j1['1'][1]))
for n, net in (('2', 'I2C_SCL'), ('3', 'I2C_SDA')):
    wire(j1[n], (38.1, j1[n][1]), net=net)
    label(net, (38.1, j1[n][1]), 'right')
g4 = (33.02, j1['4'][1])
wire(j1['4'], g4, (33.02, 55.88))
wire(j1['MP'], (j1['MP'][0], 55.88), (33.02, 55.88))
junction((33.02, 55.88))
wire((33.02, 55.88), (33.02, 58.42))
power('gnd', (33.02, 58.42))
wire((33.02, 55.88), (38.1, 55.88))
power('flag', (38.1, 55.88))
R('R1', '10k', qg[0], qg[1] + 5.08)
wire(qg, pin('R1', '1'))
gnd_under('R1')
# protected +5V rail
ry_ = qs[1]
place('Diode:SMF5V0A', 'D1', 'SMF5V0A', 66.04, ry_ + 6.35, 270,
      refpos=(68.58, ry_ + 5.715, 0, 'left'), valpos=(68.58, ry_ + 8.255, 0, 'left'),
      desc='TVS 5 V standoff, 200 W, on protected +5 V rail')
C('C1', '10uF', 78.74, ry_ + 5.08, fp='Capacitor_SMD:C_0805_2012Metric', extra={'Voltage': '10V', 'Dielectric': 'X5R'})
wire(qs, (101.6, ry_))
wire((66.04, ry_), pin('D1', '1')); junction((66.04, ry_))
power('gnd', pin('D1', '2'))
wire((78.74, ry_), pin('C1', '1')); junction((78.74, ry_))
gnd_under('C1')
power('vdd', (83.82, ry_), '+5V'); junction((83.82, ry_))
power('flag', (91.44, ry_)); junction((91.44, ry_))
# supply sense divider
R('R8', '100k', 101.6, ry_ + 5.08)
wire((101.6, ry_), pin('R8', '1'))
R('R9', '100k', 101.6, ry_ + 15.24)
wire(pin('R8', '2'), pin('R9', '1'), net='VSENSE')
gnd_under('R9')
nd = (101.6, ry_ + 10.16)
junction(nd)
place('Device:C_Small', 'C9', '100nF', 93.98, nd[1] + 5.08, 0, fp=C_FP,
      refpos=(92.202, nd[1] + 4.445, 0, 'right'), valpos=(92.202, nd[1] + 6.985, 0, 'right'))
wire(nd, (93.98, nd[1]), (88.9, nd[1]), net='VSENSE')
wire((93.98, nd[1]), pin('C9', '1'), net='VSENSE'); junction((93.98, nd[1]))
gnd_under('C9')
label('VSENSE', (88.9, nd[1]), 'left')
text('VSENSE = +5 V / 2  (PA4)', 86.36, 67.31, 1.27, color=C_PWR)

# =========================================================================
# B. 3.3 V LDO
# =========================================================================
rect(119.38, 12.7, 180.34, 78.74, C_PWR, '3.3 V LDO')
yl = 40.64
power('vdd', (123.19, yl), '+5V')
R('R2', '10R', 127.0, yl, horiz=True, fp='Resistor_SMD:R_0603_1608Metric')
wire((123.19, yl), pin('R2', '1'))
place('Regulator_Linear:MCP1703Ax-330xxTT', 'U2', 'MCP1703A-3302E/CB', 157.48, yl, 0,
      refpos=(157.48, yl - 10.16, 0, None), valpos=(157.48, yl - 7.62, 0, None),
      extra={'MPN': 'MCP1703AT-3302E/CB', 'Manufacturer': 'Microchip'})
vi, vo, ug = pin('U2', '3'), pin('U2', '2'), pin('U2', '1')
wire(pin('R2', '2'), vi, net='LDO_IN')
label('LDO_IN', (130.81, yl), 'right')
C('C2', '4.7uF', 140.97, yl + 5.08, fp='Capacitor_SMD:C_0603_1608Metric', extra={'Voltage': '10V', 'Dielectric': 'X5R'})
wire((140.97, yl), pin('C2', '1')); junction((140.97, yl))
gnd_under('C2')
power('flag', (146.05, yl)); junction((146.05, yl))
power('gnd', ug)
C('C3', '1uF', 170.18, yl + 5.08, extra={'Voltage': '10V', 'Dielectric': 'X5R'})
wire(vo, (176.53, yl))
wire((170.18, yl), pin('C3', '1')); junction((170.18, yl))
gnd_under('C3')
power('vdd', (176.53, yl), '+3V3')
text('10R + 4.7uF: keeps motor PWM', 121.92, 69.85, 1.27)
text('ripple out of the LDO.', 121.92, 72.39, 1.27)
text('MCP1703A: 16 V max in, 2 uA Iq', 121.92, 74.93, 1.27)

# =========================================================================
# C. Motor driver
# =========================================================================
rect(182.88, 12.7, 284.48, 78.74, C_MOTOUT, 'MOTOR DRIVER (DRV8210P, DRV8837-compatible, motor from +5 V)')
xu3, yu3 = 231.14, 45.72
place('Driver_Motor:DRV8837', 'U3', 'DRV8210PDSGR', xu3, yu3, 0,
      refpos=(222.25, 53.34, 0, 'right'), valpos=(222.25, 55.88, 0, 'right'),
      extra={'MPN': 'DRV8210PDSGR', 'Manufacturer': 'Texas Instruments'})
vm, vcc = pin('U3', '1'), pin('U3', '8')
for n, net in (('6', 'MOT_IN1'), ('5', 'MOT_IN2'), ('7', 'MOT_nSLEEP')):
    p = pin('U3', n)
    wire(p, (p[0] - 7.62, p[1]), net=net)
    label(net, (p[0] - 7.62, p[1]), 'left')
power('gnd', pin('U3', '4'))
top = 25.4
wire(vm, (vm[0], top)); wire(vcc, (vcc[0], top))
wire((215.9, top), (269.24, top))
junction((vm[0], top)); junction((vcc[0], top))
power('vdd', (215.9, top), '+5V')
for i, (ref, val, fp) in enumerate([('C13', '100nF', C_FP), ('C10', '100nF', C_FP),
                                    ('C11', '22uF', 'Capacitor_SMD:C_0805_2012Metric'),
                                    ('C12', '22uF', 'Capacitor_SMD:C_0805_2012Metric')]):
    xc = 238.76 + i * 10.16
    C(ref, val, xc, top + 5.08, fp=fp, extra=({'Voltage': '10V', 'Dielectric': 'X5R'} if val == '22uF' else None))
    wire((xc, top), pin(ref, '1'))
    if xc != 269.24:
        junction((xc, top))
    gnd_under(ref)
o1, o2 = pin('U3', '2'), pin('U3', '3')
wire(o1, (256.54, o1[1]), net='MOTOR_N'); label('MOTOR_N', (256.54, o1[1]), 'right')
wire(o2, (256.54, o2[1]), net='MOTOR_P'); label('MOTOR_P', (256.54, o2[1]), 'right')
C('C14', '10nF', 248.92, o2[1] + 5.08, dnp=True)
wire((248.92, o2[1]), pin('C14', '1'), net='MOTOR_P'); junction((248.92, o2[1]))
wire(pin('C14', '2'), (248.92, 53.34), (256.54, 53.34), net='MOTOR_N')
label('MOTOR_N', (256.54, 53.34), 'right')
text('C13 = VCC, C10-C12 = VM decoupling. C14 not fitted (brush-noise option).', 185.42, 67.31, 1.27)
text('IN2 = PWM, IN1 = 0: M+ positive, knob moves to the top of travel (ALPS).', 185.42, 70.485, 1.27)
text('IN1 = PWM, IN2 = 0: knob moves down.  IN1 = IN2 = 1: brake.', 185.42, 73.66, 1.27)

# =========================================================================
# D. MCU
# =========================================================================
rect(12.7, 81.28, 167.64, 196.85, C_I2C, 'MCU STM32C051F6P6')
xu1, yu1 = 91.44, 137.16
place('E0001:STM32C051F6Px', 'U1', 'STM32C051F6P6', xu1, yu1, 0,
      refpos=(76.2, 111.76, 0, 'left'), valpos=(76.2, 114.3, 0, 'left'),
      extra={'MPN': 'STM32C051F6P6', 'Manufacturer': 'STMicroelectronics'})
P = lambda n: pin('U1', n)
for n, net in {'7': 'TOUCH_SNS', '8': 'TOUCH_DRV', '9': 'POT_HI', '10': 'FADER_POS', '11': 'VSENSE',
               '12': 'LED', '13': 'MOT_IN1', '14': 'MOT_IN2', '15': 'MOT_nSLEEP', '16': 'ADDR0',
               '17': 'ADDR1', '18': 'SWDIO', '19': 'SWCLK'}.items():
    p = P(n)
    wire(p, (p[0] + 5.08, p[1]), net=net)
    label(net, (p[0] + 5.08, p[1]), 'right')
for n, net in {'20': 'I2C_SCL', '1': 'I2C_SDA', '2': 'ADDR2', '6': 'NRST'}.items():
    p = P(n)
    wire(p, (p[0] - 5.08, p[1]), net=net)
    label(net, (p[0] - 5.08, p[1]), 'left')
noconnect(P('3'))
vdd = P('4')
rt = 101.6
wire(vdd, (vdd[0], rt), (vdd[0] + 20.32, rt))
junction((vdd[0], rt)); junction((vdd[0] + 10.16, rt))
power('vdd', (vdd[0], rt), '+3V3')
for i, (ref, val, fp) in enumerate([('C4', '100nF', C_FP), ('C5', '4.7uF', 'Capacitor_SMD:C_0603_1608Metric')]):
    xc = vdd[0] + 10.16 + i * 10.16
    C(ref, val, xc, rt + 5.08, fp=fp, extra=({'Voltage': '10V', 'Dielectric': 'X5R'} if val == '4.7uF' else None))
    wire((xc, rt), pin(ref, '1'))
    gnd_under(ref)
power('gnd', P('5'))

# SWD: Tag-Connect TC2030-NL pads
text('SWD (Tag-Connect TC2030-NL pads)', 17.78, 153.67, 1.27, color=C_SWD)
xj2, yj2 = 35.56, 172.72
place('Connector:Conn_ARM_SWD_TagConnect_TC2030', 'J2', 'TC2030-IDC-NL', xj2, yj2, 0,
      fp='Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical',
      refpos=(24.13, 167.64, 0, 'left'), valpos=(24.13, 190.5, 0, 'left'),
      desc='SWD programming/debug pads for Tag-Connect TC2030-IDC-NL cable', in_bom=False)
for n, net in (('4', 'SWCLK'), ('2', 'SWDIO')):
    p = pin('J2', n)
    wire(p, (p[0] + 5.08, p[1]), net=net)
    label(net, (p[0] + 5.08, p[1]), 'right')
pr_ = pin('J2', '3')
wire(pr_, (58.42, pr_[1]), net='NRST')
label('NRST', (48.26, pr_[1]), 'right')
C('C6', '100nF', 58.42, pr_[1] + 5.08)
wire((58.42, pr_[1]), pin('C6', '1'), net='NRST')
gnd_under('C6')
noconnect(pin('J2', '6'))
p = pin('J2', '1')
wire(p, (p[0], p[1] - 2.54))
power('vdd', (p[0], p[1] - 2.54), '+3V3')
power('gnd', pin('J2', '5'))

# I2C pull-ups live on the host (bus master); none on the fader boards
text('I2C pull-ups: on the host side', 17.78, 91.44, 1.27, color=C_I2C)
text('(2.2k-4.7k to the bus logic level; SDA/SCL', 17.78, 93.98, 1.27, color=C_I2C)
text('pins are 5 V tolerant, 3.3 V or 5 V bus OK)', 17.78, 96.52, 1.27, color=C_I2C)

# Status LED
text('Status LED', 137.16, 91.44, 1.27, color=C_MISC)
label('LED', (139.7, 99.06), 'left')
R('R10', '1k', 144.78, 99.06, horiz=True)
wire((139.7, 99.06), pin('R10', '1'), net='LED')
place('Device:LED_Small', 'D3', 'green', 152.4, 99.06, 180,
      fp='LED_SMD:LED_0603_1608Metric', refpos=(152.4, 96.52, 0, None), valpos=(152.4, 101.854, 0, None))
wire(pin('R10', '2'), pin('D3', '2'))
k = pin('D3', '1')
wire(k, (157.48, k[1]), (157.48, 101.6))
power('gnd', (157.48, 101.6))

# Address jumpers
text('I2C address select:', 132.08, 158.75, 1.27, color=C_MISC)
text('open = 1, bridged = 0', 132.08, 161.29, 1.27, color=C_MISC)
for i, (ref, net) in enumerate((('JP1', 'ADDR0'), ('JP2', 'ADDR1'), ('JP3', 'ADDR2'))):
    y = 168.91 + i * 7.62
    place('Jumper:SolderJumper_2_Open', ref, net, 152.4, y, 0,
          fp='Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm',
          refpos=(152.4, y - 2.54, 0, None), valpos=(152.4, y + 2.54, 0, None), in_bom=False, hide_value=True)
    a, b = pin(ref, '1'), pin(ref, '2')
    wire(a, (a[0] - 5.08, a[1]), net=net)
    label(net, (a[0] - 5.08, a[1]), 'left')
    wire(b, (162.56, b[1]))
    if i > 0:
        junction((162.56, b[1]))
wire((162.56, 168.91), (162.56, 186.69))
power('gnd', (162.56, 186.69))

# =========================================================================
# E. Fader interface
# =========================================================================
rect(170.18, 81.28, 284.48, 162.56, C_ANA, 'FADER: POSITION, TOUCH, MOTOR (ALPS RSA0N11M9A0J)')
xf, yf = 205.74, 121.92
place('Fader:ALPS_RSA0N11M9A0J', 'RV1', 'RSA0N11M9A0J B10K', xf, yf, 0,
      refpos=(195.58, 119.38, 0, 'right'), valpos=(195.58, 121.92, 0, 'right'),
      desc='Motorized touch-sensitive fader, 100 mm, 10k linear, 10 V motor (clone of ALPS RSA0N11M9A0J)')
pt, pb, pw, ptc, pfg = pin('RV1', '3'), pin('RV1', '1'), pin('RV1', '2'), pin('RV1', 'T'), pin('RV1', 'FG')
pmp, pmn = pin('RV1', 'M+'), pin('RV1', 'M-')
wire(pt, (pt[0], 106.68), net='POT_HI'); label('POT_HI', (pt[0], 106.68), 'up')
wire(pmp, (pmp[0], 109.22), (190.5, 109.22), net='MOTOR_P'); label('MOTOR_P', (190.5, 109.22), 'left')
wire(pmn, (pmn[0], 134.62), (190.5, 134.62), net='MOTOR_N'); label('MOTOR_N', (190.5, 134.62), 'left')
wire(pb, (pb[0], 133.35)); power('gnd', (pb[0], 133.35))
wire(pfg, (pfg[0], 133.35)); power('gnd', (pfg[0], 133.35))
# touch network
yt = 106.68
wire(ptc, (215.9, ptc[1]), (215.9, yt), (238.76, yt), net='TOUCH_ELEC')
label('TOUCH_ELEC', (216.535, yt), 'right')
place('Diode:PESD5V0L1UL', 'D2', 'PESD5V0L1UL', 231.14, yt + 3.81, 270,
      refpos=(233.68, yt + 3.175, 0, 'left'), valpos=(233.68, yt + 5.715, 0, 'left'),
      desc='Low-capacitance ESD diode on the touch line (knob is user-accessible)')
junction((231.14, yt))
power('gnd', pin('D2', '2'))
R('R5', '4.7k', 241.3, yt, horiz=True)
wire(pin('R5', '2'), (256.54, yt), net='TOUCH_SNS')
label('TOUCH_SNS', (256.54, yt), 'right')
R('R6', '1M', 248.92, 101.6)
wire(pin('R6', '2'), (248.92, yt), net='TOUCH_SNS'); junction((248.92, yt))
wire(pin('R6', '1'), (248.92, 96.52), (254.0, 96.52), net='TOUCH_DRV')
label('TOUCH_DRV', (254.0, 96.52), 'right')
# wiper filter
R('R7', '1k', 238.76, pw[1], horiz=True)
wire(pw, pin('R7', '1'), net='FADER_WIPER')
label('FADER_WIPER', (214.63, pw[1]), 'right')
wire(pin('R7', '2'), (251.46, pw[1]), net='FADER_POS')
C('C7', '100nF', 246.38, pw[1] + 5.08)
wire((246.38, pw[1]), pin('C7', '1'), net='FADER_POS'); junction((246.38, pw[1]))
gnd_under('C7')
label('FADER_POS', (251.46, pw[1]), 'right')
text('Touch: conductive knob -> lever -> T. Sense by RC charge time (PA1 drives via 1M,', 172.72, 143.51, 1.27, color=C_TOUCH)
text('TIM2 capture on PA0) or by ADC charge sharing on PA0.', 172.72, 146.05, 1.27, color=C_TOUCH)
text('Position: track powered from POT_HI (PA2 high), wiper read on PA3 (ratiometric).', 172.72, 150.495, 1.27, color=C_ANA)
text('End 1 (bottom of travel) = GND, so FADER_POS rises toward the top.', 172.72, 153.035, 1.27, color=C_ANA)
text('FG = fader frame lugs: soldered for retention, tied to GND.', 172.72, 157.48, 1.27, color=C_ANA)

# =========================================================================
# purchasing data (manufacturer part numbers for the Farnell BOM)
BOM_MPN = {   # ref: (MPN, manufacturer, DigiKey LV part number) - all checked in stock at digikey.lv 2026-10-07
    'C1': ('CL21A106KPCLQNC', 'Samsung', '1276-2402-1-ND'),
    'C2': ('GRM188R61E475KE11D', 'Murata', '490-7203-1-ND'), 'C5': ('GRM188R61E475KE11D', 'Murata', '490-7203-1-ND'),
    'C3': ('CL05A105KP5NNNC', 'Samsung', '1276-1076-1-ND'),
    'C4': ('CL05B104JO5NNNC', 'Samsung', '1276-1505-1-ND'), 'C6': ('CL05B104JO5NNNC', 'Samsung', '1276-1505-1-ND'),
    'C7': ('CL05B104JO5NNNC', 'Samsung', '1276-1505-1-ND'), 'C9': ('CL05B104JO5NNNC', 'Samsung', '1276-1505-1-ND'),
    'C10': ('CL05B104JO5NNNC', 'Samsung', '1276-1505-1-ND'), 'C13': ('CL05B104JO5NNNC', 'Samsung', '1276-1505-1-ND'),
    'C11': ('CL21A226MOQNNNE', 'Samsung', ''), 'C12': ('CL21A226MOQNNNE', 'Samsung', ''),
    'C14': ('GRM155R71H103KA88D', 'Murata', ''),
    'R1': ('RC0402FR-0710KL', 'Yageo', '311-10.0KLRCT-ND'), 'R2': ('RC0603FR-0710RL', 'Yageo', '311-10.0HRCT-ND'),
    'R5': ('RC0402FR-074K7L', 'Yageo', '311-4.7KLRCT-ND'), 'R6': ('RC0402FR-071ML', 'Yageo', '311-1.00MLRCT-ND'),
    'R7': ('RC0402FR-071KL', 'Yageo', '311-1.00KLRCT-ND'), 'R10': ('RC0402FR-071KL', 'Yageo', '311-1.00KLRCT-ND'),
    'R8': ('RC0402FR-07100KL', 'Yageo', '311-100KLRCT-ND'), 'R9': ('RC0402FR-07100KL', 'Yageo', '311-100KLRCT-ND'),
    'D1': ('SMF5.0A', 'Littelfuse', 'F5748CT-ND'), 'D2': ('PESD5V0L1UL,315', 'Nexperia', '1727-4193-1-ND'),
    'D3': ('LTST-C191KGKT', 'Lite-On', '160-1446-1-ND'),
    'Q1': ('AO3401A', 'Alpha & Omega', '785-1001-1-ND'),
    'U1': ('STM32C051F6P6', 'STMicroelectronics', '497-STM32C051F6P6-ND'),
    'U2': ('MCP1703AT-3302E/CB', 'Microchip', 'MCP1703AT-3302E/CBCT-ND'),
    'U3': ('DRV8210PDSGR', 'Texas Instruments', '296-DRV8210PDSGRCT-ND'),
}
for sym in symbols:
    ref = [p for p in sym if isinstance(p, list) and p and p[0] == 'property' and p[1] == 'Reference'][0][2]
    if ref in BOM_MPN:
        mpn, mfr, dk = BOM_MPN[ref]
        for k, v in (('MPN', mpn), ('Manufacturer', mfr), ('DigiKey', dk)):
            if not v:
                continue
            ex = [p for p in sym if isinstance(p, list) and p and p[0] == 'property' and p[1] == k]
            if ex:
                ex[0][2] = v
            else:
                at = [p for p in sym if isinstance(p, list) and p and p[0] == 'at'][0]
                idx = max(i for i, p in enumerate(sym) if isinstance(p, list) and p and p[0] == 'property')
                sym.insert(idx + 1, prop(k, v, at[1], at[2], 0, hide=True))

# =========================================================================
# write
# =========================================================================
lib_symbols = [S('lib_symbols')] + [lib_cache[k] for k in sorted(lib_cache)]
sch = [S('kicad_sch'), [S('version'), 20250114], [S('generator'), 'eeschema'], [S('generator_version'), '10.0'],
       [S('uuid'), ROOT_UUID], [S('paper'), 'A4'],
       [S('title_block'), [S('title'), 'E0001 Motorized fader driver board'], [S('date'), '2026-10-07'],
        [S('rev'), 'B'], [S('company'), ''],
        [S('comment'), 1, 'Fader: ALPS RSA0N11M9A0J (clone B0H45B29YK). 5 V + I2C on JST GH 4-pin.'],
        [S('comment'), 2, 'Rev B: STM32C051F6P6 MCU, cost-reduced parts (Farnell LV), 4-layer board.']],
       lib_symbols] + items + symbols + [
       [S('sheet_instances'), [S('path'), '/', [S('page'), '1']]],
       [S('embedded_fonts'), S('no')]]
out = os.path.join(PROJ, NAME + '.kicad_sch')
open(out, 'w').write(dump(sch) + '\n')
print('wrote', out, len(symbols), 'symbols', len(items), 'items')
