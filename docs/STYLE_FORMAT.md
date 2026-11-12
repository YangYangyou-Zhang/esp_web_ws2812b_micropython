# 样式格式 / Style format

Style files live in `/styles` on the device and can be created in three ways:
on the web UI, by copying a JSON file with Thonny/mpremote, or through the HTTP API.
样式文件保存在设备 `/styles` 目录，可通过网页、Thonny/mpremote 复制、或 HTTP API 创建。

Machine-readable schema: [`style.schema.json`](../firmware/esp32/style.schema.json)
机器可读 Schema：[`style.schema.json`](../firmware/esp32/style.schema.json)

---

## 1. 文件与命名 / Files and names

- 一个样式 = 一个 JSON 文件：`/styles/<id>.json`。
- `<id>` 只能包含 `a-z 0-9 _ -`，长度 1–24，例如 `sunset`、`my-style_2`。
- Python 样式还需要同名源码文件：`/styles/<id>.py`，并在 JSON 中写 `"module": "<id>"`。
- JSON 上限 4 KB，Python 源码上限 8 KB。
- 文件名即样式 id；上传接口会校验，非法名字返回 400。

---

## 2. JSON 结构 / JSON structure

```json
{
  "schema": 1,
  "name": "日落 Sunset",
  "type": "builtin",
  "effect": "gradient",
  "params": {
    "colors": ["#FF6B35", "#F7C59F", "#7C3AED"],
    "speed": 6,
    "softness": 90,
    "reverse": false
  }
}
```

| 字段 | 必填 | 说明 / Meaning |
|---|---|---|
| `schema` | 是 | 固定为 `1` / always 1 |
| `name` | 是 | 1–32 字符，显示在网页上 / display name |
| `type` | 是 | `builtin` 或 `python` |
| `effect` | `builtin` 必填 | 内置效果 id，见下表 / built-in effect id |
| `module` | `python` 必填 | 同名 `.py` 文件 / sibling script name |
| `params` | 否 | 效果参数，缺省值自动补齐 / effect parameters |
| `param_defs` | Python 样式建议填 | 参数控件描述，见第 5 节 |

未知字段会被忽略；缺少的参数使用默认值（不会报错）。
Unknown fields are ignored; missing parameters fall back to defaults.

---

## 3. 参数类型 / Parameter types

| type | 值 / Value | 示例 / Example |
|---|---|---|
| `int` | 整数，配合 `min` / `max` | `{"speed": 40}` |
| `bool` | `true` / `false` | `{"reverse": true}` |
| `color` | `#RRGGBB` | `"#FF6600"` |
| `colors` | 1–8 个 `#RRGGBB` 的数组 | `["#FF0000", "#00FF00"]` |
| `enum` | 固定字符串 | `"classic"` |

颜色大小写均可。范围外的整数会被截断到最近边界。
Colour hex is case-insensitive; out-of-range integers are clamped.

---

## 4. 内置效果与参数 / Built-in effects

格式：`参数 (类型, 范围, 默认值)`。所有效果都会应用全局亮度。
Format: `param (type, range, default)`. Global brightness is applied by the engine.

| effect | 名称 / Name | 参数 / Parameters |
|---|---|---|
| `solid` | 纯色 / Solid | `color` (color, `#FF6600`) |
| `gradient` | 渐变 / Gradient | `colors` (colors, `["#FF6B35","#F7C59F","#004E89"]`), `speed` (int 0–100, 0), `softness` (int 0–100, 60), `reverse` (bool, false) |
| `breath` | 呼吸 / Breathing | `color` (color, `#FF6600`), `speed` (int 1–100, 30), `min_bright` (int 0–100, 5) |
| `rainbow` | 彩虹 / Rainbow | `speed` (int 0–100, 0), `spread` (int 10–100, 100), `reverse` (bool, false) |
| `rainbow_flow` | 彩虹流动 / Rainbow Flow | `speed` (int 1–100, 35), `spread` (int 10–100, 100), `reverse` (bool, false) |
| `chase` | 追逐 / Chase | `color` (color, `#FF0000`), `bg` (color, `#000000`), `size` (int 1–50, 3), `gap` (int 1–50, 6), `speed` (int 1–100, 40), `reverse` (bool, false) |
| `theater_chase` | 剧院追逐 / Theater Chase | `color` (color, `#FFFFFF`), `bg` (color, `#000000`), `size` (int 1–10, 3), `gap` (int 1–10, 3), `speed` (int 1–100, 40) |
| `comet` | 彗星 / Comet | `color` (color, `#00AAFF`), `tail` (int 1–100, 20), `speed` (int 1–100, 40), `reverse` (bool, false) |
| `sparkle` | 星闪 / Sparkle | `color` (color, `#FFFFFF`), `bg` (color, `#000000`), `density` (int 1–100, 10), `fade` (int 1–100, 40) |
| `twinkle` | 随机闪烁 / Twinkle | `colors` (colors, `["#FFFFFF","#FFDD55","#88BBFF"]`), `bg` (color, `#000000`), `density` (int 1–100, 10), `fade` (int 1–100, 40) |
| `fire` | 火焰 / Fire | `intensity` (int 1–100, 60), `speed` (int 1–100, 50), `palette` (enum `classic`/`blue`/`green`, `classic`) |
| `candle` | 烛光 / Candle | `color` (color, `#FFAA33`), `speed` (int 1–100, 40), `flicker` (int 0–100, 50) |
| `wipe` | 擦除 / Wipe | `colors` (colors, `["#FF0000","#00FF00","#0000FF"]`), `speed` (int 1–100, 30), `mode` (enum `loop`/`pingpong`, `loop`) |
| `scanner` | 扫描 / Scanner | `color` (color, `#FF0000`), `bg` (color, `#000000`), `tail` (int 1–100, 25), `speed` (int 1–100, 40) |
| `strobe` | 频闪 / Strobe | `color` (color, `#FFFFFF`), `speed` (int 1–100, 50), `duty` (int 1–100, 20) |

---

## 5. Python 样式的参数控件 / Python style controls

Python 源码在 `code` 里自己读取 `params`，但网页需要知道有哪些控件，
所以 sidecar JSON 用 `param_defs` 描述（格式与固件内置效果一致）：

The script reads `params` itself. The sidecar JSON's `param_defs` tells the UI
which controls to render, without executing user code when listing styles:

```json
{
  "schema": 1,
  "name": "彩虹彗星 Rainbow Comet",
  "type": "python",
  "module": "comet_tail",
  "params": {"speed": 30, "tail": 10},
  "param_defs": [
    {"key": "speed", "type": "int", "min": 5, "max": 100,
     "default": 30, "label": {"zh": "速度", "en": "Speed"}},
    {"key": "tail", "type": "int", "min": 2, "max": 40,
     "default": 10, "label": {"zh": "拖尾", "en": "Tail"}}
  ]
}
```

支持的 `param_defs` 类型：`int`、`bool`、`color`、`colors`、`enum`。
`enum` 需要 `options: [{"value": "...", "label": {"zh": "...", "en": "..."}}]`。
最多 16 个参数。

---

## 6. 示例 / Examples

**静态渐变 / static gradient**

```json
{
  "schema": 1,
  "name": "深海 Ocean",
  "type": "builtin",
  "effect": "gradient",
  "params": {
    "colors": ["#001F3F", "#0074D9", "#7FDBFF"],
    "speed": 0,
    "softness": 100,
    "reverse": true
  }
}
```

**带背景的流动 / animated fire**

```json
{
  "schema": 1,
  "name": "余烬 Ember",
  "type": "builtin",
  "effect": "fire",
  "params": {"intensity": 75, "speed": 60, "palette": "classic"}
}
```

详见 [`firmware/esp32/styles`](../firmware/esp32/styles) 目录中的 7 个示例。
See the seven sample files in [`firmware/esp32/styles`](../firmware/esp32/styles).

---

## 7. 导入 / 导出 / Import & export

- 网页：样式页右上角「导入 JSON」「导出」，样式卡片下有「编辑」。
- 文件：直接用 Thonny 拖入 `/styles`。
- API：`PUT /api/styles/<id>`，见 [API.md](API.md)。
- 导出文件包含完整样式定义，可分享给其他设备或让 AI 修改。

---

## 8. For AI agents

Hard rules when generating a style:

1. Validate against `style.schema.json` (draft-07). The file must be a single JSON object.
2. `schema` must be `1`; `type` is exactly `builtin` or `python`.
3. `effect` must be one of the 15 ids above. Do not invent effect names.
4. Colours are `#RRGGBB` strings. `colors` arrays hold 1–8 entries.
5. Integers must stay within the documented `min`/`max`; labels are optional.
6. Put no executable code in JSON. Python code belongs in a separate `<id>.py`
   with `render(t, n, params, out, h)` (see [CUSTOM_EFFECTS.md](CUSTOM_EFFECTS.md)).
7. File name `<id>` matches `^[a-z0-9][a-z0-9_-]{0,23}$`; JSON ≤ 4 KB, `.py` ≤ 8 KB.
8. Save with `PUT /api/styles/<id>` (JSON) or copy to `/styles/<id>.json`;
   apply with `POST /api/apply {"style_id": "<id>"}`.
9. Never touch `data/settings.json` to create a style; it is device config only.
10. Prefer declarative `builtin` styles over Python unless arbitrary logic is required.


---

作者 / Author: **洋洋柚**（B站/抖音 洋洋柚Y） · License: **CC BY-NC-SA 4.0**（禁止商用 / NonCommercial）

项目 / Project: [GitHub](https://github.com/YangYangyou-Zhang/esp_web_ws2812b_micropython) ·
[Gitee](https://gitee.com/zhangyangyangyou/esp_web_ws2812b_micropython) ·
[视频 / Video](https://www.bilibili.com/video/BV1zz5zzFEbM)
