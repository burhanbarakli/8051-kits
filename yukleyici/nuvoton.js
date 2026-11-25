// Nuvoton MS51 UART ISP yükleyici (Web Serial).
//
// Karşı taraf ../ms51_kart/bootloader içindeki LDROM bootloader'ıdır; Nuvoton'un kendi
// ISP_UART0 örneğiyle de uyumludur. Protokol:
//   - 115200 8N1, her iki yönde 64 baytlık paket
//   - istek: [0] komut, [4..7] paket no (LE), [8..63] veri
//   - yanıt: [0..1] isteğin 64 baytının toplamı, [4..7] paket no + 1, [8..] veri
//   - CMD_UPDATE_APROM: [8..11] adres (0), [12..15] boyut, [16..63] ilk 48 bayt;
//     sonraki paketler [8..63] = 56 bayt. Yanıtın [8..9]'u yazılan baytların toplamı.
// Kart, CH340'ın DTR'si ile resetlenir; bootloader her reset'ten sonra 500 ms bağlantı bekler.

import { TimeoutError, WebSerialTransport, parseIntelHex } from './stc12.js';

export { WebSerialTransport, parseIntelHex, TimeoutError };

export const MS51_DEFAULTS = {
  baud: 115200,
  autoReset: true,         // DTR ile reset; false ise kullanıcı RESET'e basar
  connectTimeoutMs: 15000,
  retryMs: 80,             // CONNECT tekrar aralığı; bootloader 50 ms'de yarım paketi atar
  eraseTimeoutMs: 5000,    // UPDATE_APROM ilk yanıtı tüm APROM silindikten sonra gelir
};

export const CMD = {
  UPDATE_APROM: 0xA0, READ_CONFIG: 0xA2, ERASE_ALL: 0xA3, SYNC_PACKNO: 0xA4,
  GET_FWVER: 0xA6, RUN_APROM: 0xAB, CONNECT: 0xAE, GET_DEVICEID: 0xB1,
};
export const OUR_FW_VERSION = 0x51;   // ../ms51_kart/bootloader; Nuvoton örneği 0x28 döner

export class IspError extends Error {}

const HATA = { 1: 'flash doğrulama hatası', 2: 'program APROM\'a sığmıyor (en fazla 30 KB)' };

export function sum16(bytes) {
  let s = 0;
  for (const b of bytes) s += b;
  return s & 0xffff;
}

export function buildRequest(cmd, packNo, data = [], offset = 8) {
  const p = new Uint8Array(64);
  p[0] = cmd;
  p[4] = packNo & 0xff;
  p[5] = (packNo >>> 8) & 0xff;
  p[6] = (packNo >>> 16) & 0xff;
  p[7] = (packNo >>> 24) & 0xff;
  p.set(data.slice(0, 64 - offset), offset);
  return p;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const u16 = (r, i) => r[i] | (r[i + 1] << 8);
const u32 = (r, i) => (r[i] | (r[i + 1] << 8) | (r[i + 2] << 16) | (r[i + 3] << 24)) >>> 0;
const hex = (bytes) => Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join(' ');

class Ms51Session {
  constructor(t, opts) {
    this.t = t;
    this.o = { ...MS51_DEFAULTS, ...opts };
    this.log = this.o.log || (() => {});
    this.packNo = 1;
  }

  checkReply(req, r) {
    if (u16(r, 0) !== sum16(req)) throw new IspError('yanıt toplamı tutmuyor');
    if (u32(r, 4) !== ((u32(req, 4) + 1) >>> 0)) throw new IspError('yanıt paket numarası tutmuyor');
  }

  async request(cmd, data = [], { offset = 8, timeoutMs = 1000 } = {}) {
    const req = buildRequest(cmd, this.packNo, data, offset);
    await this.t.write(req);
    const r = await this.t.read(64, timeoutMs, 200);
    this.checkReply(req, r);
    this.packNo += 2;
    return r;
  }

  async connect() {
    const t = this.t;
    if (this.o.autoReset) {
      // CH340 DTR# aktif düşüktür: DTR'yi açmak düşen kenar üretir, 100 nF üzerinden RST'yi çeker
      await t.setSignals({ dataTerminalReady: false, requestToSend: false });
      await sleep(100);
      await t.setSignals({ dataTerminalReady: true, requestToSend: false });
      this.log('Kart resetlendi, bootloader bekleniyor...');
    } else {
      this.log('Bağlantı bekleniyor: karttaki RESET düğmesine basıp bırakın.');
    }
    const start = Date.now();
    const deadline = start + this.o.connectTimeoutMs;
    let uyarildi = !this.o.autoReset;
    while (Date.now() < deadline) {
      t.flushInput();
      const req = buildRequest(CMD.CONNECT, 1);
      await t.write(req);
      try {
        const r = await t.read(64, this.o.retryMs, 20);
        this.checkReply(req, r);
        await sleep(30);          // önceki denemelere gecikmiş yanıt varsa at
        t.flushInput();
        this.packNo = 3;
        return;
      } catch (e) {
        if (!(e instanceof TimeoutError) && !(e instanceof IspError)) throw e;
      }
      if (!uyarildi && Date.now() - start > 1500) {
        this.log('Yanıt yok. Otomatik reset çalışmadıysa karttaki RESET düğmesine basın.');
        uyarildi = true;
      }
    }
    throw new IspError('bootloader yanıt vermedi. Kartta bootloader yüklü mü (ICP ile bir kez yüklenir)?');
  }

  async info() {
    const id = (await this.request(CMD.GET_DEVICEID)).slice(8, 12);
    const fw = (await this.request(CMD.GET_FWVER))[8];
    const cfg = (await this.request(CMD.READ_CONFIG)).slice(8, 13);
    const deviceId = (id[3] << 24 | id[2] << 16 | id[1] << 8 | id[0]) >>> 0;
    this.log(`Bağlandı. Cihaz kimliği ${deviceId.toString(16).padStart(8, '0')}, bootloader sürümü 0x${fw.toString(16)}`);
    this.log(`CONFIG: ${hex([cfg[0], cfg[1], cfg[2], cfg[4]])}`);
    if (cfg[0] & 0x80) {
      this.log('Uyarı: CONFIG0.CBS = 1 (APROM\'dan başlar). Bir sonraki reset\'te bootloader çalışmaz; ICP ile CBS = 0 yapın.');
    }
    this.fw = fw;
    return { deviceId, fwVersion: fw, config: [cfg[0], cfg[1], cfg[2], cfg[4]] };
  }

  checkProgress(r, sent) {
    const ours = this.fw === OUR_FW_VERSION;
    if (ours && r[10]) throw new IspError(HATA[r[10]] || `bootloader hata kodu ${r[10]}`);
    if (u16(r, 8) !== (sent & 0xffff)) throw new IspError('yazılan veri toplamı tutmuyor (flash yazılamadı)');
  }

  async program(code) {
    const total = code.length;
    const progress = this.o.progress || (() => {});
    const head = new Uint8Array(56);
    const dv = new DataView(head.buffer);
    dv.setUint32(0, 0, true);          // başlangıç adresi
    dv.setUint32(4, total, true);      // toplam boyut
    head.set(code.slice(0, 48), 8);
    this.log(`APROM siliniyor ve yazılıyor (${total} bayt)...`);
    let sent = sum16(code.slice(0, 48));
    let done = Math.min(48, total);
    let r = await this.request(CMD.UPDATE_APROM, head, { timeoutMs: this.o.eraseTimeoutMs });
    this.checkProgress(r, sent);
    progress(done, total);
    while (done < total) {
      const chunk = code.slice(done, done + 56);
      r = await this.request(0x00, chunk);
      sent += sum16(chunk);
      done += chunk.length;
      this.checkProgress(r, sent);
      progress(done, total);
    }
  }

  async run() {
    await this.t.write(buildRequest(CMD.RUN_APROM, this.packNo));   // yanıt gelmez
    await sleep(50);
  }
}

// MS51'e program yükler. code: Uint8Array (APROM 0 adresinden). transport: WebSerialTransport
// (eşlik bu fonksiyonda 'none' yapılır) ya da aynı arayüzü sağlayan bir nesne.
export async function programMs51(transport, code, opts = {}) {
  if (!code || !code.length) throw new IspError('yüklenecek program boş');
  if ('parity' in transport) transport.parity = 'none';
  const s = new Ms51Session(transport, opts);
  await transport.open(s.o.baud);
  try {
    await s.connect();
    const info = await s.info();
    await s.program(code);
    s.log('Yazma tamamlandı, program başlatılıyor.');
    await s.run();
    return info;
  } finally {
    await transport.close().catch(() => {});
  }
}
