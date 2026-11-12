# Python 自定义效果 / Custom effects in Python

> 建议先用 JSON 内置效果（见 [STYLE_FORMAT.md](STYLE_FORMAT.md)）。
> 只有需要任意逻辑时才写 Python。
> Prefer declarative JSON styles. Use Python only when you need custom logic.

---

## 1. 文件结构 / Files

一个 Python 样式由两个文件组成 / two files:

```
/styles/mystyle.json   # 样式定义 + 参数控件描述（sidecar）
/styles/mystyle.py     # 源码，必须提供 render()
```

`mystyle.json`:

```json
{
  "schema": 1,
  "name": "我的效果 My Effect",
  "type": "python",
  "module": "mystyle",
  "params": {"speed": 40, "color": "#FF3300"},
  "param_defs": [
    {"key": "speed", "type": "int", "min": 1, "max": 100, "default": 40,
     "label": {"zh": "速度", "en": "Speed"}},
    {"key": "color", "type": "color", "default": "#FF3300",
     "label": {"zh": "颜色", "en": "Colour"}}
  ]
}
```

- `module` 必须与 `.py` 文件名一致。
- `param_defs` 只用于生成网页控件，不会传给脚本；脚本通过 `params` 读取值。
- 没有 `param_defs` 也能运行，只是网页不会显示可调参数。
- JSON ≤ 4 KB；`.py` ≤ 8 KB。

网页「新建 Python 样式」会自动生成这两个文件。

---

## 2. 脚本接口 / Script API

```python
NAME = "My Effect"                  # 可选，仅用于调试
DEFAULTS = {"speed": 40}            # 可选，未在 JSON params 中给出的键会自动补齐

def render(t, n, params, out, h):
    ...
```

| 参数 | 类型 | 说明 |
|---|---|---|
| `t` | float | 当前样式运行时间（秒），用于动画相位 |
| `n` | int | 每条灯带的灯珠数 |
| `params` | dict | JSON `params` 与 `DEFAULTS` 合并后的参数 |
| `out` | list | 长度为 n 的可变列表，每项是 `[r, g, b]`（0–255） |
| `h` | object | 辅助函数，见下表 |

`render()` 每帧调用一次。**返回值被忽略**，请直接修改 `out[i][0..2]`。
亮度缩放由引擎统一处理，脚本输出 0–255 的原始颜色即可。
不要修改 `n`、`params` 或替换 `out` 列表本身。

`render()` 的模块级全局变量会在样式加载期间保持，可用于保存状态
（例如随机种子、上一帧的亮度），但不要依赖它做长时间计时。

### 辅助函数 / Helpers

| 调用 | 说明 |
|---|---|
| `h.sin(x)`, `h.cos(x)` | 弧度三角函数 |
| `h.pi()` | 3.14159265… |
| `h.hsv(h, s, v)` | 0≤h<1，s/v 0–1，返回 `(r,g,b)` 0–255 |
| `h.rgb("#RRGGBB")` | 十六进制转 `(r,g,b)` |
| `h.lerp(a, b, f)` | 两个颜色按 f(0–1) 插值 |
| `h.scale(c, k)` | 颜色乘以系数 k |
| `h.clamp(v, lo, hi)` | 限幅 |
| `h.rand()` | 0.0–1.0 随机数 |
| `h.randint(n)` | 0–n-1 随机整数 |

---

## 3. 示例 / Examples

### 3.1 呼吸 + 颜色参数

```python
import math

NAME = "Soft Pulse"
DEFAULTS = {"speed": 1.2, "color": "#3399FF"}

def render(t, n, params, out, h):
    c = h.rgb(params["color"])
    v = (math.sin(t * params["speed"] * 6.283) + 1.0) * 0.5
    for i in range(n):
        out[i][0] = int(c[0] * v)
        out[i][1] = int(c[1] * v)
        out[i][2] = int(c[2] * v)
```

### 3.2 双色波浪

```python
def render(t, n, params, out, h):
    a = h.rgb(params.get("a", "#FF0066"))
    b = h.rgb(params.get("b", "#00CCFF"))
    speed = params.get("speed", 30)
    for i in range(n):
        f = 0.5 + 0.5 * h.sin(i * 0.35 + t * speed * 0.1)
        c = h.lerp(a, b, f)
        out[i][0] = c[0]
        out[i][1] = c[1]
        out[i][2] = c[2]
```

### 3.3 彩虹彗星（仓库示例）

见 [`firmware/esp32/styles/comet_tail.py`](../firmware/esp32/styles/comet_tail.py)。

---

## 4. 限制与安全 / Limits and safety

1. **每帧必须很快返回。** 建议单帧 < 5 ms；ESP8266 上 < 3 ms。
2. **绝对不要 `while True` / `time.sleep()`。** 主循环是单线程合作式的；
   死循环会让设备和网页一起卡死，只能复位。固件无法抢占式打断 Python 代码。
3. 固件会统计每帧耗时：
   - 单帧 > 500 ms 连续 3 次 → 自动停用该样式并回退到纯黑；
   - 任何时候抛异常 → 立即回退，并把错误写入 `/api/log`。
   这两种保护都只在 `render()` **返回之后**生效，不能救死循环。
4. 不要在脚本里做文件、网络、串口操作，不要 `import` 固件模块。
5. 内存：脚本 bytecode 常驻；ESP8266 上请保持脚本短小（建议 < 2 KB）。
6. 不要创建大列表/无限增长的全局缓存；每帧分配越少越稳。
7. 灯珠数量为 n，索引必须 0‥n-1，越界会抛异常并回退。

If a style freezes the device: reboot, connect with Thonny, then delete
`/styles/<id>.py` (or fix it) and set the boot mode to another style in
`/data/settings.json`. A style is only executed when it is applied or is the
boot style, so deleting the sidecar JSON is enough to stop it from loading.

---

## 5. 调试 / Debugging

- 网页「设置 → 查看日志」读取 `/api/log`，最近 12 条。
- 也可 `GET /api/log`。
- 桌面模拟器可以直接跑：把两个文件放进 `styles/`，运行
  `python tools/sim.py`，在网页应用即可；报错会打印在终端。
- `print()` 输出到串口 REPL（Thonny 可看）。

---

## 6. 安装 / Install

- 网页：样式页 →「新建 Python 样式」，粘贴源码与参数定义并保存。
- 文件：把 `mystyle.json` 和 `mystyle.py` 复制到设备 `/styles/`。
- API：
  ```bash
  curl -X PUT --data-binary @mystyle.py \
       http://192.168.4.1/api/styles/mystyle.py
  curl -X PUT -H 'Content-Type: application/json' \
       --data-binary @mystyle.json \
       http://192.168.4.1/api/styles/mystyle
  ```
  先传 sidecar 或先传源码都可以，但两者都存在才能应用。

---

## 7. For AI agents

- Output exactly two files: `<id>.json` (schema in [`style.schema.json`](../firmware/esp32/style.schema.json))
  and `<id>.py`.
- `.py` must define `render(t, n, params, out, h)` at module level.
- Never emit loops without bounds, `sleep`, I/O, or imports of `machine`/`neopixel`.
- Keep the whole render body O(n) and allocation-free where practical.
- Read parameters via `params.get(key, default)` so missing keys cannot crash.
- Use `h.*` helpers instead of importing math when convenient; `import math` is allowed.
- Test with `python tools/sim.py` before uploading when possible.


---

作者 / Author: **洋洋柚**（B站/抖音 洋洋柚Y） · License: **CC BY-NC-SA 4.0**（禁止商用 / NonCommercial）

项目 / Project: [GitHub](https://github.com/YangYangyou-Zhang/esp_web_ws2812b_micropython) ·
[Gitee](https://gitee.com/zhangyangyangyou/esp_web_ws2812b_micropython) ·
[视频 / Video](https://www.bilibili.com/video/BV1zz5zzFEbM)
