#!/usr/bin/env python3
"""Generate firmware/esp32/www/effects.json from effects.py metadata.

    python tools/gen_effects.py

The device streams this file for GET /api/effects instead of building a large
JSON string at runtime (which can fail on a fragmented ESP32 heap). Re-run this
after adding or changing an effect.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FW = os.path.join(ROOT, 'firmware', 'esp32')
OUT = os.path.join(FW, 'www', 'effects.json')

sys.path.insert(0, FW)
import effects  # noqa: E402


def main():
    items = []
    for eid in effects.EFFECTS.order:
        spec = effects.META[eid]
        items.append({
            'id': eid,
            'name': spec['name'],
            'desc': spec['desc'],
            'anim': spec['anim'],
            'params': spec['params'],
        })
    data = {'ok': True, 'effects': items}
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    print('wrote %s (%d bytes, %d effects)' %
          (OUT, os.path.getsize(OUT), len(items)))


if __name__ == '__main__':
    main()
