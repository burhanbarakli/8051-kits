// LED3 (P1.7) yanıp söner. SDCC ile:  sdcc blink.c   -> blink.ihx (yükleyiciye verilir)
// LED3'ün anodu R13 üzerinden VCC_MCU'da, katodu P1.7'de: P1.7 = 0 iken yanar.
#include <8051.h>

static void bekle(unsigned int ms)
{
    // 11.0592 MHz, 1T çekirdek: iç döngü yaklaşık 1 ms (ölçülmedi, kaba ayar)
    while (ms--) {
        for (volatile unsigned int i = 0; i < 1100; i++) {
        }
    }
}

void main(void)
{
    for (;;) {
        P1_7 = 0;
        bekle(250);
        P1_7 = 1;
        bekle(250);
    }
}
