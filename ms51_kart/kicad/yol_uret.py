"""Yerleşimi yapılmış PCB'nin yollarını Freerouting ile çizer ve GND dökümü ekler.

İki adımda çalışır (KiCad'in Python ortamında; arada Freerouting):

  python3 yol_uret.py dsn     # yol kurallarını yazar, ms51_kart.dsn üretir
  java -jar freerouting-1.9.0.jar -de ms51_kart.dsn -do ms51_kart.ses -mp 30
  python3 yol_uret.py ses     # yolları içe alır, iki katmana GND dökümü ekler

pcb_uret.py'den hemen sonra çalıştırılır; mevcut yolları ve dökümleri siler.
"""
import math
import sys

import pcbnew

from kicad_uret import PROJECT

mm = pcbnew.FromMM
PCB = f'{PROJECT}.kicad_pcb'
GUC_NETLER = ['/+5V', '/VBUS']   # 0.4 mm; GND ince çizilir, dökümle güçlenir
DOKUM_PAYI = 0.5                             # dökümün kart kenarından içeri mesafesi (mm)


def kurallar(board):
    ds = board.GetDesignSettings()
    ns = ds.m_NetSettings
    d = ns.GetDefaultNetclass()
    d.SetTrackWidth(mm(0.25))
    d.SetClearance(mm(0.2))
    d.SetViaDiameter(mm(0.6))
    d.SetViaDrill(mm(0.3))
    guc = pcbnew.NETCLASS('Guc')
    guc.SetTrackWidth(mm(0.4))
    guc.SetClearance(mm(0.2))
    guc.SetViaDiameter(mm(0.8))
    guc.SetViaDrill(mm(0.4))
    ns.SetNetclass('Guc', guc)
    ns.ClearNetclassPatternAssignments()
    for n in GUC_NETLER:
        ns.SetNetclassPatternAssignment(n, 'Guc')
    ns.RecomputeEffectiveNetclasses()
    board.SynchronizeNetsAndNetClasses(True)
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_MinClearance = mm(0.15)
    ds.m_ViasMinSize = mm(0.5)
    ds.m_MinThroughDrill = mm(0.3)


def kenar_via_yasagi(board, genislik=0.8):
    """Kart kenarı boyunca via ve yol yasak şeritleri: Freerouting kenar payını (0.5 mm) bilmiyor.
    Yalnızca yönlendirme için; 'ses' adımında temizle() ile silinir."""
    k = board.GetBoardEdgesBoundingBox()
    x0, y0, x1, y1 = k.GetX(), k.GetY(), k.GetRight(), k.GetBottom()
    g = mm(genislik)
    for ax, ay, bx, by in ((x0, y0, x1, y0 + g), (x0, y1 - g, x1, y1), (x0, y0, x0 + g, y1), (x1 - g, y0, x1, y1)):
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        z.SetLayerSet(pcbnew.LSET.AllCuMask())
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((ax, ay), (bx, ay), (bx, by), (ax, by)):
            ol.Append(x, y)
        board.Add(z)


def temizle(board):
    # Remove() ve RemoveAll() KiCad 9 Python'da çöküyor; Delete() güvenli
    for z in list(board.Zones()):
        board.Delete(z)
    for t in list(board.GetTracks()):
        board.Delete(t)


def usb_kopruleri(board):
    """USB-C'de iki yüzün D+/D- pad'lerini (A6-B6, A7-B7) birleştiren kısa köprüler (F.Cu).
    Freerouting 0,5 mm aralıklı pad'ler arasında bunu her zaman bulamıyor (KiCad 10 kütüphanesiyle
    A6 açıkta kaldı); köprüler DSN'den önce çizilir ve Freerouting onlara bağlanır.
    D+ sağdan (soketin içine doğru), D- soldan dolaşır. Aynı yol zaten varsa tekrar çizmez."""
    fp = board.FindFootprintByReference('J1')
    pad = {p.GetNumber(): p.GetPosition() for p in fp.Pads()}
    var = {(t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y) for t in board.GetTracks()}
    adet = 0
    for a, b, dx in (('A6', 'B6', 1.052), ('B7', 'A7', -1.052)):
        pa, pb = pad[a], pad[b]
        ka = pcbnew.VECTOR2I(pa.x + mm(dx), pa.y)
        kb = pcbnew.VECTOR2I(pb.x + mm(dx), pb.y)
        for s0, s1 in ((pa, ka), (ka, kb), (kb, pb)):
            if (s0.x, s0.y, s1.x, s1.y) in var:
                continue
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(s0)
            t.SetEnd(s1)
            t.SetWidth(mm(0.25))
            t.SetLayer(pcbnew.F_Cu)
            t.SetNet(fp.FindPadByNumber(a).GetNet())
            board.Add(t)
            adet += 1
    return adet


def gnd_dokumu(board):
    kenar = board.GetBoardEdgesBoundingBox()
    x0, y0 = kenar.GetX() + mm(DOKUM_PAYI), kenar.GetY() + mm(DOKUM_PAYI)
    x1, y1 = kenar.GetRight() - mm(DOKUM_PAYI), kenar.GetBottom() - mm(DOKUM_PAYI)
    gnd = board.FindNet('/GND')
    for katman in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(katman)
        z.SetNet(gnd)
        z.SetLocalClearance(mm(0.3))
        z.SetMinThickness(mm(0.25))
        z.SetThermalReliefGap(mm(0.3))
        z.SetThermalReliefSpokeWidth(mm(0.4))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetAssignedPriority(0)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            ol.Append(x, y)
        board.Add(z)
    # USB-C'nin GND ve kılıf pad'leri kart kenarında, ICP'nin GND pini yollar arasında sıkışık:
    # termal kollar sığmadığı için döküme tam bağlanırlar
    for ref in ('J1', 'J6'):
        for pad in board.FindFootprintByReference(ref).Pads():
            if pad.GetNetname() == '/GND':
                pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    # Önce adacıkları silmeden doldur, iki katmanda da dökümün içinde kalan noktalara
    # dikiş viası koy, sonra adacık silerek yeniden doldur: sinyal yolları arasında kalıp
    # tek katmanda kopuk kalan döküm parçaları böylece diğer katmana bağlanıp korunur.
    for z in board.Zones():
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    n = dikis_viasi(board, gnd, x0, y0, x1, y1)
    for z in board.Zones():
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    # adacık silindikten sonra iki katmanda da dökümün içinde kalmayan dikiş vialarını at
    dolgu = [z.GetFilledPolysList(z.GetLayer()) for z in board.Zones()]
    sarkan = [v for v in board.GetTracks() if v.Type() == pcbnew.PCB_VIA_T and v.GetNetname() == '/GND'
              and v.GetWidth(pcbnew.F_Cu) == mm(0.6) and v.GetDrill() == mm(0.3)
              and not all(d.Contains(v.GetPosition()) for d in dolgu)]
    for v in sarkan:
        board.Delete(v)
    if sarkan:
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    return n - len(sarkan)


def dikis_viasi(board, gnd, x0, y0, x1, y1, aralik=3.0, cap=0.6, delik=0.3):
    """Dökümün iki katmanda da tamamen içinde kalan ızgara noktalarına GND viası koyar.
    Pin header'lar dışındaki parçaların altına (courtyard içine) via konmaz."""
    dolgu = {z.GetLayer(): z.GetFilledPolysList(z.GetLayer()) for z in board.Zones()}
    alti = [fp.GetCourtyard(pcbnew.F_CrtYd) for fp in board.GetFootprints()
            if not fp.GetFPID().GetLibItemName().wx_str().startswith('PinHeader')]
    r = mm(cap / 2 + 0.05)
    adet = 0
    y = y0 + mm(aralik / 2)
    while y < y1:
        x = x0 + mm(aralik / 2)
        while x < x1:
            daire = pcbnew.SHAPE_POLY_SET()
            daire.NewOutline()
            for k in range(16):
                a = 2 * math.pi * k / 16
                daire.Append(int(x + r * math.cos(a)), int(y + r * math.sin(a)))
            nokta = pcbnew.VECTOR2I(int(x), int(y))
            if all(_icinde(daire, p) for p in dolgu.values()) and not any(c.Contains(nokta) for c in alti):
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
                v.SetWidth(mm(cap))
                v.SetDrill(mm(delik))
                v.SetNet(gnd)
                board.Add(v)
                adet += 1
            x += mm(aralik)
        y += mm(aralik)
    return adet


def _icinde(daire, dolgu):
    kalan = pcbnew.SHAPE_POLY_SET(daire)
    kalan.BooleanSubtract(dolgu)
    return kalan.OutlineCount() == 0


adim = sys.argv[1] if len(sys.argv) > 1 else ''
board = pcbnew.LoadBoard(PCB)
if adim == 'dsn':
    temizle(board)
    kurallar(board)
    usb_kopruleri(board)
    pcbnew.SaveBoard(PCB, board)
    kenar_via_yasagi(board)   # yalnızca DSN'e girer, kart dosyasına kaydedilmez
    if not pcbnew.ExportSpecctraDSN(board, f'{PROJECT}.dsn'):
        raise SystemExit('DSN dışa aktarılamadı')
    print(f'{PROJECT}.dsn yazıldı')
elif adim == 'ses':
    temizle(board)
    if not pcbnew.ImportSpecctraSES(board, f'{PROJECT}.ses'):
        raise SystemExit('SES içe alınamadı')
    usb_kopruleri(board)   # SES'te zaten varsa eklenmez
    yollar = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
    vialar = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    dikis = gnd_dokumu(board)
    pcbnew.SaveBoard(PCB, board)
    print(f'{PCB}: {len(yollar)} yol, {len(vialar)} via + {dikis} GND dikiş viası, GND dökümü F.Cu + B.Cu')
else:
    raise SystemExit(__doc__)
