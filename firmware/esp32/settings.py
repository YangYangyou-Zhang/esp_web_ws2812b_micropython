# Persistent device settings (data/settings.json).
import json
import os
import sys

DATA_DIR = 'data'
SETTINGS_PATH = 'data/settings.json'

DEFAULT_SSID = 'ESP_WS2812B_BY_YYY'
DEFAULT_PASSWORD = '12345678'


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


class Settings:
    def __init__(self):
        self.cfg = None

    def platform(self):
        return getattr(sys, 'platform', 'unknown')

    def defaults(self):
        return {
            'schema': 1,
            'wifi': {'ssid': DEFAULT_SSID, 'password': DEFAULT_PASSWORD},
            'hardware': {'pins': [2], 'leds': 30},
            'render': {'fps': 30, 'brightness': 128, 'max_leds': 1024,
                       'color_order': 'RGB'},
            'boot': {
                'mode': 'preset',
                'style': 'builtin:rainbow',
                'params': {},
                'brightness': 128,
                'power': True,
            },
        }

    def ensure_dirs(self):
        try:
            os.mkdir(DATA_DIR)
        except OSError:
            pass
        try:
            os.mkdir('styles')
        except OSError:
            pass

    def load(self):
        self.ensure_dirs()
        cfg = None
        loaded = False
        try:
            f = open(SETTINGS_PATH)
            try:
                cfg = json.loads(f.read())
                loaded = True
            finally:
                f.close()
        except Exception:
            cfg = None
        merged = self.defaults()
        if cfg:
            self._merge(merged, cfg)
        self.cfg = self.sanitize(merged)
        if not loaded:
            self.save()
        return self.cfg

    def _merge(self, dst, src):
        for k in src:
            v = src[k]
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                self._merge(dst[k], v)
            else:
                dst[k] = v

    def sanitize(self, c):
        d = self.defaults()

        wifi = c.get('wifi') if isinstance(c.get('wifi'), dict) else {}
        ssid = wifi.get('ssid')
        if isinstance(ssid, str) and 1 <= len(ssid) <= 32:
            d['wifi']['ssid'] = ssid
        pw = wifi.get('password')
        if isinstance(pw, str) and len(pw) <= 63:
            d['wifi']['password'] = pw

        hw = c.get('hardware') if isinstance(c.get('hardware'), dict) else {}
        pins = hw.get('pins')
        clean_pins = []
        if isinstance(pins, (list, tuple)):
            for p in pins[:8]:
                if _is_int(p) and 0 <= p <= 48:
                    clean_pins.append(p)
        if clean_pins:
            d['hardware']['pins'] = clean_pins
        r = c.get('render') if isinstance(c.get('render'), dict) else {}
        max_leds = r.get('max_leds')
        if _is_int(max_leds) and 1 <= max_leds <= 2048:
            d['render']['max_leds'] = max_leds
        leds = hw.get('leds')
        if _is_int(leds):
            d['hardware']['leds'] = _clamp(leds, 1, d['render']['max_leds'])
        fps = r.get('fps')
        if _is_int(fps):
            d['render']['fps'] = _clamp(fps, 5, 60)
        br = r.get('brightness')
        if _is_int(br):
            d['render']['brightness'] = _clamp(br, 0, 255)
        order = r.get('color_order')
        if order in ('RGB', 'RBG', 'GRB', 'GBR', 'BRG', 'BGR'):
            d['render']['color_order'] = order

        b = c.get('boot') if isinstance(c.get('boot'), dict) else {}
        mode = b.get('mode')
        if mode in ('off', 'preset', 'last'):
            d['boot']['mode'] = mode
        style = b.get('style')
        if isinstance(style, str) and 0 < len(style) <= 48:
            d['boot']['style'] = style
        params = b.get('params')
        if isinstance(params, dict):
            d['boot']['params'] = params
        bbr = b.get('brightness')
        if _is_int(bbr):
            d['boot']['brightness'] = _clamp(bbr, 0, 255)
        power = b.get('power')
        if isinstance(power, bool):
            d['boot']['power'] = power
        return d

    def get(self):
        if self.cfg is None:
            self.load()
        return self.cfg

    def save(self):
        cfg = self.cfg
        if cfg is None:
            return
        tmp = SETTINGS_PATH + '.tmp'
        try:
            f = open(tmp, 'w')
            try:
                f.write(json.dumps(cfg))
            finally:
                f.close()
            try:
                os.rename(tmp, SETTINGS_PATH)
            except OSError:
                try:
                    os.remove(SETTINGS_PATH)
                except OSError:
                    pass
                os.rename(tmp, SETTINGS_PATH)
        except OSError as e:
            print('settings save failed:', e)
            try:
                os.remove(tmp)
            except OSError:
                pass

    def merge_patch(self, patch):
        cfg = self.get()
        if isinstance(patch, dict):
            self._merge(cfg, patch)
        self.cfg = self.sanitize(cfg)
        self.save()
        return self.cfg

    def set_boot(self, style, params, brightness, power=True, mode='preset'):
        cfg = self.get()
        cfg['boot']['mode'] = mode
        cfg['boot']['style'] = style
        cfg['boot']['params'] = params if isinstance(params, dict) else {}
        cfg['boot']['brightness'] = _clamp(int(brightness), 0, 255)
        cfg['boot']['power'] = bool(power)
        self.save()
        return cfg['boot']


SETTINGS = Settings()
