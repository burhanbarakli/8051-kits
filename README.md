# 8051 geliştirme kitleri

USB üzerinden, tarayıcıdaki bir web arayüzüyle programlanan iki 8051 geliştirme kartı.

| Klasör | İçerik |
|---|---|
| [`donanim/`](donanim/) | **STC12C5A60S2 kartı.** Bootloader çipin içinde fabrikadan gelir. Şema, KiCad projesi, JLCPCB üretim dosyaları, malzeme listesi, tedarik notları ([`tedarik.md`](donanim/tedarik.md)), 3D baskı kutusu ve 8051 MCU karşılaştırması ([`mcu-karsilastirma.md`](donanim/mcu-karsilastirma.md)) |
| [`ms51_kart/`](ms51_kart/) | **Nuvoton MS51PC0AE kartı (Rev C).** KiCad projesi, üretim dosyaları, LDROM bootloader'ı (`bootloader/`), 3D baskı kutusu ve alışveriş takip sayfası. Bkz. [`ms51_kart/BENIOKU.md`](ms51_kart/BENIOKU.md) |
| [`yukleyici/`](yukleyici/) | **Web Serial yükleyici** (Chrome/Edge). STC12 ve MS51 için, testleriyle. Bkz. [`yukleyici/BENIOKU.md`](yukleyici/BENIOKU.md) |

## Durum

- Kartlar KiCad'de tasarlandı. ERC ve DRC hatasız.
- Yükleyici ve bootloader bilgisayarda test edildi:
  - STC12 protokolü stcgal ile birebir karşılaştırıldı.
  - MS51 bootloader'ı yükleyiciye karşı uçtan uca test edildi.
- Kartlar henüz üretilmedi ve gerçek donanımda denenmedi.

## Testleri çalıştırma

```bash
(cd ms51_kart/bootloader && make host)
cd yukleyici && node --test test/*.test.mjs
```
