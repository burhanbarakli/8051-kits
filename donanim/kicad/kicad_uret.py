"""kart_tanim.py'den KiCad 9 şeması (stc89_kart.kicad_sch) ve proje dosyası üretir.

Kullanım:  python kicad_uret.py <KiCad sembol klasörü>
  macOS:   /Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols
  Linux:   /usr/share/kicad/symbols
  Windows: "C:/Program Files/KiCad/9.0/share/kicad/symbols"

Semboller kütüphaneden kopyalanıp şemaya gömülür. Her pinin ucuna net etiketi
(label) konur; tanımda olmayan pinlere bağlantısız (no-connect) işareti konur.
"""
import copy
import json
import re
import sys
import uuid
from pathlib import Path

from kart_tanim import NOTES, PARTS, POWER_FLAGS

PROJECT = 'stc89_kart'
OUT = Path(__file__).parent
NS = uuid.UUID('6f1c2d1e-89c5-4c52-9a00-000000008052')


class Q(str):
    """Tırnaklı S-ifadesi dizgisi."""


def uid(*key):
    # Kararlı UUID: dosya her üretildiğinde aynı kalır, git farkları temiz olur
    return Q(str(uuid.uuid5(NS, '/'.join(map(str, key)))))


TOKEN = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')


def parse(text):
    stack, cur = [], []
    for tok in TOKEN.findall(text):
        if tok == '(':
            stack.append(cur)
            cur = []
        elif tok == ')':
            done, cur = cur, stack.pop()
            cur.append(done)
        elif tok.startswith('"'):
            cur.append(Q(tok[1:-1].replace('\\"', '"').replace('\\\\', '\\')))
        else:
            cur.append(tok)
    return cur[0]


def dump(x, depth=0):
    if isinstance(x, list):
        if not any(isinstance(i, list) for i in x):
            return '(' + ' '.join(dump(i) for i in x) + ')'
        pad = '\n' + '\t' * (depth + 1)
        head = [dump(i) for i in x if not isinstance(i, list)]
        body = [dump(i, depth + 1) for i in x if isinstance(i, list)]
        return '(' + ' '.join(head) + pad + pad.join(body) + ')'
    if isinstance(x, Q):
        return '"' + x.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(x, float):
        return f'{x:.4f}'.rstrip('0').rstrip('.')
    return str(x)


def child(node, key):
    return next((c for c in node if isinstance(c, list) and c and c[0] == key), None)


def children(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


# ---------------------------------------------------------------- kütüphane
_libs = {}


def lib_symbol(lib_id, libdir):
    """Kütüphane sembolünü 'Lib:Ad' adıyla, extends çözülmüş olarak döndürür."""
    lib, name = lib_id.split(':')
    if lib not in _libs:
        _libs[lib] = {s[1]: s for s in children(parse((libdir / f'{lib}.kicad_sym').read_text(encoding='utf-8')), 'symbol')}
    syms = _libs[lib]
    sym = copy.deepcopy(syms[name])
    ext = child(sym, 'extends')
    if ext:
        base = copy.deepcopy(syms[ext[1]])
        props = {p[1]: p for p in children(sym, 'property')}
        merged = []
        for item in base:
            if isinstance(item, list) and item[0] == 'property' and item[1] in props:
                merged.append(props.pop(item[1]))
            elif isinstance(item, list) and item[0] == 'symbol':
                item[1] = Q(item[1].replace(ext[1], name, 1))
                merged.append(item)
            else:
                merged.append(item)
        merged.extend(props.values())
        sym = merged
    sym[1] = Q(lib_id)
    return sym


def pins_of(sym):
    """(numara, x, y, açı) listesi; yalnızca 1. birim ve normal gövde stili."""
    out = []
    for sub in children(sym, 'symbol'):
        unit, style = map(int, sub[1].rsplit('_', 2)[1:])
        if unit not in (0, 1) or style not in (0, 1):
            continue
        for p in children(sub, 'pin'):
            at = child(p, 'at')
            out.append((str(child(p, 'number')[1]), float(at[1]), float(at[2]), int(float(at[3]))))
    return out


# ---------------------------------------------------------------- şema öğeleri
FONT = ['effects', ['font', ['size', 1.27, 1.27]]]
LABEL_DIR = {0: (180, 'right'), 180: (0, 'left'), 90: (270, 'right'), 270: (90, 'left')}


def r(v):
    return round(v, 4)


def label(net, x, y, pin_angle, key):
    ang, just = LABEL_DIR[pin_angle % 360]
    return ['label', Q(net), ['at', r(x), r(y), ang],
            ['effects', ['font', ['size', 1.27, 1.27]], ['justify', just, 'bottom']], ['uuid', uid('lbl', *key)]]


def instance(ref, lib_id, value, footprint, lcsc, x, y, sym, root):
    props = {p[1]: p for p in children(sym, 'property')}
    node = ['symbol', ['lib_id', Q(lib_id)], ['at', x, y, 0], ['unit', 1],
            ['exclude_from_sim', 'no'], ['in_bom', (child(sym, 'in_bom') or [0, 'yes'])[1]],
            ['on_board', (child(sym, 'on_board') or [0, 'yes'])[1]], ['dnp', 'no'],
            ['uuid', uid('sym', ref)]]
    fields = [('Reference', ref), ('Value', value), ('Footprint', footprint),
              ('Datasheet', props.get('Datasheet', [0, Q('~')])[1]), ('LCSC', lcsc)]
    for k, (fname, fval) in enumerate(fields):
        lp = props.get(fname)
        at = child(lp, 'at') if lp else None
        px, py = (float(at[1]), float(at[2])) if at else (0.0, -2.54 * (k - 1))
        angle = (at[3] if at and len(at) > 3 else 0)
        prop = ['property', Q(fname), Q(fval), ['at', r(x + px), r(y - py), angle]]
        if fname not in ('Reference', 'Value'):
            prop.append(['hide', 'yes'])
        # Yazı yönü ve hizası kütüphanedekiyle aynı olsun
        effects = copy.deepcopy(child(lp, 'effects')) if lp and child(lp, 'effects') else copy.deepcopy(FONT)
        prop.append([e for e in effects if not (isinstance(e, list) and e[0] == 'hide')])
        node.append(prop)
    for num in sorted({p[0] for p in pins_of(sym)}):
        node.append(['pin', Q(num), ['uuid', uid('pin', ref, num)]])
    node.append(['instances', ['project', Q(PROJECT), ['path', Q('/' + root), ['reference', Q(ref)], ['unit', 1]]]])
    return node


def build(libdir):
    root = uid('root')
    lib_syms, items, used = {}, [], set()
    nets = {}

    def place(ref, lib_id, value, footprint, lcsc, pinmap, xy):
        sym = lib_syms.setdefault(lib_id, lib_symbol(lib_id, libdir))
        x, y = xy
        items.append(instance(ref, lib_id, value, footprint, lcsc, x, y, sym, root))
        pins = pins_of(sym)
        missing = set(pinmap) - {p[0] for p in pins}
        if missing:
            raise SystemExit(f'{ref}: sembolde olmayan pinler {sorted(missing)}')
        seen = {}
        for num, px, py, ang in pins:
            ax, ay = r(x + px), r(y - py)
            net = pinmap.get(num)
            if net and not ref.startswith('#'):
                nets.setdefault(net, set()).add(f'{ref}.{num}')
            if (ax, ay) in seen:
                # üst üste (stacked) pinler tek etiket alır; hepsi aynı nette olmalı
                if seen[(ax, ay)] != net:
                    raise SystemExit(f'{ref}.{num}: üst üste pinler farklı netlerde')
                continue
            seen[(ax, ay)] = net
            if net:
                items.append(label(net, ax, ay, ang, (ref, num)))
            else:
                items.append(['no_connect', ['at', ax, ay], ['uuid', uid('nc', ref, num)]])

    for part in PARTS:
        place(*part)
    for k, (net, xy) in enumerate(POWER_FLAGS):
        place(f'#FLG0{k + 1}', 'power:PWR_FLAG', 'PWR_FLAG', '', '', {'1': net}, xy)
    for k, (xy, text) in enumerate(NOTES):
        items.append(['text', Q(text), ['exclude_from_sim', 'no'], ['at', xy[0], xy[1], 0],
                      ['effects', ['font', ['size', 2.0, 2.0]], ['justify', 'left', 'bottom']], ['uuid', uid('txt', k)]])

    sch = ['kicad_sch', ['version', 20250114], ['generator', Q('eeschema')], ['generator_version', Q('9.0')],
           ['uuid', root], ['paper', Q('A3')],
           ['title_block', ['title', Q('STC12C5A60S2 Geliştirme Kartı')], ['rev', Q('A')],
            ['comment', 1, Q('Web Serial ile yüklenebilir 8051 kartı (ADC + PWM), otomatik ISP güç kesici')]],
           ['lib_symbols', *lib_syms.values()],
           *items,
           ['sheet_instances', ['path', Q('/'), ['page', Q('1')]]],
           ['embedded_fonts', 'no']]
    return sch, nets


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    sch, nets = build(Path(sys.argv[1]))
    (OUT / f'{PROJECT}.kicad_sch').write_text(dump(sch) + '\n', encoding='utf-8')
    pro = {'meta': {'filename': f'{PROJECT}.kicad_pro', 'version': 3},
           'sheets': [[sch[4][1], 'Root']],
           'text_variables': {}}
    (OUT / f'{PROJECT}.kicad_pro').write_text(json.dumps(pro, indent=2) + '\n', encoding='utf-8')
    (OUT / 'beklenen_netler.json').write_text(
        json.dumps({n: sorted(v) for n, v in sorted(nets.items())}, indent=1, ensure_ascii=False) + '\n',
        encoding='utf-8')
    print(f'{PROJECT}.kicad_sch: {len(PARTS)} parça, {len(nets)} net')


if __name__ == '__main__':
    main()
