"""stcgal'in STC12 akışında gönderdiği baytları kaydeder (JS yükleyicinin karşılaştırma verisi).

stcgal'in kendi testindeki gerçek STC12C5A60S2 kaydı (tests/stc12c5a60s2.yml) MCU
yanıtı olarak verilir; stcgal'in seri porta yazdığı her paket ve baud değişikliği
golden-*.json dosyalarına yazılır. stc12.test.mjs aynı yanıtlarla JS yükleyiciyi
çalıştırıp çıktıyı bu dosyalarla karşılaştırır.

Kullanım (pyserial, tqdm, pyyaml kurulu bir Python ile):
  git clone https://github.com/grigorig/stcgal.git
  python golden_uret.py <stcgal klasörü>
"""
import json
import sys
from pathlib import Path
from unittest import mock

STCGAL = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(STCGAL))

import yaml  # noqa: E402
import stcgal.frontend  # noqa: E402

OUT = Path(__file__).parent
TRACE = yaml.safe_load((STCGAL / 'tests' / 'stc12c5a60s2.yml').read_text())

# (dosya, el sıkışma baud, aktarım baud)
CASES = [('golden-9600-9600.json', 9600, 9600), ('golden-2400-19200.json', 2400, 19200)]


class FakeSerial:
    """Yazılan baytları ve baud değişikliklerini sırayla kaydeden sahte seri port."""

    def __init__(self, events, **kwargs):
        object.__setattr__(self, 'events', events)

    def __setattr__(self, name, value):
        if name == 'baudrate':
            self.events.append({'baud': value})
        object.__setattr__(self, name, value)

    def write(self, data):
        if bytes(data) != b'\x7f':  # senkron darbeleri karşılaştırmaya girmez
            self.events.append({'tx': list(bytes(data))})

    def inWaiting(self):
        return 1

    def flush(self):
        pass

    def flushInput(self):
        pass

    def close(self):
        pass


for name, handshake, baud in CASES:
    events = []
    opts = mock.MagicMock()
    opts.protocol = TRACE['protocol']
    opts.autoreset = False
    opts.port = ''
    opts.baud = baud
    opts.handshake = handshake
    opts.eeprom_image = None
    opts.option = None
    opts.debug = False
    opts.version = False
    opts.code_image.name = 'test.bin'
    opts.code_image.read.return_value = bytes(TRACE['code_data'])
    responses = [bytes(r) for r in TRACE['responses']]
    with mock.patch('stcgal.protocols.serial.Serial', lambda **kw: FakeSerial(events, **kw)), \
            mock.patch('stcgal.protocols.StcBaseProtocol.read_packet', side_effect=responses), \
            mock.patch('stcgal.protocols.time.sleep'), mock.patch('sys.stdout'):
        assert stcgal.frontend.StcGal(opts).run() == 0, name
    (OUT / name).write_text(json.dumps({
        'handshake': handshake, 'baud': baud,
        'code': TRACE['code_data'], 'responses': TRACE['responses'], 'events': events,
    }) + '\n')
    print(f'{name}: {sum("tx" in e for e in events)} paket')
