"""STC12C5A60S2 geliştirme kartı (Rev A): parça ve bağlantı tanımı.

Tek kaynak budur. kicad_uret.py bu dosyadan KiCad şemasını üretir; ../BOM.csv
ve ../baglanti-listesi.md ile birebir aynı devreyi tarif eder.

Her parça: (ref, lib_id, değer, footprint, LCSC, {pin numarası: net}, (x, y) mm)
Haritada olmayan pinler şemada "bağlantısız" (no-connect) işaretlenir.
"""

FP_R = 'Resistor_SMD:R_0603_1608Metric'
FP_C = 'Capacitor_SMD:C_0603_1608Metric'
FP_C0805 = 'Capacitor_SMD:C_0805_2012Metric'
FP_LED = 'LED_SMD:LED_0603_1608Metric'
FP_SW = 'Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A'
FP_SOT23 = 'Package_TO_SOT_SMD:SOT-23'


def two(a, b):
    return {'1': a, '2': b}


# STC12C5A60S2 (klasik 8051 DIP-40 pin dizilimi). Standart 8051'den farkları:
# P1.0-P1.7 = ADC0-7, P1.3/P1.4 = CCP0/CCP1 (PWM), pin 29/30 = P4.4/P4.5 (PSEN/ALE yerine),
# pin 31 = P4.6/EX_LVD (EA yerine; VCC'de tutulur, düşük voltaj eşiğinin üstünde kalır)
MCU_PINS = {str(i + 1): f'P1.{i}' for i in range(8)}
MCU_PINS.update({
    '9': 'RST', '10': 'MCU_RXD', '11': 'MCU_TXD',
    '12': 'P3.2', '13': 'P3.3', '14': 'P3.4', '15': 'P3.5', '16': 'P3.6', '17': 'P3.7',
    '18': 'XTAL2', '19': 'XTAL1', '20': 'GND',
    '29': 'P4.4', '30': 'P4.5', '31': 'VCC_MCU', '40': 'VCC_MCU',
})
MCU_PINS.update({str(21 + i): f'P2.{i}' for i in range(8)})
MCU_PINS.update({str(39 - i): f'P0.{i}' for i in range(8)})


def header(port):
    pins = {str(k + 1): f'{port}.{k}' for k in range(8)}
    pins.update({'9': 'VCC_MCU', '10': 'GND'})
    if port == 'P3':
        pins.update({'1': 'MCU_RXD', '2': 'MCU_TXD'})  # P3.0/P3.1 USB-UART ile ortak
    return pins


# USB-C 16P: GND A1/A12/B1/B12, VBUS A4/A9/B4/B9, CC A5/B5, D+ A6/B6, D- A7/B7, SBU A8/B8, kalkan S1
USBC_PINS = {
    'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'S1': 'GND',
    'A4': 'VBUS', 'A9': 'VBUS', 'B4': 'VBUS', 'B9': 'VBUS',
    'A5': 'CC1', 'B5': 'CC2',
    'A6': 'USB_DP', 'B6': 'USB_DP', 'A7': 'USB_DM', 'B7': 'USB_DM',
}

PARTS = [
    # --- 1. USB ve güç (sol üst)
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

    # --- 2. CH340C (orta üst)
    ('U2', 'Interface_USB:CH340C', 'CH340C', 'Package_SO:SOIC-16_3.9x9.9mm_P1.27mm', 'C84681',
     {'1': 'GND', '2': 'CH_TXD', '3': 'CH_RXD', '4': 'CH_V3', '5': 'USB_DP', '6': 'USB_DM',
      '13': 'DTR_N', '14': 'RTS_N', '16': '+5V'}, (165.1, 63.5)),
    ('C3', 'Device:C', '100nF', FP_C, 'C14663', two('+5V', 'GND'), (139.7, 88.9)),
    ('C4', 'Device:C', '100nF', FP_C, 'C14663', two('CH_V3', 'GND'), (147.32, 88.9)),

    # --- 3. UART ara bağlantısı (sağ üst)
    ('D1', 'Device:D_Schottky', 'B5819W', 'Diode_SMD:D_SOD-123', 'C8598',
     {'1': 'CH_TXD', '2': 'MCU_RXD'}, (210.82, 45.72)),
    ('R4', 'Device:R', '4.7k', FP_R, 'C23162', two('VCC_MCU', 'MCU_RXD'), (226.06, 40.64)),
    ('R5', 'Device:R', '1k', FP_R, 'C21190', two('MCU_TXD', 'CH_RXD'), (210.82, 63.5)),

    # --- 4. Otomatik ISP güç kesici (sağ üst)
    ('Q1', 'Transistor_FET:AO3401A', 'AO3401A', FP_SOT23, 'C15127',
     {'1': 'Q1_G', '2': '+5V', '3': 'VCC_MCU'}, (281.94, 45.72)),
    ('R6', 'Device:R', '10k', FP_R, 'C25804', two('+5V', 'Q1_G'), (264.16, 45.72)),
    ('Q2', 'Transistor_FET:2N7002', '2N7002', FP_SOT23, 'C8545',
     {'1': 'ISP_N', '2': 'GND', '3': 'Q1_G'}, (281.94, 71.12)),
    ('R7', 'Device:R', '10k', FP_R, 'C25804', two('+5V', 'ISP_N'), (251.46, 63.5)),
    ('Q3', 'Transistor_BJT:MMBT3904', 'MMBT3904', FP_SOT23, 'C20526',
     {'1': 'Q3_B', '2': 'DTR_N', '3': 'ISP_N'}, (264.16, 88.9)),
    ('R8', 'Device:R', '10k', FP_R, 'C25804', two('RTS_N', 'Q3_B'), (246.38, 88.9)),
    ('SW1', 'Switch:SW_Push', 'ISP', FP_SW, 'C318884', two('ISP_N', 'GND'), (299.72, 71.12)),
    ('R9', 'Device:R', '4.7k', FP_R, 'C23162', two('VCC_MCU', 'GND'), (320.04, 45.72)),
    ('R10', 'Device:R', '1k', FP_R, 'C21190', two('VCC_MCU', 'LED2_A'), (335.28, 45.72)),
    ('LED2', 'Device:LED', 'MCU sarı', FP_LED, 'C72038', {'1': 'GND', '2': 'LED2_A'}, (350.52, 45.72)),

    # --- 5. MCU ve çevresi (alt yarı)
    ('U1', 'MCU_Microchip_8051:AT89x51xxP', 'STC12C5A60S2-35I', 'Package_DIP:DIP-40_W15.24mm_Socket', 'C14550',
     MCU_PINS, (63.5, 190.5)),
    ('Y1', 'Device:Crystal', '11.0592MHz', 'Crystal:Crystal_HC49-4H_Vertical', 'C2203',
     two('XTAL1', 'XTAL2'), (127.0, 139.7)),
    ('C7', 'Device:C', '33pF', FP_C, 'C1663', two('XTAL1', 'GND'), (119.38, 152.4)),
    ('C8', 'Device:C', '33pF', FP_C, 'C1663', two('XTAL2', 'GND'), (134.62, 152.4)),
    ('C9', 'Device:C', '10uF', FP_C0805, 'C15850', two('VCC_MCU', 'RST'), (157.48, 139.7)),
    ('R11', 'Device:R', '10k', FP_R, 'C25804', two('RST', 'GND'), (157.48, 157.48)),
    ('SW2', 'Switch:SW_Push', 'RESET', FP_SW, 'C318884', two('VCC_MCU', 'RST_SW'), (175.26, 134.62)),
    ('R12', 'Device:R', '1k', FP_R, 'C21190', two('RST_SW', 'RST'), (175.26, 152.4)),
    ('C5', 'Device:C', '100nF', FP_C, 'C14663', two('VCC_MCU', 'GND'), (198.12, 139.7)),
    ('C6', 'Device:C', '10uF', FP_C0805, 'C15850', two('VCC_MCU', 'GND'), (205.74, 139.7)),
    ('R13', 'Device:R', '1k', FP_R, 'C21190', two('VCC_MCU', 'LED3_A'), (226.06, 139.7)),
    ('LED3', 'Device:LED', 'L kırmızı', FP_LED, 'C2286', {'1': 'P1.7', '2': 'LED3_A'}, (226.06, 154.94)),
    ('SW3', 'Switch:SW_Push', 'USER', FP_SW, 'C318884', two('P3.2', 'GND'), (246.38, 139.7)),
    ('RN1', 'Device:R_Network08', '10k', 'Resistor_THT:R_Array_SIP9', 'C8692',
     {'1': 'VCC_MCU', **{str(i + 2): f'P0.{i}' for i in range(8)}}, (139.7, 205.74)),
    ('J2', 'Connector_Generic:Conn_01x10', 'P1', 'Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical',
     'C2337', header('P1'), (203.2, 190.5)),
    ('J3', 'Connector_Generic:Conn_01x10', 'P0', 'Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical',
     'C2337', header('P0'), (236.22, 190.5)),
    ('J4', 'Connector_Generic:Conn_01x10', 'P2', 'Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical',
     'C2337', header('P2'), (269.24, 190.5)),
    ('J5', 'Connector_Generic:Conn_01x10', 'P3', 'Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical',
     'C2337', header('P3'), (302.26, 190.5)),
    ('J6', 'Connector_Generic:Conn_01x03', 'RST/P4.5/P4.4', 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
     'C2337', {'1': 'RST', '2': 'P4.5', '3': 'P4.4'}, (335.28, 177.8)),
]

# ERC için güç kaynağı işaretleri (PWR_FLAG) konacak netler
POWER_FLAGS = [('GND', (25.4, 266.7)), ('+5V', (38.1, 266.7)), ('VCC_MCU', (50.8, 266.7)), ('VBUS', (63.5, 266.7))]

# Blok başlıkları (şema üzerinde metin)
NOTES = [
    ((25.4, 25.4), '1. USB-C, sigorta, ESD, güç LED'),
    ((134.62, 25.4), '2. USB-UART (CH340C)'),
    ((200.66, 25.4), '3. UART ara bağlantısı (D1: MCU kapalıyken geri beslemeyi engeller)'),
    ((243.84, 30.48), '4. Otomatik ISP: DTR aktif + RTS pasif -> VCC_MCU kapanır. SW1 = elle ISP'),
    ((25.4, 116.84), '5. STC12C5A60S2 (P1 = ADC0-7, P1.3/P1.4 = PWM), kristal, reset, P0 pull-up, kullanıcı LED/buton, header\'lar'),
]
