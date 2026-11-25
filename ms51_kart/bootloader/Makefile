# MS51 UART ISP bootloader
#   make          -> ms51_isp.ihx / ms51_isp.bin (SDCC, LDROM'a yazılır)
#   make host     -> isp_host (bilgisayarda test için, cc)
LDROM_KB ?= 2
LDROM_BYTES = $(shell echo $$(($(LDROM_KB) * 1024)))

SDCC = sdcc
SDFLAGS = -mmcs51 --model-small --opt-code-size --std-sdcc11 -DLDROM_KB=$(LDROM_KB) \
          --code-size $(LDROM_BYTES) --xram-size 2048 --iram-size 256

all: ms51_isp.bin

isp.rel: isp.c hal.h
	$(SDCC) $(SDFLAGS) -c isp.c

hal_ms51.rel: hal_ms51.c hal.h
	$(SDCC) $(SDFLAGS) -c hal_ms51.c

ms51_isp.ihx: hal_ms51.rel isp.rel
	$(SDCC) $(SDFLAGS) -o $@ hal_ms51.rel isp.rel

ms51_isp.bin: ms51_isp.ihx
	makebin -p $< $@
	@echo "boyut: $$(wc -c < $@) bayt (LDROM $(LDROM_BYTES) bayt)"

host: isp_host

isp_host: isp.c hal_host.c hal.h
	cc -O2 -Wall -Wextra -DLDROM_KB=$(LDROM_KB) -o $@ isp.c hal_host.c

clean:
	rm -f *.rel *.asm *.lst *.rst *.sym *.map *.mem *.lk *.ihx *.bin isp_host

.PHONY: all host clean
