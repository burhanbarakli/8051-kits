"""MS51 geliştirme kartı (Rev C): parça ve bağlantı tanımı.

Tek kaynak budur. ms51_sembol.py MCU sembolünü, kicad_uret.py şemayı, pcb_uret.py
PCB'yi bu dosyadan üretir; ../BOM.csv ile aynı devreyi tarif eder.

Her parça: (ref, lib_id, değer, footprint, LCSC, {pin numarası: net}, (x, y) mm)
Haritada olmayan pinler şemada "bağlantısız" (no-connect) işaretlenir.

STC12 kartından farkları:
  - MCU Nuvoton MS51PC0AE (1T 8051, 32K flash, 12 bit ADC, LQFP-32)
  - Bootloader fabrikadan gelmez; ICP header'ından (J6) Nu-Link ile bir kez LDROM'a yüklenir.
    Sonra her reset'te bootloader çalıştığı için CH340'ın DTR'si ile reset atmak yeterli:
    STC'deki güç kesici (Q1-Q3, ISP butonu) yok
  - P0 açık-drain değil (portlar quasi/push-pull ayarlanabilir): P0 pull-up dizisi yok

Rev B: U2 yerine CH340C (kristalsiz, varsayılan) ya da CH340G takılabilir. İkisinin bacak
dizilimi aynı; G'nin 7/8 (XI/XO) bacaklarına 12 MHz kristal gerekir. Y1, C8, C9 bunun için:
CH340C ile boş bırakılır (TAKILMAZ), CH340G ile lehimlenir. CH340G Türkiye'de stokta bulunur.

Rev C (bir meslektaşın incelemesinden sonra):
  - MCU'ya 24 MHz kristal (Y2, XIN = P0.0 pin 23, XOUT = P0.1 pin 24) ve 18 pF yük
    kondansatörleri (C10, C11). Kristal 12 pF yüklü: 2 x (12 - ~3 pF kaçak) = 18 pF.
    Çip açılışta her zaman dahili HIRC ile başlar; HXT'ye yazılım geçer (CKEN/CKSWT).
    P0.0/P0.1 artık header'a çıkmaz (J2'nin 1-2. pinleri boş).
  - ICP: ICE_DAT ve ICE_CLK'a 100k pull-up (R9, R10) ve 100R seri direnç (R11, R12);
    J6 MCU'nun yanına alındı.
  - Reset: RST'ye 100 nF (C12). Önerilen 10 uF konmadı: DTR'den gelen otomatik reset
    darbesini (C7 üzerinden) yutardı. C7 bu yüzden 100 nF'tan 1 uF'a çıktı; DTR inince
    RST ~0,45 V'a iner, ~11 ms'de (10k x 1,1 uF) geri kalkar.
"""

FP_R = 'Resistor_SMD:R_0603_1608Metric'
FP_C = 'Capacitor_SMD:C_0603_1608Metric'
FP_C0805 = 'Capacitor_SMD:C_0805_2012Metric'
FP_LED = 'LED_SMD:LED_0603_1608Metric'
FP_SW = 'Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A'
FP_HDR = 'Connector_PinHeader_2.54mm:PinHeader_1x{:02d}_P2.54mm_Vertical'


def two(a, b):
    return {'1': a, '2': b}


# MS51PC0AE LQFP-32 (Nuvoton MS51 Series Product Brief Rev 2.00, Şekil 5-1).
# numara: (sembol adı, taraf, sıra, elektrik tipi)  taraf L/R, sıra yukarıdan aşağı
MS51_PINLER = {
    '6': ('VDD', 'L', 0, 'power_in'),
    '1': ('nRESET/P2.0', 'L', 1, 'input'),
    '16': ('P2.1/ADC9', 'L', 2, 'bidirectional'),
    '15': ('P2.2/ADC10', 'L', 3, 'bidirectional'),
    '14': ('P2.3/ADC11', 'L', 4, 'bidirectional'),
    '13': ('P2.4/ADC12', 'L', 5, 'bidirectional'),
    '8': ('P2.5/ADC15', 'L', 6, 'bidirectional'),
    '2': ('P3.0/INT0/ADC1', 'L', 8, 'bidirectional'),
    '18': ('P3.1', 'L', 9, 'bidirectional'),
    '19': ('P3.2', 'L', 10, 'bidirectional'),
    '25': ('P3.3', 'L', 11, 'bidirectional'),
    '32': ('P3.4', 'L', 12, 'bidirectional'),
    '17': ('P3.5', 'L', 13, 'bidirectional'),
    '10': ('P3.6/RXD1', 'L', 14, 'bidirectional'),
    '9': ('P3.7/TXD1', 'L', 15, 'bidirectional'),
    '4': ('VSS', 'L', 16, 'power_in'),
    '23': ('P0.0/XIN', 'R', 0, 'bidirectional'),
    '24': ('P0.1/XOUT', 'R', 1, 'bidirectional'),
    '26': ('P0.2/ICE_CLK', 'R', 2, 'bidirectional'),
    '27': ('P0.3/ADC6', 'R', 3, 'bidirectional'),
    '28': ('P0.4/ADC5', 'R', 4, 'bidirectional'),
    '29': ('P0.5/ADC4', 'R', 5, 'bidirectional'),
    '30': ('P0.6/TXD/ADC3', 'R', 6, 'bidirectional'),
    '31': ('P0.7/RXD/ADC2', 'R', 7, 'bidirectional'),
    '22': ('P1.0/PWM0_2', 'R', 9, 'bidirectional'),
    '21': ('P1.1/ADC7', 'R', 10, 'bidirectional'),
    '20': ('P1.2/PWM0_0', 'R', 11, 'bidirectional'),
    '12': ('P1.3/ADC13', 'R', 12, 'bidirectional'),
    '11': ('P1.4/PWM0_1', 'R', 13, 'bidirectional'),
    '7': ('P1.5/PWM0_5', 'R', 14, 'bidirectional'),
    '5': ('P1.6/ICE_DAT', 'R', 15, 'bidirectional'),
    '3': ('P1.7/INT1/ADC0', 'R', 16, 'bidirectional'),
}

# Pin -> net: adı '/' öncesindeki port adı; özel görevli pinler ayrıca
MCU_PINS = {num: ad.split('/')[0] for num, (ad, *_rest) in MS51_PINLER.items()}
MCU_PINS.update({'6': '+5V', '4': 'GND', '1': 'RST', '30': 'MCU_TXD', '31': 'MCU_RXD',
                 '5': 'ICE_DAT', '26': 'ICE_CLK', '23': 'XIN', '24': 'XOUT'})


def header(port, n=8):
    pins = {str(k + 1): f'{port}.{k}' for k in range(n)}
    pins.update({str(n + 1): '+5V', str(n + 2): 'GND'})
    return pins


P0_PINS = header('P0')
P0_PINS.update({'3': 'ICE_CLK', '7': 'MCU_TXD', '8': 'MCU_RXD'})   # ICP ve UART ile ortak
del P0_PINS['1'], P0_PINS['2']                                       # P0.0/P0.1: kristal (Y2)
P1_PINS = header('P1')
P1_PINS.update({'7': 'ICE_DAT'})
P3_PINS = header('P3')
P2_PINS = {'1': 'RST', **{str(k + 1): f'P2.{k}' for k in range(1, 6)}, '7': '+5V', '8': 'GND'}

# USB-C 16P: GND A1/A12/B1/B12, VBUS A4/A9/B4/B9, CC A5/B5, D+ A6/B6, D- A7/B7, SBU A8/B8, kalkan SH (KiCad 9'da S1)
USBC_PINS = {
    'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'SH': 'GND',
    'A4': 'VBUS', 'A9': 'VBUS', 'B4': 'VBUS', 'B9': 'VBUS',
    'A5': 'CC1', 'B5': 'CC2',
    'A6': 'USB_DP', 'B6': 'USB_DP', 'A7': 'USB_DM', 'B7': 'USB_DM',
}

PARTS = [
    # --- 1. USB ve güç
    ('J1', 'Connector:USB_C_Receptacle_USB2.0_16P', 'TYPE-C-31-M-12',
     'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12', 'C165948', USBC_PINS, (40.64, 60.96)),
    ('F1', 'Device:Polyfuse', '500mA', 'Fuse:Fuse_1206_3216Metric', 'C70075', two('VBUS', '+5V'), (78.74, 38.1)),
    ('R1', 'Device:R', '5.1k', FP_R, 'C23186', two('CC1', 'GND'), (68.58, 76.2)),
    ('R2', 'Device:R', '5.1k', FP_R, 'C23186', two('CC2', 'GND'), (76.2, 76.2)),
    ('U3', 'Power_Protection:USBLC6-2SC6', 'USBLC6-2SC6', 'Package_TO_SOT_SMD:SOT-23-6', 'C7519',
     {'1': 'USB_DP', '6': 'USB_DP', '3': 'USB_DM', '4': 'USB_DM', '5': '+5V', '2': 'GND'}, (106.68, 60.96)),
    ('C1', 'Device:C', '10uF', FP_C0805, 'C15850', two('+5V', 'GND'), (93.98, 88.9)),
    ('C2', 'Device:C', '100nF', FP_C, 'C14663', two('+5V', 'GND'), (101.6, 88.9)),
    ('R3', 'Device:R', '1k', FP_R, 'C21190', two('+5V', 'LED1_A'), (111.76, 86.36)),
    ('LED1', 'Device:LED', 'PWR yeşil', FP_LED, 'C72043', {'1': 'GND', '2': 'LED1_A'}, (121.92, 86.36)),

    # --- 2. CH340C
    # Sembol CH340G: pinleri CH340C ile aynı, 7/8 XI/XO (CH340C'de bu bacaklar boş, bağlantı zararsız)
    ('U2', 'Interface_USB:CH340G', 'CH340C', 'Package_SO:SOIC-16_3.9x9.9mm_P1.27mm', 'C84681',
     {'1': 'GND', '2': 'CH_TXD', '3': 'CH_RXD', '4': 'CH_V3', '5': 'USB_DP', '6': 'USB_DM',
      '7': 'XI', '8': 'XO', '13': 'DTR_N', '16': '+5V'}, (165.1, 63.5)),
    # Yalnızca CH340G takılırsa: 12 MHz kristal ve yük kondansatörleri (CH340C ile boş kalır)
    ('Y1', 'Device:Crystal', '12MHz', 'Crystal:Crystal_HC49-4H_Vertical', 'C16369', two('XI', 'XO'),
     (190.5, 96.52)),
    ('C8', 'Device:C', '22pF', FP_C, 'C1653', two('XI', 'GND'), (180.34, 104.14)),
    ('C9', 'Device:C', '22pF', FP_C, 'C1653', two('XO', 'GND'), (200.66, 104.14)),
    ('C3', 'Device:C', '100nF', FP_C, 'C14663', two('+5V', 'GND'), (139.7, 88.9)),
    ('C4', 'Device:C', '100nF', FP_C, 'C14663', two('CH_V3', 'GND'), (147.32, 88.9)),
    # UART: P0.6/P0.7 header'a da çıktığı için seri dirençler (kullanıcı devresi CH340'ı zorlarsa korur)
    ('R4', 'Device:R', '1k', FP_R, 'C21190', two('CH_TXD', 'MCU_RXD'), (210.82, 45.72)),
    ('R5', 'Device:R', '1k', FP_R, 'C21190', two('MCU_TXD', 'CH_RXD'), (226.06, 45.72)),

    # --- 3. Reset: 10k pull-up, 100nF RST-GND (C12), DTR -> 1uF -> 1k (otomatik reset), RESET butonu, tepe kırpma diyodu
    ('R6', 'Device:R', '10k', FP_R, 'C25804', two('+5V', 'RST'), (256.54, 45.72)),
    ('C7', 'Device:C', '1uF', FP_C, 'C15849', two('DTR_N', 'RST_C'), (256.54, 71.12)),
    ('R7', 'Device:R', '1k', FP_R, 'C21190', two('RST_C', 'RST'), (271.78, 71.12)),
    ('D1', 'Device:D_Schottky', 'B5819W', 'Diode_SMD:D_SOD-123', 'C8598', {'1': '+5V', '2': 'RST'}, (271.78, 45.72)),
    ('SW1', 'Switch:SW_Push', 'RESET', FP_SW, 'C318884', two('RST', 'GND'), (294.64, 58.42)),
    ('C12', 'Device:C', '100nF', FP_C, 'C14663', two('RST', 'GND'), (284.48, 86.36)),

    # --- 4. ICP (Nu-Link): VDD, DAT, CLK, RST, GND. MCU tarafında pull-up, header tarafında seri direnç
    ('J6', 'Connector_Generic:Conn_01x05', 'ICP', FP_HDR.format(5), 'C2337',
     {'1': '+5V', '2': 'ICP_DAT', '3': 'ICP_CLK', '4': 'RST', '5': 'GND'}, (337.82, 58.42)),
    ('R9', 'Device:R', '100k', FP_R, 'C25803', two('+5V', 'ICE_DAT'), (360.68, 45.72)),
    ('R10', 'Device:R', '100k', FP_R, 'C25803', two('+5V', 'ICE_CLK'), (370.84, 45.72)),
    ('R11', 'Device:R', '100', FP_R, 'C22775', two('ICE_DAT', 'ICP_DAT'), (360.68, 71.12)),
    ('R12', 'Device:R', '100', FP_R, 'C22775', two('ICE_CLK', 'ICP_CLK'), (370.84, 71.12)),

    # --- 5. MCU ve çevresi
    ('U1', 'MS51:MS51PC0AE', 'MS51PC0AE', 'Package_QFP:LQFP-32_7x7mm_P0.8mm', 'C2688383',
     MCU_PINS, (76.2, 185.42)),
    ('C5', 'Device:C', '100nF', FP_C, 'C14663', two('+5V', 'GND'), (127.0, 149.86)),
    ('C6', 'Device:C', '10uF', FP_C0805, 'C15850', two('+5V', 'GND'), (137.16, 149.86)),
    # 24 MHz kristal, 12 pF yük (YXC X322524MOB4SI); 1-3 kristal, 2-4 kılıf (GND)
    ('Y2', 'Device:Crystal_GND24', '24MHz', 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm', 'C70590',
     {'1': 'XIN', '3': 'XOUT', '2': 'GND', '4': 'GND'}, (127.0, 175.26)),
    ('C10', 'Device:C', '18pF', FP_C, 'C1647', two('XIN', 'GND'), (116.84, 187.96)),
    ('C11', 'Device:C', '18pF', FP_C, 'C1647', two('XOUT', 'GND'), (137.16, 187.96)),
    ('R8', 'Device:R', '1k', FP_R, 'C21190', two('+5V', 'LED2_A'), (157.48, 149.86)),
    ('LED2', 'Device:LED', 'L kırmızı', FP_LED, 'C2286', {'1': 'P1.2', '2': 'LED2_A'}, (157.48, 165.1)),
    ('SW2', 'Switch:SW_Push', 'USER', FP_SW, 'C318884', two('P3.0', 'GND'), (177.8, 149.86)),
    ('J2', 'Connector_Generic:Conn_01x10', 'P0', FP_HDR.format(10), 'C2337', P0_PINS, (208.28, 187.96)),
    ('J3', 'Connector_Generic:Conn_01x10', 'P1', FP_HDR.format(10), 'C2337', P1_PINS, (241.3, 187.96)),
    ('J4', 'Connector_Generic:Conn_01x10', 'P3', FP_HDR.format(10), 'C2337', P3_PINS, (274.32, 187.96)),
    ('J5', 'Connector_Generic:Conn_01x08', 'P2', FP_HDR.format(8), 'C2337', P2_PINS, (307.34, 185.42)),
]

# Varsayılan montajda takılmayan parçalar (şemada ve PCB'de DNP, dizgi dosyalarında yok)
TAKILMAZ = {'Y1', 'C8', 'C9'}

# ERC için güç kaynağı işaretleri (PWR_FLAG) konacak netler
POWER_FLAGS = [('GND', (25.4, 266.7)), ('+5V', (38.1, 266.7)), ('VBUS', (50.8, 266.7))]

# Blok başlıkları (şema üzerinde metin)
NOTES = [
    ((25.4, 25.4), '1. USB-C, sigorta, ESD, güç LED'),
    ((134.62, 25.4), '2. USB-UART (CH340C; ya da CH340G + Y1, C8, C9), UART seri dirençleri'),
    ((172.72, 88.9), 'Y1, C8, C9: yalnızca CH340G takılırsa'),
    ((241.3, 30.48), '3. Reset (DTR ile otomatik)'),
    ((322.58, 30.48), '4. ICP (Nu-Link): 100k pull-up, 100R seri'),
    ((25.4, 116.84), '5. MS51PC0AE, 24 MHz kristal (Y2), kullanıcı LED (P1.2/PWM) ve buton (P3.0/INT0), header\'lar'),
]
