# MS51 UART ISP bootloader

MS51 kartının (`..`) LDROM'una bir kez yüklenen bootloader. Yüklendikten sonra kart USB üzerinden programlanır.

| | |
|---|---|
| Boyut | **1 630 bayt.** 2 KB'lık LDROM'a sığıyor, kullanıcı programına **30 KB** APROM kalıyor |
| Protokol | Nuvoton ISP_UART0 ile uyumlu (115200 8N1, 64 baytlık paketler). Nuvoton'un *NuMicro ISP Programming Tool* programıyla da kullanılabilir |
| Saat | Dahili HIRC 24 MHz. Kullanıcı programına geçerken fabrika ayarı 16 MHz geri yüklenir |
| Giriş | Her reset'te çalışır, 500 ms bağlantı bekler; bağlantı gelmezse kullanıcı programına geçer. APROM boşsa beklemede kalır |
| Yükleyici | `../../yukleyici/nuvoton.js` (web) |

## Dosyalar

| Dosya | Ne |
|---|---|
| `isp.c` | Protokol çekirdeği. Donanımdan bağımsız C; MS51'de ve bilgisayarda aynı kod derlenir |
| `hal.h` | Donanım katmanı arayüzü |
| `hal_ms51.c` | MS51 için: yazmaçlar, IAP (flash yazma), UART0, Timer0. Kesme kullanılmaz |
| `hal_host.c` | Bilgisayarda test için: seri port yerine stdin/stdout, flash bir dosyada |
| `ms51_isp.bin`, `ms51_isp.ihx` | Derlenmiş bootloader (SDCC 4.2.0). LDROM'a yazılacak dosya |
| `Makefile` | `make` ile MS51 sürümü, `make host` ile test sürümü derlenir |

## Nuvoton örneğinden farkları

- **Doğrulama hatası:** Nuvoton örneğinde çip sonsuz döngüde kilitlenir. Burada yazma durur ve yükleyici hata kodu alır.
- **Adres sınırı:** Program APROM'u aşarsa yazma yapılmaz, yükleyici "sığmıyor" hatası verir.
- **CONFIG yazma:** `CMD_UPDATE_CONFIG` kapalı. Yanlış bir CONFIG çipi bootloader'sız bırakabilir; CONFIG yalnızca ICP ile değiştirilmeli. Komut gelirse mevcut ayarlar değiştirilmeden geri gönderilir.
- **Boş APROM:** APROM boşsa bootloader zaman aşımında boş belleğe atlamaz, beklemede kalır.
- **Sürüm numarası:** Bootloader `0x51` döner (Nuvoton örneği `0x28` döner). Yükleyici bunu görünce yanıttaki hata kodunu da kullanır.

## Çipe yükleme (her çip için bir kez, Nu-Link ile)

1. Kartı USB'den çıkarın ve Nu-Link'i J6 (ICP) header'ına bağlayın. Pin sırası: 1 = 5V, 2 = DAT, 3 = CLK, 4 = RST, 5 = GND.
2. Nuvoton'un **NuMicro ICP Programming Tool** programını açın (Windows) ve çip olarak MS51PC0AE'yi seçin.
3. **LDROM** alanına `ms51_isp.bin` dosyasını yükleyin. APROM boş kalabilir.
4. **Config** ayarları:
   - **Boot select: LDROM** (CONFIG0.CBS = 0). Çip her reset'te bootloader'dan başlar.
   - **LDROM size: 2 KB** (CONFIG1.LDSIZE). APROM 30 KB olur. `isp.c` de bu değerle derlendi (`LDROM_KB=2`).
   - **Reset pini etkin kalmalı** (P2.0 = nRESET). Kapatılırsa DTR ile otomatik reset çalışmaz.
5. Programlayın. Sonra Nu-Link'i çıkarın, kartı USB-C ile takın. Web yükleyicide "Nuvoton MS51" seçilerek program yüklenir.

**CONFIG bitleri:** CONFIG bit adlarını N76E003'teki karşılıklarına göre yazdım; MS51 bu çipin devamı. Programlamadan önce ICP aracındaki seçenek adlarını MS51 datasheet'iyle karşılaştırın.

**Mac ve Linux:** Açık kaynak [nuvoprog](https://github.com/mountaintom/nuvoprog) N76E003 ve (deneysel olarak) MS51FB9AE'yi destekliyor, ama MS51PC0AE'nin dahil olduğu 32K serisini desteklediği belirtilmemiş. Güvenilir yol Windows'taki Nuvoton aracı.

## Derleme

SDCC 4.x gerekir. Kurulum: `apt install sdcc` (Linux) ya da sdcc.sourceforge.net (Windows/macOS).

```bash
make            # ms51_isp.ihx ve ms51_isp.bin
make host       # isp_host (testler için)
```

SDCC kurmadan Docker ile derlemek için:

```bash
docker run --rm -v "$PWD":/b -w /b debian:bookworm-slim sh -c 'apt-get update -qq && apt-get install -y -qq sdcc make >/dev/null && make'
```

## Test

`isp.c`, bilgisayarda `hal_host.c` ile derlenip web yükleyiciye (`nuvoton.js`) karşı uçtan uca çalıştırılıyor:

```bash
make host
cd ../../yukleyici && node --test test/nuvoton.test.mjs
```

11 testin hepsi geçti. Sınanan durumlar:
- 3 000 baytlık programın yazılıp kullanıcı programının başlatılması
- Tam 30 KB'lık programın yazılması ve eski içeriğin tamamen silinmesi
- 30 KB'tan büyük programın reddedilmesi
- Doğrulama hatası. Toplamı değiştirmeyen sıfır baytta bile yakalanıyor
- Gerçek çipe yakın yavaş silme (sayfa başına 5 ms)
- Bağlantıdan önce hatta gelen yarım paket
- APROM doluyken 500 ms sonra kullanıcı programına geçiş, boşken beklemede kalma
- Bootloader yokken açık hata mesajı
- Nuvoton'un kendi ISP_UART0 bootloader'ının davranışıyla uyum (taklit edilerek)

**Doğrulanmayanlar:** `hal_ms51.c` gerçek MS51'de çalıştırılmadı. Şu konular kart gelince denenecek:
- HIRC ayarı
- 115200 baud hatası
- IAP zamanlaması
- Yazılım reset'iyle APROM'a geçiş

Yazmaç adresleri ve IAP komutları Nuvoton'un MS51 32K BSP'sinden (MS51_32K.h, SFR_Macro_MS51_32K.h) ve ISP_UART0 örneğinden alındı. Kod, bu örnek referans alınarak sıfırdan yazıldı.
