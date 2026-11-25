/* MS51 UART ISP bootloader: protokol çekirdeği.
 *
 * Nuvoton'un ISP_UART0 protokoluyla uyumludur (NuMicro ISP Programming Tool ile de çalışır):
 *   - Her iki yönde 64 baytlık paketler, 115200 8N1.
 *   - İstek:  [0] komut, [4..7] paket no (LE), [8..63] veri.
 *   - Yanıt:  [0..1] alınan 64 baytın toplamı (LE), [4..7] paket no + 1, [8..] komuta göre veri.
 *   - CMD_UPDATE_APROM: [8..11] başlangıç adresi (yok sayılır, hep 0), [12..15] toplam boyut,
 *     [16..63] ilk 48 bayt. Sonraki paketlerin [8..63] kısmı (56 bayt) sırayla yazılır.
 *     Yanıtın [8..9] alanı o ana kadar yazılan baytların toplamıdır.
 *
 * Nuvoton örneğinden farkları:
 *   - Doğrulama hatasında çip kilitlenmez; yazma durur, yanıtın [10] alanına hata kodu konur,
 *     toplam tutmayacağı için yükleyici hatayı fark eder.
 *   - Boyut APROM'u aşarsa yazma yapılmaz (hata kodu 2).
 *   - CMD_UPDATE_CONFIG desteklenmez: yanlış bir CONFIG çipi bootloader'sız bırakabilir.
 *     Mevcut ayarlar değiştirilmeden geri gönderilir. CONFIG yalnızca ICP ile değiştirilir.
 *   - APROM boşsa (ilk bayt 0xFF) zaman aşımında bile bootloader'da kalınır.
 */
#include "hal.h"

#define CMD_UPDATE_APROM 0xA0
#define CMD_UPDATE_CONFIG 0xA1
#define CMD_READ_CONFIG 0xA2
#define CMD_ERASE_ALL 0xA3
#define CMD_SYNC_PACKNO 0xA4
#define CMD_GET_FWVER 0xA6
#define CMD_RUN_APROM 0xAB
#define CMD_CONNECT 0xAE
#define CMD_GET_DEVICEID 0xB1

#define FW_VERSION 0x51        /* Nuvoton örneği 0x28; yükleyici 0x51 görünce [10] hata kodunu kullanır */
#define BEKLE_MS 500           /* reset sonrası bağlantı bekleme süresi */
#define BAYT_ARASI_MS 50       /* yarım kalan paketi atma süresi */

#define HATA_DOGRULAMA 1
#define HATA_BOYUT 2

static XDATA uint8_t rx[64];
static XDATA uint8_t tx[64];

static uint16_t adres;          /* sıradaki yazma adresi */
static uint16_t boyut;          /* toplam yazılacak bayt */
static uint16_t toplam;         /* yazılan baytların toplamı */
static uint8_t yaziyor;
static uint8_t hata;

static void yanit_hazirla(void)
{
    uint16_t s = 0;
    uint8_t i;
    for (i = 0; i < 64; i++) {
        s += rx[i];
        tx[i] = 0;
    }
    tx[0] = (uint8_t)s;
    tx[1] = (uint8_t)(s >> 8);
    /* paket no + 1, 32 bit */
    tx[4] = rx[4] + 1;
    tx[5] = rx[5] + (tx[4] == 0);
    tx[6] = rx[6] + (tx[4] == 0 && tx[5] == 0);
    tx[7] = rx[7] + (tx[4] == 0 && tx[5] == 0 && tx[6] == 0);
}

static void gonder(void)
{
    uint8_t i;
    for (i = 0; i < 64; i++)
        hal_tx(tx[i]);
}

static uint8_t aprom_sil(void)
{
    uint16_t a;
    for (a = 0; a < APROM_SIZE; a += PAGE_SIZE)
        if (!hal_erase_page(a))
            return 0;
    return 1;
}

/* rx[bas..63] verisini sıradaki adrese yazar */
static void veri_yaz(uint8_t bas)
{
    uint8_t i;
    for (i = bas; i < 64 && yaziyor; i++) {
        if (!hal_program(adres, rx[i])) {
            hata = HATA_DOGRULAMA;
            yaziyor = 0;
            break;
        }
        toplam += rx[i];
        if (++adres == boyut)
            yaziyor = 0;
    }
    tx[8] = (uint8_t)toplam;
    tx[9] = (uint8_t)(toplam >> 8);
    tx[10] = hata;
}

static void config_yaz_tx(void)
{
    uint8_t c[4];
    hal_read_config(c);
    tx[8] = c[0];
    tx[9] = c[1];
    tx[10] = c[2];
    tx[11] = 0xFF;
    tx[12] = c[3];
    tx[13] = tx[14] = tx[15] = 0xFF;
}

/* Bir paketi işler. Bağlantı kuruldu sinyali olarak 1 döner. */
static uint8_t isle(void)
{
    uint8_t baglandi = 0;
    yanit_hazirla();
    switch (rx[0]) {
    case CMD_CONNECT:
    case CMD_SYNC_PACKNO:
        baglandi = 1;
        break;
    case CMD_GET_FWVER:
        tx[8] = FW_VERSION;
        break;
    case CMD_GET_DEVICEID:
        hal_read_id(&tx[8]);
        break;
    case CMD_READ_CONFIG:
    case CMD_UPDATE_CONFIG:
        config_yaz_tx();
        break;
    case CMD_ERASE_ALL:
        tx[10] = aprom_sil() ? 0 : HATA_DOGRULAMA;
        break;
    case CMD_RUN_APROM:
        hal_run_aprom();
        break;
    case CMD_UPDATE_APROM:
        boyut = (uint16_t)rx[12] | ((uint16_t)rx[13] << 8);
        adres = 0;
        toplam = 0;
        hata = 0;
        yaziyor = 0;
        if (rx[14] || rx[15] || boyut > APROM_SIZE) {
            hata = HATA_BOYUT;
        } else if (!aprom_sil()) {
            hata = HATA_DOGRULAMA;
        } else if (boyut) {
            yaziyor = 1;
            veri_yaz(16);
            break;
        }
        veri_yaz(64);  /* yalnızca durum alanlarını doldurur */
        break;
    default:
        veri_yaz(yaziyor ? 8 : 64);
        break;
    }
    gonder();
    return baglandi;
}

void isp_calistir(void)
{
    uint8_t n = 0, b, bagli = 0;
    uint16_t bekle = BEKLE_MS, bosta = 0;
    uint8_t bos = hal_read(0) == 0xFF;   /* APROM'da program yoksa bootloader'da kal */

    for (;;) {
        if (hal_rx(&b)) {
            rx[n++] = b;
            bosta = 0;
            if (n == 64) {
                n = 0;
                if (isle())
                    bagli = 1;
            }
        }
        if (hal_tick()) {
            if (n && ++bosta >= BAYT_ARASI_MS)
                n = 0;
            if (!bagli && !bos && bekle && --bekle == 0)
                hal_run_aprom();
        }
    }
}
