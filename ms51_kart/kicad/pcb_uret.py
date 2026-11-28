"""kart_tanim.py'den yerleşimi yapılmış, yolları çizilmemiş PCB (ms51_kart.kicad_pcb) üretir.

Footprint'ler kütüphaneden yüklenir, pad netleri şemadan dışa aktarılan
netlist'ten alınır (şema ile birebir eşleşme için) ve YERLESIM tablosundaki
konumlara konur. Yollar yol_uret.py ile çizilir. KiCad'in Python ortamında çalışır:

  kicad-cli sch export netlist -o out.net ms51_kart.kicad_sch
  python3 pcb_uret.py /usr/share/kicad/footprints out.net

Dikkat: PCB dosyasını sıfırdan yazar. KiCad'de elle değişiklik yaptıktan sonra çalıştırmayın.
"""
import sys

import pcbnew

from kart_tanim import PARTS, TAKILMAZ
from kicad_uret import PROJECT, child, children, parse, uid

FPDIR, NETLIST = sys.argv[1], sys.argv[2]
PAD_NET = {}
DATASHEET = {}   # KiCad 10 şema-PCB eşlik denetimi Datasheet alanını da karşılaştırıyor
with open(NETLIST, encoding='utf-8') as f:
    _net = parse(f.read())
    for c in children(child(_net, 'components'), 'comp'):
        ds = child(c, 'datasheet')
        DATASHEET[str(child(c, 'ref')[1])] = str(ds[1]) if ds else ''
    for n in children(child(_net, 'nets'), 'net'):
        for node in children(n, 'node'):
            PAD_NET[(str(child(node, 'ref')[1]), str(child(node, 'pin')[1]))] = str(child(n, 'name')[1])

BOARD_W, BOARD_H = 84.0, 50.0
X0, Y0 = 40.0, 30.0  # kartın sayfa üzerindeki sol üst köşesi (mm)
P = 2.54
HDR_TOP, HDR_BOT, HDR_SAG = 3.5, BOARD_H - 3.5, BOARD_W - 3.5
MCU_X, MCU_Y = 50.0, 25.0

# Kart koordinatları (mm, sol üst köşe 0,0), açı derece (saat yönü tersine).
# Yerleşim mantığı:
#  - USB-C sol kenarda; ESD, sigorta ve CH340C hemen arkasında (STC kartıyla aynı akış).
#  - MS51 (LQFP-32) ortada, pin 1 sol üstte. Header'lar portların çıktığı kenarlarda:
#    P0 üstte (P0.2-P0.7 üst kenarda), P1 sağ kenarda dikey, P2 ve P3 altta.
#  - UART dirençleri, reset devresi ve dekuplaj CH340C ile MS51 arasında; C5 VDD (pin 6) yanında.
#  - Rev B: U2'nin altında CH340G için kristal (Y1) ve yük kondansatörleri (C8, C9); varsayılan montajda boş.
#  - Rev C: ICP header'ı (J6) MCU'nun hemen altında; pull-up'lar (R9, R10) MCU'ya, seri dirençler
#    (R11, R12) header'a yakın. 24 MHz kristal (Y2) ve yük kondansatörleri (C10, C11) MCU'nun sağ
#    üstünde, XIN/XOUT (pin 23/24) yanında. RST kondansatörü (C12) pin 1'in solunda.
YERLESIM = {
    'J1': (4.2, 25.0, 270),
    'R1': (8.0, 17.0, 0),
    'R2': (8.0, 33.0, 0),
    'F1': (12.5, 19.5, 0),
    'U3': (12.5, 25.0, 0),
    'C1': (12.5, 30.5, 0),
    'C2': (12.5, 33.5, 0),
    'U2': (22.0, 25.0, 0),
    'C3': (27.5, 20.5, 90),
    'Y1': (20.5, 35.5, 0),                   # yalnızca CH340G ile: pin 1 (XI) U2.7'ye yakın
    'C8': (18.5, 41.0, 90),
    'C9': (26.0, 41.0, 90),
    'C4': (16.5, 22.0, 90),
    'R4': (31.0, 13.5, 0),
    'R5': (31.0, 16.5, 0),
    'R6': (40.5, 18.0, 90),
    'D1': (36.5, 18.0, 90),
    'C7': (32.0, 31.0, 90),
    'R7': (35.5, 31.0, 90),
    'SW1': (12.0, 42.0, 0),
    'LED1': (10.0, 3.5, 0),
    'R3': (14.0, 3.5, 0),
    'J6': (38.5, 37.8, 90),                  # ICP: MCU'nun altında, pin 1 (5V) solda, sağa doğru
    'R9': (52.0, 35.2, 0),                   # ICE_DAT pull-up
    'R10': (52.0, 37.2, 0),                  # ICE_CLK pull-up
    'R11': (42.0, 35.2, 0),                  # ICE_DAT seri
    'R12': (45.5, 35.2, 0),                  # ICE_CLK seri
    'C12': (43.0, 22.5, 90),                 # RST - GND
    'Y2': (58.0, 20.5, 0),                   # 24 MHz: pad 1 (XIN) pin 23'e, pad 3 (XOUT) pin 24'e yakın
    'C10': (62.0, 23.5, 90),
    'C11': (62.0, 17.5, 90),
    'U1': (MCU_X, MCU_Y, 0),
    'C5': (43.5, 27.5, 90),
    'C6': (40.0, 27.5, 90),
    'LED2': (59.0, 33.0, 90),
    'R8': (59.0, 37.0, 90),
    'SW2': (72.0, 39.0, 0),
    'J2': (68.0, HDR_TOP, 270),              # P0: pin 1 (P0.0) sağda, sola doğru
    'J3': (HDR_SAG, 11.0, 0),                # P1: sağ kenarda, pin 1 (P1.0) üstte
    'J5': (24.0, HDR_BOT, 90),               # P2: pin 1 (RST) solda
    'J4': (47.5, HDR_BOT, 90),               # P3: pin 1 (P3.0) solda
}

# Referans yazısı varsayılan yerine (parçanın üstü) konacak olanlar: kart koordinatı
REF_KONUM = {'R9': (54.6, 35.2), 'R10': (54.6, 37.2)}

DELIKLER = [(3.5, 3.5), (BOARD_W - 3.5, 3.5), (3.5, BOARD_H - 3.5), (BOARD_W - 3.5, BOARD_H - 3.5)]

YAZILAR = [  # (x, y, metin[, açı]) ön serigrafi
    (12.0, 46.0, 'RESET'), (72.0, 43.2, 'USER'), (10.0, 6.0, 'PWR'), (61.3, 33.0, 'L'),
    (38.5 + 2 * P, 40.3, '5V DAT CLK RST GND'), (38.5 + 2 * P, 41.8, 'ICP (Nu-Link)'),
    (68.0 - 4.5 * P, HDR_TOP + 2.6, 'P0.7 - P0.2'), (68.0 - 0.5 * P, HDR_TOP + 2.6, 'XT'),
    (HDR_SAG - 2.8, 11.0 + 4.5 * P, 'P1.0 - P1.7', 90),
    (24.0 + 2.5 * P, HDR_BOT - 2.6, 'RST P2.1-P2.5'), (47.5 + 3.5 * P, HDR_BOT - 2.6, 'P3.0 - P3.7'),
    (MCU_X, MCU_Y + 7.2, 'MS51PC0AE'), (22.25, 39.4, 'CH340G'),
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
    lcsc_alani = fp.GetField('LCSC') if hasattr(fp, 'GetField') else fp.GetFieldByName('LCSC')  # KiCad 10 / 9
    lcsc_alani.SetVisible(False)
    if hasattr(fp, 'GetField') and fp.GetField('Datasheet') is not None:
        fp.GetField('Datasheet').SetText(DATASHEET.get(ref, ''))
    if ref in TAKILMAZ:
        fp.SetDNP(True)
    for pad in fp.Pads():
        pname = PAD_NET.get((ref, pad.GetNumber()))
        if pname:
            pad.SetNet(net(pname))
    x, y, rot = YERLESIM[ref]
    fp.SetPosition(at(x, y))
    fp.SetOrientationDegrees(rot)
    if ref in REF_KONUM:
        fp.Reference().SetPosition(at(*REF_KONUM[ref]))
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

for x, y, text, *aci in YAZILAR:
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetLayer(pcbnew.F_SilkS)
    t.SetPosition(at(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
    t.SetTextThickness(mm(0.15))
    if aci:
        t.SetTextAngleDegrees(aci[0])
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
