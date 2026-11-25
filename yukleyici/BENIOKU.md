# 8051 Web Yükleyici (STC12 ve Nuvoton MS51)

STC12C5A60S2 kartına (`../donanim`) tarayıcıdan, USB üzerinden program yükler. Programlayıcı gerekmez; çipin ROM'daki fabrika bootloader'ı kullanılır.

| Dosya | Ne |
|---|---|
| `stc12.js` | Yükleyici modülü. Bağımlılığı yok, kendi web arayüzünüze içe aktarılır |
| `index.html` | Hazır demo sayfası: dosya seçimi, hız ayarı, ilerleme çubuğu, günlük |
| `test/stc12.test.mjs` | Node testleri (`node --test test/stc12.test.mjs`) |
| `test/golden_uret.py` | İsteğe bağlı: stcgal'in kendisini çalıştırıp birebir karşılaştırma verisi üretir |
| `nuvoton.js` | MS51 kartı (`../ms51_kart`) için yükleyici. Seri port katmanını `stc12.js`'den alır |
| `test/nuvoton.test.mjs` | MS51 testleri: yükleyici, gerçek bootloader koduna (`../ms51_kart/bootloader`) karşı çalışır |
| `ornek/blink.c` | LED3'ü yakıp söndüren SDCC örneği |

## Çalıştırma

Web Serial yalnızca masaüstü Chrome ve Edge'de çalışır. Sayfa `https://` ya da `http://localhost` üzerinden açılmalıdır; `file://` ile açılırsa modül yüklenmez.

```bash
python3 -m http.server 8052 -d yukleyici
```

Tarayıcıda `http://localhost:8052` adresini açın, `.hex`/`.ihx`/`.bin` dosyasını seçin ve "Port seç ve yükle"ye basın. Kart listede "USB Serial" veya CH340 adıyla görünür.

## Kendi arayüzünüze ekleme

```js
import { WebSerialTransport, programStc12, parseIntelHex } from './stc12.js';

const port = await navigator.serial.requestPort();   // bir kullanıcı tıklamasının içinde çağrılmalı
const code = parseIntelHex(await file.text());         // .bin için: new Uint8Array(await file.arrayBuffer())
const sonuc = await programStc12(new WebSerialTransport(port), code, {
  handshakeBaud: 9600,      // varsayılan
  transferBaud: 9600,       // farklıysa port yeniden açılır (deneysel)
  autoReset: true,          // DTR/RTS ile güç kes-aç; false ise kullanıcı SW1'e basar
  log: (mesaj) => console.log(mesaj),
  progress: (yazilan, toplam) => {},
});
// sonuc: { model: 'STC12C5A60S2', clockHz, bslVersion, uid }
```

`programStc12` portu kendisi açar ve iş bitince kapatır. Hata durumunda `StcError` fırlatır; mesajları Türkçedir.

## Nasıl çalışır

1. Port çift eşlikle (even parity) açılır.
2. Otomatik ISP: DTR aktif, RTS pasif yapılır ve kart VCC_MCU'yu keser. 500 ms sonra ikisi de pasif yapılır ve MCU soğuk açılır. Bu sırada her adımda yalnızca tek sinyal değişir.
3. 30 ms aralıkla `0x7F` gönderilir. Bootloader hızı bu baytlardan kendisi algılar ve durum paketi gönderir. Paket model kodunu, kristal frekansını ve seçenek baytlarını içerir.
4. Akışın geri kalanı stcgal'in `stc12` protokolüyle birebir aynı sırada ilerler:
   - el sıkışma ve hız ayarı
   - flash silme
   - 128 baytlık bloklarla yazma
   - seçenek paketi
   - `0x82` (programı başlat)

**Seçenek baytları:** MCU'nun mevcut ayarları (reset pini, watchdog vb.) değiştirilmeden geri yazılır.

**Hız seçimi:**
- **Varsayılan, 9600 / 9600:** El sıkışma ve aktarım aynı hızda olduğu için port yeniden açılmaz. 4 KB'lık bir program yaklaşık 6 saniyede, 60 KB'lık bir program yaklaşık 85 saniyede yüklenir.
- **Daha hızlı aktarım (19200 ve üstü):** Web Serial açık portun hızını değiştiremediği için port kapatılıp yeniden açılır. Bazı işletim sistemleri ve sürücüler bu sırada DTR/RTS'yi kısa süre değiştirebilir; bu da otomatik ISP devresi üzerinden MCU'nun gücünü kesebilir. Bu yüzden bu seçenek "deneysel" olarak işaretli.
- **2400 baud el sıkışma:** stcgal'in varsayılanı budur. 11.0592 MHz kristalle 2400 baud aktarım hızı ayarlanamaz, bu yüzden 2400 seçilirse aktarım hızı farklı olmalı.

## Program derleme

8051 derleyicisi olarak SDCC (ücretsiz) veya Keil C51 kullanılabilir. SDCC örneği:

```bash
sdcc ornek/blink.c
```

Çıktı olan `blink.ihx` doğrudan yükleyiciye verilir. STC12'ye özgü yazmaçlar (ADC, PCA/PWM, P4SW) için STC'nin `STC12C5A60S2.h` başlık dosyası kullanılır.

## Doğrulama durumu

- **Protokol testi geçti (Node, 13 test).** Test stcgal deposundaki gerçek bir STC12C5A60S2 kaydının MCU yanıtlarını kullanıyor. Gönderilen her paket stcgal kaynağından türetilen beklenen baytlarla karşılaştırılıyor: el sıkışma, BRT hesabı, silme, 4 yazma bloğu, seçenekler ve UID.
- **`WebSerialTransport` testi geçti.** Web Serial'ı taklit eden sahte bir port ile uçtan uca test edildi. Okuma döngüsü, zaman aşımı, çöp baytlardan sonra yeniden hizalanma ve hız değişiminde portun yeniden açılması sınandı.
- **Demo sayfası yüklendi.** Chrome'da açıldı, HEX dosyasını doğru okudu ve konsolda hata çıkmadı.
- **Gerçek donanımda denenmedi.** Kart henüz üretilmediği için otomatik ISP zamanlaması ve hız seçenekleri doğrulanmadı.
- **stcgal'in kendisiyle birebir aynı.** `test/golden_uret.py` stcgal'i (commit `fdf5fdd`) aynı MCU yanıtlarıyla çalıştırıp gönderdiği her paketi ve hız değişikliğini `test/golden-9600-9600.json` ile `test/golden-2400-19200.json` dosyalarına kaydetti. JS yükleyicinin çıktısı iki modda da bu kayıtla bayt bayt ve sıra sıra aynı: 11 paket, ayrıca 2400/19200'de hız değişimleri. Yeniden üretmek için:

  ```bash
  git clone https://github.com/grigorig/stcgal.git /tmp/stcgal
  pip install pyserial tqdm pyyaml
  python3 yukleyici/test/golden_uret.py /tmp/stcgal
  node --test yukleyici/test/stc12.test.mjs
  ```

- **Örnek kod derlenmedi.** `ornek/blink.c` bu makinede SDCC olmadığı için derlenmedi.

## Nuvoton MS51

Demo sayfasında **Kart: Nuvoton MS51** seçilir. Kod içinden kullanmak için:

```js
import { WebSerialTransport, parseIntelHex } from './stc12.js';
import { programMs51 } from './nuvoton.js';

const port = await navigator.serial.requestPort();
await programMs51(new WebSerialTransport(port, { parity: 'none' }), parseIntelHex(hexMetni), {
  autoReset: true,          // DTR ile reset; false ise kullanıcı RESET'e basar
  log: console.log,
  progress: (yazilan, toplam) => {},
});
```

MS51'de bootloader fabrikadan gelmez. Her çipe bir kez ICP ile yüklenir; bkz. `../ms51_kart/bootloader/BENIOKU.md`.

Yükleme akışı:
1. 115200 8N1.
2. DTR açılır; düşen kenar kartı resetler.
3. Yükleyici 80 ms aralıkla `CMD_CONNECT` gönderir.
4. Bootloader yanıt verince sırasıyla kimlik, sürüm ve CONFIG okunur.
5. `CMD_UPDATE_APROM` ile APROM silinir ve yazılmaya başlanır. Sonraki her pakette 56 bayt yazılır, yanıttaki toplam kontrol edilir.
6. `CMD_RUN_APROM` ile program başlatılır.

Yükleme süresi: 4 KB'lık bir program yaklaşık 1 saniyede yüklenir. Önce tüm APROM silinir, bu da gerçek çipte yaklaşık 1,2 saniye sürer.

Testler:

```bash
(cd ../ms51_kart/bootloader && make host)
node --test test/nuvoton.test.mjs
```

11 test geçti. Testlerden biri Nuvoton'un kendi ISP_UART0 bootloader'ının davranışını taklit ediyor, yani yükleyici o bootloader'la da çalışıyor. Gerçek MS51 kartında henüz denenmedi.

## Lisans notu

Protokol, stcgal (Grigori Goronzy, MIT lisansı) kaynak kodundan uyarlanmıştır.
