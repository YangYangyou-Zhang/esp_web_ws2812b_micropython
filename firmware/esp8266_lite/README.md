# ESP8266 Lite

给库存 ESP8266（4 MB flash）用的极简版本。完整版固件需要 ESP32 系列；
ESP8266 内存放不下完整版，所以这里只保留核心功能。
A stripped-down build for stock ESP8266 boards. The full firmware targets
ESP32; this one fits the ESP8266 heap.

## 功能 / Features

- AP 网页控制，手机/电脑自适应；粉蓝渐变 UI，与完整版同一视觉。
- 内置取色器：预设色、自定义色、HEX 输入、收藏色（存浏览器 localStorage）。
- 亮度 0–255、电源开关、6 个效果：
  `solid` 纯色 / `breath` 呼吸 / `rainbow` 彩虹 / `chase` 追逐 / `comet` 彗星 / `fire` 火焰。
- LED 数量、数据引脚、开机效果可在网页修改并保存到 `lite.cfg`。
- 非阻塞主循环：动画和 HTTP 同时工作；实测 socket 超时坑已规避。
- 连接后自动弹出控制页（Captive Portal：DNS 劫持 + 302）。
- 无 JSON 解析、无样式文件系统、无自定义 Python 效果——为了省 RAM。

## 安装 / Install

只需要两个文件：`main.py` 和 `lite.html`（源码在 `firmware/esp8266_lite/`）。

```bash
pip install mpremote
python tools/install.py COM5 --lite --reset
```

等价的手动命令：

```bash
mpremote connect COM5 fs cp firmware/esp8266_lite/main.py :main.py
mpremote connect COM5 fs cp firmware/esp8266_lite/lite.html :lite.html
mpremote connect COM5 reset
```

用 Thonny 也可以：把 `main.py` 和 `lite.html` 拖到设备根目录，然后按 RST。

首次启动会生成 `lite.cfg`：

```ini
leds=30
pin=2
bright=128
boot=rainbow
color=ff6600
speed=40
```

## 使用 / Usage

1. 连接 Wi-Fi `ESP_WS2812B_BY_YYY`，密码 `12345678`。
2. 浏览器打开 <http://192.168.4.1>。
3. 默认 30 颗灯、GPIO2、开机彩虹。

改 SSID/密码：编辑 `main.py` 顶部的 `SSID` / `PASSWORD` 后重新上传。

## 强制门户 / Captive portal

和完整版一样内置：

- UDP 53 上把所有 DNS 查询解析成 AP 的 IP（`PORTAL_IP`，默认 192.168.4.1）。
- HTTP 请求的 `Host` 不是 `PORTAL_IP` 时，返回 `302 Location: http://<AP-IP>/`。
- 手机/电脑连上后系统探测 `connectivitycheck.gstatic.com`、`captive.apple.com`、
  `msftconnecttest.com` 等地址，被 302 到控制页，于是弹出「登录网络」。
- 自动弹出取决于系统：安卓关掉移动数据更可靠；iOS 可能提示无互联网，继续使用即可；
  部分 ROM 需要手动打开 <http://192.168.4.1>。
- 不想用：注释 `start_http()` 里的 `start_dns()`，以及 `handle()` 开头的 Host 判断。
- 如果 ESP8266 的 DHCP 没把 DNS 指向自己（少数固件），手机端手动把 DNS 设为 AP IP。

## HTTP 接口 / API

轻量版刻意使用 GET 查询参数，避免 JSON 解析和请求体缓冲。

| 请求 | 说明 |
|---|---|
| `GET /api/state` | 电源、亮度、LED 数、引脚、效果、速度、颜色、FPS、内存 |
| `GET /api/apply?effect=rainbow&speed=40&color=ff6600` | 应用效果（自动开灯） |
| `GET /api/power?on=1` / `?on=0` | 开/关 |
| `GET /api/bright?value=128` | 亮度，并按当前值保存 |
| `GET /api/save?leds=60&pin=2&boot=breath&bright=128&color=ff6600&speed=40` | 保存设置；LED 数/引脚立即生效，`boot` 下次启动生效 |
| `GET /api/reboot` | 重启 |

`/api/state` 示例：

```json
{"ok":1,"power":1,"bright":128,"leds":30,"pin":2,
 "effect":"rainbow","speed":40,"color":"ff6600","boot":"rainbow",
 "fps":29,"ms":8,"heap":22800,"uptime":12}
```

## 限制 / Limits

- 单条灯带，最多 300 颗（建议 30–100；内存和帧率都更稳）。
- 只有 6 个效果；没有 JSON 样式、没有多灯带、没有自定义 Python。
- `lite.cfg` 直接写入 flash；亮度滑块在网页端做了 400 ms 防抖。
- 自定义 Python 效果/样式请使用 ESP32 完整版。

## 性能 / Performance

- 渲染目标 30 FPS；ESP8266 @80 MHz 上 30 颗灯通常够用，灯数越多帧率越低。
- 状态面板显示实测 FPS、单帧耗时、剩余内存。
- 如果帧率不足：降低灯数、或用 `solid`/`breath`（单色填充最快）。

## 测试状态 / Test status

- `mpy-cross` 编译产物约 **8.2 KB**（含强制门户 DNS），为 ESP8266 堆预留了空间。
- 用 `tools/sim_lite.py` 在 CPython 上完整跑通 UI/API（含取色器、设置保存、LED 热重建）。
- **尚未在真实 ESP8266 上烧录验证**；烧录后请检查：
  1. AP 是否为 WPA2（不是开放网络）；
  2. 手机/电脑打开页面的布局；
  3. 亮度/电源/6 个效果；
  4. 改 LED 数/引脚后立即生效；
  5. 改开机效果后重启仍生效；
  6. 状态面板的 FPS 与内存。

## 修改 / Customize

- 后端：`main.py` 的 `render()`、`EFFECTS`、`DEFAULTS`。
- 前端：`lite.html` 内的 CSS/JS；效果卡片在 `FX` 对象里。
- 颜色顺序：轻量版固定按 RGB 发送；若红绿互换，可把 `render()` 里的
  `np[i] = (r,g,b)` 改成 `(g,r,b)`（或在 `scale()` 里交换通道）。


---

作者 / Author: **洋洋柚**（B站/抖音 洋洋柚Y） · License: **CC BY-NC-SA 4.0**（禁止商用 / NonCommercial）

项目 / Project: [GitHub](https://github.com/YangYangyou-Zhang/esp_web_ws2812b_micropython) ·
[Gitee](https://gitee.com/zhangyangyangyou/esp_web_ws2812b_micropython) ·
[视频 / Video](https://www.bilibili.com/video/BV1zz5zzFEbM)
