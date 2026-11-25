"""Yerleşimi yapılmış PCB'nin yollarını Freerouting ile çizer ve GND dökümü ekler.

İki adımda çalışır (KiCad'in Python ortamında; arada Freerouting):

  python3 yol_uret.py dsn     # yol kurallarını yazar, stc89_kart.dsn üretir
  java -jar freerouting-1.9.0.jar -de stc89_kart.dsn -do stc89_kart.ses -mp 30
  python3 yol_uret.py ses     # yolları içe alır, iki katmana GND dökümü ekler

pcb_uret.py'den hemen sonra çalıştırılır; mevcut yolları ve dökümleri siler.
"""
import math
import sys

import pcbnew

from kicad_uret import PROJECT

mm = pcbnew.FromMM
PCB = f'{PROJECT}.kicad_pcb'
GUC_NETLER = ['/+5V', '/VBUS', '/VCC_MCU']   # 0.4 mm; GND ince çizilir, dökümle güçlenir
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


def temizle(board):
    # Remove() ve RemoveAll() KiCad 9 Python'da çöküyor; Delete() güvenli
    for z in list(board.Zones()):
        board.Delete(z)
    for t in list(board.GetTracks()):
        board.Delete(t)


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
    # USB-C'nin GND ve kılıf pad'leri kart kenarında; termal kollar sığmadığı için döküme tam bağlanır
    for pad in board.FindFootprintByReference('J1').Pads():
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
    return n


def dikis_viasi(board, gnd, x0, y0, x1, y1, aralik=4.0, cap=0.6, delik=0.3):
    """Dökümün iki katmanda da tamamen içinde kalan ızgara noktalarına GND viası koyar."""
    dolgu = {z.GetLayer(): z.GetFilledPolysList(z.GetLayer()) for z in board.Zones()}
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
            if all(_icinde(daire, p) for p in dolgu.values()):
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
    pcbnew.SaveBoard(PCB, board)
    if not pcbnew.ExportSpecctraDSN(board, f'{PROJECT}.dsn'):
        raise SystemExit('DSN dışa aktarılamadı')
    print(f'{PROJECT}.dsn yazıldı')
elif adim == 'ses':
    temizle(board)
    if not pcbnew.ImportSpecctraSES(board, f'{PROJECT}.ses'):
        raise SystemExit('SES içe alınamadı')
    yollar = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
    vialar = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    dikis = gnd_dokumu(board)
    pcbnew.SaveBoard(PCB, board)
    print(f'{PCB}: {len(yollar)} yol, {len(vialar)} via + {dikis} GND dikiş viası, GND dökümü F.Cu + B.Cu')
else:
    raise SystemExit(__doc__)
