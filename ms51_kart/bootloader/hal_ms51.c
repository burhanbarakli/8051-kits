/* MS51 (32K serisi, MS51PC0AE) donanım katmanı: SDCC ile LDROM'a derlenir.
 *
 * Yazmaç adresleri ve IAP komutları Nuvoton MS51 32K BSP başlık dosyalarından
 * (MS51_32K.h, SFR_Macro_MS51_32K.h) alınmıştır. Kesme kullanılmaz (EA = 0),
 * UART ve zamanlayıcı yoklamayla (polling) okunur.
 *
 * Saat: dahili HIRC 24 MHz'e ayarlanır (115200 baud için). Kullanıcı programına
 * geçmeden önce fabrika varsayılanı 16 MHz geri yüklenir.
 */
#include "hal.h"

__sfr __at(0x84) RCTRIM0;
__sfr __at(0x85) RCTRIM1;
__sfr __at(0x87) PCON;
__sfr __at(0x88) TCON;
__sfr __at(0x89) TMOD;
__sfr __at(0x8A) TL0;
__sfr __at(0x8C) TH0;
__sfr __at(0x91) SFRS;
__sfr __at(0x98) SCON;
__sfr __at(0x99) SBUF;
__sfr __at(0x9F) CHPCON;
__sfr __at(0xA4) IAPTRG;
__sfr __at(0xA5) IAPUEN;
__sfr __at(0xA6) IAPAL;
__sfr __at(0xA7) IAPAH;
__sfr __at(0xA8) IE;
__sfr __at(0xAE) IAPFD;
__sfr __at(0xAF) IAPCN;
__sfr __at(0xB1) P0M1;
__sfr __at(0xB2) P0M2;
__sfr __at(0xC4) T3CON;
__sfr __at(0xC5) RL3;
__sfr __at(0xC6) RH3;
__sfr __at(0xC7) TA;

__sbit __at(0x98) RI;
__sbit __at(0x99) TI;
__sbit __at(0x8C) TR0;
__sbit __at(0x8D) TF0;

/* IAP komutları (IAPCN) */
#define IAP_READ_UID 0x04      /* UID / fabrika HIRC ayar değerleri */
#define IAP_READ_ID 0x0C
#define IAP_READ_AP 0x00
#define IAP_PROGRAM_AP 0x21
#define IAP_ERASE_AP 0x22
#define IAP_READ_CONFIG 0xC0

/* CHPCON bitleri */
#define IAPEN 0x01
#define BS 0x02
#define IAPFF 0x40
#define SWRST 0x80

#define TA_AC() do { TA = 0xAA; TA = 0x55; } while (0)

/* Timer0, mod 1, Fsys/12 = 2 MHz: 1 ms = 2000 sayım */
#define T0_YUKLE (65536u - 2000u)

static uint8_t iap(uint8_t cmd, uint16_t addr, uint8_t d)
{
    IAPCN = cmd;
    IAPAH = addr >> 8;
    IAPAL = (uint8_t)addr;
    IAPFD = d;
    TA_AC();
    IAPTRG |= 0x01;            /* IAPGO: CPU işlem bitene kadar bekler */
    if (CHPCON & IAPFF) {      /* hata bayrağı (ör. korumalı adres) */
        TA_AC();
        CHPCON &= ~IAPFF;
        return 0;
    }
    return 1;
}

static void hirc_ayarla(uint8_t uid_adres)
{
    uint8_t t0, t1;
    iap(IAP_READ_UID, uid_adres, 0);
    t0 = IAPFD;
    iap(IAP_READ_UID, uid_adres + 1, 0);
    t1 = IAPFD;
    TA_AC();
    RCTRIM0 = t0;
    TA_AC();
    RCTRIM1 = t1;
}

void hal_init(void)
{
    IE = 0;                    /* EA = 0: TA dizileri kesmeyle bölünmesin */
    SFRS = 0;
    TA_AC();
    CHPCON |= IAPEN;
    TA_AC();
    IAPUEN |= 0x01;            /* APUEN: APROM yazılabilir */
    hirc_ayarla(0x38);         /* HIRC = 24 MHz */

    /* UART0: P0.6 = TXD (quasi), P0.7 = RXD (giriş), mod 1, 115200 = 24 MHz / (16 * 13) */
    P0M1 &= ~0x40;
    P0M2 &= ~0x40;
    P0M1 |= 0x80;
    P0M2 &= ~0x80;
    SCON = 0x50;
    PCON |= 0x80;              /* SMOD */
    T3CON = (T3CON & 0xF8) | 0x20;  /* ön bölücü 1, BRCK: UART0 saati Timer3 */
    RH3 = (65536u - 13) >> 8;
    RL3 = (uint8_t)(65536u - 13);
    T3CON |= 0x08;             /* TR3 */

    TMOD = (TMOD & 0xF0) | 0x01;
    TH0 = T0_YUKLE >> 8;
    TL0 = (uint8_t)T0_YUKLE;
    TF0 = 0;
    TR0 = 1;
}

uint8_t hal_rx(uint8_t *b)
{
    if (!RI)
        return 0;
    RI = 0;
    *b = SBUF;
    return 1;
}

void hal_tx(uint8_t b)
{
    TI = 0;
    SBUF = b;
    while (!TI)
        ;
}

uint8_t hal_tick(void)
{
    if (!TF0)
        return 0;
    TR0 = 0;
    TH0 = T0_YUKLE >> 8;
    TL0 = (uint8_t)T0_YUKLE;
    TF0 = 0;
    TR0 = 1;
    return 1;
}

uint8_t hal_erase_page(uint16_t addr)
{
    return iap(IAP_ERASE_AP, addr, 0xFF);   /* silmede IAPFD = 0xFF olmalı */
}

uint8_t hal_program(uint16_t addr, uint8_t d)
{
    if (!iap(IAP_PROGRAM_AP, addr, d))
        return 0;
    return hal_read(addr) == d;
}

uint8_t hal_read(uint16_t addr)
{
    iap(IAP_READ_AP, addr, 0);
    return IAPFD;
}

void hal_read_id(uint8_t *id)
{
    uint8_t i;
    for (i = 0; i < 4; i++) {
        iap(IAP_READ_ID, i, 0);
        id[i] = IAPFD;
    }
}

void hal_read_config(uint8_t *cfg)
{
    static const uint8_t adres[4] = {0, 1, 2, 4};
    uint8_t i;
    for (i = 0; i < 4; i++) {
        iap(IAP_READ_CONFIG, adres[i], 0);
        cfg[i] = IAPFD;
    }
}

void hal_run_aprom(void)
{
    hirc_ayarla(0x30);         /* HIRC fabrika varsayılanı 16 MHz */
    TA_AC();
    IAPUEN &= ~0x01;
    TA_AC();
    CHPCON &= ~IAPEN;
    TA_AC();
    CHPCON &= ~BS;             /* yazılım reset'inden sonra APROM'dan başla */
    TA_AC();
    CHPCON |= SWRST;
    for (;;)
        ;
}

void isp_calistir(void);

void main(void)
{
    hal_init();
    isp_calistir();
}
