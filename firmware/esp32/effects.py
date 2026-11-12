# Built-in effects and their parameter metadata.
import math

HEX_CHARS = '0123456789abcdefABCDEF'


def parse_hex(s):
    if not isinstance(s, str) or len(s) != 7 or s[0] != '#':
        return (0, 0, 0)
    for ch in s[1:]:
        if ch not in HEX_CHARS:
            return (0, 0, 0)
    return (int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))


def clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def hsv(h, s, v):
    h = h % 1.0
    s = clamp(s, 0.0, 1.0)
    v = clamp(v, 0.0, 1.0)
    i = int(h * 6.0)
    f = h * 6.0 - i
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    return (int(r * 255), int(g * 255), int(b * 255))


def lerp(a, b, f):
    return (
        int(a[0] + (b[0] - a[0]) * f),
        int(a[1] + (b[1] - a[1]) * f),
        int(a[2] + (b[2] - a[2]) * f),
    )


def scale(c, k):
    return (int(c[0] * k), int(c[1] * k), int(c[2] * k))


def _hex_list(v):
    if not isinstance(v, (list, tuple)):
        return None
    out = []
    for c in v[:8]:
        if isinstance(c, str) and len(c) == 7 and c[0] == '#' and \
                all(ch in HEX_CHARS for ch in c[1:]):
            out.append('#' + c[1:].lower())
    return out or None


def _color_label(zh, en):
    return {'zh': zh, 'en': en}


def _p(key, typ, default, zh, en, lo=None, hi=None, options=None):
    d = {'key': key, 'type': typ, 'default': default,
         'label': _color_label(zh, en)}
    if lo is not None:
        d['min'] = lo
    if hi is not None:
        d['max'] = hi
    if options is not None:
        d['options'] = options
    return d


def _enum(key, default, zh, en, options):
    return {'key': key, 'type': 'enum', 'default': default,
            'label': _color_label(zh, en), 'options': options}


META = {
    'solid': {
        'name': _color_label('纯色', 'Solid'),
        'desc': _color_label('整条灯带显示单一颜色', 'Whole strip in one colour'),
        'anim': 'static',
        'params': [_p('color', 'color', '#ff6600', '颜色', 'Colour')],
    },
    'gradient': {
        'name': _color_label('渐变', 'Gradient'),
        'desc': _color_label('多色线性渐变，可流动', 'Multi-colour gradient, optionally moving'),
        'anim': 'flow',
        'params': [
            _p('colors', 'colors', ['#ff6b35', '#f7c59f', '#004e89'], '配色', 'Colours'),
            _p('speed', 'int', 0, '流动速度', 'Speed', 0, 100),
            _p('softness', 'int', 60, '柔和度', 'Softness', 0, 100),
            _p('reverse', 'bool', False, '反向', 'Reverse'),
        ],
    },
    'breath': {
        'name': _color_label('呼吸', 'Breathing'),
        'desc': _color_label('整条灯带明暗呼吸', 'Fade the whole strip in and out'),
        'anim': 'pulse',
        'params': [
            _p('color', 'color', '#ff6600', '颜色', 'Colour'),
            _p('speed', 'int', 30, '速度', 'Speed', 1, 100),
            _p('min_bright', 'int', 5, '最低亮度 %', 'Min brightness %', 0, 100),
        ],
    },
    'rainbow': {
        'name': _color_label('彩虹', 'Rainbow'),
        'desc': _color_label('沿灯带铺开七彩光谱', 'Full spectrum across the strip'),
        'anim': 'flow',
        'params': [
            _p('speed', 'int', 0, '流动速度', 'Speed', 0, 100),
            _p('spread', 'int', 100, '光谱跨度 %', 'Spread %', 10, 100),
            _p('reverse', 'bool', False, '反向', 'Reverse'),
        ],
    },
    'rainbow_flow': {
        'name': _color_label('彩虹流动', 'Rainbow Flow'),
        'desc': _color_label('七彩沿灯带持续流动', 'Rainbow scrolling along the strip'),
        'anim': 'flow',
        'params': [
            _p('speed', 'int', 35, '速度', 'Speed', 1, 100),
            _p('spread', 'int', 100, '光谱跨度 %', 'Spread %', 10, 100),
            _p('reverse', 'bool', False, '反向', 'Reverse'),
        ],
    },
    'chase': {
        'name': _color_label('追逐', 'Chase'),
        'desc': _color_label('色块沿灯带奔跑', 'A block of light runs along the strip'),
        'anim': 'chase',
        'params': [
            _p('color', 'color', '#ff0000', '颜色', 'Colour'),
            _p('bg', 'color', '#000000', '背景色', 'Background'),
            _p('size', 'int', 3, '色块长度', 'Block size', 1, 50),
            _p('gap', 'int', 6, '间隔', 'Gap', 1, 50),
            _p('speed', 'int', 40, '速度', 'Speed', 1, 100),
            _p('reverse', 'bool', False, '反向', 'Reverse'),
        ],
    },
    'theater_chase': {
        'name': _color_label('剧院追逐', 'Theater Chase'),
        'desc': _color_label('等间距色块逐格推进', 'Evenly spaced blocks stepping forward'),
        'anim': 'chase',
        'params': [
            _p('color', 'color', '#ffffff', '颜色', 'Colour'),
            _p('bg', 'color', '#000000', '背景色', 'Background'),
            _p('size', 'int', 3, '亮灯数', 'Lit LEDs', 1, 10),
            _p('gap', 'int', 3, '暗灯数', 'Dark LEDs', 1, 10),
            _p('speed', 'int', 40, '速度', 'Speed', 1, 100),
        ],
    },
    'comet': {
        'name': _color_label('彗星', 'Comet'),
        'desc': _color_label('带拖尾的流星循环运动', 'A meteor with a fading tail'),
        'anim': 'chase',
        'params': [
            _p('color', 'color', '#00aaff', '颜色', 'Colour'),
            _p('tail', 'int', 20, '拖尾长度', 'Tail length', 1, 100),
            _p('speed', 'int', 40, '速度', 'Speed', 1, 100),
            _p('reverse', 'bool', False, '反向', 'Reverse'),
        ],
    },
    'sparkle': {
        'name': _color_label('星闪', 'Sparkle'),
        'desc': _color_label('随机亮点点缀在背景上', 'Random sparkles over a background'),
        'anim': 'flicker',
        'params': [
            _p('color', 'color', '#ffffff', '闪烁色', 'Sparkle colour'),
            _p('bg', 'color', '#000000', '背景色', 'Background'),
            _p('density', 'int', 10, '密度', 'Density', 1, 100),
            _p('fade', 'int', 40, '衰减', 'Fade', 1, 100),
        ],
    },
    'twinkle': {
        'name': _color_label('随机闪烁', 'Twinkle'),
        'desc': _color_label('多色彩随机闪烁', 'Random multi-colour twinkling'),
        'anim': 'flicker',
        'params': [
            _p('colors', 'colors', ['#ffffff', '#ffdd55', '#88bbff'], '配色', 'Colours'),
            _p('bg', 'color', '#000000', '背景色', 'Background'),
            _p('density', 'int', 10, '密度', 'Density', 1, 100),
            _p('fade', 'int', 40, '衰减', 'Fade', 1, 100),
        ],
    },
    'fire': {
        'name': _color_label('火焰', 'Fire'),
        'desc': _color_label('模拟火焰跳动', 'Simulated flickering fire'),
        'anim': 'flicker',
        'params': [
            _p('intensity', 'int', 60, '强度', 'Intensity', 1, 100),
            _p('speed', 'int', 50, '速度', 'Speed', 1, 100),
            _enum('palette', 'classic', '配色', 'Palette', [
                {'value': 'classic', 'label': _color_label('经典', 'Classic')},
                {'value': 'blue', 'label': _color_label('蓝焰', 'Blue')},
                {'value': 'green', 'label': _color_label('绿焰', 'Green')},
            ]),
        ],
    },
    'candle': {
        'name': _color_label('烛光', 'Candle'),
        'desc': _color_label('暖光随机摇曳', 'Warm light with random flicker'),
        'anim': 'flicker',
        'params': [
            _p('color', 'color', '#ffaa33', '颜色', 'Colour'),
            _p('speed', 'int', 40, '摇曳速度', 'Flicker speed', 1, 100),
            _p('flicker', 'int', 50, '摇曳幅度', 'Flicker depth', 0, 100),
        ],
    },
    'wipe': {
        'name': _color_label('擦除', 'Wipe'),
        'desc': _color_label('多种颜色轮流铺满灯带', 'Colours wipe across the strip in turn'),
        'anim': 'chase',
        'params': [
            _p('colors', 'colors', ['#ff0000', '#00ff00', '#0000ff'], '配色', 'Colours'),
            _p('speed', 'int', 30, '速度', 'Speed', 1, 100),
            _enum('mode', 'loop', '模式', 'Mode', [
                {'value': 'loop', 'label': _color_label('循环', 'Loop')},
                {'value': 'pingpong', 'label': _color_label('往返', 'Ping-pong')},
            ]),
        ],
    },
    'scanner': {
        'name': _color_label('扫描', 'Scanner'),
        'desc': _color_label('光点来回扫描', 'A light dot bounces back and forth'),
        'anim': 'chase',
        'params': [
            _p('color', 'color', '#ff0000', '颜色', 'Colour'),
            _p('bg', 'color', '#000000', '背景色', 'Background'),
            _p('tail', 'int', 25, '拖尾', 'Tail', 1, 100),
            _p('speed', 'int', 40, '速度', 'Speed', 1, 100),
        ],
    },
    'strobe': {
        'name': _color_label('频闪', 'Strobe'),
        'desc': _color_label('按频率闪烁', 'Flash at a fixed rate'),
        'anim': 'flash',
        'params': [
            _p('color', 'color', '#ffffff', '颜色', 'Colour'),
            _p('speed', 'int', 50, '频率', 'Rate', 1, 100),
            _p('duty', 'int', 20, '占空比 %', 'Duty %', 1, 100),
        ],
    },
}

ORDER = [
    'solid', 'gradient', 'breath', 'rainbow', 'rainbow_flow',
    'chase', 'theater_chase', 'comet', 'sparkle', 'twinkle',
    'fire', 'candle', 'wipe', 'scanner', 'strobe',
]

_RAINBOW = None


def _rainbow_lut():
    global _RAINBOW
    if _RAINBOW is None:
        _RAINBOW = [hsv(i / 128.0, 1.0, 1.0) for i in range(128)]
    return _RAINBOW


# ---- effects ---------------------------------------------------------

def _fx_solid(ctx):
    ctx.fill(ctx.color(ctx.p['color']))


def _fx_gradient(ctx):
    cols = [ctx.color(c) for c in ctx.p['colors']]
    seg = len(cols) - 1
    if seg < 1:
        ctx.fill(cols[0])
        return
    speed = ctx.p['speed'] / 100.0 * 0.25
    softw = ctx.p['softness'] / 100.0
    rev = ctx.p['reverse']
    n = ctx.n
    denom = (n - 1) if n > 1 else 1
    for i in range(n):
        pos = i / denom
        if rev:
            pos = 1.0 - pos
        pos = (pos + ctx.t * speed) % 1.0
        f = pos * seg
        a = int(f)
        frac = f - a
        w = 0.0
        if softw > 0.0:
            edge = 1.0 - softw
            if frac > edge:
                w = (frac - edge) / softw
        ctx.set(i, lerp(cols[a], cols[(a + 1) % len(cols)], w))


def _fx_breath(ctx):
    p = ctx.p
    v = (math.sin(ctx.t * p['speed'] * 0.12) + 1.0) * 0.5
    m = p['min_bright'] / 100.0
    v = m + (1.0 - m) * v
    ctx.fill(scale(ctx.color(p['color']), v))


def _fx_rainbow(ctx):
    p = ctx.p
    lut = _rainbow_lut()
    spread = p['spread'] / 100.0
    off = ctx.t * p['speed'] / 100.0
    rev = p['reverse']
    n = ctx.n
    denom = n if n else 1
    for i in range(n):
        x = (i / denom) * spread
        if rev:
            x = -x
        ctx.set(i, lut[int((x + off) * 128) % 128])


def _fx_chase(ctx):
    p = ctx.p
    col = ctx.color(p['color'])
    bg = ctx.color(p['bg'])
    n = ctx.n
    size = p['size']
    period = size + p['gap']
    pos = int(ctx.t * p['speed'] * 0.2) % period
    rev = p['reverse']
    for i in range(n):
        idx = (n - 1 - i) if rev else i
        ctx.set(i, col if ((idx - pos) % period) < size else bg)


def _fx_theater(ctx):
    p = ctx.p
    col = ctx.color(p['color'])
    bg = ctx.color(p['bg'])
    n = ctx.n
    period = p['size'] + p['gap']
    pos = int(ctx.t * p['speed'] * 0.15) % period
    for i in range(n):
        ctx.set(i, col if ((i + pos) % period) < p['size'] else bg)


def _fx_comet(ctx):
    p = ctx.p
    col = ctx.color(p['color'])
    n = ctx.n
    tail = p['tail']
    if tail > n:
        tail = n
    head = int(ctx.t * p['speed'] * 0.3) % n
    if p['reverse']:
        head = n - 1 - head
    for i in range(n):
        d = (head - i) % n
        if d < tail:
            ctx.set(i, scale(col, 1.0 - d / tail))
        else:
            ctx.set(i, (0, 0, 0))


def _fx_sparkle(ctx):
    p = ctx.p
    n = ctx.n
    col = ctx.color(p['color'])
    bg = ctx.color(p['bg'])
    lvl = ctx.state.get('lvl')
    if lvl is None or len(lvl) != n:
        lvl = bytearray(n)
        ctx.state['lvl'] = lvl
    decay = 255 - int(p['fade'] * 2.5)
    if decay < 0:
        decay = 0
    for i in range(n):
        v = lvl[i]
        if v:
            v = v * decay // 255
            lvl[i] = v
            ctx.set(i, scale(col, v / 255.0))
        else:
            ctx.set(i, bg)
    hits = 1 + (n * p['density']) // 900
    for _ in range(hits):
        lvl[ctx.randint(n)] = 255


def _fx_twinkle(ctx):
    p = ctx.p
    n = ctx.n
    cols = [ctx.color(c) for c in p['colors']]
    bg = ctx.color(p['bg'])
    lvl = ctx.state.get('lvl')
    if lvl is None or len(lvl) != n:
        lvl = bytearray(n)
        ctx.state['lvl'] = lvl
        ctx.state['cols'] = [bg] * n
    colmap = ctx.state['cols']
    decay = 255 - int(p['fade'] * 2.5)
    if decay < 0:
        decay = 0
    for i in range(n):
        v = lvl[i]
        if v:
            v = v * decay // 255
            lvl[i] = v
            ctx.set(i, scale(colmap[i], v / 255.0))
        else:
            ctx.set(i, bg)
    hits = 1 + (n * p['density']) // 900
    for _ in range(hits):
        k = ctx.randint(n)
        lvl[k] = 255
        colmap[k] = cols[ctx.randint(len(cols))]


def _fire_palette(name):
    if name == 'blue':
        return [(0, 0, 0), (0, 20, 110), (0, 90, 220), (140, 210, 255)]
    if name == 'green':
        return [(0, 0, 0), (0, 70, 10), (20, 180, 40), (190, 255, 150)]
    return [(0, 0, 0), (140, 10, 0), (255, 110, 0), (255, 230, 120)]


_FIRE_LUTS = {}


def _fire_lut(name):
    lut = _FIRE_LUTS.get(name)
    if lut is None:
        pal = _fire_palette(name)
        lut = []
        for idx in range(64):
            j = idx * 3 // 64
            frac = (idx * 3 / 64.0) - j
            lut.append(lerp(pal[j], pal[j + 1], frac))
        _FIRE_LUTS[name] = lut
    return lut


def _fx_fire(ctx):
    p = ctx.p
    n = ctx.n
    heat = ctx.state.get('heat')
    if heat is None or len(heat) != n:
        heat = bytearray(n)
        ctx.state['heat'] = heat
    cooling = 2 + (100 - p['intensity']) // 12
    sparking = p['speed'] * 2

    for i in range(n):
        v = heat[i] - ctx.randint(cooling + 1)
        heat[i] = v if v > 0 else 0
    for i in range(n - 1, 1, -1):
        heat[i] = (heat[i - 1] + heat[i - 2] * 2) // 3
    if ctx.randint(255) < sparking:
        heat[ctx.randint(n)] = 255

    lut = _fire_lut(p['palette'])
    for i in range(n):
        ctx.set(i, lut[heat[i] >> 2])


def _fx_candle(ctx):
    p = ctx.p
    n = ctx.n
    col = ctx.color(p['color'])
    phase = ctx.state.get('ph')
    if phase is None or len(phase) != n:
        phase = [ctx.rand() * 6.283 for _ in range(n)]
        ctx.state['ph'] = phase
    depth = p['flicker'] / 100.0
    spd = p['speed'] * 0.08
    g = 0.82 + 0.18 * math.sin(ctx.t * spd * 7.0)
    for i in range(n):
        v = g + depth * (0.5 + 0.5 * math.sin(ctx.t * spd * 3.0 + phase[i]))
        v = clamp(v, 0.1, 1.0)
        ctx.set(i, scale(col, v))


def _fx_wipe(ctx):
    p = ctx.p
    cols = [ctx.color(c) for c in p['colors']]
    n = ctx.n
    m = len(cols)
    prog = (ctx.t * p['speed'] / 200.0) % 1.0
    if p['mode'] == 'pingpong':
        prog = 1.0 - abs(prog * 2.0 - 1.0)
    phase = prog * m
    ci = int(phase) % m
    cur = cols[ci]
    prev = cols[(ci - 1) % m]
    cut = int((phase - int(phase)) * n)
    for i in range(n):
        ctx.set(i, prev if i >= cut else cur)


def _fx_scanner(ctx):
    p = ctx.p
    n = ctx.n
    col = ctx.color(p['color'])
    bg = ctx.color(p['bg'])
    tail = p['tail']
    period = (n - 1) * 2 if n > 1 else 2
    pos = (ctx.t * p['speed'] * 0.35) % period
    if pos > (n - 1):
        pos = period - pos
    for i in range(n):
        d = abs(i - pos)
        if d < tail:
            ctx.set(i, scale(col, 1.0 - d / tail))
        else:
            ctx.set(i, bg)


def _fx_strobe(ctx):
    p = ctx.p
    hz = 0.5 + p['speed'] * 0.25
    phase = (ctx.t * hz) % 1.0
    if phase < p['duty'] / 100.0:
        ctx.fill(ctx.color(p['color']))
    else:
        ctx.fill((0, 0, 0))


_FX = {
    'solid': _fx_solid,
    'gradient': _fx_gradient,
    'breath': _fx_breath,
    'rainbow': _fx_rainbow,
    'rainbow_flow': _fx_rainbow,
    'chase': _fx_chase,
    'theater_chase': _fx_theater,
    'comet': _fx_comet,
    'sparkle': _fx_sparkle,
    'twinkle': _fx_twinkle,
    'fire': _fx_fire,
    'candle': _fx_candle,
    'wipe': _fx_wipe,
    'scanner': _fx_scanner,
    'strobe': _fx_strobe,
}


class Effects:
    def __init__(self):
        self.meta = META
        self.order = ORDER

    def display_name(self, effect):
        spec = META.get(effect)
        if not spec:
            return effect
        return spec['name'].get('zh') or effect

    def param_defs(self, effect):
        spec = META.get(effect)
        return spec['params'] if spec else []

    def normalize(self, effect, params):
        spec = META.get(effect)
        if not spec:
            raise ValueError('unknown effect: %s' % effect)
        src = params if isinstance(params, dict) else {}
        out = {}
        for d in spec['params']:
            key = d['key']
            typ = d['type']
            v = src.get(key, d.get('default'))
            if typ == 'int':
                if isinstance(v, bool) or not isinstance(v, int):
                    v = d['default']
                v = clamp(v, d.get('min', 0), d.get('max', 100))
            elif typ == 'bool':
                v = bool(v) if isinstance(v, bool) else bool(d['default'])
            elif typ == 'color':
                v = _hex_list([v])
                v = v[0] if v else d['default']
            elif typ == 'colors':
                v = _hex_list(v) or list(d['default'])
            elif typ == 'enum':
                values = [o['value'] for o in d['options']]
                if v not in values:
                    v = d['default']
            out[key] = v
        return out

    def apply(self, effect, ctx):
        fn = _FX.get(effect)
        if fn is None:
            raise ValueError('unknown effect: %s' % effect)
        fn(ctx)


EFFECTS = Effects()
