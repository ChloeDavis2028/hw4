"""Funny promo reels: a short looping "cargo drop" GIF for each product, made from its own photo.

The story (~3 s loop, 320x320):
  1. A C-130 flies in from the left and opens its rear cargo ramp.
  2. The product drops out on a red-and-white striped parachute and sways down.
  3. It crash-lands on the runway with a bounce and a puff of dust; the chute flops over.
  4. A "SPECIAL DELIVERY!" stamp slams down and the price tag pops in.
The product's fun name rides on the navy runway banner the whole time.

Everything is drawn from our own data, so the reels are free to use. They are
generated on first request and cached in data/reels/ (not committed to git,
since they are made from the product images).
"""

import json
import math
import threading
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"
REELS_DIR = DATA_DIR / "reels"
FLAIR = json.loads((HERE / "product_flair.json").read_text(encoding="utf-8"))

REEL_VERSION = 2  # bump when the reel design changes, so browsers and the cache refresh
SIZE = 320
FRAMES = 34
FRAME_MS = 85
HOLD_MS = 1100  # pause on the final "special delivery" frame before looping
NAVY = (0, 53, 107)
GOLD = (242, 182, 50)
INK = (15, 27, 45)
RED = (200, 40, 40)
BANNER_H = 58
GROUND_Y = SIZE - BANNER_H  # top of the runway banner = where the package lands
DROP_T = 0.24  # moment the package falls out of the cargo ramp

_lock = threading.Lock()


def reel_url(product_id: str) -> str:
    return f"/api/products/{product_id}/reel.gif?v={REEL_VERSION}"


def _font(names: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            continue
    return ImageFont.load_default()


TITLE_FONT = _font(["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"], 18)
PRICE_FONT = _font(["impact.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"], 22)
STAMP_FONT = _font(["impact.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"], 30)


# ---------- scenery and props ----------

def _sky() -> Image.Image:
    sky = Image.new("RGB", (SIZE, SIZE))
    top, bottom = (120, 176, 238), (214, 232, 250)
    d = ImageDraw.Draw(sky)
    for y in range(SIZE):
        f = y / SIZE
        d.line([(0, y), (SIZE, y)], fill=tuple(int(a + (b - a) * f) for a, b in zip(top, bottom)))
    for cx, cy, w in ((60, 120, 70), (250, 160, 90)):  # a couple of soft clouds
        d.ellipse([cx - w // 2, cy - 12, cx + w // 2, cy + 12], fill=(250, 252, 255))
        d.ellipse([cx - w // 4, cy - 22, cx + w // 4, cy + 4], fill=(250, 252, 255))
    return sky


def _c130_side(ramp_open: float) -> Image.Image:
    """Side view of a C-130 flying right; ramp_open 0..1 lowers the rear cargo ramp."""
    img = Image.new("RGBA", (130, 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    gray, dark = (86, 98, 112), (52, 62, 74)
    d.rounded_rectangle([18, 22, 118, 40], radius=9, fill=gray)  # fuselage
    d.ellipse([104, 22, 126, 40], fill=gray)  # nose
    d.polygon([(18, 24), (4, 6), (16, 6), (34, 24)], fill=dark)  # tail fin
    d.polygon([(10, 26), (2, 30), (22, 30)], fill=dark)  # tail plane
    d.rounded_rectangle([46, 17, 98, 22], radius=2, fill=dark)  # high wing
    for x in (54, 76):  # engines + spinning props
        d.rounded_rectangle([x, 18, x + 14, 25], radius=3, fill=dark)
        d.line([(x + 15, 13), (x + 15, 30)], fill=(30, 30, 30), width=2)
    d.polygon([(110, 26), (121, 26), (121, 31), (112, 31)], fill=(170, 210, 240))  # cockpit window
    for x in range(40, 100, 12):
        d.ellipse([x, 27, x + 4, 31], fill=(190, 215, 235))  # side windows
    # rear cargo ramp swings down from the belly
    hinge = (34, 40)
    ang = math.radians(10 + 55 * ramp_open)
    end = (hinge[0] - 20 * math.cos(ang), hinge[1] + 20 * math.sin(ang))
    d.line([hinge, end], fill=dark, width=4)
    if ramp_open > 0.3:  # dark open doorway
        d.rectangle([20, 34, 34, 40], fill=(20, 24, 30))
    return img


def _parachute(collapse: float = 0.0) -> Image.Image:
    """Red-and-white striped canopy with shroud lines; collapse 0..1 flattens it."""
    w, h = 96, 70
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ch = int(34 * (1 - 0.8 * collapse))
    box = [4, 4 + (34 - ch), w - 4, 4 + (34 - ch) + ch * 2]
    for k in range(6):
        d.pieslice(box, 180 + k * 30, 180 + (k + 1) * 30, fill=RED if k % 2 == 0 else (255, 255, 255), outline=(120, 20, 20))
    rim = 4 + 34
    for x in (6, 30, 66, w - 6):
        d.line([(x, rim), (w // 2, h - 2)], fill=(90, 90, 90), width=1)
    return img


def _package(photo: Image.Image) -> Image.Image:
    """The product photo on a white card with a cargo strap."""
    pw, ph = photo.size
    img = Image.new("RGBA", (pw + 12, ph + 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, pw + 11, ph + 11], radius=10, fill="white", outline=INK, width=2)
    img.paste(photo, (6, 6))
    d.line([((pw + 12) // 2, 0), ((pw + 12) // 2, 6)], fill=(120, 90, 40), width=3)  # strap tab
    return img


def _stamp(text: str) -> Image.Image:
    tmp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    tw = int(tmp.textlength(text, font=STAMP_FONT))
    img = Image.new("RGBA", (tw + 26, 50), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([1, 1, tw + 24, 48], radius=8, fill=(255, 255, 255, 240), outline=RED, width=4)
    d.text((13, 6), text, font=STAMP_FONT, fill=RED)
    return img.rotate(-9, expand=True, resample=Image.BICUBIC)


def _wrap(text: str, font, max_w: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words, lines, line = text.split(), [], ""
    for w in words:
        trial = f"{line} {w}".strip()
        if draw.textlength(trial, font=font) <= max_w:
            line = trial
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    if len(lines) > 2:
        lines = lines[:2]
        while draw.textlength(lines[1] + "…", font=font) > max_w and len(lines[1]) > 1:
            lines[1] = lines[1][:-1]
        lines[1] = lines[1].rstrip() + "…"
    return lines


def _ease_out_back(x: float) -> float:
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def _paste_center(base: Image.Image, img: Image.Image, cx: float, cy: float) -> None:
    base.paste(img, (int(cx - img.width / 2), int(cy - img.height / 2)), img)


# ---------- the reel ----------

def make_reel(product_id: str, image_file_path: str, price: float, name: str) -> Path:
    """Build (or reuse) the cargo-drop GIF for one product and return its path."""
    REELS_DIR.mkdir(parents=True, exist_ok=True)
    out = REELS_DIR / f"{product_id}-v{REEL_VERSION}.gif"
    with _lock:
        if out.exists():
            return out
        fun_name = FLAIR.get(product_id, {}).get("fun_name", name)
        photo = Image.open(DATA_DIR / image_file_path).convert("RGB")
        photo.thumbnail((112, 104))
        package = _package(photo)
        sky = _sky()
        delivery = _stamp("SPECIAL DELIVERY!")
        price_text = f"${price:,.0f}" if float(price).is_integer() else f"${price:,.2f}"

        # the package leaves through the open ramp, just behind the plane's belly
        drop_x = -130 + (SIZE + 260) * (DROP_T / 0.55) + 26
        land_cx = SIZE // 2
        frames: list[Image.Image] = []
        for i in range(FRAMES):
            t = i / (FRAMES - 1)
            f = sky.copy()
            d = ImageDraw.Draw(f)

            # 1. plane flies left -> right; ramp opens as it reaches the drop point
            plane_x = -130 + (SIZE + 260) * min(1.0, t / 0.55)
            ramp = max(0.0, min(1.0, (plane_x - 40) / 70))
            if t < 0.55:
                plane = _c130_side(ramp)
                f.paste(plane, (int(plane_x), 18), plane)

            # 2. package falls under the chute, swaying; 3. lands at t=0.62
            if t >= DROP_T:
                k = min(1.0, (t - DROP_T) / (0.62 - DROP_T))  # 0 -> 1 during the fall
                landed = t >= 0.62
                sway = 0 if landed else 12 * math.sin(k * math.pi * 3)
                x = drop_x + (land_cx - drop_x) * k
                y_top, y_land = 40 + package.height / 2, GROUND_Y - package.height / 2 - 2
                y = y_top + (y_land - y_top) * (k ** 1.15)
                squash = 1.0
                if landed:  # bounce after touchdown
                    b = (t - 0.62) / 0.12
                    if b < 1:
                        y -= 18 * abs(math.sin(b * math.pi * 1.5)) * (1 - b)
                        squash = 1 - 0.12 * max(0.0, math.cos(b * math.pi * 3)) * (1 - b)
                pkg = package.resize((package.width, max(10, int(package.height * squash))), Image.BICUBIC)
                pkg = pkg.rotate(sway, expand=True, resample=Image.BICUBIC)
                y += package.height * (1 - squash) / 2

                collapse = 0.0 if not landed else min(1.0, (t - 0.62) / 0.1)
                chute = _parachute(collapse)
                if collapse > 0:  # chute flops over to the side after landing
                    chute = chute.rotate(-70 * collapse, expand=True, resample=Image.BICUBIC)
                    _paste_center(f, chute, x + 52 * collapse, y - package.height / 2 - 18 + 30 * collapse)
                else:
                    cx_chute = x + sway * 0.8
                    _paste_center(f, chute.rotate(sway * 0.6, expand=True, resample=Image.BICUBIC), cx_chute, y - package.height / 2 - 30)
                _paste_center(f, pkg, x, y)

                # dust puff on touchdown
                if 0.62 <= t < 0.82:
                    p = (t - 0.62) / 0.2
                    for dx in (-1, 1):
                        r = int(8 + 22 * p)
                        cx = land_cx + dx * (package.width / 2 + 6 * p * 4)
                        shade = int(200 + 40 * p)
                        d.ellipse([cx - r, GROUND_Y - r, cx + r, GROUND_Y + r // 3], fill=(shade, shade - 10, shade - 30))

            # runway banner with the fun name (the package lands on it)
            d.rectangle([0, GROUND_Y, SIZE, SIZE], fill=NAVY)
            for x in range(-30, SIZE, 40):
                d.line([(x, SIZE - 7), (x + 20, SIZE - 7)], fill=GOLD, width=3)
            lines = _wrap(fun_name, TITLE_FONT, SIZE - 24, d)
            y0 = GROUND_Y + (BANNER_H - 10 - 21 * len(lines)) // 2
            for n, line in enumerate(lines):
                d.text((SIZE // 2, y0 + 21 * n + 10), line, font=TITLE_FONT, fill="white", anchor="mm")

            # 4. SPECIAL DELIVERY! slams down, then the price pops
            if t >= 0.7:
                k = min(1.0, (t - 0.7) / 0.08)
                sc = 2.0 - 1.0 * k
                st = delivery.resize((int(delivery.width * sc), int(delivery.height * sc)), Image.BICUBIC)
                _paste_center(f, st, SIZE / 2, 88)
            if t >= 0.8:
                k = min(1.0, (t - 0.8) / 0.12)
                r = int(30 * _ease_out_back(k))
                if r > 2:
                    tx, ty = SIZE - 46, 150
                    d.ellipse([tx - r, ty - r, tx + r, ty + r], fill=GOLD, outline=INK, width=2)
                    if k > 0.6:
                        d.text((tx, ty), price_text, font=PRICE_FONT, fill=INK, anchor="mm")

            frames.append(f.convert("P", palette=Image.ADAPTIVE, colors=128))

        durations = [FRAME_MS] * (FRAMES - 1) + [HOLD_MS]
        tmp = out.with_suffix(".tmp.gif")
        frames[0].save(tmp, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True, disposal=2)
        tmp.replace(out)
        return out
