"""Turn my GitHub avatar into a stylised portrait for the profile card.

Run by hand when the avatar changes (it needs a 170 MB segmentation model, so
it does not run in CI):

    uv run --with "rembg[cpu]" --with opencv-python-headless --with numpy \
        --with pillow --with scikit-image python .github/scripts/portrait.py --style shape

It writes assets/profile/portrait-dark.svg and portrait-light.svg: SVG
fragments with no colours of their own (everything is painted with url(#ink)),
which profile.py places inside the card. Ink means light on the dark theme and
dark on the light theme, so the light fragment is drawn from the inverted tones
inside the cut-out. --gallery DIR also renders every style side by side.

Pipeline: cut the subject out with a portrait segmentation model, drop the
chair behind me, lift the shadows with local contrast (CLAHE), half-equalise
the tones inside the cut-out so the face and the white shirt get the same
spread, then draw it in the chosen style.
"""

import argparse
import io
import os
import urllib.request
from html import escape

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

USER = "cliffkoome"
PW, PH = 336, 420  # portrait box in the card
OUT = "assets/profile/portrait-{theme}.svg"
FONT = "DejaVu Sans Mono, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
FONT_FILE = "/usr/share/fonts/TTF/DejaVuSansMono.ttf"


# ------------------------------------------------------------------ prepare

def prepare():
    from rembg import new_session, remove

    url = f"https://avatars.githubusercontent.com/{USER}?s=800"
    with urllib.request.urlopen(url) as resp:
        photo = Image.open(io.BytesIO(resp.read())).convert("RGB")
    cut = np.array(remove(photo, session=new_session("birefnet-portrait")))
    bgr, alpha = cv2.cvtColor(cut[..., :3], cv2.COLOR_RGB2BGR), cut[..., 3]
    h, w = alpha.shape

    m = (alpha > 200).astype(np.uint8)
    # The model keeps part of the wicker chair behind my shoulders: drop warm,
    # saturated pixels below the chin and outside the neck/tie column.
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    yy, xx = np.mgrid[0:h, 0:w]
    chair = (hsv[..., 0] < 30) & (hsv[..., 1] > 70) & (yy > .5 * h) & ((xx < .33 * w) | (xx > .64 * w))
    m[chair] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    m = (lab == 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])).astype(np.uint8)  # biggest blob: me
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    mask = cv2.GaussianBlur(m.astype(np.float32), (5, 5), 0)

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    img = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray).astype(np.float32) / 255
    inside = mask > .5
    rank = np.argsort(np.argsort(img[inside])) / max(1, inside.sum() - 1)
    eq = np.zeros_like(img)
    eq[inside] = .12 + .88 * rank
    img = (.5 * cv2.GaussianBlur(eq, (3, 3), 0) + .5 * img) * mask

    # Crop to the box's aspect ratio, centred on me.
    cw = int(h * PW / PH)
    x0 = max(0, min(w - cw, int(np.average(xx[inside])) - cw // 2))
    return img[:, x0:x0 + cw], mask[:, x0:x0 + cw]


# ------------------------------------------------------------------ styles
# Each returns (svg_body, css). Bodies paint with url(#ink) only.

ROWCSS = ".pr { animation: pin .45s steps(5) backwards; } @keyframes pin { from { opacity: 0; } }"


def runs(line, cw):
    """Place each run of non-space characters at its own x, so no renderer can
    collapse the leading spaces and shift the picture."""
    out, i = [], 0
    while i < len(line):
        if line[i] == " ":
            i += 1
            continue
        j = i
        while j < len(line) and line[j] != " ":
            j += 1
        out.append(f'<tspan x="{i * cw:.1f}">{escape(line[i:j])}</tspan>')
        i = j
    return "".join(out)


def text_block(lines, fs, step=.03):
    cw = fs * .6
    rows = "".join(
        f'<text y="{(y + 1) * fs:.1f}" class="pr" style="animation-delay:{y * step:.2f}s">{runs(l, cw)}</text>'
        for y, l in enumerate(lines)
    )
    return f'<g font-family="{FONT}" font-size="{fs:.2f}" fill="url(#ink)">{rows}</g>', ROWCSS


def cells(img, cols, sub=(1, 1)):
    fs = PW / cols / .6
    rows = int(PH / fs)
    return fs, rows, cv2.resize(img, (cols * sub[0], rows * sub[1]), interpolation=cv2.INTER_AREA)


def style_shape(img, mask, cols=58):
    """Shape-matched ASCII: for each cell, the printable character whose ink
    layout (3x5 sub-cells) best matches the image."""
    font = ImageFont.truetype(FONT_FILE, 20)
    chars = [chr(c) for c in range(32, 127)]
    vecs = []
    for ch in chars:
        g = Image.new("L", (12, 20), 0)
        ImageDraw.Draw(g).text((0, -2), ch, fill=255, font=font)
        vecs.append(cv2.resize(np.asarray(g, np.float32) / 255, (3, 5), interpolation=cv2.INTER_AREA).ravel())
    gv = np.stack(vecs)
    gv /= gv.max()
    fs, rows, big = cells(img, cols, (3, 5))
    big = np.clip((big - .04) * 1.25, 0, 1)
    lines = []
    for r in range(rows):
        c = big[r * 5:(r + 1) * 5].reshape(5, cols, 3).transpose(1, 0, 2).reshape(cols, 15)
        lines.append("".join(chars[i] for i in ((c[:, None] - gv[None]) ** 2).sum(-1).argmin(1)))
    return text_block(lines, fs)


def style_classic(img, mask, cols=46):
    """Brightness ramp, the classic neofetch / Andrew Grant look."""
    ramp = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
    fs, rows, small = cells(img, cols)
    lines = ["".join(ramp[int(v ** .85 * (len(ramp) - 1))] for v in row) for row in small]
    return text_block(lines, fs)


def style_braille(img, mask, cols=58):
    fs, rows, big = cells(img, cols, (2, 4))
    px = Image.fromarray((big * 255).astype(np.uint8)).convert("1").load()  # Floyd-Steinberg
    bits = [(0, 0, 1), (0, 1, 2), (0, 2, 4), (1, 0, 8), (1, 1, 16), (1, 2, 32), (0, 3, 64), (1, 3, 128)]
    lines = [
        "".join(chr(0x2800 + sum(b for dx, dy, b in bits if px[cx + dx, cy + dy])) for cx in range(0, cols * 2, 2))
        for cy in range(0, rows * 4, 4)
    ]
    lines = [l.replace("⠀", " ") for l in lines]  # blank cells as spaces, so they are skipped
    return text_block(lines, fs)


def style_halftone(img, mask, step=6):
    cols, rows = PW // step, PH // step
    small = cv2.resize(img, (cols, rows), interpolation=cv2.INTER_AREA)
    dots = "".join(
        f'<circle cx="{x * step + step / 2}" cy="{y * step + step / 2}" r="{small[y, x] * step * .55:.2f}"/>'
        for y in range(rows) for x in range(cols) if small[y, x] >= .05
    )
    css = ".ht { animation: hin 1.6s ease-out backwards, breathe 6s ease-in-out 2s infinite; } " \
          "@keyframes hin { from { opacity: 0; } } @keyframes breathe { 50% { opacity: .78; } }"
    return f'<g class="ht" fill="url(#ink)">{dots}</g>', css


def style_engraving(img, mask, rows=60, samples=150):
    lh = PH / rows
    small = cv2.resize(img, (samples, rows), interpolation=cv2.INTER_AREA)
    paths = []
    for y in range(rows):
        cy = (y + .5) * lh
        xs = [x * PW / (samples - 1) for x in range(samples)]
        top = [f"{x:.1f},{cy - small[y, i] * lh * .48:.2f}" for i, x in enumerate(xs)]
        bot = [f"{x:.1f},{cy + small[y, i] * lh * .48:.2f}" for i, x in enumerate(xs)]
        paths.append(f'<path class="en" style="animation-delay:{y * .03:.2f}s" d="M{" L".join(top)} L{" L".join(reversed(bot))}Z"/>')
    css = ".en { transform-box: fill-box; transform-origin: left; animation: ein .8s ease-out backwards; } " \
          "@keyframes ein { from { transform: scaleX(0); } }"
    return f'<g fill="url(#ink)">{"".join(paths)}</g>', css


def style_mosaic(img, mask, step=6):
    cols, rows = PW // step, PH // step
    small = cv2.resize(img, (cols, rows), interpolation=cv2.INTER_AREA)
    bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16
    rects = []
    for y in range(rows):
        for x in range(cols):
            lv = int(np.clip(round(small[y, x] * 4 + bayer[y % 4, x % 4] - .5), 0, 4))
            if lv:
                rects.append(f'<rect x="{x * step}" y="{y * step}" width="{step - .7}" height="{step - .7}" fill-opacity="{.25 * lv:.2f}"/>')
    css = ".mo { animation: mon 1.4s steps(8) backwards; } @keyframes mon { from { opacity: 0; } }"
    return f'<g class="mo" fill="url(#ink)">{"".join(rects)}</g>', css


def style_contours(img, mask, levels=11):
    from skimage import measure

    sm = cv2.GaussianBlur(img, (9, 9), 0)
    s = PW / sm.shape[1]
    paths = []
    for li, lv in enumerate(np.linspace(.08, .85, levels)):
        for c in measure.find_contours(sm, lv):
            if len(c) < 25:
                continue
            c = c[::2]
            d = "M" + " L".join(f"{p[1] * s:.1f},{p[0] * s:.1f}" for p in c)
            paths.append(f'<path d="{d}" style="--l:{len(c) * 2 * s:.0f};animation-delay:{li * .25:.2f}s" class="ct"/>')
    css = ".ct { fill: none; stroke: url(#ink); stroke-width: .9; stroke-dasharray: var(--l); animation: trace 3s ease-out backwards; } " \
          "@keyframes trace { from { stroke-dashoffset: var(--l); } }"
    return "".join(paths), css


STYLES = {
    "shape": style_shape, "classic": style_classic, "braille": style_braille, "halftone": style_halftone,
    "engraving": style_engraving, "mosaic": style_mosaic, "contours": style_contours,
}


def fragment(body, css):
    return f'<g class="portrait"><style>{css}</style>{body}</g>\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", choices=STYLES, default="shape")
    ap.add_argument("--gallery", metavar="DIR", help="also write every style to DIR/<style>.svg")
    args = ap.parse_args()
    img, mask = prepare()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    light = np.where(mask > .5, .1 + .9 * (1 - img), 0) * mask   # ink where the photo is dark
    for theme, im in (("dark", img), ("light", light)):
        with open(OUT.format(theme=theme), "w") as f:
            f.write(fragment(*STYLES[args.style](im, mask)))
    if args.gallery:
        os.makedirs(args.gallery, exist_ok=True)
        for name, fn in STYLES.items():
            with open(f"{args.gallery}/{name}.svg", "w") as f:
                f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{PW}" height="{PH}" viewBox="0 0 {PW} {PH}">'
                        f'<defs><linearGradient id="ink" x1="0" y1="0" x2=".3" y2="1"><stop offset="0" stop-color="#2dd4bf"/>'
                        f'<stop offset=".6" stop-color="#38bdf8"/><stop offset="1" stop-color="#818cf8"/></linearGradient></defs>'
                        f'<rect width="{PW}" height="{PH}" fill="#0a0e16"/>{fragment(*fn(img, mask))}</svg>')


if __name__ == "__main__":
    main()
