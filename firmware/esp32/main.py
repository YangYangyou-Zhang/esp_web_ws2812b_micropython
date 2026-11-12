# ESP Web WS2812B - entry point.
# Author: 洋洋柚 (Bilibili/Douyin: 洋洋柚Y) - License: CC BY-NC-SA 4.0 (NonCommercial)
# Project: https://github.com/YangYangyou-Zhang/esp_web_ws2812b_micropython
#          https://gitee.com/zhangyangyangyou/esp_web_ws2812b_micropython
# Video:   https://www.bilibili.com/video/BV1zz5zzFEbM
import gc
import time

import network

from engine import ENGINE
from httpd import HTTPD
from settings import SETTINGS
from stylelib import STYLELIB


def set_freq():
    try:
        import machine
        if machine.freq() != 240000000:
            machine.freq(240000000)
    except Exception:
        pass


def setup_rmt():
    try:
        import esp32
    except ImportError:
        return
    try:
        esp32.RMT.bitstream_channel(0)
    except Exception as e:
        print('RMT setup skipped:', e)


def start_ap(wifi):
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    try:
        ap.config(essid=wifi['ssid'], password=wifi['password'],
                  authmode=network.AUTH_WPA2_PSK)
    except Exception as e:
        print('AP config failed:', e)
        try:
            ap.config(essid=wifi['ssid'], authmode=network.AUTH_OPEN)
        except Exception:
            pass
    start = time.ticks_ms()
    while not ap.active():
        if time.ticks_diff(time.ticks_ms(), start) > 10000:
            print('AP start timeout')
            break
        time.sleep_ms(200)
    try:
        ip = ap.ifconfig()[0]
    except Exception:
        ip = '192.168.4.1'
    print('AP:', wifi['ssid'], 'http://%s/' % ip)
    return ip


def run():
    set_freq()
    cfg = SETTINGS.load()
    STYLELIB.ensure_dirs()
    setup_rmt()
    try:
        ENGINE.init(cfg)
    except Exception as e:
        print('engine init failed:', e)
        ENGINE.log('engine init failed: %s' % e)
        try:
            ENGINE.reinit(leds=30, pins=[2])
        except Exception as e2:
            print('fallback failed:', e2)
    ENGINE.boot(cfg)
    start_ap(cfg['wifi'])
    HTTPD.start(80)
    gc.collect()
    print('free mem:', gc.mem_free() if hasattr(gc, 'mem_free') else '?')
    last_gc = time.ticks_ms()
    while True:
        handled = HTTPD.poll(0)
        ENGINE.tick()
        if not handled:
            time.sleep_ms(1)
        now = time.ticks_ms()
        if time.ticks_diff(now, last_gc) > 3000:
            gc.collect()
            last_gc = now


if __name__ == '__main__':
    run()
