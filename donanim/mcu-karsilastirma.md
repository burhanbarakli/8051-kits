# 8051 ailesi: bootloader'lı alternatifler

Mevcut karttaki STC12C5A60S2 yerine ya da ikinci kuşak kart için düşünülebilecek 8051 çekirdekli çiplerin karşılaştırması.
- **LCSC fiyat ve stokları:** 17 Kasım 2026'da LCSC'den alındı. 1 $ ≈ 50.4 TL.
- **Türkiye bilgisi:** Aynı gün mağaza sayfaları tek tek açılarak kontrol edildi.
- **Teknik özellikler:** Üreticilerin belgelerinden özetlendi. Kart tasarımına başlamadan önce ilgili datasheet ile doğrulanmalı.

## Karşılaştırma

| Çip | Çekirdek | Flash / RAM | ADC | PWM | USB | Bootloader |
|---|---|---|---|---|---|---|
| **STC12C5A60S2** (mevcut) | 1T, 35 MHz | 60K / 1.25K | 10 bit, 8 kanal | 2 kanal (PCA) | – | ROM, UART |
| **STC8H8K64U** | 1T, 45 MHz | 64K / 8K | **12 bit**, 15 kanala kadar | 16 bit gelişmiş PWM, 8 kanal | **Var** | ROM, UART + USB |
| **STC8H1K28** | 1T, 36 MHz | 28K / 1.25K | 10 bit | 16 bit gelişmiş PWM | – | ROM, UART |
| **WCH CH552G** | 24 MHz | 16K / 1.25K | **8 bit**, 4 kanal | 2 kanal | **Var** | ROM, USB + UART |
| **WCH CH559L** | 56 MHz | 64K / 6K | var, 8 kanal | var | **Var**, host + device | ROM, USB + UART |
| **Nuvoton N76E003** | 1T, 16 MHz | 18K / 1K | 12 bit, 8 kanal | 6 kanal | – | **Yok.** LDROM boş gelir |
| **Nuvoton MS51** (FB9AE / FC0AE) | 1T, 24 MHz | 16–32K / 1–2K | 12 bit, 8 kanal | 6 kanal | – | **Yok.** LDROM boş gelir |
| **SiLabs EFM8BB1** | 25 MHz (CIP-51) | 8K / 512 | 12 bit | 3 kanal (PCA) | – | Fabrikada UART bootloader (AN945; model ve tarih koduna bağlı) |
| **Microchip AT89C51ED2** | klasik 8051 (12T/6T) | 64K / 2K + 2K EEPROM | – | 5 kanal (PCA) | – | ROM, UART (FLIP) |

## Fiyat ve bulunabilirlik

| Çip | LCSC (1 adet) | LCSC stok | Kılıf | Türkiye |
|---|---|---|---|---|
| STC12C5A60S2 | [2.35 $](https://www.lcsc.com/product-detail/C14550.html) | 153 | DIP-40 | Yok |
| STC8H8K64U | [1.13 $](https://www.lcsc.com/product-detail/C2987962.html) | **4** | DIP-40 | Çip yok. Yalnızca [STC8H1K08 geliştirme kartı (motorobit)](https://www.motorobit.com/stc8h1k08-tssop20-gelistirme-karti), 185 TL |
| | [0.92 $](https://www.lcsc.com/product-detail/C3013145.html) | 11 395 | LQFP-48 | |
| | [0.61 $](https://www.lcsc.com/product-detail/C5210758.html) | 5 407 | TSSOP-20 | |
| STC8H1K28 | [0.68 $](https://www.lcsc.com/product-detail/C914618.html) | 7 413 | LQFP-32 | Yok |
| CH552G | [0.61 $](https://www.lcsc.com/product-detail/C111292.html) | 5 062 | SOP-16 | Yok |
| CH559L | [1.88 $](https://www.lcsc.com/product-detail/C150548.html) | 1 768 | LQFP-48 | Yok |
| N76E003AT20 | [0.90 $](https://www.lcsc.com/product-detail/C82751.html) | 20 950 | TSSOP-20 | [Özdisan](https://www.ozdisan.com/p/mikroislemciler-218/nuvoton-n76e003at20-528697): stok 0, teslim 23–24 hafta |
| MS51FB9AE | [0.69 $](https://www.lcsc.com/product-detail/C408539.html) | 18 259 | TSSOP-20 | **[Özdisan MS51FC0AE](https://www.ozdisan.com/p/mikroislemciler-218/nuvoton-ms51fc0ae-589664)** (32K), 37 TL KDV dahil, stok 109. [MS51PC0AE (LQFP-32)](https://www.ozdisan.com/p/mikroislemciler-218/nuvoton-ms51pc0ae-tr-652409), 40 TL + KDV, stok 16 483 |
| EFM8BB10F8G | [0.89 $](https://www.lcsc.com/product-detail/C406735.html) | 6 966 | yalnızca QFN-20 (QSOP-24 stokta yok) | Yok. Farnell/SAMM sayfaları "tükendi" |
| AT89C51ED2 | [10.90 $](https://www.lcsc.com/product-detail/C2693199.html) | 3 | PLCC-44 | [AT89C51RD2 (direnc)](https://www.direnc.net/at89c51rd2-rltum-smd-8bit-40mhz-mikrodenetleyici-vqfp44), 162 TL. ED2 [komponentci](https://www.komponentci.net/at89c51ed2-slsim-at89c51ed2-im-plcc-44-mcu-microcontroller-pmu67292), 1 078 TL |

Türkiye'de düzgün bir yerel kaynağı olan tek aile **Nuvoton**. Özdisan resmi distribütör: MS51 çipleri stokta, Nu-Link programlayıcı ve NT-N76E003 geliştirme kartı da satıyor.

## Çip bazında notlar

- **STC8H8K64U:** STC12'nin doğal devamı.
  - **Artıları:** Aynı firma, aynı ROM bootloader mantığı. ADC 12 bit, PWM ve RAM çok daha fazla, USB'si var. stcgal'de STC8 protokolü mevcut, yani web yükleyiciyi genişletmek orta büyüklükte bir iş.
  - **Kılıf:** DIP-40'ın LCSC stoğu çok az (4 adet). Pratikte LQFP-48 ya da TSSOP-20 kullanılır, bu da soketli "çip değiştirilebilir" yapıdan vazgeçmek demek.
  - **USB'den yükleme:** Açılışta P3.2 GND'ye çekilmeli; bunun için bir buton gerekir.
- **CH552G:** USB çipin içinde olduğu için CH340 ve otomatik ISP devresi kalkar; kart en sade ve en ucuz hâline gelir. Chrome'un WebUSB'siyle tarayıcıdan yüklenebilir. Ama **ADC 8 bit**, eğitimde analog ölçüm için zayıf kalır.
- **N76E003 / MS51:** Ucuz, popüler, ADC'si ve PWM'i iyi. Türkiye'de bulunan tek aile. Ama **fabrikadan bootloader'sız** geliyor (aşağıya bakın).
- **EFM8BB1:** Kaliteli ve iyi belgelenmiş, ama LCSC'de yalnızca 3x3 mm QFN kılıfı stokta. Elle lehimlemek zor, Türkiye'de de yok.
- **AT89C51ED2:** Klasik ve ROM bootloader'lı, ama pahalı ve eski. ADC'si yok.

## Bootloader'sız çip kullanılırsa

Çip boş gelir. İlk programı yazmak için çipin kendi programlama arayüzünü konuşan bir donanım gerekir:
- **Nuvoton:** ICP. Üç hat (DAT, CLK, RST) ile besleme ve GND.
- **Silicon Labs:** C2. İki hat.
- **AT89S serisi:** SPI.

Bootloader'sız bir çiple web yükleyici kurmanın üç yolu var:

### A. Her yüklemede programlayıcı

- **Nasıl:** Programlayıcı kart ile bilgisayar arasına takılır. Nuvoton için bu [Nu-Link (Özdisan)](https://www.ozdisan.com/p/islemci-programlayicilari-610/nuvoton-nu-link-531781) ya da [motorobit'in uyumlu kopyası](https://www.motorobit.com/nu-link-plus-icp-programlayici-nuvoton-uyumlu) olabilir.
- **Maliyet:** 1 545 TL + KDV veya 1 669 TL KDV dahil. Bir Arduino da ICP programlayıcı yapılabilir; açık kaynak `nuvo51icp` projesinde bunun için bir Arduino köprü programı var.
- **Sakıncası:** Her öğrenciye bir programlayıcı gerekir. Web'den yükleme için Nu-Link'in belgelenmemiş USB protokolünü (açık kaynak `nuvoprog` tersine mühendislikle çıkarmış) tarayıcıya taşımak gerekir.
- **Değerlendirme:** Pahalı ve zahmetli.

### B. Bootloader'ı bir kez yüklemek (Nuvoton için önerilen)

1. Her çipe **bir kez** programlayıcıyla Nuvoton'un UART ISP bootloader'ı yüklenir. Bootloader, çipin ayrı bir bölümüne (LDROM) yazılır.
2. Çipin ayar baytı (CONFIG), çipin her açılışta önce bu bölümden başlayacağı şekilde ayarlanır.
3. Bundan sonra kart, STC kartıyla aynı mantıkla çalışır: CH340 üzerinden seri port ve web yükleyici. Protokol açık kaynak `nvtispflash` projesinde mevcut.

Bu yolun artıları:
- Kullanıcı programı yalnızca kendi bölümüne (APROM) yazılır, bootloader silinmez.
- **Güç kesme devresi gerekmez.** Bootloader her reset'te çalıştığı için CH340'ın DTR hattıyla reset atmak yeter. STC'deki Q1–Q3 devresi kalkar.
- Programlayıcıyı yalnızca laboratuvar sorumlusu kullanır, öğrenci hiç görmez. Çip başına birkaç dakikalık iş.

Sakıncası: Yeni ya da değiştirilen her çipte bu ilk adım tekrarlanmalı.

### C. Programlayıcıyı karta gömmek

- **Nasıl:** CH340 yerine karta küçük bir USB'li çip konur, örneğin CH552 (0.61 $). Bu çip hem USB-seri köprüsü hem ICP programlayıcısı olur; web yükleyici onunla konuşur, o da hedef çipi programlar.
- **Artısı:** Hedef çip boş bile olsa doğrudan yüklenir, ön hazırlık gerekmez. CH552'nin kendi ROM'unda USB bootloader'ı olduğu için köprü yazılımı da USB'den güncellenebilir. Arduino Uno'daki 16U2 bu mantıkla çalışır.
- **Sakıncası:** Köprü çipi için ICP protokolünü uygulayan bir yazılım yazmak gerekir. Referans olarak `nuvo51icp` var. Bu yollar arasındaki en büyük yazılım işi.

## Öneri

| Hedef | Seçim |
|---|---|
| Şu anki kart | **STC12C5A60S2'de kalın.** Kart, yükleyici ve kutu hazır. |
| İkinci kuşak, daha güçlü kart | **STC8H8K64U** (LQFP-48 veya TSSOP-20). 12 bit ADC, bol PWM, USB ve ROM bootloader. Ucuz, LCSC'de stok bol, yükleyici STC12 tecrübesiyle genişletilir. |
| Parçalar Türkiye'den alınabilsin | **Nuvoton MS51** + yol B. Özdisan'dan çip ve Nu-Link alınır; laboratuvarda her çipe bir kez bootloader yüklenir. |
| En sade ve en ucuz USB'li kart | **CH552G.** ADC 8 bit olduğu için analog ağırlıklı dersler için uygun değil. |

## Kaynaklar

- **LCSC ürün sayfaları:** Tablodaki linkler. Fiyatlar LCSC'nin ürün servisinden alındı.
- **Türk mağaza sayfaları:** Tablodaki linkler.
- **EFM8 fabrika bootloader'ı:** [Silicon Labs AN945](https://www.silabs.com/documents/public/application-notes/an945-efm8-factory-bootloader-user-guide.pdf)
- **Nuvoton açık kaynak araçları:**
  - [nuvoprog](https://github.com/mountaintom/nuvoprog): Nu-Link
  - [nvtispflash](https://github.com/frank-zago/nvtispflash): UART ISP
  - NuMicro-8051-prog / nuvo51icp (GitHub, SeTcbPrivilege): Raspberry Pi ve Arduino ile ICP
