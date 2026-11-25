"""STC12C5A60S2 geliştirme kartı şeması (Rev A).

Çalıştırma:  pip install schemdraw  &&  python sema_ciz.py
Çıktı: bu klasöre 01..05 numaralı SVG dosyaları.
Bağlantılar etiket (net label) ile yapılır; aynı isimli etiketler aynı nettir.
Ayrıntılı pin tablosu: ../baglanti-listesi.md
"""
from pathlib import Path

import schemdraw
import schemdraw.elements as elm
from schemdraw.elements import IcPin

schemdraw.use('svg')
OUT = Path(__file__).parent
TW = 2.0  # etiket genişliği (en uzun net adı: VCC_MCU)
SUPPLIES = ('+5V', 'VCC_MCU', 'VBUS')


def new():
    d = schemdraw.Drawing(show=False)
    d.config(unit=2.2, fontsize=12, lw=1.4)
    return d


def tag(d, pt, name, side='right', lead=0.6):
    """pt noktasından kısa bir hat çekip net etiketi koyar."""
    ln = d.add(getattr(elm.Line().at(pt), side)(lead))
    d.add(getattr(elm.Tag(width=TW).at(ln.end), side)().label(name, fontsize=11))


def top(d, pt, name):
    """Dikey zincirin üst ucu: besleme sembolü ya da sinyal etiketi."""
    if name in SUPPLIES:
        d.add(elm.Vdd().at(pt).label(name, fontsize=11))
    else:
        d.add(elm.Line().at(pt).up(0.4))
        d.add(elm.Tag(width=TW).at((pt[0], pt[1] + 0.4)).up().label(name, fontsize=11, rotate=True))


def chain(d, x, y, head, parts, tail='GND'):
    """(x, y)'den aşağı doğru seri parça zinciri; altta GND ya da etiket."""
    top(d, (x, y), head)
    p = (x, y)
    for part in parts:
        p = d.add(part.at(p).down()).end
    if tail == 'GND':
        d.add(elm.Ground().at(p))
    elif tail in SUPPLIES:
        d.add(elm.Line().at(p).down(0.4))
        d.add(elm.Vdd().at((p[0], p[1] - 0.4)).down().label(tail, fontsize=11, loc='bottom'))
    elif tail:
        d.add(elm.Line().at(p).down(0.4))
        d.add(elm.Tag(width=TW).at((p[0], p[1] - 0.4)).down().label(tail, fontsize=11, rotate=True))
    return p


def title(d, x, y, text):
    d.add(elm.Label().at((x, y)).label(text, fontsize=15, halign='left'))


def ic(pins_left, pins_right, label, w=3.2, spacing=1.0):
    # schemdraw yan pinleri alttan üste dizer; listeler yukarıdan aşağıya yazılır
    pins = [IcPin(name=n, pin=p, side='L', anchorname=a) for p, n, a in reversed(pins_left)]
    pins += [IcPin(name=n, pin=p, side='R', anchorname=a) for p, n, a in reversed(pins_right)]
    nl, nr = len(pins_left), len(pins_right)
    h = max(nl, nr) * spacing + 1.0
    return elm.Ic(pins=pins, size=(w, h), pinspacing=spacing, edgepadH=0.5, leadlen=0.8).theta(0).label(label, loc='top', fontsize=12)


def save(d, name):
    d.save(str(OUT / name))
    print('yazildi', name)


# --------------------------------------------------------------- 1. USB + güç
d = new()
title(d, -2, 9.5, '1. USB-C, sigorta, ESD, güç LED')
J1 = d.add(ic([], [
    ('A4,B4,A9,B9', 'VBUS', 'VBUS'),
    ('A6,B6', 'D+', 'DP'),
    ('A7,B7', 'D-', 'DM'),
    ('A5', 'CC1', 'CC1'),
    ('B5', 'CC2', 'CC2'),
    ('A1,A12,B1,B12', 'GND', 'GND'),
], 'J1  USB-C (TYPE-C-31-M-12)', w=2.6, spacing=1.7).at((0, 0)))
v = d.add(elm.Line().at(J1.VBUS).right(1.0))
f = d.add(elm.Fuse().right().label('F1\n500mA PTC'))
tag(d, f.end, '+5V')
tag(d, J1.DP, 'USB_DP', lead=1.4)
tag(d, J1.DM, 'USB_DM', lead=1.4)
for anc, rname in (('CC1', 'R1'), ('CC2', 'R2')):
    ln = d.add(elm.Line().at(getattr(J1, anc)).right(0.8))
    r = d.add(elm.Resistor().right().label(f'{rname}\n5.1k'))
    d.add(elm.Ground().at(r.end).right())
ln = d.add(elm.Line().at(J1.GND).right(0.8))
d.add(elm.Ground().at(ln.end))

U3 = d.add(ic([('1', 'I/O1', 'IO1a'), ('2', 'GND', 'GND'), ('3', 'I/O2', 'IO2a')],
              [('6', 'I/O1', 'IO1b'), ('5', 'VBUS', 'VB'), ('4', 'I/O2', 'IO2b')],
              'U3  USBLC6-2SC6', w=2.4, spacing=1.2).at((13, 0)))
tag(d, U3.IO1a, 'USB_DP', side='left')
d.add(elm.Ground().at(d.add(elm.Line().at(U3.GND).left(0.6)).end))
tag(d, U3.IO2a, 'USB_DM', side='left')
tag(d, U3.IO1b, 'USB_DP')
tag(d, U3.VB, '+5V')
tag(d, U3.IO2b, 'USB_DM')

chain(d, 22, 4, '+5V', [elm.Capacitor().label('C1\n10µF')])
chain(d, 25, 4, '+5V', [elm.Capacitor().label('C2\n100nF')])
chain(d, 28.5, 4, '+5V', [elm.Resistor().label('R3\n1k'), elm.LED().label('LED1\nPWR yeşil')])
save(d, '01-usb-guc.svg')

# --------------------------------------------------------------- 2. CH340C
d = new()
title(d, -4, 9, '2. USB-UART köprü (CH340C, 5V)')
U2 = d.add(ic([
    ('16', 'VCC', 'VCC'),
    ('4', 'V3', 'V3'),
    ('5', 'UD+', 'UDP'),
    ('6', 'UD-', 'UDM'),
    ('1', 'GND', 'GND'),
], [
    ('2', 'TXD', 'TXD'),
    ('3', 'RXD', 'RXD'),
    ('13', 'DTR#', 'DTR'),
    ('14', 'RTS#', 'RTS'),
    ('7-12,15', 'NC', 'NC'),
], 'U2  CH340C', w=3.4, spacing=1.2).at((0, 0)))
tag(d, U2.VCC, '+5V', side='left')
tag(d, U2.UDP, 'USB_DP', side='left')
tag(d, U2.UDM, 'USB_DM', side='left')
d.add(elm.Ground().at(d.add(elm.Line().at(U2.GND).left(0.6)).end))
tag(d, U2.V3, 'CH_V3', side='left')
tag(d, U2.TXD, 'CH_TXD')
tag(d, U2.RXD, 'CH_RXD')
tag(d, U2.DTR, 'DTR_N')
tag(d, U2.RTS, 'RTS_N')
d.add(elm.NoConnect().at(U2.NC))
chain(d, -10, 7, '+5V', [elm.Capacitor().label('C3\n100nF\n(pin 16 dibine)')])
chain(d, -14, 7, 'CH_V3', [elm.Capacitor().label('C4\n100nF')])
save(d, '02-ch340c.svg')

# --------------------------------------------------------------- 3. UART ara bağlantı
d = new()
title(d, -3, 4.5, '3. UART ara bağlantısı (MCU kapalıyken geri beslemeyi engeller)')
# CH_TXD -|<|- MCU_RXD : katot CH_TXD tarafında
d.add(elm.Tag(width=TW).at((0, 0)).left().label('CH_TXD', fontsize=11))
d.add(elm.Line().at((0, 0)).right(0.6))
d1 = d.add(elm.Schottky().right().reverse().label('D1\nB5819W'))
dot = d.add(elm.Dot())
ln = d.add(elm.Line().right(1.5))
d.add(elm.Tag(width=TW).at(ln.end).right().label('MCU_RXD', fontsize=11))
r4 = d.add(elm.Resistor().at(dot.center).up().label('R4\n4.7k', loc='bottom'))
d.add(elm.Vdd().at(r4.end).label('VCC_MCU', fontsize=11))
# MCU_TXD -R5- CH_RXD
d.add(elm.Tag(width=TW).at((0, -3.5)).left().label('CH_RXD', fontsize=11))
d.add(elm.Line().at((0, -3.5)).right(0.6))
d.add(elm.Resistor().right().label('R5\n1k'))
ln = d.add(elm.Line().right(1.5 + 0.0))
d.add(elm.Tag(width=TW).at(ln.end).right().label('MCU_TXD', fontsize=11))
save(d, '03-uart.svg')

# --------------------------------------------------------------- 4. Otomatik ISP güç kesici
def wire(d, a, b, vfirst=True):
    """a'dan b'ye dik açılı hat."""
    corner = (a[0], b[1]) if vfirst else (b[0], a[1])
    d.add(elm.Line().at(a).to(corner))
    d.add(elm.Line().at(corner).to(b))


d = new()
title(d, 0, 9, '4. Otomatik ISP: DTR aktif + RTS pasif → VCC_MCU kapanır')
RAIL = 7
XR7, XR6, XSW = 3, 9, 6
d.add(elm.Vdd().at((XR7, RAIL)).label('+5V', fontsize=11))
r7 = d.add(elm.Resistor().at((XR7, RAIL)).down().label('R7\n10k', loc='bottom'))
r6 = d.add(elm.Resistor().at((XR6, RAIL)).down().label('R6\n10k', loc='bottom'))
d.add(elm.Dot().at((XR6, RAIL)))
# Q1 P-MOSFET: kapı R6 ucuyla aynı hizada
q1 = d.add(elm.PFet().theta(0).reverse().anchor('gate').at((XR6 + 3, r6.end[1])).label('Q1 AO3401A', loc='right', ofst=(0.2, 0)))
wire(d, (XR7, RAIL), (q1.source[0], RAIL), vfirst=False)
d.add(elm.Line().at((q1.source[0], RAIL)).to(q1.source))
d.add(elm.Line().at(r6.end).to(q1.gate))
d.add(elm.Dot().at(r6.end))
d.add(elm.Label().at((XR6 + 0.2, r6.end[1] + 0.35)).label('Q1_G', fontsize=10, halign='left'))
dd = d.add(elm.Line().at(q1.drain).down(0.8))
d.add(elm.Tag(width=TW).at(dd.end).right().label('VCC_MCU', fontsize=11))
# Q2 N-MOSFET: drain Q1_G, kaynak GND, kapı ISP_N
q2 = d.add(elm.NFet().theta(0).reverse().anchor('drain').at((XR6, r6.end[1] - 1.4)).label('Q2 2N7002', loc='right', ofst=(0.2, 0)))
d.add(elm.Line().at(r6.end).to(q2.drain))
d.add(elm.Ground().at(q2.source))
node = (XR7, q2.gate[1])
d.add(elm.Line().at(q2.gate).to(node))
d.add(elm.Line().at(r7.end).to(node))
d.add(elm.Dot().at(node))
d.add(elm.Label().at((XR7 - 0.2, node[1] + 0.35)).label('ISP_N', fontsize=10, halign='right'))
# SW1: ISP_N -> GND
d.add(elm.Dot().at((XSW, node[1])))
s1 = d.add(elm.Button().at((XSW, node[1])).down().label('SW1 ISP', loc='bottom'))
d.add(elm.Ground().at(s1.end))
# Q3 NPN: kollektör ISP_N, emiter DTR_N, baz R8 -> RTS_N
q3 = d.add(elm.BjtNpn().theta(0).anchor('collector').at((XR7, node[1] - 1.5)).label('Q3\nMMBT3904', loc='right'))
d.add(elm.Line().at(node).to(q3.collector))
de = d.add(elm.Line().at(q3.emitter).down(0.8))
d.add(elm.Tag(width=TW).at(de.end).down().label('DTR_N', fontsize=11, rotate=True))
r8 = d.add(elm.Resistor().at(q3.base).left().label('R8\n10k'))
d.add(elm.Tag(width=TW).at(r8.end).left().label('RTS_N', fontsize=11))
d.add(elm.Label().at((-4, -3.2)).label(
    'DTR_N=L ve RTS_N=H → Q3 iletim → ISP_N=L → Q2 kesim → Q1_G=H → Q1 kesim → VCC_MCU kapalı.\n'
    'Diğer kombinasyonlarda VCC_MCU açık. SW1 basılıyken VCC_MCU kapalı (elle ISP).',
    fontsize=11, halign='left'))
# VCC_MCU yükleri
chain(d, 18, RAIL, 'VCC_MCU', [elm.Resistor().label('R9\n4.7k\ndeşarj')])
chain(d, 21.5, RAIL, 'VCC_MCU', [elm.Resistor().label('R10\n1k'), elm.LED().label('LED2\nMCU sarı')])
save(d, '04-otomatik-isp.svg')

# --------------------------------------------------------------- 5. MCU
d = new()
title(d, -6, 23, '5. STC12C5A60S2 (PDIP-40), kristal, reset, P0 pull-up, kullanıcı LED/buton')
left = [
    ('1', 'P1.0/ADC0', 'p1'), ('2', 'P1.1/ADC1', 'p2'), ('3', 'P1.2/ADC2/RXD2', 'p3'),
    ('4', 'P1.3/ADC3/PWM0', 'p4'), ('5', 'P1.4/ADC4/PWM1', 'p5'), ('6', 'P1.5/ADC5/MOSI', 'p6'),
    ('7', 'P1.6/ADC6/MISO', 'p7'), ('8', 'P1.7/ADC7/SCLK', 'p8'),
    ('9', 'RST', 'p9'), ('10', 'P3.0/RXD', 'p10'), ('11', 'P3.1/TXD', 'p11'),
    ('12', 'P3.2/INT0', 'p12'), ('13', 'P3.3/INT1', 'p13'), ('14', 'P3.4/T0', 'p14'),
    ('15', 'P3.5/T1', 'p15'), ('16', 'P3.6/WR', 'p16'), ('17', 'P3.7/RD', 'p17'),
    ('18', 'XTAL2', 'p18'), ('19', 'XTAL1', 'p19'), ('20', 'GND', 'p20'),
]
right = [
    ('40', 'VCC', 'p40'), ('39', 'P0.0', 'p39'), ('38', 'P0.1', 'p38'), ('37', 'P0.2', 'p37'),
    ('36', 'P0.3', 'p36'), ('35', 'P0.4', 'p35'), ('34', 'P0.5', 'p34'), ('33', 'P0.6', 'p33'),
    ('32', 'P0.7', 'p32'), ('31', 'P4.6/EX_LVD', 'p31'), ('30', 'P4.5/ALE', 'p30'), ('29', 'P4.4', 'p29'),
    ('28', 'P2.7', 'p28'), ('27', 'P2.6', 'p27'), ('26', 'P2.5', 'p26'), ('25', 'P2.4', 'p25'),
    ('24', 'P2.3', 'p24'), ('23', 'P2.2', 'p23'), ('22', 'P2.1', 'p22'), ('21', 'P2.0', 'p21'),
]
U1 = d.add(ic(left, right, 'U1  STC12C5A60S2-35I (PDIP-40, soketli)', w=5.0, spacing=1.0).at((0, 0)))
left_nets = {
    'p9': 'RST', 'p10': 'MCU_RXD', 'p11': 'MCU_TXD', 'p18': 'XTAL2', 'p19': 'XTAL1',
}
for p, n, a in left:
    pt = getattr(U1, a)
    if a == 'p20':
        d.add(elm.Ground().at(d.add(elm.Line().at(pt).left(0.6)).end).theta(0))
    else:
        tag(d, pt, left_nets.get(a, n.split('/')[0]), side='left')
right_nets = {'p40': 'VCC_MCU', 'p31': 'VCC_MCU'}
for p, n, a in right:
    tag(d, getattr(U1, a), right_nets.get(a, n.split('/')[0]))

# Kristal
X0, Y0 = 20, 20
d.add(elm.Tag(width=TW).at((X0, Y0)).left().label('XTAL1', fontsize=11))
l1 = d.add(elm.Line().at((X0, Y0)).right(1.0))
d.add(elm.Dot())
y1 = d.add(elm.Crystal().right().label('Y1\n11.0592MHz'))
d.add(elm.Dot())
l2 = d.add(elm.Line().right(1.0))
d.add(elm.Tag(width=TW).at(l2.end).right().label('XTAL2', fontsize=11))
c7 = d.add(elm.Capacitor().at(l1.end).down().label('C7\n33pF', loc='bottom'))
d.add(elm.Ground().at(c7.end))
c8 = d.add(elm.Capacitor().at(y1.end).down().label('C8\n33pF'))
d.add(elm.Ground().at(c8.end))

# Reset devresi: C9 VCC_MCU-RST, R11 RST-GND, SW2+R12 VCC_MCU-RST
RX, RY = 21, 13
d.add(elm.Vdd().at((RX, RY)).label('VCC_MCU', fontsize=11))
c9 = d.add(elm.Capacitor().at((RX, RY)).down().label('C9\n10µF', loc='bottom'))
nd = d.add(elm.Dot())
r11 = d.add(elm.Resistor().down().label('R11\n10k', loc='bottom'))
d.add(elm.Ground().at(r11.end))
sw2 = d.add(elm.Button().at((RX, RY)).right().label('SW2 RESET', loc='bottom'))
r12 = d.add(elm.Resistor().down().label('R12\n1k'))
d.add(elm.Line().at(r12.end).to(nd.center))
d.add(elm.Line().at(nd.center).left(1.0))
d.add(elm.Tag(width=TW).at((RX - 1.0, nd.center[1])).left().label('RST', fontsize=11))

# Dekuplaj
chain(d, 27, 13, 'VCC_MCU', [elm.Capacitor().label('C5\n100nF\npin 40')])
chain(d, 30.5, 13, 'VCC_MCU', [elm.Capacitor().label('C6\n10µF')])

# Kullanıcı LED ve buton
chain(d, 27, 21, 'VCC_MCU', [elm.Resistor().label('R13\n1k'), elm.LED().label('LED3\nL kırmızı')], tail='P1.7')
chain(d, 31, 21, 'P3.2', [elm.Button().label('SW3\nUSER')])

# RN1 P0 pull-up
RN1 = d.add(ic([('1', 'COM', 'c')], [
    ('2', 'R', 'r2'), ('3', 'R', 'r3'), ('4', 'R', 'r4'), ('5', 'R', 'r5'),
    ('6', 'R', 'r6'), ('7', 'R', 'r7'), ('8', 'R', 'r8'), ('9', 'R', 'r9'),
], 'RN1  10k x8 (A09-103)', w=2.2, spacing=1.0).at((21, -2)))
tag(d, RN1.c, 'VCC_MCU', side='left')
for i, a in enumerate(['r2', 'r3', 'r4', 'r5', 'r6', 'r7', 'r8', 'r9']):
    tag(d, getattr(RN1, a), f'P0.{i}')

# Header'lar
hx = 32
for j, (ref, port) in enumerate((('J2', 'P1'), ('J3', 'P0'), ('J4', 'P2'), ('J5', 'P3'))):
    pins = [(str(k + 1), f'{port}.{k}', f'h{k}') for k in range(8)] + [('9', 'VCC_MCU', 'h8'), ('10', 'GND', 'h9')]
    H = d.add(ic(pins, [], f'{ref}  1x10', w=1.6, spacing=0.8).at((hx + (j % 2) * 7, -4 - (j // 2) * 11.5)))
    for k, (_, n, a) in enumerate(pins):
        pt = getattr(H, a)
        if n == 'GND':
            d.add(elm.Ground().at(d.add(elm.Line().at(pt).left(0.5)).end).theta(0))
        else:
            tag(d, pt, n, side='left', lead=0.4)
H6 = d.add(ic([('1', 'RST', 'a'), ('2', 'P4.5', 'b'), ('3', 'P4.4', 'c')], [], 'J6  1x3', w=1.6, spacing=0.8).at((hx + 14, -4)))
for a, n in (('a', 'RST'), ('b', 'P4.5'), ('c', 'P4.4')):
    tag(d, getattr(H6, a), n, side='left', lead=0.4)
save(d, '05-mcu.svg')

# --------------------------------------------------------------- tek sayfa (SVG'ler gömülü)
SHEETS = ['01-usb-guc.svg', '02-ch340c.svg', '03-uart.svg', '04-otomatik-isp.svg', '05-mcu.svg']
figs = []
for name in SHEETS:
    svg = (OUT / name).read_text(encoding='utf-8')
    svg = svg[svg.index('<svg'):]
    figs.append(f'<figure>{svg}</figure>')
html = (OUT / 'index_sablon.html').read_text(encoding='utf-8').replace('<!-- SHEETS -->', '\n'.join(figs))
(OUT / 'index.html').write_text(html, encoding='utf-8')
print('yazildi index.html')
