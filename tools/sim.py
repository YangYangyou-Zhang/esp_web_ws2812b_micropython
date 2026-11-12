#!/usr/bin/env python3
"""Run the firmware on desktop CPython with stubbed hardware.

    python tools/sim.py [--port 8000]

Serves the real www/ UI against the real engine/effects/httpd modules.
No LEDs are attached; frames are rendered but not transmitted.
"""
import argparse
import gc
import os
import shutil
import sys
import time
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FW = os.path.join(ROOT, 'firmware', 'esp32')
SIM = os.path.join(ROOT, '.sim')


def _stub_modules():
    machine = types.ModuleType('machine')

    class Pin:
        OUT = 1

        def __init__(self, num, mode=None):
            self.num = num

    class _Reset(Exception):
        pass

    def reset():
        raise _Reset('machine.reset() requested')

    machine.Pin = Pin
    machine.reset = reset
    machine.unique_id = lambda: b'\x01\x02\x03\x04\x05\x06'
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

        def fill(self, v):
            self.buf = [v] * self.n

    neopixel.NeoPixel = NeoPixel
    sys.modules['neopixel'] = neopixel

    network = types.ModuleType('network')
    network.AP_IF = 2
    network.STA_IF = 1

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
                return {'essid': 'ESP_SIM'}.get(key)
            return None

        def ifconfig(self):
            return ('127.0.0.1', '255.0.0.0', '127.0.0.1', '8.8.8.8')

    network.WLAN = WLAN
    sys.modules['network'] = network

    esp32 = types.ModuleType('esp32')

    class RMT:
        @staticmethod
        def bitstream_channel(v):
            return None

    esp32.RMT = RMT
    sys.modules['esp32'] = esp32

    time.ticks_ms = lambda: int(time.monotonic() * 1000)
    time.ticks_diff = lambda a, b: a - b
    time.ticks_add = lambda a, b: a + b
    time.sleep_ms = lambda ms: time.sleep(ms / 1000.0)
    gc.mem_free = lambda: 120000
    sys.platform = 'esp32'


def _prepare():
    os.makedirs(SIM, exist_ok=True)
    for sub in ('www', 'styles'):
        src = os.path.join(FW, sub)
        dst = os.path.join(SIM, sub)
        os.makedirs(dst, exist_ok=True)
        for name in os.listdir(src):
            s = os.path.join(src, name)
            if os.path.isfile(s):
                shutil.copy2(s, os.path.join(dst, name))
    os.makedirs(os.path.join(SIM, 'data'), exist_ok=True)
    os.chdir(SIM)
    if FW not in sys.path:
        sys.path.insert(0, FW)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8000)
    args = ap.parse_args()

    _stub_modules()
    _prepare()

    import settings
    import stylelib
    import engine
    import httpd

    httpd.DNS_PORT = 15353
    cfg = settings.SETTINGS.load()
    stylelib.STYLELIB.ensure_dirs()
    engine.ENGINE.init(cfg)
    engine.ENGINE.boot(cfg)
    httpd.HTTPD.start(args.port)
    print('simulator: http://127.0.0.1:%d/  (Ctrl+C to stop)' % args.port)

    last = time.monotonic()
    try:
        while True:
            httpd.HTTPD.poll(0)
            engine.ENGINE.tick()
            time.sleep(0.002)
            now = time.monotonic()
            if now - last >= 5.0:
                last = now
                print('fps=%s render=%sms power=%s style=%s' % (
                    engine.ENGINE.fps, engine.ENGINE.render_ms,
                    engine.ENGINE.power, engine.ENGINE.style_id))
    except KeyboardInterrupt:
        print('\nstopped')
    except Exception as e:
        if e.__class__.__name__ == '_Reset':
            print('\nmachine.reset() called')
        else:
            raise


if __name__ == '__main__':
    main()
