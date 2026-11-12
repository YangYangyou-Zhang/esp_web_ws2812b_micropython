# ESP8266 Lite - WS2812B web controller (MicroPython)
#
# Author: 洋洋柚 (Bilibili/Douyin: 洋洋柚Y) - License: CC BY-NC-SA 4.0 (NonCommercial)
# Project: https://github.com/YangYangyou-Zhang/esp_web_ws2812b_micropython
#          https://gitee.com/zhangyangyangyou/esp_web_ws2812b_micropython
# Video:   https://www.bilibili.com/video/BV1zz5zzFEbM
#
# Upload this file as main.py and lite.html to the board root.
# Tested target: ESP8266 with MicroPython 1.19+ / 4 MB flash.
#
# Limits: one strip, 6 effects, no custom styles, no JSON API.
# The full-featured firmware is the project root (ESP32 family only).

import gc
import math
import os
import socket
import time

import machine
import network
import neopixel
from machine import Pin

SSID = 'ESP_WS2812B_BY_YYY'
PASSWORD = '12345678'
PORT = 80
CFG_PATH = 'lite.cfg'
UI_PATH = 'lite.html'
FPS_TARGET = 30
DNS_PORT = 53
PORTAL_IP = '192.168.4.1'
PORTAL_BYTES = b'\xc0\xa8\x04\x01'

EFFECTS = ('solid', 'breath', 'rainbow', 'chase', 'comet', 'fire')
DEFAULTS = {
    'leds': '30',
    'pin': '2',
    'bright': '128',
    'boot': 'rainbow',
    'color': 'ff6600',
    'speed': '40',
}

CFG = {}
NP = None
N = 30
STRIP_PIN = 2
BRIGHT = 128
POWER = True
EFFECT = 'rainbow'
SPEED = 40
COLOR = (255, 102, 0)
COLOR_HEX = 'ff6600'
T0 = 0
LAST = 0
STATE = None
RAINBOW = None
FIRE_LUT = None
RNG = 12345
FPS = 0
FCNT = 0
FMARK = 0
FPSMS = 0
BOOT_MS = 0
SOCK = None
DNS = None


def clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def rnd():
    global RNG
    RNG = (RNG * 1103515245 + 12345) & 0x7fffffff
    return RNG


def parse_hex(s):
    if not s or len(s) != 6:
        return None
    try:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    except ValueError:
        return None


def scale(c, k):
    return (c[0] * k // 255, c[1] * k // 255, c[2] * k // 255)


def hsv(h, s, v):
    h = h % 1.0
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


# ---- config ---------------------------------------------------------

def save_cfg():
    tmp = CFG_PATH + '.tmp'
    try:
        f = open(tmp, 'w')
        try:
            for k in ('leds', 'pin', 'bright', 'boot', 'color', 'speed'):
                f.write('%s=%s\n' % (k, CFG.get(k, DEFAULTS[k])))
        finally:
            f.close()
        try:
            os.rename(tmp, CFG_PATH)
        except OSError:
            try:
                os.remove(CFG_PATH)
            except OSError:
                pass
            os.rename(tmp, CFG_PATH)
    except OSError as e:
        print('cfg save failed:', e)


def cfg_int(key):
    try:
        return int(CFG.get(key, DEFAULTS[key]))
    except Exception:
        return int(DEFAULTS[key])


def load_cfg():
    global CFG
    CFG = dict(DEFAULTS)
    try:
        f = open(CFG_PATH)
        try:
            for line in f:
                line = line.strip()
                if '=' in line:
                    k, _, v = line.partition('=')
                    if k in DEFAULTS:
                        CFG[k] = v.strip()
        finally:
            f.close()
    except OSError:
        save_cfg()
    CFG['leds'] = str(clamp(cfg_int('leds'), 1, 300))
    CFG['pin'] = str(clamp(cfg_int('pin'), 0, 16))
    CFG['bright'] = str(clamp(cfg_int('bright'), 0, 255))
    CFG['speed'] = str(clamp(cfg_int('speed'), 1, 100))
    if CFG['boot'] != 'off' and CFG['boot'] not in EFFECTS:
        CFG['boot'] = 'rainbow'
    if parse_hex(CFG['color']) is None:
        CFG['color'] = 'ff6600'


# ---- strip ----------------------------------------------------------

def init_strip(leds, pin):
    global NP, N, STRIP_PIN, STATE
    np = neopixel.NeoPixel(Pin(pin, Pin.OUT), leds)
    NP = np
    N = leds
    STRIP_PIN = pin
    STATE = None
    gc.collect()


def clear_strip():
    c = (0, 0, 0)
    for i in range(N):
        NP[i] = c
    NP.write()


def apply_cfg():
    global BRIGHT, EFFECT, SPEED, COLOR, COLOR_HEX, POWER, T0, LAST
    try:
        init_strip(cfg_int('leds'), cfg_int('pin'))
    except Exception as e:
        print('strip init failed, fallback to GPIO2/30:', e)
        CFG['leds'] = '30'
        CFG['pin'] = '2'
        init_strip(30, 2)
    BRIGHT = cfg_int('bright')
    SPEED = cfg_int('speed')
    COLOR = parse_hex(CFG['color'])
    COLOR_HEX = CFG['color']
    boot = CFG['boot']
    if boot == 'off':
        EFFECT = 'rainbow'
        POWER = False
        clear_strip()
    else:
        EFFECT = boot
        POWER = True
        T0 = time.ticks_ms()
        LAST = 0


# ---- effects --------------------------------------------------------

def rainbow_lut():
    global RAINBOW
    if RAINBOW is None:
        RAINBOW = [hsv(i / 48.0, 1.0, 1.0) for i in range(48)]
    return RAINBOW


def fire_lut():
    global FIRE_LUT
    if FIRE_LUT is None:
        pal = ((0, 0, 0), (140, 10, 0), (255, 110, 0), (255, 230, 120))
        out = []
        for i in range(32):
            j = i * 3 // 32
            f = (i * 3 / 32.0) - j
            a = pal[j]
            b = pal[j + 1]
            out.append((
                int(a[0] + (b[0] - a[0]) * f),
                int(a[1] + (b[1] - a[1]) * f),
                int(a[2] + (b[2] - a[2]) * f),
            ))
        FIRE_LUT = out
    return FIRE_LUT


def render(t):
    n = N
    np = NP
    b = BRIGHT
    c = COLOR
    fx = EFFECT

    if fx == 'solid':
        cc = scale(c, b)
        for i in range(n):
            np[i] = cc
        return

    if fx == 'breath':
        v = (math.sin(t * SPEED * 0.12) + 1.0) * 0.5
        cc = scale(c, int(b * (0.04 + 0.96 * v)))
        for i in range(n):
            np[i] = cc
        return

    if fx == 'rainbow':
        lut = rainbow_lut()
        off = int(t * SPEED * 0.15)
        for i in range(n):
            cc = lut[(i * 48 // n + off) % 48]
            np[i] = (cc[0] * b // 255, cc[1] * b // 255, cc[2] * b // 255)
        return

    if fx == 'chase':
        period = 9
        pos = int(t * SPEED * 0.2) % period
        cc = scale(c, b)
        black = (0, 0, 0)
        for i in range(n):
            np[i] = cc if ((i - pos) % period) < 3 else black
        return

    if fx == 'comet':
        head = int(t * SPEED * 0.3) % n
        tail = 10
        if tail > n:
            tail = n
        black = (0, 0, 0)
        for i in range(n):
            d = (head - i) % n
            if d < tail:
                np[i] = scale(c, b * (tail - d) // tail)
            else:
                np[i] = black
        return

    # fire
    global STATE
    if STATE is None or len(STATE) != n:
        STATE = bytearray(n)
    heat = STATE
    cool = 2 + (100 - SPEED) // 15
    for i in range(n):
        v = heat[i] - (rnd() % (cool + 1))
        heat[i] = v if v > 0 else 0
    for i in range(n - 1, 1, -1):
        heat[i] = (heat[i - 1] + heat[i - 2] * 2) // 3
    if rnd() % 255 < SPEED * 2:
        heat[rnd() % n] = 255
    lut = fire_lut()
    for i in range(n):
        cc = lut[heat[i] >> 3]
        np[i] = (cc[0] * b // 255, cc[1] * b // 255, cc[2] * b // 255)


def apply_effect(effect, speed, color):
    global EFFECT, SPEED, COLOR, COLOR_HEX, POWER, T0, STATE, LAST
    changed = effect in EFFECTS and effect != EFFECT
    if changed:
        EFFECT = effect
        STATE = None
        T0 = time.ticks_ms()
    if speed:
        try:
            SPEED = clamp(int(speed), 1, 100)
        except ValueError:
            pass
    if color:
        cc = parse_hex(color)
        if cc:
            COLOR = cc
            COLOR_HEX = color.lower()
    POWER = True
    LAST = 0


def power_on():
    global POWER, T0, LAST
    POWER = True
    T0 = time.ticks_ms()
    LAST = 0


def power_off():
    global POWER
    POWER = False
    clear_strip()


def set_bright(v):
    global BRIGHT
    BRIGHT = clamp(int(v), 0, 255)


def tick():
    global LAST, FCNT, FMARK, FPS, FPSMS
    if not POWER:
        return
    now = time.ticks_ms()
    if LAST and time.ticks_diff(now, LAST) < 1000 // FPS_TARGET:
        return
    LAST = now
    start = time.ticks_ms()
    render(time.ticks_diff(now, T0) / 1000.0)
    NP.write()
    FPSMS = time.ticks_diff(time.ticks_ms(), start)
    FCNT += 1
    if time.ticks_diff(now, FMARK) >= 1000:
        FPS = FCNT
        FCNT = 0
        FMARK = now


# ---- http -----------------------------------------------------------

def send_all(cl, data):
    mv = memoryview(data)
    while mv:
        n = cl.send(mv)
        if n is None or n <= 0:
            raise OSError('send')
        mv = mv[n:]


def http_send(cl, code, ctype, body):
    if isinstance(body, str):
        body = body.encode()
    head = ('HTTP/1.1 %d %s\r\nContent-Type: %s\r\nContent-Length: %d\r\n'
            'Connection: close\r\nCache-Control: no-store\r\n\r\n') % (
                code, 'OK' if code == 200 else 'Error', ctype, len(body))
    send_all(cl, head.encode())
    if body:
        send_all(cl, body)


def http_redirect(cl):
    head = ('HTTP/1.1 302 Found\r\nLocation: http://%s/\r\n'
            'Content-Length: 0\r\nConnection: close\r\n'
            'Cache-Control: no-store\r\n\r\n') % PORTAL_IP
    send_all(cl, head.encode())


def http_file(cl):
    try:
        size = os.stat(UI_PATH)[6]
        f = open(UI_PATH, 'rb')
    except OSError:
        http_send(cl, 404, 'text/plain', 'lite.html missing')
        return
    head = ('HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n'
            'Content-Length: %d\r\nConnection: close\r\n'
            'Cache-Control: no-store\r\n\r\n') % size
    send_all(cl, head.encode())
    try:
        while True:
            chunk = f.read(384)
            if not chunk:
                break
            send_all(cl, chunk)
    finally:
        f.close()


def state_json():
    return ('{"ok":1,"power":%d,"bright":%d,"leds":%d,"pin":%d,'
            '"effect":"%s","speed":%d,"color":"%s","boot":"%s",'
            '"fps":%d,"ms":%d,"heap":%d,"uptime":%d}') % (
                POWER, BRIGHT, N, STRIP_PIN, EFFECT, SPEED, COLOR_HEX,
                CFG['boot'], FPS, FPSMS, gc.mem_free(),
                time.ticks_diff(time.ticks_ms(), BOOT_MS) // 1000)


def parse_query(q):
    out = {}
    for part in q.split('&'):
        if '=' in part:
            k, _, v = part.partition('=')
            out[k] = v
    return out


def handle(cl):
    data = b''
    while b'\r\n\r\n' not in data:
        try:
            chunk = cl.recv(256)
        except OSError:
            return
        if not chunk:
            break
        data += chunk
        if len(data) > 1024:
            break
    try:
        cl.settimeout(2.0)
    except OSError:
        pass
    host = ''
    for hline in data.split(b'\r\n'):
        if hline.lower().startswith(b'host:'):
            host = hline[5:].strip().decode()
            if ':' in host:
                host = host.split(':')[0]
            host = host.lower()
            break
    if host and host != PORTAL_IP:
        http_redirect(cl)
        return
    line = data.split(b'\r\n', 1)[0]
    try:
        parts = line.decode().split(' ')
        target = parts[1]
    except Exception:
        return
    if '?' in target:
        path, q = target.split('?', 1)
    else:
        path, q = target, ''
    p = parse_query(q)

    if path == '/' or path == '/index.html':
        http_file(cl)
        return
    if path == '/favicon.ico':
        http_send(cl, 204, 'text/plain', b'')
        return
    if path == '/api/state':
        http_send(cl, 200, 'application/json', state_json())
        return
    if path == '/api/apply':
        apply_effect(p.get('effect', ''), p.get('speed'), p.get('color'))
        http_send(cl, 200, 'application/json', state_json())
        return
    if path == '/api/power':
        if p.get('on') == '1':
            power_on()
        else:
            power_off()
        http_send(cl, 200, 'application/json', state_json())
        return
    if path == '/api/bright':
        try:
            set_bright(int(p.get('value', BRIGHT)))
            CFG['bright'] = str(BRIGHT)
            save_cfg()
        except ValueError:
            pass
        http_send(cl, 200, 'application/json', state_json())
        return
    if path == '/api/save':
        save_settings(p)
        http_send(cl, 200, 'application/json', state_json())
        return
    if path == '/api/reboot':
        http_send(cl, 200, 'application/json', '{"ok":1}')
        time.sleep_ms(200)
        machine.reset()
        return
    http_send(cl, 404, 'application/json', '{"ok":0}')


def save_settings(p):
    global CFG, SPEED, COLOR, COLOR_HEX
    leds = p.get('leds')
    pin = p.get('pin')
    try:
        nl = int(leds) if leds else N
        npin = int(pin) if pin is not None else STRIP_PIN
    except ValueError:
        return
    nl = clamp(nl, 1, 300)
    npin = clamp(npin, 0, 16)
    if nl != N or npin != STRIP_PIN:
        try:
            init_strip(nl, npin)
        except Exception as e:
            print('strip init failed:', e)
            return
    CFG['leds'] = str(nl)
    CFG['pin'] = str(npin)
    if 'boot' in p:
        b = p['boot']
        if b == 'off' or b in EFFECTS:
            CFG['boot'] = b
    if 'speed' in p:
        try:
            SPEED = clamp(int(p['speed']), 1, 100)
            CFG['speed'] = str(SPEED)
        except ValueError:
            pass
    if 'color' in p and len(p['color']) == 6 and parse_hex(p['color']):
        CFG['color'] = p['color'].lower()
        COLOR = parse_hex(CFG['color'])
        COLOR_HEX = CFG['color']
    if 'bright' in p:
        try:
            set_bright(int(p['bright']))
            CFG['bright'] = str(BRIGHT)
        except ValueError:
            pass
    save_cfg()


def start_dns():
    global DNS
    try:
        d = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            d.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except OSError:
            pass
        d.bind(('0.0.0.0', DNS_PORT))
        d.settimeout(0)
        DNS = d
        print('portal dns on', DNS_PORT)
    except OSError as e:
        DNS = None
        print('portal dns disabled:', e)


def dns_reply(data):
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
                PORTAL_BYTES)
    return head + b'\x00\x00\x00\x00\x00\x00' + data[12:qend]


def poll_dns():
    if DNS is None:
        return
    for _ in range(4):
        try:
            data, addr = DNS.recvfrom(512)
        except OSError:
            return
        try:
            reply = dns_reply(data)
            if reply:
                DNS.sendto(reply, addr)
        except Exception:
            pass


def poll():
    poll_dns()
    handled = False
    for _ in range(4):
        try:
            SOCK.settimeout(0)
            cl, _ = SOCK.accept()
        except OSError:
            return handled
        handled = True
        try:
            cl.settimeout(0.5)
            handle(cl)
        except Exception as e:
            print('http error:', e)
        finally:
            try:
                cl.close()
            except OSError:
                pass
    return handled


# ---- boot -----------------------------------------------------------

def start_ap():
    global PORTAL_IP, PORTAL_BYTES
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    try:
        ap.config(essid=SSID, password=PASSWORD,
                  authmode=network.AUTH_WPA2_PSK)
    except Exception as e:
        print('AP config failed:', e)
        try:
            ap.config(essid=SSID, password=PASSWORD,
                      authmode=network.AUTH_WPA_WPA2_PSK)
        except Exception:
            try:
                ap.config(essid=SSID)
            except Exception:
                pass
    start = time.ticks_ms()
    while not ap.active():
        if time.ticks_diff(time.ticks_ms(), start) > 10000:
            break
        time.sleep_ms(200)
    try:
        ip = ap.ifconfig()[0]
    except Exception:
        ip = '192.168.4.1'
    PORTAL_IP = ip
    try:
        p = ip.split('.')
        PORTAL_BYTES = bytes((int(p[0]), int(p[1]), int(p[2]), int(p[3])))
    except Exception:
        pass
    print('AP:', SSID, 'http://%s/' % ip)


def start_http():
    global SOCK
    addr = socket.getaddrinfo('0.0.0.0', PORT)[0][-1]
    s = socket.socket()
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except OSError:
        pass
    s.bind(addr)
    s.listen(4)
    s.settimeout(0)
    SOCK = s
    print('http on', PORT)
    start_dns()


def run():
    global BOOT_MS, FMARK, T0
    try:
        machine.freq(160000000)
    except Exception:
        pass
    load_cfg()
    apply_cfg()
    gc.collect()
    BOOT_MS = time.ticks_ms()
    FMARK = BOOT_MS
    T0 = BOOT_MS
    start_ap()
    start_http()
    last_gc = time.ticks_ms()
    while True:
        handled = poll()
        tick()
        if not handled:
            time.sleep_ms(1)
        now = time.ticks_ms()
        if time.ticks_diff(now, last_gc) > 3000:
            gc.collect()
            last_gc = now


if __name__ == '__main__':
    run()
