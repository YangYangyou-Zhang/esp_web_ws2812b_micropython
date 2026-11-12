# Minimal blocking-free HTTP server with JSON API.
import gc
import json
import os
import socket
import sys
import time

from machine import reset

from effects import EFFECTS
from engine import ENGINE
from settings import SETTINGS
from stylelib import STYLELIB

MAX_HEAD = 2048
MAX_JSON = 4096
MAX_SOURCE = 8192
DNS_PORT = 53

STATIC = {
    '/': ('www/index.html', 'text/html; charset=utf-8'),
    '/index.html': ('www/index.html', 'text/html; charset=utf-8'),
    '/app.css': ('www/app.css', 'text/css; charset=utf-8'),
    '/app.js': ('www/app.js', 'application/javascript; charset=utf-8'),
}

REASON = {200: 'OK', 204: 'No Content', 400: 'Bad Request',
          404: 'Not Found', 405: 'Method Not Allowed',
          413: 'Payload Too Large', 500: 'Internal Server Error'}

HEX_CHARS = '0123456789abcdefABCDEF'


class _PayloadTooLarge(Exception):
    pass


def _unquote(s):
    out = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == '%' and i + 2 < n:
            h = s[i + 1:i + 3]
            try:
                out.append(chr(int(h, 16)))
                i += 3
                continue
            except ValueError:
                pass
        out.append(ch)
        i += 1
    return ''.join(out)


def _hexid(b):
    out = ''
    for x in b:
        out += '%02x' % x
    return out


def _send_all(cl, data):
    mv = memoryview(data)
    while mv:
        n = cl.send(mv)
        if not n:
            raise OSError('send failed')
        mv = mv[n:]


class HttpServer:
    def __init__(self):
        self.sock = None
        self.port = 80
        self._req = 0
        self.dns = None
        self.portal_ip = '192.168.4.1'
        self.portal_bytes = b'\xc0\xa8\x04\x01'

    # ---- lifecycle --------------------------------------------------
    def start(self, port=80):
        addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]
        s = socket.socket()
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except OSError:
            pass
        s.bind(addr)
        s.listen(5)
        s.settimeout(0)
        self.sock = s
        self.port = port
        print('http server on 0.0.0.0:%d' % port)
        self._start_portal()

    def _start_portal(self):
        try:
            import network
            ip = network.WLAN(network.AP_IF).ifconfig()[0]
        except Exception:
            ip = '192.168.4.1'
        self.portal_ip = ip
        try:
            p = ip.split('.')
            self.portal_bytes = bytes((int(p[0]), int(p[1]),
                                       int(p[2]), int(p[3])))
        except Exception:
            self.portal_bytes = b'\xc0\xa8\x04\x01'
        try:
            d = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                d.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except OSError:
                pass
            d.bind(('0.0.0.0', DNS_PORT))
            d.settimeout(0)
            self.dns = d
            print('captive portal DNS on %s:%d' % (ip, DNS_PORT))
            ENGINE.log('portal DNS on %s:%d' % (ip, DNS_PORT))
        except OSError as e:
            self.dns = None
            print('captive portal DNS disabled:', e)
            ENGINE.log('portal DNS disabled: %s' % e)

    def _poll_dns(self):
        if self.dns is None:
            return
        for _ in range(4):
            try:
                data, addr = self.dns.recvfrom(512)
            except OSError:
                return
            try:
                reply = self._dns_reply(data)
                if reply:
                    self.dns.sendto(reply, addr)
            except Exception:
                pass

    def _dns_reply(self, data):
        if len(data) < 17:
            return None
        if ((data[4] << 8) | data[5]) != 1:
            return None
        i = 12
        n = len(data)
        while i < n:
            ln = data[i]
            if ln == 0:
                i += 1
                break
            if ln & 0xC0:
                i += 2
                break
            i += ln + 1
            if i >= n:
                return None
        if i + 4 > n:
            return None
        qtype = (data[i] << 8) | data[i + 1]
        qend = i + 4
        head = data[0:2] + b'\x81\x80\x00\x01'
        if qtype == 1:
            return (head + b'\x00\x01\x00\x00\x00\x00' + data[12:qend] +
                    b'\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04' +
                    self.portal_bytes)
        return head + b'\x00\x00\x00\x00\x00\x00' + data[12:qend]

    def poll(self, timeout_ms=0):
        if self.sock is None:
            return False
        self._poll_dns()
        handled = False
        for _ in range(6):
            try:
                self.sock.settimeout(0)
            except OSError:
                return handled
            try:
                cl, _ = self.sock.accept()
            except OSError:
                return handled
            handled = True
            try:
                cl.settimeout(0.5)
            except OSError:
                pass
            try:
                self._handle(cl)
            except Exception as e:
                print('request error:', e)
                try:
                    self._json(cl, 500, {'ok': False, 'error': str(e)})
                except Exception:
                    pass
            finally:
                try:
                    cl.close()
                except OSError:
                    pass
        if handled:
            gc.collect()
        return handled

    # ---- primitives -------------------------------------------------
    def _send(self, cl, code, ctype, body, extra=''):
        if isinstance(body, str):
            body = body.encode()
        head = ('HTTP/1.1 %d %s\r\nContent-Type: %s\r\n'
                'Content-Length: %d\r\nConnection: close\r\n'
                'Cache-Control: no-store\r\n%s\r\n') % (
                    code, REASON.get(code, 'OK'), ctype, len(body), extra)
        _send_all(cl, head.encode())
        if body:
            _send_all(cl, body)

    def _json(self, cl, code, obj):
        self._send(cl, code, 'application/json; charset=utf-8',
                   json.dumps(obj))

    def _error(self, cl, code, msg):
        self._json(cl, code, {'ok': False, 'error': str(msg)})

    def _read_head(self, cl):
        data = b''
        while b'\r\n\r\n' not in data:
            try:
                chunk = cl.recv(256)
            except OSError:
                return None
            if not chunk:
                return None
            data += chunk
            if len(data) > MAX_HEAD:
                return None
        head, _, rest = data.partition(b'\r\n\r\n')
        lines = head.split(b'\r\n')
        first = lines[0].decode().split(' ')
        if len(first) < 2:
            return None
        headers = {}
        for line in lines[1:]:
            if b':' in line:
                k, v = line.split(b':', 1)
                headers[k.strip().lower().decode()] = v.strip().decode()
        return first[0].upper(), first[1], headers, rest

    def _read_body(self, cl, headers, rest, limit):
        try:
            n = int(headers.get('content-length', '0'))
        except ValueError:
            n = 0
        if n > limit:
            left = n - len(rest)
            if n <= limit * 8:
                while left > 0:
                    chunk = cl.recv(min(512, left))
                    if not chunk:
                        break
                    left -= len(chunk)
            raise _PayloadTooLarge()
        body = rest
        while len(body) < n:
            try:
                chunk = cl.recv(min(512, n - len(body)))
            except OSError:
                break
            if not chunk:
                break
            body += chunk
        return body[:n]

    # ---- static -----------------------------------------------------
    def _send_file(self, cl, fname, ctype):
        try:
            size = os.stat(fname)[6]
            f = open(fname, 'rb')
        except OSError:
            return False
        head = ('HTTP/1.1 200 OK\r\nContent-Type: %s\r\n'
                'Content-Length: %d\r\nConnection: close\r\n'
                'Cache-Control: no-store\r\n\r\n') % (ctype, size)
        _send_all(cl, head.encode())
        try:
            while True:
                chunk = f.read(512)
                if not chunk:
                    break
                _send_all(cl, chunk)
        finally:
            f.close()
        return True

    def _serve_static(self, cl, path):
        if path == '/favicon.ico':
            self._send(cl, 204, 'text/plain', b'')
            return
        entry = STATIC.get(path)
        if not entry:
            self._error(cl, 404, 'not found')
            return
        fname, ctype = entry
        if not self._send_file(cl, fname, ctype):
            self._error(cl, 404, 'asset missing')


    # ---- request ----------------------------------------------------
    def _handle(self, cl):
        parsed = self._read_head(cl)
        if not parsed:
            return
        try:
            cl.settimeout(2.0)
        except OSError:
            pass
        method, target, headers, rest = parsed
        host = headers.get('host', '')
        if host:
            host = host.split(':')[0].strip().lower()
            if host and host != self.portal_ip:
                self._redirect(cl)
                return
        target = target.split('#')[0]
        if '?' in target:
            path, query = target.split('?', 1)
        else:
            path, query = target, ''
        path = _unquote(path)
        self._req += 1
        try:
            if path.startswith('/api/'):
                self._api(cl, method, path, query, headers, rest)
            elif method in ('GET', 'HEAD'):
                self._serve_static(cl, path)
            else:
                self._error(cl, 405, 'method not allowed')
        except _PayloadTooLarge:
            self._error(cl, 413, 'body too large')
        except ValueError as e:
            self._error(cl, 400, e)
        except Exception as e:
            print('api error:', e)
            self._error(cl, 500, e)

    def _redirect(self, cl):
        head = ('HTTP/1.1 302 Found\r\nLocation: http://%s/\r\n'
                'Content-Length: 0\r\nConnection: close\r\n'
                'Cache-Control: no-store\r\n\r\n') % self.portal_ip
        _send_all(cl, head.encode())

    def _body_json(self, cl, headers, rest):
        body = self._read_body(cl, headers, rest, MAX_JSON)
        if not body:
            return {}
        return json.loads(body.decode())

    # ---- api --------------------------------------------------------
    def _api(self, cl, method, path, query, headers, rest):
        if path == '/api/state' and method == 'GET':
            self._json(cl, 200, {
                'ok': True,
                'device': self._device(),
                'settings': SETTINGS.get(),
                'runtime': ENGINE.state_dict(),
            })
            return

        if path == '/api/effects' and method == 'GET':
            if self._send_file(cl, 'www/effects.json',
                               'application/json; charset=utf-8'):
                return
            gc.collect()
            items = []
            for eid in EFFECTS.order:
                spec = EFFECTS.meta[eid]
                items.append({
                    'id': eid, 'name': spec['name'], 'desc': spec['desc'],
                    'anim': spec['anim'], 'params': spec['params'],
                })
            self._json(cl, 200, {'ok': True, 'effects': items})
            return

        if path == '/api/styles':
            if method == 'GET':
                gc.collect()
                self._json(cl, 200, {'ok': True,
                                     'styles': STYLELIB.list_styles()})
                return
            self._error(cl, 405, 'method not allowed')
            return

        if path.startswith('/api/styles/'):
            self._styles(cl, method, path[len('/api/styles/'):], headers, rest)
            return

        if path == '/api/apply' and method == 'POST':
            body = self._body_json(cl, headers, rest)
            sid = body.get('style_id')
            if not sid:
                raise ValueError('style_id required')
            try:
                style = ENGINE.apply_id(sid, body.get('params'))
            except Exception as e:
                raise ValueError(str(e))
            self._json(cl, 200, {'ok': True, 'style': style,
                                 'runtime': ENGINE.state_dict()})
            return

        if path == '/api/power' and method == 'POST':
            body = self._body_json(cl, headers, rest)
            on = bool(body.get('on'))
            ENGINE.set_power(on)
            self._json(cl, 200, {'ok': True, 'power': ENGINE.power})
            return

        if path == '/api/brightness' and method == 'POST':
            body = self._body_json(cl, headers, rest)
            ENGINE.set_brightness(body.get('value', 128))
            self._json(cl, 200, {'ok': True,
                                 'brightness': ENGINE.brightness})
            return

        if path == '/api/settings':
            if method == 'GET':
                self._json(cl, 200, {'ok': True, 'settings': SETTINGS.get()})
                return
            if method == 'PUT':
                body = self._body_json(cl, headers, rest)
                self._settings_put(cl, body)
                return
            self._error(cl, 405, 'method not allowed')
            return

        if path == '/api/save-boot' and method == 'POST':
            body = self._body_json(cl, headers, rest)
            sid = body.get('style_id')
            params = body.get('params')
            if not sid:
                raise ValueError('style_id required')
            try:
                STYLELIB.resolve(sid, params)
            except Exception as e:
                raise ValueError(str(e))
            boot = SETTINGS.set_boot(
                sid, params or {},
                body.get('brightness', ENGINE.brightness),
                body.get('power', True), 'preset')
            self._json(cl, 200, {'ok': True, 'boot': boot})
            return

        if path == '/api/colors':
            if method == 'GET':
                self._json(cl, 200, {'ok': True,
                                     'colors': STYLELIB.get_colors()})
                return
            if method == 'PUT':
                body = self._body_json(cl, headers, rest)
                colors = STYLELIB.set_colors(body.get('colors', []))
                self._json(cl, 200, {'ok': True, 'colors': colors})
                return
            self._error(cl, 405, 'method not allowed')
            return

        if path == '/api/log' and method == 'GET':
            self._json(cl, 200, {'ok': True, 'logs': ENGINE.logs})
            return

        if path == '/api/reboot' and method == 'POST':
            self._json(cl, 200, {'ok': True, 'rebooting': True})
            time.sleep_ms(200)
            reset()
            return

        self._error(cl, 404, 'unknown api')

    def _styles(self, cl, method, rest, headers, rest_body):
        is_py = rest.endswith('.py')
        sid = rest[:-3] if is_py else rest
        if not sid:
            self._error(cl, 400, 'style id required')
            return
        if method == 'GET':
            if is_py:
                src = STYLELIB.get_source(sid)
                if src is None:
                    self._error(cl, 404, 'source not found')
                    return
                self._send(cl, 200, 'text/plain; charset=utf-8', src)
                return
            st = STYLELIB.get_style(sid)
            if not st:
                self._error(cl, 404, 'style not found')
                return
            self._json(cl, 200, {'ok': True, 'style': st})
            return
        if method == 'PUT':
            if is_py:
                if sid.endswith('/'):
                    raise ValueError('bad id')
                src = self._read_body(cl, headers, rest_body, MAX_SOURCE)
                try:
                    text = src.decode()
                except Exception:
                    raise ValueError('source must be utf-8')
                STYLELIB.save_source(sid, text)
                self._json(cl, 200, {'ok': True, 'id': sid})
                return
            body = self._body_json(cl, headers, rest_body)
            try:
                st = STYLELIB.save_style(sid, body)
            except Exception as e:
                raise ValueError(str(e))
            self._json(cl, 200, {'ok': True, 'style': st})
            return
        if method == 'DELETE':
            ok = STYLELIB.delete_style(sid)
            if not ok:
                self._error(cl, 404, 'style not found')
                return
            self._json(cl, 200, {'ok': True})
            return
        self._error(cl, 405, 'method not allowed')

    def _settings_put(self, cl, patch):
        old = json.loads(json.dumps(SETTINGS.get()))
        merged = json.loads(json.dumps(old))
        if isinstance(patch, dict):
            for section in patch:
                if isinstance(patch[section], dict) and \
                        isinstance(merged.get(section), dict):
                    for k in patch[section]:
                        merged[section][k] = patch[section][k]
                else:
                    merged[section] = patch[section]
        clean = SETTINGS.sanitize(merged)
        reboot = False
        if clean['hardware']['pins'] != old['hardware']['pins']:
            reboot = True
        if clean['wifi']['ssid'] != old['wifi']['ssid'] or \
                clean['wifi']['password'] != old['wifi']['password']:
            reboot = True
        if clean['hardware']['leds'] != old['hardware']['leds']:
            try:
                ENGINE.reinit(leds=clean['hardware']['leds'])
            except Exception as e:
                SETTINGS.cfg = old
                raise ValueError('cannot apply LED count: %s' % e)
        if clean['render']['fps'] != old['render']['fps']:
            ENGINE.fps_target = clean['render']['fps']
        if clean['render']['brightness'] != old['render']['brightness']:
            ENGINE.set_brightness(clean['render']['brightness'])
        if clean['render']['color_order'] != old['render']['color_order']:
            ENGINE.color_order = clean['render']['color_order']
        SETTINGS.cfg = clean
        SETTINGS.save()
        self._json(cl, 200, {'ok': True, 'settings': SETTINGS.get(),
                             'reboot_required': reboot})

    def _device(self):
        d = {
            'platform': getattr(sys, 'platform', 'unknown'),
            'version': getattr(sys, 'version', ''),
        }
        try:
            d['machine'] = sys.implementation._machine
        except Exception:
            d['machine'] = getattr(sys, 'platform', 'unknown')
        try:
            import network
            ap = network.WLAN(network.AP_IF)
            d['ip'] = ap.ifconfig()[0]
            ssid = ap.config('essid')
            if isinstance(ssid, bytes):
                try:
                    ssid = ssid.decode()
                except Exception:
                    ssid = ''
            d['ssid'] = ssid
        except Exception:
            d['ip'] = '127.0.0.1'
            d['ssid'] = ''
        try:
            import machine
            d['chip_id'] = _hexid(machine.unique_id())
        except Exception:
            d['chip_id'] = ''
        return d


HTTPD = HttpServer()
