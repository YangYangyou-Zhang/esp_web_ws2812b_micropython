# esp_web_ws2812b_micropython

#### 介绍
基于micropython固件esp平台利用wifi打开网页控制ws2812b可编程灯带的开源项目

An open-source project based on the Micropython firmware ESP platform, utilizing WiFi to open web pages and control the WS2812b programmable LED strip

#### 软件架构
在esp8266 esp32 esp32s3芯片组，直接使用esp8266_xxxx.py代码即可，esp32c3芯片组必须使用esp32c3_xxxx.py代码或者手动添加RMT通道。

On the ESP8266 ESP32 ESP32S3 chipset, simply use the ESP8266_ xxxx.py code, while the ESP32c3 chipset must use the ESP32c3_ xxxx.py code or manually add RMT channels.

#### 其他资料相关 
micropython官网下载https://micropython.org/download/ 
esp芯片下载方法https://docs.espressif.com/projects/esp-test-tools/zh_CN/latest/esp32/production_stage/tools/flash_download_tool.html


#### 安装教程
﻿
1.  给esp芯片组安装micropython固件
2.  给ws2812b灯带接入5v供电和gnd连接，将信号输入引脚连接到开发板任意引脚，例如此处是GPIO2上（pin1变量名字）（演示视频是接在GPIO9上）
3.  使用thonnyIDE下载程序到开发板内并且重命名为main.py

####Installation tutorial
1. Install micropython firmware for ESP chipset
2. Connect the WS2812b LED strip to 5V power supply and GND connection, and connect the signal input pin to any pin on the development board, such as GPO2 (pin1 variable name) (the demonstration video is connected to GPO9)
3. Use Python IDE to download the program to the development board and rename it to main. py

﻿
#### 使用说明
﻿
1.  接通电源，按下rst按钮重启开发板，打开手机或者电脑wifi，找到设置的wifi名称并且连接（默认名称是“ESP_WS2812B_BY_YYY”，默认密码是“12345678”）
2.  关闭手机流量，保持连接当前WiFi，打开浏览器并且转到网址http://192.168.4.1
3.  在颜色选择框选择颜色即可，按下呼吸灯按钮即可一键以当前颜色为主体开始呼吸灯不断变换亮度。

####Instructions for use
1. Turn on the power, press the RST button to restart the development board, turn on the phone or computer WiFi, find the set WiFi name and connect (default name is "ESP_SS2812B_BY_YYY", default password is "12345678")
2. Turn off mobile data, keep connected to the current WiFi, open a browser and go to the website http://192.168.4.1
3. Select a color in the color selection box and press the breathing light button to start the breathing light continuously changing brightness with the current color as the main body.
﻿
#### 特技
﻿
在esp32c3平台使用ws2812b的neopixel库控制时会报错
Traceback (most recent call last):
File "<stdin>", line ...
File "neopixel.py", line 1, in write
OSError: (-258, 'ESP_ERR_INVALID_ARG')
在代码前计入手动配置 RMT 通道即可

```
﻿
import esp32
﻿
esp32.RMT.bitstream_channel(0)
﻿
```


####Special skills
When using the ws2812b neopixel library control on the ESP32C3 platform, an error will occur
Traceback (most recent call last):
File "<stdin>", line ...
File "neopixel.py", line 1, in write
OSError: (-258, 'ESP_ERR_INVALID_ARG')
Just include manual configuration of RMT channel before code
