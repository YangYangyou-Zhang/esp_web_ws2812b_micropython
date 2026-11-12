# Style files (styles/*.json + styles/*.py) and the user colour palette.
import json
import os

from effects import EFFECTS

STYLE_DIR = 'styles'
COLORS_PATH = 'data/colors.json'
MAX_STYLE_FILE = 4096
MAX_SOURCE_FILE = 8192
MAX_COLORS = 24
HEX_CHARS = '0123456789abcdefABCDEF'


def _id_ok(s):
    if not isinstance(s, str) or not (1 <= len(s) <= 24):
        return False
    for ch in s:
        if not (('a' <= ch <= 'z') or ('0' <= ch <= '9') or
                ch == '_' or ch == '-'):
            return False
    return True


def _hex_ok(s):
    if not isinstance(s, str) or len(s) != 7 or s[0] != '#':
        return False
    for ch in s[1:]:
        if ch not in HEX_CHARS:
            return False
    return True


def _norm_hex(s):
    return '#' + s[1:].lower()


def _read_json(path, limit):
    try:
        if os.stat(path)[6] > limit:
            return None
        f = open(path)
        try:
            return json.loads(f.read())
        finally:
            f.close()
    except Exception:
        return None


def _atomic_write(path, text):
    tmp = path + '.tmp'
    f = open(tmp, 'w')
    try:
        f.write(text)
    finally:
        f.close()
    try:
        os.rename(tmp, path)
    except OSError:
        try:
            os.remove(path)
        except OSError:
            pass
        os.rename(tmp, path)


class StyleLib:
    def ensure_dirs(self):
        try:
            os.mkdir(STYLE_DIR)
        except OSError:
            pass

    # ---- validation -------------------------------------------------
    def _defs(self, defs):
        out = []
        if not isinstance(defs, (list, tuple)):
            return out
        for d in defs[:16]:
            if not isinstance(d, dict):
                continue
            key = d.get('key')
            if not isinstance(key, str) or not (1 <= len(key) <= 24):
                continue
            typ = d.get('type')
            if typ not in ('int', 'color', 'colors', 'bool', 'enum'):
                continue
            item = {
                'key': key,
                'type': typ,
                'label': self._label(d.get('label'), key),
            }
            if typ == 'int':
                lo = d.get('min', 0)
                hi = d.get('max', 100)
                if not isinstance(lo, int):
                    lo = 0
                if not isinstance(hi, int) or hi <= lo:
                    hi = lo + 100
                item['min'] = lo
                item['max'] = hi
                dv = d.get('default', lo)
                item['default'] = dv if isinstance(dv, int) else lo
            elif typ == 'bool':
                item['default'] = bool(d.get('default', False))
            elif typ == 'enum':
                opts = []
                raw = d.get('options')
                if isinstance(raw, (list, tuple)):
                    for o in raw[:8]:
                        if isinstance(o, dict) and 'value' in o:
                            opts.append({
                                'value': o['value'],
                                'label': self._label(o.get('label'), str(o['value'])),
                            })
                if not opts:
                    continue
                item['options'] = opts
                item['default'] = d.get('default', opts[0]['value'])
            out.append(item)
        return out

    def _label(self, label, fallback):
        if isinstance(label, dict):
            return {
                'zh': str(label.get('zh') or fallback),
                'en': str(label.get('en') or fallback),
            }
        if isinstance(label, str) and label:
            return {'zh': label, 'en': label}
        return {'zh': fallback, 'en': fallback}

    def validate(self, obj, style_id):
        if not isinstance(obj, dict):
            raise ValueError('style must be an object')
        typ = obj.get('type', 'builtin')
        name = obj.get('name')
        if not isinstance(name, str) or not (1 <= len(name) <= 32):
            raise ValueError('name must be 1..32 chars')
        out = {'schema': 1, 'id': style_id, 'name': name, 'type': typ}
        params = obj.get('params')
        params = params if isinstance(params, dict) else {}
        if typ == 'builtin':
            effect = obj.get('effect')
            if effect not in EFFECTS.meta:
                raise ValueError('unknown effect: %s' % effect)
            out['effect'] = effect
            out['params'] = EFFECTS.normalize(effect, params)
            out['param_defs'] = EFFECTS.param_defs(effect)
        elif typ == 'python':
            module = obj.get('module', style_id)
            if not _id_ok(module):
                raise ValueError('invalid module id')
            out['module'] = module
            out['params'] = params
            out['param_defs'] = self._defs(obj.get('param_defs'))
        else:
            raise ValueError('type must be builtin or python')
        return out

    # ---- files ------------------------------------------------------
    def list_styles(self):
        self.ensure_dirs()
        out = []
        try:
            names = os.listdir(STYLE_DIR)
        except OSError:
            return out
        for fn in names:
            if not fn.endswith('.json'):
                continue
            sid = fn[:-5]
            if not _id_ok(sid):
                continue
            st = self.get_style(sid)
            if st:
                out.append({
                    'id': sid,
                    'name': st.get('name', sid),
                    'type': st.get('type', 'builtin'),
                    'effect': st.get('effect'),
                    'module': st.get('module'),
                    'params': st.get('params', {}),
                    'param_defs': st.get('param_defs', []),
                })
        out.sort(key=lambda s: s['name'])
        return out

    def get_style(self, sid):
        if not _id_ok(sid):
            return None
        obj = _read_json('%s/%s.json' % (STYLE_DIR, sid), MAX_STYLE_FILE)
        if not obj:
            return None
        try:
            return self.validate(obj, sid)
        except Exception:
            return None

    def save_style(self, sid, obj):
        if not _id_ok(sid):
            raise ValueError('invalid style id')
        st = self.validate(obj, sid)
        _atomic_write('%s/%s.json' % (STYLE_DIR, sid), json.dumps(st))
        return st

    def delete_style(self, sid):
        if not _id_ok(sid):
            raise ValueError('invalid style id')
        removed = False
        for path in ('%s/%s.json' % (STYLE_DIR, sid),
                     '%s/%s.py' % (STYLE_DIR, sid)):
            try:
                os.remove(path)
                removed = True
            except OSError:
                pass
        return removed

    def get_source(self, sid):
        if not _id_ok(sid):
            return None
        try:
            if os.stat('%s/%s.py' % (STYLE_DIR, sid))[6] > MAX_SOURCE_FILE:
                return None
            f = open('%s/%s.py' % (STYLE_DIR, sid))
            try:
                return f.read()
            finally:
                f.close()
        except OSError:
            return None

    def save_source(self, sid, src):
        if not _id_ok(sid):
            raise ValueError('invalid style id')
        if not isinstance(src, str) or len(src) > MAX_SOURCE_FILE:
            raise ValueError('source too large')
        _atomic_write('%s/%s.py' % (STYLE_DIR, sid), src)

    # ---- palette ----------------------------------------------------
    def get_colors(self):
        obj = _read_json(COLORS_PATH, 2048)
        out = []
        if isinstance(obj, dict):
            obj = obj.get('colors')
        if isinstance(obj, (list, tuple)):
            for c in obj:
                if _hex_ok(c):
                    c = _norm_hex(c)
                    if c not in out:
                        out.append(c)
        return out[:MAX_COLORS]

    def set_colors(self, colors):
        if not isinstance(colors, (list, tuple)):
            raise ValueError('colors must be a list')
        clean = []
        for c in colors[:MAX_COLORS]:
            if _hex_ok(c):
                c = _norm_hex(c)
                if c not in clean:
                    clean.append(c)
        self.ensure_dirs()
        _atomic_write(COLORS_PATH, json.dumps({'colors': clean}))
        return clean

    # ---- resolve ----------------------------------------------------
    def resolve(self, style_id, override=None):
        override = override if isinstance(override, dict) else {}
        if style_id.startswith('builtin:'):
            effect = style_id[8:]
            if effect not in EFFECTS.meta:
                raise ValueError('unknown effect: %s' % effect)
            params = EFFECTS.normalize(effect, override)
            return {
                'id': style_id,
                'name': EFFECTS.display_name(effect),
                'type': 'builtin',
                'effect': effect,
                'params': params,
                'param_defs': EFFECTS.param_defs(effect),
            }
        st = self.get_style(style_id)
        if not st:
            raise ValueError('unknown style: %s' % style_id)
        if override:
            merged = dict(st.get('params', {}))
            for k in override:
                merged[k] = override[k]
            st['params'] = merged
        return st


STYLELIB = StyleLib()
