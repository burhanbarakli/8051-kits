"""kart_tanim.py'den yerleşimi yapılmış, yolları çizilmemiş PCB (stc89_kart.kicad_pcb) üretir.

Footprint'ler kütüphaneden yüklenir, pad netleri şemadan dışa aktarılan
netlist'ten alınır (şema ile birebir eşleşme için) ve YERLESIM tablosundaki
konumlara konur. Yol çizimi elle yapılacaktır. KiCad'in Python ortamında çalışır:

  kicad-cli sch export netlist -o out.net stc89_kart.kicad_sch
  python3 pcb_uret.py /usr/share/kicad/footprints out.net

Dikkat: PCB dosyasını sıfırdan yazar. KiCad'de elle değişiklik yaptıktan sonra çalıştırmayın.
"""
import sys

import pcbnew

from kart_tanim import PARTS
from kicad_uret import PROJECT, child, children, parse, uid

FPDIR, NETLIST = sys.argv[1], sys.argv[2]
PAD_NET = {}
with open(NETLIST, encoding='utf-8') as f:
    for n in children(child(parse(f.read()), 'nets'), 'net'):
        for node in children(n, 'node'):
            PAD_NET[(str(child(node, 'ref')[1]), str(child(node, 'pin')[1]))] = str(child(n, 'name')[1])

BOARD_W, BOARD_H = 100.0, 56.0
X0, Y0 = 40.0, 30.0  # kartın sayfa üzerindeki sol üst köşesi (mm)
P = 2.54
DIP_X, DIP_TOP = 40.0, 18.0          # U1 pin 40 (sol üst) konumu, kart koordinatı
DIP_BOT = DIP_TOP + 6 * P            # alt sıra (pin 1..20)
HDR_TOP, HDR_BOT = 3.5, BOARD_H - 3.5


def bot(n):
    """U1 alt sıra pin n (1..20) x konumu."""
    return DIP_X + (n - 1) * P


def top(n):
    """U1 üst sıra pin n (21..40) x konumu."""
    return DIP_X + (40 - n) * P


# Kart koordinatları (mm, sol üst köşe 0,0), açı derece (saat yönü tersine).
# Yerleşim mantığı:
#  - U1 kartın ortasında yatay; port header'ları uzun kenarlarda, kendi portlarının
#    hizasında (J3/J4 üstte P0/P2, J2/J5 altta P1/P3) -> düz, kısa yollar.
#  - RN1 (P0 pull-up) P0 pinlerinin tam üstünde, pin 1 (ortak uç) U1 pin 40 (VCC) hizasında.
#  - Y1 ve C7/C8 XTAL pinlerinin (18-19) hemen altında.
#  - USB-C sol kenarda; ESD, sigorta ve CH340C hemen arkasında, otomatik ISP sol üstte.
#  - ISP ve RESET butonları sol kenarda yan yana, USER butonu P3.2'nin altında.
YERLESIM = {
    # MCU ve port header'ları
    'U1': (DIP_X, DIP_BOT, 90),             # footprint orijini pin 1 (sol alt)
    'J3': (top(39) - 2 * P, HDR_TOP, 90),   # P0: J4 ile çakışmasın diye 2 adım sola kaydırıldı
    'J4': (top(21), HDR_TOP, 270),          # P2: pin 1 sağda, sola doğru
    'J2': (bot(1) - 2 * P, HDR_BOT, 90),    # P1
    'J5': (bot(10), HDR_BOT, 90),           # P3: pin 1 = P3.0
    'RN1': (top(40), 10.5, 0),
    'C5': (36.5, DIP_TOP, 90),
    'C6': (36.5, DIP_TOP + 4.5, 90),
    # Alt kanal: kullanıcı LED'i, reset RC, USER butonu, kristal
    'LED3': (bot(8), 38.5, 90),
    'R13': (bot(8), 42.5, 90),
    'C9': (61.5, 38.5, 90),
    'R11': (61.5, 42.8, 90),
    'SW3': (70.0, 43.0, 0),
    'Y1': (bot(19) + 0.3, 39.5, 180),     # pin 1 (XTAL1) U1 pin 19, pin 2 (XTAL2) pin 18 hizasında
    'C7': (88.0, 45.0, 90),
    'C8': (80.5, 45.0, 90),
    # USB ve CH340C
    'J1': (4.2, 28.0, 270),               # ağız sol kenarda
    'R1': (8.0, 20.0, 0),                 # CC1 pull-down
    'R2': (8.0, 36.0, 0),                 # CC2 pull-down
    'F1': (12.5, 22.5, 0),
    'U3': (12.5, 28.0, 0),
    'C1': (12.5, 33.5, 0),
    'C2': (12.5, 36.5, 0),
    'U2': (22.0, 28.0, 0),
    'C3': (27.5, 23.5, 90),
    'C4': (16.5, 25.0, 90),
    'D1': (22.0, 37.0, 0),
    'R5': (22.0, 41.0, 0),
    'R4': (27.5, 37.0, 0),
    # Otomatik ISP ve LED'ler (sol üst)
    'LED1': (10.0, 3.5, 0),
    'R3': (14.0, 3.5, 0),
    'LED2': (19.0, 3.5, 0),
    'R10': (23.0, 3.5, 0),
    'R9': (28.0, 3.5, 0),
    'Q1': (32.5, 12.0, 0),
    'R6': (28.0, 9.0, 90),
    'Q2': (28.0, 14.5, 0),
    'R7': (22.0, 9.0, 90),
    'Q3': (22.0, 14.5, 0),
    'R8': (17.0, 14.5, 0),
    'SW1': (8.0, 12.0, 0),
    # Sol alt: RESET butonu ve J6
    'SW2': (8.0, 44.0, 0),
    'R12': (13.0, 44.0, 90),
    'J6': (14.0, HDR_BOT, 90),
}

DELIKLER = [(3.5, 3.5), (BOARD_W - 3.5, 3.5), (3.5, BOARD_H - 3.5), (BOARD_W - 3.5, BOARD_H - 3.5)]

YAZILAR = [  # (x, y, metin) ön serigrafi
    (8.0, 16.2, 'ISP'), (8.0, 48.2, 'RESET'), (70.0, 47.2, 'USER'),
    (10.0, 6.0, 'PWR'), (19.0, 6.0, 'MCU'), (bot(8), 35.9, 'L'),
    # port adları header'ın iç tarafında, port pinlerinin (1-8) ortasında
    (top(39) - 2 * P + 3.5 * P, HDR_TOP + 2.6, 'P0.0 - P0.7'), (top(21) - 3.5 * P, HDR_TOP + 2.6, 'P2.0 - P2.7'),
    (bot(1) - 2 * P + 3.5 * P, HDR_BOT - 2.6, 'P1.0 - P1.7 / ADC'), (bot(10) + 3.5 * P, HDR_BOT - 2.6, 'P3.0 - P3.7'),
    (12.0, 49.8, 'RST P4.5 P4.4'), (65.0, 27.0, 'STC12C5A60S2'),
]

mm = pcbnew.FromMM
board = pcbnew.BOARD()
nets = {}


def net(name):
    if name not in nets:
        nets[name] = pcbnew.NETINFO_ITEM(board, name)
        board.Add(nets[name])
    return nets[name]


def at(x, y):
    return pcbnew.VECTOR2I(mm(X0 + x), mm(Y0 + y))


missing = {p[0] for p in PARTS} - set(YERLESIM)
if missing:
    raise SystemExit(f'YERLESIM tablosunda olmayan parçalar: {sorted(missing)}')

for ref, _lib, value, footprint, lcsc, _pins, _xy in PARTS:
    lib, name = footprint.split(':')
    fp = pcbnew.FootprintLoad(f'{FPDIR}/{lib}.pretty', name)
    if fp is None:
        raise SystemExit(f'{ref}: footprint bulunamadı {footprint}')
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    fp.SetPath(pcbnew.KIID_PATH('/' + uid('sym', ref)))
    fp.SetSheetname('/')
    fp.SetSheetfile(f'{PROJECT}.kicad_sch')
    fp.SetField('LCSC', lcsc)
    fp.GetFieldByName('LCSC').SetVisible(False)
    for pad in fp.Pads():
        pname = PAD_NET.get((ref, pad.GetNumber()))
        if pname:
            pad.SetNet(net(pname))
    x, y, rot = YERLESIM[ref]
    fp.SetPosition(at(x, y))
    fp.SetOrientationDegrees(rot)
    board.Add(fp)

# M3 montaj delikleri (yalnızca kartta; şemada ve BOM'da yok)
for k, (x, y) in enumerate(DELIKLER, 1):
    fp = pcbnew.FootprintLoad(f'{FPDIR}/MountingHole.pretty', 'MountingHole_3.2mm_M3')
    fp.SetReference(f'H{k}')
    fp.SetValue('M3')
    fp.SetFPID(pcbnew.LIB_ID('MountingHole', 'MountingHole_3.2mm_M3'))
    fp.SetBoardOnly(True)
    fp.SetExcludedFromBOM(True)
    fp.SetExcludedFromPosFiles(True)
    fp.SetPosition(at(x, y))
    board.Add(fp)

for x, y, text in YAZILAR:
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetLayer(pcbnew.F_SilkS)
    t.SetPosition(at(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
    t.SetTextThickness(mm(0.15))
    board.Add(t)

rect = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_RECT)
rect.SetStart(at(0, 0))
rect.SetEnd(at(BOARD_W, BOARD_H))
rect.SetLayer(pcbnew.Edge_Cuts)
rect.SetWidth(mm(0.1))
board.Add(rect)

board.SetCopperLayerCount(2)
pcbnew.SaveBoard(f'{PROJECT}.kicad_pcb', board)
print(f'{PROJECT}.kicad_pcb: {len(PARTS)} footprint + {len(DELIKLER)} delik, {len(nets)} net, kart {BOARD_W:.0f}x{BOARD_H:.0f} mm')
