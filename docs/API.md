# HTTP API

Base URL in AP mode: `http://192.168.4.1` (no auth; the device is a local AP).
AP 模式下地址为 `http://192.168.4.1`，接口无鉴权，仅建议在本地 AP 内使用。

所有响应都是 JSON，成功为 `{"ok": true, ...}`，失败为
`{"ok": false, "error": "..."}`，并带相应 HTTP 状态码（400/404/405/413/500）。
All responses are JSON. Errors use `ok:false` plus an HTTP error code.

强制门户：任何 `Host` 不是设备 IP（默认 `192.168.4.1`）的 HTTP 请求都会收到
`302 Location: http://192.168.4.1/`。请始终用 IP 访问 API。
Captive portal: requests whose `Host` is not the device IP get a 302 to the portal;
always address the API by IP.

Limits / 限制：请求头 ≤ 2 KB，JSON body ≤ 4 KB，Python 源码 ≤ 8 KB；socket 超时 2 s。

---

## Endpoints

| Method | Path | 说明 / Purpose |
|---|---|---|
| GET | `/api/state` | 设备信息 + 设置 + 运行态 / device, settings, runtime |
| GET | `/api/effects` | 15 个内置效果及参数元数据 / effect catalogue |
| GET | `/api/styles` | 自定义样式列表 / saved styles |
| GET | `/api/styles/<id>` | 读取样式 JSON / read style JSON |
| PUT | `/api/styles/<id>` | 新建或覆盖样式 / create or replace |
| DELETE | `/api/styles/<id>` | 删除样式及同名 `.py` / delete style + source |
| GET | `/api/styles/<id>.py` | 读取 Python 源码（text/plain） |
| PUT | `/api/styles/<id>.py` | 上传 Python 源码（text/plain） |
| POST | `/api/apply` | 立即应用效果 / apply a style now |
| POST | `/api/power` | 开/关灯 / power on/off |
| POST | `/api/brightness` | 全局亮度 0–255 |
| GET | `/api/settings` | 读取设置 / read settings |
| PUT | `/api/settings` | 部分更新设置 / partial update |
| POST | `/api/save-boot` | 设为开机默认 / save boot default |
| GET | `/api/colors` | 用户色板 / user palette |
| PUT | `/api/colors` | 覆盖用户色板 / replace palette |
| GET | `/api/log` | 最近 12 条日志 / recent logs |
| POST | `/api/reboot` | 重启（先返回响应）/ reboot |

Static files: `/` → `www/index.html`, `/app.css`, `/app.js`, `/favicon.ico` (204).

---

## GET /api/state

```json
{
  "ok": true,
  "device": {
    "platform": "esp32", "machine": "ESP32C3 module with ESP32C3",
    "ip": "192.168.4.1", "ssid": "ESP_WS2812B_BY_YYY",
    "chip_id": "a1b2c3d4e5f6", "version": "3.4.0; MicroPython ..."
  },
  "settings": {
    "schema": 1,
    "wifi": {"ssid": "ESP_WS2812B_BY_YYY", "password": "12345678"},
    "hardware": {"pins": [2], "leds": 30},
    "render": {"fps": 30, "brightness": 128, "max_leds": 1024, "color_order": "RGB"},
    "boot": {"mode": "preset", "style": "builtin:rainbow", "params": {},
             "brightness": 128, "power": true}
  },
  "runtime": {
    "power": true, "brightness": 128, "fps": 28, "fps_target": 30,
    "render_ms": 3, "leds": 30, "pins": [2], "max_leds": 1024,
    "heap": 84200, "uptime": 132,
    "style_id": "builtin:rainbow", "style_name": "彩虹", "style_type": "builtin",
    "style_params": {"speed": 0, "spread": 100, "reverse": false},
    "logs": ["..."]
  }
}
```

`runtime.style_id` 对内置效果是 `builtin:<effect>`，对保存的样式是文件 id。
For built-in effects the id is `builtin:<effect>`; for saved styles it is the file id.

---

## POST /api/apply

```json
{"style_id": "builtin:fire", "params": {"intensity": 80}}
```

- `style_id`：`builtin:<effect>` 或 `/styles/<id>` 的 id。
- `params` 可省略；只覆盖给出的键，其余用样式默认值。
- 重复应用同一内置效果时保留动画相位，适合拖动滑块实时调参。
- 成功返回 `{"ok":true,"style":{...},"runtime":{...}}`。

```bash
curl -s -X POST http://192.168.4.1/api/apply \
  -H 'Content-Type: application/json' \
  -d '{"style_id":"builtin:comet","params":{"color":"#00AAFF","speed":60}}'
```

---

## POST /api/power · /api/brightness

```bash
curl -X POST http://192.168.4.1/api/power -d '{"on":true}'
curl -X POST http://192.168.4.1/api/brightness -d '{"value":90}'
```

关闭电源只停止渲染并熄灭灯带；重新打开恢复上一个样式。
Power off stops rendering and blanks the strip; power on restores the last style.

---

## GET/PUT /api/settings

PUT 接受部分结构，深合并后校验：
PUT accepts a partial object, deep-merged then sanitised:

```json
{
  "hardware": {"leds": 60, "pins": [2, 4]},
  "render": {"fps": 25, "brightness": 150, "color_order": "GRB"},
  "wifi": {"ssid": "MyStrip", "password": "12345678"},
  "boot": {"mode": "off"}
}
```

- `hardware.leds` 立即生效（重建灯带对象）；上限 `render.max_leds`（默认 1024）。
- `hardware.pins` / `wifi` 变更返回 `"reboot_required": true`，重启后生效。
- `render.color_order`：`RGB`（默认）或 `RBG/GRB/GBR/BRG/BGR`；红绿互换时改成 `GRB`。
- 引脚最多 8 条，引脚号 0–48；灯珠缓冲区总量限制 64 KB。

---

## 样式接口 / Style endpoints

```bash
# 列表
curl -s http://192.168.4.1/api/styles

# 新建/覆盖（文件名即 id）
curl -X PUT http://192.168.4.1/api/styles/sunset \
  -H 'Content-Type: application/json' \
  --data-binary @sunset.json

# 读取、导出
curl -s http://192.168.4.1/api/styles/sunset

# Python 源码
curl -X PUT --data-binary @mystyle.py \
  http://192.168.4.1/api/styles/mystyle.py

# 删除（同时删除同名 .py）
curl -X DELETE http://192.168.4.1/api/styles/mystyle
```

- id 必须匹配 `^[a-z0-9][a-z0-9_-]{0,23}$`。
- JSON 样式在保存时会按 [style.schema.json](../firmware/esp32/style.schema.json) 的规则校验；
  未知 effect、非法颜色、超长名称会返回 400。
- `.py` 上传不会执行代码；只在应用/开机时才 `exec`。

---

## POST /api/save-boot

```json
{"style_id": "builtin:rainbow", "params": {"speed": 20},
 "brightness": 100, "power": true}
```

写入 `settings.boot`。下次上电使用该样式的参数（`params` 会存下来）。
Writes the boot preset; the device restores it on power-up.

---

## GET/PUT /api/colors

```json
{"ok": true, "colors": ["#ff6600", "#00aaff"]}
```

PUT 覆盖整个列表：`{"colors": [...]}`；最多 24 个，重复项自动去重，非法色值忽略。
PUT replaces the list; max 24 entries, duplicates removed, invalid values dropped.

---

## GET /api/log · POST /api/reboot

`/api/log` 返回 `{"ok":true,"logs":["..."]}`（最多 12 条，最新的在后面）。
自定义 Python 效果的异常会出现在这里。

`/api/reboot` 先返回 `{"ok":true,"rebooting":true}`，约 200 ms 后调用
`machine.reset()`；随后设备会断开约 3 秒。


---

作者 / Author: **洋洋柚**（B站/抖音 洋洋柚Y） · License: **CC BY-NC-SA 4.0**（禁止商用 / NonCommercial）

项目 / Project: [GitHub](https://github.com/YangYangyou-Zhang/esp_web_ws2812b_micropython) ·
[Gitee](https://gitee.com/zhangyangyangyou/esp_web_ws2812b_micropython) ·
[视频 / Video](https://www.bilibili.com/video/BV1zz5zzFEbM)
