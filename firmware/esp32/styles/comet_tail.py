# Rainbow comet - example Python style.
# The engine calls render() on every frame; keep it short.
NAME = "Rainbow Comet"
DEFAULTS = {"speed": 30, "tail": 10}


def render(t, n, params, out, h):
    head = int(t * params["speed"]) % n
    tail = params["tail"]
    for i in range(n):
        d = (head - i) % n
        if d < tail:
            v = 1.0 - d / tail
            c = h.hsv((i / 12.0 + t * 0.1) % 1.0, 1.0, v)
            out[i][0] = c[0]
            out[i][1] = c[1]
            out[i][2] = c[2]
        else:
            out[i][0] = 0
            out[i][1] = 0
            out[i][2] = 0
