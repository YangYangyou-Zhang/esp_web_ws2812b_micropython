#!/usr/bin/env python3
"""Run the ESP8266 lite firmware on desktop CPython with stubs.

    python tools/sim_lite.py [--port 8002]

Only the listen port is rewritten; the rest of esp8266_lite/main.py runs as-is.
"""
import argparse
import gc
import os
import shutil
import sys
import time
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LITE = os.path.join(ROOT, 'firmware', 'esp8266_lite')
SIM = os.path.join(ROOT, '.sim_lite')


def stub():
    machine = types.ModuleType('machine')

    class Pin:
        OUT = 1

        def __init__(self, num, mode=None):
            self.num = num

    class _Reset(Exception):
        pass

    machine.Pin = Pin
    machine.reset = lambda: (_ for _ in ()).throw(_Reset())
    sys.modules['machine'] = machine

    neopixel = types.ModuleType('neopixel')

    class NeoPixel:
        frames = 0

        def __init__(self, pin, n, bpp=3):
            self.pin = pin
            self.n = n
            self.buf = [(0, 0, 0)] * n

        def __setitem__(self, i, v):
            if 0 <= i < self.n:
                self.buf[i] = v

        def __getitem__(self, i):
            return self.buf[i]

        def write(self):
            NeoPixel.frames += 1

    neopixel.NeoPixel = NeoPixel
    sys.modules['neopixel'] = neopixel

    network = types.ModuleType('network')
    network.AP_IF = 2
    network.AUTH_OPEN = 0
    network.AUTH_WPA_PSK = 2
    network.AUTH_WPA2_PSK = 3
    network.AUTH_WPA_WPA2_PSK = 4

    class WLAN:
        def __init__(self, iface):
            self.iface = iface
            self._active = False

        def active(self, v=None):
            if v is None:
                return self._active
            self._active = bool(v)

        def config(self, key=None, **kw):
            if key:
                return {'essid': 'ESP_LITE_SIM'}.get(key)
            return None

        def ifconfig(self):
            return ('127.0.0.1', '255.0.0.0', '127.0.0.1', '8.8.8.8')

    network.WLAN = WLAN
    sys.modules['network'] = network

    time.ticks_ms = lambda: int(time.monotonic() * 1000)
    time.ticks_diff = lambda a, b: a - b
    time.sleep_ms = lambda ms: time.sleep(ms / 1000.0)
    gc.mem_free = lambda: 28000
    sys.platform = 'esp8266'


def prepare(port):
    os.makedirs(SIM, exist_ok=True)
    shutil.copy2(os.path.join(LITE, 'lite.html'), os.path.join(SIM, 'lite.html'))
    src = open(os.path.join(LITE, 'main.py'), encoding='utf-8').read()
    src = src.replace('PORT = 80', 'PORT = %d' % port, 1)
    src = src.replace('DNS_PORT = 53', 'DNS_PORT = 15353', 1)
    with open(os.path.join(SIM, 'main.py'), 'w', encoding='utf-8') as f:
        f.write(src)
    os.chdir(SIM)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8002)
    args = ap.parse_args()

    stub()
    prepare(args.port)
    print('lite simulator: http://127.0.0.1:%d/' % args.port)
    import runpy
    try:
        runpy.run_path('main.py', run_name='__main__')
    except KeyboardInterrupt:
        print('\nstopped')
    except Exception as e:
        if e.__class__.__name__ == '_Reset':
            print('\nmachine.reset() called')
        else:
            raise


if __name__ == '__main__':
    main()
