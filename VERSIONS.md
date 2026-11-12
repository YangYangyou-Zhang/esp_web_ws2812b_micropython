# 版本与使用方法 / Versions & Quick Start

本仓库有三个可烧录版本，按芯片选择。三个版本共用同一套粉蓝 UI 和强制门户。
This repository contains three firmware variants; pick one by chip.

| 版本 | 适用芯片 | 源码目录 | 主要能力 | 安装 |
|---|---|---|---|---|
| **完整版 Full** | ESP32 / ESP32-C3 / ESP32-S3 | [`firmware/esp32/`](firmware/esp32) | 15 个效果、样式保存/导入导出、Python 自定义效果、15+ 参数元数据、强制门户 | `python tools/install.py COM5` |
| **ESP8266 Lite** | ESP8266（4 MB flash） | [`firmware/esp8266_lite/`](firmware/esp8266_lite) | 6 个效果、取色器、亮度/电源、LED 数/引脚/开机效果、强制门户 | `python tools/install.py COM5 --lite --reset` |
| **Legacy** | ESP8266 / ESP32（旧版） | [`legacy/`](legacy) | 旧版单文件脚本，仅保留参考 | 手动上传为 `main.py` |

单文件版：`python tools/build_single.py` → `dist/main_single.py`（仅完整版，ESP32 系列）。

---

## 1. 完整版（ESP32 / C3 / S3）

源码在 [`firmware/esp32/`](firmware/esp32)：

```
main.py  settings.py  engine.py  effects.py  stylelib.py  httpd.py
www/     styles/      configs/    style.schema.json
```

### 安装

1. 先给开发板刷入 **普通 ESP32 / C3 / S3 的 MicroPython 固件**（不要刷 SPIRAM 版到无 PSRAM 的普通 ESP32）。
2. 在项目根目录执行：

   ```bash
   pip install mpremote
   python tools/install.py COM5          # Windows
   python tools/install.py /dev/ttyACM0  # Linux / macOS
   ```

   脚本会从 `firmware/esp32/` 上传模块、`www/` 和 `styles/` 到设备根目录。
   也可以按 [README](README.md) 里的手动 mpremote 命令操作。

3. 按 RST 重启。连接 WiFi `ESP_WS2812B_BY_YYY`，密码 `12345678`，打开
   <http://192.168.4.1>。手机通常会自动弹出登录页（强制门户）。

普通 ESP32 建议 30–60 颗灯；100 颗以上优先 C3/S3（实测数据见 [README](README.md#性能参考实测会因固件版本布线不同而变化)）。

### 单文件版

```bash
python tools/build_single.py
```

把 `dist/main_single.py` 上传为设备的 `main.py`。首次启动会把网页和示例样式写入 flash。
仅建议 ESP32 系列；ESP8266 不要用这个包。

### 改配置

首次启动生成 `data/settings.json`。示例见
[`firmware/esp32/configs/`](firmware/esp32/configs)：复制成 `data/settings.json` 上传即可。
改引脚/AP 需要重启，改 LED 数立即生效。

---

## 2. ESP8266 Lite

源码在 [`firmware/esp8266_lite/`](firmware/esp8266_lite)：

```
main.py  lite.html
```

只支持一条灯带、6 个效果、无 JSON 样式/自定义 Python；为 ESP8266 约 30 KB 堆设计。
详细说明见 [`firmware/esp8266_lite/README.md`](firmware/esp8266_lite/README.md)。

### 安装

1. 先刷入 **ESP8266 的 MicroPython 固件**（4 MB flash，普通版）。
2. 在项目根目录执行：

   ```bash
   python tools/install.py COM5 --lite --reset
   ```

   或手动：

   ```bash
   mpremote connect COM5 fs cp firmware/esp8266_lite/main.py :main.py
   mpremote connect COM5 fs cp firmware/esp8266_lite/lite.html :lite.html
   mpremote connect COM5 reset
   ```

3. 连接热点 `ESP_WS2812B_BY_YYY`（密码 `12345678`），打开 <http://192.168.4.1>。

配置文件是设备上的 `lite.cfg`（首次启动自动生成），适合手工修改 LED 数/引脚/开机效果。

---

## 3. Legacy（旧版单文件）

[`legacy/`](legacy) 保留最初的三个单文件脚本：

- `esp8266.py`、`esp8266_75_4.py`：ESP8266 / ESP32 / C3 的旧版（无 PSRAM 也能跑，但只有呼吸灯）
- `esp32c3_75_4.py`：ESP32-C3 旧版

直接上传任意一个为设备的 `main.py` 即可。旧版没有强制门户、样式系统和现代 UI；
新项目请用上面的完整版或 Lite。

---

## 通用信息

- **AP**：SSID `ESP_WS2812B_BY_YYY`，密码 `12345678`，地址 `192.168.4.1`
- **强制门户**：连接后系统通常会自动弹出控制页；未弹出就手动打开 IP。安卓建议关闭移动数据。
- **接线**：灯带 5V/GND 独立供电并与开发板共地，DIN 默认接 GPIO2。
- **作者**：洋洋柚（B站/抖音 洋洋柚Y）
- **许可**：CC BY-NC-SA 4.0，允许个人 DIY/学习/非商业分享，**禁止商用（含售卖套件）**。
  见 [LICENSE](LICENSE) 与 [NOTICE.md](NOTICE.md)。
- **项目**：[GitHub](https://github.com/YangYangyou-Zhang/esp_web_ws2812b_micropython) ·
  [Gitee](https://gitee.com/zhangyangyangyou/esp_web_ws2812b_micropython) ·
  [视频](https://www.bilibili.com/video/BV1zz5zzFEbM)

---

## English summary

| Variant | Chip | Source | Install |
|---|---|---|---|
| Full | ESP32 / C3 / S3 | `firmware/esp32/` | `python tools/install.py COM5` |
| ESP8266 Lite | ESP8266 (4 MB) | `firmware/esp8266_lite/` | `python tools/install.py COM5 --lite --reset` |
| Legacy | ESP8266 / ESP32 | `legacy/` | upload one script as `main.py` |

Full firmware needs a plain MicroPython build for your chip (do **not** flash the SPIRAM
build to a plain ESP32 without PSRAM). After uploading, join `ESP_WS2812B_BY_YYY`
(password `12345678`) and open <http://192.168.4.1>. The captive portal usually opens
the page automatically. See the Chinese sections above and [README](README.md) for details.
