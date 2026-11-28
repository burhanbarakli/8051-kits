"""MS51 kartı için 3D baskı kutusu (CadQuery). STC12 kutusunun (../../donanim/kutu) uyarlaması.

  pip install cadquery
  python kutu.py [kart.step]

Çıktılar bu klasöre yazılır:
  kutu_alt.stl        Alt tabla (tabanı tablaya gelecek şekilde basılır)
  kutu_ust.stl        Üst kapak (STL'de ters çevrili: üst yüzü tablaya gelir)
  pim_x2.stl          RESET / USER basma pimleri (2 adet)
  isik_borusu_x2.stl  LED ışık boruları (2 adet, şeffaf filamentle)
  kutu.step           Montajlı hâl (kart hariç)

kart.step verilirse (kicad-cli pcb export step ile) kutu parçalarının kartla
çakışıp çakışmadığı hacim olarak ölçülür.

Koordinatlar: kartın sol alt köşesi (0, 0), PCB'nin alt yüzü z = 0, y yukarı.
Kart üzerindeki konumlar KiCad'deki gibi (y aşağı) verilir ve K() ile çevrilir.
Konumlar ../kicad/ms51_kart.kicad_pcb'den alındı (pcb_uret.py YERLESIM tablosu).
"""
import sys
from pathlib import Path

import cadquery as cq

OUT = Path(__file__).parent

# Kart
PCB_W, PCB_H, PCB_T = 84.0, 50.0, 1.6
DELIKLER = [(3.5, 3.5), (80.5, 3.5), (3.5, 46.5), (80.5, 46.5)]  # M3, KiCad koordinatı
P = 2.54

# Kutu
BOSLUK = 0.5            # kart kenarı ile iç duvar arası
DUVAR = 2.0
TABAN = 2.0
AYAK = 5.0              # kartın altındaki boşluk (header bacakları iniyor)
UST = 11.0              # kartın üst yüzünden kapağın alt yüzüne (header uçları 8.5 mm)
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


# Kartın üst yüzünden erişilen parçalar (KiCad koordinatı)
BUTONLAR = {'RESET': (12.0, 42.0), 'USER': (72.0, 39.0)}
LEDLER = {'PWR': (10.0, 3.5), 'L': (59.0, 33.0)}
# (1. pin x, y, pin sayısı, yön): yön 'x+' pinler sağa, 'x-' sola, 'y+' aşağı (KiCad'de)
HEADERLAR = {
    'J6 ICP': (38.5, 37.8, 5, 'x+'), 'J2 P0': (68.0, 3.5, 10, 'x-'),   # Rev C: J6 MCU'nun altında
    'J3 P1': (80.5, 11.0, 10, 'y+'),
    'J5 P2': (24.0, 46.5, 8, 'x+'), 'J4 P3': (47.5, 46.5, 10, 'x+'),
}
USB_Y, USB_Z = PCB_H - 25.0, PCB_T + 1.63   # USB-C ağız merkezi (kılıf 3.26 mm)
USB_W, USB_H, USB_R = 13.0, 7.4, 2.5        # kablo ucunun kalıbı içeri girebilsin


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


def header_uclari(x, y, n, yon):
    """Header'ın ilk ve son pininin KiCad koordinatı."""
    d = (n - 1) * P
    return {'x+': (x, y, x + d, y), 'x-': (x, y, x - d, y), 'y+': (x, y, x, y + d)}[yon]


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
    yazi = None
    for metin, dy, boy in (('MS51 Gelistirme Karti', 3.0, 4.0), ('MS51PC0AE  Rev B', -3.0, 3.0)):
        w = (cq.Workplane('XY').workplane(offset=Z0).center(PCB_W / 2, PCB_H / 2 + dy)
             .transformed(rotate=(180, 0, 0))
             .text(metin, boy, -0.6, combine=False, halign='center', valign='center'))
        yazi = w if yazi is None else yazi.union(w)
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
    # header yarıkları: Dupont kablo uçları (ve ICP'ye Nu-Link kablosu) yarıktan geçip pinlere takılır
    for h in HEADERLAR.values():
        xa, ya, xb, yb = header_uclari(*h)
        (x0, y0), (x1, y1) = K(min(xa, xb), max(ya, yb)), K(max(xa, xb), min(ya, yb))
        k = k.cut(kutu(x0 - 1.6, y0 - 1.6, x1 + 1.6, y1 + 1.6, Z_KAPAK_ALT - 0.1, Z1 + 0.1))
    k = k.cut(usb_acikligi())
    return k.cut(kapak_yazilari())


YAZILAR = [  # (metin, KiCad x, y, boy, hizalama, açı)
    ('P0.7 - P0.2', (45.14 + 62.92) / 2, 7.3, 2.6, 'center', 0), ('XT', (65.46 + 68.0) / 2, 7.3, 2.0, 'center', 0),
    ('ICP (Nu-Link)', 38.5 + 2 * P, 31.3, 2.0, 'center', 0),
    ('5V DAT CLK RST GND', 38.5 + 2 * P, 33.5, 1.6, 'center', 0),
    ('P1.0 - P1.7', 76.6, 11.0 + 4.5 * P, 2.6, 'center', 90),
    ('RST P2.1 - P2.5', (24.0 + 41.78) / 2, 42.7, 2.4, 'center', 0),
    ('P3.0 - P3.7', (47.5 + 70.36) / 2, 42.7, 2.6, 'center', 0),
    ('RESET', 12.0, 37.6, 2.6, 'center', 0), ('USER', 72.0, 34.6, 2.6, 'center', 0),
    ('PWR', 10.0, 7.0, 2.2, 'center', 0), ('L', 61.0, 33.0, 2.6, 'left', 0),
    ('USB', 4.0, 25.0, 2.4, 'center', -90),
    ('MS51PC0AE', 46.0, 21.0, 3.6, 'center', 0), ('8051 / 32K flash', 46.0, 26.0, 2.4, 'center', 0),
]
PIN1 = [(38.5 - 2.6, 37.8), (68.0 + 2.6, 3.5), (80.5, 11.0 - 2.6), (24.0 - 2.6, 46.5), (47.5 - 2.6, 46.5)]


def kapak_yazilari():
    g = None
    for metin, x, y, boy, hiza, aci in YAZILAR:
        cx, cy = K(x, y)
        t = (cq.Workplane('XY').workplane(offset=Z1).center(cx, cy).transformed(rotate=(0, 0, aci))
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
    """3D modeli olmayan parçalar: USB-C (HRO TYPE-C-31-M-12) ve TS-1187A butonlar."""
    g = kutu(0.0, USB_Y - 4.47, 7.35, USB_Y + 4.47, PCB_T, PCB_T + 3.26)
    for x, y in BUTONLAR.values():
        cx, cy = K(x, y)
        g = g.union(kutu(cx - 2.55, cy - 2.55, cx + 2.55, cy + 2.55, PCB_T, PCB_T + SW_H))
    return g


def yerlestir(parca, konumlar, z):
    g = None
    for x, y in konumlar:
        cx, cy = K(x, y)
        q = parca.translate((cx, cy, z))
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
    nb, nl = len(BUTONLAR), len(LEDLER)
    cq.exporters.export(alt, str(OUT / 'kutu_alt.stl'), tolerance=0.02, angularTolerance=0.1)
    cq.exporters.export(ust.rotate((0, 0, 0), (1, 0, 0), 180), str(OUT / 'kutu_ust.stl'), tolerance=0.02,
                        angularTolerance=0.1)
    cq.exporters.export(yan_yana(pm, nb, 12), str(OUT / f'pim_x{nb}.stl'), tolerance=0.01, angularTolerance=0.1)
    boru_baski = br.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, Z1 - (PCB_T + 1.1)))
    cq.exporters.export(yan_yana(boru_baski, nl, 8), str(OUT / f'isik_borusu_x{nl}.stl'), tolerance=0.01,
                        angularTolerance=0.1)
    pimler = yerlestir(pm, BUTONLAR.values(), PCB_T + SW_H)
    borular = yerlestir(br, LEDLER.values(), PCB_T + 0.8 + 0.3)
    montaj = (cq.Assembly()
              .add(alt, name='alt_tabla', color=cq.Color(0.20, 0.22, 0.25))
              .add(ust, name='ust_kapak', color=cq.Color(0.85, 0.86, 0.88))
              .add(pimler, name='pimler', color=cq.Color(0.9, 0.3, 0.2))
              .add(borular, name='isik_borulari', color=cq.Color(0.8, 0.9, 1.0, 0.6)))
    montaj.save(str(OUT / 'kutu.step'))
    bb = alt.union(ust).val().BoundingBox()
    print(f'Dış ölçü: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm')

    if len(sys.argv) > 1:
        kart = cq.importers.importStep(sys.argv[1]).translate((-40.0, 80.0, 0.0))  # KiCad sayfa -> kart
        kart = kart.union(yer_tutucular())
        for ad, a, b in (('alt tabla - kart', alt, kart), ('üst kapak - kart', ust, kart),
                         ('pimler - kart', pimler, kart), ('ışık boruları - kart', borular, kart),
                         ('alt tabla - üst kapak', alt, ust), ('üst kapak - pimler', ust, pimler),
                         ('üst kapak - borular', ust, borular)):
            print(f'Çakışma {ad:22} {a.intersect(b).val().Volume():8.3f} mm³')
        # kontrolün gerçekten çakışma yakaladığını göster: kapak 3 mm aşağıda header'lara girer
        print(f'Kontrol (kapak 3 mm aşağıda) {ust.translate((0, 0, -3)).intersect(kart).val().Volume():8.1f} mm³')
        ust_parca = kart.val().BoundingBox().zmax
        print(f'En yüksek parça z = {ust_parca:.2f} mm, kapak alt yüzü z = {Z_KAPAK_ALT:.2f} mm, '
              f'boşluk {Z_KAPAK_ALT - ust_parca:.2f} mm')
