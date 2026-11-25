// nuvoton.js testleri: yükleyici, ../ms51_kart/bootloader'ın bilgisayarda derlenmiş hâline
// (isp_host; aynı isp.c protokol kodu, flash bir dosyada) karşı uçtan uca çalıştırılır.
//   (cd ../ms51_kart/bootloader && make host) && node --test test/nuvoton.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { CMD, IspError, TimeoutError, buildRequest, programMs51, sum16 } from '../nuvoton.js';

const HOST = fileURLToPath(new URL('../../ms51_kart/bootloader/isp_host', import.meta.url));
const APROM = 30 * 1024;   // LDROM 2 KB
const skip = !existsSync(HOST) && 'isp_host yok: (cd ms51_kart/bootloader && make host)';

// Bootloader sürecini seri port gibi kullanan taşıyıcı (WebSerialTransport ile aynı arayüz)
class ProcessTransport {
  constructor(flashFile, env = {}) {
    this.flashFile = flashFile;
    this.env = env;
    this.buf = [];
    this.waiter = null;
    this.signals = [];
    this.written = [];
  }

  async open(baud) {
    this.baud = baud;
    this.p = spawn(HOST, [this.flashFile], { env: { ...process.env, ...this.env } });
    this.exit = new Promise((r) => this.p.on('exit', (code) => r(code)));
    this.p.stdout.on('data', (d) => {
      for (const x of d) this.buf.push(x);
      if (this.waiter) { this.waiter(); this.waiter = null; }
    });
    this.p.stdin.on('error', () => {});
  }

  async close() {
    this.p.stdin.end();
    return this.exit;
  }

  async setSignals(s) { this.signals.push(s); }

  async write(bytes) {
    this.written.push(Uint8Array.from(bytes));
    this.p.stdin.write(Buffer.from(bytes));
  }

  flushInput() { this.buf.length = 0; }

  async read(n, firstMs, interMs) {
    const out = [];
    while (out.length < n) {
      if (!this.buf.length) {
        let timer;
        const got = await Promise.race([
          new Promise((r) => { this.waiter = () => r(true); }),
          new Promise((r) => { timer = setTimeout(() => r(false), out.length ? interMs : firstMs); }),
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

function tmpFlash(content) {
  const f = join(mkdtempSync(join(tmpdir(), 'ms51-')), 'flash.bin');
  if (content) writeFileSync(f, content);
  return f;
}

function randomCode(n, seed = 1) {
  const c = new Uint8Array(n);
  let x = seed;
  for (let i = 0; i < n; i++) { x = (x * 1103515245 + 12345) >>> 0; c[i] = x >>> 24; }
  return c;
}

function expectFlash(file, code) {
  const f = readFileSync(file);
  assert.equal(f.length, APROM);
  assert.deepEqual(f.subarray(0, code.length), Buffer.from(code));
  assert.ok(f.subarray(code.length).every((b) => b === 0xff), 'programın sonrası boş (0xFF) olmalı');
}

test('paket yapısı', () => {
  const p = buildRequest(CMD.UPDATE_APROM, 0x01020304, [1, 2, 3]);
  assert.equal(p.length, 64);
  assert.deepEqual([...p.slice(0, 11)], [0xa0, 0, 0, 0, 4, 3, 2, 1, 1, 2, 3]);
  assert.equal(sum16(new Uint8Array(64).fill(0xff)), (64 * 255) & 0xffff);
});

test('uçtan uca: 3000 baytlık program yazılır, APROM başlatılır', { skip }, async () => {
  const file = tmpFlash();
  const t = new ProcessTransport(file);
  const code = randomCode(3000);
  const logs = [];
  const steps = [];
  const info = await programMs51(t, code, { log: (m) => logs.push(m), progress: (d) => steps.push(d) });
  assert.equal(await t.exit, 0, 'bootloader RUN_APROM ile çıkmalı');
  expectFlash(file, code);
  assert.equal(info.fwVersion, 0x51);
  assert.deepEqual(info.config, [0x7f, 0xfd, 0xff, 0xff]);
  assert.equal(steps.at(-1), 3000);
  assert.equal(steps[0], 48);
  // DTR ile reset: önce kapalı, sonra açık (CH340 DTR# düşen kenarı)
  assert.deepEqual(t.signals.map((s) => s.dataTerminalReady), [false, true]);
  // CONNECT bootloader yanıt verene kadar tekrarlanır; sonrası: 3 bilgi + 1 UPDATE + veri + RUN
  const rest = t.written.filter((p) => p[0] !== CMD.CONNECT);
  assert.ok(t.written[0][0] === CMD.CONNECT);
  assert.equal(rest.length, 3 + 1 + Math.ceil((3000 - 48) / 56) + 1);
  assert.equal(t.written.at(-1)[0], CMD.RUN_APROM);
});

test('tam 30 KB sığar; eski program tamamen silinir', { skip }, async () => {
  const file = tmpFlash(Buffer.alloc(APROM, 0x00));   // önceden dolu flash
  const big = randomCode(APROM, 7);
  await programMs51(new ProcessTransport(file), big);
  expectFlash(file, big);
  const small = randomCode(100, 9);
  await programMs51(new ProcessTransport(file), small);
  expectFlash(file, small);
});

test('30 KB\'tan büyük program bootloader tarafından reddedilir', { skip }, async () => {
  const file = tmpFlash();
  await assert.rejects(programMs51(new ProcessTransport(file), randomCode(APROM + 1)), /sığmıyor/);
});

test('flash doğrulama hatası yakalanır (sıfır bayt dahil)', { skip }, async () => {
  const file = tmpFlash();
  const code = randomCode(500);
  code[200] = 0x00;   // toplamı değiştirmeyen bayt: yalnızca hata koduyla fark edilir
  await assert.rejects(programMs51(new ProcessTransport(file, { BOZUK_ADRES: '200' }), code), IspError);
});

test('yavaş silme (gerçek çipe yakın, sayfa başı 5 ms) zaman aşımına düşmez', { skip }, async () => {
  const file = tmpFlash();
  const code = randomCode(2000, 3);
  const t0 = Date.now();
  await programMs51(new ProcessTransport(file, { SILME_MS: '5' }), code);
  assert.ok(Date.now() - t0 > 240 * 5, 'tüm APROM silinmiş olmalı');
  expectFlash(file, code);
});

test('bağlantıdan önce gelen yarım paket bootloader\'ı şaşırtmaz', { skip }, async () => {
  const file = tmpFlash();
  const t = new ProcessTransport(file);
  const open = t.open.bind(t);
  t.open = async (b) => { await open(b); t.p.stdin.write(Buffer.alloc(20, 0x5a)); };   // hat gürültüsü
  const code = randomCode(300, 5);
  await programMs51(t, code);
  expectFlash(file, code);
});

test('APROM doluysa bootloader 500 ms sonra kullanıcı programına geçer', { skip }, async () => {
  const file = tmpFlash(Buffer.alloc(APROM, 0x12));
  const t0 = Date.now();
  const p = spawn(HOST, [file]);
  const code = await new Promise((r) => p.on('exit', r));
  const ms = Date.now() - t0;
  assert.equal(code, 0);
  assert.ok(ms >= 450 && ms < 2000, `geçen süre ${ms} ms`);
});

test('APROM boşsa bootloader beklemede kalır', { skip }, async () => {
  const p = spawn(HOST, [tmpFlash()]);
  const exited = await Promise.race([
    new Promise((r) => p.on('exit', () => r(true))),
    new Promise((r) => setTimeout(() => r(false), 1200)),
  ]);
  p.kill();
  assert.equal(exited, false);
});

test('bootloader yoksa açık hata verir', async () => {
  const sessiz = {
    open: async () => {}, close: async () => {}, setSignals: async () => {}, write: async () => {},
    flushInput() {}, read: async () => { await new Promise((r) => setTimeout(r, 5)); throw new TimeoutError('x'); },
  };
  await assert.rejects(programMs51(sessiz, new Uint8Array(10), { connectTimeoutMs: 300 }), /bootloader yanıt vermedi/);
});

// Nuvoton'un kendi ISP_UART0 örneğinin davranışı: yanıt tamponu hiç temizlenmez (önceki
// yanıtların baytları kalır), paket no yalnızca 16 bit artırılır, sürüm 0x28.
class NuvotonOrnegi {
  constructor() {
    this.flash = new Uint8Array(28 * 1024).fill(0xff);
    this.tx = new Uint8Array(64);
    this.buf = [];
    this.prog = false;
  }
  async open() {} async close() {} async setSignals() {} flushInput() { this.buf.length = 0; }
  async write(rx) {
    const tx = this.tx;
    const checksum = () => {
      const s = sum16(rx);
      tx[0] = s & 0xff; tx[1] = s >> 8; tx[4] = (rx[4] + 1) & 0xff; tx[5] = rx[5] + (tx[4] === 0);
    };
    const yaz = (from) => {
      for (let i = from; i < 64 && this.prog; i++) {
        this.flash[this.addr] = rx[i]; this.total += rx[i];
        if (++this.addr === this.size) this.prog = false;
      }
      checksum(); tx[8] = this.total & 0xff; tx[9] = (this.total >> 8) & 0xff;
    };
    let reply = true;
    if (this.prog) { yaz(8); this.buf.push(...tx); }
    switch (rx[0]) {
      case CMD.CONNECT: case CMD.SYNC_PACKNO: checksum(); break;
      case CMD.GET_FWVER: checksum(); tx[8] = 0x28; break;
      case CMD.GET_DEVICEID: checksum(); tx.set([0x4b, 0x00, 0x61, 0x02], 8); break;
      case CMD.READ_CONFIG: checksum(); tx.set([0x7f, 0xfb, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff], 8); break;
      case CMD.RUN_APROM: this.ran = true; reply = false; break;
      case CMD.UPDATE_APROM:
        this.flash.fill(0xff); this.addr = 0; this.total = 0;
        this.size = rx[12] | (rx[13] << 8); this.prog = true; yaz(16); break;
      default: reply = false;
    }
    if (reply) this.buf.push(...tx);
  }
  async read(n) {
    if (this.buf.length < n) throw new TimeoutError('yok');
    return Uint8Array.from(this.buf.splice(0, n));
  }
}

test('Nuvoton\'un kendi ISP_UART0 bootloader\'ıyla da çalışır', async () => {
  const t = new NuvotonOrnegi();
  const code = randomCode(1000, 11);
  const info = await programMs51(t, code);
  assert.equal(info.fwVersion, 0x28);
  assert.ok(t.ran);
  assert.deepEqual(t.flash.subarray(0, 1000), code);
});
