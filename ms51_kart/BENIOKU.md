# MS51 geliştirme kartı (Rev B)

Nuvoton **MS51PC0AE** ile 8051 geliştirme kartı.
- **MCU:** 1T 8051, 32K flash, 2K XRAM, 12 bit ADC, 6 kanal PWM. Dahili 16/24 MHz osilatörü var, kristal gerekmez.
- **Kart:** 84 x 50 mm, 2 katman. USB-C ile beslenir ve programlanır.

STC12 kartından (`../donanim`) en önemli farkı şu: MS51 fabrikadan bootloader'sız gelir. Bootloader her çipe bir kez ICP header'ından (J6) Nu-Link ile yüklenir. Bundan sonra kart, STC kartı gibi USB üzerinden programlanır.

![Kart](kicad/pcb_3d_izometrik.png)

## STC12 kartıyla karşılaştırma

| | STC12 kartı | MS51 kartı |
|---|---|---|
| MCU | STC12C5A60S2, DIP-40, sokette | MS51PC0AE, LQFP-32, lehimli |
| ADC | 10 bit, 8 kanal | **12 bit, 15 kanal** |
| PWM | 2 kanal | 6 kanal (PWM0) + ek PWM birimleri |
| Bootloader | Fabrikada ROM'da | **Yok.** Bir kez ICP ile LDROM'a yüklenir |
| Bootloader'a giriş | MCU'nun gücü kesilip verilmeli (Q1–Q3 + ISP butonu) | Her reset'te çalışır. CH340'ın DTR'si reset atar |
| Kristal | 11.0592 MHz | Yok (dahili osilatör) |
| P0 pull-up dizisi | Var (P0 açık-drain) | Yok (portlar push-pull/quasi ayarlanabilir) |
| Parça sayısı | 44 | 30 (CH340G seçeneğiyle 33) |
| Malzeme, kart başına (LCSC) | 4.34 $ | **2.81 $** |
| Türkiye'de MCU | Yok | **Özdisan**: MS51PC0AE-TR, 40.05 TL + KDV, 16 bin adet stok |

## Devre

| Blok | Parçalar | Not |
|---|---|---|
| USB ve güç | J1, F1, U3, R1, R2, C1, C2, LED1 | STC kartıyla aynı. MCU doğrudan +5V ile çalışır (MS51: 2.4–5.5 V) |
| USB-UART | U2 (CH340C ya da CH340G), C3, C4; CH340G ise Y1, C8, C9 | CH340 TXD → **R4 (1k)** → P0.7/RXD. P0.6/TXD → **R5 (1k)** → CH340 RXD. P0.6/P0.7 header'a da çıktığı için seri dirençler var |
| Reset | R6, C7, R7, D1, SW1 | RST 10k ile +5V'a çekili. DTR → 100 nF → 1k → RST: port açılınca kısa bir reset darbesi gider (Arduino'daki gibi). D1, darbe bitince RST'nin +5V'u aşmasını engeller. SW1 = RESET |
| ICP | J6 | Nu-Link bağlantısı. Sıra: **1 = +5V, 2 = DAT (P1.6), 3 = CLK (P0.2), 4 = RST, 5 = GND** |
| Kullanıcı | LED2 (P1.2, aktif düşük), SW2 (P3.0/INT0 → GND) | LED2, PWM0_CH0 pininde; parlaklık ayarı denenebilir |

### CH340C ya da CH340G (Rev B)

U2 yerine iki entegreden biri takılır. İkisinin bacak dizilimi aynı.

| | CH340C (varsayılan) | CH340G |
|---|---|---|
| Kristal | Gerekmez | 12 MHz kristal (Y1, HC-49S) ve 2 × 22 pF (C8, C9) takılır |
| Nereden | LCSC C84681, Türkiye'de yok | Türkiye'de stokta: [Özdisan](https://www.ozdisan.com/en/p/controllers-227/wch-ch340g-469466), ≈ 27 TL + KDV |
| Y1, C8, C9 | Boş kalır | Lehimlenir |

Kartta bu üç parçanın yeri U2'nin altında ve serigrafide "CH340G" yazıyor. Şemada ve PCB'de "takılmaz" (DNP) işaretli, bu yüzden JLCPCB dizgi dosyalarına girmezler. CH340G kullanılacaksa elle lehimlenirler: kristal delikli, kondansatörler 0603.

### Header'lar

| Header | Pinler (1 → son) |
|---|---|
| J2 · P0 | P0.0 … P0.7, +5V, GND |
| J3 · P1 | P1.0 … P1.7, +5V, GND |
| J4 · P3 | P3.0 … P3.7, +5V, GND |
| J5 · P2 | RST, P2.1 … P2.5, +5V, GND |

Ortak kullanılan pinler:
- **P0.6 / P0.7:** USB-UART hattı (TXD/RXD). Program çalışırken başka iş için kullanılabilir, ama yükleme sırasında üzerlerine bir şey bağlı olmamalı.
- **P0.2 / P1.6:** ICP hattı. Bootloader yüklenirken üzerlerine bir şey bağlı olmamalı.
- **P1.2:** Kullanıcı LED'i.
- **P3.0:** USER butonu.

**ADC kanalları:**

| Kanal | Pin | Kanal | Pin | Kanal | Pin |
|---|---|---|---|---|---|
| CH0 | P1.7 | CH5 | P0.4 | CH11 | P2.3 |
| CH1 | P3.0 | CH6 | P0.3 | CH12 | P2.4 |
| CH2 | P0.7 | CH7 | P1.1 | CH13 | P1.3 |
| CH3 | P0.6 | CH9 | P2.1 | CH14 | P1.4 |
| CH4 | P0.5 | CH10 | P2.2 | CH15 | P2.5 |

Pin dizilimi kaynağı: Nuvoton *MS51 Series Product Brief* Rev 2.00, Şekil 5-1 (LQFP-32). Ayrıntılı pin görevleri için Nuvoton'un MS51 32KB datasheet'ine bakın.

## Bootloader yükleme (her çip için bir kez)

Bootloader `bootloader/` klasöründe: `ms51_isp.bin`, 1 630 bayt. Yükleme adımlarının ayrıntısı `bootloader/BENIOKU.md` dosyasında.

1. Kartı USB'den çıkarın. Nu-Link'i J6'ya bağlayın; pin sırası yukarıdaki tabloda. Nu-Link'in kablo ucundaki sırayı kendi kılavuzundan kontrol edin.
2. Nuvoton'un *NuMicro ICP Programming Tool* programıyla `bootloader/ms51_isp.bin` dosyasını LDROM'a yazın.
3. CONFIG ayarları:
   - **Boot select: LDROM:** Çip her reset'te bootloader'dan başlar.
   - **LDROM size: 2 KB:** APROM 30 KB olur.
   - **Reset pini etkin kalmalı:** P2.0'ın reset görevi kapatılmamalı.

Bundan sonra kart USB-C ile takılıp web yükleyicide "Nuvoton MS51" seçilerek programlanır (`../yukleyici/nuvoton.js`). Bootloader her reset'ten sonra 500 ms bağlantı bekler, gelmezse kullanıcı programını (APROM) başlatır.

## Dosyalar

| Dosya | Ne |
|---|---|
| `kicad/ms51_kart.kicad_pro` | KiCad projesi (KiCad 9 veya üstü) |
| `kicad/ms51_kart.kicad_sch`, `.pdf` | Şema |
| `kicad/ms51_kart.kicad_pcb` | PCB: yollar çizildi, iki katmanda GND dökümü var |
| `kicad/ms51.kicad_sym`, `sym-lib-table` | MS51PC0AE sembolü. KiCad'in kendi kütüphanesinde Nuvoton yok |
| `kicad/pcb_3d_*.png`, `pcb_onizleme.svg` | Görüntüler |
| `kicad/ms51_kart-easyeda.zip` | EasyEDA Pro'ya aktarmak için |
| `uretim/` | JLCPCB sipariş dosyaları (Gerber, BOM, CPL); bkz. `uretim/BENIOKU.md` |
| `kutu/` | 3D baskı kutusu (CadQuery): STL, STEP ve kaynak; bkz. `kutu/BENIOKU.md` |
| `bootloader/` | LDROM bootloader'ı: kaynak, derlenmiş `ms51_isp.bin` ve testler; bkz. `bootloader/BENIOKU.md` |
| `BOM.csv` | Malzeme listesi (LCSC kodlarıyla) |
| `kicad/kart_tanim.py` | **Tek kaynak:** parçalar, pin-net eşleşmesi, MS51 pin tablosu |
| `kicad/ms51_sembol.py`, `kicad_uret.py`, `pcb_uret.py`, `yol_uret.py`, `uretim.py`, `dogrula.py` | Üretici ve doğrulama betikleri; STC kartındakilerin uyarlaması |

## Doğrulama (KiCad 9.0.9)

- **ERC:** 0 hata, 0 uyarı.
- **Netlist:** KiCad'in netlist'i `kart_tanim.py` ile birebir aynı: 46 net, 154 bağlantı.
- **DRC:** 0 ihlal, 0 bağlanmamış nokta, şemayla 0 eşleşme hatası.
- **Yollar:**
  - Freerouting 1.9.0 ile çizildi: 456 yol parçası ve 23 via.
  - Sinyal yolları 0.25 mm, +5V ve VBUS 0.4 mm. Aralık en az 0.2 mm.
  - Kart kenarına yakın via olmasın diye yönlendirme sırasında kenarlarda 0.8 mm'lik via yasağı kullanıldı.
  - 196 GND dikiş viası eklendi. Parçaların altına konmadı; iki katmana birden bağlanamayanlar silindi.

**Doğrulanmayanlar:**
- **Donanım:** Kart üretilmedi, gerçek donanımda denenmedi.
- **Reset ile ICP etkileşimi:** DTR otomatik reset devresi (C7 + R7) ICP sırasında reset hattına küçük bir yük ekliyor. Seri 1k bunu sınırlıyor, ama Nu-Link ile denenmedi. Sorun çıkarsa programlarken R7 sökülebilir. İleride bir köprü (jumper) da eklenebilir.
- **Bootloader ve web yükleyici:** Yazıldı ve SDCC ile derlendi (`bootloader/`, `../yukleyici/nuvoton.js`). Protokol kodu, bilgisayarda yükleyiciye karşı uçtan uca test edildi; 11 test geçti. MS51'e özel donanım kodu (`hal_ms51.c`) gerçek çipte henüz çalıştırılmadı.

## Maliyet ve tedarik

- **Malzeme:** LCSC'de kart başına **2.81 $** (≈ 142 TL). Minimum alım adetleriyle tek kartlık sepet 9.92 $. Fiyatlar 17 Kasım 2026'da alındı.
- **MS51PC0AE:** LCSC C2688383, 1.33 $, stok 2 242. Türkiye'de [Özdisan](https://www.ozdisan.com/p/mikroislemciler-218/nuvoton-ms51pc0ae-tr-652409), 40.05 TL + KDV.
- **Nu-Link:** [Özdisan](https://www.ozdisan.com/p/islemci-programlayicilari-610/nuvoton-nu-link-531781), 1 545 TL + KDV. Uyumlu kopyası [motorobit](https://www.motorobit.com/nu-link-plus-icp-programlayici-nuvoton-uyumlu)'te 1 669 TL KDV dahil. Bir laboratuvara bir tane yeter.
- **LCSC'de stokta olmayanlar (17 Kasım):** 100 nF (C14663), 1k (C21190) ve yeşil LED (C72043). Aynı kılıfta herhangi bir muadili kullanılabilir.
- **Diğer parçalar:** STC kartıyla aynı. Türkiye'deki kaynakları için `../donanim/tedarik.md` dosyasına bakın.

## Yeniden üretme

```bash
cd kicad
docker run --rm --platform linux/amd64 -v "$PWD":/p -w /p kicad/kicad:9.0 sh -c 'python3 ms51_sembol.py && python3 kicad_uret.py /usr/share/kicad/symbols && kicad-cli sch erc -o erc.rpt ms51_kart.kicad_sch && kicad-cli sch export netlist -o out.net ms51_kart.kicad_sch && python3 dogrula.py && python3 pcb_uret.py /usr/share/kicad/footprints out.net && python3 yol_uret.py dsn'
java -jar freerouting-1.9.0.jar -da -dct 0 -de ms51_kart.dsn -do ms51_kart.ses -mp 100 -mt 1
docker run --rm --platform linux/amd64 -v "$PWD":/p -w /p kicad/kicad:9.0 sh -c 'python3 yol_uret.py ses && kicad-cli pcb drc --schematic-parity --severity-all -o drc.rpt ms51_kart.kicad_pcb'
docker run --rm --platform linux/amd64 -v "$PWD/..":/d -w /d/kicad kicad/kicad:9.0 python3 uretim.py
```

Dikkat: `pcb_uret.py` ve `yol_uret.py` PCB'yi baştan yazar. KiCad'de elle değişiklik yaptıktan sonra çalıştırmayın.
