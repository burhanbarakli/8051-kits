"""KiCad'in dışa aktardığı netlist (out.net) ile beklenen_netler.json'u karşılaştırır.

  kicad-cli sch export netlist -o out.net stc89_kart.kicad_sch
  python dogrula.py
"""
import json
from pathlib import Path

from kicad_uret import children, child, parse

here = Path(__file__).parent
expected = {k: set(v) for k, v in json.loads((here / 'beklenen_netler.json').read_text(encoding='utf-8')).items()}
actual = {}
for net in children(child(parse((here / 'out.net').read_text(encoding='utf-8')), 'nets'), 'net'):
    name = str(child(net, 'name')[1]).lstrip('/')
    nodes = {f"{child(n, 'ref')[1]}.{child(n, 'pin')[1]}" for n in children(net, 'node')}
    nodes = {n for n in nodes if not n.startswith('#')}
    if name.startswith('unconnected-'):
        continue
    if nodes:
        actual[name] = nodes

ok = True
for name in sorted(set(expected) | set(actual)):
    e, a = expected.get(name, set()), actual.get(name, set())
    if e != a:
        ok = False
        print(f'FARK {name}: eksik={sorted(e - a)} fazla={sorted(a - e)}')
print('Tüm netler eşleşiyor' if ok else 'Netlerde fark var')
print(f'{len(actual)} net, {sum(map(len, actual.values()))} bağlantı')
