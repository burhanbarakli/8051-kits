"""JLCPCB üretim dosyalarını ../uretim/ klasörüne yazar (KiCad'in Docker imajında çalışır).

  python3 uretim.py

Çıktılar:
  stc12_kart-gerber.zip  Gerber + delik dosyaları (PCB siparişine yüklenir)
  jlcpcb-bom.csv         Dizgi (SMT montaj) için BOM, yalnızca SMD parçalar
  jlcpcb-cpl.csv         Dizgi için parça konumları, yalnızca SMD parçalar
  delikli-parcalar.csv   Elle lehimlenecek delikli (THT) parçalar
"""
import csv
import subprocess
import zipfile
from pathlib import Path

from kart_tanim import PARTS
from kicad_uret import PROJECT

PCB = f'{PROJECT}.kicad_pcb'
OUT = Path('../uretim')
GERBER = OUT / 'gerber'
KATMANLAR = 'F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts'


def cli(*args):
    subprocess.run(['kicad-cli', 'pcb', 'export', *args, PCB], check=True, stdout=subprocess.DEVNULL)


GERBER.mkdir(parents=True, exist_ok=True)
for f in GERBER.iterdir():
    f.unlink()
cli('gerbers', '--layers', KATMANLAR, '--subtract-soldermask', '-o', f'{GERBER}/')
cli('drill', '--format', 'excellon', '--excellon-separate-th', '--generate-map', '--map-format', 'gerberx2',
    '-u', 'mm', '-o', f'{GERBER}/')
with zipfile.ZipFile(OUT / 'stc12_kart-gerber.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(GERBER.iterdir()):
        z.write(f, f.name)

# Parça konumları: KiCad'in SMD listesi -> JLCPCB CPL biçimi
pos = OUT / 'konumlar.csv'
cli('pos', '--format', 'csv', '--units', 'mm', '--side', 'both', '--smd-only', '-o', str(pos))
with open(pos, newline='', encoding='utf-8') as f:
    konumlar = list(csv.DictReader(f))
pos.unlink()
smd = {k['Ref'] for k in konumlar}
with open(OUT / 'jlcpcb-cpl.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    for k in konumlar:
        w.writerow([k['Ref'], f"{float(k['PosX']):.4f}mm", f"{float(k['PosY']):.4f}mm",
                    'Top' if k['Side'] == 'top' else 'Bottom', f"{float(k['Rot']):.1f}"])


# BOM satırları ../BOM.csv'den (aynı parçalar tek satırda); SMD olanlar dizgiye, kalanlar elle lehime
with open('../BOM.csv', newline='', encoding='utf-8') as f:
    bom = list(csv.DictReader(f))
kalan = {p[0] for p in PARTS}
with open(OUT / 'jlcpcb-bom.csv', 'w', newline='', encoding='utf-8') as fs, \
        open(OUT / 'delikli-parcalar.csv', 'w', newline='', encoding='utf-8') as ft:
    ws, wt = csv.writer(fs), csv.writer(ft)
    ws.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
    wt.writerow(['Comment', 'Designator', 'LCSC Part #', 'Adet', 'Aciklama'])
    for r in bom:
        refs = r['Designator'].split(',')
        kalan -= set(refs)
        if set(refs) <= smd:
            ws.writerow([r['Comment'], r['Designator'], r['Footprint'], r['LCSC Part #']])
        elif set(refs) & smd:
            raise SystemExit(f'BOM satırında SMD ve THT karışık: {r["Designator"]}')
        else:
            wt.writerow([r['Comment'], r['Designator'], r['LCSC Part #'], r['Qty'], r['Aciklama']])
if kalan:
    raise SystemExit(f'BOM.csv\'de olmayan parçalar: {sorted(kalan)}')

print(f'{OUT}: gerber {len(list(GERBER.iterdir()))} dosya, dizgiye {len(smd)} SMD parça')
