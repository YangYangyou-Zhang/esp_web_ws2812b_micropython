# AGENTS.md

Entry point for AI coding tools working on this repository.
For other AI tools that need to **generate LED styles**, read
[`firmware/esp32/style.schema.json`](firmware/esp32/style.schema.json) and
[`docs/STYLE_FORMAT.md`](docs/STYLE_FORMAT.md) first.

## What this project is

MicroPython firmware for ESP8266 / ESP32 / ESP32-C3 / ESP32-S3 that drives a
WS2812B strip and serves a self-contained web UI from `firmware/esp32/www/`.
The device is a WiFi AP; the browser talks to a minimal hand-written HTTP
server (`httpd.py`).

## Hard rules

1. **MicroPython compatibility.** Firmware code must run on MicroPython 1.19+
   (ESP8266 included): no `f-strings` assumptions beyond 1.17, no CPython-only
   stdlib, no `asyncio` in the main loop. Desktop-only code belongs in `tools/`.
2. **Never block the cooperative loop.** `engine.tick()` and `httpd.poll()` share
   one thread. Do not add `while True`, `sleep`, or long work to HTTP handlers,
   effects, or custom styles. Python styles are user code and cannot be preempted.
3. **Two firmwares, two RAM budgets.** The full firmware targets ESP32 / C3 / S3.
   `firmware/esp8266_lite/` is a separate, dependency-free build for stock ESP8266
   (~30 KB heap); keep its `main.py` around 8–9 KB of bytecode and do not import
   full-firmware modules into it. Both must stream web files from flash in
   small chunks — never read a whole asset into RAM.
4. **Styles are data.** Repo styles live in `firmware/esp32/styles/<id>.json`;
   on the device they are `/styles/<id>.json`, following
   `firmware/esp32/style.schema.json`. Python styles are the same JSON plus a
   sibling `.py` with `render(t, n, params, out, h)`. Never put executable code in JSON.
5. **Validate at the boundary.** All HTTP input is untrusted: check ids against
   `^[a-z0-9][a-z0-9_-]{0,23}$`, enforce body limits, clamp numbers, and only
   serve files from the static whitelist in `httpd.py`.
6. **Persist user state atomically.** `data/settings.json` and style files are
   written via temp file + `os.rename` (`settings.py`, `stylelib.py`).
7. **Never store secrets or server details in docs/assets.**

## Layout (flat modules, no packages)

| File | Responsibility |
|---|---|
| `firmware/esp32/main.py` | AP startup, RMT setup for C3, boot style, main loop |
| `firmware/esp32/settings.py` | `data/settings.json` load/sanitise/save |
| `firmware/esp32/engine.py` | non-blocking frame scheduler, brightness, output, watchdog |
| `firmware/esp32/effects.py` | 15 built-in effects + `EFFECT_META` parameter metadata |
| `firmware/esp32/stylelib.py` | style file validation/CRUD, Python source, user palette |
| `firmware/esp32/httpd.py` | HTTP parsing, static streaming, JSON API, captive-portal DNS + 302 |
| `firmware/esp32/www/` | vanilla HTML/CSS/JS UI (no build step, no CDN) |
| `firmware/esp32/styles/` | shipped example styles |
| `tools/sim.py` | CPython simulator with hardware stubs |
| `tools/gen_effects.py` | regenerate `firmware/esp32/www/effects.json` from effect metadata |
| `tools/build_single.py` | bundles modules + `www/` into `dist/main_single.py` |
| `tools/uitest.js` | headless Edge screenshots and layout checks |
| `tools/install.py` | mpremote upload helper |
| `firmware/esp8266_lite/main.py` | separate stripped-down ESP8266 firmware (do not import full-firmware modules); includes its own portal DNS |
| `firmware/esp8266_lite/lite.html` | lite single-file UI, served from flash |
| `tools/sim_lite.py` | CPython simulator for the lite build |
| `tools/lite_uitest.js` | headless checks for the lite UI |
| `legacy/` | old single-file scripts, do not modify |
| `VERSIONS.md` | version matrix and quick start for Full / Lite / Legacy |
| `LICENSE` / `NOTICE.md` | CC BY-NC-SA 4.0 text and the attribution / third-party notice (do not change without the author) |

All full-firmware modules live in `firmware/esp32/`.
Sibling imports are written as `from settings import SETTINGS`, etc., because
`tools/build_single.py` strips those lines and concatenates the modules in order
`settings → effects → stylelib → engine → httpd → main`. Keep module-level names
unique across these files.

## Adding an effect

1. Implement `_fx_name(ctx)` in `firmware/esp32/effects.py`; write directly with `ctx.set/fill`.
2. Add a `META['name']` entry with `name`, `desc`, `anim`, and parameter
   descriptors (`type`: `int|bool|color|colors|enum`, with `min/max/default`).
3. Register it in `_FX`. The web UI generates controls automatically — no
   frontend change required.
4. Add the effect id to the enum in `firmware/esp32/style.schema.json` and to the table in
   `docs/STYLE_FORMAT.md`.
5. Run `python tools/gen_effects.py` to refresh `firmware/esp32/www/effects.json`
   (served by `/api/effects`; there is a runtime fallback).
6. Test in `tools/sim.py`; check FPS on the status card.

## Adding an API endpoint

Add the route in `HttpServer._api` (`httpd.py`), return `{"ok": true, ...}`,
validate input, update `docs/API.md`. Keep responses small.

## Validation & tests

```bash
python -m py_compile firmware/esp32/*.py firmware/esp8266_lite/main.py
python tools/sim.py                  # full firmware, http://127.0.0.1:8000
python tools/sim_lite.py             # ESP8266 lite, http://127.0.0.1:8002
python tools/gen_effects.py          # refresh static effect metadata
python tools/build_single.py         # also compiles the bundle
node tools/uitest.js                 # full UI screenshots + console/overflow checks
node tools/lite_uitest.js            # lite UI checks
python -m json.tool firmware/esp32/styles/*.json
python -m mpy_cross firmware/esp8266_lite/main.py   # keep the .mpy small
nslookup example.com 192.168.4.1            # captive DNS -> device IP
curl -H 'Host: connectivitycheck.gstatic.com' http://192.168.4.1/generate_204  # expect 302
```

`mpy-cross` from the matching MicroPython version can be used for bytecode
verification when available.

## Style generation contract (for style-generating agents)

- One JSON object per file, `schema: 1`, `type: "builtin"` (preferred) or `"python"`.
- `effect` must be one of: `solid, gradient, breath, rainbow, rainbow_flow,
  chase, theater_chase, comet, sparkle, twinkle, fire, candle, wipe, scanner, strobe`.
- Colours: `#RRGGBB`; `colors` arrays have 1–8 entries.
- Integers stay inside documented ranges; unknown params are ignored.
- Python source: bounded O(n) `render()`, no sleeps/IO/infinite loops, reads params
  with `.get()`, ≤ 8 KB. See `docs/CUSTOM_EFFECTS.md`.
- The device validates on upload; `PUT /api/styles/<id>` is the canonical way to
  create a style, or copy files into `/styles/`.

## 中文摘要

- 固件必须兼容 MicroPython 1.19+，主循环是单线程合作式，任何地方都不能阻塞。
- 完整版模块都在 firmware/esp32/；ESP8266 用 firmware/esp8266_lite/。
- ESP8266 内存有限：网页资源从 flash 流式发送，效果避免大缓存和大量分配。
- 样式是数据：`firmware/esp32/styles/<id>.json`（设备上为 `/styles/<id>.json`）遵循
  `firmware/esp32/style.schema.json`；Python 样式额外有同名 `.py`，接口为
  `render(t, n, params, out, h)`。
- 新增效果只改 `firmware/esp32/effects.py`（实现 + META + 注册）并同步 Schema/文档，前端自动生成控件。
- 所有 HTTP 输入都要校验：文件 id、请求体大小、数值范围、静态文件白名单。
- 单文件构建靠剥离 `from settings/effects/... import` 后按顺序拼接，模块级命名不要冲突。


## Attribution / 许可

Author: **洋洋柚** (Bilibili / Douyin: 洋洋柚Y) — License: **CC BY-NC-SA 4.0** (NonCommercial).
Project: <https://github.com/YangYangyou-Zhang/esp_web_ws2812b_micropython> ·
<https://gitee.com/zhangyangyangyou/esp_web_ws2812b_micropython> ·
Video: <https://www.bilibili.com/video/BV1zz5zzFEbM>
