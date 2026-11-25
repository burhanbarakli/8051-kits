// stc12.js testleri:  node --test test/
//
// MCU yanıtları stcgal deposundaki gerçek STC12C5A60S2 kaydından (tests/stc12c5a60s2.yml)
// alınmıştır. Beklenen host paketleri stcgal protocols.py (Stc12BaseProtocol) kodundan
// elle türetilmiştir; hesap adımları her beklentinin yanında yazılı.
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { test } from 'node:test';

import {
  buildPacket, findModel, FramingError, parseIntelHex, parsePacket, programStc12, StcError, TimeoutError,
  WebSerialTransport,
} from '../stc12.js';

// --- stcgal tests/stc12c5a60s2.yml: MCU yanıt yükleri (payload)
const STATUS = [0x50, 0x04, 0xBD, 0x04, 0xBC, 0x04, 0xBC, 0x04, 0xBD, 0x04, 0xBC, 0x04, 0xBC, 0x04, 0xBC,
  0x04, 0xBC, 0x62, 0x49, 0x00, 0xD1, 0x7E, 0x8C, 0xFF, 0x7F, 0xF7, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x03,
  0x00, 0xB0, 0x02, 0x2E, 0x6B, 0x00, 0xCD, 0x80, 0x00, 0x00];
const RESPONSES = [
  [0x8F],
  [0x8F, 0xC0, 0x7E, 0x3F, 0xFE, 0xA0, 0x83, 0x04],
  [0x84, 0xC0, 0x7E, 0x3F, 0xFE, 0xA0, 0x04],
  [0x00],
  [0x00, 0x03], [0x00, 0x00], [0x00, 0x00], [0x00, 0x00],
  [0x8D],
  [0x50, 0xFF, 0x7F, 0xF7, 0xFF, 0xFF, 0x03, 0xFF, 0x62, 0x49, 0xFF, 0x7F, 0xF7, 0xFF, 0xFF, 0xFF, 0xFF, 0x01,
    0x00, 0x03, 0x00, 0xB0, 0x02, 0x2E, 0x6B, 0x00, 0xCD, 0x80, 0x00, 0x00],
];
const CODE = Uint8Array.from([49, 50, 51, 52, 53, 54, 55, 56, 57]); // "123456789"

// MCU -> host çerçevesi: 46 B9 68 | uzunluk | yük | sağlama | 16
function mcuFrame(payload, withStart = true) {
  const body = [0x68, (payload.length + 6) >> 8, (payload.length + 6) & 0xff, ...payload];
  const sum = body.reduce((a, b) => a + b, 0) & 0xffff;
  const full = [0x46, 0xB9, ...body, sum >> 8, sum & 0xff, 0x16];
  return withStart ? full : full.slice(2);
}

// Sahte seri port: host paketlerini kaydeder, her pakete kayıttaki sıradaki yanıtı verir
class MockTransport {
  constructor({ statusPrefix = [], statusWithStart = true, afterPulses = 3 } = {}) {
    this.buf = [];
    this.events = [];
    this.responses = RESPONSES.map((r) => mcuFrame(r));
    this.statusBytes = [...statusPrefix, ...mcuFrame(STATUS, statusWithStart)];
    this.afterPulses = afterPulses;
    this.pulses = 0;
    this.statusSent = false;
  }

  async open(baud) { this.events.push({ open: baud }); }
  async close() { this.events.push({ close: true }); }
  async setBaud(baud) { this.events.push({ baud }); }
  async setSignals(s) { this.events.push({ signals: s }); }
  available() { return this.buf.length; }
  flushInput() { this.buf.length = 0; }

  async write(bytes) {
    const b = Array.from(bytes);
    if (b.length === 1 && b[0] === 0x7f) {
      if (!this.statusSent && ++this.pulses >= this.afterPulses) {
        this.statusSent = true;
        this.buf.push(...this.statusBytes);
      }
      return;
    }
    this.events.push({ tx: b });
    const payload = parseHostPacket(b);
    if (payload[0] !== 0x82) this.buf.push(...this.responses.shift());
  }

  async read(n) {
    if (this.buf.length < n) {
      this.buf.length = 0;
      throw new TimeoutError('okuma zaman aşımı');
    }
    return Uint8Array.from(this.buf.splice(0, n));
  }
}

// Host paketini doğrular (başlangıç, yön, uzunluk, sağlama, bitiş) ve yükü döndürür
function parseHostPacket(p) {
  assert.deepEqual(p.slice(0, 3), [0x46, 0xB9, 0x6A], 'host paket başlangıcı');
  assert.equal((p[3] << 8) | p[4], p.length - 2, 'host paket uzunluğu');
  assert.equal(p[p.length - 1], 0x16, 'host paket sonu');
  const sum = p.slice(2, -3).reduce((a, b) => a + b, 0) & 0xffff;
  assert.equal((p[p.length - 3] << 8) | p[p.length - 2], sum, 'host paket sağlaması');
  return p.slice(5, -3);
}

const payloads = (events) => events.filter((e) => e.tx).map((e) => parseHostPacket(e.tx));
const countdown = () => Array.from({ length: 0x80 - 0x0d }, (_, i) => 0x80 - i); // 0x80..0x0E

function block(addr, data) {
  const p = [0, 0, 0, addr >> 8, addr & 0xff, 0x00, 0x80];
  for (let i = 0; i < 128; i++) p.push(i < data.length ? data[i] : 0xff);
  return p;
}

// Ortak beklentiler (H = el sıkışma baud):
//  frekans sayacı ortalaması = (0x4BD*2 + 0x4BC*6) / 8 = 1212.25
//  saat = H * 1212.25 * 12 / 7
//  magic = D1 7E -> STC12C5A60S2, flash 61440 -> silme boyutu 61440/512*2 = 240 (0xF0)
//  kod 9 bayt -> 512'ye 0xFF ile tamamlanır -> 2 silme bloğu, 4 yazma bloğu
//  seçenek baytları (msr) = durum[23..25] + durum[27] = FF 7F F7 FF
function expectedPayloads({ brt, brtCsum, iap, clock }) {
  return [
    [0x50, 0x00, 0x00, 0x36, 0x01, 0xD1, 0x7E],
    [0x8F, 0xC0, brt, 0x3F, brtCsum, 0x80, iap],
    [0x8E, 0xC0, brt, 0x3F, brtCsum, 0x80],
    [0x84, 0xFF, 0x00, 0x02, 0x00, 0x00, 0xF0, ...new Array(12).fill(0), ...countdown()],
    block(0, CODE), block(128, []), block(256, []), block(384, []),
    [0x69, 0x00, 0x00, 0x36, 0x01, 0xD1, 0x7E],
    [0x8D, 0xFF, 0x7F, 0xF7, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, ...new Array(7).fill(0xFF),
      clock >>> 24, (clock >> 16) & 0xff, (clock >> 8) & 0xff, clock & 0xff],
    [0x82],
  ];
}

test('9600/9600: tek hız, port yeniden açılmaz', async () => {
  const t = new MockTransport();
  const progress = [];
  const r = await programStc12(t, CODE, { powerOffMs: 1, progress: (a, b) => progress.push([a, b]) });
  // saat = 9600*1212.25*12/7 = 19950171.43 Hz
  // BRT = 256 - round(19950171.43 / (9600*16)) = 256 - round(129.88) = 126 (0x7E)
  // BRT sağlaması = 2*(256-126) & 0xFF = 260 & 0xFF = 0x04;  IAP: 12-20 MHz -> 0x82
  assert.deepEqual(payloads(t.events), expectedPayloads({ brt: 0x7E, brtCsum: 0x04, iap: 0x82, clock: 19950171 }));
  assert.equal(r.model, 'STC12C5A60S2');
  assert.equal(r.bslVersion, '6.2I');
  assert.equal(Math.trunc(r.clockHz), 19950171);
  assert.deepEqual(Array.from(r.uid), [0x00, 0x03, 0x00, 0xB0, 0x02, 0x2E, 0x6B]); // seçenek yanıtı [18:25]
  assert.equal(t.events.filter((e) => e.baud).length, 0);
  assert.deepEqual(progress.at(-1), [512, 512]);
  // otomatik ISP: önce DTR aktif + RTS pasif (güç kesik), sonra ikisi pasif (güç açık)
  assert.deepEqual(t.events.filter((e) => e.signals).map((e) => e.signals), [
    { dataTerminalReady: true, requestToSend: false },
    { dataTerminalReady: false, requestToSend: false },
  ]);
  assert.deepEqual(t.events[0], { open: 9600 });
  assert.deepEqual(t.events.at(-1), { close: true });
});

test('2400/19200: stcgal varsayılanı, hız değişimi sırası', async () => {
  const t = new MockTransport();
  await programStc12(t, CODE, { powerOffMs: 1, handshakeBaud: 2400, transferBaud: 19200 });
  // saat = 2400*1212.25*12/7 = 4987542.86 Hz
  // BRT = 256 - round(4987542.86 / 307200) = 256 - round(16.24) = 240 (0xF0)
  // BRT sağlaması = 2*16 = 0x20;  IAP: 3-6 MHz -> 0x84
  assert.deepEqual(payloads(t.events), expectedPayloads({ brt: 0xF0, brtCsum: 0x20, iap: 0x84, clock: 4987542 }));
  // stcgal handshake(): test paketi -> 19200'de oku -> 2400'e dön -> ayar paketi -> 19200
  const seq = t.events.filter((e) => e.baud || e.tx).map((e) => (e.baud ? e.baud : e.tx[5]));
  assert.deepEqual(seq.slice(0, 7), [0x50, 0x8F, 19200, 2400, 0x8E, 19200, 0x84]);
});

test('durum paketi çerçeve başlangıcı olmadan ve öncesinde çöp baytla gelse de bağlanır', async () => {
  const t = new MockTransport({ statusPrefix: [0x00, 0x7F, 0x13], statusWithStart: false });
  const r = await programStc12(t, CODE, { powerOffMs: 1 });
  assert.equal(r.model, 'STC12C5A60S2');
});

test('desteklenmeyen MCU (STC89 magic) açık hata verir', async () => {
  const t = new MockTransport();
  t.statusBytes = mcuFrame([...STATUS.slice(0, 20), 0xF0, 0x02, ...STATUS.slice(22)]);
  await assert.rejects(programStc12(t, CODE, { powerOffMs: 1 }), /Desteklenmeyen MCU/);
});

test('program flash boyutunu aşarsa hata', async () => {
  const t = new MockTransport();
  await assert.rejects(programStc12(t, new Uint8Array(61441), { powerOffMs: 1 }), /flash/);
});

test('paket çerçevesi', () => {
  // 46 B9 6A 00 07 82 00 F3 16 : uzunluk = 1+6, sağlama = 6A+00+07+82 = F3
  assert.deepEqual(Array.from(buildPacket([0x82])), [0x46, 0xB9, 0x6A, 0x00, 0x07, 0x82, 0x00, 0xF3, 0x16]);
  const f = Uint8Array.from(mcuFrame([0x8F]));
  assert.deepEqual(Array.from(parsePacket(f)), [0x8F]);
  f[5] ^= 1;
  assert.throws(() => parsePacket(f), FramingError);
});

test('model tablosu stcgal models.py ile aynı', () => {
  assert.deepEqual(findModel(0xD17E), { name: 'STC12C5A60S2', magic: 0xD17E, code: 61440 });
  assert.equal(findModel(0xD15E).name, 'STC12C5A60AD');
  assert.equal(findModel(0xD128).name, 'STC12C5A16CCP');
  assert.equal(findModel(0xD104).code, 8192);
  assert.equal(findModel(0xF002), null);
});

test('Intel HEX', () => {
  const hex = [
    ':03000000020003F8', // 0000: 02 00 03 (LJMP 0003)
    ':0200040080FE7C',   // 0004: 80 FE (boşluk 0003 -> 0xFF)
    ':00000001FF',
  ].join('\n');
  assert.deepEqual(Array.from(parseIntelHex(hex)), [0x02, 0x00, 0x03, 0xFF, 0x80, 0xFE]);
  assert.throws(() => parseIntelHex(':03000000020003F9\n:00000001FF'), /sağlama/);
  assert.throws(() => parseIntelHex(':03000000020003F8'), /bitiş/);
  assert.throws(() => parseIntelHex('merhaba\n:00000001FF'), StcError);
});

// --- WebSerialTransport: Web Serial API'yi taklit eden sahte SerialPort ile
// MCU benzetimi: el sıkışma hızında dinler; 0x8F (hız testi) yanıtını aktarım hızında
// verip el sıkışma hızına döner, 0x8E (hız ayarı) yanıtından sonra aktarım hızında kalır.
// Yanlış hızda gelen paketler yok sayılır, yanlış hızda okunan yanıtlar bozuk bayt olur.
class FakeSerialPort {
  constructor(transferBaud) {
    this.transferBaud = transferBaud;
    this.responses = RESPONSES.map((r) => mcuFrame(r));
    this.pulses = 0;
    this.opens = [];
    this.signals = [];
    this.readable = null;
    this.writable = null;
  }

  async open({ baudRate, parity }) {
    if (this.readable) throw new Error('port zaten açık');
    assert.equal(parity, 'even');
    this.baud = baudRate;
    this.mcuBaud ??= baudRate;
    this.opens.push(baudRate);
    this.readable = new ReadableStream({ start: (c) => { this.ctrl = c; } });
    this.writable = new WritableStream({ write: (chunk) => this.receive(Array.from(chunk)) });
  }

  async close() {
    if (this.readable.locked || this.writable.locked) throw new TypeError('akış kilitli');
    this.readable = null;
    this.writable = null;
  }

  async setSignals(s) { this.signals.push(s); }

  deliver(bytes, baud) {
    if (!this.readable) return; // port kapalıyken gelen veri kaybolur
    this.ctrl.enqueue(Uint8Array.from(baud === this.baud ? bytes : bytes.map(() => 0xF0)));
  }

  receive(b) {
    if (b.length === 1 && b[0] === 0x7f) {
      if (++this.pulses === 3) this.deliver(mcuFrame(STATUS), this.baud); // MCU hızı kendisi algılar
      return;
    }
    if (this.baud !== this.mcuBaud) return;
    const cmd = parseHostPacket(b)[0];
    if (cmd === 0x82) return;
    const resp = this.responses.shift();
    if (cmd === 0x8f && b.length === 15) {        // hız testi: yanıt yeni hızda, sonra geri dön
      setTimeout(() => this.deliver(resp, this.transferBaud), 150);
    } else if (cmd === 0x8e) {                    // hız ayarı: yeni hızda kal
      this.mcuBaud = this.transferBaud;
      setTimeout(() => this.deliver(resp, this.transferBaud), 150);
    } else {
      this.deliver(resp, this.mcuBaud);
    }
  }
}

for (const [h, b] of [[9600, 9600], [2400, 19200]]) {
  test(`WebSerialTransport ile uçtan uca ${h}/${b}`, async () => {
    const port = new FakeSerialPort(b);
    const r = await programStc12(new WebSerialTransport(port), CODE,
      { powerOffMs: 1, handshakeBaud: h, transferBaud: b });
    assert.equal(r.model, 'STC12C5A60S2');
    assert.equal(port.responses.length, 0);
    assert.equal(port.readable, null, 'port kapatılmalı');
    assert.deepEqual(port.opens, h === b ? [h] : [h, b, h, b]);
    // yeniden açılıştan sonra sinyaller güç açık konumuna geri yüklenir
    assert.ok(port.signals.slice(2).every((s) => !s.dataTerminalReady && !s.requestToSend));
  });
}

test('WebSerialTransport: MCU yanıt vermezse zaman aşımı hatası', async () => {
  const port = new FakeSerialPort(9600);
  port.receive = () => {};
  await assert.rejects(programStc12(new WebSerialTransport(port), CODE,
    { powerOffMs: 1, connectTimeoutMs: 300 }), /MCU yanıt vermedi/);
  assert.equal(port.readable, null, 'hata sonrası port kapatılmalı');
});

// stcgal'in kendisi çalıştırılıp golden-*.json üretildiyse (test/golden_uret.py), birebir karşılaştır
for (const [file, h, b] of [['golden-9600-9600.json', 9600, 9600], ['golden-2400-19200.json', 2400, 19200]]) {
  const path = new URL(file, import.meta.url);
  test(`stcgal çıktısıyla birebir: ${file}`, { skip: !existsSync(path) && 'golden dosyası yok' }, async () => {
    const golden = JSON.parse(readFileSync(path, 'utf8'));
    const t = new MockTransport();
    await programStc12(t, Uint8Array.from(golden.code), { powerOffMs: 1, handshakeBaud: h, transferBaud: b });
    const norm = (evts, start) => {
      let cur = start;
      return evts.flatMap((e) => {
        if (e.tx) return [e.tx];
        if (e.baud && e.baud !== cur) { cur = e.baud; return [e.baud]; }
        return [];
      });
    };
    assert.deepEqual(norm(t.events, h), norm(golden.events, h));
  });
}
