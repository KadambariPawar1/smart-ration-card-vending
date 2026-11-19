# Pin Connections — Raspberry Pi Zero 2 W

## R307S Fingerprint Sensor (UART0)

| R307S | Raspberry Pi |
|---|---|
| VCC | 5V (Pin 4) |
| GND | GND (Pin 6) |
| TX (Yellow) | GPIO15 (Pin 10 — RXD0) |
| RX (Green) | GPIO14 (Pin 8 — TXD0) |

- TX ↔ RX crossed
- Serial console disabled on the Pi (required for UART0 access)

## LCD 16x2 (I2C)

| LCD I2C | Raspberry Pi |
|---|---|
| VCC | 5V (Pin 2) |
| GND | GND (Pin 9) |
| SDA | GPIO2 (Pin 3) |
| SCL | GPIO3 (Pin 5) |

## RTC DS1307 (shares I2C bus with LCD)

| RTC | Raspberry Pi |
|---|---|
| VCC | 5V (Pin 4) |
| GND | GND (Pin 20) |
| SDA | GPIO2 (shared) |
| SCL | GPIO3 (shared) |

## HX711 Load Cell Amp — Wheat

| HX711 (Wheat) | Raspberry Pi |
|---|---|
| VCC | 5V (Pin 4) |
| GND | GND (Pin 25) |
| DT | GPIO16 (Pin 36) |
| SCK | GPIO6 (Pin 31) |

## HX711 Load Cell Amp — Rice

| HX711 (Rice) | Raspberry Pi |
|---|---|
| VCC | 5V (Pin 4) |
| GND | GND (Pin 34) |
| DT | GPIO13 (Pin 33) |
| SCK | GPIO19 (Pin 35) |

## Servo Motors (external 5V supply recommended)

| Wheat Servo | Raspberry Pi |
|---|---|
| VCC | External 5V supply |
| GND | Shared GND with external supply |
| Signal | GPIO18 (Pin 12) |

| Rice Servo | Raspberry Pi |
|---|---|
| VCC | External 5V supply |
| GND | Shared GND with external supply |
| Signal | GPIO12 (Pin 32) |

## 4x4 Keypad

**Rows**

| Row | Raspberry Pi |
|---|---|
| R1 | GPIO17 (Pin 11) |
| R2 | GPIO27 (Pin 13) |
| R3 | GPIO22 (Pin 15) |
| R4 | GPIO23 (Pin 16) |

**Columns**

| Column | Raspberry Pi |
|---|---|
| C1 | GPIO24 (Pin 18) |
| C2 | GPIO25 (Pin 22) |
| C3 | GPIO8 (Pin 24) |
| C4 | GPIO7 (Pin 26) |

## Shutdown Push Button

| Button | Raspberry Pi |
|---|---|
| One side | GPIO21 (Pin 40) |
| Other side | GND |

## EM-18 RFID Reader & SIM800L GSM (USB-UART adapters)

Both modules are connected via external USB-to-UART adapters rather than the Pi's onboard UART, since that's already used by the fingerprint sensor.

| Device | Port |
|---|---|
| EM-18 RFID | `/dev/ttyUSB0` |
| SIM800L GSM | `/dev/ttyUSB1` |

**EM-18 → USB-UART adapter #1** (powered from the Pi)

| EM-18 | Connection |
|---|---|
| VCC | Pi 5V (Pin 2 or 4) |
| GND | Pi GND |
| TX | USB-UART RXD |
| RX | USB-UART TXD (optional) |

**SIM800L → USB-UART adapter #2** (powered via LM2596 buck converter set to ~4.0V — SIM800L draws current spikes up to 2A during transmission, so it should **not** be powered directly from the Pi)

| SIM800L | Connection |
|---|---|
| VCC | LM2596 OUT+ (4V) |
| GND | LM2596 OUT- |
| TX | USB-UART RXD |
| RX | USB-UART TXD |

## Full GPIO Map (no pin conflicts)

| Component | GPIO |
|---|---|
| I2C (LCD + RTC) | 2, 3 |
| Fingerprint (UART0) | 14, 15 |
| Keypad | 17, 27, 22, 23, 24, 25, 8, 7 |
| HX711 (Wheat + Rice) | 16, 6, 13, 19 |
| Servos | 18, 12 |
| Shutdown button | 21 |

> RFID and GSM don't use dedicated Pi GPIO/UART pins — they connect through external USB-UART adapters.
