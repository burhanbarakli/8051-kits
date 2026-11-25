# KiCad projesi — STC12C5A60S2 kartı (Rev A)

MCU STC12C5A60S2 (10 bit 8 kanal ADC, 2 kanal PWM). Dosya adları ilk tasarımdan kalma olarak `stc89_kart` adını taşıyor. Şemadaki U1 sembolü KiCad'in standart 8051 sembolü (AT89x51); pin adları 8051'e göre yazılı (EA, ALE, PSEN). STC12'deki karşılıkları ve net adları için `../baglanti-listesi.md` bölüm 5 ve 7'ye bakın.

KiCad 9 veya üstüyle açın: `stc89_kart.kicad_pro`.

| Dosya | Ne |
|---|---|
| `stc89_kart.kicad_sch` | Şema. Tek A3 sayfa, bağlantılar net etiketleriyle |
| `stc89_kart.kicad_pcb` | 100x56 mm, 2 katman, 4 adet M3 delik. **Yollar çizildi**, iki katmanda GND dökümü var |
| `stc89_kart.pdf` | Şemanın PDF çıktısı |
| `pcb_onizleme.svg` | Bakır katmanlar ve serigrafi önizlemesi |
| `pcb_3d_izometrik.png`, `pcb_3d_ust.png`, `pcb_3d_alt.png` | KiCad 3D görüntüleyici çıktısı. J1 (USB-C) ve SW1–SW3 için kütüphanede 3D model yok |
| `stc89_kart-easyeda.zip` | EasyEDA Pro'ya içe aktarmak için proje paketi |
| `erc.rpt`, `drc.rpt` | Doğrulama raporları |
| `stc89_kart.dsn`, `stc89_kart.ses` | Otomatik yönlendiricinin giriş ve çıkış dosyaları |
| `../uretim/` | JLCPCB sipariş dosyaları (Gerber, BOM, CPL), bkz. `../uretim/BENIOKU.md` |
| `kart_tanim.py` | **Tek kaynak:** parçalar, footprint'ler, LCSC kodları, pin-net eşleşmesi |
| `kicad_uret.py`, `pcb_uret.py`, `yol_uret.py`, `uretim.py`, `dogrula.py` | Üretici ve doğrulama betikleri |

## Doğrulama durumu (KiCad 9.0.9, kicad-cli)

- ERC: 0 hata, 0 uyarı.
- KiCad'in dışa aktardığı netlist, `kart_tanim.py` ile birebir aynı: 57 net, 193 bağlantı.
- PCB DRC ve şema eşleşmesi: 0 ihlal, 0 bağlanmamış nokta, 0 eşleşme hatası. Bu kontrol yol aralıklarını, courtyard çakışmasını, kart kenarına mesafeyi ve serigrafiyi de kapsıyor.
- Tüm sembol pin numaraları footprint pad'leriyle karşılaştırıldı, eksik pad yok.

## Yollar (Rev A)

Yollar Freerouting 1.9.0 ile otomatik çizildi, sonra `yol_uret.py` iki katmana GND dökümü ekledi. Elle iyileştirme yapılmadı.

| | |
|---|---|
| Yol genişliği | Sinyaller 0.25 mm. +5V, VBUS ve VCC_MCU 0.4 mm |
| Aralık | En az 0.2 mm. JLCPCB'nin standart sınırı 0.127 mm |
| Via | Sinyal geçişi için 11 adet (0.6/0.3 mm). Ayrıca 193 adet GND dikiş viası |
| Katman dağılımı | 388 yol parçası, toplam 1.76 m. 285'i üstte, 103'ü altta. Port header yolları çoğunlukla altta düz iniyor |
| GND | İki katmanın boş kalan her yeri GND dökümü. Dikiş viaları iki katmanı 4 mm'lik ızgarayla bağlıyor; yollar arasında kalan döküm parçaları da böylece kopuk kalmıyor |

Siparişten önce KiCad'de bir göz atmanızda yarar var:
- **USB_DP/USB_DM:** J1 → U3 → U2 arası kısa ve viasız. Ama otomatik yönlendirici bu iki hattı fark çifti (differential pair) olarak çizmedi. 12 Mbit/s'lik Full-Speed USB için bu kadar kısa bir mesafede sorun çıkarmaz.
- **Kristal:** Y1–U1 yolları kısa ve üst katmanda. Altlarında GND dökümü var.
- **Elle düzeltme:** Bir yolu elle düzeltirseniz `yol_uret.py`'yi tekrar çalıştırmayın, çünkü bütün yolları silip yeniden içe alır. Dökümü güncellemek için KiCad'de `B` tuşuna basın (tüm dökümleri doldur).

## KiCad'de devam

1. Sipariş için `../uretim/BENIOKU.md`'ye bakın. Kartta bir şeyi değiştirdikten sonra üretim dosyalarını `uretim.py` ile yeniden üretin.
2. Her footprint'te gizli bir `LCSC` alanı var. JLCPCB montajı için BOM/CPL çıkarırken (örneğin "JLC PCB Tools" eklentisi) bu alan kullanılır.
3. 3D görünüm: PCB düzenleyicide `Görünüm > 3D Görüntüleyici` (Alt+3). Modeller KiCad kurulumuyla gelir (macOS'ta tam paket). Eksik iki model için LCSC/EasyEDA'dan C165948 ve C318884'ün STEP dosyasını indirip footprint özelliklerindeki `3D Modeller` sekmesinden ekleyebilirsiniz.
4. Şemada bir şeyi elle değiştirirseniz, PCB'ye aktarmak için `Araçlar > PCB'yi Şemadan Güncelle (F8)` kullanın. Footprint'ler şemadaki sembollere bağlı olduğu için kopya oluşmaz.

## Yerleşim (Rev A önerisi)

```
 ┌──────────────────────────────────────────────────────────────┐
 │ H1  PWR MCU LED     [J3 P0 ··········][J4 P2 ··········]   H2 │
 │ [SW1 ISP]  Q3 Q2 Q1     [RN1 10k x8 ·········]                │
 │ R1         R8           ┌──────────────────────────────┐      │
 │[J1 ]F1  U2 CH340C   C5  │ U1 STC12C5A60S2 (DIP-40,soket)│      │
 │[USB]U3              C6  └──────────────────────────────┘      │
 │ R2 C1 C2  D1 R5 R4        LED3 C9   [SW3 USER]   [Y1] C8 C7   │
 │ [SW2 RESET] R12                                               │
 │ H3  [J6 RST P4.5 P4.4] [J2 P1 ··········][J5 P3 ··········] H4│
 └──────────────────────────────────────────────────────────────┘
```

Neden böyle:

- **Port header'ları kendi portlarının hizasında.** U1 yatay duruyor, J3/J4 (P0/P2) üst kenarda, J2/J5 (P1/P3) alt kenarda. P0..P3 yolları kısa ve neredeyse düz. J3 ile J2, komşu header'la çakışmasın diye 2 pin sola kaydırıldı.
- **RN1 P0 pinlerinin tam üstünde.** RN1'in pin 2–9'u U1'in pin 39–32'siyle aynı hizada, ortak ucu da (pin 1) U1'in VCC pininin (40) üstünde.
- **Kristal XTAL pinlerine 6 mm mesafede.** Y1, U1'in pin 18–19'unun hemen altında, C7/C8 de yanında.
- **USB tarafı sol kenarda tek akışta.** USB-C ağzı kart kenarında. Hemen arkasında ESD koruma (U3) ve sigorta, sonra CH340C. UD+/UD− pinleri USB'ye bakıyor.
- **Otomatik ISP sol üstte.** Q1, U1'in VCC köşesine yakın, böylece VCC_MCU yolu kısa kalıyor.
- **Butonlar kolay erişilir yerde.** ISP ve RESET sol kenarda üst üste, USER butonu P3.2'nin altında.
- **Delikler köşelerde.** 4 adet M3 delik var, kenarlardan 3.5 mm içeride.

Yolları elle yeniden çizmek isterseniz dikkat edilecekler:

1. Sinyalleri olabildiğince üst katmanda tutun; alt katmandaki GND dökümü ne kadar az bölünürse o kadar iyi.
2. USB_DP/USB_DM: J1'den U3'ün pad'lerinden geçerek U2'ye kısa, paralel ve viasız gidin.
3. Kristal: Y1–U1 yollarını kısa tutun, altlarından başka sinyal geçirmeyin, C7/C8'in GND uçlarına hemen yanlarında via koyun.
4. C5'i U1'in pin 40'ına en kısa yoldan bağlayın, GND ucuna via koyun. U1'in GND pini (20) çaprazda kaldığı için GND dökümüne birden fazla via ile bağlayın.
5. ADC hatları (P1.0–P1.6 → J2): ADC referansı VCC_MCU olduğu için bu hattın gürültüsü ölçüme doğrudan yansır. Analog yolları kristal, USB ve CH340C bölgesinden uzak tutun.

## EasyEDA Pro'ya aktarma

EasyEDA Pro, KiCad'in 10'dan eski sürümlerinde kaydedilmiş, paketlenmiş (zip) projeleri içe alabiliyor.

1. EasyEDA Pro başlangıç sayfası > **İçe Aktar > KiCad** > `stc89_kart-easyeda.zip` dosyasını seçin.
2. İçe alınamazsa projeyi KiCad'de açıp `Dosya > Projeyi Arşivle` ile yeniden paketleyin ve o zip'i deneyin.
3. İçe aktardıktan sonra footprint'leri ve LCSC alanlarını kontrol edin. EasyEDA'da parçaları LCSC koduyla eşleştirmek, JLCPCB siparişini kolaylaştırır.

Bu adım bu ortamda denenmedi; EasyEDA dönüşümünü ilk açışta gözle kontrol edin.

## Yeniden üretme

Devreyi değiştirmek için `kart_tanim.py`'yi düzenleyin, sonra:

```bash
python3 kicad_uret.py "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"
```

Footprint'leri ve PCB'yi KiCad'in Python ortamıyla üretmek ve doğrulamak için (Docker, Apple Silicon'da emülasyonla):

```bash
docker run --rm --platform linux/amd64 -v "$PWD":/p -w /p kicad/kicad:9.0 sh -c 'kicad-cli sch erc -o erc.rpt stc89_kart.kicad_sch && kicad-cli sch export netlist -o out.net stc89_kart.kicad_sch && python3 dogrula.py && python3 pcb_uret.py /usr/share/kicad/footprints out.net && kicad-cli pcb drc --schematic-parity -o drc.rpt stc89_kart.kicad_pcb'
```

Dikkat: `pcb_uret.py` PCB'yi yolları ve dökümüyle birlikte sıfırdan yazar (yerleşim `YERLESIM` tablosundan gelir). Kartı KiCad'de elle düzenledikten sonra çalıştırmayın; şema değişikliklerini KiCad içinde F8 ile aktarın.

Yolları yeniden çizmek için (`pcb_uret.py`'den sonra). Freerouting 1.9.0 Java 17 ile çalışır; 1.9.0 ekransız çalışmadığı için kısa süre bir pencere açar. `-da` anonim kullanım istatistiğini kapatır:

```bash
docker run --rm --platform linux/amd64 -v "$PWD":/p -w /p kicad/kicad:9.0 python3 yol_uret.py dsn
java -jar freerouting-1.9.0.jar -da -dct 0 -de stc89_kart.dsn -do stc89_kart.ses -mp 30 -mt 1
docker run --rm --platform linux/amd64 -v "$PWD":/p -w /p kicad/kicad:9.0 sh -c 'python3 yol_uret.py ses && kicad-cli pcb drc --schematic-parity --severity-all -o drc.rpt stc89_kart.kicad_pcb'
```

Üretim dosyaları için:

```bash
docker run --rm --platform linux/amd64 -v "$PWD/..":/d -w /d/kicad kicad/kicad:9.0 python3 uretim.py
```
