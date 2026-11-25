# JLCPCB sipariş dosyaları: MS51 kartı (Rev B)

Bu klasördeki dosyalar `../kicad/uretim.py` ile KiCad PCB dosyasından üretilir. Elle düzenlemeyin.

| Dosya | Ne için |
|---|---|
| `ms51_kart-gerber.zip` | PCB siparişi: Gerber ve delik dosyaları |
| `jlcpcb-bom.csv` | Dizgi (SMT montaj) için BOM: 14 satır, 25 SMD parça, LCSC kodlarıyla |
| `jlcpcb-cpl.csv` | Dizgi için parça konumları ve açıları |
| `delikli-parcalar.csv` | Elle lehimlenecek parçalar: yalnızca pin header'lar |
| `takilmaz.csv` | Varsayılan montajda boş kalanlar: Y1, C8, C9. Yalnızca U2 yerine CH340G takılırsa elle lehimlenir |
| `gerber/` | Zip'in açılmış hâli |

## PCB siparişi

1. jlcpcb.com > **Order Now** > `ms51_kart-gerber.zip` dosyasını yükleyin. Kart 84 x 50 mm, 2 katman olarak algılanır.
2. Varsayılan seçenekler uygundur: FR-4, 1.6 mm, 1 oz, HASL.
3. Kartta 0.2 mm'nin altında aralık ya da 0.3 mm'nin altında delik yok. En ucuz standart üretim yeterli.

## Dizgi (önerilir)

MCU, 0.8 mm adımlı LQFP-32 kılıfında. Havyayla lehimlenebilir ama ilk kez yapacak biri için zor. Bu yüzden SMD parçaları JLCPCB'ye lehimletmek önerilir.

1. **PCB Assembly**'yi seçin, montaj tarafı **Top**. BOM olarak `jlcpcb-bom.csv`, CPL olarak `jlcpcb-cpl.csv` dosyasını yükleyin.
2. **Açıları önizlemede kontrol edin.** Özellikle şunlara bakın:
   - **U1 (LQFP-32):** 1. pin noktası serigrafideki üçgenle aynı köşede olmalı.
   - **U2 (SOP-16)**
   - **U3 (SOT-23-6)**
   - **LED'lerin kutbu**
   - **J1 (USB-C)**
3. **Stok:** 17 Kasım'da 100 nF (C14663), 1k (C21190) ve yeşil LED (C72043) LCSC'de stokta değildi. JLCPCB'nin önerdiği muadilleri seçebilirsiniz; aynı kılıfta herhangi bir 100 nF, 1k ve 0603 LED olur.
4. **JLCPCB çipleri programlamaz.** Kart elinize bootloader'sız gelir. Her karta bir kez Nu-Link ile bootloader yüklenir; bkz. `../BENIOKU.md`.

## Elle lehimlenecekler

2 adet 1x40 pin header kesilerek şunlar elde edilir:
- 3 adet 1x10: J2 (P0), J3 (P1), J4 (P3)
- 1 adet 1x8: J5 (P2)
- 1 adet 1x5: J6 (ICP)

**CH340G seçeneği:** U2'ye CH340C yerine CH340G takılacaksa dizgide U2'yi BOM'dan çıkarın (ya da boş bırakın) ve şunları elle lehimleyin (`takilmaz.csv`):
- CH340G (U2, SOP-16)
- 12 MHz kristal (Y1, HC-49S, delikli)
- 2 × 22 pF (C8, C9, 0603)
