# Malzeme tedariki

[BOM.csv](BOM.csv) kalemlerinin Türkiye'de ve yurt dışında nereden alınacağı. Linkler, fiyatlar ve stoklar 15 Kasım 2026'da kontrol edildi.

Fiyat notları:
- direnc.net fiyatlarına KDV dahildir.
- motorobit fiyatlarına KDV dahil değildir.
- Özdisan KDV'siz birim fiyat gösterir ve minimum sipariş adedi (MOQ) uygular.

## Önce bunu okuyun

İki parça Türkiye'de satılmıyor:
- **STC12C5A60S2:** Bu MCU hiçbir Türk mağazasında yok. Yurt dışından alınmak zorunda.
- **CH340C:** Türkiye'de yalnızca CH340G var. CH340G dışarıdan 12 MHz kristal ister ve kartta bu kristalin yeri yok, yani yerine takılamaz.

Bu iki parça zaten LCSC'den gelecekse **en kolayı bütün BOM'u tek LCSC siparişiyle almak**. Her satırdaki C numarası LCSC kodudur. Kart JLCPCB'de bastırılacaksa LCSC siparişi aynı kargoya birleştirilebilir.

İsterseniz JLCPCB'nin dizgi hizmeti SMD parçaları sizin yerinize lehimler. Bu durumda size yalnızca DIP soket, kristal, header ve SIP direnç dizisini lehimlemek kalır.

Türkiye'den almak isterseniz:
- **Özdisan** listedeki parçaların neredeyse hepsini stokta tutuyor.
- **direnc.net** daha ucuz ama eksiği daha fazla.

## Yalnızca yurt dışında olanlar

| Ref | Parça | Yurt dışı | Not |
|---|---|---|---|
| U1 | STC12C5A60S2-35I, PDIP-40 | [LCSC C14550](https://www.lcsc.com/product-detail/C14550.html) · [AliExpress araması](https://www.aliexpress.com/w/wholesale-STC12C5A60S2-DIP40.html) | Türkiye'de yok. Türk mağazalarındaki AT89S52 bunun yerine geçmez: ADC'si, PWM'i ve 2. UART'ı yok. |
| U2 | CH340C, SOP-16 | [LCSC C84681](https://www.lcsc.com/product-detail/C84681.html) | Türkiye'de yalnızca CH340G satılıyor ([Özdisan](https://www.ozdisan.com/en/p/controllers-227/wch-ch340g-469466), [motorobit](https://www.motorobit.com/ch340g-sop-16-usbden-seri-donusturucu-entegresi)). G harici kristal ister, karta uymaz. |
| U3 | USBLC6-2SC6, SOT-23-6 | [LCSC C7519](https://www.lcsc.com/product-detail/C7519.html) | [Özdisan'da](https://www.ozdisan.com/en/p/tvs-diodes-386/stm-usblc6-2sc6-402751) listeleniyor ama stok 0, tahmini teslim 5–6 hafta. |
| Q1 | AO3401A, SOT-23 | [LCSC C15127](https://www.lcsc.com/product-detail/C15127.html) | Türkiye'de stokta yok. Muadili aşağıda. |
| J1 | USB-C 16P, HRO TYPE-C-31-M-12 | [LCSC C165948](https://www.lcsc.com/product-detail/C165948.html) | Türkiye'deki 16 pinli soketlerin lehim ayağı (footprint) farklı. Ayrıntı aşağıda. |

### Türkiye'de alınacaksa muadiller

**Q1 yerine AO3407.** Kılıfı ve bacak dizilişi aynı: [motorobit](https://www.motorobit.com/ao3407-30v-41a-p-kanal-mofset-sot-23), 5.15 TL + KDV.
- Bu kartta Q1'in kapısı tam −5 V ile sürülüyor. AO3407 bu gerilimde tam açılır, yani karta uyar.
- Diğer seçenek: [Özdisan DMP3056L-7](https://www.ozdisan.com/en/p/discrete-mosfets-435/diodes-dmp3056l-7-585279).

**J1 yerine KLS1-5416.** [Özdisan KLS1-5416](https://www.ozdisan.com/p/usb-konnektorler-357/kls-electronic-l-kls1-5416-l1-01-r-1564461), 4.41 TL.
- Lehim ayağı HRO'dan farklı, bu yüzden PCB'deki footprint'in buna göre değiştirilmesi gerekir.

## Türkiye'de bulunanlar

| Ref | Parça | Türkiye | Yurt dışı |
|---|---|---|---|
| XU1 | DIP-40 soket, 600 mil | [Özdisan Connfly DS1009-40AT1WX-0A2](https://www.ozdisan.com/en/p/spring-loaded-ic-sockets-339/connfly-ds1009-40at1wx-0a2-955582), BOM'daki parçanın kendisi, 4.00 TL · [direnc.net](https://www.direnc.net/40-li-entegre-soketi), 4.11 TL · Torna (machined) tip: [Özdisan KLS](https://www.ozdisan.com/en/p/precision-ic-sockets-338/kls-electronic-l-kls1-217-40-z-2-527974), 32 TL | [LCSC C72123](https://www.lcsc.com/product-detail/C72123.html) |
| F1 | PTC sigorta 1206, 500 mA | [direnc.net](https://www.direnc.net/500ma-24v-smt-ptc-sigorta-1206), 7.17 TL · [Özdisan FSMD050](https://www.ozdisan.com/en/p/ptc-resettable-fuses-845/fuzetec-fsmd050-24-1206r-537038), 5.36 TL | [LCSC C70075](https://www.lcsc.com/product-detail/C70075.html) |
| Q2 | 2N7002, SOT-23 | [direnc.net](https://www.direnc.net/2n7002-n-kanal-mosfet-sot-23-smd-60v-250ma), 1.01 TL · [Özdisan Nexperia](https://www.ozdisan.com/en/p/discrete-mosfets-435/nexperia-2n7002-215-343822) | [LCSC C8545](https://www.lcsc.com/product-detail/C8545.html) |
| Q3 | MMBT3904, SOT-23 | [direnc.net](https://www.direnc.net/mmbt3904-smd-npn-transistor-sot-23), 1.15 TL · [komponentci](https://www.komponentci.net/mmbt3904lt1g-sot23-smd-transistor-pmu3236), 3.68 TL | [LCSC C20526](https://www.lcsc.com/product-detail/C20526.html) |
| D1 | B5819W, SOD-123 | [motorobit](https://www.motorobit.com/b5819w-1a-40v-smd-schottky-diyot), 1.03 TL + KDV · [direnc.net](https://www.direnc.net/b5819w-1a-40v-silicon-signal-diode), 2.42 TL · [Özdisan](https://www.ozdisan.com/en/p/schottky-diodes-385/hottech-b5819w-469437), MOQ 10 | [LCSC C8598](https://www.lcsc.com/product-detail/C8598.html) |
| Y1 | 11.0592 MHz kristal, HC-49S | [direnc.net](https://www.direnc.net/110592-mhz-kristal-x), 4.54 TL · [motorobit](https://www.motorobit.com/110592-mhz-kristal-hc-49s), 4.64 TL + KDV · [Özdisan Raltron](https://www.ozdisan.com/en/p/crystals-508/raltron-as-11-0592-18-ext-642558), 5.37 TL | [LCSC C2203](https://www.lcsc.com/product-detail/C2203.html) |
| C7, C8 | 33 pF, 0603 | [direnc.net](https://www.direnc.net/470pf-50v-10-603-smd-kondansator-12828), en az 10 adet, 0.33 TL/adet (adres "470pf" diyor ama sayfadaki ürün 33 pF) · [motorobit](https://www.motorobit.com/33pf-50v-5-603-smd-kondansator-10-adet), 10'lu paket | [LCSC C1663](https://www.lcsc.com/product-detail/C1663.html) |
| C2–C5 | 100 nF X7R, 0603 | [direnc.net](https://www.direnc.net/100nf-50v-603-smd-kondansator), en az 10 adet, 0.26 TL/adet · [Özdisan Yageo](https://www.ozdisan.com/en/p/smt-smd-and-mlcc-capacitors-184/yageo-cc0603krx7r9bb104-476015), BOM'daki parçanın kendisi | [LCSC C14663](https://www.lcsc.com/product-detail/C14663.html) |
| C1, C6, C9 | 10 µF, 0805 | [direnc.net 10 µF 25 V](https://www.direnc.net/47uf-50v-10-x5r-805-smd-kondansator), 0.86 TL (adres "47uf" diyor ama sayfadaki ürün 10 µF) · [Özdisan Samsung CL21A106KAYNNNE](https://www.ozdisan.com/en/p/smt-smd-and-mlcc-capacitors-184/samsung-cl21a106kaynnne-453566), BOM'daki parçanın kendisi | [LCSC C15850](https://www.lcsc.com/product-detail/C15850.html) |
| R1, R2 | 5.1 kΩ, 0603 | [Özdisan 0603SAJ0512T5E](https://www.ozdisan.com/en/p/smt-smd-and-chip-resistors-194/royalohm-0603saj0512t5e-346979), %5, MOQ 200, 10.82 TL. direnc.net'te yok. %5 tolerans USB-C için yeterli. | [LCSC C23186](https://www.lcsc.com/product-detail/C23186.html) |
| R6–R8, R11 | 10 kΩ, 0603 | [Özdisan %1](https://www.ozdisan.com/en/p/smt-smd-and-chip-resistors-194/royalohm-0603saf1002tde-516106), 100'lük paket 9.17 TL · [direnc.net %5](https://www.direnc.net/10k-5-110w-s-603-smd-direnc-5000-adet), en az 100 adet | [LCSC C25804](https://www.lcsc.com/product-detail/C25804.html) |
| R4, R9 | 4.7 kΩ, 0603 | [Özdisan %1](https://www.ozdisan.com/en/p/smt-smd-and-chip-resistors-194/royalohm-0603saf4701t5e-341796), 100'lük paket · [direnc.net %5](https://www.direnc.net/4k7-5-110w-s-603-smd-direnc-5000-adet) | [LCSC C23162](https://www.lcsc.com/product-detail/C23162.html) |
| R3, R5, R10, R12, R13 | 1 kΩ, 0603 | [Özdisan %1](https://www.ozdisan.com/en/p/smt-smd-and-chip-resistors-194/royalohm-0603saf1001t5e-341789), 100'lük paket. direnc.net'te stok 68 adet, minimum sipariş 100'ün altında kalıyor. | [LCSC C21190](https://www.lcsc.com/product-detail/C21190.html) |
| RN1 | 10 kΩ ×8, SIP-9 ortak uçlu | [direnc.net](https://www.direnc.net/10k-81-sira-direnc), 5.44 TL · [Özdisan RNLA09J0103B0E](https://www.ozdisan.com/en/p/network-and-array-resistors-196/royalohm-rnla09j0103b0e-29272). Ortak ucun 1. pin olduğunu kontrol edin. | [LCSC C8692](https://www.lcsc.com/product-detail/C8692.html) |
| LED1 | Yeşil LED, 0603 | [direnc.net](https://www.direnc.net/603-kilif-smd-yesil-led-500mcd-honglitronic), 1.38 TL · [Özdisan](https://www.ozdisan.com/en/p/led-signal-color-361/honglitronic-hl-pst-1608u51gc-471660), MOQ 20 | [LCSC C72043](https://www.lcsc.com/product-detail/C72043.html) |
| LED2 | Sarı LED, 0603 | [Özdisan HL-PST-1608S29YC](https://www.ozdisan.com/en/p/led-signal-color-361/honglitronic-hl-pst-1608s29yc-471661), MOQ 10 · [Özdisan LTST-C191KSKT](https://www.ozdisan.com/en/p/led-signal-color-361/liteon-ltst-c191kskt-502201). direnc.net'te 0603 sarı yok. | [LCSC C72038](https://www.lcsc.com/product-detail/C72038.html) |
| LED3 | Kırmızı LED, 0603 | [direnc.net](https://www.direnc.net/603-kilif-smd-kirmizi-led-90mcd-honglitronic), 1.38 TL · [Özdisan LTST-C190KRKT](https://www.ozdisan.com/en/p/led-signal-color-361/liteon-ltst-c190krkt-456428), MOQ 20 | [LCSC C2286](https://www.lcsc.com/product-detail/C2286.html) |
| SW1–SW3 | SMD tact buton, 5×5 mm | [Özdisan KLS 5.2×5.2](https://www.ozdisan.com/en/p/tactile-switches-485/kls-electronic-l-kls7-tk-052v-1-5-160-595732), 6.24 TL · [motorobit 5×5×1.5](https://www.motorobit.com/4-pinli-5x5x15mm-smd-tact-buton), 2.06 TL + KDV. Pad aralığı TS-1187A'ya çok yakın ama datasheet'ten kontrol edin. | [LCSC C318884](https://www.lcsc.com/product-detail/C318884.html) |
| J2–J6 | Erkek pin header 1×40, 2.54 mm | [motorobit](https://www.motorobit.com/1x40-erkek-header-40-pin-254mm-180-derece), 3.09 TL + KDV · [Özdisan Connfly](https://www.ozdisan.com/en/p/pin-headers-293/connfly-ds1021-1x40sf11-b-346538), 6.54 TL. direnc.net'in standart header'ı stokta yok. | [LCSC C2337](https://www.lcsc.com/product-detail/C2337.html) |

## Önerilen sipariş planları

**A. Tek sipariş (önerilen).** BOM'un tamamını LCSC'den alın. Kargo genelde 1–2 hafta sürer. Gümrük limitinin altında kalan küçük siparişlerde ek masraf çıkmaz.

**B. Türkiye ağırlıklı.** U1, U2, U3 ve J1 LCSC'den gelir. Geri kalanların hepsi Özdisan'dan alınır; yalnızca 33 pF kondansatörler direnc.net'ten (Özdisan'da stokta yok). Q1 için AO3407 kullanılır.

**C. En ucuz yerli.** U1, U2, U3 ve J1 yine LCSC'den gelir. Pasiflerin ve transistörlerin çoğu direnc.net'ten alınır. Şunlar ise Özdisan'dan alınır:
- sarı LED
- 5.1 kΩ direnç
- 1 kΩ direnç

## Maliyet

LCSC fiyatları 16 Kasım 2026'da LCSC'den alındı. Kur 1 $ ≈ 50.4 TL.

| | Tutar |
|---|---|
| Malzeme, kart başına (yalnızca kullanılan adetler) | **4.34 $ ≈ 219 TL** |
| LCSC sepeti, 1 kart (minimum alım adetleriyle; artan pasifler 5+ karta yeter) | 15.78 $ ≈ 795 TL |
| LCSC sepeti, 5 kart | ≈ 28 $ ≈ 1 420 TL |
| PCB, JLCPCB, 5 adet (100x56 mm, 2 katman) | ≈ 2–5 $ |

Türkiye ağırlıklı plan da (plan B) kart başına yaklaşık aynı tutar: ≈ 220 TL. Bu planda 163 TL LCSC'den gelen dört parçaya, ≈ 56 TL yerli parçalara gidiyor.

Tabloda olmayan masraflar:
- **Kargo:** LCSC ve JLCPCB siparişleri birleştirilip tek kargoda gönderilebilir.
- **Gümrük**
- **Dizgi ücreti:** SMT montaj seçilirse eklenir.

Kart başına tutarın yarısından fazlası MCU'ya gidiyor (2.35 $).

16 Kasım'da LCSC'de stokta olmayanlar: C25804 (10k), C72043 (yeşil LED), C72038 (sarı LED). Aynı kılıfta herhangi bir 10k 0603 direnç ve 0603 LED bunların yerine geçer. C14663'ün (100 nF) stoğu ise yalnızca 200 adet.

## Notlar

- **Fiyatlar:** Fiyat ve stoklar sık değişir. Sipariş vermeden önce linkleri tekrar açın.
- **LCSC linkleri:** C numarasından oluşturuldu. Fiyat ve stok o sayfada görünür.
- **Doğrulanmayan mağazalar:** robo90, elektrovadi ve SAMM Market sayfalarını otomatik okumak mümkün olmadı. Bu mağazalarda elle arama yapılabilir.
