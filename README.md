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
![1765650117166](https://github.com/user-attachments/assets/7be6bf83-5488-4938-bb40-6b297184d881)

## Custom Firware

Tested with OpenRTL87X0C_1.18.313 firmware from [OpenBK7231T/OpenBeken](https://github.com/openshwprojects/OpenBK7231T_App). You can download [Original FirmWare](http://eltexhome.ru:80/api/v1/files/download/67f74506f2cacf07f5bf529d/SW-PLG_2.4.0-279_ota.bin) as well.

There are 2 options to flash custom firmware:

1. Use [ltchiptool](https://github.com/libretiny-eu/ltchiptool) (tested with version v4.12.2) to read and flash firware. Select AmebaZ2 chip family. OTA firmware offset is 0xC000. This method requires soldering and is more advanced.
2. Configure device using `plgreg.py` utility to connect to a MQTT broker. After device connected and published parameters you have to publish `device_upgrade` command using MQTT. Device will download and flash OTA firmware.
   * *optional* Download the latest firmware version from the [OpenBeken repository](https://github.com/openshwprojects/OpenBK7231T_App/releases) `OpenRTL87X0C_1.xx.xxx_ota.img`, and rename the firmware file to `SW-PLG0X_2.5.0-298_ota.img`.
   * **Run python script to connect the smart plug to the MQTT broker:** `python plgreg.py --ssid MySSID --password MyPassword --mqtt-broker 192.168.100.60:1883 --mqtt-login mqttdevice --mqtt-password mqttdevice_pass --node-id swplg01_01 --host 10.24.83.55`
   * **Execute the update command via MQTT:** MQTT -> Topic: `sys/cmd/swplg01_01` -> Data: `device_upgrade swplg01_01|https://github.com/baiandin/eltex_sw_plg01/blob/main/fw/SW-PLG0X_2.5.0-298_ota.img`

   You can also configure sys_log:
   * `syslog_server.py`
   * **Start:** MQTT -> Topic: `sys/cmd/swplg01_01` -> Data: `sys_log 192.168.0.31:514`
   * **Stop:** MQTT -> Topic: `sys/cmd/swplg01_01` -> Data: `sys_log stop`

## OpenBeken module configuration

* Button, LED, Relay
  - PA4 - Rel
  - PA7 - LED_n
  - PA8 - BTN
* Power Monitoring: 
  - PA9 - BL0937.SEL
  - PA2 - BL0937.CF1
  - PA3 - BL0937.CF
