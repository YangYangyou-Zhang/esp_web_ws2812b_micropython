# Cooperative, non-blocking LED animation engine.
import gc
import math
import time

import neopixel
from machine import Pin

from effects import EFFECTS, clamp, hsv, lerp, parse_hex, scale
from stylelib import STYLELIB

MAX_LOG = 12


def _ticks_ms():
    try:
        return time.ticks_ms()
    except AttributeError:
        return int(time.time() * 1000)


def _ticks_diff(a, b):
    try:
        return time.ticks_diff(a, b)
    except AttributeError:
        return a - b


class Ctx:
    __slots__ = ('e', 't', 'p', 'n', 'state', '_cc')

    def __init__(self, engine):
        self.e = engine
        self.t = 0.0
        self.p = {}
        self.n = 0
        self.state = {}
        self._cc = {}

    def set(self, i, c):
        f = self.e.frame[i]
        f[0] = c[0]
        f[1] = c[1]
        f[2] = c[2]

    def fill(self, c):
        frame = self.e.frame
        for i in range(self.n):
            f = frame[i]
            f[0] = c[0]
            f[1] = c[1]
            f[2] = c[2]

    def color(self, hx):
        c = self._cc.get(hx)
        if c is None:
            c = parse_hex(hx)
            self._cc[hx] = c
        return c

    def hsv(self, h, s, v):
        return hsv(h, s, v)

    def lerp(self, a, b, f):
        return lerp(a, b, f)

    def scale(self, c, k):
        return scale(c, k)

    def rand(self):
        return self.e.rand()

    def randint(self, n):
        return self.e.randint(n)


class Helpers:
    def __init__(self, engine):
        self.e = engine

    def sin(self, x):
        return math.sin(x)

    def cos(self, x):
        return math.cos(x)

    def pi(self):
        return math.pi

    def hsv(self, h, s, v):
        return hsv(h, s, v)

    def rgb(self, hx):
        return parse_hex(hx)

    def lerp(self, a, b, f):
        return lerp(a, b, f)

    def scale(self, c, k):
        return scale(c, k)

    def clamp(self, v, lo, hi):
        return clamp(v, lo, hi)

    def rand(self):
        return self.e.rand()

    def randint(self, n):
        return self.e.randint(n)


class Engine:
    def __init__(self):
        self.strips = []
        self.pins = []
        self.n = 0
        self.max_leds = 1024
        self.power = False
        self.brightness = 128
        self.fps_target = 30
        self.color_order = 'RGB'
        self.fps = 0
        self.style = None
        self.style_id = None
        self.t0 = 0
        self.boot_ms = _ticks_ms()
        self.last_frame = 0
        self.render_ms = 0
        self.frame = []
        self.state = {}
        self.scale_lut = None
        self.py_render = None
        self.py_ns = None
        self.slow_count = 0
        self.fail_count = 0
        self.logs = []
        self.rng_state = (_ticks_ms() * 2654435761 + 1) & 0x7fffffff
        self._fps_count = 0
        self._fps_mark = _ticks_ms()
        self.ctx = Ctx(self)
        self.helpers = Helpers(self)

    # ---- random -----------------------------------------------------
    def rand(self):
        self.rng_state = (self.rng_state * 1103515245 + 12345) & 0x7fffffff
        return self.rng_state / 2147483648.0

    def randint(self, n):
        if n <= 1:
            return 0
        self.rng_state = (self.rng_state * 1103515245 + 12345) & 0x7fffffff
        return (self.rng_state >> 8) % n

    # ---- logging ----------------------------------------------------
    def log(self, msg):
        print('[ws2812]', msg)
        self.logs.append(str(msg))
        if len(self.logs) > MAX_LOG:
            self.logs.pop(0)

    # ---- hardware ---------------------------------------------------
    def _build(self, pins, leds):
        strips = []
        for p in pins:
            strips.append(neopixel.NeoPixel(Pin(p, Pin.OUT), leds))
        self.strips = strips
        self.pins = list(pins)
        self.n = leds
        self.frame = [[0, 0, 0] for _ in range(leds)]
        self.scale_lut = None
        self.state = {}
        self.py_out_reset()

    def init(self, cfg):
        hw = cfg['hardware']
        self.max_leds = cfg['render']['max_leds']
        leds = hw['leds']
        if leds * 3 * len(hw['pins']) > 65536:
            raise ValueError('LED buffer too large')
        self._build(hw['pins'], leds)
        self.brightness = cfg['render']['brightness']
        self.fps_target = cfg['render']['fps']
        self.color_order = cfg['render'].get('color_order', 'RGB')
        self.log('strips=%s leds=%s' % (self.pins, self.n))

    def reinit(self, leds=None, pins=None):
        old_pins = list(self.pins)
        old_n = self.n
        was_on = self.power
        if leds is None:
            leds = self.n
        if pins is None:
            pins = list(self.pins)
        if leds * 3 * len(pins) > 65536:
            raise ValueError('LED buffer too large')
        self.strips = []
        gc.collect()
        try:
            self._build(pins, leds)
        except Exception as e:
            self._build(old_pins, old_n)
            raise e
        gc.collect()
        if self.style:
            self.apply(self.style, keep_phase=True)
            self.power = was_on
            if not was_on:
                self.clear()
        else:
            self.clear()
        self.log('reinit leds=%s pins=%s' % (leds, pins))
        return True

    def clear(self):
        for s in self.strips:
            for i in range(self.n):
                s[i] = (0, 0, 0)
            s.write()

    # ---- output -----------------------------------------------------
    def _scale(self):
        if self.scale_lut is None:
            b = self.brightness
            self.scale_lut = [i * b // 255 for i in range(256)]
        return self.scale_lut

    def _write(self):
        lut = self._scale()
        frame = self.frame
        n = self.n
        order = self.color_order
        if order == 'RGB':
            for s in self.strips:
                for i in range(n):
                    c = frame[i]
                    s[i] = (lut[c[0]], lut[c[1]], lut[c[2]])
                s.write()
            return
        o0 = 'RGB'.index(order[0])
        o1 = 'RGB'.index(order[1])
        o2 = 'RGB'.index(order[2])
        for s in self.strips:
            for i in range(n):
                c = frame[i]
                s[i] = (lut[c[o0]], lut[c[o1]], lut[c[o2]])
            s.write()

    def set_brightness(self, v):
        self.brightness = clamp(int(v), 0, 255)
        self.scale_lut = None

    # ---- styles -----------------------------------------------------
    def py_out_reset(self):
        self.py_render = None
        self.py_ns = None

    def _load_python(self, style):
        sid = style.get('module')
        src = STYLELIB.get_source(sid)
        if not src:
            raise ValueError('python source missing: %s' % sid)
        ns = {'__name__': 'userstyle_' + sid}
        exec(src, ns)
        fn = ns.get('render')
        if not callable(fn):
            raise ValueError('render() missing in %s.py' % sid)
        self.py_ns = ns
        self.py_render = fn
        params = dict(style.get('params') or {})
        defaults = ns.get('DEFAULTS')
        if isinstance(defaults, dict):
            for k in defaults:
                if k not in params:
                    params[k] = defaults[k]
        style['params'] = params
        self.log('loaded python style: %s' % sid)

    def apply(self, style, keep_phase=False):
        if not isinstance(style, dict):
            raise ValueError('bad style')
        typ = style.get('type', 'builtin')
        if typ == 'builtin':
            effect = style.get('effect')
            if effect not in EFFECTS.meta:
                raise ValueError('unknown effect: %s' % effect)
            style['params'] = EFFECTS.normalize(effect, style.get('params'))
            self.py_out_reset()
        elif typ == 'python':
            self._load_python(style)
        else:
            raise ValueError('bad style type')
        self.style = style
        self.style_id = style.get('id')
        if not keep_phase:
            self.t0 = _ticks_ms()
            self.state = {}
            self.slow_count = 0
            self.fail_count = 0
        self.power = True
        self.last_frame = 0
        return self.style

    def apply_id(self, style_id, params=None):
        same = (style_id == self.style_id)
        style = STYLELIB.resolve(style_id, params)
        if same and self.style and self.style.get('type') == 'builtin' \
                and style.get('type') == 'builtin':
            self.style['params'] = style['params']
            return self.style
        return self.apply(style)

    def update_params(self, params):
        if not self.style:
            return None
        if self.style.get('type') == 'builtin':
            self.style['params'] = EFFECTS.normalize(
                self.style['effect'], params)
        else:
            merged = dict(self.style.get('params') or {})
            if isinstance(params, dict):
                for k in params:
                    merged[k] = params[k]
            self.style['params'] = merged
        return self.style

    def set_power(self, on):
        if on:
            if not self.style:
                self.apply(STYLELIB.resolve('builtin:solid'))
            else:
                self.power = True
                self.last_frame = 0
        else:
            self.power = False
            self.clear()
        return self.power

    def boot(self, cfg):
        b = cfg['boot']
        self.brightness = b.get('brightness', cfg['render']['brightness'])
        self.scale_lut = None
        if b.get('mode') == 'off' or not b.get('power', True):
            self.power = False
            self.clear()
            return
        try:
            style = STYLELIB.resolve(b.get('style', 'builtin:rainbow'),
                                     b.get('params'))
            self.apply(style)
        except Exception as e:
            self.log('boot style failed: %s' % e)
            try:
                self.apply(STYLELIB.resolve('builtin:rainbow'))
            except Exception:
                pass

    # ---- render -----------------------------------------------------
    def _render_builtin(self, t):
        ctx = self.ctx
        ctx.t = t
        ctx.p = self.style['params']
        ctx.n = self.n
        ctx.state = self.state
        EFFECTS.apply(self.style['effect'], ctx)

    def _render_python(self, t):
        if self.py_render is None:
            self._load_python(self.style)
        self.py_render(t, self.n, self.style['params'], self.frame,
                       self.helpers)

    def _fallback(self, reason):
        self.log('style disabled: %s' % reason)
        black = {'id': 'builtin:solid', 'name': 'Solid', 'type': 'builtin',
                 'effect': 'solid', 'params': {'color': '#000000'},
                 'param_defs': EFFECTS.param_defs('solid')}
        try:
            self.apply(black)
        except Exception:
            self.power = False
            self.clear()

    def tick(self, now=None):
        if not self.power:
            return False
        if now is None:
            now = _ticks_ms()
        period = 1000 // self.fps_target
        if self.last_frame and _ticks_diff(now, self.last_frame) < period:
            return False
        self.last_frame = now
        t = _ticks_diff(now, self.t0) / 1000.0
        start = _ticks_ms()
        try:
            if not self.style:
                return False
            if self.style.get('type') == 'python':
                self._render_python(t)
            else:
                self._render_builtin(t)
            self._write()
            self.fail_count = 0
        except Exception as e:
            self.fail_count += 1
            self.log('render error: %s' % e)
            if self.fail_count >= 3 or self.style.get('type') == 'python':
                self._fallback(str(e))
            return False
        dt = _ticks_diff(_ticks_ms(), start)
        self.render_ms = dt
        if dt > 500:
            self.slow_count += 1
            if self.slow_count >= 3 and self.style.get('type') == 'python':
                self._fallback('too slow (%d ms/frame)' % dt)
                self.slow_count = 0
        elif self.slow_count > 0:
            self.slow_count = 0
        self._fps_count += 1
        if _ticks_diff(now, self._fps_mark) >= 1000:
            self.fps = self._fps_count
            self._fps_count = 0
            self._fps_mark = now
        return True

    # ---- status -----------------------------------------------------
    def state_dict(self):
        try:
            heap = gc.mem_free()
        except AttributeError:
            heap = 0
        return {
            'power': self.power,
            'brightness': self.brightness,
            'fps': self.fps,
            'fps_target': self.fps_target,
            'render_ms': self.render_ms,
            'leds': self.n,
            'pins': list(self.pins),
            'max_leds': self.max_leds,
            'heap': heap,
            'uptime': _ticks_diff(_ticks_ms(), self.boot_ms) // 1000,
            'style_id': self.style_id,
            'style_name': (self.style or {}).get('name'),
            'style_type': (self.style or {}).get('type'),
            'style_params': (self.style or {}).get('params'),
            'logs': self.logs[-5:],
        }


ENGINE = Engine()
