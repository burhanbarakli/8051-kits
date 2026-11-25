# JLCPCB sipariş dosyaları (Rev A)

Bu klasördeki dosyalar `../kicad/uretim.py` ile KiCad PCB dosyasından üretilir. Elle düzenlemeyin.

| Dosya | Ne için |
|---|---|
| `stc12_kart-gerber.zip` | PCB siparişi. Gerber ve delik dosyaları |
| `jlcpcb-bom.csv` | Dizgi (SMT montaj) siparişi için BOM: 19 satır, 36 SMD parça, LCSC kodlarıyla |
| `jlcpcb-cpl.csv` | Dizgi için parça konumları ve açıları |
| `delikli-parcalar.csv` | Dizgiye girmeyen, elle lehimlenecek parçalar |
| `gerber/` | Zip'in açılmış hâli |

## PCB siparişi

1. jlcpcb.com > **Order Now** > `stc12_kart-gerber.zip` dosyasını yükleyin. Kart 100 x 56 mm, 2 katman olarak algılanır.
2. Varsayılan seçenekler uygundur: FR-4, 1.6 mm, 1 oz bakır, HASL. Renk tercihe bağlı.
3. Kartta 0.2 mm'nin altında aralık ya da 0.3 mm'nin altında delik yok. Bu yüzden en ucuz standart üretim yeterli.

## Dizgi (isteğe bağlı)

SMD parçaları JLCPCB'nin lehimlemesini isterseniz aynı siparişte **PCB Assembly** seçeneğini açın:

1. Montaj tarafı **Top**.
2. BOM olarak `jlcpcb-bom.csv`, CPL olarak `jlcpcb-cpl.csv` dosyasını yükleyin.
3. **Parça açılarını önizlemede kontrol edin.** KiCad ve JLCPCB bazı kılıflarda sıfır açıyı farklı kabul eder. Özellikle şunlara bakın:
   - SOT-23: Q1–Q3
   - SOT-23-6: U3
   - SOP-16: U2
   - LED'lerin kutbu
   - USB-C: J1

   Açısı yanlış görünen parçayı önizlemede döndürebilirsiniz. JLCPCB'nin mühendisleri de üretimden önce ayrıca kontrol eder.
4. **Stok durumu:** Bazı parçalar o gün LCSC stoğunda olmayabilir. Örneğin C14550 (STC12) zaman zaman sıfıra düşüyor, ama o parça zaten dizgiye girmiyor. Stokta olmayan parça için JLCPCB muadil önerir ya da o parçayı boş bırakmanızı ister.

## Elle lehimlenecek parçalar

`delikli-parcalar.csv` dosyasındaki parçalar delikli (THT). Dizgi siparişine dahil edilmediler, çünkü havya ile lehimlemesi kolay ve JLCPCB'de THT montaj ayrıca ücretli.

| Parça | Not |
|---|---|
| U1 (STC12C5A60S2) + XU1 (DIP-40 soket) | Önce soketi lehimleyin. Çip sokete takılır. Çipin çentiği serigrafideki çentikle aynı yöne bakmalı. |
| Y1 (11.0592 MHz kristal) | Kutbu yok. |
| RN1 (10k ×8 SIP-9) | **Kutbu var.** Üzerindeki nokta, serigrafideki kare pad'e (pin 1) gelmeli. |
| J2–J6 (pin header) | 2 adet 1x40 header kesilerek elde edilir: 4 adet 1x10 ve 1 adet 1x3. |

Parçaların nereden alınacağı için `../tedarik.md` dosyasına bakın.
