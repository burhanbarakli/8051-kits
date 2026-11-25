// STC12C5Axx seri bootloader (ISP) yükleyicisi, Web Serial API için.
//
// Protokol stcgal'in "stc12" sürücüsünün (github.com/grigorig/stcgal, MIT) birebir
// karşılığıdır: aynı paket çerçevesi, el sıkışma, silme, 128 baytlık yazma blokları ve
// seçenek paketi. Bağımlılığı yoktur, ES modülü olarak içe aktarılır:
//
//   import { WebSerialTransport, programStc12, parseIntelHex } from './stc12.js';
//   const port = await navigator.serial.requestPort();
//   const code = parseIntelHex(await file.text());
//   await programStc12(new WebSerialTransport(port), code, { log: console.log });
//
// Kart tarafı (otomatik ISP): DTR aktif + RTS pasif iken VCC_MCU kesilir. STC
// bootloader'ı yalnızca soğuk açılışta 0x7F bekler; yükleyici gücü kesip açar ve
// hemen 0x7F göndermeye başlar. Otomatik reset çalışmazsa SW1'e basıp bırakmak yeter.

export const DEFAULTS = {
  handshakeBaud: 9600,  // MCU bu hızı 0x7F darbelerinden kendisi algılar
  transferBaud: 9600,   // el sıkışmadan farklıysa port yeniden açılır (deneysel)
  autoReset: true,
  powerOffMs: 500,      // VCC_MCU'nun boşalması için (R9 + C5/C6)
  connectTimeoutMs: 20000,
};

const PACKET_START = [0x46, 0xb9];
const PACKET_END = 0x16;
const PACKET_MCU = 0x68;
const PACKET_HOST = 0x6a;
const BLOCK = 128;           // yazma bloğu
const ERASE_COUNTDOWN = 0x0d;

export class StcError extends Error {}
export class FramingError extends StcError {}
export class TimeoutError extends StcError {}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const be16 = (b, i) => (b[i] << 8) | b[i + 1];
const u16 = (v) => [(v >> 8) & 0xff, v & 0xff];
const u32 = (v) => [(v >>> 24) & 0xff, (v >>> 16) & 0xff, (v >>> 8) & 0xff, v & 0xff];
const hex = (b) => Array.from(b, (x) => x.toString(16).padStart(2, '0')).join(' ');

// Python round(): yarımlarda çifte yuvarlar (stcgal ile aynı BRT değeri için)
function pyRound(x) {
  const r = Math.round(x);
  return Math.abs(x % 1) === 0.5 && r % 2 !== 0 ? r - 1 : r;
}

// ------------------------------------------------------------------ modeller
// STC12C5Axx ailesi: magic = 0xD1 | (tip + boyut kodu). stcgal models.py ile aynı.
const SIZES = { 0x04: 8, 0x08: 16, 0x10: 32, 0x14: 40, 0x18: 48, 0x1a: 52, 0x1c: 56, 0x1e: 60 };
const KINDS = { 0x00: 'X', 0x20: 'CCP', 0x40: 'AD', 0x60: 'S2' };

export function findModel(magic) {
  if (magic >> 8 !== 0xd1) return null;
  const kind = KINDS[magic & 0xe0];
  const kb = SIZES[magic & 0x1f];
  if (!kind || !kb) return null;
  return { name: `STC12C5A${String(kb).padStart(2, '0')}${kind}`, magic, code: kb * 1024 };
}

// ------------------------------------------------------------------ paketler
export function buildPacket(payload) {
  const body = [PACKET_HOST, ...u16(payload.length + 6), ...payload];
  const csum = body.reduce((a, b) => a + b, 0) & 0xffff;
  return Uint8Array.from([...PACKET_START, ...body, ...u16(csum), PACKET_END]);
}

// MCU'dan gelen tam paketi doğrular, yükü döndürür
export function parsePacket(packet) {
  if (packet[packet.length - 1] !== PACKET_END) throw new FramingError('çerçeve sonu hatalı');
  const csum = be16(packet, packet.length - 3);
  let calc = 0;
  for (let i = 2; i < packet.length - 3; i++) calc += packet[i];
  if ((calc & 0xffff) !== csum) throw new FramingError('sağlama toplamı hatalı');
  return packet.slice(5, packet.length - 3);
}

// ------------------------------------------------------------------ Intel HEX
export function parseIntelHex(text) {
  const mem = new Map();
  let base = 0;
  let end = 0;
  let done = false;
  for (const [n, raw] of text.split(/\r?\n/).entries()) {
    const line = raw.trim();
    if (!line) continue;
    if (line[0] !== ':' || line.length < 11 || line.length % 2 === 0) {
      throw new StcError(`HEX satır ${n + 1}: geçersiz kayıt`);
    }
    const b = [];
    for (let i = 1; i < line.length; i += 2) b.push(parseInt(line.substr(i, 2), 16));
    if (b.some(Number.isNaN) || b.length !== b[0] + 5) throw new StcError(`HEX satır ${n + 1}: geçersiz kayıt`);
    if (b.reduce((a, x) => a + x, 0) & 0xff) throw new StcError(`HEX satır ${n + 1}: sağlama toplamı hatalı`);
    const [len, , , type] = b;
    const data = b.slice(4, 4 + len);
    if (type === 0x00) {
      const addr = base + be16(b, 1);
      data.forEach((x, i) => mem.set(addr + i, x));
      end = Math.max(end, addr + len);
    } else if (type === 0x01) {
      done = true;
      break;
    } else if (type === 0x02) {
      base = be16(data, 0) << 4;
    } else if (type === 0x04) {
      base = be16(data, 0) << 16;
    } // 0x03/0x05 (başlangıç adresi) 8051 için önemsiz
  }
  if (!done) throw new StcError('HEX dosyası eksik (bitiş kaydı yok)');
  const out = new Uint8Array(end).fill(0xff);
  for (const [addr, x] of mem) out[addr] = x;
  return out;
}

// ------------------------------------------------------------------ Web Serial
// Seri port soyutlaması. Testlerde aynı arayüzü sağlayan sahte bir sınıf kullanılır.
export class WebSerialTransport {
  // parity: STC12 bootloader'ı 'even', Nuvoton ISP 'none' kullanır
  constructor(port, { parity = 'even' } = {}) {
    this.port = port;
    this.parity = parity;
    this.buf = [];
    this.waiter = null;
    this.reading = null;
  }

  async open(baudRate) {
    await this.port.open({ baudRate, dataBits: 8, stopBits: 1, parity: this.parity, bufferSize: 4096 });
    this.closing = false;
    this.reading = this.readLoop();
  }

  async readLoop() {
    // Eşlik (parity) / çerçeve hataları akışı kırar; port.readable yenisiyle devam eder
    while (this.port.readable && !this.closing) {
      this.reader = this.port.readable.getReader();
      try {
        for (;;) {
          const { value, done } = await this.reader.read();
          if (done) break;
          for (const x of value) this.buf.push(x);
          this.wake();
        }
      } catch (e) {
        if (!this.closing) this.lastError = e;
      } finally {
        this.reader.releaseLock();
      }
    }
  }

  wake() {
    if (this.waiter) {
      this.waiter();
      this.waiter = null;
    }
  }

  async close() {
    this.closing = true;
    if (this.reader) await this.reader.cancel().catch(() => {});
    await this.reading;
    await this.port.close();
  }

  async setBaud(baudRate) {
    // Web Serial açık portta hız değiştiremez: kapat, yeniden aç, sinyalleri hemen geri yükle
    const signals = this.signals;
    await this.close();
    await this.open(baudRate);
    if (signals) await this.setSignals(signals);
  }

  async setSignals(signals) {
    this.signals = signals;
    await this.port.setSignals(signals);
  }

  async write(bytes) {
    const w = this.port.writable.getWriter();
    try {
      await w.write(bytes);
    } finally {
      w.releaseLock();
    }
  }

  available() {
    return this.buf.length;
  }

  flushInput() {
    this.buf.length = 0;
  }

  // n bayt okur: ilk bayt için firstMs, sonrakiler için baytlar arası interMs bekler
  async read(n, firstMs, interMs) {
    const out = [];
    while (out.length < n) {
      if (!this.buf.length) {
        const ms = out.length ? interMs : firstMs;
        let timer;
        const got = await Promise.race([
          new Promise((r) => { this.waiter = () => r(true); }),
          new Promise((r) => { timer = setTimeout(() => r(false), ms); }),
        ]);
        clearTimeout(timer);
        if (!got && !this.buf.length) throw new TimeoutError('okuma zaman aşımı');
        continue;
      }
      out.push(this.buf.shift());
    }
    return Uint8Array.from(out);
  }
}

// ------------------------------------------------------------------ protokol
class Stc12Session {
  constructor(t, opts) {
    this.t = t;
    this.o = { ...DEFAULTS, ...opts };
    this.log = this.o.log || (() => {});
    this.firstMs = 500;   // senkron sırasında kısa, sonra 15 s (stcgal ile aynı)
    this.interMs = 500;
  }

  async writePacket(payload) {
    await this.t.write(buildPacket(payload));
  }

  async readPacket() {
    const t = this.t;
    let head = await t.read(1, this.firstMs, this.interMs);
    // Bazı BSL sürümleri durum paketini çerçeve başlangıcı olmadan gönderir
    if (head[0] === PACKET_MCU) {
      head = [...PACKET_START, PACKET_MCU];
    } else {
      if (head[0] !== PACKET_START[0]) throw new FramingError('çerçeve başlangıcı hatalı');
      head = [head[0], ...(await t.read(2, this.interMs, this.interMs))];
      if (head[1] !== PACKET_START[1]) throw new FramingError('çerçeve başlangıcı hatalı');
      if (head[2] !== PACKET_MCU) throw new FramingError('paket yönü hatalı');
    }
    const len = await t.read(2, this.interMs, this.interMs);
    const n = be16(len, 0);
    if (n < 6) throw new FramingError('paket uzunluğu hatalı');
    const rest = await t.read(n - 3, this.interMs, this.interMs);
    return parsePacket(Uint8Array.from([...head, ...len, ...rest]));
  }

  async pulse(deadline) {
    while (!this.t.available()) {
      if (Date.now() > deadline) throw new StcError(
        'MCU yanıt vermedi. Kart bağlı mı? SW1 (ISP) düğmesine basıp bırakarak tekrar deneyin.');
      if (this.o.signal?.aborted) throw new StcError('iptal edildi');
      await this.t.write(Uint8Array.of(0x7f));
      await sleep(30);
    }
  }

  async connect() {
    const { t, o } = this;
    t.flushInput();
    if (o.autoReset) {
      this.log('MCU gücü kesiliyor (DTR aktif, RTS pasif)...');
      await t.setSignals({ dataTerminalReady: true, requestToSend: false });
      await sleep(o.powerOffMs);
      await t.setSignals({ dataTerminalReady: false, requestToSend: false });
    } else {
      this.log('SW1 (ISP) düğmesine basıp bırakın...');
    }
    this.log('MCU bekleniyor...');
    const deadline = Date.now() + o.connectTimeoutMs;
    for (;;) {
      try {
        await this.pulse(deadline);
        let status = await this.readPacket();
        if (status[0] === 0x80) {
          // yeniden onay isteyen BSL'ler (stcgal get_status_packet)
          await t.write(Uint8Array.from([...PACKET_START, PACKET_HOST, 0x00, 0x07, 0x80, 0x00, 0xf1, PACKET_END]));
          await this.pulse(deadline);
          status = await this.readPacket();
        }
        if (status.length < 23) throw new StcError('durum paketi çok kısa');
        this.status = status;
        break;
      } catch (e) {
        // Tampon boşaltılmaz: sonraki denemede okuma bir sonraki bayttan başlar ve
        // paket başlangıcına kendiliğinden hizalanır (stcgal ile aynı)
        if (!(e instanceof FramingError || e instanceof TimeoutError)) throw e;
      }
    }
    this.firstMs = 15000;
    this.interMs = 1000;
    this.initialize();
  }

  initialize() {
    const s = this.status;
    this.magic = be16(s, 20);
    this.model = findModel(this.magic);
    if (!this.model) {
      throw new StcError(`Desteklenmeyen MCU (magic ${hex(s.slice(20, 22))}). Bu yükleyici STC12C5Axx ailesi içindir.`);
    }
    let counter = 0;
    for (let i = 0; i < 8; i++) counter += be16(s, 1 + 2 * i);
    counter /= 8;
    this.clockHz = (this.o.handshakeBaud * counter * 12) / 7;
    this.bslVersion = `${s[17] >> 4}.${s[17] & 0x0f}${String.fromCharCode(s[18])}`;
    if (s.length < 29) throw new StcError('durum paketindeki seçenekler eksik');
    this.msr = [s[23], s[24], s[25], s[27]];
    this.log(`MCU: ${this.model.name}, saat ${(this.clockHz / 1e6).toFixed(3)} MHz, BSL ${this.bslVersion}`);
  }

  calculateBaud() {
    const baud = this.o.transferBaud;
    const brt = 256 - pyRound(this.clockHz / (baud * 16));
    if (brt <= 1 || brt > 255) throw new StcError(`${baud} baud bu saat frekansında ayarlanamıyor`);
    const brtCsum = (2 * (256 - brt)) & 0xff;
    const actual = this.clockHz / (16 * (256 - brt));
    const err = (Math.abs(baud - actual) * 100) / baud;
    if (err > 5) this.log(`UYARI: baud hatası %${err.toFixed(2)}, daha düşük bir hız seçin.`);
    const f = this.clockHz;
    const iap = f < 1e6 ? 0x87 : f < 2e6 ? 0x86 : f < 3e6 ? 0x85 : f < 6e6 ? 0x84
      : f < 12e6 ? 0x83 : f < 20e6 ? 0x82 : f < 24e6 ? 0x81 : 0x80;
    return { brt, brtCsum, iap, delay: 0x80 };
  }

  async switchBaud(baud) {
    if (this.currentBaud !== baud) {
      await this.t.setBaud(baud);
      this.currentBaud = baud;
    }
  }

  async expect(magic, what) {
    const r = await this.readPacket();
    if (r[0] !== magic) throw new StcError(`${what}: beklenmeyen yanıt ${hex(r.slice(0, 4))}`);
    return r;
  }

  async handshake() {
    const { brt, brtCsum, iap, delay } = this.calculateBaud();
    const { handshakeBaud, transferBaud } = this.o;
    this.log(`${transferBaud} baud'a geçiliyor...`);
    await this.writePacket([0x50, 0x00, 0x00, 0x36, 0x01, ...u16(this.magic)]);
    await this.expect(0x8f, 'el sıkışma');
    // yeni ayarı dene
    await this.writePacket([0x8f, 0xc0, brt, 0x3f, brtCsum, delay, iap]);
    await sleep(100);
    await this.switchBaud(transferBaud);
    await this.expect(0x8f, 'hız testi');
    await this.switchBaud(handshakeBaud);
    // ayarı kalıcı yap
    await this.writePacket([0x8e, 0xc0, brt, 0x3f, brtCsum, delay]);
    await sleep(100);
    await this.switchBaud(transferBaud);
    await this.expect(0x84, 'hız ayarı');
  }

  async erase(eraseSize) {
    const blks = Math.ceil(eraseSize / 512) * 2;
    const size = Math.ceil(this.model.code / 512) * 2;
    this.log(`Flash siliniyor (${blks} blok)...`);
    const p = [0x84, 0xff, 0x00, blks, 0x00, 0x00, size, ...new Array(12).fill(0)];
    for (let i = 0x80; i > ERASE_COUNTDOWN; i--) p.push(i);
    await this.writePacket(p);
    const r = await this.expect(0x00, 'silme');
    if (r.length >= 8) this.uid = r.slice(1, 8);
  }

  async program(data) {
    this.log(`${data.length} bayt yazılıyor...`);
    for (let i = 0; i < data.length; i += BLOCK) {
      const p = new Array(BLOCK + 7).fill(0);
      p.splice(3, 4, ...u16(i), ...u16(BLOCK));
      data.slice(i, i + BLOCK).forEach((x, k) => { p[7 + k] = x; });
      await this.writePacket(p);
      await this.expect(0x00, 'yazma');
      this.o.progress?.(Math.min(i + BLOCK, data.length), data.length);
    }
    await this.writePacket([0x69, 0x00, 0x00, 0x36, 0x01, ...u16(this.magic)]);
    await this.expect(0x8d, 'yazma bitişi');
  }

  async programOptions() {
    // MCU'nun mevcut seçenek baytları değiştirilmeden geri yazılır
    const m = this.msr;
    await this.writePacket([0x8d, m[0], m[1], m[2], m[3], 0xff, 0xff, 0xff, 0xff, m[3],
      ...new Array(7).fill(0xff), ...u32(Math.trunc(this.clockHz))]);
    const r = await this.expect(0x50, 'seçenekler');
    if (!this.uid) this.uid = r.slice(18, 25);
  }

  async disconnect() {
    await this.writePacket([0x82]);  // MCU'yu kullanıcı programına başlatır
  }
}

// code: Uint8Array (0 adresinden başlayan ikili görüntü). Port kapalı olmalı; işlem
// bitince kapatılır. Dönüş: { model, clockHz, bslVersion, uid }
export async function programStc12(transport, code, opts = {}) {
  if (!code.length) throw new StcError('Program boş');
  const s = new Stc12Session(transport, opts);
  const { handshakeBaud } = s.o;
  await transport.open(handshakeBaud);
  s.currentBaud = handshakeBaud;
  try {
    await s.connect();
    if (code.length > s.model.code) {
      throw new StcError(`Program ${code.length} bayt, ${s.model.name} flash'ı ${s.model.code} bayt`);
    }
    // 512 bayt sınırına 0xFF ile tamamla (stcgal ile aynı)
    const padded = new Uint8Array(Math.ceil(code.length / 512) * 512).fill(0xff);
    padded.set(code);
    await s.handshake();
    await s.erase(padded.length);
    await s.program(padded);
    s.log('Seçenekler yazılıyor...');
    await s.programOptions();
    await s.disconnect();
    s.log(`Tamam. UID ${hex(s.uid || [])}. Program çalışıyor.`);
    return { model: s.model.name, clockHz: s.clockHz, bslVersion: s.bslVersion, uid: s.uid };
  } finally {
    await transport.close().catch(() => {});
  }
}
