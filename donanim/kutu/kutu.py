"""STC12 kartı için 3D baskı kutusu (CadQuery).

  pip install cadquery
  python kutu.py [kart.step]

Çıktılar bu klasöre yazılır:
  kutu_alt.stl      Alt tabla (tabanı tablaya gelecek şekilde basılır)
  kutu_ust.stl      Üst kapak (STL'de ters çevrili: üst yüzü tablaya gelir)
  pim_x3.stl        ISP / RESET / USER basma pimleri (3 adet)
  isik_borusu_x3.stl  LED ışık boruları (3 adet, şeffaf filamentle)
  kutu.step         Montajlı hâl (kart hariç)

kart.step verilirse (kicad-cli pcb export step ile) kutu parçalarının kartla
çakışıp çakışmadığı hacim olarak ölçülür.

Koordinatlar: kartın sol alt köşesi (0, 0), PCB'nin alt yüzü z = 0, y yukarı.
Kart üzerindeki konumlar KiCad'deki gibi (y aşağı) verilir ve K() ile çevrilir.
"""
import sys
from pathlib import Path

import cadquery as cq

OUT = Path(__file__).parent

# Kart
PCB_W, PCB_H, PCB_T = 100.0, 56.0, 1.6
DELIKLER = [(3.5, 3.5), (96.5, 3.5), (3.5, 52.5), (96.5, 52.5)]  # M3, KiCad koordinatı
P = 2.54

# Kutu
BOSLUK = 0.5            # kart kenarı ile iç duvar arası
DUVAR = 2.0
TABAN = 2.0
AYAK = 5.0              # kartın altındaki boşluk (delikli parça bacakları 2.2 mm iniyor)
UST = 11.0              # kartın üst yüzünden kapağın alt yüzüne (çip + soket ~8.5 mm)
KAPAK = 2.0
R_DIS = 3.0             # dış köşe yarıçapı
AYRIM = PCB_T + 1.0     # alt tabla ile kapağın birleştiği yükseklik
DIL_Y, DIL_K, DIL_B = 1.5, 1.0, 0.15   # hizalama dili: yükseklik, kalınlık, boşluk

BOSS_D = 6.4            # vida kulesi dış çapı (kart deliğinin courtyard'ı 7 mm)
VIDA_D = 3.4            # M3 geçiş deliği
BAS_D, BAS_H = 6.0, 3.2  # M3 imbus başı yuvası
KILAVUZ_D = 2.5         # M3 vidanın plastiğe kendi yolunu açtığı delik (sıcak somun için 4.0)

SW_H = 1.5              # TS-1187A buton yüksekliği
PIM_D, PIM_DELIK = 4.6, 5.2
TUP_D, TUP_L = 7.6, 4.0  # pim kılavuz tüpü
LED_D, BORU_D, YAKA_D, YAKA_H = 2.8, 2.6, 4.2, 0.8

X0, X1 = -BOSLUK - DUVAR, PCB_W + BOSLUK + DUVAR
Y0, Y1 = X0, PCB_H + BOSLUK + DUVAR
Z0 = -AYAK - TABAN
Z_KAPAK_ALT = PCB_T + UST
Z1 = Z_KAPAK_ALT + KAPAK


def K(x, y):
    """KiCad kart koordinatı (y aşağı) -> kutu koordinatı (y yukarı)."""
    return (x, PCB_H - y)


def bot(n):
    return 40.0 + (n - 1) * P


# Kartın üst yüzünden erişilen parçalar (KiCad koordinatı)
BUTONLAR = {'ISP': (8.0, 12.0), 'RESET': (8.0, 44.0), 'USER': (70.0, 43.0)}
LEDLER = {'PWR': (10.0, 3.5), 'MCU': (19.0, 3.5), 'L': (57.78, 38.5)}
# (ilk pin x, y, pin sayısı, yön) yön +1: pinler sağa, -1: sola
HEADERLAR = {
    'P0': (37.46, 3.5, 10, +1), 'P2': (88.26, 3.5, 10, -1),
    'P1': (34.92, 52.5, 10, +1), 'P3': (62.86, 52.5, 10, +1), 'J6': (14.0, 52.5, 3, +1),
}
SOKET = (38.36, 16.42, 89.88, 34.81)   # U1 courtyard: x0, y0, x1, y1
USB_Y, USB_Z = 28.0, PCB_T + 1.63      # USB-C ağız merkezi (kılıf 3.26 mm)
USB_W, USB_H, USB_R = 13.0, 7.4, 2.5   # kablo ucunun kalıbı içeri girebilsin


def kutu(x0, y0, x1, y1, z0, z1, r=0.0):
    b = cq.Workplane().box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))
    return b.edges('|Z').fillet(r) if r > 0 else b


def silindir(x, y, z0, z1, d):
    return cq.Workplane().circle(d / 2).extrude(z1 - z0).translate((x, y, z0))


def ic_kenar(ofset, z0, z1):
    """İç duvar yüzünden `ofset` kadar dışarıdaki yuvarlatılmış dikdörtgen gövde."""
    return kutu(-BOSLUK - ofset, -BOSLUK - ofset, PCB_W + BOSLUK + ofset, PCB_H + BOSLUK + ofset,
                z0, z1, R_DIS - DUVAR + ofset)


def kabuk():
    dis = kutu(X0, Y0, X1, Y1, Z0, Z1, R_DIS)
    return dis.cut(ic_kenar(0, -AYAK, Z_KAPAK_ALT))


def usb_acikligi():
    a = (cq.Workplane('YZ').center(USB_Y, USB_Z).rect(USB_W, USB_H).extrude(-(BOSLUK + DUVAR + 1))
         .edges('|X').fillet(USB_R))
    return a.translate((0.5, 0, 0))


def alt_tabla():
    t = kabuk().intersect(kutu(X0 - 1, Y0 - 1, X1 + 1, Y1 + 1, Z0 - 1, AYRIM))
    # hizalama dili: duvarın iç yarısı birleşme çizgisinin üstüne çıkar, kapaktaki yuvaya girer
    t = t.union(ic_kenar(DIL_K, AYRIM - 0.01, AYRIM + DIL_Y).cut(ic_kenar(0, AYRIM - 1, AYRIM + DIL_Y + 1)))
    for x, y in DELIKLER:
        cx, cy = K(x, y)
        t = t.union(silindir(cx, cy, -AYAK - 0.01, 0, BOSS_D))
        t = t.cut(silindir(cx, cy, -AYAK - 1.2, 0.1, KILAVUZ_D))
    t = t.cut(usb_acikligi())
    # alt yüz: lastik ayak yuvaları ve yazı
    for cx, cy in ((10, 10), (PCB_W - 10, 10), (10, PCB_H - 10), (PCB_W - 10, PCB_H - 10)):
        t = t.cut(silindir(cx, cy, Z0 - 0.1, Z0 + 0.6, 10.5))
    yazi = (cq.Workplane('XY').workplane(offset=Z0).center(PCB_W / 2, PCB_H / 2)
            .transformed(rotate=(180, 0, 0))
            .text('STC12C5A60S2 Gelistirme Karti  Rev A', 4.0, -0.6, combine=False))
    return t.cut(yazi)


def ust_kapak():
    k = kabuk().intersect(kutu(X0 - 1, Y0 - 1, X1 + 1, Y1 + 1, AYRIM, Z1 + 1))
    # alt tablanın diline yuva
    k = k.cut(ic_kenar(DIL_K + DIL_B, AYRIM - 0.1, AYRIM + DIL_Y + 0.2))
    # vida kuleleri: kapaktan kartın üst yüzüne iner, kartı ayaklara sıkıştırır
    for x, y in DELIKLER:
        cx, cy = K(x, y)
        k = k.union(silindir(cx, cy, PCB_T, Z_KAPAK_ALT + 0.01, BOSS_D))
        k = k.cut(silindir(cx, cy, PCB_T - 0.1, Z1 + 0.1, VIDA_D))
        k = k.cut(silindir(cx, cy, Z1 - BAS_H, Z1 + 0.1, BAS_D))
    # butonlar: kılavuz tüpü + delik
    for x, y in BUTONLAR.values():
        cx, cy = K(x, y)
        k = k.union(silindir(cx, cy, Z_KAPAK_ALT - TUP_L, Z_KAPAK_ALT + 0.01, TUP_D))
        k = k.cut(silindir(cx, cy, Z_KAPAK_ALT - TUP_L - 0.1, Z1 + 0.1, PIM_DELIK))
    # LED delikleri ve ışık borusu yakası yuvası
    for x, y in LEDLER.values():
        cx, cy = K(x, y)
        k = k.cut(silindir(cx, cy, Z_KAPAK_ALT - 0.1, Z1 + 0.1, LED_D))
        k = k.cut(silindir(cx, cy, Z1 - YAKA_H, Z1 + 0.1, YAKA_D))
    # header yarıkları: Dupont kablo uçları yarıktan geçip pinlere takılır
    for x, y, n, yon in HEADERLAR.values():
        xa, xb = sorted((x, x + yon * (n - 1) * P))
        cy = K(0, y)[1]
        k = k.cut(kutu(xa - 1.6, cy - 1.5, xb + 1.6, cy + 1.5, Z_KAPAK_ALT - 0.1, Z1 + 0.1))
    # soket penceresi: çip takılıp çıkarılabilsin
    sx0, sy0, sx1, sy1 = SOKET
    (wx0, wy1), (wx1, wy0) = K(sx0 - 0.8, sy0 - 0.8), K(sx1 + 0.8, sy1 + 0.8)
    k = k.cut(kutu(wx0, wy0, wx1, wy1, Z_KAPAK_ALT - 0.1, Z1 + 0.1, 1.0))
    k = k.cut(usb_acikligi())
    return k.cut(kapak_yazilari())


YAZILAR = [  # (metin, KiCad x, y, boy, hizalama)
    ('P0.0 - P0.7', 37.46 + 4.5 * P, 7.3, 2.6, 'center'),
    ('P2.0 - P2.7', 88.26 - 4.5 * P, 7.3, 2.6, 'center'),
    ('P1.0 - P1.7 / ADC', 34.92 + 4.5 * P, 48.7, 2.6, 'center'),
    ('P3.0 - P3.7', 62.86 + 4.5 * P, 48.7, 2.6, 'center'),
    ('RST P4.5 P4.4', 16.54, 48.7, 2.2, 'center'),
    ('ISP', 11.8, 12.0, 2.8, 'left'), ('RESET', 11.8, 44.0, 2.8, 'left'), ('USER', 74.0, 43.0, 2.8, 'left'),
    ('PWR', 10.0, 7.0, 2.2, 'center'), ('MCU', 19.0, 7.0, 2.2, 'center'), ('L', 60.3, 38.5, 2.6, 'left'),
    ('USB', 4.5, 28.0, 2.6, 'center'), ('STC12C5A60S2', 76.0, 12.0, 3.0, 'center'),
]
PIN1 = [(37.46 - 2.6, 3.5), (88.26 + 2.6, 3.5), (34.92 - 2.6, 52.5), (62.86 - 2.6, 52.5), (14.0 - 2.6, 52.5)]


def kapak_yazilari():
    g = None
    for metin, x, y, boy, hiza in YAZILAR:
        cx, cy = K(x, y)
        t = (cq.Workplane('XY').workplane(offset=Z1).center(cx, cy)
             .text(metin, boy, -0.6, combine=False, halign=hiza, valign='center', kind='bold'))
        g = t if g is None else g.union(t)
    for x, y in PIN1:   # 1. pin işareti
        cx, cy = K(x, y)
        g = g.union(silindir(cx, cy, Z1 - 0.6, Z1 + 0.1, 1.0))
    return g


def pim():
    """Buton pimi; ucu butona, koni ve yaka altta, tablaya koni ucu gelecek şekilde basılır."""
    koni = cq.Solid.makeCone(1.5, 4.0, 2.5)
    p = cq.Workplane().add(koni)
    p = p.union(silindir(0, 0, 2.5, 3.5, 8.0))
    boy = (Z1 + 1.0) - (PCB_T + SW_H)
    p = p.union(silindir(0, 0, 3.5, boy, PIM_D).faces('>Z').edges().fillet(0.8))
    return p


def isik_borusu():
    """LED üstünden kapak yüzüne kadar; yaka kapaktaki yuvaya oturur. Yaka tablaya gelecek şekilde basılır."""
    boy = Z1 - (PCB_T + 0.8 + 0.3)
    return silindir(0, 0, 0, YAKA_H, YAKA_D - 0.2).union(silindir(0, 0, 0, boy, BORU_D))


def yer_tutucular():
    """3D modeli olmayan parçalar ve sokete takılı çip (çakışma kontrolü için)."""
    g = kutu(0.0, USB_Y - 4.47, 7.35, USB_Y + 4.47, PCB_T, PCB_T + 3.26)
    for x, y in BUTONLAR.values():
        cx, cy = K(x, y)
        g = g.union(kutu(cx - 2.55, cy - 2.55, cx + 2.55, cy + 2.55, PCB_T, PCB_T + SW_H))
    cx, cy = K(40.0 + 9.5 * P, (16.42 + 34.81) / 2)
    return g.union(kutu(cx - 26.0, cy - 7.0, cx + 26.0, cy + 7.0, 6.0, 10.0))  # DIP-40 çip, soket üstünde


def yerlestir_pim(p):
    g = None
    for x, y in BUTONLAR.values():
        cx, cy = K(x, y)
        q = p.translate((cx, cy, PCB_T + SW_H))
        g = q if g is None else g.union(q)
    return g


def yerlestir_boru(b):
    g = None
    for x, y in LEDLER.values():
        cx, cy = K(x, y)
        q = b.translate((cx, cy, PCB_T + 0.8 + 0.3))
        g = q if g is None else g.union(q)
    return g


def yan_yana(parca, adet, aralik):
    g = None
    for i in range(adet):
        q = parca.translate((i * aralik, 0, 0))
        g = q if g is None else g.union(q)
    return g


if __name__ == '__main__':
    alt, ust, pm, br = alt_tabla(), ust_kapak(), pim(), isik_borusu()
    cq.exporters.export(alt, str(OUT / 'kutu_alt.stl'), tolerance=0.02, angularTolerance=0.1)
    cq.exporters.export(ust.rotate((0, 0, 0), (1, 0, 0), 180), str(OUT / 'kutu_ust.stl'), tolerance=0.02,
                        angularTolerance=0.1)
    cq.exporters.export(yan_yana(pm, 3, 12), str(OUT / 'pim_x3.stl'), tolerance=0.01, angularTolerance=0.1)
    boru_baski = br.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, Z1 - (PCB_T + 1.1)))
    cq.exporters.export(yan_yana(boru_baski, 3, 8), str(OUT / 'isik_borusu_x3.stl'), tolerance=0.01,
                        angularTolerance=0.1)
    montaj = (cq.Assembly()
              .add(alt, name='alt_tabla', color=cq.Color(0.20, 0.22, 0.25))
              .add(ust, name='ust_kapak', color=cq.Color(0.85, 0.86, 0.88))
              .add(yerlestir_pim(pm), name='pimler', color=cq.Color(0.9, 0.3, 0.2))
              .add(yerlestir_boru(br), name='isik_borulari', color=cq.Color(0.8, 0.9, 1.0, 0.6)))
    montaj.save(str(OUT / 'kutu.step'))
    bb = alt.union(ust).val().BoundingBox()
    print(f'Dış ölçü: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm')

    if len(sys.argv) > 1:
        kart = cq.importers.importStep(sys.argv[1]).translate((-40.0, 86.0, 0.0))  # KiCad sayfa -> kart
        kart = kart.union(yer_tutucular())
        pimler, borular = yerlestir_pim(pm), yerlestir_boru(br)
        for ad, a, b in (('alt tabla - kart', alt, kart), ('üst kapak - kart', ust, kart),
                         ('pimler - kart', pimler, kart), ('ışık boruları - kart', borular, kart),
                         ('alt tabla - üst kapak', alt, ust), ('üst kapak - pimler', ust, pimler),
                         ('üst kapak - borular', ust, borular)):
            print(f'Çakışma {ad:22} {a.intersect(b).val().Volume():8.3f} mm³')
        # kontrolün gerçekten çakışma yakaladığını göster: kapak 3 mm aşağıda header ve çipe girer
        print(f'Kontrol (kapak 3 mm aşağıda) {ust.translate((0, 0, -3)).intersect(kart).val().Volume():8.1f} mm³')
