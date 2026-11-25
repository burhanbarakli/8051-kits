/* Bootloader donanım katmanı. isp.c yalnızca bu fonksiyonları kullanır;
 * hal_ms51.c gerçek çip için, hal_host.c bilgisayarda test için uygular. */
#ifndef HAL_H
#define HAL_H

#include <stdint.h>

#ifdef __SDCC
#define XDATA __xdata
#else
#define XDATA
#endif

/* MS51PC0AE: 32 KB flash; LDROM (bootloader) boyutu CONFIG1 ile seçilir. */
#ifndef LDROM_KB
#define LDROM_KB 2
#endif
#define APROM_SIZE ((uint16_t)(32 - LDROM_KB) * 1024u)
#define PAGE_SIZE 128u

void hal_init(void);
uint8_t hal_rx(uint8_t *b);      /* bayt geldiyse 1 döner, beklemez */
void hal_tx(uint8_t b);
uint8_t hal_tick(void);          /* her ~1 ms'de bir 1 döner */

uint8_t hal_erase_page(uint16_t addr);            /* başarılıysa 1 */
uint8_t hal_program(uint16_t addr, uint8_t d);   /* yazar ve geri okuyarak doğrular; başarılıysa 1 */
uint8_t hal_read(uint16_t addr);                  /* APROM'dan bir bayt */
void hal_read_id(uint8_t *id);                    /* DID düşük, DID yüksek, PID düşük, PID yüksek */
void hal_read_config(uint8_t *cfg);               /* CONFIG0, 1, 2, 4 */
void hal_run_aprom(void);                         /* dönmez */

#endif
