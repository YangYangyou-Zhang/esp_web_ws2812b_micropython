#!/usr/bin/env python3
"""Upload the firmware to a MicroPython board over USB using mpremote.

    pip install mpremote
    python tools/install.py COM5
    python tools/install.py COM5 --single
    python tools/install.py --port /dev/ttyACM0

Requires mpremote (`pip install mpremote`).
"""
import argparse
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FW = os.path.join(ROOT, 'firmware', 'esp32')
LITE = os.path.join(ROOT, 'firmware', 'esp8266_lite')
FILES = ['main.py', 'settings.py', 'effects.py', 'stylelib.py', 'engine.py', 'httpd.py']
DIRS = ['www', 'styles']


def mpremote_cmd():
    exe = shutil.which('mpremote')
    if exe:
        return [exe]
    try:
        import mpremote  # noqa: F401
        return [sys.executable, '-m', 'mpremote']
    except ImportError:
        print('mpremote not found. Install it with: pip install mpremote')
        sys.exit(1)


def run(base, args, ignore=False):
    cmd = base + (['connect', PORT] if PORT else []) + args
    print('>', ' '.join(cmd))
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        if not ignore:
            raise


def main():
    global PORT
    ap = argparse.ArgumentParser()
    ap.add_argument('port', nargs='?', default=None,
                    help='serial port, e.g. COM5 or /dev/ttyACM0 (omit for auto)')
    ap.add_argument('--single', action='store_true',
                    help='upload dist/main_single.py instead of the multi-file layout')
    ap.add_argument('--lite', action='store_true',
                    help='upload the ESP8266 lite build (main.py + lite.html)')
    ap.add_argument('--reset', action='store_true', help='reset the board when done')
    args = ap.parse_args()
    if args.single and args.lite:
        print('choose either --single or --lite')
        sys.exit(1)
    PORT = args.port
    base = mpremote_cmd()

    if args.lite:
        run(base, ['fs', 'cp', os.path.join(LITE, 'main.py'), ':main.py'])
        run(base, ['fs', 'cp', os.path.join(LITE, 'lite.html'), ':lite.html'])
        print('uploaded ESP8266 lite build')
    elif args.single:
        src = os.path.join(ROOT, 'dist', 'main_single.py')
        if not os.path.exists(src):
            print('missing', src, '- run: python tools/build_single.py')
            sys.exit(1)
        run(base, ['fs', 'cp', src, ':main.py'])
        print('uploaded single-file build')
    else:
        for f in FILES:
            run(base, ['fs', 'cp', os.path.join(FW, f), ':' + f])
        for d in DIRS:
            run(base, ['fs', 'mkdir', ':' + d], ignore=True)
            for name in sorted(os.listdir(os.path.join(FW, d))):
                p = os.path.join(FW, d, name)
                if os.path.isfile(p):
                    run(base, ['fs', 'cp', p, ':%s/%s' % (d, name)])
        print('uploaded firmware + www + styles')

    if args.reset:
        run(base, ['reset'])


if __name__ == '__main__':
    main()
