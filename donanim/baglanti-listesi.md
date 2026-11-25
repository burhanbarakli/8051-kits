# STC12C5A60S2 Geliştirme Kartı — Bağlantı Listesi (Rev A)

Şema çizimleri: `sema/*.svg` (topluca görmek için `sema/index.html`). Parçalar: `BOM.csv`.
KiCad 9 projesi (şema + PCB, ERC/DRC doğrulanmış): `kicad/` — ayrıntılar `kicad/BENIOKU.md`.

## Besleme hatları

| Net | Kaynak | Açıklama |
|---|---|---|
| `VBUS` | J1 VBUS (A4, A9, B4, B9) | USB'den gelen ham 5V |
| `+5V` | F1 çıkışı | CH340, LED1 ve otomatik ISP devresini besler. **Her zaman açık** |
| `VCC_MCU` | Q1 drain | U1 ve tüm header'ların besleme ucu. DTR/RTS veya SW1 ile kesilebilir |
| `GND` | J1 GND (A1, A12, B1, B12, gövde) | Ortak toprak |

> Header'lardaki besleme ucu bilerek `VCC_MCU` yapıldı. Harici modüller MCU ile birlikte kapanır. Böylece MCU'yu I/O pinleri üzerinden besleyip soğuk açılışı (cold boot) bozamazlar.

## 1. USB ve güç

| Parça | Pin | Net |
|---|---|---|
| J1 | VBUS | `VBUS` |
| J1 | CC1 (A5) | R1 → `GND` |
| J1 | CC2 (B5) | R2 → `GND` |
| J1 | D+ (A6, B6 birleşik) | `USB_DP` |
| J1 | D− (A7, B7 birleşik) | `USB_DM` |
| J1 | SBU1, SBU2 | Bağlantısız |
| F1 | 1 / 2 | `VBUS` / `+5V` |
| U3 USBLC6 | 1, 6 (I/O1) | `USB_DP` |
| U3 USBLC6 | 3, 4 (I/O2) | `USB_DM` |
| U3 USBLC6 | 5 (VBUS) / 2 (GND) | `+5V` / `GND` |
| C1 10µF, C2 100nF | — | `+5V` ↔ `GND` |
| LED1 + R3 | — | `+5V` → R3 → LED1 → `GND` |

## 2. CH340C (U2)

| Pin | Ad | Net |
|---|---|---|
| 1 | GND | `GND` |
| 2 | TXD | `CH_TXD` |
| 3 | RXD | `CH_RXD` |
| 4 | V3 | C4 100nF → `GND` (5V çalışmada sadece kondansatör) |
| 5 | UD+ | `USB_DP` |
| 6 | UD− | `USB_DM` |
| 7, 8, 9, 10, 11, 12, 15 | NC / CTS# / DSR# / RI# / DCD# / R232 | Bağlantısız |
| 13 | DTR# | `DTR_N` |
| 14 | RTS# | `RTS_N` |
| 16 | VCC | `+5V` (C3 100nF ile) |

## 3. UART ara bağlantısı (geri besleme korumalı)

| Bağlantı | Not |
|---|---|
| `CH_TXD` ─▶\|─ `MCU_RXD`: D1'in katodu `CH_TXD`'de, anodu `MCU_RXD`'de | CH340 hattı sadece aşağı çekebilir. MCU kapalıyken TX hattının yüksek seviyesi MCU'ya ulaşmaz |
| R4 4.7k: `MCU_RXD` → `VCC_MCU` | Yüksek seviyeyi MCU'nun kendi beslemesi sağlar |
| R5 1k: `MCU_TXD` → `CH_RXD` | Akım sınırlama |

## 4. Otomatik ISP güç kesici

| Parça | Pin | Net |
|---|---|---|
| Q1 AO3401A | S / D / G | `+5V` / `VCC_MCU` / `Q1_G` |
| R6 10k | — | `Q1_G` → `+5V` |
| Q2 2N7002 | D / S / G | `Q1_G` / `GND` / `ISP_N` |
| R7 10k | — | `ISP_N` → `+5V` |
| Q3 MMBT3904 | C / E / B | `ISP_N` / `DTR_N` / R8 üzerinden `RTS_N` |
| SW1 (ISP) | — | `ISP_N` ↔ `GND` |
| R9 4.7k | — | `VCC_MCU` → `GND` (kapanınca kondansatörleri hızlıca boşaltır) |
| LED2 + R10 | — | `VCC_MCU` → R10 → LED2 → `GND` |

### Doğruluk tablosu

Host tarafındaki sinyal "aktif" ise CH340'ın ilgili pini LOW olur.

| DTR | RTS | DTR_N | RTS_N | Q3 | ISP_N | VCC_MCU |
|---|---|---|---|---|---|---|
| pasif | pasif | H | H | kesim | H | **AÇIK** |
| aktif | aktif | L | L | kesim | H | **AÇIK** |
| pasif | aktif | H | L | kesim | H | **AÇIK** |
| **aktif** | **pasif** | L | H | iletim | L | **KAPALI** |

Gücü yalnızca DTR aktif ve RTS pasif kombinasyonu keser. Normal seri terminaller ikisini birlikte açıp kapattığı için seri monitör açmak MCU'yu kapatmaz.

## 5. MCU (U1, STC12C5A60S2 PDIP-40)

Pin dizilimi standart 8051 ile aynı. Farklı olan pinler aşağıda kalın yazıldı.

| Pin | Ad | Net / bağlantı |
|---|---|---|
| 1–8 | P1.0–P1.7 / **ADC0–ADC7** | J2. P1.7 ayrıca LED3 katoduna bağlı (`VCC_MCU` → R13 → LED3 → P1.7) |
| 9 | RST | `RST`: C9 10µF `VCC_MCU`'ya, R11 10k `GND`'ye, SW2 + R12 1k `VCC_MCU`'ya; ayrıca J6 |
| 10 | P3.0/RXD | `MCU_RXD`, J5 |
| 11 | P3.1/TXD | `MCU_TXD`, J5 |
| 12 | P3.2/INT0 | J5 ve SW3 → `GND` |
| 13–17 | P3.3–P3.7 | J5 |
| 18 | XTAL2 | Y1, C8 33pF → `GND` |
| 19 | XTAL1 | Y1, C7 33pF → `GND` |
| 20 | GND | `GND` |
| 21–28 | P2.0–P2.7 | J4 |
| 29 | **P4.4** (8051'de PSEN) | `P4.4`, J6 |
| 30 | **P4.5**/ALE | `P4.5`, J6 |
| 31 | **P4.6/EX_LVD/RST2** (8051'de EA) | `VCC_MCU`. Harici düşük voltaj algılama girişi; 5V'ta eşiğin (yaklaşık 1.3V) hep üstünde kaldığı için reset tetiklemez. P4.6 bu kartta G/Ç olarak kullanılamaz |
| 32–39 | P0.7–P0.0 | J3 ve RN1 (pin 2–9). RN1 pin 1 → `VCC_MCU` |
| 40 | VCC | `VCC_MCU` (C5 100nF ve C6 10µF pin dibine) |

## 6. Header'lar

| Header | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| J2 | P1.0 | P1.1 | P1.2 | P1.3 | P1.4 | P1.5 | P1.6 | P1.7 | VCC_MCU | GND |
| J3 | P0.0 | P0.1 | P0.2 | P0.3 | P0.4 | P0.5 | P0.6 | P0.7 | VCC_MCU | GND |
| J4 | P2.0 | P2.1 | P2.2 | P2.3 | P2.4 | P2.5 | P2.6 | P2.7 | VCC_MCU | GND |
| J5 | P3.0 | P3.1 | P3.2 | P3.3 | P3.4 | P3.5 | P3.6 | P3.7 | VCC_MCU | GND |
| J6 | RST | P4.5 | P4.4 | | | | | | | |

P3.0 ve P3.1 USB-UART ile ortak. Yükleme sırasında bu pinlere harici bir sürücü bağlamayın.

## 7. ADC ve PWM (STC12C5A60S2)

| İşlev | Pin | Header | Not |
|---|---|---|---|
| ADC0–ADC7, 10 bit | P1.0–P1.7 | J2 1–8 | Kanal `P1ASF` ile analog moda alınır. Referans VCC_MCU (5V) |
| PWM0 (PCA CCP0) | P1.3 | J2 4 | `AUXR1` ile P4.2'ye taşınabilir; DIP-40'ta P4.2 yok, P1.3'te kalır |
| PWM1 (PCA CCP1) | P1.4 | J2 5 | Aynı şekilde P1.4'te kalır |
| UART2 | P1.2 (RXD2) / P1.3 (TXD2) | J2 3–4 | PWM0 ile aynı pini paylaşır |
| SPI | P1.4 SS, P1.5 MOSI, P1.6 MISO, P1.7 SCLK | J2 5–8 | |
| P4.4, P4.5 | Pin 29, 30 | J6 2–3 | G/Ç olarak kullanmak için `P4SW` ayarlanır |

> **ADC7 uyarısı:** P1.7'ye LED3 ve R13 üzerinden VCC_MCU bağlı. Bu yük ADC7 okumasını bozar. Analog ölçüm için ADC0–ADC6'yı kullanın.

## Web yükleyici sırası (Web Serial)

Uygulaması: `../yukleyici/stc12.js` (demo sayfası ve testler aynı klasörde, ayrıntılar `../yukleyici/BENIOKU.md`).

1. Port çift eşlikle (even parity) açılır. Varsayılan el sıkışma ve aktarım hızı 9600 baud'dur; ikisi aynı olduğu için port yeniden açılmaz.
2. `setSignals({ dataTerminalReady: true, requestToSend: false })` ile MCU kapatılır, 500 ms beklenir.
3. `setSignals({ dataTerminalReady: false, requestToSend: false })` ile MCU açılır. Aynı anda 30 ms aralıkla `0x7F` gönderilir ve MCU'nun durum paketi beklenir. Her adımda yalnızca tek sinyal değişir, ara durumda istenmeyen güç kesilmesi olmaz.
4. Yanıt gelmezse kullanıcı SW1'e (ISP) basıp bırakır; yükleyici `0x7F` göndermeyi 20 saniye sürdürür.
5. El sıkışma, silme, 128 baytlık bloklarla yazma ve seçenek paketi stcgal'in `stc12` protokolüyle aynıdır. Sonunda `0x82` komutu kullanıcı programını başlatır.

## Yerleşim (PCB) notları

- Y1, C7 ve C8'i U1'in 18–19. pinlerine olabildiğince yakın yerleştirin. Altlarındaki toprak dökümünü kesintisiz tutun.
- USB_DP ve USB_DM izlerini yan yana ve kısa çizin. U3'ü J1'in hemen arkasına koyun.
- C5'i U1'in 40. pinine yakın, C3'ü U2'nin 16. pinine yakın yerleştirin.
- Q1'in VCC_MCU izini en az 0.5 mm genişlikte çizin.
- ADC kullanılacaksa VCC_MCU üzerindeki C5/C6 dekuplajını kısa tutun; analog sinyalleri kristal ve USB hatlarından uzak geçirin.
- SW2 (RESET) ISP moduna sokmaz. STC yalnızca soğuk açılışta bootloader'a bakar, ISP için SW1 kullanılır.
