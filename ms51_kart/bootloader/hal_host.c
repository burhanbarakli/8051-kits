/* Bilgisayarda test için donanım katmanı: isp.c değiştirilmeden derlenir.
 *
 *   ./isp_host flash.bin
 *
 * Seri port yerine stdin/stdout kullanılır (ikili). APROM, flash.bin dosyasında tutulur
 * (yoksa 0xFF ile başlar); CMD_RUN_APROM gelince ya da stdin kapanınca dosyaya yazılır ve
 * program çıkar (çıkış kodu 0: RUN_APROM, 3: stdin kapandı, 4: bekleme süresi doldu).
 *
 * Ortam değişkenleri: SILME_MS (sayfa başına silme gecikmesi, gerçek çipte ~5 ms),
 * BOZUK_ADRES (bu adreste doğrulama hatası taklit edilir).
 */
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include "hal.h"

static uint8_t flash[APROM_SIZE];
static const char *dosya;
static long silme_ms;
static long bozuk = -1;
static struct timespec son;

static void kaydet(void)
{
    FILE *f = fopen(dosya, "wb");
    if (f) {
        fwrite(flash, 1, sizeof flash, f);
        fclose(f);
    }
}

void hal_init(void)
{
    FILE *f = fopen(dosya, "rb");
    memset(flash, 0xFF, sizeof flash);
    if (f) {
        size_t n = fread(flash, 1, sizeof flash, f);
        (void)n;
        fclose(f);
    }
    if (getenv("SILME_MS"))
        silme_ms = atol(getenv("SILME_MS"));
    if (getenv("BOZUK_ADRES"))
        bozuk = atol(getenv("BOZUK_ADRES"));
    clock_gettime(CLOCK_MONOTONIC, &son);
}

uint8_t hal_rx(uint8_t *b)
{
    struct pollfd p = {0, POLLIN, 0};
    if (poll(&p, 1, 1) <= 0)
        return 0;
    if (read(0, b, 1) != 1) {      /* stdin kapandı */
        kaydet();
        exit(3);
    }
    return 1;
}

void hal_tx(uint8_t b)
{
    if (write(1, &b, 1) != 1)
        exit(5);
}

uint8_t hal_tick(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    if ((t.tv_sec - son.tv_sec) * 1000000000L + (t.tv_nsec - son.tv_nsec) < 1000000L)
        return 0;
    son.tv_nsec += 1000000L;
    if (son.tv_nsec >= 1000000000L) {
        son.tv_nsec -= 1000000000L;
        son.tv_sec++;
    }
    return 1;
}

uint8_t hal_erase_page(uint16_t addr)
{
    if (addr >= APROM_SIZE)
        return 0;
    if (silme_ms)
        usleep(silme_ms * 1000);
    memset(flash + (addr & ~(PAGE_SIZE - 1)), 0xFF, PAGE_SIZE);
    return 1;
}

uint8_t hal_program(uint16_t addr, uint8_t d)
{
    if (addr >= APROM_SIZE)
        return 0;
    flash[addr] &= d;              /* flash yalnızca 1 -> 0 yazabilir */
    if (addr == bozuk)
        flash[addr] ^= 0x01;
    return flash[addr] == d;
}

uint8_t hal_read(uint16_t addr)
{
    return addr < APROM_SIZE ? flash[addr] : 0xFF;
}

void hal_read_id(uint8_t *id)
{
    /* Gerçek çipin kimliği değil, test için sabit değer */
    id[0] = 0x51;
    id[1] = 0x4B;
    id[2] = 0x00;
    id[3] = 0x00;
}

void hal_read_config(uint8_t *cfg)
{
    cfg[0] = 0x7F;   /* CBS = 0: LDROM'dan başla */
    cfg[1] = 0xFD;   /* LDSIZE: 2 KB */
    cfg[2] = 0xFF;
    cfg[3] = 0xFF;
}

void hal_run_aprom(void)
{
    kaydet();
    exit(0);
}

void isp_calistir(void);

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "kullanım: %s flash.bin\n", argv[0]);
        return 2;
    }
    dosya = argv[1];
    hal_init();
    isp_calistir();
    return 0;
}
