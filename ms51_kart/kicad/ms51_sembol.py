"""kart_tanim.MS51_PINLER'den KiCad sembol kütüphanesi (ms51.kicad_sym) üretir.

KiCad'in standart kütüphanesinde Nuvoton MS51 yok. Pinler sol/sağ iki sütunda,
taraf ve sıra kart_tanim.py'deki tabloda.

  python ms51_sembol.py
"""
from pathlib import Path

from kart_tanim import MS51_PINLER
from kicad_uret import Q, dump

OUT = Path(__file__).parent
AD = 'MS51PC0AE'
ADIM = 2.54
SIRA = 17                      # sütun başına sıra (boşluklar dahil)
GENISLIK = 17.78               # gövdenin yarı genişliği (iki sütunun pin adları sığsın)
UST = (SIRA - 1) / 2 * ADIM    # ilk sıranın y'si
FONT = ['effects', ['font', ['size', 1.27, 1.27]]]


def prop(ad, deger, x, y, gizli=False):
    p = ['property', Q(ad), Q(deger), ['at', x, y, 0], FONT]
    if gizli:
        p.append(['hide', 'yes'])
    return p


def pin(num, ad, taraf, sira, tip):
    y = round(UST - sira * ADIM, 4)
    x, aci = (-(GENISLIK + ADIM), 0) if taraf == 'L' else (GENISLIK + ADIM, 180)
    return ['pin', tip, 'line', ['at', x, y, aci], ['length', ADIM],
            ['name', Q(ad), FONT], ['number', Q(num), FONT]]


def sembol():
    govde = ['symbol', Q(f'{AD}_0_1'),
             ['rectangle', ['start', -GENISLIK, UST + ADIM], ['end', GENISLIK, -(UST + ADIM)],
              ['stroke', ['width', 0.254], ['type', 'default']], ['fill', ['type', 'background']]]]
    pinler = ['symbol', Q(f'{AD}_1_1'), *[pin(n, *v) for n, v in MS51_PINLER.items()]]
    return ['symbol', Q(AD), ['pin_names', ['offset', 1.016]], ['exclude_from_sim', 'no'],
            ['in_bom', 'yes'], ['on_board', 'yes'],
            prop('Reference', 'U', 0, UST + 2 * ADIM),
            prop('Value', AD, 0, -(UST + 2 * ADIM)),
            prop('Footprint', 'Package_QFP:LQFP-32_7x7mm_P0.8mm', 0, 0, True),
            prop('Datasheet', 'https://www.nuvoton.com/products/microcontrollers/8bit-8051-mcus/', 0, 0, True),
            prop('Description', 'Nuvoton MS51 1T 8051, 32KB flash, 2KB XRAM, 12 bit ADC, LQFP-32', 0, 0, True),
            govde, pinler]


if __name__ == '__main__':
    lib = ['kicad_symbol_lib', ['version', 20241209], ['generator', Q('kicad_symbol_editor')],
           ['generator_version', Q('9.0')], sembol()]
    (OUT / 'ms51.kicad_sym').write_text(dump(lib) + '\n', encoding='utf-8')
    (OUT / 'sym-lib-table').write_text(
        '(sym_lib_table\n  (version 7)\n'
        '  (lib (name "MS51")(type "KiCad")(uri "${KIPRJMOD}/ms51.kicad_sym")(options "")(descr "Nuvoton MS51"))\n'
        ')\n', encoding='utf-8')
    print(f'ms51.kicad_sym: {AD}, {len(MS51_PINLER)} pin')
