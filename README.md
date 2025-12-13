# ELTEX SW-PLG01 FiWi Smart Plug

Eltex SW-PLG01 smart plug is using following chips:

- RTL8710C - controller chip.
- BL0937 - AC monitoring.
- LP2178 - non isolated DC power output.

After configuration reset (press button 6 times fast) listens on 56684/TCP and accepts configuration from mobile App.
Use `plgreg.py` to upload configuration manually.

## PINOUT:

Contains 6 conctac holes for UART console and programming. 1st conntact hole is near BL0937, last one is near the board side.

1. **3.3v**
1. **GND**
1. **RX** - UART RX 115200
1. **TX** - UART TX 115200
1. **GPIO_A0** - connect to **3.3v** to enable flashing mode
1. **CHIP_EN** - connect to **GND** to reset contoller.
   
![Eltex_SW-PLG01-pinout](https://github.com/user-attachments/assets/3a05f05e-b94a-467c-bb57-12f2a1eecc5e)

## Custom Firware

Tested with OpenRTL87X0C_1.18.226 firmware from [OpenBK7231T/OpenBeken](https://github.com/openshwprojects/OpenBK7231T_App). You can download [Original FirmWare](http://eltexhome.ru:80/api/v1/files/download/67f74506f2cacf07f5bf529d/SW-PLG_2.4.0-279_ota.bin) as well.

There are 2 options to flash custom firmware:

1. Use [ltchiptool](https://github.com/libretiny-eu/ltchiptool) (tested with version v4.12.2) to read and flash firware. OTA firmware is at offset 0xC000. This method require soldering and is more advanced.
2. Configure device using `plgreg.py` utility to connect to a MQTT broker. After device connected and published parameters you have to publish `device_upgrade` command using MQTT.
   * **Topic:** `sys/cmd/<node_id>`, for example `sys/cmd/6063d83b-f235-4f79-8c69-26a14cd7d003`
   * **Data:** `device_upgrade <node_id>|http://example.com/ota.img`, for example `device_upgrade cdfa91fc-d60a-4882-afc6-84e336faf778|http://example.com/OpenRTL87X0C_1.18.226_ota.img`

## OpenBeken module configuration

* Button, LED, Relay
  - GPIO_A4 - Rel
  - GPIO_A7 - LED_n
  - GPIO_A8 - BTN
* Power Monitoring: 
  - GPIO_A9 - BL0937.SEL
  - GPIO_A2 - BL0937.CF1
  - GPIO_A3 - BL0937.CF
