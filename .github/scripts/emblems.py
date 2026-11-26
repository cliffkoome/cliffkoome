"""Draw the icons that cycle inside the profile card's ring.

Each icon is drawn as a greyscale image, shaded, then turned into the same
dither mosaic as the old portrait (square cells, ordered Bayer dither, four
ink levels). Run by hand when the icons change:

    uv run --with numpy --with pillow python .github/scripts/emblems.py

It writes assets/profile/emblems.svg: one <g> per area, in a 240x240 box, with
no colours of their own (cells are painted with url(#ink), which the card
defines per theme). profile.py places them and animates the cycle.
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw

BOX, STEP, SS = 240, 6, 4           # icon box, cell size, supersampling
OUT = "assets/profile/emblems.svg"

# (label, drawing function); the order is the order they cycle in
AREAS = []


def area(label):
    def wrap(fn):
        AREAS.append((label, fn))
        return fn
    return wrap


def s(*v):
    """Scale coordinates from the 240 box to the supersampled canvas."""
    return [x * SS for x in v]


@area("cybersecurity")
def shield(d):
    pts = [(120, 26), (192, 52), (190, 118), (168, 166), (120, 212), (72, 166), (50, 118), (48, 52)]
    d.polygon([tuple(s(*p)) for p in pts], fill=80, outline=None)
    d.line([tuple(s(*p)) for p in pts + pts[:1]], fill=255, width=13 * SS, joint="curve")
    d.ellipse(s(102, 84, 138, 120), fill=255)
    d.polygon([tuple(s(*p)) for p in [(110, 110), (130, 110), (136, 158), (104, 158)]], fill=255)


@area("hardware")
def chip(d):
    for k in range(4):
        o = 84 + k * 24
        for a, b in (((o - 5, 34), (o + 5, 70)), ((o - 5, 170), (o + 5, 206)),
                     ((34, o - 5), (70, o + 5)), ((170, o - 5), (206, o + 5))):
            d.rectangle(s(*a, *b), fill=230)
    d.rounded_rectangle(s(66, 66, 174, 174), radius=12 * SS, fill=80, outline=255, width=12 * SS)
    d.rectangle(s(98, 98, 142, 142), fill=255)


@area("frontend")
def browser(d):
    d.rounded_rectangle(s(26, 46, 214, 194), radius=14 * SS, fill=70, outline=255, width=11 * SS)
    d.rectangle(s(30, 50, 210, 76), fill=255)
    for x in (46, 64, 82):
        d.ellipse(s(x - 5, 58, x + 5, 68), fill=0)
    w = 11 * SS
    d.line([tuple(s(96, 104)), tuple(s(70, 134)), tuple(s(96, 164))], fill=255, width=w, joint="curve")
    d.line([tuple(s(144, 104)), tuple(s(170, 134)), tuple(s(144, 164))], fill=255, width=w, joint="curve")
    d.line([tuple(s(132, 100)), tuple(s(108, 168))], fill=230, width=w)


@area("backend")
def database(d):
    l, r, w = 56, 184, 11 * SS
    d.rectangle(s(l, 56, r, 192), fill=80)
    d.ellipse(s(l, 172, r, 212), fill=80)
    for y in (102, 148, 192):
        d.arc(s(l, y - 20, r, y + 20), 0, 180, fill=255, width=w)
    d.line([tuple(s(l + 5, 56)), tuple(s(l + 5, 192))], fill=255, width=w)
    d.line([tuple(s(r - 5, 56)), tuple(s(r - 5, 192))], fill=255, width=w)
    d.ellipse(s(l, 36, r, 76), fill=255)


@area("devops")
def infinity(d):
    a, cx, cy = 100, 120, 120
    pts = []
    for i in range(361):
        t = math.radians(i)
        den = 1 + math.sin(t) ** 2
        pts.append(tuple(s(cx + a * math.cos(t) / den, cy + a * math.sin(t) * math.cos(t) / den * 1.25)))
    d.line(pts, fill=255, width=20 * SS, joint="curve")


@area("ai / ml")
def network(d):
    layers = [(50, [70, 120, 170]), (120, [48, 96, 144, 192]), (190, [95, 145])]
    for (x1, ys1), (x2, ys2) in zip(layers, layers[1:]):
        for y1 in ys1:
            for y2 in ys2:
                d.line([tuple(s(x1, y1)), tuple(s(x2, y2))], fill=120, width=4 * SS)
    for x, ys in layers:
        for y in ys:
            d.ellipse(s(x - 15, y - 15, x + 15, y + 15), fill=255)


BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16


def mosaic(fn):
    img = Image.new("L", (BOX * SS, BOX * SS), 0)
    fn(ImageDraw.Draw(img))
    n = BOX // STEP
    a = np.asarray(img.resize((n, n), Image.Resampling.BOX), dtype=float) / 255
    yy, xx = np.mgrid[0:n, 0:n] / n
    a = a * (1 - .32 * (xx + yy) / 2)            # light falls from the top left
    rects = []
    for y in range(n):
        for x in range(n):
            lv = int(np.clip(round(a[y, x] * 4 + BAYER[y % 4, x % 4] - .5), 0, 4))
            if lv:
                rects.append(f'<rect x="{x * STEP}" y="{y * STEP}" width="{STEP - .7}" height="{STEP - .7}" fill-opacity="{.25 * lv:.2f}"/>')
    return "".join(rects)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        for label, fn in AREAS:
            f.write(f'<g data-label="{label}" fill="url(#ink)">{mosaic(fn)}</g>\n')
    print(f"wrote {OUT}: {', '.join(l for l, _ in AREAS)}")


if __name__ == "__main__":
    main()
